import atexit
from multiprocessing.shared_memory import ShareableList, SharedMemory
from driver.common import _max_channels
import numpy as np

_default_name = 'default_shared_list'


class _SharedChannels:

    def __init__(self, name=None, dtype=np.int16):

        if name is None:
            name = _default_name

        # we want to keep track how many clients have access
        # to the shared memory, so we hold this information
        # in the shared memory itself.
        cl = np.array([0], dtype=np.int32)
        ch_arr = np.array([0]*_max_channels, dtype=dtype)
        nbytes = ch_arr.nbytes + cl.nbytes

        try:
            shm = SharedMemory(create=True, size=nbytes, name=name)
            init = True
        except FileExistsError:
            shm = SharedMemory(name=name)
            init = False

        # make numpy arrays for easy access
        ch_arr = np.ndarray(ch_arr.shape, dtype=ch_arr.dtype, buffer=shm.buf[cl.nbytes:])
        cl = np.ndarray(cl.shape, dtype=cl.dtype, buffer=shm.buf)

        if init:
            ch_arr[:] = 0
            cl[:] = 0

        # shared memory channels
        self._shm = shm
        self._channels = ch_arr
        self._clients = cl

        # we're a client
        self._clients += 1
        self._dead = False
        atexit.register(self._cleanup)

    @property
    def channels(self):
        return self._channels

    @property
    def clients(self):
        return self._clients[0]

    def _cleanup(self):
        # prevent double cleanup
        print('cleanup called')
        if self._dead:
            return
        print('do cleanup')
        self._dead = True

        self._clients -= 1
        clients = self.clients

        self._shm.close()

        if clients == 0:
            print('unlink called')
            self._shm.unlink()

    def __del__(self):
        self._cleanup()


class Channel:

    def __init__(
        self, nr, ch_min=0, ch_max=4095, normalize=False, vmin=None, vmax=None
    ):

        if not 0 <= nr < _max_channels:
            raise ValueError(f'nr out of bounds: 0 <= nr < {_max_channels}')

        self._shared = _SharedChannels()
        self.nr = nr

        self.ch_min = ch_min
        self.ch_max = ch_max

        self.normalize = normalize
        self.vmin = vmin
        self.vmax = vmax

    def write(self, value):
        if self.normalize:
            value = self._normalize(value, self.vmin, self.vmax, self.ch_min, self.ch_max)

        value = max(value, self.ch_min)
        value = min(value, self.ch_max)

        self._shared.channels[self.nr] = value

    def read(self):
        return self._shared.channels[self.nr]

    @staticmethod
    def _normalize(v, vmin, vmax, resmin, resmax):
        return resmin + (v - vmin) * (resmax - resmin) / (vmax - vmin)


if __name__ == '__main__':
    ch2 = Channel(2)
    print(ch2._shared.clients)
