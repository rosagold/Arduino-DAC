
#include <SPI.h>
#include "channels.h"

const uint8_t P3 = 3;
const uint8_t P10 = 10;

const uint32_t SPI_BAUD = 20000000;
const unsigned long SERIAL_BAUD = 256000;

// massage looks like so:
// 'channel-nr,value', eg. '0,4095'
// channelnr (1b) + ',' (1b) + val (1-4b) + '\n' (1b)
const uint8_t MIN_MSG_SZ = 4;

// container for channels
const uint8_t CHANNELS = 2;
channel_t channels[CHANNELS] = {
        {.cs_pin = P10, .value = 0},
        {.cs_pin = P3, .value = 0},
};



//#define DEBUG




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

    if (ch >= CHANNELS || val > 0xFFF){
        return 3;
    }

    channels[ch].value = val;

    return 0;

}


int8_t parse_msg_str(channel_t *channels){

    String s;
    uint8_t ch = 255;
    uint16_t val = 0xFFFF;
    uint8_t l;

    s = Serial.readStringUntil(',');
    ch = s.toInt();
    if (s.length() != 1 || ch >= CHANNELS){
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


int8_t ch = -1;
void loop() {

    if(Serial.available() >= MIN_MSG_SZ){

        ch = parse_msg_str(channels);

        // something went wrong
        if (ch < 0){
            Serial.println("err");
            Serial.flush();

        // all ok
        } else {
            write_channel(ch);
        }

    }
}
