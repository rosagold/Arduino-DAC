import atexit
from multiprocessing.shared_memory import ShareableList, SharedMemory
from common import _max_channels

_default_name = 'default_shared_list'


class _SharedChannels:

    def __init__(self, name=None):

        if name is None:
            name = _default_name

        try:

            l = [0] * _max_channels
            shared = ShareableList(l, name=name)
            clients = ShareableList([0], name=name + '_cl')

        except FileExistsError:

            shared = ShareableList(None, name=name)
            clients = ShareableList(None, name=name + '_cl')

        # shared memory channels
        self._channels = shared

        # keep track how many clients have access
        # to the shared memory. this is also stored
        # in shared memory.
        self._clients = clients
        self._clients[0] += 1

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
        if self._dead:
            return
        self._dead = True

        self._clients[0] -= 1
        clients = self.clients

        self._clients.shm.close()
        self._channels.shm.close()

        if clients == 0:
            self._clients.shm.unlink()
            self._channels.shm.unlink()

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
