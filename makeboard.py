#!/usr/bin/env python3
import SAMDconfig
import os
import shutil

# Read all board configuration data
print("Reading board config...")
board = SAMDconfig.SAMDconfig("board_data/board-config.ini")

print("\nChecking for the latest version of the Adafruit UF-2 Repo")
board.check_uf2_version()

# setup buidl directory and move there all source files
print("\nCopying sources to build directory...")
board.setup_build_directory("build")

# Customize the various template files
print("\nCustomizing all template files")
board.write_platform_templates()

print("\nCloning the current Adafruit UF2 repo")
board.clone_uf2_repo()

# write config files for bootloader
print("\nCreating config files for the board bootloader")
bootloader_config_dir = f"{board.build_directory}/uf2-samdx1/boards/{board.name}"
os.mkdir(bootloader_config_dir)
board.write_board_mk(bootloader_config_dir)
board.write_board_config(bootloader_config_dir)

# build bootloader
print("\nBuilding bootloader...")
board.build_bootloader()

# copy built bootloader into the package
bootloader_dest = f"{board.package_directory}/bootloaders/{board.name}"
os.mkdir(f"{board.package_directory}/bootloaders")
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
            board.d["bootloader_buildname"], board.d["bootloader_versioned_name"]
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
board.package_archive()

# create json file
print("\nCreating json index file")
board.write_index_json()

print("\nCleaning cloned and copied files from the build directory")
board.clean_build_directory()
