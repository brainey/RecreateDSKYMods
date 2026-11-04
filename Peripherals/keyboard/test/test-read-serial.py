# Test reading serial port with pySerial library

import serial

# Configure the serial port
ser = serial.Serial(
    port='/dev/ttyACM0',  # Replace with your serial port
    baudrate=9600,
    timeout=1
)

# Read data from the serial port
while True:
    if ser.in_waiting > 0:
        data = ser.readline().decode('utf-8').rstrip()
        print(data)
