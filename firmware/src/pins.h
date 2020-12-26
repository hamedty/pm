#define MOTOR_COUNT 4
#define MOTOR_PIN_COUNT 2     // number of pins for each motor
#define PNEUMATIC_PIN_COUNT 6 // number of pins for pneumatic system


#define MOTOR_DIR    0
#define MOTOR_PULS   1

#define RESERVE_BYTES 0

const uint8_t MOTOR_PINS[MOTOR_COUNT][MOTOR_PIN_COUNT] = {
        { 13, 12 },
        { 10, 11 },
        { 7, 6 },
        { 8, 9 },
};

const uint8_t PNEUMATIC_PINS[PNEUMATIC_PIN_COUNT] = {
        31, // lp1
        33, // lp2
        35, // lp3
        37, // lp4
        39, // lp5
        41, // hp1

};

const uint8_t HOME_PIN = 4;

#define SUCCESS 0
#define ERR_INVALID_PACKET_SIZE 1
#define ERR_HOMING_FAILED 2
