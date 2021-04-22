#include <Arduino.h>
#include "motor.h"
#include "gpio.h"

#ifndef Communication_h
# define Communication_h


# define RESPONSE_CODE_BAD_DATA 5
# define RESPONSE_CODE_BAD_PAYLOAD 6
# define RESPONSE_CODE_BAD_PAYLOAD_SIZE 7

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
  int a;
} DefineMotor;

#endif /* ifndef Communication_h */
