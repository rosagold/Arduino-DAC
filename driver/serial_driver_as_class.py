import serial
import time
import numpy as np
from driver.common import _max_chanels
import logging

log = logging.getLogger()


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

    def __init__(self, force=False, **kwargs):
        default_port = "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"

        kwargs.setdefault("port", default_port)
        kwargs.setdefault('baudrate', 256000)
        kwargs.setdefault('parity', serial.PARITY_NONE)
        kwargs.setdefault('stopbits', serial.STOPBITS_ONE)
        kwargs.setdefault('bytesize', serial.EIGHTBITS)
        kwargs.setdefault('timeout', 0.5)  # for read, in sec

        self.ser = serial.Serial(**kwargs)

        if force and self.ser.is_open:
            self.ser.close()

        self.ser.open()

        if not self.ser.is_open:
            raise RuntimeError("After initialisation serial port is still closed.")

        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        self.channels = np.zeros(_max_chanels, dtype=int)

    def _get_answer(self):
        if self.ser.in_waiting:
            return self.ser.read_until('\n').decode()
        return None

    def run(self):
        while True:
            ch = 0
            val = self.channels[ch]
            msg = f'{ch},{val}\n'.encode()
            self.ser.write(msg)

            time.sleep(0.001)

            # todo log this
            # a = self._get_answer()
            # if a is not None:
            #     print(a)

    def __del__(self):
        try:
            self.ser.close()
        except Exception:
            pass

    def close(self):
        # this just calls,
        # does not delete
        self.__del__()


if __name__ == '__main__':
    s = SerialDriver()
    s.run()
