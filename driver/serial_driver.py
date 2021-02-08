import serial
import time
import numpy as np
from common import _max_channels
import logging
import atexit

DEFAULT_PORT = "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"
logger = logging.getLogger(__name__)


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

    def __init__(self, force=False, shared_channels=False, **kwargs):

        self._mem_obj = None
        self.ser = None

        # if port is passed as kwarg the port is opened
        # in init, but we want to have more control
        port = kwargs.pop("port", DEFAULT_PORT)

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
            from driver.channels import _SharedChannels
            mem_obj = _SharedChannels(create=True)
            channels = mem_obj.channels
        else:
            mem_obj = None
            channels = np.zeros(_max_channels, dtype=int)

        self._mem_obj = mem_obj
        self.channels = channels
        self.ser = ser

        atexit.register(self.__del__)

    def _get_answer(self):
        if self.ser.in_waiting:
            return self.ser.read_until('\n').decode()
        return None

    def run(self):

        ch = 0
        old_val = self.channels[ch]

        while True:

            if (val := self.channels[ch]) == old_val:
                time.sleep(0.0001)
                continue

            old_val = val
            logger.info(f'ch:{ch}, val:{val}')

            msg = f'{ch},{val}\n'
            self.ser.write(msg.encode())

            time.sleep(0.001)

            # the uC only reports warnings and errors
            if (asw := self._get_answer()) is not None:
                logging.warning(asw)

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
    logging.basicConfig(level=logging.DEBUG)
    s = SerialDriver(shared_channels=True)
    try:
        s.run()
    finally:
        s.close()
