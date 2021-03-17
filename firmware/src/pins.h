#define RESERVE_BYTES 0

#define SUCCESS 0
#define ERR_INVALID_PACKET_SIZE 1
#define ERR_HOMING_FAILED 2
#define ERR_RAIL_SOFT_LIMIT 3


// Motors

#define MOTOR_COUNT 4
#define MOTOR_PIN_COUNT 5     // number of pins for each motor

#define MOTOR_DIR    0
#define MOTOR_PULS   1
#define MOTOR_M0     2
#define MOTOR_M1     3
#define MOTOR_M2     4


const uint8_t MOTOR_PINS[MOTOR_COUNT][MOTOR_PIN_COUNT] = {
        { 42, 43, 46, 45, 44 },
        { 23,25, 31, 29, 27 },
        { 47, 48, 51, 50, 49 },
        { 33, 35, 39, 38, 37 },
};
const bool MOTOR_PRESET[MOTOR_COUNT][MOTOR_PIN_COUNT] = {
        // M0 M1 M2
        { 0, 0, 1, 1, 1 }, // Motor 1
        { 0, 0, 1, 1, 1 }, // Motor 2
        { 0, 0, 1, 1, 1 }, // Motor 3
        { 0, 0, 0, 0, 0 },
};



// Pneumatic

#define PNEUMATIC_COUNT 6 // number of pins for pneumatic system

const uint8_t PNEUMATIC_PINS[PNEUMATIC_COUNT] = {
        8,
        7,
        6,
        5,
        4,
        3,

};

// Encoder

#define ENC_A 2
#define ENC_B 13


// Loadcells
const int LC1_DOUT_PIN = 41;
const int LC1_SCK_PIN = 40;

const int LC2_DOUT_PIN = 53;
const int LC2_SCK_PIN = 52;


// Digital Output
#define DO_COUNT 4
#define DO_1 30
#define DO_2 32
#define DO_3 34
#define DO_4 36

const uint8_t DO_PINS[DO_COUNT] = {DO_1, DO_2, DO_3, DO_4};
const bool DO_PRESET[DO_COUNT] = {0, 0, 0, 0};

// Digital Input
#define DI_COUNT 4
#define DI_1 22
#define DI_2 24
#define DI_3 26
#define DI_4 28

const uint8_t DI_PINS[DI_COUNT] = {DI_1, DI_2, DI_3, DI_4};

#define HOME_PIN DI_1
