# Peripheral Support for DSKY

## Peripherals
- [Keyboard](keyboard/README.md)
- Display
- Annunciator
- GPS
- NFC Reader
- SDR
- Stereo speakers and amplifier - possible media player use in addition to player CM and LM alert tones
- HDMI out - possible media player use

## Architecture of Replica DSKY Peripherals

Based on the RecreateApolle project's RecreateDSKY, the keyboard will have a microcontroller actting as an HID keyboard and that plugs in to the Raspberry Pi via USB. Similarly, the annunciator panel and display will have another microcontroller that also plugs into the Raspberry Pi via USB. The microcontroller will directly control the addressable LEDs that make up the annunciator panel. It will also relay commands to the Nextion display via a serial connection. It is currently unclear what the control interface between the microcontroller and the Raspberry Pi - I believe the current interface is some sort of serial protocol.

Version 1 will be adapting the current RecreateDSKY arduino code to the Circuitpython being used in the RP2040/RP2350 microcontroller that I'm using.

Version 2's goal is to adapt this interface to a custom HID and based on that effort, possibly merge all three periperals under one microprocessor.

Version 3's goal is to replace the Nextion display with an DSI display that is directly connected to the Raspberry Pi and the pi will take over all display functions. The one microcontroller will be responsible just for the keyboard and annunciator.

Here the current system diagram.

![V1 Architecture Diagram](peripheral-architecture-v1.png)
