# Arduino board support package

The **$package_name** package contains Arduino board support files for SAM/SAMD boards developed by $vendor_name_long.
It is maintained by $maintainer_name; contact [$vendor_email](mailto:$vendor_email).
See [$info_url]($info_url) for project information and [$help_url]($help_url) for help.

This package is version $package_version, built on $build_date.
Its source is maintained at [$package_repository]($package_repository).
Package archives are published from [$package_archive_url]($package_archive_url).
The index for the Arduino Board Manager is available at [$package_index_url]($package_index_url).

All boards in this package compile with a compile-time package-version macro of  `$package_define_name`.
You can use this macro in your sketches to check the package version at compile time, for example:

```cpp
#if defined($package_define_name)
  Serial.println($package_define_name);
#endif
```

You can also check the package version at runtime by using the the macro:

```cpp
#if ${package_define_name}_VERSION >= ${package_define_name}_VERSION_VAL(4, 0, 0)
  Serial.println(${package_define_name}_VERSION);
#endif
```

For each individual board, you can check the compiled variant version at compile time using the the same macro code with the board-specific define name in place of the package define name.

Boards included in this package:

$board_list

It relies on Adafruit's SAMD board support package; thus, users need to have that package installed.
Please see installation instructions here: https://learn.adafruit.com/add-boards-arduino-v164/setup

This package was built using tools from [Sara Damiano's fork](https://github.com/SRGDamia1/SAMD-custom-board) of [shurik179's SAMD-custom-board repository](https://github.com/shurik179/SAMD-custom-board).
