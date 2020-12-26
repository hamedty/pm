#include <Arduino.h>
#include <SPI.h>
#include "PacketSerial.h"
#include "DueTimer.h"
#include "pins.h"
// #include "curve_rail_long.h"
// #include "curve_rail_short.h"


// Timers
DueTimer MOTOR_TIMERS[MOTOR_COUNT] = {Timer1, Timer2, Timer3, Timer4};


typedef struct Command {
        // motors
        int32_t steps[MOTOR_COUNT];
        int32_t delay[MOTOR_COUNT];
        bool blocking[MOTOR_COUNT];

        // pneumatic
        bool pneumatic[PNEUMATIC_PIN_COUNT];

        // homing
        bool home;

        // reserve
        bool reserve[RESERVE_BYTES];
} Command;

typedef struct Response {
        uint16_t status_code;
        uint16_t reserve[3];
} Response;

typedef struct Motor {
        int32_t steps;
        bool value;
} Motor;

void setup_pins();
bool home();
void motor_loop_0();
void motor_loop_1();
void motor_loop_2();
void motor_loop_3();

void (*motor_loop_array[MOTOR_COUNT])(void) = {
        motor_loop_0, motor_loop_1, motor_loop_2, motor_loop_3
};
// void rail_fast_run(uint16_t);
// void rail_fast_run(uint16_t, unsigned long *, unsigned long *, uint16_t, uint16_t);

Motor motors[MOTOR_COUNT];

Command command;
volatile bool motors_running[MOTOR_COUNT];

PacketSerial packet_serial;
void process_command_wrapper(const uint8_t *, size_t);
uint8_t process_command(const uint8_t *, size_t);

void setup() {
        SerialUSB.begin(115200);
        packet_serial.setStream(&SerialUSB);

        setup_pins();
        packet_serial.setPacketHandler(&process_command_wrapper);
}

void loop() {
        // digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
        for (uint32_t i = 0; i < 50000; i++) packet_serial.update();
        // digitalWrite(PNEUMATIC_PINS[1], digitalRead(HOME_PIN));

}

void process_command_wrapper(const uint8_t *data, size_t size) {
        Response response;

        response.status_code = process_command(data, size);
        response.reserve[0]  = sizeof(Command);
        response.reserve[1]  = command.pneumatic[0];

        packet_serial.send((uint8_t *)&response, sizeof(Response));
}

uint8_t process_command(const uint8_t *data, size_t size) {
        if (sizeof(Command) != size) {
                return ERR_INVALID_PACKET_SIZE;
        }
        memcpy(&command, data, size);

        // uint32_t total_steps = 0;

        // Pneumatic
        for (uint8_t valve = 0; valve < PNEUMATIC_PIN_COUNT; valve++) {
                digitalWrite(PNEUMATIC_PINS[valve], !command.pneumatic[valve]);
        }

        if (command.home) {
                if(home())
                        return SUCCESS;
                return ERR_HOMING_FAILED;
        }

        // Motors
        for (uint8_t motor_number = 0; motor_number < MOTOR_COUNT; motor_number++) {
                Motor  *motor     = &motors[motor_number];
                int32_t steps_raw = command.steps[motor_number];
                int32_t delay_ = command.delay[motor_number];
                uint32_t steps = abs(steps_raw) << 1;

                if (steps) {
                        motor->steps = steps;
                        digitalWrite(MOTOR_PINS[motor_number][MOTOR_DIR], steps_raw > 0);
                        motor->value = false;
                        if (motor_number==0)
                                Timer1.attachInterrupt(motor_loop_0).start(delay_);
                        if (motor_number==1)
                                Timer2.attachInterrupt(motor_loop_1).start(delay_);
                        if (motor_number==2)
                                Timer3.attachInterrupt(motor_loop_2).start(delay_);
                        if (motor_number==3)
                                Timer4.attachInterrupt(motor_loop_3).start(delay_);
                        motors_running[motor_number] = true;
                        delayMicroseconds(10);
                        // if (motor_rail.steps > (CURVE_RAIL_LONG_A_LEN + CURVE_RAIL_LONG_D_LEN + 20)) {
                        //         rail_fast_run(motor_rail.steps, CURVE_RAIL_LONG_A, CURVE_RAIL_LONG_D, CURVE_RAIL_LONG_A_LEN, CURVE_RAIL_LONG_D_LEN);
                        //         motor_rail.steps = 0;
                        // } else if (motor_rail.steps > (CURVE_RAIL_SHORT_A_LEN + CURVE_RAIL_SHORT_D_LEN + 20)) {
                        //         rail_fast_run(motor_rail.steps, CURVE_RAIL_SHORT_A, CURVE_RAIL_SHORT_D, CURVE_RAIL_SHORT_A_LEN, CURVE_RAIL_SHORT_D_LEN);
                        //         motor_rail.steps = 0;
                        // } else {
                        //  rail_running = true;
                        //  RAIL_TIMER.attachInterrupt(rail_loop).start(RAIL_PERIOD);
                        // }


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
        if (motor_p->steps) {
                motor_p->value = !motor_p->value;
                digitalWrite(MOTOR_PINS[motor_index][MOTOR_PULS], motor_p->value);
                motor_p->steps--;
        }
        else {
                MOTOR_TIMERS[motor_index].stop();
                motors_running[motor_index] = false;
        }
}

void motor_loop_1() {
        uint8_t motor_index = 1;
        Motor* motor_p = &motors[motor_index];
        if (motor_p->steps) {
                motor_p->value = !motor_p->value;
                digitalWrite(MOTOR_PINS[motor_index][MOTOR_PULS], motor_p->value);
                motor_p->steps--;
        }
        else {
                MOTOR_TIMERS[motor_index].stop();
                motors_running[motor_index] = false;
        }
}
void motor_loop_2() {
        uint8_t motor_index = 2;
        Motor* motor_p = &motors[motor_index];
        if (motor_p->steps) {
                motor_p->value = !motor_p->value;
                digitalWrite(MOTOR_PINS[motor_index][MOTOR_PULS], motor_p->value);
                motor_p->steps--;
        }
        else {
                MOTOR_TIMERS[motor_index].stop();
                motors_running[motor_index] = false;
        }
}
void motor_loop_3() {
        uint8_t motor_index = 3;
        Motor* motor_p = &motors[motor_index];
        if (motor_p->steps && !digitalRead(HOME_PIN) ) {
                motor_p->value = !motor_p->value;
                digitalWrite(MOTOR_PINS[motor_index][MOTOR_PULS], motor_p->value);
                motor_p->steps--;
        }
        else {
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
        for (uint8_t valve = 0; valve < PNEUMATIC_PIN_COUNT; valve++) {
                pinMode(PNEUMATIC_PINS[valve], OUTPUT);
                digitalWrite(PNEUMATIC_PINS[valve], 1);
        }

        pinMode(HOME_PIN, INPUT);

}

// void rail_run_curve(unsigned long *start, unsigned long *finish) {
//         unsigned long t0 = micros();
//         bool value       = 0;
//
//         while (start < finish) {
//                 delayMicroseconds(*start - (micros() - t0));
//
//                 value = !value;
//                 digitalWrite(RAIL_PINS[MOTOR_PULS], value);
//                 start++;
//         }
// }
//
// void rail_fast_run(uint16_t steps, unsigned long * A, unsigned long * D, uint16_t A_LEN, uint16_t D_LEN) {
//         rail_run_curve(A, A + A_LEN);
//
//         unsigned long delay_time = A[A_LEN - 1] - A[A_LEN - 2];
//         bool value               = 0;
//
//         steps = steps - A_LEN - D_LEN;
//
//         for (uint16_t i = 0; i < steps; i++) {
//                 value = !value;
//                 digitalWrite(RAIL_PINS[MOTOR_PULS], value);
//                 delayMicroseconds(delay_time);
//         }
//         rail_run_curve(D, D + D_LEN);
// }

bool home() {
        uint8_t motor_number = 3;
        uint8_t pulse_pin = MOTOR_PINS[motor_number][MOTOR_PULS];
        uint8_t dir_pin = MOTOR_PINS[motor_number][MOTOR_DIR];
        uint32_t pos_step_count = 20000;
        uint32_t neg_step_count = 500;


        digitalWrite(dir_pin, 0);
        while (!digitalRead(HOME_PIN)) {

                digitalWrite(pulse_pin, !digitalRead(pulse_pin));
                pos_step_count--;
                if (pos_step_count==0) return false;
                delay(2);

        }

        digitalWrite(dir_pin, 1);
        while (digitalRead(HOME_PIN)) {
                digitalWrite(pulse_pin, !digitalRead(pulse_pin));
                neg_step_count--;
                if (neg_step_count==0) return false;
                delay(2);
        }
        for (uint8_t i=0; i< 50; i++) {
                digitalWrite(pulse_pin, !digitalRead(pulse_pin));
                delay(2);
        }

        return true;

}
