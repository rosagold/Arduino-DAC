ArduinoNano, SPI, 12bit-DAC
=====================

Connect ArduinoNano via SPI with a MCP4921, a 12-bit digital to analog converter (DAC).
One can send numbers [0,4095] via arduino IDE "Serial Monitor" that will set the 
DAC which will than output the corresponding [0..~5] voltage on its output. 

ArduinoNano
-----------
- board rev 3
- AVR Part: ATmega328P

in IDE use:
 - board: arduino Nano
 - processor:ATmega328P (old Bootloader)
 - programmer: AVRISP mkll
 - use SerialMonitor with baud 9600 and lineend '\n'

Pins: 10 (SS), 11 (MOSI), 12 (MISO), 13 (SCK). 
> These pins support SPI communication using the SPI library.

DAC
---
- wire Vref & Vcc to 5V (arduino)
- wire LDAC & Vss to GND (arduino) 
- wire CS to SS, SCK to SCK and SDI to MOSI
- measure between GND and Vout with a multimeter

Schematics
----------
Use easyEDA online [1] or download the free desktop version to open the schematics or
simply view the pdf :P.


[1] https://easyeda.com/editor



