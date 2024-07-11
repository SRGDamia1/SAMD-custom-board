#!/usr/bin/env python3
import SAMDconfig
import os
import shutil

# Read all board configuration data
print("Reading board config...")
board = SAMDconfig.SAMDconfig("board_data/board-config.ini")

# setup buidl directory and move there all source files
print("Copying sources to build directory...")
board.setup_build_directory("build")

# write config files for bootloader
print("Creating config files for the board bootloader")
bootloader_config_dir = f"{board.build_directory}/uf2-samdx1/boards/{board.name}"
print(f"bootloader_config_dir {bootloader_config_dir}")
os.mkdir(bootloader_config_dir)
board.write_board_mk(bootloader_config_dir)
board.write_board_config(bootloader_config_dir)

# build bootloader
print("Building bootloader...")
bootloader_dir, bootloader_basename = board.build_bootloader()

# copy built bootloader into the package
bootloader_dest = f"{board.package_directory}/bootloaders/{board.name}"
os.mkdir(f"{board.package_directory}/bootloaders")
os.mkdir(bootloader_dest)
# copy all of the built files into the bootloader directory
src_files = os.listdir(bootloader_dir)
for file_name in src_files:
    full_file_name = os.path.join(bootloader_dir, file_name)
    if os.path.isfile(full_file_name):
        shutil.copy(full_file_name, bootloader_dest)
# also, copy the main bin to the top of build directory
shutil.copy(f"{bootloader_dir}/{bootloader_basename}.bin", board.build_directory)

# add bootloader filename to dictionary
board.d["bootloader_filename"] = f"{bootloader_basename}.bin"

# create boards.txt, platform.txt, README.md
print("Writing boards.txt file")
board.write_boards_txt()

# compressing directory into zip archive
board.package_archive()

# create json file
print("Creating json index file")
board.write_index_json()

# create platformio board json file
print("Creating PlatformIO board json file")
board.write_board_json()

print("Cleaning cloned and copied files from the build directory")
board.clean_build_directory()
