
/*----------------------------------------------------------------------------
 *        Version Information
 *----------------------------------------------------------------------------*/
// clang-format off
/** Package major version number (X.x.x) */
#define ${package_define_name}_VERSION_MAJOR $package_version_major
/** Package minor version number (x.X.x) */
#define ${package_define_name}_VERSION_MINOR $package_version_minor
/** Patch version number (x.x.X) */
#define ${package_define_name}_VERSION_PATCH $package_version_patch

/** Board major version number (X.x.x) */
#define ${board_name_upper}_VERSION_MAJOR $board_version_major
/** Board minor version number (x.X.x) */
#define ${board_name_upper}_VERSION_MINOR $board_version_minor
/** Board patch version number (x.x.X) */
#define ${board_name_upper}_VERSION_PATCH $board_version_patch

/**
 * Macro to convert version number into an integer
 *
 * To be used in comparisons, such as ${board_name_upper}_VERSION >= ${board_name_upper}_VERSION_VAL(4, 0, 0)
 */
#define ${package_define_name}_VERSION_VAL(major, minor, patch)((major << 16) | (minor << 8) | (patch))
#define ${board_name_upper}_VERSION_VAL(major, minor, patch)((major << 16) | (minor << 8) | (patch))

/**
 * Current Board version, as an integer
 *
 * To be used in comparisons, such as ${board_name_upper}_VERSION >= ${board_name_upper}_VERSION_VAL(4, 0, 0)
 */
#define ${package_define_name}_VERSION ${package_define_name}_VERSION_VAL(${package_define_name}_VERSION_MAJOR, ${package_define_name}_VERSION_MINOR, ${package_define_name}_VERSION_PATCH)
#define ${board_name_upper}_VERSION ${board_name_upper}_VERSION_VAL(${board_name_upper}_VERSION_MAJOR, ${board_name_upper}_VERSION_MINOR, ${board_name_upper}_VERSION_PATCH)
// clang-format on
