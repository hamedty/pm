#include <Arduino.h>
#include <SPI.h>
#include "PacketSerial.h"
#include "pins.h"
#include "motor.h"


// Command
// no_commands (<10)| type | id | data

// Response (TBA)
// id | status_code | data
#include "DueTimer.h"


PacketSerial packet_serial;
void process_command(const uint8_t *, size_t);

void setup() {
  SerialUSB.begin(115200);

  packet_serial.setStream(&SerialUSB);
  packet_serial.setPacketHandler(&process_command);

  Motor0.set_isr(m0_isr);
  Motor0.set_pins(10, 20);
}

void loop() {
  packet_serial.update();
}

void process_command(const uint8_t *buffer_in, size_t size) {
  uint16_t rptr = size;

  switch (buffer_in[rptr++]) {
  case 1: // Pneumatic
  {
    uint16_t data = buffer_in[rptr++];
    data = data << 8;
    data = data | buffer_in[rptr++];

    for (uint8_t valve = 0; valve < PNEUMATIC_COUNT; valve++) {
      digitalWrite(PNEUMATIC_PINS[valve], data && (1 << valve));
    }
    break;
  }

  case 2: // Motor - normal movement
  {
    int32_t steps = buffer_in[rptr++];
    steps = (steps << 8) | buffer_in[rptr++];
    steps = (steps << 8) | buffer_in[rptr++];
    steps = (steps << 8) | buffer_in[rptr++];

    bool dir       = buffer_in[rptr++];
    uint16_t delay = buffer_in[rptr++];
    delay = (delay << 8) | buffer_in[rptr++];
    Motor0.go_steps(steps, delay);
    break;
  }


  default:
    return;
  }
}
