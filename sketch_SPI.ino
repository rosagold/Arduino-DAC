#include <SPI.h> 

int p9 = 9;
int p10 = 10;
int p11 = 11;

int baud = 20000000;

void setup() {
  //pinMode(p9, OUTPUT);
  //analogWrite(p9, 64);
  Serial.begin(9600);

  // Initializes the SPI bus by setting SCK, MOSI, 
  // and SS to outputs, pulling SCK and MOSI low, and SS high. 
  SPI.begin();
  SPI.beginTransaction(SPISettings(baud, MSBFIRST, SPI_MODE3));
  
}

void writeSPI(unsigned int val){

  val = val | 0x3000;

  // enable Chip/Slave Select
  digitalWrite(SS, LOW);    // SS is pin 10

  SPI.transfer16(val);

  // disable Chip/Slave Select
  digitalWrite(SS, HIGH);
}

void loop() {
  
  if(Serial.available()){
    String data = Serial.readStringUntil("\n");

    unsigned int i = data.toInt();

    writeSPI(i);
    Serial.print("set: ");
    Serial.println(i);

  }
}
