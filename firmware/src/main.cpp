#include <Arduino.h>
#include <SPI.h>
#include "PacketSerial.h"
#include "motor.h"
#include "gpio.h"
#include "communication.h"


#include "DueTimer.h"


PacketSerial packet_serial;
void process_commands(const uint8_t *, size_t);

void setup() {
  SerialUSB.begin(115200);

  packet_serial.setStream(&SerialUSB);
  packet_serial.setPacketHandler(&process_commands);

  Motor0.set_isr(m0_isr);
  Motor1.set_isr(m1_isr);
  Motor2.set_isr(m2_isr);
  Motor3.set_isr(m3_isr);
}

void loop() {
  packet_serial.update();
}

void process_command(const CommandHeader *);
void send_response(uint16_t, uint32_t);

void process_commands(const uint8_t *buffer_in, size_t size) {
  const uint8_t *rptr = buffer_in;
  uint32_t bytes_left = size;

  while (bytes_left) {
    if (bytes_left < sizeof(CommandHeader)) {
      send_response(RESPONSE_CODE_BAD_DATA, 0);
      return;
    }

    CommandHeader *command_header = (CommandHeader *)buffer_in;

    if (bytes_left < sizeof(CommandHeader) + command_header->payload_size) {
      send_response(RESPONSE_CODE_BAD_PAYLOAD, command_header->command_id);
      return;
    }

    process_command(command_header);
    rptr       = rptr + sizeof(CommandHeader) + command_header->payload_size;
    bytes_left = buffer_in + size - rptr;
  }
}

void process_command(const CommandHeader *command_header) {
  uint8_t *payload_buffer = (uint8_t *)command_header;

  payload_buffer = payload_buffer + sizeof(CommandHeader);

  switch (command_header->command_type) {
  case COMMAND_TYPE_DEFINE_VALVE: // valve_pin_setup
  {
    if (command_header->payload_size != sizeof(DefineValve)) {
      send_response(RESPONSE_CODE_BAD_PAYLOAD_SIZE, command_header->command_id);
      return;
    }

    DefineValve *payload = (DefineValve *)payload_buffer;

    for (uint8_t valve_index = 0; valve_index < VALVES_NO; valve_index++) {
      valves[valve_index].set_pin(payload->pins[valve_index]);
    }

    break;
  }

  case COMMAND_TYPE_SET_VALVE: // valve_set_value
  {
    if (command_header->payload_size != sizeof(SetValve)) {
      send_response(RESPONSE_CODE_BAD_PAYLOAD_SIZE, command_header->command_id);
      return;
    }

    SetValve *payload = (SetValve *)payload_buffer;

    for (uint8_t valve_index = 0; valve_index < VALVES_NO; valve_index++) {
      if (payload->mask[valve_index]) valves[valve_index].set(payload->value[
                                                                valve_index]);
    }

    break;
  }

  case COMMAND_TYPE_DEFINE_MOTOR: // define_motor
  {
    if (command_header->payload_size != sizeof(DefineMotor)) {
      send_response(RESPONSE_CODE_BAD_PAYLOAD_SIZE, command_header->command_id);
      return;
    }

    DefineMotor *payload = (DefineMotor *)payload_buffer;
    break;
  }

  default:
    break;
  }
}

void send_response(uint16_t response_type,
                   uint32_t command_id) {
  // TODO: add payload
  ResponseHeader response_header;

  response_header.response_type = response_type;
  response_header.payload_size  = 0;
  response_header.command_id    = command_id;
  packet_serial.send((uint8_t *)&response_header, sizeof(response_header));
}

// motors[0]->set_pins(12, 11, 16, 15, INVALID_PIN, INVALID_PIN, INVALID_PIN);
// motors[0]->set_timer(); // this call allocates a timer - don't confilit
// with
//                         // encoder
// encoders[0].init();
// motors[0]->set_encoder(&encoders[0]);
//
// motors[1]->set_pins(9, 8, INVALID_PIN, 14, INVALID_PIN, INVALID_PIN,
// INVALID_PIN);
// motors[1]->set_timer(); // this call allocates a timer - don't confilit
// with
//                         // encoder
// encoders[1].init();
// motors[1]->set_encoder(&encoders[1]);


// motors[0]->go_steps(500, 500);
// motors[1]->go_steps(500, 500);
//
// delay(100);
// motors[0]->go_steps(-500, 500);
// motors[1]->go_steps(-500, 500);
//
// delay(100);
