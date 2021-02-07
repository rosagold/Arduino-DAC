import atexit
import time
from multiprocessing.shared_memory import ShareableList, SharedMemory
import multiprocessing.resource_tracker as resource_tracker
from driver.common import _max_channels
import numpy as np
import logging

logger = logging.getLogger(__name__)

_default_name = 'default_shared_list'


class _SharedChannels:

    def __init__(self, name=None, create=False, dtype=np.int16):

        self._2nd = getattr(self, '_2nd', False)
        self._shm = None
        self._channels = None
        self._clients = None
        self._alive = None
        self._create = create

        if name is None:
            name = _default_name

        # we need to store if the server is alive also
        # we want to keep track how many clients have access
        # to the shared memory, so we hold this information
        # in the shared memory itself.
        alive = np.array([0], dtype=np.int8)
        cl = np.array([0], dtype=np.int32)
        ch_arr = np.array([0] * _max_channels, dtype=dtype)
        nbytes = ch_arr.nbytes + cl.nbytes + alive.nbytes

        try:
            self._shm = SharedMemory(create=create, size=nbytes, name=name)
        except FileNotFoundError:
            raise RuntimeError("no server. start a with create=True")
        except FileExistsError:
            if self._2nd:
                raise
            self._2nd = True
            print('again')
            self._shm = SharedMemory(name=name)
            self._shm.close()
            self._shm.unlink()
            self.__init__(name=name, create=create, dtype=dtype)
            return

        # make numpy arrays for easy access
        buffer = self._shm.buf[cl.nbytes + alive.nbytes:]
        self._channels = np.ndarray(ch_arr.shape, dtype=ch_arr.dtype, buffer=buffer)

        buffer = self._shm.buf[alive.nbytes:]
        self._clients = np.ndarray(cl.shape, dtype=cl.dtype, buffer=buffer)

        buffer = self._shm.buf
        self._alive = np.ndarray(alive.shape, dtype=alive.dtype, buffer=buffer)

        if self._create:
            self._channels[:] = 0
            self._clients[:] = 0
            self._alive[:] = 1
            logger.info('server created')

        else:
            self._clients[:] += 1
            logger.info(f'client created, we have now: {self.clients}')

        atexit.register(self.close)

    @property
    def channels(self):
        return self._channels

    @property
    def clients(self):
        return self._clients[0]

    @property
    def server_running(self):
        return self._alive[0]

    def close(self):
        logger.debug(f'cleanup called')

        # prevent double cleanup
        if self._shm is None:
            return

        if self._create:
            logging.info(f'teardown server, active clients: {self.clients}')
            self._alive[:] = 0
            self._shm.close()
            self._shm.unlink()

        else:
            self._clients -= 1
            clients = self.clients
            self._shm.close()
            # see python bug #39959
            # https://bugs.python.org/issue39959
            resource_tracker.unregister(self._shm._name, "shared_memory")
            logging.debug(f'closing client, left clients: {clients}')

        self._shm = None

    def __del__(self):
        logger.debug(f'_SharedChannels.__del__')
        self.close()


class Channel:

    def __init__(
        self, nr, ch_min=0, ch_max=4095, normalize=False, vmin=None, vmax=None
    ):
        self._shc = None

        if not 0 <= nr < _max_channels:
            raise ValueError(f'nr out of bounds: 0 <= nr < {_max_channels}')

        self._shc = _SharedChannels()
        self.nr = nr

        self.ch_min = ch_min
        self.ch_max = ch_max

        self.normalize = normalize
        self.vmin = vmin
        self.vmax = vmax

    def _validate_connection(self):
        if not self._shc.server_running:
            raise ConnectionAbortedError('server died. sorry.')

    def write(self, value):
        self._validate_connection()

        if self.normalize:
            value = self._normalize(value, self.vmin, self.vmax, self.ch_min, self.ch_max)

        value = max(value, self.ch_min)
        value = min(value, self.ch_max)

        self._shc.channels[self.nr] = value

    def read(self):
        self._validate_connection()
        return self._shc.channels[self.nr]

    @staticmethod
    def _normalize(v, vmin, vmax, resmin, resmax):
        return resmin + (v - vmin) * (resmax - resmin) / (vmax - vmin)

    def close(self):
        if self._shc is not None:
            self._shc.close()

    def __del__(self):
        logger.debug('Channel.__del__')
        self.close()


if __name__ == '__main__':
    # shch = _SharedChannels(create=True)
    logging.basicConfig(level=logging.DEBUG)
    ch = Channel(0)
    for i in range(50):
        time.sleep(0.1)
        ch.write(i)
    # ch.close()
