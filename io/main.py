import time
import numpy as np
import cv2

import serial
import random

_BLUE = 0
_GREEN = 1
_RED = 2
ser = serial.Serial()


def serial_setup(port='/dev/ttyUSB0'):
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


# def send_stuff(ch):
#     while True:
#         time.sleep(0.1)
#
#         r = random.randint(0, 0xFFF - 1)
#         m = make_msg(ch, r)
#
#         send_msg(m)
#
#         time.sleep(0.001)
#
#         a = get_answer()
#         if a is not None:
#             print(a)


def calc(old, new):
    # diff = np.abs(new - old)
    # diff = diff.flatten()
    diff = new
    r = diff.sum()
    max_r = 255*300*300*3.
    val = (r/max_r) * 0xFFF
    val = int(val)
    print(val)
    m = make_msg(0, val)
    send_msg(m)
    time.sleep(0.002)
    a = get_answer()
    if a is not None:
        print(a)


def run(show=False):
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 300)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 300)
    if show:
        cv2.namedWindow("preview")

    if not cap.isOpened():
        raise RuntimeError('could not open cam')

    _, frame0 = cap.read()
    rval, frame1 = cap.read()

    while rval:

        rval, frame1 = cap.read()
        calc(frame0, frame1)
        frame0 = frame1.copy()

        if show:
            cv2.imshow("preview", frame0)
            key = cv2.waitKey(20)
            if key == 27:  # exit on ESC
                show = False
                cv2.destroyWindow("preview")


if __name__ == '__main__':

    try:
        serial_setup()
        run(True)
    finally:
        ser.close()
