# The Pin Descriptions array

For each new SAMD variant, you need to create a pin description array.
The digital pin number is assigned by the order of your array.
I had a very hard time finding documentation for the values of the array, so I'm dumping most of what I've found here.
All of the information needed for the pin descriptions comes from the multiples tables from the SAMD datasheets.
For the SAMD51, that table is [here in the datasheet](https://onlinedocs.microchip.com/oxy/GUID-F5813793-E016-46F5-A9E2-718D8BCED496-en-US-15/GUID-B3DD274A-0286-4C14-8A91-0B9A5980582F.html)

## The _PinDescription struct

The struct for each object in the pin description array comes from [WVariant.h](https://github.com/adafruit/ArduinoCore-samd/blob/master/cores/arduino/WVariant.h) of the SAMD core.

```cpp
 typedef struct _PinDescription
 {
   EPortType       ulPort ; // IO Pin Controller PORT/group
   uint32_t        ulPin ;  // The pin within the PORT (not the physical pin number!)
   EPioType        ulPinType ; // The peripheral controlling the pin, see WVariant.h
   uint32_t        ulPinAttribute ; // See Pin Attributes to be OR-ed in WVariant.h
   EAnalogChannel  ulADCChannelNumber ; // ADC Channel number in the SAM device
   EPWMChannel     ulPWMChannel ; // The pulse wave management channel (tied to the timer channel)
   ETCChannel      ulTCChannel ; //  The Timer/Counter for Control applications (TCC) peripheral channel
   EExt_Interrupts ulExtInt ; // For attachInterrupt(), which external interrupt does this pin tie to
 } PinDescription ;
 ```

### PioType

The EPioType value within the PinDescription struct determines which peripheral controls the input and output (io) of the pin.
The EPioType is itself a struct defined in [the WVariant.hfile](https://github.com/adafruit/ArduinoCore-samd/blob/master/cores/arduino/WVariant.h).

```cpp
typedef enum _EPioType
{
  PIO_NOT_A_PIN=-1,     /* Not under control of a peripheral. */
  PIO_EXTINT=0,         /* The pin is controlled by the associated signal of peripheral A. */
  PIO_ANALOG,           /* The pin is controlled by the associated signal of peripheral B. */
  PIO_SERCOM,           /* The pin is controlled by the associated signal of peripheral C. */
  PIO_SERCOM_ALT,       /* The pin is controlled by the associated signal of peripheral D. */
  PIO_TIMER,            /* The pin is controlled by the associated signal of peripheral E. */
  PIO_TIMER_ALT,        /* The pin is controlled by the associated signal of peripheral F. */
#if defined(__SAMD51__)
  PIO_TCC_PDEC, |  |  | /* The pin is controlled by the associated signal of peripheral G. */
  PIO_COM,             /* The pin is controlled by the associated signal of peripheral H. */
  PIO_SDHC,             /* The pin is controlled by the associated signal of peripheral I. */
  PIO_I2S,              /* The pin is controlled by the associated signal of peripheral J. */
  PIO_PCC,              /* The pin is controlled by the associated signal of peripheral K. */
  PIO_GMAC,             /* The pin is controlled by the associated signal of peripheral L. */
  PIO_AC_CLK,           /* The pin is controlled by the associated signal of peripheral M. */
  PIO_CCL,              /* The pin is controlled by the associated signal of peripheral N. */
#else
  PIO_COM,              /* The pin is controlled by the associated signal of peripheral G. */
  PIO_AC_CLK,           /* The pin is controlled by the associated signal of peripheral H. */
#endif
  PIO_DIGITAL,          /* The pin is controlled by PORT. */
  PIO_INPUT,            /* The pin is controlled by PORT and is an input. */
  PIO_INPUT_PULLUP,     /* The pin is controlled by PORT and is an input with internal pull-up resistor enabled. */
  PIO_OUTPUT,           /* The pin is controlled by PORT and is an output. */

  PIO_PWM=PIO_TIMER,
  PIO_PWM_ALT=PIO_TIMER_ALT,
} EPioType ;
```

Here's the same information in a table, which I found easier to understand:

| EPioType         | Letter for Peripheral in Multiplexing Table | Applicable Processor | Peripheral Use / Description                                                                                                                                                           |
| ---------------- | ------------------------------------------- | -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PIO_NOT_A_PIN    | -                                           | All SAMD             | Use this for dummy lines in your array.  I.e., to assign a pin for the USB Host enable on a board that has no such pin.                                                                |
| PIO_EXTINT       | A                                           | All SAMD             | External Interrupt Control, the pins are used as interrupts                                                                                                                            |
| PIO_ANALOG       | B                                           | All SAMD             | Analog-to-digital converter (ADC), digital-to-analog converter (DAC), or Peripheral Touch Controller (PTC)                                                                             |
| PIO_SERCOM       | C                                           | All SAMD             | SERCOM using primary pad configuration.  NOTE: You cannot combine SERCOM and SERCOM_ALT pins in a single SERCOM configuration.                                                         |
| PIO_SERCOM_ALT   | D                                           | All SAMD             | SERCOM using alternate pad. NOTE: You cannot combine SERCOM and SERCOM_ALT pins in a single SERCOM configuration. configuration                                                        |
| PIO_TIMER        | E                                           | All SAMD             | Timer Capture Input                                                                                                                                                                    |
| PIO_TIMER_ALT    | F                                           | All SAMD             | Timer Compare Output                                                                                                                                                                   |
| PIO_TCC_PDEC     | G                                           | SAMD51 only          | Position decoder                                                                                                                                                                       |
| PIO_COM          | H                                           | SAMD51 only          | Other communication protocols without a dedicated peripheral (QSPI, CAN1, USB, CORTEX_CM4, SWD, TPIU)                                                                                  |
| PIO_SDHC         | I                                           | SAMD51 only          | SDHC, CAN0                                                                                                                                                                             |
| PIO_I2S          | J                                           | SAMD51 only          | I2S: Inter-IC Sound Controller                                                                                                                                                         |
| PIO_PCC          | K                                           | SAMD51 only          | Parallel Capture Controller                                                                                                                                                            |
| PIO_GMAC         | L                                           | SAMD51 only          | Gigabit Ethernet Media Access Controller (GMAC)                                                                                                                                        |
| PIO_AC_CLK       | M                                           | SAMD51 only          | Generic Clock Controller Input/Outputs and Analog Comparitor Outputs                                                                                                                   |
| PIO_CCL          | N                                           | SAMD51 only          | CLC/CCL: Configurable Custom Logic                                                                                                                                                     |
| PIO_COM          | G                                           | NOT SAMD51           | Other communication protocols without a dedicated peripheral (I2S, USB, SWD)                                                                                                           |
| PIO_AC_CLK       | H                                           | NOT SAMD51           | Generic Clock Controller Input/Outputs and Analog Comparitor Outputs                                                                                                                   |
| PIO_DIGITAL      | No peripheral, general I/O                  | All SAMD             | Use these for pins that will be used for basic I/O and directly controlled by the I/O port registers. I.e., real pins that are not going to be used by any of the fancier peripherals. |
| PIO_INPUT        | Generic I/O input                           | All SAMD             | This is treated identically to PIO_DIGITAL within the SAMD core.                                                                                                                       |
| PIO_INPUT_PULLUP | Generic I/O input with internal pull-up     | All SAMD             | This is treated identically to PIO_DIGITAL within the SAMD core.                                                                                                                       |
| PIO_OUTPUT       | Generic I/O output                          | All SAMD             | This is treated identically to PIO_DIGITAL within the SAMD core.                                                                                                                       |
| PIO_PWM          | Equivalent to PIO_TIMER                     | All SAMD             | Equivalent to PIO_TIMER                                                                                                                                                                |
| PIO_PWM_ALT      | Equivalent to PIO_TIMER_ALT                 | All SAMD             | Equivalent to PIO_TIMER_ALT                                                                                                                                                            |

### Pin Attributes

The pin attribute value is used to differentiate between functions within the same peripheral, mostly.
Figuring out what to put here is.. confusing.
You can put a set of values here, not just a single attribute for each pin.
If you have multiple attributes, you should write them like this `( ATTR_1 | ATTR2 )`
Generally, you probably want to list as many attributes as are possibly valid for your pin.
Look at the multiplexing table for your processor to see what each pin is capable of.

| Pin Attributes to be OR-ed | Defined Value | Applicable Processor | Notes                                                                                                                                                                                                                                                                                                         |
| -------------------------- | ------------- | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PIN_ATTR_NONE              | (0UL<<0)      | All SAMD             | Pin has no extra use attributes                                                                                                                                                                                                                                                                               |
| PIN_ATTR_COMBO             | (1UL<<0)      | All SAMD             | Not used by core                                                                                                                                                                                                                                                                                              |
| PIN_ATTR_EXTINT            | (1UL<<6)      | All SAMD             | Not used by core, but seems to be intended to help specify for EPioTypes PIO_EXTINT.  External interrupt channels are set by EExt_Interrupts.                                                                                                                                                                 |
| PIN_ATTR_DIGITAL           | (1UL<<2)      | All SAMD             | Not used by core, but seems to be intended to help specify for EPioTypes PIO_DIGITAL, PIO_INPUT, PIO_OUTPUT, PIO_INPUT_PULLUP                                                                                                                                                                                 |
| PIN_ATTR_ANALOG            | (1UL<<1)      | All SAMD             | Analog input can be read on ADC0 or Analog output sent on DAC.  The analog channel number is set by the value of EAnalogChannel.                                                                                                                                                                              |
| PIN_ATTR_ANALOG_ALT        | (1UL<<7)      | All SAMD             | Analog input can be read on ADC1.  The analog channel number is set by EAnalogChannel.                                                                                                                                                                                                                        |
| PIN_ATTR_PWM               | (1UL<<3)      | NOT SAMD51           | Pin supports PWM.  If the pin has a channel assigned for either the TC or TCC peripheral in the multiplexing table, it supports PWM and you should add this attribute.  The peripheral clock used for PWM is set by PIN_ATTR_TIMER or PIN_ATTR_TIMER_ALT.  The clock channel is set to the PWM channel value. |
| PIN_ATTR_TIMER             | (1UL<<4)      | NOT SAMD51           | PWM Output timing of SAMD21 uses TC (PIO_TIMER, peripheral E)                                                                                                                                                                                                                                                 |
| PIN_ATTR_TIMER_ALT         | (1UL<<5)      | NOT SAMD51           | PWM Output timing of SAMD21 uses TC TCC (PIO_TIMER_ALT, peripheral F)                                                                                                                                                                                                                                         |
| PIN_ATTR_PWM_E             | (1UL<<3)      | SAMD51 Only          | The pin supports PWM and the PWM timing is controlled by PIO_TIMER, peripheral E.  Any pin with a TCx/WO channel assigned in the TC column of the multiplexing table supports PWM.  The clock channel is set to the PWM channel value.                                                                        |
| PIN_ATTR_PWM_F             | (1UL<<8)      | SAMD51 Only          | The pin supports PWM and the PWM timing is controlled by PIO_TIMER_ALT, peripheral F.  Any pin with a TCCx/WO channel assigned in the TC column of the multiplexing table supports PWM.  The clock channel is set to the PWM channel value.                                                                   |
| PIN_ATTR_PWM_G             | (1UL<<9)      | SAMD51 Only          | The pin supports PWM and the PWM timing is controlled by TCC of PIO_TCC_PDEC, peripheral G.  Any pin with a TCCx/WO channel assigned in the TC column of the multiplexing table supports PWM. The PDEC channels do not support PWM.  The clock channel is set to the PWM channel value.                       |

### Analog Channel

This is the analog channel for each port and pin comes from the multiplexing table.
*IF* you set the PioType to PIO_ANALOG or PIO_ANALOG_ALT, you fill in the channel here.
The value here should be `ACD_Channelx` where the value of x comes from the ADC0 or ACD1 column of the multiplexing table (i.e., AIN[x]).
If your PioType is *not* set to PIO_ANALOG or PIO_ANALOG_ALT, this should be set to `No_ADC_Channel`.

### PWM Channel

This is the timer channel used for pulse width modulation (PWM), based on what's listed in the multiplexing table.
It does *not* matter what PioType you set the pin to for the PWM channel to apply, only the pin attribute.
For a SAMD21 processor, the pin attribute must have *both* PIN_ATTR_PWM and PIN_ATTR_ANALOG or PIN_ATTR_ANALOG_ALT listed to work properly.
For a SAMD51 processor, you the attribute only needs to contain PIN_ATTR_PWM_E, or PIN_ATTR_PWM_F, or PIN_ATTR_PWM_G.
Whichever is listed first will be used, no matter how many are listed.
The value here is `PWMy_CHx` where the values of x and y come from the TC, TCC, or PDEC columns of the multiplexing table (i.e., TCy/WO[x] or TCCy/WO[x]).
Remember, pins controlled by the PDEC peripheral that have a PDEC channel instead of a TCC channel do not support PWM.
If your pin does not support PWM, the value should be set to `NOT_ON_PWM`.

### TC Channel

This is the timer channel use for any other timing application except PWM (ie, Tone or SDI-12).
The value of the PioType or the pin attribute are probably not relevant here.
The value here is `TCCy_CHx` or `TCy_CHx` where the values of x and y come from the TC, TCC, or PDEC columns of the multiplexing table (i.e., TCy/WO[x] or TCCy/WO[x]).
If your pin is not connected to a timer, the value should be set to `NOT_ON_TIMER`.

### External interrupt Channel

This is the external interrupt channel assigned to your pin in the multiplexing table.
There are only 16 external interrupt channels that can be used, but each channel has more than one pin as an option for the input.
The value here is `EXTERNAL_INT_x` where the value of x comes from the EIC column of the multiplexing table (i.e., EIC/EXTINT[x]).
The value of the PioType or the pin attributes do not matter for the EIC.
