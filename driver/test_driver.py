import time
import logging

from channels import SharedChannels

logger = logging.getLogger(__name__)


class TestDriver:

    def __init__(self):
        self.mem_obj = SharedChannels(create=True)
        self.channels = self.mem_obj.channels

    # noinspection PyTypeChecker
    def run(self):

        vals0 = self.channels.copy()
        vals1 = self.channels.copy()

        while True:

            vals1[:] = self.channels

            if all(vals1 == vals0):
                time.sleep(0.0000001)
                continue

            vals0[:] = vals1

            logger.info(f'{vals0}')

    def close(self):
        if self.mem_obj is not None:
            self.mem_obj.close()
            self.mem_obj = None

    def __del__(self):
        self.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    drv = TestDriver()
    drv.run()
