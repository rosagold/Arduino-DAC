import time

import serial
import random

ser = serial.Serial()


def serial_setup(port=None):
    """

    Parameters
    ----------
    port: str, default None
        path to port eg. `"/dev/ttyUSB0"`. If None,
        try to automatically find a ArduinoNano connected via USB
        and use this port.

    Returns
    -------
    ser: serial

    """
    if port is None:
        port = "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"

    ser.port = port
    ser.baudrate = 256000
    ser.parity = serial.PARITY_NONE
    ser.stopbits = serial.STOPBITS_ONE
    ser.bytesize = serial.EIGHTBITS

    # read time out in sec
    ser.timeout = 0.5

    ser.close()
    ser.open()

    assert ser.is_open, "After initialisation serial port is still closed."

    ser.reset_input_buffer()
    ser.reset_output_buffer()
    return ser


def make_msg(ch, val):
    print(val)
    msg = f'{ch},{val}\n'
    return msg.encode()


def send_msg(m):
    ser.write(m)


def get_answer():
    if ser.in_waiting:
        return ser.read_until('\n').decode()
    return None


def send_stuff(ch):
    while True:
        time.sleep(0.1)

        r = random.randint(0, 0xFFF - 1)
        m = make_msg(ch, r)

        send_msg(m)

        time.sleep(0.001)

        a = get_answer()
        if a is not None:
            print(a)


if __name__ == '__main__':

    try:
        serial_setup()
        send_stuff(0)
    finally:
        ser.close()
