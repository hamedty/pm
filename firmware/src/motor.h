#include <Arduino.h>
#include "DueTimer.h"
#include "encoder.h"

#ifndef Motor_h
# define Motor_h

class Motor {
public:

  Motor();


  bool has_encoder = false;
  Encoder *encoder;

  DueTimer timer = Timer3;

  uint8_t pin_pulse = 0;
  uint8_t pin_dir   = 0;

  uint8_t pin_microstep_0 = 0;
  uint8_t pin_microstep_1 = 0;
  uint8_t pin_microstep_2 = 0;

  uint8_t pin_limit_p = 0;
  uint8_t pin_limit_n = 0;

  int32_t _steps;
  bool _value;
  bool _dir;

  void     set_pins(uint8_t pin_pulse,
                    uint8_t pin_dir);
  void     set_isr(void (*isr)());
  void     set_timer();
  void     init();
  uint32_t home();
  uint32_t go_steps(int32_t  steps,
                    uint32_t delay);
  bool     limit_not_reached() {
    return true;
  }

  void isr();
  void (*isr_ptr)();

  // uint32_t go_steps(int         steps,
  //                   Trajectory *trajectory);
};


Motor::Motor() {}

void Motor::set_pins(uint8_t pin_pulse,
                     uint8_t pin_dir) {
  this->pin_pulse = pin_pulse;

  this->pin_dir = pin_dir;

  pinMode(pin_pulse, OUTPUT);
  pinMode(pin_dir,   OUTPUT);
}

void Motor::set_isr(void (*isr)()) {
  this->isr_ptr = isr;
}

void Motor::set_timer() {
  this->timer.timer = this->timer.getAvailable();
  this->timer.attachInterrupt(this->isr_ptr);
}

void     Motor::init() {}

uint32_t Motor::home() {
  return 10;
}

uint32_t Motor::go_steps(int32_t steps_raw, uint32_t delay) {
  this->_dir   = steps_raw > 0;
  this->_steps = abs(steps_raw) << 2;
  this->_value = 0;

  digitalWrite(this->pin_dir, this->_dir);

  this->timer.start(delay);

  return 0;
}

void Motor::isr() {
  if (this->_steps && this->limit_not_reached()) {
    this->_value = !this->_value;
    digitalWrite(this->pin_pulse, this->_value);
    this->_steps--;
  }
  else {
    this->timer.stop();
    this->_steps = 0;
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

#endif // ifndef Motor_h
