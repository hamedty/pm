#include <Arduino.h>

#define RESERVE_BYTES 0

#define SUCCESS 0
#define ERR_INVALID_PACKET_SIZE 1
#define ERR_HOMING_FAILED 2
#define ERR_RAIL_SOFT_LIMIT 3


// Motors

#define MOTOR_COUNT 2
#define MOTOR_PIN_COUNT 2     // number of pins for each motor

#define MOTOR_DIR    0
#define MOTOR_PULS   1


const uint8_t MOTOR_PINS[MOTOR_COUNT][MOTOR_PIN_COUNT] = {
        { 11, 12},
        { 8, 9},
};


// Pneumatic

#define PNEUMATIC_COUNT 6 // number of pins for pneumatic system

const uint8_t PNEUMATIC_PINS[PNEUMATIC_COUNT] = {
        37,
        39,
        37,
        39,
        37,
        39,
};

// Encoder

#define ENC1_A 2
#define ENC1_B 13



// Digital Input
#define DI_COUNT 4
#define DI_1 0
#define DI_2 14
#define DI_3 15
#define DI_4 16

const uint8_t DI_PINS[DI_COUNT] = {DI_1, DI_2, DI_3, DI_4};

#define M0_LIMIT_N DI_3
#define M0_LIMIT_P DI_4
#define M1_LIMIT_N DI_2
#define M1_LIMIT_P DI_1
