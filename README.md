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
  --no-filter        Do not ignore "weak" unresolved symbols
  --no-indent        Do not indent the generated JSON (requires --json-format)
  --keep-going       Keep going, even when an error is encountered
```

## Output

The first column (no indentation) shows the binary, i.e. executable file or shared library, whose dependencies are being analyzed. The second column (first level of indentation) shows the "soname" and the resolved path of each shared library that the current binary (column #1) depends on. Finally, the third column (second level of indentation) shows the individual symbols that are imported ***by*** the current binary (column #1) ***from*** the current shared library (column #2). Symbols that need to be imported by the binary but that could **not** be traced back to one of the required shared libraries, if any, are shown under the `unresolved symbols` label.

**Note:** By default, only *direct* dependencies are tracked. Use the `--recursive` option to enable *recursive* mode! This will automatically analyze the dependencies of each required shared library that has been found.

## Example

In this example, the dependencies of the `/usr/bin/cp` program are dumped (output was shortened):

```
$ ./dependencies.py -r -t /usr/bin/cp
/usr/bin/cp
    libselinux.so.1 => /lib/x86_64-linux-gnu/libselinux.so.1
        context_free@LIBSELINUX_1.0 [T]
        context_new@LIBSELINUX_1.0 [T]
        context_str@LIBSELINUX_1.0 [T]
        context_type_get@LIBSELINUX_1.0 [T]
        ...
        matchpathcon@LIBSELINUX_1.0 [T]
        mode_to_security_class@LIBSELINUX_1.0 [T]
        security_compute_create@LIBSELINUX_1.0 [T]
        setfscreatecon@LIBSELINUX_1.0 [T]
    libacl.so.1 => /lib/x86_64-linux-gnu/libacl.so.1
        acl_delete_def_file@ACL_1.0 [T]
        acl_entries@ACL_1.0 [T]
        acl_free@ACL_1.0 [T]
        acl_from_mode@ACL_1.0 [T]
        ...
        acl_get_file@ACL_1.0 [T]
        acl_get_tag_type@ACL_1.0 [T]
        acl_set_fd@ACL_1.0 [T]
        acl_set_file@ACL_1.0 [T]
    libattr.so.1 => /lib/x86_64-linux-gnu/libattr.so.1
        attr_copy_check_permissions@ATTR_1.1 [T]
        attr_copy_fd@ATTR_1.1 [T]
        attr_copy_file@ATTR_1.1 [T]
    libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6
        __assert_fail@GLIBC_2.2.5 [T]
        __ctype_b_loc@GLIBC_2.3 [T]
        __ctype_get_mb_cur_max@GLIBC_2.2.5 [W]
        __cxa_atexit@GLIBC_2.2.5 [T]
        ...
        unlinkat@GLIBC_2.4 [T]
        utimensat@GLIBC_2.6 [W]
        utimes@GLIBC_2.2.5 [W]
        write@GLIBC_2.2.5 [W]
/lib/x86_64-linux-gnu/libselinux.so.1
    libpcre2-8.so.0 => /lib/x86_64-linux-gnu/libpcre2-8.so.0
        pcre2_code_free_8 [T]
        pcre2_compile_8 [T]
        pcre2_config_8 [T]
        pcre2_get_error_message_8 [T]
        ...
        pcre2_match_data_free_8 [T]
        pcre2_pattern_info_8 [T]
        pcre2_serialize_decode_8 [T]
        pcre2_serialize_get_number_of_codes_8 [T]
    libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6
        __asprintf_chk@GLIBC_2.8 [T]
        __assert_fail@GLIBC_2.2.5 [T]
        __ctype_b_loc@GLIBC_2.3 [T]
        __cxa_finalize@GLIBC_2.2.5 [T]
        ....
        umount2@GLIBC_2.2.5 [W]
        umount@GLIBC_2.2.5 [W]
        uname@GLIBC_2.2.5 [W]
        write@GLIBC_2.2.5 [W]
    ld-linux-x86-64.so.2 => /lib64/ld-linux-x86-64.so.2
        __tls_get_addr@GLIBC_2.3 [T]
/lib/x86_64-linux-gnu/libacl.so.1
    libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6
        __cxa_finalize@GLIBC_2.2.5 [T]
        __errno_location@GLIBC_2.2.5 [T]
        __stack_chk_fail@GLIBC_2.4 [T]
        chmod@GLIBC_2.2.5 [W]
        ...
        strlen@GLIBC_2.2.5 [i]
        strncmp@GLIBC_2.2.5 [i]
        strncpy@GLIBC_2.2.5 [i]
        strtol@GLIBC_2.2.5 [W]
/lib/x86_64-linux-gnu/libattr.so.1
    libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6
        __cxa_finalize@GLIBC_2.2.5 [T]
        __errno_location@GLIBC_2.2.5 [T]
        __stack_chk_fail@GLIBC_2.4 [T]
        dcgettext@GLIBC_2.2.5 [W]
        ...
        strncpy@GLIBC_2.2.5 [i]
        strndup@GLIBC_2.2.5 [W]
        strspn@GLIBC_2.2.5 [i]
        syscall@GLIBC_2.2.5 [T]
/lib/x86_64-linux-gnu/libc.so.6
    ld-linux-x86-64.so.2 => /lib64/ld-linux-x86-64.so.2
        __libc_enable_secure@GLIBC_PRIVATE [D]
        __libc_stack_end@GLIBC_2.2.5 [D]
        __nptl_change_stack_perm@GLIBC_PRIVATE [T]
        __tls_get_addr@GLIBC_2.3 [T]
        __tunable_get_val@GLIBC_PRIVATE [T]
        ...
        _dl_find_dso_for_object@GLIBC_PRIVATE [T]
        _dl_rtld_di_serinfo@GLIBC_PRIVATE [T]
        _rtld_global@GLIBC_PRIVATE [D]
        _rtld_global_ro@GLIBC_PRIVATE [D]
/lib/x86_64-linux-gnu/libpcre2-8.so.0
    libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6
        __ctype_b_loc@GLIBC_2.3 [T]
        __ctype_tolower_loc@GLIBC_2.3 [T]
        __ctype_toupper_loc@GLIBC_2.3 [T]
        __cxa_finalize@GLIBC_2.2.5 [T]
        ...
        pthread_mutex_lock@GLIBC_2.2.5 [T]
        pthread_mutex_unlock@GLIBC_2.2.5 [T]
        strchr@GLIBC_2.2.5 [i]
        sysconf@GLIBC_2.2.5 [W]
```

## License

Copyright (c) 2024 "dEajL3kA" &lt;Cumpoing79@web.de&gt;  
This work has been released under the MIT license. See [LICENSE.txt](LICENSE.txt) for details!
