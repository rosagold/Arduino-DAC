
#include <SPI.h>
#include "channels.h"
#include "string.h"

const uint8_t P3 = 3;
const uint8_t P10 = 10;

const uint32_t SPI_BAUD = 20000000;
const unsigned long SERIAL_BAUD = 256000;

// container for channels
channel_t channels[NR_OF_CHANNELS] = {
        {.cs_pin = P10, .value = 0},
        {.cs_pin = P3, .value = 0},
};



//#define DEBUG
#define BIN_MESSAGE
//#define STR_MESSAGE




static void inline spi_write(uint8_t cs_pin, uint16_t val){

#ifdef DEBUG
    Serial.print("spi: pin=");
    Serial.print(cs_pin);
    Serial.print(", val=");
    Serial.println(val);
#endif

    val = val | 0x3000;

    // enable Chip Select
    digitalWrite(cs_pin, LOW);

    SPI.transfer16(val);

    // disable Chip Select
    digitalWrite(cs_pin, HIGH);
}


static void inline write_channel(uint8_t nr){
    spi_write(channels[nr].cs_pin, channels[nr].value);
}

uint8_t parse_msg_bytes(channel_t *channels){

    uint8_t success = 0;
    uint8_t ch = 255;
    uint16_t val = 0xFFFF;

    success = Serial.readBytes(&ch, 1);
    if (~success){
        return 1;
    }

    success = Serial.readBytes((uint8_t*)&val, 4);
    if (~success){
        return 2;
    }

    if (ch >= NR_OF_CHANNELS || val > 0xFFF){
        return 3;
    }

    channels[ch].value = val;

    return 0;

}

void setup() {
    Serial.begin(SERIAL_BAUD);

    // init all chip selects
    for (channel_t ch : channels){
        pinMode(ch.cs_pin, OUTPUT);
        digitalWrite(ch.cs_pin, HIGH);
    }

    // Initializes the SPI bus by setting SCK, MOSI,
    // and SS to outputs, pulling SCK and MOSI low, and SS high.
    SPI.begin();
    SPI.beginTransaction(SPISettings(SPI_BAUD, MSBFIRST, SPI_MODE3));
}


#ifdef BIN_MESSAGE


uint8_t *find_sync(uint8_t *start, uint8_t *end){
    uint8_t *ptr = NULL;
    uint32_t count = end - start;

    // find the sync 2 bytes (0xFF,0xFF)
    while (count > 0){

        // find ptr to 0xFF
        ptr = (uint8_t *) memchr(start, 0xFF, count);

        // not found
        if (!ptr){
            break;
        }

        // found
        if (*(ptr + 1) == 0xFF){
            break;
        }

        // if we come here we found a 0xFF, but not
        // the second, so it was probably just a value.
        // We continue search maybe the sync bytes are
        // later in the buffer.
        start = ptr + 2;
        count = end - start;
    }

    return ptr;
}

// find the Sync bytes in the current message and read
// from stream until we have the message after the Sync
// complete. return 0 on success, non-zero otherwise.
// this works inplace.
int8_t resync_serial(msg_t *broken){

    static uint32_t sz = sizeof(msg_t);
    uint8_t *head = (uint8_t *) broken;
    uint8_t *end = head + sz;
    uint8_t *ptr = NULL;
    uint8_t *tmp ;

    // find the LAST sync
    tmp = find_sync(head, end);
    while (tmp) {
        ptr = tmp;
        tmp = find_sync(++tmp, end);
    }

    // copy from found sync byte up to end of the broken message to new buffer
    if (ptr) {
        memcpy()
        for (; ptr < end ; ++head, ++ptr){
            *head = *ptr;
        }
    }

    sz = end - head;
    while (Serial.available() < sz){
        delay(1);
    }
    sz = Serial.readBytes(&head, sz);

    return 0;
}

void loop() {

    static int8_t ch = -1;
    static msg_t msg;
    static uint32_t msg_sz = sizeof(msg_t);
    static uint32_t nbytes;
    static uint32_t err;

    if(Serial.available() >= msg_sz){
        err = 0;

        nbytes = Serial.readBytes((uint8_t *)&msg, msg_sz);

        if (nbytes != msg_sz){
            err = 1;
            goto error;
        }

        if (msg.sync != 0xFFFF){
            err = resync_serial(&msg);
            if (err){
                goto error;
            }
        }


        // something went wrong
        if (ch < 0){

        // all ok
        } else {
            write_channel(ch);
        }

    }

    return;

    error:
    Serial.println("err");
    Serial.flush();
}
#endif /* BIN_MESSAGE */

#ifdef STR_MESSAGE
// we a string messages for each single channels

// massage looks like so:
// 'channel-nr,value', eg. '0,4095'
// channelnr (1b) + ',' (1b) + val (1-4b) + '\n' (1b)
const uint8_t MIN_MSG_SZ = 4;


int8_t parse_msg_str(channel_t *channels){

    String s;
    uint8_t ch = 255;
    uint16_t val = 0xFFFF;
    uint8_t l;

    s = Serial.readStringUntil(',');
    ch = s.toInt();
    if (s.length() != 1 || ch >= NR_OF_CHANNELS){
        return -1;
    }

    s = Serial.readStringUntil('\n');
    l = s.length();
    val = s.toInt();
    if ( l <= 0 || l > 4 || val > 0x0FFF){
        return -2;
    }

    channels[ch].value = val;

    return ch;
}


void loop() {

    static int8_t ch = -1;

    if(Serial.available() >= MIN_MSG_SZ){

        ch = parse_msg_str(channels);

        // all ok
        if (ch >= 0){
            write_channel(ch);

        // something went wrong
        } else {
            Serial.println("err");
            Serial.flush();
        }
    }
}
#endif /* STR_MESSAGE */