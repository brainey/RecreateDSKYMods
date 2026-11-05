# Test access to Nextion display via writing serial port with pySerial library
# Using arduino code in Nextion_LED_Pro_Micro.ino as a reference to communicating with the Nextion display
# Will read the console for user input to trigger actions on the Nextion display

from atexit import register
import sys
import argparse
import select
import tty
import time
import serial
import termios

DEFAULT_NEXTION_SERIAL_PORT = '/dev/ttyUSB0'  # Replace with your serial port

# Communication constants for Nextion display
NEXTION_BAUDRATE = 9600
NEXTION_TIMEOUT = 1
NEXTION_COMMAND_DELAY = 0.1  # Delay between sending commands to the Nextion display

# Protocol constants for Nextion display
NEXTION_PAYLOAD_SIZE = 38
NEXTION_BUFFER_SIZE = 40

NEXTION_END_OF_COMMAND = b'\xFF\xFF\xFF'

# Nextion serial port
nextion = None

old_terminal_settings = None

def initialize_terminal():
    """
    Initialize the terminal for reading user input.
    """
    fd = 0  # File descriptor for standard input
    old_settings = termios.tcgetattr(fd)
    register(lambda: termios.tcsetattr(fd, termios.TCSADRAIN, old_settings))
    return fd, old_settings

def restore_terminal():
    """
    Restore the terminal to its previous settings.
    """
    if old_terminal_settings is not None:
        fd = 0  # File descriptor for standard input
        termios.tcsetattr(fd, termios.TCSADRAIN, old_terminal_settings)


parser = argparse.ArgumentParser(description="Test Nextion display via serial port.")
parser.add_argument("port", help=f"Serial port name (default: {DEFAULT_NEXTION_SERIAL_PORT})", default=DEFAULT_NEXTION_SERIAL_PORT, nargs='?')
parser.add_argument("--baud", type=int, default=NEXTION_BAUDRATE, help=f"Baud rate (default: {NEXTION_BAUDRATE})")

def process_arguments():
    args = parser.parse_args()
    return args

def initialize_nextion(args: argparse.Namespace):
    """
    Initialize the Nextion display.
    """

    print(f"Initializing Nextion display...{args.port}@{args.baud}")
    try:
        ser = serial.Serial(
            port=args.port,
            baudrate=args.baud,
            timeout=NEXTION_TIMEOUT
        )
    except serial.SerialException as e:
        print(f"Failed to initialize Nextion display: {e}")
        sys.exit(1)

    # send_nextion_command(ser,"comp_acty.pic=2")  # Replace with your desired initial page
    print("DSKY Display Controller Ready. Type 't' for self-test.")

    return ser

def close_nextion(ser):
    if ser is not None:
        ser.close()
        ser = None

def send_nextion_command(port: serial.Serial, command: str):
    """
    Send a command to the Nextion display.
    """
    port.write(command.encode('utf-8') + NEXTION_END_OF_COMMAND)
    port.flush()
    time.sleep(NEXTION_COMMAND_DELAY)

def set_nextion_text(port: serial.Serial, component: str, text: str):
    """
    Set the text of a Nextion component.
    """
    send_nextion_command(port, f"{component}.txt=\"{text}\"")
    print(f"Set text of component '{component}' to '{text}'")

def reset_nextion_display(port: serial.Serial):
    """
    Reset the Nextion display to its initial state.
    """
    send_nextion_command(port, "comp_acty.pic=2")  # Replace with your desired initial page

    # Clear all numeric register positions on the Nextion display
    set_nextion_text(port, "PROG1", "")
    set_nextion_text(port, "PROG2", "")
    set_nextion_text(port, "VERB1", "")
    set_nextion_text(port, "VERB2", "")
    set_nextion_text(port, "NOUN1", "")
    set_nextion_text(port, "NOUN2", "")
    for register in range(1,4):
        for digit in range(1, 7):
            set_nextion_text(port, f"R{register}_{digit}", "")

    print("Nextion display reset to initial state.")
    time.sleep(1)  # Give the display some time to update
    print("Nextion display update complete.")

def execute_self_test():
    """
    Execute self-test on the Nextion display.
    """
    print("Executing self-test on the Nextion display.")

    reset_nextion_display(nextion)

    # Populate status fields on the Nextion display for self-test
    set_nextion_text(nextion, "PROG1", "0")
    set_nextion_text(nextion, "PROG2", "1")
    set_nextion_text(nextion, "VERB1", "2")
    set_nextion_text(nextion, "VERB2", "3")
    set_nextion_text(nextion, "NOUN1", "4")
    set_nextion_text(nextion, "NOUN2", "5")

    # Populate numeric register positions on the Nextion display for self-test
    for register in range(1,4):
        set_nextion_text(nextion, f"R{register}_1", "+")
        for digit in range(2, 7):
            set_nextion_text(nextion, f"R{register}_{digit}", str(register + digit - 2))

    # toggle the '+' sign on the first digit of each register for visual confirmation
    send_nextion_command(nextion, "comp_acty.pic=\"3\"")
    for count in range(1,4):
        time.sleep(0.5)
        send_nextion_command(nextion, "comp_acty.pic=\"2\"")
        set_nextion_text(nextion, "R1_1", "-")
        set_nextion_text(nextion, "R2_1", "-")
        set_nextion_text(nextion, "R3_1", "-")
        time.sleep(0.5)
        send_nextion_command(nextion, "comp_acty.pic=\"3\"")
        set_nextion_text(nextion, "R1_1", "+")
        set_nextion_text(nextion, "R2_1", "+")
        set_nextion_text(nextion, "R3_1", "+")

    # Indicate completion of self-test on the Nextion display
    print("Self-test completed.")

def run_serial_terminal(nextion):
    """
    Run a simple serial terminal for the Nextion display.
    """

    try:
        while True:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                user_input = sys.stdin.readline().strip()
                if user_input.lower() == "x":
                    print("Exiting terminal...")
                    break
                # Hardware self-test command
                if user_input.lower() == "t":
                    # flush the terminal buffer
                    sys.stdin.flush()
                    print("Executing self-test...")
                    execute_self_test()
                    continue
                # WHOAMI Handshake
                if user_input.lower() == "w":
                    # flush the terminal buffer
                    sys.stdin.flush()
                    print("DSKY_DISPLAY")
                    continue
                # Reset command for the Nextion display
                if user_input.lower() == "r":
                    reset_nextion_display(nextion)
                    # flush the terminal buffer
                    sys.stdin.flush()
                    continue
                if user_input.lower() == "help":
                    print("Available commands:")
                    print("  x         - Exit the terminal")
                    print("  t         - Execute self-test on the Nextion display")
                    print("  r         - Reset the Nextion display")
                    print("  w         - WHOAMI handshake with the Nextion display")

                    continue
                nextion.write(user_input.encode('utf-8') + NEXTION_END_OF_COMMAND)
                nextion.flush()
    except KeyboardInterrupt:
        pass
    finally:
        if nextion is not None:
            nextion.close()
            nextion = None

# Example usage
if __name__ == "__main__":
    args = process_arguments()
    fd, old_terminal_settings = initialize_terminal()
    nextion = initialize_nextion(args)

    # old_terminal_settings = initialize_terminal()
    # nextion = initialize_nextion()

    # send_nextion_command("page 0")  # Replace with your desired command
    # send_nextion_command("t0.txt=\"Hello\"")  # Example of setting text on a Nextion component  
    # send_nextion_command("t1.txt=\"World\"")  # Example of setting text on another Nextion component
    # send_nextion_command("t2.txt=\"!\"")  # Example of setting text on a third Nextion component
    # send_nextion_command("t3.txt=\"Goodbye\"")  # Example of setting text on a fourth Nextion component
    # send_nextion_command("t4.txt=\"!\"")  # Example of setting text on a fifth Nextion component
    # send_nextion_command("t5.txt=\"Hello again\"")  # Example of setting text on a sixth Nextion component
    # send_nextion_command("t6.txt=\"Goodbye again\"")  # Example of setting text on a seventh Nextion component
    # send_nextion_command("t7.txt=\"Final\"")  # Example of setting text on an eighth Nextion component
    # send_nextion_command("t8.txt=\"Extra\"")  # Example of setting text on a ninth Nextion component
    # send_nextion_command("t9.txt=\"More\"")  # Example of setting text on a tenth Nextion component
    # send_nextion_command("t10.txt=\"Even More\"")  # Example of setting text on an eleventh Nextion component
    # send_nextion_command("t11.txt=\"Last\"")  # Example of setting text on a twelfth Nextion component
    # send_nextion_command("t12.txt=\"Extra\"")  # Example of setting text on a thirteenth Nextion component
    # send_nextion_command("t13.txt=\"More\"")  # Example of setting text on a fourteenth Nextion component
    # send_nextion_command("t14.txt=\"Even More\"")  # Example of setting text on a fifteenth Nextion component
    # send_nextion_command("t15.txt=\"Final\"")  # Example of setting text on a sixteenth Nextion component   

    run_serial_terminal(nextion)

    restore_terminal()