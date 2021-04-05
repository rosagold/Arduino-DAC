import time
import numpy as np
import cv2

import serial
import random
import driver
import logging
logger = logging.getLogger(__name__)

_BLUE = 0
_GREEN = 1
_RED = 2

WIDTH = 300
HIGHT = 300
MAX_VAL = 0xFFF


def pic_to_value(arr):
    r = arr.sum()
    max_r = 255 * HIGHT * WIDTH * 3.
    val = (r / max_r) * MAX_VAL
    return int(val)


def calc(ch, old, new):
    # diff = np.abs(new - old)
    # diff = diff.flatten()
    diff = new
    r = diff.sum()
    max_r = 255 * HIGHT * WIDTH * 3.
    val = (r / max_r) * MAX_VAL
    val = int(val)
    ch.write(val)
    time.sleep(0.002)


def run(show=False, test=False):
    if test:
        ch = driver.DummyChannel(0)
    else:
        ch = driver.Channel(0)

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HIGHT)
    if show:
        cv2.namedWindow("preview")

    if not cap.isOpened():
        raise RuntimeError('could not open cam')

    _, frame0 = cap.read()
    rval, frame1 = cap.read()

    thresh = -1
    val = pic_to_value(frame0)
    arrsz = 4
    arr = [val] * arrsz
    i = 0

    while rval:

        rval, frame1 = cap.read()

        val_old = arr[i]

        val = pic_to_value(frame0)
        logger.info(f'picval: {val}')

        arr[i] = val

        i += 1
        if i >= arrsz:
            i = 0

        # calculation
        if val <= thresh < val_old or val_old < thresh <= val:
            ch.write(MAX_VAL)
        else:
            ch.write(0)

        if val_old > val * 1.01:
            ch.write(MAX_VAL)

        frame0 = frame1.copy()

        if show:
            cv2.imshow("preview", frame0)
            key = cv2.waitKey(20)
            if key == 27:  # exit on ESC
                show = False
                cv2.destroyWindow("preview")
            elif key == ord('t'):
                thresh = input(f'current: {thresh}\nset new threshold:')
                try:
                    thresh = int(thresh)
                except (ValueError, TypeError):
                    print(f'invalid value: {thresh}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run(True)
