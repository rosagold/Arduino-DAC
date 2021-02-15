import sys

import serial
import time
import numpy as np
from common import _max_channels
import logging as _logging
import atexit

# QinHeng Electronics HL-340 USB-Serial adapter, used in
# Arduino Nano
ARD_NANO_MAGIC_PORT = "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"
logger = _logging.getLogger(__name__)

MSG_SYNC_HEADER = (0xEEEE).to_bytes(length=2, byteorder='little')


class SerialDriver:
    """

    Parameters
    ----------
    port: str, default None
        path to port eg. `"/dev/ttyUSB0"`. If None,
        try to automatically find a ArduinoNano connected via USB
        and use this port.

    Returns
    -------
    ser: SerialDriver

    """

    def __init__(self, shared_channels=True, force=False, **kwargs):

        self._mem_obj = None
        self.ser = None

        # if port is passed as kwarg the port is opened
        # in init, but we want to have more control
        port = kwargs.pop("port", ARD_NANO_MAGIC_PORT)

        kwargs.setdefault('baudrate', 256000)
        kwargs.setdefault('parity', serial.PARITY_NONE)
        kwargs.setdefault('stopbits', serial.STOPBITS_ONE)
        kwargs.setdefault('bytesize', serial.EIGHTBITS)
        kwargs.setdefault('timeout', 0.5)  # for read, in sec

        ser = serial.Serial(**kwargs)
        ser.port = port

        if force and ser.is_open:
            ser.close()

        ser.open()

        if not ser.is_open:
            raise RuntimeError("After initialisation serial port is still closed.")

        ser.reset_input_buffer()
        ser.reset_output_buffer()

        if shared_channels:
            from driver.channels import SharedChannels
            mem_obj = SharedChannels(create=True, force=force)
            channels = mem_obj.channels
        else:
            mem_obj = None
            channels = np.zeros(_max_channels, dtype=int)

        self._mem_obj = mem_obj
        self.channels = channels
        self.ser = ser
        self.reply = ''

        atexit.register(self.__del__)

    def _log_replies(self):

        if inwait := self.ser.in_waiting:
            self.reply += self.ser.read_until(serial.LF, inwait).decode()

            *replies, self.reply = self.reply.split('\n')

            # the uC only reports warnings and errors
            for r in replies:
                logger.warning(r)

    def mk_msg(self):
        channels = self.channels
        logger.info(f'will send:{channels}')

        # target, Arduino, is little endian
        if sys.byteorder == 'big':
            channels = channels.byteswap()

        msg = MSG_SYNC_HEADER + channels.tobytes()
        return msg

    def run(self):

        vals0 = self.channels.copy()

        while True:

            if all(vals0 == self.channels):
                time.sleep(0.000000001)
                self._log_replies()
                continue

            vals0[:] = self.channels

            msg = self.mk_msg()
            self.ser.write(msg)
            logger.debug(f'wrote:{msg}')

            # wait for bytes to receive
            # time.sleep(0.0005)

            self._log_replies()

    def close(self):

        if self._mem_obj is not None:
            self._mem_obj.close()
            self._mem_obj = None

        if self.ser is not None:
            self.ser.close()
            self.ser = None

    def __del__(self):
        self.close()


if __name__ == '__main__':
    _logging.basicConfig(level=_logging.WARNING)
    s = SerialDriver()
    try:
        s.run()
    finally:
        s.close()
