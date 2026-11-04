# Test access to Nextion display via writing serial port with pySerial library
# Using arduino code in Nextion_LED_Pro_Micro.ino as a reference to communicating with the Nextion display
# Will read the console for user input to trigger actions on the Nextion display

from atexit import register
import sys
import select
import tty
import time
import serial
import termios

NEXTION_SERIAL_PORT = '/dev/ttyACM0'  # Replace with your serial port

# Communication constants for Nextion display
NEXTION_BAUDRATE = 9600
NEXTION_TIMEOUT = 1
NEXTION_COMMAND_DELAY = 0.1  # Delay between sending commands to the Nextion display

# Protocol constants for Nextion display
NEXTION_PAYLOAD_SIZE = 38
NEXTION_BUFFER_SIZE = 40

NEXTION_END_OF_COMMAND = b'\xFF\xFF\xFF'

# Nextion serial port
nextion_serial = None

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

def initialize_nextion():
    """
    Initialize the Nextion display.
    """

    ser = serial.Serial(
        port=NEXTION_SERIAL_PORT,  # Replace with your serial port
        baudrate=NEXTION_BAUDRATE,
        timeout=NEXTION_TIMEOUT
    )
    # send_nextion_command("comp_acty.pic=2")  # Replace with your desired initial page
    # print("DSKY Display Controller Ready. Type 't' for self-test.")

    return ser

def close_nextion(ser):
    if ser is not None:
        ser.close()
        ser = None

def send_nextion_command(command: str):
    """
    Send a command to the Nextion display.
    """
    global nextion_serial

    nextion_serial.write(command.encode('utf-8') + NEXTION_END_OF_COMMAND)
    nextion_serial.flush()
    time.sleep(NEXTION_COMMAND_DELAY)

def set_nextion_text(component: str, text: str):
    """
    Set the text of a Nextion component.
    """
    send_nextion_command(f"{component}.txt=\"{text}\"")
    print(f"Set text of component '{component}' to '{text}'")

def execute_self_test():
    """
    Execute self-test on the Nextion display.
    """
    print("Executing self-test on the Nextion display.")

    # Populate status fields on the Nextion display for self-test
    set_nextion_text("PROG1", "0")
    set_nextion_text("PROG2", "1")
    set_nextion_text("VERB1", "2")
    set_nextion_text("VERB2", "3")
    set_nextion_text("NOUN1", "4")
    set_nextion_text("NOUN2", "5")
    set_nextion_text("R1_1", "+")
    set_nextion_text("R2_1", "+")
    set_nextion_text("R3_1", "+")

    # Populate Numeric Register Positions on the Nextion display for self-test
    for register in range(2,7):
        set_nextion_text(f"R1_{register}", str(register - 1))
        set_nextion_text(f"R2_{register}", str(register))
        set_nextion_text(f"R3_{register}", str(register + 1))
        print(f"Setting R1_{register} to {register - 1}")
        print(f"Setting R2_{register} to {register}")
        print(f"Setting R3_{register} to {register + 1}")

    # Veriify COMP ACTY State
    send_nextion_command("COMP_ACTY.pic=\"3\"")
    time.sleep(1)
    send_nextion_command("COMP_ACTY.pic=\"2\"")

    # Indicate completion of self-test on the Nextion display
    print("Self-test completed.")

def run_serial_terminal():
    """
    Run a simple serial terminal for the Nextion display.
    """
    global nextion_serial
    try:
        while True:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                user_input = sys.stdin.readline().strip()
                if user_input.lower() == "x":
                    print("Exiting terminal...")
                    break
                if user_input.lower() == "t":
                    # flush the terminal buffer
                    sys.stdin.flush()
                    print("Executing self-test...")
                    execute_self_test()
                    continue
                if user_input.lower() == "w":
                    print("DSKY_DISPLAY")
                    # flush the terminal buffer
                    sys.stdin.flush()
                    continue
                if user_input.lower() == "help":
                    print("Available commands:")
                    print("  x         - Exit the terminal")
                    print("  t         - Execute self-test on the Nextion display")
                    print("  w         - Display DSKY_DISPLAY")
                    continue
                nextion_serial.write(user_input.encode('utf-8') + NEXTION_END_OF_COMMAND)
                nextion_serial.flush()
    except KeyboardInterrupt:
        pass
    finally:
        if nextion_serial is not None:
            nextion_serial.close() 
            nextion_serial = None

# Example usage
if __name__ == "__main__":
    fd, old_terminal_settings = initialize_terminal()
    nextion_serial = initialize_nextion()

    # old_terminal_settings = initialize_terminal()
    # nextion_serial = initialize_nextion()

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

    run_serial_terminal()

    restore_terminal()