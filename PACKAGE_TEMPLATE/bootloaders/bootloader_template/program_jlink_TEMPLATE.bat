@echo off
setlocal

if not defined JLINK_EXE set "JLINK_EXE=JLink.exe"
set "COMMAND_FILE=%TEMP%\program_bootloader_${board_name}_%RANDOM%_%RANDOM%.jlink"
set "CLEAR_FUSES=$jlink_clear_fuses"
set "SET_FUSES=$jlink_set_fuses"
set "BOOTLOADER=$bootloader_path_windows"

if exist "%JLINK_EXE%" goto :jlink_found
where "%JLINK_EXE%" >nul 2>&1
if errorlevel 1 (
    echo Could not find JLink.exe. Add it to PATH or set JLINK_EXE to its full path.
    exit /b 1
)

:jlink_found
> "%COMMAND_FILE%" (
    echo loadfile "%CLEAR_FUSES%"
    echo r
    echo erase
    echo r
    echo loadfile "%BOOTLOADER%" 0
    echo r
    echo loadfile "%SET_FUSES%"
    echo r
    echo exit
)

echo Programming $bootloader_filename with J-Link Commander...
"%JLINK_EXE%" -device $chip_variant -if SWD -speed 4000 -autoconnect 1 -ExitOnError 1 -NoGui 1 -CommandFile "%COMMAND_FILE%"
set "EXIT_CODE=%ERRORLEVEL%"
del /q "%COMMAND_FILE%" >nul 2>&1

if not "%EXIT_CODE%"=="0" echo Bootloader programming failed with exit code %EXIT_CODE%.
if "%EXIT_CODE%"=="0" echo Successfully programmed $bootloader_filename.
exit /b %EXIT_CODE%
