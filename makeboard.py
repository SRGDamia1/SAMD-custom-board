#!/usr/bin/env python3
import SAMDconfig
import os
import shutil

# Read the package configuration file
# this will also read all of the board config files and store them in the SAMDPackage object
print("Reading board config...")
package = SAMDconfig.SAMDPackage("board_data")

# %%
# get the latest version of the UF2 repo and check that it is compatible with the board configuration
print("\nChecking for the latest version of the Adafruit UF-2 Repo")
package.check_uf2_version()

# setup build directory and move there all source files
print("\nCopying sources to build directory...")
package.setup_build_directory()

# Customize the various template files
print("\nCustomizing all template files")
package.write_platform_templates()

print("\nCloning the current Adafruit UF2 repo")
package.clone_uf2_repo()

# %%
# write config files for bootloader
print("\nCreating config files for the board bootloaders")
for board in package.boards_config:
    bootloader_config_dir = (
        f"{package.build_directory}/uf2-samdx1/boards/{board.d['board_name']}"
    )
    os.mkdir(bootloader_config_dir)
    board.write_board_mk(bootloader_config_dir)
    board.write_board_config(bootloader_config_dir, package.d)

# %%
# build bootloader
print("\nBuilding bootloader...")
package.build_bootloaders()

# copy built bootloader into the package
for board in package.boards_config:
    bootloader_dest = f"{package.package_directory}/bootloaders/{board.name}"
    os.makedirs(f"{package.package_directory}/bootloaders", exist_ok=True)
    os.mkdir(bootloader_dest)

    # copy all of the built files into the bootloader directory
    src_files = os.listdir(board.d["bootloader_dir"])
    for file_name in src_files:
        full_file_name = os.path.join(board.d["bootloader_dir"], file_name)
        if (
            os.path.isfile(full_file_name)
            and board.d["bootloader_buildname"] in full_file_name
            and "map" not in full_file_name
            and "update" not in full_file_name
        ):
            shutil.copy(full_file_name, bootloader_dest)
            new_filename = file_name.replace(
                board.d["bootloader_buildname"],
                board.d["bootloader_versioned_name"],
            )
            # rename from the UF2 version set by make to the configured version
            print(
                f"Renaming from {os.path.join(bootloader_dest, file_name)} to {os.path.join(bootloader_dest, new_filename)}"
            )
            os.rename(
                f"{os.path.join(bootloader_dest, file_name)}",
                f"{os.path.join(bootloader_dest, new_filename)}",
            )

# # copy all of the built files into the bootloader directory
# src_files = os.listdir(board.d['bootloader_dir'])
# for file_name in src_files:
#     full_file_name = os.path.join(board.d['bootloader_dir'], file_name)
#     if os.path.isfile(full_file_name):
#         shutil.copy(full_file_name, bootloader_dest)
# also, copy the main bin to the top of build directory
# shutil.copy(f"{board.d['bootloader_dir']}/{board.d['bootloader_buildname']}.bin", board.build_directory)

# compressing directory into zip archive
print("\nCompressing the package archive")
package.package_archive()

# create json file
print("\nCreating json index file")
package.write_index_json()


# %%
# clean up build directory by removing all cloned and copied files
print("\nCleaning cloned and copied files from the build directory")
package.clean_build_directory()


# %%
print("\nAll done!")
