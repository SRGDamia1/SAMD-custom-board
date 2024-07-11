# Installing your newly built bootloader

Here are two different sets of instructions for installing the bootloader onto a SAMD device using either OpenOCD and a DAPLink Device or a J-Link Edu Mini and J-Flash Lite.

The paths are written for windows. You should change your username in the path from `{user}` to your own user directory and the `{build_dir}` path to the output build directory for your built bootloader.

## Install the Bootloader with OpenOCD and a DAPLink Device (ie, Particle Debugger)

From: <https://wiki.seeedstudio.com/Flashing-Arduino-Bootloader-DAPLink/>

- Connect the DAPLink device to both your PC and your target board
- Power your target board

- Open a terminal for OpenOCD (OpenOCD acts as the GDB server)
- Navigate to the the installation directory of OpenOCD within the Arduino15 directory
  - `cd "C:\Users\{user}\AppData\Local\Arduino15\packages\arduino\tools\openocd\0.11.0-arduino2\bin"`
- Run the OpenOCD with specific scripts:
  - `./openocd -s ..\share\openocd\scripts\ -f "{build_dir}\{version}\scripts\openocd\daplink_samd51.cfg"`
- If all goes well, you should see a message that the programmer is listening on port 3333 for gdb connections

- Open a *second* terminal for the GDB client session
- Navigate to the installation director of arm-none-eabi-gcc
  - `cd "C:\Users\{user}\AppData\Local\Arduino15\packages\adafruit\tools\arm-none-eabi-gcc\9-2019q4\bin"`
- Start the GDB Client
  - `./arm-none-eabi-gdb`
- Once within the GDB, connect with OpenOCD server using:
  - `target extended-remote localhost:3333`
- Reset the and halt the chip
  - `monitor reset halt`
  - `monitor halt`
- Fully erase the chip
  - `monitor atsame5 chip-erase` or `at91samd chip-erase`
- Set the bootloader elf file as the active file:
  - **NOTE**: *On windows, you need to flip the direction of the slashes from `\` to `/` for this command!*
  - `file "{build_dir}/{version}/bootloaders/{board_name}/bootloader-{board_name}-{uf2_version}.elf"`
- Flash the bootloader to the target:
  - `load`
- Reset the target device by pressing reset buttons and you should see that COM appeared

## Install the Bootloader with J-Link Edu Mini and J-Flash Lite

- Install the J-Link software package, including J-Flash Lite from <https://www.segger.com/downloads/jlink/>
- Connect the J-Link Edu Mini device to your PC
- If desired, update the firmware on your J-Link by using the J-Link Configurator program
- Connect the J-Link Edu mini to and your target board with the JTAG cable
  - Make sure that the JTAG cable is conneced so that the red wire is at the top near where the "1" is printed on the J-Link Edu Mini.  The cable can connect either way (stupid design) so you need to make sure it's connected correctly.
- Power your target board
- Open J-Flash **Lite**
  - J-Flash requires a full licence, J-Flash Lite does not.
- Select your specific chip as the device, "SWD" as the interface, "4000 kHz" as the speed, and hit "OK"
- Select the compiled bootloader bin (`{build_dir}\bootloader-{board_name}-{uf2_version}.bin`) file as the data file
  - Set the Prog. Address to 0x00000000
- (Optional) Erase any previous bootloader by hitting the "Erase" button
- Hit "Program Device"
