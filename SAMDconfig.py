"""
Main class to keep configuration data for SAMD board
* Author(s): Alexander Kirillov
* Version: 4.0
"""

import os
import shutil
import stat
import configparser
import subprocess
import glob
from string import Template
import hashlib
import json
from datetime import date
import requests


# Cloning the uf2 directory as part of the build creates read-only files which rmtree cannot
# delete without a helper.
def remove_readonly(func, path, _):
    "Clear the readonly bit and reattempt the removal"
    os.chmod(path, stat.S_IWRITE)
    func(path)


class SAMDconfig:
    # constructor
    def __init__(self, filename):
        # dictionary containign all config data
        self.d = {}
        self.d["build_date"] = date.today().isoformat()
        # read all values from main sections of config file
        config_file = configparser.ConfigParser()
        config_file.read(filename)
        for s in ["hardware", "usb", "names", "paths"]:
            for key, value in config_file[s].items():
                self.d[key] = value

        # now, read additional options for the bootloader
        self.extras = {}
        for s in ["m4_usart_options", "bootloader_extras"]:
            for key, value in config_file[s].items():
                self.extras[key] = value

        # check for empty values
        self.check_missing_values(self.d)
        self.check_missing_values(self.extras)

        # define common properties
        self.name = self.d["board_name"]
        self.version = self.d["package_version"]
        self.chip_family = self.d["chip_family"]
        self.chip_variant = self.d["chip_variant"]
        self.is_samd51 = (self.d["chip_family"] == "SAMD51") or (
            self.d["chip_family"] == "SAME51"
        )

        # add MCU-specific parameters
        if self.chip_family == "SAMD21":
            self.d["flash_size"] = 262144
            self.d["data_size"] = 0
            self.d["offset"] = "0x2000"
            self.d["build_mcu"] = "cortex-m0plus"
            self.d["f_cpu"] = "48000000L"
            self.d["extra_flags"] = "-DARDUINO_SAMD_ZERO -DARM_MATH_CM0PLUS"
            self.d["openocdscript"] = "scripts/openocd/daplink_samd21.cfg"
        elif self.is_samd51:
            # SAMD51J20A, SAMD51P20A, and SAMD51N20A have 1032192 flash size (1024kB program memory size)
            if self.chip_variant in ["SAMD51J20A", "SAMD51P20A", "SAMD51N20A"]:
                self.d["flash_size"] = 1032192
            # other SAMD51's have 507904 flash size (512kB program memory size)
            else:
                self.d["flash_size"] = 507904
            self.d["data_size"] = 0
            self.d["offset"] = "0x4000"
            self.d["build_mcu"] = "cortex-m4"
            self.d["f_cpu"] = "120000000L"
            self.d["extra_flags"] = (
                "-D__SAMD51__ -D__FPU_PRESENT -DARM_MATH_CM4 -mfloat-abi=hard -mfpu=fpv4-sp-d16"
            )
            self.d["openocdscript"] = "scripts/openocd/daplink_samd51.cfg"
        else:
            raise RuntimeError("Invalid MCU family")

        # add extra GCC flags
        self.d["extra_flags"] += f" -D__{self.chip_variant}__"
        if "crystalless" in self.d.keys() and self.d["crystalless"] != "0":
            self.d["extra_flags"] += " -DCRYSTALLESS"

        # add extra extra GCC flags
        self.d["extra_flags"] += (
            " " + config_file["additional_build_flags"]["extra_extra_flags"]
        )

    def check_missing_values(self, dictionary):
        for key, value in dictionary.items():
            if not value:
                print(f"No value provided for {key}")
                raise RuntimeError("Missing configuration parameters")

    # reads template file, does all substitutions from the dictionary, saves result as destination
    # source and destination shoudl be filenames
    def process_file(self, source, destination):

        # open the template file
        with open(source, "r", encoding="UTF-8") as template_file:
            original = template_file.read()

        # make substitutions
        new_data = Template(original).substitute(self.d)

        # write the new file
        with open(destination, "w", encoding="UTF-8") as dest_file:
            dest_file.write(new_data)

        # delete the template file
        os.remove(source)

    def setup_build_directory(self, dirname):
        self.build_directory = dirname
        self.package_directory = f"{dirname}/{self.version}"
        # remove old build directory, if it exists
        if os.path.exists(dirname):
            print("Removing old build directory")
            shutil.rmtree(dirname, onerror=remove_readonly)
        # copy the template directory into the build directory
        shutil.copytree("PACKAGE_TEMPLATE", self.package_directory)

        # clone the latest version of the uf2-samdx1 repo into the build directory
        # shutil.copytree("uf2-samdx1", f"{self.build_directory}/uf2-samdx1")
        print("Checking the tag of the latest release of Adafruit's uf2 repo...")
        response = requests.get(
            "https://api.github.com/repos/adafruit/uf2-samdx1/releases/latest"
        )
        latest_release_tag = response.json()["tag_name"]
        self.d["uf2_version_tag"] = latest_release_tag
        print(
            f"The latest release of Adafruit's uf2 repo is tag {latest_release_tag}, published {response.json()['published_at']}"
        )
        print("Cloning Adafruit's uf2 repo...")
        with open(
            f"{self.build_directory}/bootloader_build_log.txt", "w", encoding="UTF-8"
        ) as logfile:
            command = f"git clone --depth 1 --branch {latest_release_tag} https://github.com/adafruit/uf2-samdx1.git {self.build_directory}/uf2-samdx1"
            git_process = subprocess.run(
                command,
                shell=True,
                stdout=logfile,
                stderr=subprocess.STDOUT,
                text=True,
            )
            if git_process.returncode:
                print(
                    "Cloning Adafruit uf2 repo failed. Please see the log file for details"
                )
            else:
                print("Successfully cloned latest Adafruit uf2 repo")

        # select which board variant template directory to use -
        # There are different linker scripts depending on the chip and memory size
        variants_dir = self.package_directory + "/variants"
        board_variant = f"{variants_dir}/{self.name}"
        if self.chip_family == "SAMD21":
            # rename one of template directories and delete two others
            shutil.move(variants_dir + "/TEMPLATE_SAMD21", board_variant)
            shutil.rmtree(variants_dir + "/TEMPLATE_SAMD51")
            shutil.rmtree(variants_dir + "/TEMPLATE_SAMD51P20A")

        # SAMD boards with 1024kB Flash/256kB SRAM
        elif self.chip_variant in ["SAMD51J20A", "SAMD51P20A", "SAMD51N20A"]:
            # rename one of template directories and delete two others
            shutil.move(variants_dir + "/TEMPLATE_SAMD51P20A", board_variant)
            shutil.rmtree(variants_dir + "/TEMPLATE_SAMD51")
            shutil.rmtree(variants_dir + "/TEMPLATE_SAMD21")
        # Remaining SAMD boards with 512kB Flash/192kB SRAM
        else:
            # rename one of template directories and delete two others
            shutil.move(variants_dir + "/TEMPLATE_SAMD51", board_variant)
            shutil.rmtree(variants_dir + "/TEMPLATE_SAMD21")
            shutil.rmtree(variants_dir + "/TEMPLATE_SAMD51P20A")

        # move the hand written variants files into the board variant directory
        shutil.copy2("board_data/variant.cpp", board_variant)
        shutil.copy2("board_data/variant.h", board_variant)

    # creates script files for J-Link and OpenOCD
    # these are needed to write the bootloader onto the board and for debugging
    def write_ocd_scripts(self):
        # Select which script directory to use for J-Link and OpenOCD
        scripts_dir = self.package_directory + "/scripts"
        # create the scripts directory
        os.makedirs(scripts_dir, exist_ok=True)
        os.makedirs(f"{scripts_dir}/jlink", exist_ok=True)
        os.makedirs(f"{scripts_dir}/jlink/{self.chip_family.lower()}", exist_ok=True)
        os.makedirs(f"{scripts_dir}/openocd", exist_ok=True)

        # write the J-Link debug json
        debug_custom = {
            "servertype": "jlink",
            "device": self.chip_variant,
            "interface": "SWD",
            "serverpath": "JLinkGDBServer",
        }
        jlink_debug_file = (
            f"{scripts_dir}/jlink/{self.chip_family.lower()}/debug_custom.json"
        )
        print(f"Writing J-Link debug profile to {jlink_debug_file}")
        with open(jlink_debug_file, "w", encoding="UTF-8") as json_file:
            json.dump(debug_custom, json_file, indent=2)

        jlink_ocd_cfg = f"{scripts_dir}/openocd/jlink_{self.chip_family.lower()}.cfg"
        daplink_ocd_cfg = (
            f"{scripts_dir}/openocd/daplink_{self.chip_family.lower()}.cfg"
        )
        for file, source in zip(
            [jlink_ocd_cfg, daplink_ocd_cfg], ["jlink", "cmsis-dap"]
        ):
            with open(file, "w", encoding="UTF-8") as ocd_script:
                # write header
                ocd_script.write("#\n#  Arduino SAMD51 OpenOCD script.\n#\n\n")
                # set the interface source
                ocd_script.write(f"source [find interface/{source}.cfg]\n")
                # select SWD as the transport
                ocd_script.write("transport select swd\n\n")
                # set the chip name
                ocd_script.write(
                    f"# chip name\nset CHIPNAME {self.d['chip_variant'].lower()}\n\n"
                )
                # set the source script
                if self.chip_family == "SAMD21":
                    ocd_script.write("source [find target/at91samdXX.cfg]\n")
                else:
                    ocd_script.write("source [find target/atsame5x.cfg]\n")

    # creates boards.txt, platform.txt and README.md files, by processing template files in package directory
    # these are used by the Arduino IDE
    def write_boards_txt(self):
        # if necessary, add entries for cache and speed menus
        self.d["menu_cache"] = ""
        self.d["menu_speed"] = ""
        if self.is_samd51:
            # cache menu
            cache_prefix = f"{self.name}.menu.cache"
            self.d["menu_cache"] += f"{cache_prefix}.on = Enabled\n"
            self.d[
                "menu_cache"
            ] += f"{cache_prefix}.on.build.cache_flags=-DENABLE_CACHE\n"
            self.d["menu_cache"] += f"{cache_prefix}.off=Disabled\n"
            self.d["menu_cache"] += f"{cache_prefix}.off.build.cache_flags=\n"
            # speed menu
            speed_prefix = f"{self.name}.menu.speed"
            self.d["menu_speed"] += f"{speed_prefix}.120=120 MHz (standard)\n"
            self.d["menu_speed"] += f"{speed_prefix}.120.build.f_cpu=120000000L\n"
            self.d["menu_speed"] += f"{speed_prefix}.150=150 MHz (overclock)\n"
            self.d["menu_speed"] += f"{speed_prefix}.150.build.f_cpu=150000000L\n"
            self.d["menu_speed"] += f"{speed_prefix}.180=180 MHz (overclock)\n"
            self.d["menu_speed"] += f"{speed_prefix}.180.build.f_cpu=180000000L\n"
            self.d["menu_speed"] += f"{speed_prefix}.200=200 MHz (overclock)\n"
            self.d["menu_speed"] += f"{speed_prefix}.200.build.f_cpu=200000000L\n"

        # substitute all values in the template board.txt file
        self.process_file(
            f"{self.package_directory}/boards_TEMPLATE.txt",
            f"{self.package_directory}/boards.txt",
        )
        # substitute all values in the template platfotm.txt file
        self.process_file(
            f"{self.package_directory}/platform_TEMPLATE.txt",
            f"{self.package_directory}/platform.txt",
        )
        self.process_file(
            f"{self.package_directory}/README_TEMPLATE.md",
            f"{self.package_directory}/README.md",
        )

    # creates board.mk file in given directory
    # this is needed to make/build the bootloader
    def write_board_mk(self, dest_directory):
        print(f"Writing board.mk file to {dest_directory}/board.mk")
        with open(f"{dest_directory}/board.mk", "w", encoding="UTF-8") as board_mk:
            board_mk.write("CHIP_FAMILY = " + self.d["chip_family"].lower() + "\n")
            board_mk.write("CHIP_VARIANT = " + self.d["chip_variant"] + "\n")

    # creates board_config.h file in given directory
    # this is for the Arduino IDE
    def write_board_config(self, dest_directory):
        print(f"Writing board_config.h file to {dest_directory}/board_config.h")
        with open(
            f"{dest_directory}/board_config.h", "w", encoding="UTF-8"
        ) as board_config:
            board_config.write("#ifndef BOARD_CONFIG_H\n")
            board_config.write("#define BOARD_CONFIG_H\n\n")
            board_config.write(
                '#define VENDOR_NAME      "' + self.d["vendor_name_long"] + '"\n'
            )
            board_config.write(
                '#define PRODUCT_NAME     "' + self.d["board_name_long"] + '"\n'
            )
            board_config.write(
                '#define VOLUME_LABEL     "' + self.d["volume_label"] + '"\n'
            )
            board_config.write(
                '#define INDEX_URL        "' + self.d["info_url"] + '"\n\n'
            )
            board_config.write("#define USB_VID          " + self.d["usb_vid"] + "\n")
            board_config.write("#define USB_PID          " + self.d["usb_pid"] + "\n")
            board_id = self.chip_variant + "-" + self.d["board_define_name"] + "-v0"
            board_config.write('#define BOARD_ID         "' + board_id + '"\n\n')
            if self.d["crystalless"]:
                board_config.write("#define CRYSTALLESS      1\n\n")
            if "led_pin" in self.d:
                board_config.write(
                    "#define LED_PIN          " + self.d["led_pin"] + "\n\n"
                )
            if "board_neopixel_pin" in self.d:
                board_config.write(
                    "#define BOARD_NEOPIXEL_PIN   "
                    + self.d["board_neopixel_pin"]
                    + "\n"
                )
                board_config.write(
                    "#define BOARD_NEOPIXEL_COUNT   "
                    + self.d["board_neopixel_count"]
                    + "\n\n"
                )
            if "board_rgbled_clock_pin" in self.d:
                board_config.write(
                    "#define BOARD_RGBLED_CLOCK_PIN   "
                    + self.d["board_rgbled_clock_pin"]
                    + "\n"
                )
                board_config.write(
                    "#define BOARD_RGBLED_DATA_PIN   "
                    + self.d["board_rgbled_data_pin"]
                    + "\n\n"
                )

            # now, add extras
            for key, value in self.extras.items():
                padded_key = key.ljust(27).upper()
                board_config.write(f"#define {padded_key} {value}\n")
            board_config.write("#endif\n")

    # creates board_name.json file in given directory
    # this is for PlatformIO
    def write_board_json(self):
        board_json = {
            "name": self.d["board_name_long"],
            "url": self.d["info_url"],
            "vendor": self.d["vendor_name_long"],
            "frameworks": ["arduino"],
            "build": {
                "arduino": {"ldscript": "flash_with_bootloader.ld"},
                "core": "adafruit",
                "cpu": "cortex-m4",
                "extra_flags": self.d["extra_flags"].split(" "),
                "f_cpu": "120000000L",
                "hwids": [[self.d["usb_vid"], self.d["usb_pid"]]],
                "mcu": self.chip_variant.lower(),
                "system": "samd",
                "usb_product": self.d["board_name_long"],
                "variant": self.d["board_name"],
            },
            "upload": {
                "disable_flushing": True,
                "native_usb": True,
                "protocol": "sam-ba",
                "protocols": ["sam-ba", "jlink", "atmel-ice"],
                "require_upload_port": True,
                "use_1200bps_touch": True,
                "wait_for_upload_port": True,
            },
            "debug": {
                "jlink_device": self.chip_variant.lower(),
                "openocd_chipname": f"at91{self.chip_variant.lower()}",
                "openocd_target": (
                    "at91samdXX" if self.chip_family == "SAMD21" else "atsame5x"
                ),
                "svd_path": f"{self.chip_variant}.svd",
            },
        }

        # add MCU-specific parameters
        if self.chip_family == "SAMD21":
            # set the RAM and offset sizes
            board_json["upload"]["maximum_ram_size"] = 32768
            board_json["upload"]["maximum_size"] = 262144
            board_json["upload"]["offset_address"] = "0x2000"
        elif self.is_samd51:
            # enable the cache
            board_json["build"]["extra_flags"].append("-DENABLE_CACHE")
            # remove the duplicate flags added by default by PlatformIO
            board_json["build"]["extra_flags"] = [
                flag
                for flag in board_json["build"]["extra_flags"]
                if flag not in ["-mfloat-abi=hard", "-mfpu=fpv4-sp-d16"]
            ]
            # SAMD51J20A, SAMD51P20A, and SAMD51N20A have 1032192 flash size (1024kB program memory size)
            if self.chip_variant in ["SAMD51J20A", "SAMD51P20A", "SAMD51N20A"]:
                # set the RAM and offset sizes
                board_json["upload"]["maximum_ram_size"] = 262144
                board_json["upload"]["maximum_size"] = 1048576
                board_json["upload"]["offset_address"] = "0x4000"
            # other SAMD51's have 507904 flash size (512kB program memory size)
            else:
                # set the RAM and offset sizes
                board_json["upload"]["maximum_ram_size"] = 196608
                board_json["upload"]["maximum_size"] = 524288
                board_json["upload"]["offset_address"] = "0x4000"
        # now save to json
        pio_boards_json_name = (
            self.build_directory
            + "/"
            + self.d["vendor_name"]
            + "_"
            + self.d["board_name"]
            + ".json"
        )
        with open(pio_boards_json_name, "w", encoding="UTF-8") as boards_json:
            json.dump(board_json, boards_json, indent=2)

    # gets all necessary paths for GCC and make and adds them to PATH
    # returns environment with these paths
    def get_paths(self):
        new_env = os.environ.copy()
        # find GCC included with Adafruit SAMD package
        gcc_tool_path = (
            new_env["HOME"]
            + "/"
            + self.d["arduino15"]
            + "/packages/adafruit/tools/arm-none-eabi-gcc"
        )
        # e.g. /Users/shurik/Library/Arduino15/packages/adafruit/tools/arm-none-eabi-gcc
        if not os.path.exists(gcc_tool_path):
            raise RuntimeError(
                "Couldn't find arm-none-eabi-gcc. Make sure you have installed Adafruit SAMD boards package!"
            )
        # now look for latest version.
        # we do not use just listdir since we want to make sure we do not include dotfiles
        gcc_versions = sorted(glob.glob(gcc_tool_path + "/*"))
        last_gcc_version = gcc_versions[-1]
        gcc_path = f"{last_gcc_version}/bin"
        print(f"Found GCC compiler at {gcc_path}")
        # add the paths to PATH env variable
        if "make_path" in self.d:
            if not os.path.exists(os.path.join(self.d["make_path"], "make.exe")):
                raise RuntimeError("Couldn't find make in the make_path directory!")
            new_env["PATH"] = os.pathsep.join(
                [new_env["PATH"], gcc_path, self.d["make_path"]]
            )
            print("Found GNU Make in specified make_path")
        else:
            new_env["PATH"] = os.pathsep.join([new_env["PATH"], gcc_path])
        return new_env

    def update_make_for_windows(self):
        print("Tweaking the make file for Windows")
        replacements = {
            # fix the mkdir to the windows version (no -p)
            "-@mkdir -p $(BUILD_PATH)": 'if not exist "$(BUILD_PATH)" mkdir "$(BUILD_PATH)"',
            # fix quotes around the echo to the version base file
            'echo "#define UF2_VERSION_BASE \\"$(UF2_VERSION_BASE)\\""> $@': 'echo #define UF2_VERSION_BASE "$(UF2_VERSION_BASE)"> $@',
            # call python as python not as python 3
            "python3 ": "python ",
            # because we've just modified this make file, the repo will be dirty; ignore this dirt
            "git describe --dirty --always --tags": "git describe --always --tags",
        }

        os.rename("Makefile", "archive_Makefile")
        with open("archive_Makefile") as infile, open("Makefile", "w") as outfile:
            i = 1
            for line in infile:
                # print(i, line)
                for src, target in replacements.items():
                    # print(src)
                    # print(src in line)
                    line = line.replace(src, target)
                outfile.write(line)
                i += 1

    def build_bootloader(self):
        # first, get paths
        new_env = self.get_paths()
        os.chdir("build/uf2-samdx1")
        if self.d["build_os"].lower() == "windows":
            self.update_make_for_windows()
        # run make to build bootloader
        print("Starting GNU make...")
        with open("../bootloader_build_log.txt", "a", encoding="UTF-8") as logfile:
            command = f"make BOARD={self.name} VERSION={self.version}"
            make_process = subprocess.run(
                command,
                shell=True,
                env=new_env,
                stdout=logfile,
                stderr=subprocess.STDOUT,
                text=True,
            )
            if make_process.returncode:
                print("Making bootloader failed. Please see the log file for details")
            else:
                print("Successfully built bootloader")

        # copy built bootloader
        os.chdir("../..")
        bootloader_dir = f"{self.build_directory}/uf2-samdx1/build/{self.name}"
        bootloader_basename = f"bootloader-{self.name}-{self.d['uf2_version_tag']}"
        return (bootloader_dir, bootloader_basename)

    # compress already constructed package directory into a zip archive and
    # record archive size and SHA256 checksum
    def package_archive(self):
        zip_archive = shutil.make_archive(
            f"{self.build_directory}/{self.name}-{self.version}",
            "zip",
            root_dir=self.build_directory,
            base_dir=self.version,
        )
        archive_size = os.path.getsize(zip_archive)
        # compute hash:
        with open(zip_archive, "rb") as f:
            bytes = f.read()  # read entire file as bytes
            hash = hashlib.sha256(bytes).hexdigest()

        print(
            f"Created package archive, size {archive_size} bytes,\n SHA256 hash: {hash}"
        )
        # add the info to dictionary
        self.d["archive_filename"] = f"{self.name}-{self.version}.zip"
        self.d["archive_size"] = archive_size
        self.d["archive_checksum"] = hash

    # write json index file
    def write_index_json(self):
        # see structure specifications here: https://arduino.github.io/arduino-cli/0.35/package_index_json-specification/
        # let's create the current version of samd platform
        samd_current = {
            "name": self.d["package_name"],
            "architecture": "samd",
            "version": self.d["package_version"],
            "category": "Contributed",
            "url": "FIXME",
            "archiveFileName": self.d["archive_filename"],
            "checksum": "SHA-256:" + self.d["archive_checksum"],
            "size": self.d["archive_size"],
            "boards": [{"name": self.d["board_name_long"]}],
            "toolsDependencies": [],
        }

        # create the package structure
        package = {
            "name": self.d["vendor_name"],
            "maintainer": self.d["vendor_name_long"],
            "websiteURL": self.d["info_url"],
            "help": {"online": self.d["help_url"]},
            "email": self.d["vendor_email"],
            "platforms": [samd_current],
            "tools": [],
        }
        # FIXME: deal wiht previous versions
        packages = {"packages": [package]}
        # now save to json
        indexfile_name = (
            self.build_directory + "/package_" + self.d["vendor_name"] + "_index.json"
        )
        with open(indexfile_name, "w", encoding="UTF-8") as indexfile:
            json.dump(packages, indexfile, indent=2)

    def clean_build_directory(self):
        # remove cloned repo
        if os.path.exists(f"{self.build_directory}/uf2-samdx1"):
            shutil.rmtree(f"{self.build_directory}/uf2-samdx1", onerror=remove_readonly)
