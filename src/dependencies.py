#!/usr/bin/env python3

###################################################################################
# Copyright (c) 2024 "dEajL3kA" <Cumpoing79@web.de>                               #
# This work has been released under the MIT license. See LICENSE.txt for details! #
###################################################################################

import argparse
import io
import json
import os
import re
import subprocess
import sys

from datetime import datetime
from copy import deepcopy
from os.path import isfile, realpath, normpath
from collections import deque
from typing import Dict, List, Callable, Optional, Any

# ============================================================================
# Constants
# ============================================================================

# Version information
_VERSION = (1, 3, 1712225082)

# Dictionary keys
_KEY_DEPENDENCIES = 'dependencies'
_KEY_FILENAME = 'filename'
_KEY_NAME = 'name'
_KEY_PATH = 'path'
_KEY_SONAME = 'soname'
_KEY_SYMBOLS = 'symbols'
_KEY_TYPE = 'type'

# ============================================================================
# Functions
# ============================================================================

def _start_process(args: List[str]) -> subprocess.Popen:
    return subprocess.Popen(args, stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdout=subprocess.PIPE, env=my_env)

def _lazy_compute(cache: Dict, category: str, key: str, factory: Callable[[str], Any]) -> Any:
    cache_entry = json.dumps({ 'category': category, 'name': key }, sort_keys=True, separators=(',', ':'))
    value = cache.get(cache_entry, NotImplemented)
    return deepcopy(value if value is not NotImplemented else cache.setdefault(cache_entry, factory(key)))

def _merge_dict(first: Optional[dict], second: Optional[dict]) -> dict:
    merged = deepcopy(first) if first is not None else {}
    if second is not None:
        merged.update({ _key: _value for _key, _value in second.items() if _key not in merged })
    return merged

def _is_weak_symbol(symbol_type: str) -> bool:
    return (len(symbol_type) > 0) and ("VvWw".find(symbol_type[-1]) >= 0)

# ~~~~~~~~~~~~~~~~~~~~~~
# Detect executable file
# ~~~~~~~~~~~~~~~~~~~~~~

def _detect_executable(filename: str) -> bool:
    is_executable = False
    regex = re.compile(r'^([^:]+:)?\s*ELF(\s|,|$)', re.I)
    try:
        with _start_process(['/usr/bin/file', filename]) as proc:
            for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
                match = regex.search(line)
                if match:
                    is_executable = True
            proc.wait()
    except OSError:
        raise ValueError("Failed to execute \"file\" program!")
    return is_executable

# ~~~~~~~~~~~~~~~~~~~~~~~
# Detect all dependencies
# ~~~~~~~~~~~~~~~~~~~~~~~

def _detect_dependencies(filename: str) -> Dict[str, str]:
    dependencies, openbsd_compat = {}, sys.platform.startswith('openbsd')
    regex = re.compile(
        r'^\s+([0-9A-Fa-f]+\s+){2}(exe|rlib|dlib|ld\.so)\s+(\d+\s+){3}(.+?)\s*$' if openbsd_compat else
        r'^\s+([^<>]+?)(\s+=>\s+(.*?))??(\s*\(0x[0-9A-Fa-f]+\))?\s*$')
    try:
        with _start_process(['/usr/bin/ldd', filename]) as proc:
            for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
                match = regex.search(line)
                if match:
                    if openbsd_compat:
                        type, library = match.group(2), match.group(4)
                        if type != "exe":
                            basename = os.path.basename(library)
                            dependencies[basename] = realpath(normpath(library))
                    else:
                        library, path = match.group(1), match.group(3)
                        if path:
                            if path != "not found":
                                dependencies[library] = realpath(normpath(path))
                        elif library.startswith("/"):
                            basename = os.path.basename(library)
                            dependencies[basename] = realpath(normpath(library))
            error_code = proc.wait()
            if error_code != 0:
                raise ValueError(f"Failed to detect dependencies! (error code: {error_code})")
    except OSError:
        raise ValueError("Failed to execute \"ldd\" program!")
    return dependencies

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Detect all imported/exported symbols
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def _detect_symbols(filename: str, get_defined: bool) -> Dict[str, str]:
    dynamic_symbols = {}
    regex_line = re.compile(r'^\s*([0-9a-fA-F]+\s+)?([A-Za-z])\s+([^\s]+)\s*$')
    regex_zero = re.compile(r'^0+$')
    regex_name = re.compile(r'([^@\s]+)@@([^@\s]+)')
    try:
        with _start_process(['/usr/bin/nm', '-D', '-p', filename]) as proc:
            for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
                match = regex_line.search(line)
                if match:
                    address, symbol_type, symbol_name = match.group(1), match.group(2), match.group(3)
                    is_defined = address and (not regex_zero.search(address)) and (symbol_type != 'U')
                    if (is_defined if get_defined else (not is_defined)):
                        match = regex_name.search(symbol_name)
                        if match:
                            dynamic_symbols[f"{match.group(1)}@{match.group(2)}"] = symbol_type
                            dynamic_symbols[match.group(1)] = f"~{symbol_type}"
                        else:
                            dynamic_symbols[symbol_name] = symbol_type
            error_code = proc.wait()
            if error_code != 0:
                raise ValueError(f"Failed to read symbol table! (error code: {error_code})")
    except OSError:
        raise ValueError("Failed to execute \"nm\" program!")
    return dynamic_symbols

# ============================================================================
# Process File
# ============================================================================

def process_file_recursive(filename: str, ignore_weak: bool, cache: Dict[str, Any] = {}, preloaded: Optional[Dict[str, str]] = None) -> Optional[List[Dict]]:
    # Detect dependencies
    dependencies = _merge_dict(preloaded, _lazy_compute(cache, 'dep', filename, lambda _key: _detect_dependencies(_key)))

    # Detect imported symbols
    imported = _lazy_compute(cache, 'imp', filename, lambda _key: _detect_symbols(_key, False))
    if len(imported) < 1:
        return None

    # Detect exported symbols of each library
    exported = {}
    for library in dependencies:
        filename = dependencies[library]
        if not (isfile(filename) and os.access(filename, os.R_OK)):
            raise ValueError(f"Required library \"{filename}\" not found or access denied!")
        exported[library] = _lazy_compute(cache, 'exp', filename, lambda _key: _detect_symbols(_key, True))

    # Initialize buffers
    library_resolved, already_found = {}, set()
    for library in dependencies:
        library_resolved[library] = []

    # Determine which symbols are imported from each library
    for stage in range(3):
        for library in dependencies:
            _library_resolved = library_resolved[library]
            _exported = exported[library]
            for symbol in [ name for name in _exported if (name not in already_found) and (name in imported) ]:
                type = _exported[symbol]
                if (stage > 1) or (not type.startswith('~')):
                    if (stage > 0) or (not _is_weak_symbol(type)):
                        _library_resolved.append({ _KEY_NAME: symbol, _KEY_TYPE: type[-1] })
                        already_found.add(symbol)
        if not any(symbol not in already_found for symbol in imported):
            break

    # Build the result data
    result_list = []
    for library in dependencies:
        _library_resolved = library_resolved[library]
        if len(_library_resolved) > 0:
            result_list.append({ _KEY_SONAME: library, _KEY_PATH: dependencies[library], _KEY_SYMBOLS: sorted(_library_resolved, key=lambda sym: sym[_KEY_NAME]) })

    # Check for unresolved symbols
    unresolved = [ { _KEY_NAME: name, _KEY_TYPE: imported[name]} for name in imported if name not in already_found ]
    if ignore_weak:
        unresolved = [ symbol for symbol in unresolved if not _is_weak_symbol(symbol[_KEY_TYPE]) ]
    if len(unresolved) > 0:
        result_list.append({ _KEY_SONAME: None, _KEY_SYMBOLS: sorted(unresolved, key=lambda sym: sym[_KEY_NAME]) })

    return result_list

def process_file(filename: str, cache: Dict[str, Any] = {}, recursive: bool = False, print_types: bool = False, no_preload: bool = False, no_filter: bool = False) -> List[Any]:
    # Normalize file name
    filename = realpath(normpath(filename))
    if not (isfile(filename) and os.access(filename, os.R_OK)):
        raise OSError(f"Input file \"{filename}\" not found or access denied!")

    # Check file type
    if not _detect_executable(filename):
        raise ValueError(f"Input file \"{filename}\" is not a supported executable file or shared library!")

    # Create queue
    results, files_visited, pending_files, = [], { filename }, deque({ (filename, None) })

    # Process all pending files
    while True:
        try:
            filename, preloaded = pending_files.popleft()
        except IndexError:
            break
        result = process_file_recursive(filename, not no_filter, cache, preloaded)
        if result:
            results.append({ _KEY_FILENAME: filename, _KEY_DEPENDENCIES: result[0] if len(result) == 1 else result })
            if recursive:
                preloaded = _merge_dict(preloaded, { _library[_KEY_SONAME]: _library[_KEY_PATH] for _library in result if _KEY_PATH in _library }) if not no_preload else None
                for path in [ _path for _path in [ library[_KEY_PATH] for library in result if _KEY_PATH in library ] if _path not in files_visited ]:
                    files_visited.add(path)
                    pending_files.append((path, preloaded))

    # Eradicate symbol types, if requested
    if not print_types:
        for result in results:
            depslist = result[_KEY_DEPENDENCIES]
            for library in depslist if isinstance(depslist, list) else [depslist]:
                library[_KEY_SYMBOLS] = [ symbol[_KEY_NAME] for symbol in library[_KEY_SYMBOLS] ]

    return results

# ============================================================================
# Output
# ============================================================================

def print_results(results: List[Any], json_format: bool = False, indent: int = 3):
    # Output the final results
    if json_format:
        json.dump(results[0] if len(results) == 1 else results, sys.stdout, indent=(indent if indent > 0 else None))
        print(file=sys.stdout)
    else:
        indent_chars = ('\x20' * indent, '\x20' * (2 * indent)) if indent > 0 else ('\t', '\t\t')
        for result in results:
            print(result[_KEY_FILENAME])
            depslist = result[_KEY_DEPENDENCIES]
            for library in depslist if isinstance(depslist, list) else [depslist]:
                imported_symbols = library[_KEY_SYMBOLS]
                print(f"{indent_chars[0]}{library[_KEY_SONAME]} => {library[_KEY_PATH]}" if library[_KEY_SONAME] else f"{indent_chars[0]}unresolved symbols:")
                for symbol in imported_symbols:
                    print(f"{indent_chars[1]}{symbol[_KEY_NAME]} [{symbol[_KEY_TYPE]}]" if isinstance(symbol, dict) else f"{indent_chars[1]}{symbol}")
        print()

# ============================================================================
# MAIN
# ============================================================================

def main() -> int:
    # Check python version
    if  (sys.version_info[0] << 8) + sys.version_info[1] < 0x307:
        print("Dependencies.py: Sorry, this script requires Python version 3.7 or later!", file=sys.stderr)
        return 1

    # Check operating system
    if not re.search(r'^(linux|(free|open|net)bsd)|sunos', sys.platform, re.A | re.I):
        print(f"Dependencies.py: Sorry, this script must run on the Linux or *BSD platform! [{sys.platform}]", file=sys.stderr)
        return 1

    # Initialize version string
    version_string = f"Dependencies.py {_VERSION[0]:d}.{_VERSION[1]:02d} [{datetime.fromtimestamp(_VERSION[2]).date()}]"

    # Initialize argument parser
    parser = argparse.ArgumentParser(description="Detects all symbols that an executable file (or shared library) imports from other shared libraries.",
        epilog="Please check \"https://github.com/dEajL3kA/dependencies.py\" for updates!")
    parser.add_argument('input', action='store', nargs='+', help="The input file(s) to be processed")
    parser.add_argument('-r', '--recursive', action='store_true', default=False, help="Recursively analyze shared library dependencies")
    parser.add_argument('-j', '--json-format', action='store_true', default=False, help="Generate JSON compatible output")
    parser.add_argument('-t', '--print-types', action='store_true', default=False, help="Output the type of each resolved symbol")
    parser.add_argument('-v', '--version', action='version', version=version_string, help="Print the script version")
    parser.add_argument('--no-preload', action='store_true', default=False, help="Ignore pre-loaded libraries (only relevant with --recursive)")
    parser.add_argument('--no-filter', action='store_true', default=False, help="Do not ignore \"weak\" unresolved symbols")
    parser.add_argument('--keep-going', action='store_true', default=False, help="Keep going, even when an error is encountered")
    parser.add_argument('--indent', type=int, default=3, help="Set number of spaces to use for indentation (default: 3)")

    # Parse arguments
    args = parser.parse_args()

    # Check required tool
    for tool in ['file', 'ldd', 'nm']:
        if not os.access(f'/usr/bin/{tool}', os.R_OK | os.X_OK):
            print(f"Required tool \"/usr/bin/{tool}\" is not available or inaccessible!", file=sys.stderr)
            return 1

    # Initialize the cache
    cache = {}

    # Create a modified environment
    global my_env
    my_env = os.environ.copy()
    my_env['LC_ALL'] = 'C.UTF-8'
    my_env['LANG'] = 'C.UTF-8'

    # Process all given input files
    for filename in args.input:
        try:
            results = process_file(filename, cache, args.recursive, args.print_types, args.no_preload, args.no_filter)
            if results:
                print_results(results, args.json_format, args.indent)
            else:
                print(f"No dependencies for \"{filename}\" have been found!", file=sys.stderr)
        except Exception as e:
            print(f"Error: {str(e)}", file=sys.stderr)
            if not args.keep_going:
                return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
