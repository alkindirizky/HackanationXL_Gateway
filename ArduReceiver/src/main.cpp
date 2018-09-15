// Feather9x_RX
// -*- mode: C++ -*-
// Example sketch showing how to create a simple messaging client (receiver)
// with the RH_RF95 class. RH_RF95 class does not provide for addressing or
// reliability, so you should only use RH_RF95 if you do not need the higher
// level messaging abilities.
// It is designed to work with the other example Feather9x_TX

#include <SPI.h>
#include <RH_RF95.h>

// for Feather32u4 RFM9x
#define RFM95_CS 8
#define RFM95_RST 4
#define RFM95_INT 7
#define RF95_FREQ 433.0

// Packet setting
#define IND_START_BYTE (0)
#define IND_SENSOR_COUNT (1)
#define IND_DATA (2)
#define PAYLOAD_HEADER_SIZE (2)
#define PAYLOAD_DATA_SIZE (3)

// Blinky on receipt
#define LED 13

// Singleton instance of the radio driver
RH_RF95 rf95(RFM95_CS, RFM95_INT);

void setup()
{
  pinMode(LED, OUTPUT);
  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH);

  Serial.begin(115200);
  while (!Serial) {
    delay(1);
  }
  delay(100);

  // manual reset
  digitalWrite(RFM95_RST, LOW);
  delay(10);
  digitalWrite(RFM95_RST, HIGH);
  delay(10);

  while (!rf95.init()) {
    Serial.println("STAT : Radio Init Failed");
    while (1);
  }
  Serial.println("STAT : Radio Init Successful");

  // Defaults after init are 434.0MHz, modulation GFSK_Rb250Fd250, +13dbM
  if (!rf95.setFrequency(RF95_FREQ)) {
    Serial.println("STAT : Set Frequency is Failed");
    while (1);
  }

  // Defaults after init are 434.0MHz, 13dBm, Bw = 125 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on

  // The default transmitter power is 13dBm, using PA_BOOST.
  // If you are using RFM95/96/97/98 modules which uses the PA_BOOST transmitter pin, then
  // you can set transmitter powers from 5 to 23 dBm:
  rf95.setTxPower(23, false);
}

uint8_t calc_sum(const uint8_t* buff, uint8_t buff_len)
{
    uint8_t checksum = buff[0];

    for(uint8_t i = 1; i < buff_len; i++)
    {
        checksum ^= buff[i];
    }

    return checksum;
}

bool check_sum(const uint8_t* data, uint8_t data_len, uint8_t checksum_ref)
{
    uint8_t checksum = data[0];

    for(uint8_t id = 1; id < data_len; id++)
    {
        checksum ^= data[id];
    }

    return checksum == checksum_ref ? true : false;
}

bool process_data(const uint8_t* buff, uint8_t buff_len, int8_t rssi)
{
    if(buff[IND_START_BYTE] != 0xFA)
    {
        Serial.println("STAT : Invalid Start Byte");
        return false;
    }

    uint8_t ind_checksum = (buff[IND_SENSOR_COUNT] * PAYLOAD_DATA_SIZE) + PAYLOAD_HEADER_SIZE;

    if(!check_sum(buff, buff_len - 1, buff[ind_checksum]))
    {
       Serial.println("STAT : Checksum Invalid");
       return false; 
    }

    for(uint8_t startind = IND_DATA; startind < ind_checksum; startind += PAYLOAD_DATA_SIZE)
    {
        Serial.write(rssi);
        for(uint8_t dataind = 0; dataind < PAYLOAD_DATA_SIZE; dataind++)
        {
            Serial.write(buff[startind + dataind]);
        }
        Serial.write(0x0A);
    }

    return true;
}

void loop()
{
  if (rf95.available())
  {
    // Should be a message for us now
    uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
    uint8_t len = sizeof(buf);

    if (rf95.recv(buf, &len))
    {
        digitalWrite(LED, HIGH);
        process_data(buf, len, rf95.lastRssi());
        digitalWrite(LED, LOW);
    }
    else
    {
        Serial.println("STAT : Receive Error");
    }
  }
}
