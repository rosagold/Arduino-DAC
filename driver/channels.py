__all__ = ['SharedChannels', 'Channel']

import atexit
import time
from multiprocessing.shared_memory import SharedMemory
import multiprocessing.resource_tracker as resource_tracker
from driver.common import _max_channels
import numpy as np
import logging
from functools import wraps

_default_name = 'default_shared_list'
_SVR_RUNNING = 1
_SVR_CLOSED = 0

logger = logging.getLogger(__name__)


def log_method_name(func):
    """
    Decorator that logs the method name on call
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        logging.debug(f"{self.__class__.__name__}.{func.__name__}")
        return func(self, *args, **kwargs)

    return wrapper


class _SharedMemoryServer(SharedMemory):

    @log_method_name
    def __init__(self, nbytes, name=None, force=False):
        self._linked = False

        if name is None:
            name = _default_name

        try:
            super().__init__(name=name, create=True, size=nbytes)
        except FileExistsError:
            if not force:
                raise
            super().__init__(name=name)

        self._linked = True
        atexit.register(self.close)

    @log_method_name
    def close(self):
        super().close()
        if self._linked:
            logging.debug(f"{self.__class__.__name__}.close: unlink shared memory")
            self.unlink()
        self._linked = False

    @log_method_name
    def __del__(self):
        self.close()


class _SharedMemoryClient(SharedMemory):

    @log_method_name
    def __init__(self, name=None):

        self._registered = False

        if name is None:
            name = _default_name

        try:
            super().__init__(name=name)
        except FileNotFoundError:
            raise RuntimeError("connecting to shared_memory failed, probably no server running")

        self._registered = True
        atexit.register(self.close)

    @log_method_name
    def close(self):
        super().close()

        # see python bug #39959
        # https://bugs.python.org/issue39959
        if self._registered:
            logging.debug(f"{self.__class__.__name__}.close: unregister from resource_tracker")
            resource_tracker.unregister(self._name, "shared_memory")
        self._registered = False

    @log_method_name
    def __del__(self):
        self.close()


class SharedChannels:

    @log_method_name
    def __init__(self, name=None, create=False, dtype=np.int16, force=False):

        self._shm = None
        self._channels = None
        self._clients = None
        self._status = None
        self._is_server = create

        if name is None:
            name = _default_name

        # we need to store if the server is alive also
        # we want to keep track how many clients have access
        # to the shared memory, so we hold this information
        # in the shared memory itself.
        st = np.array([0], dtype=np.int8)
        cl = np.array([0], dtype=np.int32)
        ch = np.array([0] * _max_channels, dtype=dtype)

        if self._is_server:
            nbytes = ch.nbytes + cl.nbytes + st.nbytes
            self._shm = _SharedMemoryServer(nbytes, name=name, force=force)
        else:
            self._shm = _SharedMemoryClient(name=name)

        self._status = self._mk_shared_array(st, offset=0)
        self._clients = self._mk_shared_array(cl, offset=st.nbytes)
        self._channels = self._mk_shared_array(ch, offset=cl.nbytes + st.nbytes)

        if self._is_server:
            self._status[:] = _SVR_RUNNING
            self._clients[:] = 0
            self._channels[:] = 0
            logger.info('server created')

        else:
            self._clients += 1
            logger.info(f'client created, we have now: {self.clients}')

    def _mk_shared_array(self, ref, offset):
        buffer = self._shm.buf[offset:]
        shape, dtype = ref.shape, ref.dtype
        return np.ndarray(shape=shape, dtype=dtype, buffer=buffer)

    @property
    def channels(self):
        return self._channels

    @property
    def clients(self):
        return self._clients[0]

    @property
    def status(self):
        return self._status[0]

    @log_method_name
    def close(self):

        # prevent double cleanup
        if self._shm is None:
            return

        if self._is_server:
            self._status[:] = _SVR_CLOSED
            logging.info(f'{self.__class__.__name__}.close: teardown server, active clients: {self.clients}')

        else:
            self._clients -= 1
            logging.debug(f'{self.__class__.__name__}.close: closing client, left clients: {self.clients}')

        self._shm.close()
        self._shm = None

    @log_method_name
    def __del__(self):
        self.close()


class Channel:

    def __init__(
        self, nr, ch_min=0, ch_max=4095, normalize=False, vmin=None, vmax=None
    ):
        self._shc = None

        if not 0 <= nr < _max_channels:
            raise ValueError(f'nr out of bounds: 0 <= nr < {_max_channels}')

        self._shc = SharedChannels()
        self.nr = nr

        self.ch_min = ch_min
        self.ch_max = ch_max

        self.normalize = normalize
        self.vmin = vmin
        self.vmax = vmax

    def _validate_connection(self):
        if not self._shc.status == _SVR_RUNNING:
            raise ConnectionAbortedError('server died. sorry.')

    def write(self, value):
        self._validate_connection()

        if self.normalize:
            value = self._normalize(value, self.vmin, self.vmax, self.ch_min, self.ch_max)

        # ensure we not exceed the limits
        value = max(value, self.ch_min)
        value = min(value, self.ch_max)

        self._shc.channels[self.nr] = value

    def read(self):
        self._validate_connection()
        return self._shc.channels[self.nr]

    @staticmethod
    def _normalize(v, vmin, vmax, resmin, resmax):
        return resmin + (v - vmin) * (resmax - resmin) / (vmax - vmin)

    @log_method_name
    def close(self):
        self._shc.close()

    @log_method_name
    def __del__(self):
        if self._shc is not None:
            self.close()


if __name__ == '__main__':
    # shch = SharedChannels(create=True)
    logging.basicConfig(level=logging.DEBUG)
    ch = Channel(0)
    for i in range(50):
        time.sleep(0.1)
        ch.write(i)
        print(i)
    ch.close()
