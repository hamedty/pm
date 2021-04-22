#include <Arduino.h>
#include "DueTimer.h"
#include "encoder.h"
#include <base.h>

#ifndef Motor_h
# define Motor_h
enum MotorStatus { idle, running, limit_reached };

class Motor {
public:

  Motor();

  Encoder *encoder = NULL;

  DueTimer timer = Timer3;

  uint8_t pin_pulse = INVALID_PIN;
  uint8_t pin_dir   = INVALID_PIN;

  uint8_t pin_microstep_0 = INVALID_PIN;
  uint8_t pin_microstep_1 = INVALID_PIN;
  uint8_t pin_microstep_2 = INVALID_PIN;

  uint8_t pin_limit_p = INVALID_PIN;
  uint8_t pin_limit_n = INVALID_PIN;

  volatile MotorStatus _status = idle;
  volatile int32_t _steps;
  volatile bool _value;
  volatile bool _dir;

  void set_pins(uint8_t pin_pulse,
                uint8_t pin_dir,
                uint8_t pin_limit_p,
                uint8_t pin_limit_n,
                uint8_t pin_microstep_0,
                uint8_t pin_microstep_1,
                uint8_t pin_microstep_2
                );
  void     set_isr(void (*isr)());
  void     set_timer();
  void     set_encoder(Encoder *);
  void     init();
  uint32_t home();
  uint32_t go_steps(int32_t  steps,
                    uint32_t delay);
  bool     limit_not_reached() {
    return
      (!_dir || (pin_limit_p == INVALID_PIN) || !digitalRead(pin_limit_p))
      &&
      (_dir || (pin_limit_n == INVALID_PIN) || !digitalRead(pin_limit_n));
  }

  void isr();
  void (*isr_ptr)();

  // uint32_t go_steps(int         steps,
  //                   Trajectory *trajectory);
};


Motor::Motor() {}

void Motor::set_pins(uint8_t pin_pulse,
                     uint8_t pin_dir,
                     uint8_t pin_limit_p,
                     uint8_t pin_limit_n,
                     uint8_t pin_microstep_0,
                     uint8_t pin_microstep_1,
                     uint8_t pin_microstep_2
                     ) {
  this->pin_pulse = pin_pulse;
  this->pin_dir   = pin_dir;

  pinMode(pin_pulse, OUTPUT);
  pinMode(pin_dir,   OUTPUT);

  this->pin_limit_p = pin_limit_p;

  if (pin_limit_p != INVALID_PIN) pinMode(pin_limit_p,   INPUT_PULLUP);

  this->pin_limit_n = pin_limit_n;

  if (pin_limit_n != INVALID_PIN) pinMode(pin_limit_n,   INPUT_PULLUP);

  this->pin_microstep_0 = pin_microstep_0;

  if (pin_microstep_0 != INVALID_PIN) pinMode(pin_microstep_0,   OUTPUT);

  this->pin_microstep_1 = pin_microstep_1;

  if (pin_microstep_1 != INVALID_PIN) pinMode(pin_microstep_1,   OUTPUT);

  this->pin_microstep_2 = pin_microstep_2;

  if (pin_microstep_2 != INVALID_PIN) pinMode(pin_microstep_2,   OUTPUT);
}

void Motor::set_isr(void (*isr)()) {
  this->isr_ptr = isr;
}

void Motor::set_timer() {
  this->timer.timer = this->timer.getAvailable();
  this->timer.attachInterrupt(this->isr_ptr);
}

void Motor::set_encoder(Encoder *enc) {
  encoder = enc;
}

void     Motor::init() {}

uint32_t Motor::home() {
  return 10;
}

uint32_t Motor::go_steps(int32_t steps_raw, uint32_t delay) {
  this->_status = running;
  this->_dir    = steps_raw > 0;
  this->_steps  = abs(steps_raw) << 2;
  this->_value  = 0;

  digitalWrite(this->pin_dir, this->_dir);

  this->timer.start(delay);

  while (this->_status == running);

  return 0;
}

void Motor::isr() {
  bool steps = this->_steps;
  bool ll    = this->limit_not_reached();

  if (steps && ll) {
    this->_value = !this->_value;
    digitalWrite(this->pin_pulse, this->_value);
    this->_steps--;
    return;
  }
  this->timer.stop();
  this->_steps = 0;

  if (!steps) {
    this->_status = idle;
    return;
  }

  if (!ll) {
    this->_status = limit_reached;
    return;
  }
}

Motor Motor0;
Motor Motor1;
Motor Motor2;
Motor Motor3;

void m0_isr() {
  Motor0.isr();
}

void m1_isr() {
  Motor1.isr();
}

void m2_isr() {
  Motor2.isr();
}

void m3_isr() {
  Motor3.isr();
}

# define MOTORS_NO 4
Motor *motors[MOTORS_NO] = {
  &Motor0,
  &Motor1,
  &Motor2,
  &Motor3,
};

#endif // ifndef Motor_h
