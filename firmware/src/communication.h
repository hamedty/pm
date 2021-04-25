#include <Arduino.h>
#include "motor.h"
#include "gpio.h"

#ifndef Communication_h
# define Communication_h

enum RESPONSE_CODE {
  RESPONSE_CODE_SUCCESS,          // 0
  RESPONSE_CODE_BAD_DATA,         // 1
  RESPONSE_CODE_BAD_PAYLOAD,      // 2
  RESPONSE_CODE_BAD_PAYLOAD_SIZE, // 3
  RESPONSE_CODE_BAD_MOTOR_NO,     // 4
  RESPONSE_CODE_BAD_ENCODER_NO,   // 5
  RESPONSE_CODE_INVALID_COMMAND,  // 6
};


// Command
// [(type | size | id  | data), ...]

typedef struct CommandHeader {
  uint16_t command_type;
  uint16_t payload_size;
  uint32_t command_id;
} CommandHeader;

typedef struct ResponseHeader {
  uint16_t response_type;
  uint16_t payload_size;
  uint32_t command_id;
} ResponseHeader;

# define COMMAND_TYPE_DEFINE_VALVE 1
typedef struct DefineValve {
  uint8_t pins[VALVES_NO];
} DefineValve;


# define COMMAND_TYPE_SET_VALVE 2
typedef struct SetValve {
  bool mask[VALVES_NO];
  bool value[VALVES_NO];
} SetValve;


# define COMMAND_TYPE_DEFINE_MOTOR 3
typedef struct DefineMotor {
  uint8_t  motor_no;
  uint8_t  pin_pulse;
  uint8_t  pin_dir;
  uint8_t  pin_limit_p;
  uint8_t  pin_limit_n;
  uint8_t  pin_microstep_0;
  uint8_t  pin_microstep_1;
  uint8_t  pin_microstep_2;
  uint32_t microstep;
  uint32_t encoder_ratio;
  uint32_t course;
  uint32_t homing_delay;
  uint32_t home_retract;
  bool     has_encoder;
  uint8_t  encoder_no;
} DefineMotor;

# define COMMAND_TYPE_MOVE_MOTOR 4
typedef struct MoveMotor {
  int32_t steps[MOTORS_NO];
  int32_t delay[MOTORS_NO];
  bool    block[MOTORS_NO];
} MoveMotor;

# define COMMAND_TYPE_HOME_MOTOR 41
typedef struct HomeMotor {
  uint8_t motor_index;
} HomeMotor;


# define COMMAND_TYPE_QUERY_MOTOR 5
# define COMMAND_TYPE_QUERY_ENCODER 6

# define COMMAND_TYPE_DEFINE_DI 7
typedef struct DefineDI {
  uint8_t pins[INPUTS_NO];
} DefineDI;

# define COMMAND_TYPE_QUERY_DI 8


# define COMMAND_TYPE_DEFINE_TRAJECTORY 9

#endif /* ifndef Communication_h */
