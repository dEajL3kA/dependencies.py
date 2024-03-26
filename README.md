# Dependencies.py

A simple Python script to dump the shared library dependencies of a given executable file or shared library.

Unlike tools like **`ldd`** or **`nm`** alone, this script tries to track which *specific* symbols (e.g. functions) are imported from each shared library file! Internally, the script invokes `ldd` to detect the required libraries and `nm` to detect the imported or exported symbols of each file. These information are then combined to build the dependency graph.

## Platform support

This is script requires Python 3 and was written exclusively for the Linux platform. No non-standard Python packages are required. It is assumed that the Linux command-line tools **`file`**, **`ldd`** and **`nm`** are available.

## Usage

This script is used as follows:

```
dependencies.py [-h] --input INPUT [INPUT ...] [--json-format] [--no-indent] [--keep-going]

options:
  -h, --help            show this help message and exit
  --input INPUT [INPUT ...]
                        The executable file(s) to be processed
  --json-format         Generate JSON compatible output
  --no-indent           Do not indent the generated JSON (requires --json-format)
  --keep-going          Keep going, even when an error is encountered
```

## Example

In this example, the dependencies of the `/usr/bin/cp` program are dumped:

```
$ ./dependencies.py --input /usr/bin/cp
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
		utimensat@GLIBC_2.6
		utimes@GLIBC_2.2.5
		write@GLIBC_2.2.5
	unresolved symbols:
		_ITM_deregisterTMCloneTable
		_ITM_registerTMCloneTable
		__gmon_start__
```

## License

Copyright (c) 2024 "dEajL3kA" &lt;Cumpoing79@web.de&gt;  
This work has been released under the MIT license. See [LICENSE.txt](LICENSE.txt) for details!
