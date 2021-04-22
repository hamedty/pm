#include <Arduino.h>
#include "PacketSerial.h"
#include "DueTimer.h"
#include "pins.h"
#include "curve_rail_long.h"
// #include "curve_rail_short.h"

#include "HX711.h"

// Timers
DueTimer MOTOR_TIMERS[MOTOR_COUNT] = {Timer4, Timer5};


typedef struct Command {
        // motors
        int32_t steps[MOTOR_COUNT];
        int32_t delay[MOTOR_COUNT];
        bool blocking[MOTOR_COUNT];

        // pneumatic
        bool pneumatic[PNEUMATIC_COUNT];

        // homing
        bool home;

        // reserve
        bool reserve[RESERVE_BYTES];
} Command;

typedef struct Response {
        uint32_t status_code;
        uint32_t encoder;
        uint32_t reserve[3];
} Response;

typedef struct Motor {
        int32_t steps;
        bool value;
        bool dir;
} Motor;

void setup_pins();
bool home();
void motor_loop_0();
void motor_loop_1();

void (*motor_loop_array[MOTOR_COUNT])(void) = {
        motor_loop_0, motor_loop_1
};

void rail_fast_run(uint16_t, bool);

Motor motors[MOTOR_COUNT];

Command command;
volatile bool motors_running[MOTOR_COUNT];

PacketSerial packet_serial;
void process_command_wrapper(const uint8_t *, size_t);
uint8_t process_command(const uint8_t *, size_t);


void setup() {
        SerialUSB.begin(115200);

        packet_serial.setStream(&SerialUSB);
        packet_serial.setPacketHandler(&process_command_wrapper);

        setup_pins();
}

void loop() {
        packet_serial.update();
}

void process_command_wrapper(const uint8_t *data, size_t size) {
        Response response;

        response.status_code = process_command(data, size);
        response.encoder  = REG_TC0_CV0;
        response.reserve[0]  = sizeof(Command);
        response.reserve[1] = digitalRead(DI_1) | (digitalRead(DI_2) << 1) | (digitalRead(DI_3) << 2) | (digitalRead(DI_4) << 3);
        response.reserve[2] = REG_TC2_CV0;

        packet_serial.send((uint8_t *)&response, sizeof(Response));
}

uint8_t process_command(const uint8_t *data, size_t size) {
        if (sizeof(Command) != size) {
                return ERR_INVALID_PACKET_SIZE;
        }
        memcpy(&command, data, size);


        // Pneumatic
        for (uint8_t valve = 0; valve < PNEUMATIC_COUNT; valve++) {
                digitalWrite(PNEUMATIC_PINS[valve], command.pneumatic[valve]);
        }

        // Motors
        for (uint8_t motor_number = 0; motor_number < MOTOR_COUNT; motor_number++) {
                Motor  *motor     = &motors[motor_number];
                int32_t steps_raw = command.steps[motor_number];
                int32_t delay_ = command.delay[motor_number];
                bool dir = steps_raw > 0;
                uint32_t steps = abs(steps_raw) << 1;

                motors_running[motor_number] = true;

                if (steps) {
                        motor->steps = steps;
                        motor->dir = dir;
                        digitalWrite(MOTOR_PINS[motor_number][MOTOR_DIR], dir);
                        motor->value = false;
                        if (motor_number==0)
                                Timer4.attachInterrupt(motor_loop_0).start(delay_);
                        if (motor_number==1)

                                Timer5.attachInterrupt(motor_loop_1).start(delay_);
                } else {
                        motors_running[motor_number] = false;
                }
        }

        bool anything_running = true;
        while (anything_running) {
                anything_running = false;
                for (uint8_t motor_number = 0; motor_number < MOTOR_COUNT; motor_number++) {
                        anything_running = anything_running || motors_running[motor_number];
                }
        }

        return SUCCESS;
}

void motor_loop_0() {
        uint8_t motor_index = 0;
        Motor* motor_p = &motors[motor_index];
        if (motor_p->steps && (
                    (motor_p->dir  && !digitalRead(M0_LIMIT_P))// pos movement
                    ||
                    (!motor_p->dir && !digitalRead(M0_LIMIT_N)) // neg movemebt
                    )) {
                motor_p->value = !motor_p->value;
                digitalWrite(MOTOR_PINS[motor_index][MOTOR_PULS], motor_p->value);
                motor_p->steps--;
        }
        else {
                motor_p->steps = 0;
                MOTOR_TIMERS[motor_index].stop();
                motors_running[motor_index] = false;
        }
}

void motor_loop_1() {
        uint8_t motor_index = 1;
        Motor* motor_p = &motors[motor_index];
        if (motor_p->steps && (
                    (motor_p->dir )// && !digitalRead(M1_LIMIT_P))// pos movement
                    ||
                    (!motor_p->dir && !digitalRead(M1_LIMIT_N)) // neg movemebt
                    )) {
                motor_p->value = !motor_p->value;
                digitalWrite(MOTOR_PINS[motor_index][MOTOR_PULS], motor_p->value);
                motor_p->steps--;
        }
        else {
                motor_p->steps = 0;
                MOTOR_TIMERS[motor_index].stop();
                motors_running[motor_index] = false;
        }
}



void setup_pins() {
        // Motors
        for (uint8_t motor = 0; motor < MOTOR_COUNT; motor++) {
                for (uint8_t pin = 0; pin < MOTOR_PIN_COUNT; pin++) {
                        pinMode(MOTOR_PINS[motor][pin], OUTPUT);
                }
        }

        // Valves
        for (uint8_t valve = 0; valve < PNEUMATIC_COUNT; valve++) {
                pinMode(PNEUMATIC_PINS[valve], OUTPUT);
                digitalWrite(PNEUMATIC_PINS[valve], 0);
        }

        // // Encoder1
        pinMode(ENC1_A, INPUT_PULLUP);
        pinMode(ENC1_B, INPUT_PULLUP);
        // For more information see http://forum.arduino.cc/index.php?topic=140205.30
        REG_PMC_PCER0 = PMC_PCER0_PID27;     // activate clock for TC0
        REG_TC0_CMR0 = TC_CMR_TCCLKS_XC0;    // select XC0 as clock source

        // activate quadrature encoder and position measure mode, no filters
        REG_TC0_BMR = TC_BMR_QDEN
                      | TC_BMR_POSEN
                      | TC_BMR_EDGPHA;

        // enable the clock (CLKEN=1) and reset the counter (SWTRG=1)
        REG_TC0_CCR0 = TC_CCR_CLKEN | TC_CCR_SWTRG;

        // // Encoder2
        pinMode(4, INPUT_PULLUP);
        pinMode(5, INPUT_PULLUP);
        REG_PMC_PCER1 = PMC_PCER1_PID33;
        REG_TC2_CMR0 = TC_CMR_TCCLKS_XC0;
        REG_TC2_BMR = TC_BMR_QDEN
                      | TC_BMR_POSEN
                      | TC_BMR_EDGPHA;
        REG_TC2_CCR0 = TC_CCR_CLKEN | TC_CCR_SWTRG;















        // Digital Input
        for (uint8_t pin_index = 0; pin_index < DI_COUNT; pin_index++) {
                pinMode(DI_PINS[pin_index], INPUT_PULLUP);
        }


}
