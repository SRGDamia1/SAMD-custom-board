# change forceupdate to 1 to update the fuses to factory default values specified below
set forceupdate 0

# Default value for Fuse 0 (User Row / USER_WORD_0)
# 0xD8E0C7FF = 0b11011000111000001100011111111111
# 2:0 BOOTPROT, default = 7, 0b111 (0 bytes protected) (see datasheet table 22-2 for options)
#                        0x2 0b010 for 8KB, the size of the UF2 SAMD21 bootloader
# 3 Reserved (0b1 << 3)
# 6:4 EEPROM, default = 7, 0b111 << 4 (see datasheet table 22-3 for options)
# 3 Reserved (0b1 << 7)
# ---- Brownout Detection - see SYSCTRL BOD33 register
# 13:8 BOD33 Level, default = 7, 0b111 << 8 (1.64V)
# 14 BOD33 Enable, default = 1 , 0b1 << 14 (enabled)
# 16:15 BOD33 Action Default = 1, 0b1 << 15 (RESET)
# 24:17 Reserved, default = 0x70, 0b1110000 << 17 [Internal Brownout Detection]
# ---- Watchdog Timer - see WDT CTRL and WDT CONFIG registers
# 25 WDT Enable, default = 0, 0b0 << 25 (disabled)
# 26 WDT Always On, default = 0, 0b0 << 26 (disabled)
# 30:27 WDT Period, default = 0x0B, 0b1011 << 27 (16384 clock cycles)
# 34:31 WDT Window, default = 0x05, 0b101 << 31 (256 clocks cycles)
# ^^ NOTE: only lowest bit of WDT Window is in USER_WORD_0
set v0 0xD8E0C7FF
# Default value for Fuse 1 ((User Row / USER_WORD_1)
# 0xFFFFFC5D = 0b11111111111111111111110001011101
# 34:31 WDT Window, default = 0x05, 0b101 (256 clocks cycles)
# ^^ NOTE: only upper 3 bits of WDT Window is in USER_WORD_1
# 38:35 WDT EWOFFSET (Early Warning Offset), default = 0x0B, 0b1011 << 3 (16384 clock cycles)
# 39 WDT WEN (Window Moden Enable), default = 0, 0b0 << 7 (disabled)
# ---- Brownout Detection - see SYSCTRL BOD33 register
# 40 BOD33 Hysteresis, default = 0, 0b0 << 8 (no hysteresis)
# 41 Reserved, default = 0, 0b0 << 9 [Internal Brownout Detection]
# ---- Reserved
# 47:42 Reserved, default = 0b11111 << 10
# 63:48 LOCK, default = 0xFFFF, 0b1111111111111111 << 16 (unlocked)
set v1 0xFFFFFC5D

# initialize
init

# find other used scripts
set CPU_MAX_ADDRESS 0xFFFFFFFF
source [find bitsbytes.tcl]
source [find memory.tcl]

# 0x00804000 is the offset of Fuse 0 ((User Row / USER_WORD_0)
set fuse0 0x00804000
# 0x00804004 is the offset of Fuse 1 ((User Row / USER_WORD_1)
set fuse1 0x00804004
# 0x41004000 is the base address of the NVMCTRL peripheral
set nvmctrl 0x41004000

# (NVMCTRL_CTRLA) Erase Auxiliary Row
# Erases the auxiliary row addressed by the ADDR register.
# This command can be given only when the security bit is not set and only to the user configuration row.
set cmd_ear 0x5
# (NVMCTRL_CTRLA) Page Buffer Clear
# Clears the page buffer.
set cmd_pbc 0x44
# (NVMCTRL_CTRLA) Write Auxiliary Page
# Writes the contents of the page buffer to the page addressed by the ADDR register.
# This command can be given only when the security bit is not set and only to the user configuration row.
set cmd_wap 0x6

# Helper procedure to send a commands to change values within the NVMCTRL
proc cmd {C} {
  global nvmctrl
  global fuse0
    # Set the starting address of the registers which we're going to write to the offset of fuse 0
    #   0x1C is the offset of the NVMCTRL_ADDR register
    #   ADDR drives the hardware half-word offset from the start address of the corresponding NVM section when a command is executed using CMDEX.
    #   This register is also automatically updated when writing to the page buffer.
    #   The effective address for the operation is Start address of the section + 2*ADDR.
    memwrite32 [expr $nvmctrl + 0x1C] [expr $fuse0 / 2]
    # Sent the command and the execution key needed to execute the command
    #   0xA500 is the NVMCTRL_CTRLA Execution Key
    memwrite16 $nvmctrl [expr 0xA500 | $C]
}

# get the current values of the fuses
set f0 [memread32 $fuse0]
set f1 [memread32 $fuse1]

# print the current values of the fuses
puts "Fuses:"
puts [format %x $f0]
puts [format %x $f1]

# Don't change anything unless force-update is set or the fuses are locked
set updatefuses 0

# If we're forcing an update (re-writing all fuses to factory settings)
if { $forceupdate } then {
  set updatefuses 1
} else {
  # if we're not re-writing all the fuses, just unlocking
  # if the fuse is locked (!0kb protected)
    if { ($f0 & 0x7) != 0x7 } then {
      # then we will force an update to un-lock it
        set updatefuses 1
        # set the value for fuse 0 the read value xor 0b111, which sets to 0kb protected
        set v0 [expr $f0 | 0x7]
        # set the value for fuse 1 to whatever we already read from it
        set v1 $f1
      }
}

if { $updatefuses } then {
  puts "*** Updating fuses! ***"
  puts [format %x $v0]
  puts [format %x $v1]
    # clear the CTRLA page buffer starting at the address/offset of fuse 0
    cmd $cmd_pbc
    # erase the auxillary row of starting at the address/offset of fuse 0
    cmd $cmd_ear

    # write new values to fuse 0
    memwrite32 $fuse0 $v0
    # write new values to fuse 1
    memwrite32 $fuse1 $v1

    # write page buffer starting at the address/offset of fuse 0
    cmd $cmd_wap

    # reset the chip to apply
    reset
}

# end the script
shutdown
