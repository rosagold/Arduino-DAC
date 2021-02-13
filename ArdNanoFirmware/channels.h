//
// Created by rg on 29.01.21.
//

#ifndef UNTITLED1_CHANNELS_H
#define UNTITLED1_CHANNELS_H

#include "Arduino.h"

#define  NR_OF_CHANNELS   2

typedef struct {
    int8_t cs_pin;
    uint16_t value;
} channel_t ;

typedef struct {
    uint16_t sync ;
    uint16_t values[NR_OF_CHANNELS];
} msg_t;

#endif //UNTITLED1_CHANNELS_H
