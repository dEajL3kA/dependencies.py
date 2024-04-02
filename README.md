# Dependencies.py

A simple Python script to dump the shared library dependencies of a given executable file or shared library.

Unlike tools like **`ldd`** or **`nm`** alone, this script tries to track which *specific* symbols (e.g. functions) are imported from each shared library file! Internally, the script invokes `ldd` to detect the required libraries and `nm` to detect the imported or exported symbols of each file. These information are then combined to build the dependency graph.

## Platform support

This is script requires Python 3.7+ and was written for Linux and ✱BSD platforms. No non-standard Python packages are required. It is assumed that the standard command-line tools **`file`**, **`ldd`** and **`nm`** are available.

## Usage

This script is used as follows:

```
python3 /path/to/dependencies.py [OPTIONS] input [input ...]

positional arguments:
  input              The input file(s) to be processed

options:
  -h, --help         show this help message and exit
  -r, --recursive    Recursively analyze shared library dependencies
  -j, --json-format  Generate JSON compatible output
  -t, --print-types  Output the type of each resolved symbol
  -v, --version      Print the script version
  --no-preload       Ignore pre-loaded libraries (only relevant with --recursive)
  --no-filter        Do not ignore "weak" unresolved symbols
  --keep-going       Keep going, even when an error is encountered
  --indent INDENT    Set number of spaces to use for indentation (default: 3)
```

## Output

The first column (no indentation) shows the binary, i.e. executable file or shared library, whose dependencies are being analyzed. The second column (first level of indentation) shows the "soname" and the resolved path of each shared library that the current binary (column #1) depends on. Finally, the third column (second level of indentation) shows the individual symbols that are imported ***by*** the current binary (column #1) ***from*** the current shared library (column #2). Symbols that need to be imported by the binary but that could **not** be traced back to one of the required shared libraries, if any, are shown under the `unresolved symbols` label.

**Note:** By default, only *direct* dependencies are tracked. Use the `--recursive` option to enable *recursive* mode! This will automatically analyze the dependencies of each required shared library that has been found.

## Example

In this example, the dependencies of the `/usr/bin/pandoc` program are dumped (output was shortened):

```
$ ./dependencies -rt /usr/bin/pandoc
/usr/bin/pandoc
   libm.so.6 => /usr/lib/x86_64-linux-gnu/libm.so.6
      acos@GLIBC_2.2.5 [W]
      acosf@GLIBC_2.2.5 [W]
      acosh@GLIBC_2.2.5 [W]
      ...
      tanf@GLIBC_2.2.5 [W]
      tanh@GLIBC_2.2.5 [W]
      tanhf@GLIBC_2.2.5 [W]
   libz.so.1 => /usr/lib/x86_64-linux-gnu/libz.so.1.2.11
      adler32 [T]
      crc32 [T]
      deflate [T]
      ...
      inflateReset [T]
      inflateSetDictionary [T]
      zlibVersion [T]
   libpcre.so.3 => /usr/lib/x86_64-linux-gnu/libpcre.so.3.13.3
      pcre_compile [T]
      pcre_config [T]
      pcre_exec [T]
      pcre_fullinfo [T]
      pcre_version [T]
   libcmark-gfm.so.0.29.0.gfm.3 => /usr/lib/x86_64-linux-gnu/libcmark-gfm.so.0.29.0.gfm.3
      cmark_find_syntax_extension [T]
      cmark_get_default_mem_allocator [T]
      cmark_llist_append [T]
      ...
      cmark_render_latex [T]
      cmark_render_man [T]
      cmark_render_xml [T]
   libcmark-gfm-extensions.so.0.29.0.gfm.3 => /usr/lib/x86_64-linux-gnu/libcmark-gfm-extensions.so.0.29.0.gfm.3
      cmark_gfm_core_extensions_ensure_registered [T]
      cmark_gfm_extensions_get_table_alignments [T]
      cmark_gfm_extensions_get_table_columns [T]
   libgmp.so.10 => /usr/lib/x86_64-linux-gnu/libgmp.so.10.4.1
      __gmpn_add [T]
      __gmpn_add_1 [T]
      __gmpn_and_n [T]
      ...
      __gmpz_powm_sec [T]
      __gmpz_probab_prime_p [T]
      __gmpz_sizeinbase [T]
   libc.so.6 => /usr/lib/x86_64-linux-gnu/libc.so.6
      __assert_fail@GLIBC_2.2.5 [T]
      __ctype_b_loc@GLIBC_2.3 [T]
      __ctype_tolower_loc@GLIBC_2.3 [T]
      ...
      waitpid@GLIBC_2.2.5 [W]
      write@GLIBC_2.2.5 [W]
      writev@GLIBC_2.2.5 [W]
   libffi.so.8 => /usr/lib/x86_64-linux-gnu/libffi.so.8.1.0
      ffi_call@LIBFFI_BASE_8.0 [T]
      ffi_closure_alloc@LIBFFI_CLOSURE_8.0 [T]
      ffi_closure_free@LIBFFI_CLOSURE_8.0 [T]
      ...
      ffi_type_uint64@LIBFFI_BASE_8.0 [R]
      ffi_type_uint8@LIBFFI_BASE_8.0 [R]
      ffi_type_void@LIBFFI_BASE_8.0 [R]
/usr/lib/x86_64-linux-gnu/libm.so.6
   libc.so.6 => /usr/lib/x86_64-linux-gnu/libc.so.6
      __assert_fail@GLIBC_2.2.5 [T]
      __cxa_finalize@GLIBC_2.2.5 [T]
      __stack_chk_fail@GLIBC_2.4 [T]
      ...
      fwrite@GLIBC_2.2.5 [W]
      qsort@GLIBC_2.2.5 [T]
      stderr@GLIBC_2.2.5 [D]
   ld-linux-x86-64.so.2 => /usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2
      _rtld_global_ro@GLIBC_PRIVATE [D]
/usr/lib/x86_64-linux-gnu/libz.so.1.2.11
   libc.so.6 => /usr/lib/x86_64-linux-gnu/libc.so.6
      __cxa_finalize@GLIBC_2.2.5 [T]
      __errno_location@GLIBC_2.2.5 [T]
      __snprintf_chk@GLIBC_2.3.4 [T]
      ...
      strerror@GLIBC_2.2.5 [T]
      strlen@GLIBC_2.2.5 [i]
      write@GLIBC_2.2.5 [W]
/usr/lib/x86_64-linux-gnu/libpcre.so.3.13.3
   libc.so.6 => /usr/lib/x86_64-linux-gnu/libc.so.6
      __ctype_b_loc@GLIBC_2.3 [T]
      __ctype_tolower_loc@GLIBC_2.3 [T]
      __ctype_toupper_loc@GLIBC_2.3 [T]
      ...
      strlen@GLIBC_2.2.5 [i]
      strncmp@GLIBC_2.2.5 [i]
      sysconf@GLIBC_2.2.5 [W]
/usr/lib/x86_64-linux-gnu/libcmark-gfm.so.0.29.0.gfm.3
   libc.so.6 => /usr/lib/x86_64-linux-gnu/libc.so.6
      __assert_fail@GLIBC_2.2.5 [T]
      __cxa_finalize@GLIBC_2.2.5 [T]
      __fprintf_chk@GLIBC_2.3.4 [T]
      ...
      strcpy@GLIBC_2.2.5 [i]
      strlen@GLIBC_2.2.5 [i]
      strncmp@GLIBC_2.2.5 [i]
/usr/lib/x86_64-linux-gnu/libcmark-gfm-extensions.so.0.29.0.gfm.3
   libcmark-gfm.so.0.29.0.gfm.3 => /usr/lib/x86_64-linux-gnu/libcmark-gfm.so.0.29.0.gfm.3
      cmark_arena_pop [T]
      cmark_arena_push [T]
      cmark_consolidate_text_nodes [T]
      ...
      cmark_utf8proc_is_punctuation [T]
      cmark_utf8proc_is_space [T]
      cmark_utf8proc_iterate [T]
   libc.so.6 => /usr/lib/x86_64-linux-gnu/libc.so.6
      __assert_fail@GLIBC_2.2.5 [T]
      __ctype_tolower_loc@GLIBC_2.3 [T]
      __cxa_finalize@GLIBC_2.2.5 [T]
      ...
      strlen@GLIBC_2.2.5 [i]
      strncasecmp@GLIBC_2.2.5 [i]
      strstr@GLIBC_2.2.5 [i]
/usr/lib/x86_64-linux-gnu/libgmp.so.10.4.1
   libc.so.6 => /usr/lib/x86_64-linux-gnu/libc.so.6
      __ctype_b_loc@GLIBC_2.3 [T]
      __cxa_finalize@GLIBC_2.2.5 [T]
      __fprintf_chk@GLIBC_2.3.4 [T]
      ...
      strtol@GLIBC_2.2.5 [W]
      ungetc@GLIBC_2.2.5 [T]
      vfprintf@GLIBC_2.2.5 [T]
/usr/lib/x86_64-linux-gnu/libc.so.6
   ld-linux-x86-64.so.2 => /usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2
      __libc_enable_secure@GLIBC_PRIVATE [D]
      __libc_stack_end@GLIBC_2.2.5 [D]
      __nptl_change_stack_perm@GLIBC_PRIVATE [T]
      ...
      _dl_rtld_di_serinfo@GLIBC_PRIVATE [T]
      _rtld_global@GLIBC_PRIVATE [D]
      _rtld_global_ro@GLIBC_PRIVATE [D]
/usr/lib/x86_64-linux-gnu/libffi.so.8.1.0
   libc.so.6 => /usr/lib/x86_64-linux-gnu/libc.so.6
      __cxa_finalize@GLIBC_2.2.5 [T]
      __errno_location@GLIBC_2.2.5 [T]
      __getdelim@GLIBC_2.2.5 [T]
      ...
      sysconf@GLIBC_2.2.5 [W]
      unlink@GLIBC_2.2.5 [W]
      write@GLIBC_2.2.5 [W]
```

## License

Copyright (c) 2024 "dEajL3kA" &lt;Cumpoing79@web.de&gt;  
This work has been released under the MIT license. See [LICENSE.txt](LICENSE.txt) for details!
