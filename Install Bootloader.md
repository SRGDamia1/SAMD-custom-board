# Installing your newly built bootloader

Here are two different sets of instructions for installing the bootloader onto a SAMD device using either OpenOCD and a DAPLink Device or a J-Link Edu Mini and J-Flash Lite.

The paths are written for windows. You should change your username in the path from `{user}` to your own user directory and `{repo_path}` to wherever you have this repo installed.

## Fuses and Bootloader Protection

Atmel boards feature protections to prevent the all or sections of the chip from being written.
For a novice user, it's much safer to keep the bootloader locked so they cannot accidently overwrite it.
BUT, to write a bootloader, you must unlock the BOOTPROT region for programming.
The settings for the bootloader protection are in sections of memory commonly called "fuses", though you may also see them labeled as "configuration bits" or "user rows."
There is very little documentation online on how to set the fuses - and most of what is available only applies to the simpler SAMD21.

For these instructions, I've sourced information from the [datasheets](https://onlinedocs.microchip.com/oxy/GUID-F5813793-E016-46F5-A9E2-718D8BCED496-en-US-13/GUID-864A0628-0E75-4AFA-969D-A18360C6A381.html?hl=nvmctrl%2Caddr), [Adafruit UF2 bootloader source](https://github.com/adafruit/uf2-samdx1), [Adafruit's instructions for installing a bootloader](https://learn.adafruit.com/installing-circuitpython-on-samd21-boards/installing-the-uf2-bootloader), [SEEED Studio's DAP Link instructions](https://wiki.seeedstudio.com/Flashing-Arduino-Bootloader-DAPLink/), and [Tom Magnier's HACKADAY.IO instructions for SAMD bootloaders](https://hackaday.io/page/5997-programming-a-samd-bootloader-using-jlink-linux).

- The BOOTPROT region is protected against write, erase, or Chip-Erase operations.
- The NVM User Row (ie, "fuses" or "configuration bits") mapping is available in [section 9.4 of the SAM D5x/E5x Family Data Sheet](https://onlinedocs.microchip.com/oxy/GUID-F5813793-E016-46F5-A9E2-718D8BCED496-en-US-13/GUID-3F814D93-0756-4B17-804B-7F76FA821673.html?hl=nvm%2Cuser%2Cpage) and [section 10.3.1 of the SAM D21/DA1 Family Data Sheet](https://ww1.microchip.com/downloads/aemDocuments/documents/MCU32/ProductDocuments/DataSheets/SAM-D21-DA1-Family-Data-Sheet-DS40001882H.pdf)
  - `0x41004000` is the base address of the NVMCTRL peripheral
    - `0x00804000` is the memory offset of Fuse 0/USER_WORD_0
    - Every other fuse is offset from the first fuse by 32 bits (4 bytes)
    - The SAMD21 has 2 user fuses and they can be written in individual memory writes
    - The SAMD51 has 5 user fuses
      - Writes to the user rows must be done as an entire 512 byte "page" that includes the 5 fuses and other factory calibration data.
- For a **SAMD21**, the size of the BOOTPROT region is defined in bits 0:2 of the 32-bit USER_WORD_0
- For a **SAMD51**, the size of the BOOTPROT region is defined in bits 26:29 of the 32-bit USER_WORD_0
  - This size is given by the following formula (15-BOOTPROT)*8KB.
    - Set to 0x0F (15) for 0 kb protected
      - (15-15)*8 = 0
    - Set to 0x0D (13) for 16kb protected (the SAMD51 UF2 bootloader is 16kb)
      - (15-13)*8 = 16
  - On device startup, the value set for the BOOTPROT in USER_WORD_0 is loaded into NVMCTRL.STATUS bits 11:8

The OpenOCD script for the fuses on the SAMD21 is a lightly modified and heavily documented version of the [fuse setting script](https://github.com/adafruit/uf2-samdx1/blob/master/scripts/fuses.tcl) from the UF2 bootloader.
The OpenOCD script from the fuses on the SAMD51 started with the SAMD21 script, but had to be re-written almost completely to account for the larger user pages and the fact that individual 32-bit registers cannot be written, only entire 512 byte pages.

## Install the Bootloader with OpenOCD and a DAPLink Device (ie, Particle Debugger)

### Start up Open OCD

- Connect the DAPLink device to both your PC and your target board
- Power your target board
- Open a terminal for OpenOCD (OpenOCD acts as the GDB server)
- Within the terminal, chage directories to the the installation directory of OpenOCD within the Arduino15 directory
  - `cd "C:\Users\{user}\AppData\Local\Arduino15\packages\arduino\tools\openocd\0.11.0-arduino2\bin"`
- Use this terminal for all of the remaining steps!

### Unlock the BOOTPROT "fuses"

- Run the following OpenOCD command:
  - SAMD21: `./openocd -d2 -s ..\share\openocd\scripts\ -c "set bootprot 0x7" -f "{repo_path}\build\current\scripts\fuses\openocd\samd21_fuses.tcl"`
  - SAMD51: `./openocd -d2 -s ..\share\openocd\scripts\ -c "set bootprot 0x0F" -f "{repo_path}\build\current\scripts\fuses\openocd\samd51_fuses.tcl"`

Explanation of Command/Arguments:

- `./openocd` runs OpenoCD
- `-d2` sets the debugging level to 2
- `-s ..\share\openocd\scripts\` sets the directory to search for config files and scripts
- `-c "set bootprot {value}"` runs the command to set the value for boot protection
  - Values to **UNLOCK** the fuses
    - `set bootprot 0x7` for SAMD-21 [0x7, 0b111 = 0 bytes protected (not locked)]
    - `set bootprot 0x0F` for SAMD-51 [0x0F (15) for 0 kb protected]
  - Values to **LOCK** the fuses
    - `set bootprot 0x2` for SAMD-21 [0x2, 0b010 = 8KB protected (the size of the UF2 SAMD21 bootloader)]
    - `set bootprot 0x0D` for SAMD-51 [0x0D (13) for 16kb protected (the SAMD51 UF2 bootloader is 16kb)]
  - NOTE: *Use capital letters for the hex values:* `0x0F` **NOT** `0x0f`
- `-f "{repo_path}\build\current\scripts\fuses\openocd\samd51_fuses.tcl"` runs the file with the fuse changing script
- See: https://openocd.org/doc/html/Running.html#Running

#### Unlock and Factory Reset the Bootloader Fuses
- Run the following OpenOCD command:
  - SAMD21: `./openocd -d2 -s ..\share\openocd\scripts\ -c "set forceupdate 1; set bootprot 0x7" -f "{repo_path}\build\current\scripts\fuses\openocd\samd21_fuses.tcl"`
  - SAMD51: `./openocd -d2 -s ..\share\openocd\scripts\ -c "set forceupdate 1; set bootprot 0x0F" -f "{repo_path}\build\current\scripts\fuses\openocd\samd51_fuses.tcl"`

### Write the Bootloader

- Run OpenOCD with these commands to program the board
  - ```./openocd -d2 -s ..\share\openocd\scripts\ -f "{repo_path}\build\current\scripts\openocd\daplink_samdx1.cfg" -c "telnet_port disabled; init; reset halt; `$_FLASHDRIVER chip-erase; program {repo_path}/build/current/bootloaders/{board_name}/bootloader-{board_name}-{board_version}-{uf2_version}.bin verify reset; shutdown"```

Explanation of Command/Arguments:

- `./openocd` runs OpenoCD
- `-d2` sets the debugging level to 2
- `-s ..\share\openocd\scripts\` sets the directory to search for config files and scripts
- `-f "..\scripts\openocd\daplink_samdx1.cfg"` runs the configuration setup for DAPLink connection to the board
- `-c ... runs the commands to program the board
  - `telnet_port disabled` temporarily disables telnet communication with OpenOCD while we're programming
  - `init` initializes OpenOCD and the TCL language
  - `reset halt` resets the board and halts any further program execution while programming the bootloader
  - `$_FLASHDRIVER chip-erase` erases any lingering programs and bootloaders on the board
    - NOTE: To run this command on Windows, you must escape the `$`  in the command by adding an extra backtick (`)
  - `program {bootloader}.bin verify reset` actually writes the bootloader, verifies that it was written correctly, and resets the board
    - **NOTE**: *On windows, you need to flip the direction of all slashes in the path of the bootloader from `\` to `/` for this command!*
  - `shutdown` shuts down OpenOCD

### Re-Lock the BOOTPROT "fuses"

This is essentially the same procedure as un-locking the boot protection fuses, except we set the value of the boot protection to the size of the bootloader instead of 0.
See the locking section for a detailed explanation of the commands

- Run the following OpenOCD command:
  - SAMD21: `./openocd -d2 -s ..\share\openocd\scripts\ -c "set bootprot 0x2" -f "{repo_path}\build\current\scripts\fuses\openocd\samd21_fuses.tcl"`
  - SAMD51: `./openocd -d2 -s ..\share\openocd\scripts\ -c "set bootprot 0x0D" -f "{repo_path}\build\current\scripts\fuses\openocd\samd51_fuses.tcl"`

## Install the Bootloader with OpenOCD and a DAPLink Device (v2)

### Do everything with a Single OpenOCD Command

> [!Warning]
> This uses the "bootloader" command within OpenOCD.
> The developers of the UF2 bootloader consider this command to be "buggy" and don't recommend using it.
> See the [UF2 ReadMe](https://github.com/adafruit/uf2-samdx1) for more information.

- Connect the DAPLink device to both your PC and your target board
- Power your target board, if your DAPLink device cannot provide power
- Within the terminal, chage directories to the the installation directory of OpenOCD within the Arduino15 directory
  - `cd "C:\Users\{user}\AppData\Local\Arduino15\packages\arduino\tools\openocd\0.11.0-arduino2\bin"`
- Run the following OpenOCD command:
  - SAMD51: ```./openocd -d2 -s ..\share\openocd\scripts\ -f "{repo_path}\build\current\scripts\openocd\daplink_samdx1.cfg" -c "telnet_port disabled; init; reset halt; `$_FLASHDRIVER bootloader 0; `$_FLASHDRIVER chip-erase; reset; program {repo_path}/build/current/bootloaders/{board_name}/bootloader-{board_name}-{board_version}-{uf2_version}.bin verify reset; reset halt; `$_FLASHDRIVER bootloader 16384; shutdown"```
  - SAMD21: ```./openocd -d2 -s ..\share\openocd\scripts\ -f "{repo_path}\build\current\scripts\openocd\daplink_samdx1.cfg" -c "telnet_port disabled; init; reset halt; `$_FLASHDRIVER bootloader 0; `$_FLASHDRIVER chip-erase; program {repo_path}/build/current/bootloaders/{board_name}/bootloader-{board_name}-{board_version}-{uf2_version}.bin verify reset; reset halt; `$_FLASHDRIVER bootloader 8192; shutdown"```

Explanation of Command/Arguments:

- `./openocd` runs OpenoCD
- `-d2` sets the debugging level to 2
- `-s ..\share\openocd\scripts\` sets the directory to search for config files and scripts
- `-f "..\scripts\openocd\daplink_samdx1.cfg"` runs the configuration setup for DAPLink connection to the board
- `-c ... runs the commands to program the board
  - `telnet_port disabled` temporarily disables telnet communication with OpenOCD while we're programming
  - `init` initializes OpenOCD and the TCL language
  - `reset halt` resets the board and halts any further program execution while programming the bootloader
  - `$_FLASHDRIVER bootloader 0` sets the bootloader protection to 0 bytes.
    - NOTE: To run this command on Windows, you must escape the `$`  in the command by adding an extra backtick (`)
  - `$_FLASHDRIVER chip-erase` erases any lingering programs and bootloaders on the board
    - NOTE: To run this command on Windows, you must escape the `$`  in the command by adding an extra backtick (`)
  - `program {bootloader}.bin verify reset` actually writes the bootloader, verifies that it was written correctly, and resets the board
    - **NOTE**: *On windows, you need to flip the direction of all slashes in the path of the bootloader from `\` to `/` for this command!*
  - `reset halt` once again resets the board and halts any further program execution while programming the bootloader
  - `$_FLASHDRIVER bootloader #` sets the bootloader protection to to the size of the bootloader.
    - NOTE: To run this command on Windows, you must escape the `$`  in the command by adding an extra backtick (`)
  - `shutdown` shuts down OpenOCD

## Install the Bootloader with J-Link Edu Mini and J-Flash Lite

See [Tom Magnier's HACKADAY.IO instructions for SAMD bootloaders](https://hackaday.io/page/5997-programming-a-samd-bootloader-using-jlink-linux) for a walk-through with screenshots. That page is the primary source for these instructions

WARNING: Using this procedure will reset all fuses to their default values!  If you've customized your fuses and you want to only change the BOOTPROT fuse, use the OpenOCD method.

TODO: It should be possible to make a J-Link script to read and write the fuses as is done in the OpenOCD method.
This would be significanly better (though much more complex) than hard-writing a "mot" memory file with the factory settings for the user words/user pages.

### Install J-Link Software Package

- Install the J-Link software package, including J-Flash Lite from <https://www.segger.com/downloads/jlink/>
- Connect the J-Link Edu Mini device to your PC
- If desired, update the firmware on your J-Link by using the J-Link Configurator program

- Connect the J-Link Edu mini to and your target board with the JTAG cable
  - Make sure that the JTAG cable is conneced so that the red wire is at the top near where the "1" is printed on the J-Link Edu Mini.  The cable can connect either way (stupid design) so you need to make sure it's connected correctly.
- Power your target board

### Connect J-Link to Target

- Start JLink.exe
- Connect to the microcontroller. You have to specify the device type, SWD interface and you can use the default interface speed.
  - Type `connect` to start the connection process
  - Enter `ATSAMD21G18` for the device (or whatever chip you have)
  - Enter `S` for SWD interface
  - Enter `4000` for the speed (or just hit enter, because that's the default)

### Unlock the BOOTPROT "fuses"

- Load the memory file that will clear the boot loader protection fuse
  - for SAMD21: `loadfile {repo_path}\fuses\jlink\SAMD21_clear_BOOTPROT.mot`
  - for SAMD51: `loadfile {repo_path}\fuses\jlink\SAMD51_clear_BOOTPROT.mot`
- Reset the target
  - `r`

### Write the Bootloader

- Erase any old firmware and bootloader
  - `erase`
- Reset the target
  - `r`
- Upload the bootloader file to address 0
  - `loadbin "{repo_path}\build\current\bootloaders\{board_name}\bootloader-{board_name}-{board_version}-{uf2_version}.bin",0`
- Reset the target
  - `r`

### Re-Lock the BOOTPROT "fuses"

- Load the memory file that will set the boot loader protection fuse to 8kb
  - for SAMD21: `loadfile {repo_path}\fuses\jlink\SAMD21_set_BOOTPROT_8k.mot`
  - for SAMD51: `loadfile {repo_path}\fuses\jlink\SAMD51_set_BOOTPROT_16k.mot`
- Reset the target
  - `r`
