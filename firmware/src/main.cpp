#include <Arduino.h>
#include <SPI.h>
#include "PacketSerial.h"
#include "motor.h"
#include "gpio.h"
#include "communication.h"


#include "DueTimer.h"


PacketSerial packet_serial;
void process_commands(const uint8_t *, size_t);
uint32_t last_response;
void process_command(const CommandHeader *);
void send_response(RESPONSE_CODE, uint32_t);

void setup() {
  SerialUSB.begin(115200);

  packet_serial.setStream(&SerialUSB);
  packet_serial.setPacketHandler(&process_commands);

  Motor0.set_isr(m0_isr);
  Motor1.set_isr(m1_isr);
  Motor2.set_isr(m2_isr);
  Motor3.set_isr(m3_isr);

  last_response = millis();
}

void loop() {
  packet_serial.update();

  // if ((millis() - last_response) > 100) {
  send_response(RESPONSE_CODE_SUCCESS, 0);
  delay(100);

  // }
}

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

    if (payload->motor_no >= 4) {
      send_response(RESPONSE_CODE_BAD_MOTOR_NO, command_header->command_id);
      return;
    }
    Motor *m = motors[payload->motor_no];
    m->set_pins(payload->pin_pulse,
                payload->pin_dir,
                payload->pin_limit_p,
                payload->pin_limit_n,
                payload->pin_microstep_0,
                payload->pin_microstep_1,
                payload->pin_microstep_2
                );
    m->set_microstep(payload->microstep);

    m->set_timer(); // this call allocates a timer - don't confilit with


    if (payload->has_encoder && (payload->encoder_no > 1)) {
      send_response(RESPONSE_CODE_BAD_ENCODER_NO, command_header->command_id);
      return;
    }

    if (payload->has_encoder) {
      encoders[payload->encoder_no].init();
      m->set_encoder(&encoders[payload->encoder_no], payload->encoder_ratio);
    } else {
      m->set_encoder(NULL, 1);
    }
    m->set_homing_params(payload->course,
                         payload->homing_delay,
                         payload->home_retract);
    break;
  }

  case COMMAND_TYPE_MOVE_MOTOR: // move_motor
  {
    if (command_header->payload_size != sizeof(MoveMotor)) {
      send_response(RESPONSE_CODE_BAD_PAYLOAD_SIZE, command_header->command_id);
      return;
    }
    MoveMotor *payload = (MoveMotor *)payload_buffer;

    for (uint8_t motor_index = 0; motor_index < MOTORS_NO; motor_index++) {
      if (payload->steps[motor_index]) {
        motors[motor_index]->go_steps(payload->steps[motor_index],
                                      payload->delay[motor_index],
                                      payload->block[motor_index]);
      }
    }

    break;
  }

  case COMMAND_TYPE_HOME_MOTOR: // home_motor
  {
    if (command_header->payload_size != sizeof(HomeMotor)) {
      send_response(RESPONSE_CODE_BAD_PAYLOAD_SIZE, command_header->command_id);
      return;
    }
    HomeMotor *payload = (HomeMotor *)payload_buffer;

    if (payload->motor_index >= 4) {
      send_response(RESPONSE_CODE_BAD_MOTOR_NO, command_header->command_id);
      return;
    }
    motors[payload->motor_index]->home();
    break;
  }

  case COMMAND_TYPE_QUERY_MOTOR: // query_motor
  {
    break;
  }

  case COMMAND_TYPE_QUERY_ENCODER: // query_encoder
  {
    break;
  }

  case COMMAND_TYPE_DEFINE_DI: // define_digital_input
  {
    if (command_header->payload_size != sizeof(DefineDI)) {
      send_response(RESPONSE_CODE_BAD_PAYLOAD_SIZE, command_header->command_id);
      return;
    }

    DefineDI *payload = (DefineDI *)payload_buffer;

    for (uint8_t di_index = 0; di_index < INPUTS_NO; di_index++) {
      inputs[di_index].set_pin(payload->pins[di_index]);
    }

    break;
  }

  case COMMAND_TYPE_QUERY_DI: // query_digital_input
  {
    break;
  }

  case COMMAND_TYPE_DEFINE_TRAJECTORY: // define_trajectory
  {
    break;
  }

  default:
    send_response(RESPONSE_CODE_INVALID_COMMAND, command_header->command_id);
    return;
  }
  send_response(RESPONSE_CODE_SUCCESS, command_header->command_id);
}

void send_response(RESPONSE_CODE response_code,
                   uint32_t      command_id) {
  // TODO: add payload
  ResponseHeader response_header;

  // header
  response_header.response_code = (uint16_t)response_code;
  response_header.payload_size  = 0;
  response_header.command_id    = command_id;

  // status
  response_header.encoders[0] =
    encoders[0].initialized ? encoders[0].read() : 0;
  response_header.encoders[1] =
    encoders[1].initialized ? encoders[1].read() : 0;
  response_header.di_status[0]    = inputs[0].read();
  response_header.di_status[1]    = inputs[1].read();
  response_header.motor_status[0] = Motor0._status;
  response_header.motor_status[1] = Motor1._status;
  response_header.motor_status[2] = Motor2._status;
  response_header.motor_status[3] = Motor3._status;
  packet_serial.send((uint8_t *)&response_header, sizeof(response_header));
  last_response = millis();
}
