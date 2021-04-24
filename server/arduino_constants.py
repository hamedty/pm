INVALID_PIN = 128
MOTORS_NO = 4
VALVES_NO = 10
INPUTS_NO = 2

# formats
bool = '?'
int8_t = 'b'
uint8_t = 'B'
int16_t = 'h'
uint16_t = 'H'
int32_t = 'i'
uint32_t = 'I'
pad = 'x'


CommandHeader = [
    (uint16_t, 'command_type'),
    (uint16_t, 'payload_size'),
    (uint32_t, 'command_id'),
]

ResponseHeader = [
    (uint16_t, 'response_type'),
    (uint16_t, 'payload_size'),
    (uint32_t, 'command_id'),
]


COMMAND_TYPE_DEFINE_VALVE = 1
DefineValve = [
    (uint8_t * VALVES_NO, 'pins'),
]

COMMAND_TYPE_SET_VALVE = 2
SetValve = [
    (bool * VALVES_NO, 'mask'),
    (bool * VALVES_NO, 'value'),
]


COMMAND_TYPE_DEFINE_MOTOR = 3
DefineMotor = [
    (uint8_t, 'motor_no'),
    (uint8_t, 'pin_pulse'),
    (uint8_t, 'pin_dir'),
    (uint8_t, 'pin_limit_p'),
    (uint8_t, 'pin_limit_n'),
    (uint8_t, 'pin_microstep_0'),
    (uint8_t, 'pin_microstep_1'),
    (uint8_t, 'pin_microstep_2'),
    (uint32_t, 'microstep'),
    (uint32_t, 'encoder_ratio'),
    (bool, 'has_encoder'),
    (uint8_t, 'encoder_no'),
    (pad, None),
    (pad, None),
]


COMMAND_TYPE_MOVE_MOTOR = 4
MoveMotor = [
    (int32_t * MOTORS_NO, 'steps'),
    (int32_t * MOTORS_NO, 'delay'),
    (bool * MOTORS_NO,    'block'),
]


COMMAND_TYPE_QUERY_MOTOR = 5
COMMAND_TYPE_QUERY_ENCODER = 6
COMMAND_TYPE_DEFINE_DI = 7


COMMAND_TYPE_QUERY_DI = 8
DefineDI = [
    (uint8_t * INPUTS_NO, 'pins'),
]

COMMAND_TYPE_DEFINE_TRAJECTORY = 9
