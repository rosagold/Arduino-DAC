Reverse visuals project
=====================
The prototype: 6 channels, each with an independent DAC.
Auto-Generate a number on PC in range `[0, 4095]` and set a channel to the corresponding Voltage `[0,5] V`. 

Hardware
--------

### ArduinoNano
- board rev 3
- AVR Part: ATmega328P

- in IDE use:
    - board: arduino Nano
    - processor:ATmega328P (old Bootloader)
    - programmer: AVRISP mkll


### DAC
- `Vref` and `Vcc` to 5V (arduino)
- `LDAC` and `Vss` to `GND` (arduino)
- `CS` the channel-pins (see SPI)
- `SCK` to `SCK` and `SDI` to `MOSI`
- measure between GND and Vout with a multimeter


### SPI
- connects the Nano with all DACs
- `D11` (MOSI), `D12` (MISO - not used here), `D13` (SCK). 
- channel `0`, use Arduinos `D10` as chip-select (CS)
- channel `1`, use Arduinos `D9` as chip-select (CS)
- channel `3 / 4`, use Arduinos `D8` as chip-select (CS), use a address-bit in SPI-message to differentiate channels
- channel `5 / 6`, use Arduinos `D8` as chip-select (CS), use a address-bit in SPI-message to differentiate channels

### Serial
- connects the PC with the Nano 
- baudrate of `256000` 
- message format:
  ``` 
  [ sync , ch0,   ,ch1    , ch2  , ... ]
  [0xEEEE, 0xXXXX, 0xXXXX, 0xXXXX, ... ]
  ```
  values are `12bit` integer represented in 16 bit. upper bits are discarded.
- all channel-values are always transmitted at once


Schematics
----------
Use easyEDA online [1] or download the free desktop version to open the schematics or
simply view the pdf :P. 
The schematics only show a single DAC connected to Arduino. wire all the same except the CS signal.

[1] https://easyeda.com/editor

Prototype
---------
![Front](/photo_front.jpg)


Software
--------
I will refer the piece of binary blob, that is loaded to the Arduino as the *firmware* and the driver and stuff
that run on the PC as the *software*.

How to use the software:
- connect board with PC via USB

- start `serial_driver.py` and keep it running (server)

- the server will print log/debug messages returned from the firmware
  
- in any other thread / process or even a different script, create a channel instance and write to it:
  ```python
  import channels 
  ch  = channels.Channel(nr=0)
  # at any time
  ch.write(value)
  ```
  
- one can create multiple instances of the same channel, which then are concurrent and possibly create a race-condition,
  between each other. Nevertheless, this should work and is intended (and honestly, it wasn't easy to implement)
  
- if the server dies, and a client try to write, it will fail hard. If the server dies and is restarted, the client
  should still work (experimental).
  
- each time the server detect a channel write it triggers the forwarding of **all** channel-values (via serial) 
  to the arduino
  
- somehow improved to speed.

Good to Know
------------
- the number of channels to use, is defined in `driver/number_of_channels.h`. 
  This file is somehow *parsed* by `common.py` to ensure same number of channels in the message. -> See also Bugs
  
- If a lot of `sync erros` occur, maybe the driver and the firmware does not use the same number of 
  channels (that's why the nr of channels, now is read from the C-header-file)
  
- strange numbers as messages from the firmware, often happens if a string in C is surrounded by 
  single quotation (`'`), instead of double ones (`"`).
  
Known Bugs
----------
Currently, the firmware only work for `8` channels, even if the board is build with
only 6 physical channels.
