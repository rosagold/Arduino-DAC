from multiprocessing import Lock
from multiprocessing.shared_memory import ShareableList, SharedMemory
import time

class SharedChannels:
    __instance = None

    def __new__(cls, *args, **kwargs):

        if cls.__instance is None:
            cls.__instance = object.__new__(cls)

        return cls.__instance

    @classmethod
    def __make_shared(cls):
        try:

        l = [0] * self._max_chanels
        self.memarr = SharedMemory(l, name=self.__shmem_name)




if __name__ == '__main__':
    sd = SerialDriver()
    sd.enqueue(0, 0)

    for i in range(200):
        v = 20+i*10
        print(v)
        time.sleep(0.01)
        sd.enqueue(0, v)
