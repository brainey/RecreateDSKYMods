import usb_hid
import usb_midi

# Custom Interface Descriptor: Addressable LED Control (Host -> Device)
LED_OUT_DESCRIPTOR = bytes((
    0x06, 0x00, 0xFF,  # Usage Page (Vendor Defined 0xFF00)
    0x09, 0x01,        # Usage (Vendor Usage 1)
    0xA1, 0x01,        # Collection (Application)
    0x85, 0x04,        #   Report ID (4)
    0x19, 0x01,        #   Usage Minimum (1)
    0x29, 0x3F,        #   Usage Maximum (64)
    0x15, 0x00,        #   Logical Minimum (0)
    0x25, 0xFF,        #   Logical Maximum (255)
    0x75, 0x08,        #   Report Size (8 bits)
    0x95, 0x3F,        #   Report Count (64 bytes)
    0x91, 0x02,        #   Output (Data, Variable, Absolute) -> Host to Device
    0xC0               # End Collection
))

led_device = usb_hid.Device(
    report_descriptor=LED_OUT_DESCRIPTOR,
    usage_page=0xFF00,
    usage=0x01,
    report_ids=(4,),
    in_report_lengths=(0,),
    out_report_lengths=(63,),
)

# Enable standard keyboard + the single custom LED interface
usb_hid.enable((usb_hid.Device.KEYBOARD, led_device))
# Disable MIDI interface as it's not needed for this setup
usb_midi.disable()

# Set the USB identification strings for your custom DSKY interface
usb_hid.set_interface_name("DSKY Keypad Controller")
