import usb_hid

# Define a custom HID report descriptor for receiving data from the host (OUT report)

# 5-byte payload descriptor: [Report ID, Offset, Count, R, G, B]
CUSTOM_HID_REPORT_DESCRIPTOR = bytes(
    (
        0x06, 0x00, 0xFF,  # Usage Page (Vendor Defined 0xFF00)
        0x09, 0x01,        # Usage (1)
        0xA1, 0x01,        # Collection (Application)
        0x85, 0x01,        #   Report ID (1)
        0x09, 0x01,        #   Usage (1)
        0x15, 0x00,        #   Logical Minimum (0)
        0x25, 0xFF,        #   Logical Maximum (255)
        0x75, 0x08,        #   Report Size (8 bits)
        0x95, 0x05,        #   Report Count (5 bytes total for control data)
        0x91, 0x02,        #   Output (Data, Var, Abs)
        0xC0,              # End Collection
    )
)

custom_hid_device = usb_hid.Device(
    report_descriptor=CUSTOM_HID_REPORT_DESCRIPTOR,
    usage_page=0xFF00,
    usage=0x01,
    report_ids=(1,),
    in_report_lengths=(0,),
    out_report_lengths=(5,),  # Increased to 5 bytes
)

# Enable only the custom HID device (or combine with keyboard/mouse if needed)
usb_hid.enable((custom_hid_device,))

# Set the USB identification strings for your custom DSKY interface
usb_hid.set_interface_name("DSKY Keypad and Annunciator Controller")
