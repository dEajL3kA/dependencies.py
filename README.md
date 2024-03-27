# Dependencies.py

A simple Python script to dump the shared library dependencies of a given executable file or shared library.

Unlike tools like **`ldd`** or **`nm`** alone, this script tries to track which *specific* symbols (e.g. functions) are imported from each shared library file! Internally, the script invokes `ldd` to detect the required libraries and `nm` to detect the imported or exported symbols of each file. These information are then combined to build the dependency graph.

## Platform support

This is script requires Python 3 and was written exclusively for the Linux platform. No non-standard Python packages are required. It is assumed that the Linux command-line tools **`file`**, **`ldd`** and **`nm`** are available.

## Usage

This script is used as follows:

```
python3 dependencies.py [OPTIONS] input [input ...]

positional arguments:
  input              The input file(s) to be processed

optional arguments:
  -h, --help         show this help message and exit
  -r, --recursive    Recursively analyze shared library dependencies
  -j, --json-format  Generate JSON compatible output
  --no-indent        Do not indent the generated JSON (requires --json-format)
  --no-filter        Do not ignore certain unresolved symbols
  --keep-going       Keep going, even when an error is encountered
```

## Output

The first column (no indentation) shows the binary, i.e. executable file or shared library, whose dependencies are being analyzed. The second column (first level of indentation) shows the "soname" and the resolved path of each shared library that the current binary (column #1) depends on. Finally, the third column (second level of indentation) shows the individual symbols that are imported ***by*** the current binary (column #1) ***from*** the current shared library (column #2). Symbols that need to be imported by the binary but that could **not** be traced back to one of the required shared libraries, if any, are shown under the `unresolved symbols` label.

**Note:** By default, only *direct* dependencies are tracked. Use the `--recursive` option to enable *recursive* mode! This will automatically analyze the dependencies of each required shared library that has been found.

## Example

In this example, the dependencies of the `/usr/bin/cp` program are dumped (output was shortened):

```
$ ./dependencies.py --recursive /usr/bin/cp
/usr/bin/cp
	libselinux.so.1 => /lib/x86_64-linux-gnu/libselinux.so.1
		context_free@LIBSELINUX_1.0
		context_new@LIBSELINUX_1.0
		context_str@LIBSELINUX_1.0
		...
		mode_to_security_class@LIBSELINUX_1.0
		security_compute_create@LIBSELINUX_1.0
		setfscreatecon@LIBSELINUX_1.0
	libacl.so.1 => /lib/x86_64-linux-gnu/libacl.so.1
		acl_delete_def_file@ACL_1.0
		acl_entries@ACL_1.0
		acl_free@ACL_1.0
		...
		acl_get_tag_type@ACL_1.0
		acl_set_fd@ACL_1.0
		acl_set_file@ACL_1.0
	libattr.so.1 => /lib/x86_64-linux-gnu/libattr.so.1
		attr_copy_check_permissions@ATTR_1.1
		attr_copy_fd@ATTR_1.1
		attr_copy_file@ATTR_1.1
	libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6
		__assert_fail@GLIBC_2.2.5
		__ctype_b_loc@GLIBC_2.3
		__ctype_get_mb_cur_max@GLIBC_2.2.5
		...
		pcre2_pattern_info_8
		pcre2_serialize_decode_8
		pcre2_serialize_get_number_of_codes_8
	libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6
		__asprintf_chk@GLIBC_2.8
		__assert_fail@GLIBC_2.2.5
		__ctype_b_loc@GLIBC_2.3
		...
		umount@GLIBC_2.2.5
		uname@GLIBC_2.2.5
		write@GLIBC_2.2.5
	unresolved symbols:
		__tls_get_addr@GLIBC_2.3
/lib/x86_64-linux-gnu/libacl.so.1
	libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6
		__cxa_finalize@GLIBC_2.2.5
		__errno_location@GLIBC_2.2.5
		__stack_chk_fail@GLIBC_2.4
		...
		strncmp@GLIBC_2.2.5
		strncpy@GLIBC_2.2.5
		strtol@GLIBC_2.2.5
/lib/x86_64-linux-gnu/libattr.so.1
	libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6
		__cxa_finalize@GLIBC_2.2.5
		__errno_location@GLIBC_2.2.5
		__stack_chk_fail@GLIBC_2.4
		...
		strndup@GLIBC_2.2.5
		strspn@GLIBC_2.2.5
		syscall@GLIBC_2.2.5
/lib/x86_64-linux-gnu/libpcre2-8.so.0
	libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6
		__ctype_b_loc@GLIBC_2.3
		__ctype_tolower_loc@GLIBC_2.3
		__ctype_toupper_loc@GLIBC_2.3
		...
		pthread_mutex_unlock@GLIBC_2.2.5
		strchr@GLIBC_2.2.5
		sysconf@GLIBC_2.2.5
```

## License

Copyright (c) 2024 "dEajL3kA" &lt;Cumpoing79@web.de&gt;  
This work has been released under the MIT license. See [LICENSE.txt](LICENSE.txt) for details!