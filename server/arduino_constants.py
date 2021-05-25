INVALID_PIN = 128
MOTORS_NO = 4
ENCODER_NO = 2
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
    (uint16_t, 'response_code'),
    (uint16_t, 'payload_size'),
    (uint32_t, 'command_id'),
    (int32_t * ENCODER_NO, 'encoders'),
    (uint8_t * INPUTS_NO, 'di_status'),
    (uint8_t * 2, None),
    (uint8_t * MOTORS_NO, 'motor_status'),
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
    (uint32_t, 'course'),
    (uint32_t, 'homing_delay'),
    (uint32_t, 'home_retract'),
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
    (bool * MOTORS_NO,    'absolute'),
]

COMMAND_TYPE_HOME_MOTOR = 41
HomeMotor = [
    (uint8_t,  'motor_index'),
]

COMMAND_TYPE_QUERY_MOTOR = 5
COMMAND_TYPE_QUERY_ENCODER = 6
COMMAND_TYPE_DEFINE_DI = 7
DefineDI = [
    (uint8_t * INPUTS_NO, 'pins'),
]


COMMAND_TYPE_QUERY_DI = 8

COMMAND_TYPE_DEFINE_TRAJECTORY = 9


MOTOR_STATUS_NOT_DEFINED = 0
MOTOR_STATUS_IDLE = 1
MOTOR_STATUS_RUNNING = 2
MOTOR_STATUS_LIMIT_REACHED_P = 3
MOTOR_STATUS_LIMIT_REACHED_N = 4
MOTOR_STATUS_HOMED = 5
MOTOR_STATUS_HOMEING_FAILED = 6
