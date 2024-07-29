# change forceupdate to 1 to update the fuses to factory default values specified below
set forceupdate 0

# if NOT forcing an updated (`set forceupdate 0`), set the size of the bootloader to protect here
# see datasheet table 22-2 for options
# 0x7, 0b111 = 0 bytes protected (not locked)
# 0x2, 0b010 = 8KB protected (the size of the UF2 SAMD21 bootloader)
set bootprot 0x7

#  Set up the Transport and Chip

source [find interface/cmsis-dap.cfg]
transport select swd

# chip name
set CHIPNAME samd21g18a

set _FLASHDRIVER at91samd

source [find target/at91samdXX.cfg]

# The SAMD21 has 2 32-bit "fuses", aka User Rows, USER_WORD, or Configuration Bits
# Each row on the SAMD21 can be written individually

# Default values for Fuse 0 (User Row / USER_WORD_0)
# ---- Boot protection!
# 2:0 BOOTPROT, default = 7, 0b111 (0 bytes protected) (see datasheet table 22-2 for options)
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
# ^^ NOTE: only lowest bit of WDT Window is in USER_WORD_0 (WHY??)
# Factory Default:
# 0xD8E0C7FF = 0b11011000111000001100011111111111
# Changable Bits Mask (1 bits are user changable, 0 bits are reserved)
# 0xFE01FF77 = 0b11111110000000011111111101110111
set v0 0xD8E0C7FF

# Default values for Fuse 1 ((User Row / USER_WORD_1)
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
# Factory Default:
# 0xFFFFFC5D = 0b11111111111111111111110001011101
# Changable Bits Mask (1 bits are user changable, 0 bits are reserved)
# 0xFFFF01FF = 0b11111111111111110000000111111111
set v1 0xFFFFFC5D

# initialize
init

# find other used scripts
set CPU_MAX_ADDRESS 0xFFFFFFFF
source [find bitsbytes.tcl]
source [find memory.tcl]

# 0x00804000 is the offset of Fuse 0 (User Row / USER_WORD_0 / NVMCTRL_AUX0_ADDRESS)
set fuse0 0x00804000
# 0x00804004 is the offset of Fuse 1 (User Row / USER_WORD_1)
set fuse1 0x00804004
# 0x41004000 is the base address of the NVMCTRL peripheral
set nvmctrl 0x41004000

# (NVMCTRL_CTRLA - NVMCTRL_CTRLA_CMD_PBC) Page Buffer Clear
# Clears the page buffer.
set cmd_pbc 0x44
# (NVMCTRL_CTRLA - NVMCTRL_CTRLA_CMD_EAR) Erase Auxiliary Row
# Erases the auxiliary row addressed by the ADDR register.
# This command can be given only when the security bit is not set and only to the user configuration row.
set cmd_ear 0x5
# (NVMCTRL_CTRLA - NVMCTRL_CTRLA_CMD_WAP) Write Auxiliary Page
# Writes the contents of the page buffer to the page addressed by the ADDR register.
# This command can be given only when the security bit is not set and only to the user configuration row.
set cmd_wap 0x6

# Helper procedure to send a commands to change values within the NVMCTRL
proc cmd {C} {
    global nvmctrl
    global fuse0
    # Set the starting address of the registers which we're going to write to the offset of fuse 0
    # ie, write the address of fuse 0 to the ADDR register, itself located at NVMCTRL + NVMCTRL_ADDR
    #   0x1C is the offset of the NVMCTRL_ADDR register
    #   ADDR drives the hardware half-word offset from the start address of the corresponding NVM section when a command is executed using CMDEX.
    #   This register is also automatically updated when writing to the page buffer.
    #   The effective address for the operation is Start address of the section + 2*ADDR.
    memwrite32 [expr $nvmctrl + 0x1C] [expr $fuse0 / 2]
    # Clear the status mask??
    # NVMCTRL->STATUS.reg |= NVMCTRL_STATUS_MASK;  // Clear error status bits.
    # Sent the command and the execution key needed to execute the command
    #   NVMCTRL_CTRLB is offset from NVMCTRL by 0x0 (ie, not offset)
    #   0xA500 (0xA5<<8) is the NVMCTRL_CTRLA Execution Key
    memwrite16 $nvmctrl [expr 0xA500 | $C]
    # Wait for the interrupt bit to be ready??
    # while (NVMCTRL->INTFLAG.bit.READY == 0) { }
}


puts "Reading Fuses"
# get the current values of the fuses
set f0 [memread32 $fuse0]
set f1 [memread32 $fuse1]

# print the current values of the fuses
puts "Fuses:"
puts [format %x $f0]
puts [format %x $f1]


puts "BOOTPROT Bit Read:"
puts [format %x [expr $f0 & 0x7]]
puts "BOOTPROT Bit Requested:"
puts [format %x $bootprot]


# Don't change anything unless force-update is set or the fuses are locked
set updatefuses 0

# If we're forcing an update (re-writing all fuses to factory settings)
if { $forceupdate } then {
    set updatefuses 1
} else {
    # if we're not re-writing all the fuses, just changing the protection size
    # check if the boot protection settings line up
    if { ($f0 & 0x7) != $bootprot } then {
        # if the boot protection setting isn't what we want, we'll update fuses
        set updatefuses 1
        # clear the value of the bootprot portion of fuse 0
        set v0_p [expr $f0 & 0b11111111111111111111111111111000]
        # set the value for fuse 0 the read value bitwise-or with the requested bootprot setting
        set v0 [expr $v0_p | $bootprot]
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
