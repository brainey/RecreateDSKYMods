# DSKY Keyboard Controller

## Goals

- support hand wired DSKY 19 key matrix keyboard
- provide USB HID interface of the keyboard to the Raspberry Pi
- eventually support PCB keyboard which will addressable LEDs for each key which means will need to extend HID ([see Google AI exchange on this](https://share.google/aimode/NCBkGEfayACtSsrWQ))
- Microcontroller to be used to used when only supporting keyboard will be an RP2040-Zero board from Waveshare. See pin out below. Plan to use the RP2350-Zero for the merge support of keyboard, nextion display and annunciator since the TX/RX serial pins are able to support the +5V TX of the nextion - the RP2040 will no handle this +5V TX on its RX pin.


## Pinout for the RP2040 / RP2350 Zero boards from Waveshare
![RP2350-Zero Pinout diagram](RP2350-Zero-pinout.png)

## Breadboard for DSKY Keyboard

![Breadboard Wiring Diagram for DSKY Keyboard](Revised-Keyboard-Bread-Board-Wiring.png)

## Notes on RP2040
- Unable to handle a +5V TX on its serial port RX pins, must be +3.3V TX signal.

## Notes RP2350
- Internal pull-ups ineffective when port configured as digital pin
- GP16 avoid as it has conflicts with RGB LED somehow (need to investigate this further - might be the GPIO to use for NeoPixels ...)
- Okay - while make these notes, I realized I had messed up in my test code, attempting to use GP14-GP17 as the column line inputs from my DSKY wired matrix keyboard. The problem doing this is that the RP2350-Zero stops at GP15 and then jumps to GP26 to GP29 (which are also ADC0 thru ADC3). So the reason my code didn't work is that I was using the GPIOs for the third and fourth columsn - duh! 


