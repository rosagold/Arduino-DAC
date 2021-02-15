//
// Created by rg on 14.02.21.
//

#ifndef FIRMWARE_SERIAL_LOGGING_H
#define FIRMWARE_SERIAL_LOGGING_H

#define _log(...)
#define _logln(...)
#define _debug(...)
#define _debugln(...)
#define _debuglog_buffer_fill()

# if DEBUG_LEVEL >= 1
#undef _log
#define _log            Serial.print
#undef _logln
#define _logln          Serial.println
# endif

# if DEBUG_LEVEL >= 2
#undef _debug
#define _debug          Serial.print
#undef _debugln
#define _debugln        Serial.println

#undef _debuglog_buffer_fill
#define _debuglog_buffer_fill()   \
do{ \
    _debug("buf: "); \
    _debug(Serial.available()); \
    _debugln("/64"); \
} while(0)
# endif


#endif //FIRMWARE_SERIAL_LOGGING_H
