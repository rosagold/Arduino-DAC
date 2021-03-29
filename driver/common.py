

import os

__nr = None
__f = os.path.dirname(__file__) + '/../firmware/number_of_channels.h'
with open(__f, 'r') as __f:
    code = '#define NR_OF_CHANNELS '
    for line in __f.readlines():
        if line.startswith(code):
            __nr = int(line.strip(code))

    if not 0 < __nr <= 255:
        raise RuntimeError("parsing number of channels failed very likely")

_max_channels = __nr

