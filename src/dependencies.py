#!/usr/bin/env python3

###################################################################################
# Copyright (c) 2024 "dEajL3kA" <Cumpoing79@web.de>                               #
# This work has been released under the MIT license. See LICENSE.txt for details! #
###################################################################################

import subprocess
import io
import re
import os
import sys
import argparse
import json

from os.path import abspath, realpath
from collections import deque
from typing import Set, Dict, List, Tuple

# ============================================================================
# Constants
# ============================================================================

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

# ~~~~~~~~~~~~~~~~~
# Start sub-process
# ~~~~~~~~~~~~~~~~~

def _start_process(args: List[str]) -> subprocess.Popen:
    return subprocess.Popen(args, stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdout=subprocess.PIPE, env={'LC_ALL': 'C.UTF-8', 'LANG': 'C.UTF-8'})

# ~~~~~~~~~~~~~~~~~~~~~~
# Detect executable file
# ~~~~~~~~~~~~~~~~~~~~~~

def _detect_executable(filename: str) -> bool:
    is_executable = False
    regex = re.compile(r'application\s*/\s*x-((pie-)?executable|sharedlib)\s*;\s*charset\s*=\s*binary\s*$')
    try:
        with _start_process(['/usr/bin/file', '-L', '-i', filename]) as proc:
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

def _detect_dependencies(filename: str) -> Tuple[List[str], Dict[str, str]]:
    dependencies, dependency_paths = [], {}
    regex = re.compile(r'^\s*([^<>]+?)\s+(=>\s+(.+?))?(\s*\(0x[0-9A-Fa-f]+\))?\s*$')
    try:
        with _start_process(['/usr/bin/ldd', filename]) as proc:
            for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
                match = regex.search(line)
                if match:
                    library, path = match.group(1), match.group(3)
                    if path:
                        if path != "not found":
                            dependencies.append(library)
                            dependency_paths[library] = path
                    else:
                        if library.startswith("/"):
                            basename = os.path.basename(library)
                            dependencies.append(basename)
                            dependency_paths[basename] = library
            error_code = proc.wait()
            if error_code != 0:
                raise ValueError(f"Failed to detect dependencies! (error code: {error_code})")
    except OSError:
        raise ValueError("Failed to execute \"ldd\" program!")
    return (dependencies, dependency_paths)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Detect all imported/exported symbols
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def _detect_symbols(filename: str, defined: bool) -> Dict[str, str]:
    dynamic_symbols = {}
    regex_line = re.compile(r'^\s*([0-9a-zA-Z]+\s+)?([A-Za-z])\s+([^\s]+)\s*$')
    regex_name = re.compile(r'([^@\s]+)@@([^@\s]+)')
    try:
        with _start_process(['/usr/bin/nm', '-D', '--defined-only' if defined else '--undefined-only', filename]) as proc:
            for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
                match = regex_line.search(line)
                if match:
                    symbol_type, symbol_name = match.group(2), match.group(3)
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

# ~~~~~~~~~~~~~~~~~~~~~~~~
# Check for "weak" symbols
# ~~~~~~~~~~~~~~~~~~~~~~~~

def _is_weak_symbol(symbol_type: str) -> bool:
    return (len(symbol_type) > 0) and ("VvWw".find(symbol_type[-1]) >= 0)

# ============================================================================
# Process File
# ============================================================================

def process_file(filename: str, ignore_weak: bool) -> Tuple[List[Dict]]:
    if not _detect_executable(filename):
        raise ValueError(f"Input file \"{filename}\" is not a supported executable file or shared library!")

    dependencies, dependency_paths = _detect_dependencies(filename)
    if len(dependencies) < 1:
        return None

    imported = _detect_symbols(filename, False)
    if len(imported) < 1:
        return None

    exported = {}
    for library in dependencies:
        if not os.access(dependency_paths[library], os.R_OK):
            raise ValueError(f"Required library \"{dependency_paths[library]}\" not found or access denied!")
        exported[library] = _detect_symbols(dependency_paths[library], True)

    library_resolved, already_found = {}, set()
    for library in dependencies:
        library_resolved[library] = []

    for stage in range(3):
        for library in dependencies:
            _library_resolved = library_resolved[library]
            _exported = exported[library]
            for symbol in [ name for name in _exported if (name not in already_found) and (name in imported) ]:
                _type = _exported[symbol]
                if (stage > 1) or (not _type.startswith('~')):
                    if (stage > 0) or (not _is_weak_symbol(_type)):
                        _library_resolved.append({ _KEY_NAME: symbol, _KEY_TYPE: _type[-1] })
                        already_found.add(symbol)

    result_list = []
    for library in dependencies:
        _library_resolved = library_resolved[library]
        if len(_library_resolved) > 0:
            result_list.append({
                _KEY_SONAME: library, _KEY_PATH: dependency_paths[library],
                _KEY_SYMBOLS: sorted(_library_resolved, key=lambda sym: sym[_KEY_NAME]) })

    unresolved = [ { _KEY_NAME: name, _KEY_TYPE: imported[name]} for name in imported if name not in already_found ]
    if ignore_weak:
        unresolved = [ symbol for symbol in unresolved if not _is_weak_symbol(symbol[_KEY_TYPE]) ]
    if len(unresolved) > 0:
        result_list.append({ _KEY_SONAME: None, _KEY_SYMBOLS: sorted(unresolved, key=lambda sym: sym[_KEY_NAME]) })

    return result_list

# ============================================================================
# MAIN
# ============================================================================

def main() -> int:
    if not sys.platform.startswith('linux'):
        print(f"Sorry, this script must run on the Linux platform!", file=sys.stderr)
        return 1

    parser = argparse.ArgumentParser(description="Detects all symbols that an executable file (or shared library) imports from other shared libraries.")
    parser.add_argument('input', action='store', nargs='+', help="The input file(s) to be processed")
    parser.add_argument('-r', '--recursive', action='store_true', default=False, help="Recursively analyze shared library dependencies")
    parser.add_argument('-j', '--json-format', action='store_true', default=False, help="Generate JSON compatible output")
    parser.add_argument('--no-indent', action='store_true', default=False, help="Do not indent the generated JSON (requires --json-format)")
    parser.add_argument('--no-filter', action='store_true', default=False, help="Do not ignore \"weak\" unresolved symbols")
    parser.add_argument('--keep-going', action='store_true', default=False, help="Keep going, even when an error is encountered")

    args = parser.parse_args()

    if args.no_indent and not args.json_format:
        print("Option --no-indent is only valid, if option --json-format is enabled too!", file=sys.stderr)
        return 1

    for tool in ['file', 'ldd', 'nm']:
        if not os.access(f'/usr/bin/{tool}', os.R_OK | os.X_OK):
            print(f"Required tool \"/usr/bin/{tool}\" is not available or inaccessible!", file=sys.stderr)
            return 1

    results, files_visited, pending_files = [], set(), deque()

    for filename in args.input:
        try:
            filename = realpath(abspath(filename))
            if not (os.path.isfile(filename) and os.access(filename, os.R_OK)):
                raise OSError("File not found or access denied!")
            pending_files.append(filename)
        except OSError:
            print(f"Error: Input file \"{filename}\" could not be found or access denied!", file=sys.stderr)
            if not args.keep_going:
                return 1
            else:
                continue

    files_visited.update(pending_files)

    while True:
        try:
            filename = pending_files.popleft()
        except IndexError:
            break
        try:
            result = process_file(filename, not args.no_filter)
            if result:
                results.append({ _KEY_FILENAME: filename, _KEY_DEPENDENCIES: result })
                if args.recursive:
                    pending_files.extend([ path for path in [ library[_KEY_PATH] for library in result if _KEY_PATH in library ] if path not in files_visited ])
                    files_visited.update(pending_files)
        except Exception as e:
            print(f"Error: {str(e)}", file=sys.stderr)
            if not args.keep_going:
                return 1
            else:
                continue

    if args.json_format:
        json.dump(results[0] if len(results) == 1 else results, sys.stdout, indent=(None if args.no_indent else 3))
    else:
        if len(results) > 0:
            for result in results:
                print(result[_KEY_FILENAME])
                for library in result[_KEY_DEPENDENCIES]:
                    imported_symbols = library[_KEY_SYMBOLS]
                    print(f"\t{library[_KEY_SONAME]} => {library[_KEY_PATH]}" if library[_KEY_SONAME] else f"\tunresolved symbols:")
                    for symbol in imported_symbols:
                        print(f"\t\t{symbol[_KEY_NAME]} [{symbol[_KEY_TYPE]}]")
        else:
            print("No dependencies have been found!", file=sys.stderr)

    return 0

if __name__ == '__main__':
    sys.exit(main())
