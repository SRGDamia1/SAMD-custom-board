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
      - writes to the user rows must be done as an entire 512 byte "page" that includes the 5 fuses and other blank and factory written regions.
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

NOTE: If you are using a SAMD/E-51 board and you are 100% certain that your BOOTPROT size is properly set for the UF2 bootloader, you can skip this.

- Open the file `{repo_path}\fuses\openocd\samd21_fuses.tcl` or `{repo_path}\fuses\openocd\samd51_fuses.tcl` in any text editor.
- Within the tcl file, change the `set bootprot` statement (line 8) to the correct value for 0kb protected
  - `set bootprot 0x7` for SAMD-21
  - `set bootprot 0x0F` for SAMD-51
    - NOTE: *Use capital letters for the hex valuez:* `0x0F` **NOT** `0x0f`
- Within the tcl file, also change the chip name in line 16 to the correct value for your board
  - ie `set CHIPNAME samd51n19a` for the SAMD51N19A on the Stonefly
- Save the changes to your tcl file
- Run OpenOCD with your modified fuse writing script:
  - `./openocd -s ..\share\openocd\scripts\ -f "{repo_path}\fuses\openocd\samd51_fuses.tcl"`

### Write the Bootloader

- Run OpenOCD with specific scripts:
  - `./openocd -s ..\share\openocd\scripts\ -f "{repo_path}\build\0.0.1\scripts\openocd\daplink_samd51.cfg"`
- If all goes well, you should see a message that the programmer is listening on port 3333 for gdb connections

- Open a *second* terminal for the GDB client session
- Navigate to the installation director of arm-none-eabi-gcc
  - `cd "C:\Users\{user}\AppData\Local\Arduino15\packages\adafruit\tools\arm-none-eabi-gcc\9-2019q4\bin"`
- Start the GDB Client
  - `./arm-none-eabi-gdb`
- Once within the GDB, connect with OpenOCD server using:
  - `target extended-remote localhost:3333`
- For almost all of the following commands, **we use the "monitor" command to pass the command from the GDB client to the OpenOCD server.**
- Reset the and halt the chip.
  - `monitor init`
  - `monitor reset halt`
  - `monitor halt`
- For a *SAMD51*, if the BOOTPROT fuse is properly set to the correct size for your bootloader, you can *temporarily* disable it just for a single erase and write using the command:
  - If you unlocked the fuses using the steps above, don't use this!
  - `monitor memwrite16 [expr 0x41004000 + 0x04]  [expr 0xA500 | 0x1a]`
  - `set ((NVMCTRL *)0x41004000UL)->CTRLB.reg = (0xA5 << 8) | 0x1a`
    - 0x41004000 = NVMCTRL (Start address of NVM control registers)
    - 0x04 = Offset of NVMCTRL_CTRLB from NVMCTRL (CTRLB.reg)
    - 0xa5 = Position of Execution Key wihtin NVMCTRL_CTRLB
    - 0x1a = Value of command to set STATUS.BPDIS; Boot loader protection is discarded until CBPDIS is issued or next start-up sequence
- Fully erase the chip
  - For SAMD21: `monitor at91samd chip-erase`
  - For SAMD51: `monitor atsame5 chip-erase`
- Program the bin file:
  - **NOTE**: *On windows, you need to flip the direction of the slashes from `\` to `/` for this command!*
  - `monitor program "{repo_path}/build/bootloader-{board_name}-{uf2_version}" verify reset`
- Shutdown the OpenOCD server:
  - `monitor shutdown`
- Reset the target device by pressing reset buttons and you should see that a COM appeared
- Quit GDB
  - `quit` then `y`
- Close this second terminal.  Leave the OpenOCD terminal open.

### Re-Lock the BOOTPROT "fuses"

NOTE: If you are using a SAMD/E-51 board and you skipped unlocking fuses, you can skip this too.

This is essentially the same procedure as un-locking the boot protection fuses, except we set the value of the boot protection to the size of the bootloader instead of 0.

- Open the file `{repo_path}\fuses\openocd\samd21_fuses.tcl` or `{repo_path}\fuses\openocd\samd51_fuses.tcl` in any text editor.
- Within the tcl file, change the `set bootprot` statement (line 8) to the correct value for the size of the bootloader
  - `set bootprot 0x2` for 8kb protection for the SAMD-21
  - `set bootprot 0x0D` for 16kB protection on the SAMD-51
    - NOTE: *Use capital letters for the hex valuez:* `0x0D` **NOT** `0x0d`
- Save the changes to your tcl file
- Run OpenOCD with your modified fuse writing script:
  - `./openocd -s ..\share\openocd\scripts\ -f "{repo_path}\fuses\openocd\samd51_fuses.tcl"`

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

- Start JLinkExe
- Connect to the microcontroller. You have to specify the device type, SWD interface and you can use the default interface speed.
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
  - `loadbin "{repo_path}\build\bootloader-stonefly_m4-v3.16.0.bin",0`
- Reset the target
  - `r`

### Re-Lock the BOOTPROT "fuses"

- Load the memory file that will set the boot loader protection fuse to 8kb
  - for SAMD21: `loadfile {repo_path}\fuses\jlink\SAMD21_set_BOOTPROT_8k.mot`
  - for SAMD51: `loadfile {repo_path}\fuses\jlink\SAMD51_set_BOOTPROT_16k.mot`
- Reset the target
  - `r`
