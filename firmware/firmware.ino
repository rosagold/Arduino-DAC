
// increase buffer size
//#define SERIAL_RX_BUFFER_SIZE 256
#include "HardwareSerial.h"
#include <SPI.h>
#include "string.h"
#include "number_of_channels.h"
#include "channels.h"

#define DEBUG_LEVEL   1
#include "serial_logging.h"


#define BIN_MESSAGE
//#define STR_MESSAGE

#if defined(BIN_MESSAGE) && defined(STR_MESSAGE)
#error "just one can be defined"
#endif

#define SYNC_ERR  4
#define SERIAL_ERR  5
#define SERIAL_OVERFLOW_ERR  6

#define MASK_12BIT 0x0FFF


static const uint32_t SPI_BAUD = 20000000;
static const unsigned long SERIAL_BAUD = 256000;

static const uint16_t SYNC_HEADER = 0xEEEE;
static const uint8_t SYNC_HEADER_SZ = 2;

static const uint32_t CONTENT_SZ = sizeof(uint16_t) * NR_OF_CHANNELS;
static const uint32_t MSG_SZ = SYNC_HEADER_SZ + CONTENT_SZ;
static const uint32_t OVERFLOW =  MSG_SZ * 3;


// container for channels
// ======================
//
// - .ctrl : defines first 4-bits, depending on the chip
//
//     REGISTER 5:
//     WRITE COMMAND REGISTER FOR MCP4921 (12-BIT DAC)  [1]
//     WRITE COMMAND REGISTER FOR MCP4922 (2-channel 12-BIT DAC)  [2]
//      ____________________________________________________
//     | nA/B | BUF | nGA | nSHDN |      D11:D0 (data)      |
//     |----------------------------------------------------|
//      15                                                 0
//
//     For [1] the first bit must be '0', otherwise the command is ignored
//     For [2] the first bit select channel A ('0') or channel B ('1')
//
// - .pin : defines the chip select (CS) pin
//      D7  - channel 4 / 5
//      D8  - channel 2 / 3
//      D9  - channel 1
//      D10 - channel 0
//      D11 - (reserved) MOSI (SPI-data)
//      D12 - (NC)
//      D13 - (reserved) SCK (SPI-clock)
// - .value : hold the 12-bit value to analogize
//
channel_t channels[NR_OF_CHANNELS] = {
        {.pin = 10, .ctrl = 0x3000, .value = 0},  // ch 0
        {.pin = 9,  .ctrl = 0x3000, .value = 0},  // ch 1
        {.pin = 8,  .ctrl = 0x3000, .value = 0},  // ch 2
        {.pin = 8,  .ctrl = 0xB000, .value = 0},  // ch 3
        {.pin = 7,  .ctrl = 0x3000, .value = 0},  // ch 4
        {.pin = 7,  .ctrl = 0xB000, .value = 0},  // ch 5
};


static inline void spi_write(uint8_t pin, uint16_t val){
    // enable Chip Select
    digitalWrite(pin, LOW);

    SPI.transfer16(val);

    // disable Chip Select
    digitalWrite(pin, HIGH);
}


static inline void send_err(uint8_t err){
    Serial.print("ERR: ");
    switch (err) {
        case SYNC_ERR:
            Serial.print("sync err");
            break;
        case SERIAL_ERR:
            Serial.print("serial read err ");
            break;
        case SERIAL_OVERFLOW_ERR:
            Serial.print("overflow, to much data");
            break;
        default:
            Serial.print("read error");
    }
    Serial.print("(");Serial.print(err);Serial.println(")");
}


void setup() {
    Serial.begin(SERIAL_BAUD);

    Serial.print("SERIAL_RX_BUFFER_SIZE=");
    Serial.println(SERIAL_RX_BUFFER_SIZE);

    // init all chip selects
    for (channel_t ch : channels){
        pinMode(ch.pin, OUTPUT);
        digitalWrite(ch.pin, HIGH);
    }

    // Initializes the SPI bus by setting SCK, MOSI,
    // and SS to outputs, pulling SCK and MOSI low, and SS high.
    SPI.begin();
    SPI.beginTransaction(SPISettings(SPI_BAUD, MSBFIRST, SPI_MODE3));
}


#ifdef BIN_MESSAGE
#define serial_overflow  (Serial.available() > OVERFLOW)

static inline void serial_flush_rx(void){
    do {} while (Serial.read() != -1);
}

// return -1 on overflow, 0 otherwise
// if flush is true, serial rx buffer is emptied
// on buffer overflow
static inline int8_t serial_wait(uint8_t nbytes, bool flush = true){
    if (serial_overflow){
        send_err(SERIAL_OVERFLOW_ERR);
        if (flush){
            serial_flush_rx();
        }
        return -1;
    }

    do {} while (Serial.available() < nbytes);
    return 0;
}

static inline void sync(void){
    static const uint8_t *sync = (uint8_t*) &SYNC_HEADER;
    volatile uint8_t b0, b1;

    _debuglog_buffer_fill();

    while (true) {

        // we assume we're in sync
        l_insync:

        if (serial_wait(2)) {
            continue;
        }

        b0 = Serial.read();
        b1 = Serial.read();
        if (b0 == sync[0] && b1 == sync[1]) {
            return;
        }

        // if we come here, we lost sync, we
        // need to check every single byte, if
        // it is the start of our sync header
        send_err(SYNC_ERR);

        while(true) {
            _debugln(b0);
            _debuglog_buffer_fill();

            if (serial_wait(1)) {
                // on error, serial_wait flushes the rx-
                // buffer, so maybe we are still not in sync,
                // but we can safely read 2 bytes now.
                goto l_insync;
            }

            b0 = b1;
            b1 = Serial.read();
            if (b0 == sync[0] && b1 == sync[1]) {
                _debugln(b1);
                return;
            }
        }
    }
}

void loop() {

    static volatile uint16_t old_msg[NR_OF_CHANNELS] = {0};
    static volatile uint16_t new_msg[NR_OF_CHANNELS] = {0};
    static uint32_t nbytes;

    sync();
    _debugln("sync found");

    if(serial_wait(CONTENT_SZ)){
        return;
    }

    nbytes = Serial.readBytes((uint8_t *)&new_msg, CONTENT_SZ);

    if (nbytes != CONTENT_SZ){
        send_err(SERIAL_ERR);
        return;
    }

    for (uint8_t i = 0; i < NR_OF_CHANNELS; i++){

        _debug("ch");_debug(i);_debug(": ");_debugln(new_msg[i]);

        if ((new_msg[i] == old_msg[i]) || (channels[i].pin == NOT_A_PIN)){
            continue;
        }
        spi_write(channels[i].pin, channels[i].ctrl | (new_msg[i] & MASK_12BIT));
    }

    memcpy((uint8_t *)old_msg, (uint8_t*)new_msg, CONTENT_SZ);
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
            spi_write(channels[ch].pin, channels[ch].value);

        // something went wrong
        } else {
            Serial.println("err");
            Serial.flush();
        }
    }
}
#endif /* STR_MESSAGE */