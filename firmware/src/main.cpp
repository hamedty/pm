#include <Arduino.h>
#include <SPI.h>
#include "PacketSerial.h"
#include "DueTimer.h"
#include "pins.h"
#include "curve_rail_long.h"
// #include "curve_rail_short.h"

#include "HX711.h"

// Timers
DueTimer MOTOR_TIMERS[MOTOR_COUNT] = {Timer4, Timer5, Timer6, Timer7};


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
void motor_loop_2();
void motor_loop_3();

void (*motor_loop_array[MOTOR_COUNT])(void) = {
        motor_loop_0, motor_loop_1, motor_loop_2, motor_loop_3
};

void rail_fast_run(uint16_t);

Motor motors[MOTOR_COUNT];

Command command;
volatile bool motors_running[MOTOR_COUNT];

PacketSerial packet_serial;
void process_command_wrapper(const uint8_t *, size_t);
uint8_t process_command(const uint8_t *, size_t);

HX711 loadcell_1;
HX711 loadcell_2;

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
        response.reserve[1] = !digitalRead(DI_1) | (!digitalRead(DI_2) << 1) | (!digitalRead(DI_3) << 2) | (!digitalRead(DI_4) << 3);
        response.reserve[2] = 0;

        packet_serial.send((uint8_t *)&response, sizeof(Response));
}

uint8_t process_command(const uint8_t *data, size_t size) {
        if (sizeof(Command) != size) {
                return ERR_INVALID_PACKET_SIZE;
        }
        memcpy(&command, data, size);

        // uint32_t total_steps = 0;

        // Pneumatic
        for (uint8_t valve = 0; valve < PNEUMATIC_COUNT; valve++) {
                digitalWrite(PNEUMATIC_PINS[valve], command.pneumatic[valve]);
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
                        if (motor_number==2)
                                Timer6.attachInterrupt(motor_loop_2).start(delay_);
                        if (motor_number==3)
                                if (abs(motor->steps) > (CURVE_RAIL_LONG_A_DISTANCE + CURVE_RAIL_LONG_D_DISTANCE + 20)) {
                                        rail_fast_run(motor->steps);
                                        motor->steps = 0;
                                        motors_running[motor_number] = false;

                                } else {
                                        Timer7.attachInterrupt(motor_loop_3).start(delay_);
                                }


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
        if (motor_p->steps && (!digitalRead(HOME_PIN) ||  motor_p->dir)) {
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
                        digitalWrite(MOTOR_PINS[motor][pin], MOTOR_PRESET[motor][pin]);
                }
        }

        // Valves
        for (uint8_t valve = 0; valve < PNEUMATIC_COUNT; valve++) {
                pinMode(PNEUMATIC_PINS[valve], OUTPUT);
                digitalWrite(PNEUMATIC_PINS[valve], 0);
        }

        // Encoder
        pinMode(ENC_A, INPUT_PULLUP);
        pinMode(ENC_B, INPUT_PULLUP);
        // For more information see http://forum.arduino.cc/index.php?topic=140205.30
        REG_PMC_PCER0 = PMC_PCER0_PID27;     // activate clock for TC0
        REG_TC0_CMR0 = TC_CMR_TCCLKS_XC0;    // select XC0 as clock source

        // activate quadrature encoder and position measure mode, no filters
        REG_TC0_BMR = TC_BMR_QDEN
                      | TC_BMR_POSEN
                      | TC_BMR_EDGPHA;

        // enable the clock (CLKEN=1) and reset the counter (SWTRG=1)
        REG_TC0_CCR0 = TC_CCR_CLKEN | TC_CCR_SWTRG;

        // Loadcells
        // loadcell_1.begin(LC1_DOUT_PIN, LC1_SCK_PIN);
        // loadcell_2.begin(LC2_DOUT_PIN, LC2_SCK_PIN);


        // Digital Output
        for (uint8_t pin_index = 0; pin_index < DO_COUNT; pin_index++) {
                pinMode(DO_PINS[pin_index], OUTPUT);
                digitalWrite(DO_PINS[pin_index], DO_PRESET[pin_index]);

        }

        // Digital Input
        for (uint8_t pin_index = 0; pin_index < DI_COUNT; pin_index++) {
                pinMode(DI_PINS[pin_index], INPUT_PULLUP);
        }


}

uint16_t rail_run_curve(unsigned long *start, unsigned long *finish) {
        bool value       = 0;
        uint16_t delay;

        while (start < finish) {
                delay = *start;
                uint16_t count = *(start +1);
                while(count) {
                        delayMicroseconds(delay);

                        value = !value;
                        digitalWrite(MOTOR_PINS[3][MOTOR_PULS], value);
                        count--;

                        if (digitalRead(HOME_PIN)) return 0;
                }

                start = start + 2;
        }
        return delay;
}

void rail_fast_run(uint16_t steps) {
        uint16_t delay_time = rail_run_curve(CURVE_RAIL_LONG_A, CURVE_RAIL_LONG_A + CURVE_RAIL_LONG_A_LEN);
        bool value               = 0;

        steps = steps - CURVE_RAIL_LONG_A_DISTANCE - CURVE_RAIL_LONG_D_DISTANCE;

        for (uint16_t i = 0; i < steps; i++) {
                value = !value;
                digitalWrite(MOTOR_PINS[3][MOTOR_PULS], value);
                if (digitalRead(HOME_PIN)) return;
                delayMicroseconds(delay_time);
        }
        rail_run_curve(CURVE_RAIL_LONG_D, CURVE_RAIL_LONG_D + CURVE_RAIL_LONG_D_LEN);
}

bool sure_pin_high(){
        for (int16_t i=0; i<1000; i++)
                if (!digitalRead(HOME_PIN))
                        return false;
        return true;
}
bool sure_pin_low(){
        for (int16_t i=0; i<1000; i++)
                if (digitalRead(HOME_PIN))
                        return false;

        return true;
}

bool home() {
        digitalWrite(PNEUMATIC_PINS[3], 1);
        uint8_t motor_number = 3;
        uint8_t pulse_pin = MOTOR_PINS[motor_number][MOTOR_PULS];
        uint8_t dir_pin = MOTOR_PINS[motor_number][MOTOR_DIR];
        uint32_t pos_step_count = 100000;
        uint32_t neg_step_count = 500;

        digitalWrite(dir_pin, 0);
        // while (!digitalRead(HOME_PIN)) {
        while (!sure_pin_high()) {
                digitalWrite(pulse_pin, !digitalRead(pulse_pin));
                pos_step_count--;
                if (pos_step_count==0) return false;
                delayMicroseconds(100);

        }

        digitalWrite(dir_pin, 1);
        while (!sure_pin_low()) {
                digitalWrite(pulse_pin, !digitalRead(pulse_pin));
                neg_step_count--;
                if (neg_step_count==0) return false;
                delay(1);
        }
        for (uint8_t i=0; i< 50; i++) {
                digitalWrite(pulse_pin, !digitalRead(pulse_pin));
                delay(1);
        }

        REG_TC0_CV0 = 0;
        return true;

}
