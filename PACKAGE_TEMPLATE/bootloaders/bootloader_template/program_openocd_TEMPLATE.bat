@echo off
setlocal

set "OPENOCD=$openocd_executable"
set "OPENOCD_SCRIPTS=$openocd_scripts_directory"
set "FUSE_SCRIPT=$openocd_fuse_script"
set "DAPLINK_CONFIG=$openocd_daplink_config"
set "BOOTLOADER=$bootloader_path_forward"

echo Unlocking bootloader protection for $board_name...
"%OPENOCD%" -d2 -s "%OPENOCD_SCRIPTS%" -c "set bootprot $bootprot_unlock" -f "%FUSE_SCRIPT%"
if errorlevel 1 goto :error

echo Erasing the chip and programming $bootloader_filename...
"%OPENOCD%" -d2 -s "%OPENOCD_SCRIPTS%" -f "%DAPLINK_CONFIG%" -c "telnet_port disabled; init; reset halt; $$_FLASHDRIVER chip-erase; program {%BOOTLOADER%} verify reset; shutdown"
if errorlevel 1 goto :error

echo Restoring bootloader protection for $board_name...
"%OPENOCD%" -d2 -s "%OPENOCD_SCRIPTS%" -c "set bootprot $bootprot_lock" -f "%FUSE_SCRIPT%"
if errorlevel 1 goto :error

echo Successfully programmed $bootloader_filename.
exit /b 0

:error
set "EXIT_CODE=%ERRORLEVEL%"
echo Bootloader programming failed with exit code %EXIT_CODE%.
exit /b %EXIT_CODE%
