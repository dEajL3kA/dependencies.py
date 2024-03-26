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

from os.path import realpath
from typing import Set, Dict, List, Tuple

# Dictionary keys
_KEY_DEPENDENCIES = 'dependencies'
_KEY_FILENAME = 'filename'
_KEY_PATH = 'path'
_KEY_SONAME = 'soname'
_KEY_SYMBOLS = 'symbols'

# ============================================================================
# Functions
# ============================================================================

# ~~~~~~~~~~~~~~~~~
# Start sub-process
# ~~~~~~~~~~~~~~~~~

def start_process(args: List[str]) -> subprocess.Popen:
    return subprocess.Popen(args, stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdout=subprocess.PIPE, env={'LC_ALL': 'C.UTF-8', 'LANG': 'C.UTF-8'})

# ~~~~~~~~~~~~~~~~~~~~~~
# Detect executable file
# ~~~~~~~~~~~~~~~~~~~~~~

def detect_executable(filename: str) -> bool:
    is_executable = False
    regex = re.compile(r'application\s*/\s*x-((pie-)?executable|sharedlib)\s*;\s*charset\s*=\s*binary\s*$')
    try:
        with start_process(['/usr/bin/file', '-i', filename]) as proc:
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

def detect_dependencies(filename: str) -> Tuple[List[str], Dict[str, str]]:
    dependencies, dependency_paths = [], {}
    regex = re.compile(r'^\s*(.+?)\s+=>\s+(.+?)(\s*\(0x[^\)]+\))?\s*$')
    try:
        with start_process(['/usr/bin/ldd', filename]) as proc:
            for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
                match = regex.search(line)
                if match:
                    library, path = match.group(1), match.group(2)
                    if path != "not found":
                        dependencies.append(library)
                        dependency_paths[library] = path
            error_code = proc.wait()
            if error_code != 0:
                raise ValueError(f"Failed to detect dependencies! (error code: {error_code})")
    except OSError:
        raise ValueError("Failed to execute \"ldd\" program!")
    return (dependencies, dependency_paths)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Detect all imported/exported symbols
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def detect_symbols(filename: str, defined: bool) -> Set[str]:
    dynamic_symbols = set()
    regex_line = re.compile(r'^\s*([0-9a-zA-Z]+\s+)?[A-Za-z]\s+([^\s]+)\s*$')
    regex_name = re.compile(r'([^@\s]+)@@([^@\s]+)')
    try:
        with start_process(['/usr/bin/nm', '-D', '--defined-only' if defined else '--undefined-only', filename]) as proc:
            for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
                match = regex_line.search(line)
                if match:
                    name = match.group(2)
                    match = regex_name.search(name) if defined else None
                    if match:
                        dynamic_symbols.add(match.group(1))
                        dynamic_symbols.add(f"{match.group(1)}@{match.group(2)}")
                    else:
                        dynamic_symbols.add(name)
            error_code = proc.wait()
            if error_code != 0:
                raise ValueError(f"Failed to read symbol table! (error code: {error_code})")
    except OSError:
        raise ValueError("Failed to execute \"nm\" program!")
    return dynamic_symbols

# ============================================================================
# Process File
# ============================================================================

def process_file(filename: str) -> Tuple[List[Dict]]:
    if not detect_executable(filename):
        raise ValueError(f"Input file \"{filename}\" is not a supported executable file or shared library!")

    dependencies, dependency_paths = detect_dependencies(filename)
    if len(dependencies) < 1:
        raise ValueError("No shared library dependencies have been found!")

    imported = detect_symbols(filename, False)
    if len(imported) < 1:
        raise ValueError("No imported (unresolved) symbols have been found!")

    result, already_found = [], set()

    for library in dependencies:
        exported = detect_symbols(dependency_paths[library], True)
        library_resolved = set()
        for symbol in [name for name in exported if name not in already_found]:
            if symbol in imported:
                library_resolved.add(symbol)
                already_found.add(symbol)
        if len(library_resolved) > 0:
            result.append({ _KEY_SONAME: library, _KEY_PATH: dependency_paths[library], _KEY_SYMBOLS: sorted(library_resolved) })

    unresolved = [name for name in imported if name not in already_found]
    if len(unresolved) > 0:
        result.append({ _KEY_SONAME: None, _KEY_SYMBOLS: sorted(unresolved) })

    return result

# ============================================================================
# MAIN
# ============================================================================

def main() -> int:
    if not sys.platform.startswith('linux'):
        print(f"Sorry, this script must run on the Linux platform!", file=sys.stderr)
        return 1

    parser = argparse.ArgumentParser(description="Detects all symbols that an executable file (or shared library) imports from other shared libraries.")
    parser.add_argument('--input', action='store', nargs='+', required=True, help="The executable file(s) to be processed")
    parser.add_argument('--json-format', action='store_true', default=False, help="Generate JSON compatible output")
    parser.add_argument('--no-indent', action='store_true', default=False, help="Do not indent the generated JSON (requires --json-format)")
    parser.add_argument('--keep-going', action='store_true', default=False, help="Keep going, even when an error is encountered")

    args = parser.parse_args()

    for tool in ['file', 'ldd', 'nm']:
        if not os.access(f'/usr/bin/{tool}', os.R_OK | os.X_OK):
            print(f"Required tool \"/usr/bin/{tool}\" is not available or inaccessible!", file=sys.stderr)
            return 1

    results = []

    for filename in args.input:
        try:
            _filename = realpath(filename, strict=True)
        except OSError:
            print(f"Error: Input file \"{filename}\" could not be found!", file=sys.stderr)
            if not args.keep_going:
                return 1
            continue

        try:
            results.append({ _KEY_FILENAME: _filename, _KEY_DEPENDENCIES: process_file(_filename) })
        except Exception as e:
            print(f"Error: {str(e)}", file=sys.stderr)
            if not args.keep_going:
                return 1
            continue

    if args.json_format:
        json.dump(results[0] if len(results) == 1 else results, sys.stdout, indent=(None if args.no_indent else 3))
    else:
        for result in results:
            print(result[_KEY_FILENAME])
            for library in result[_KEY_DEPENDENCIES]:
                imported_symbols = library[_KEY_SYMBOLS]
                print(f"\t{library[_KEY_SONAME]} => {library[_KEY_PATH]}" if library[_KEY_SONAME] else f"\tunresolved symbols:")
                for symbol in imported_symbols:
                    print(f"\t\t{symbol}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
