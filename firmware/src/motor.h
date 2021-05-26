#include <Arduino.h>
#include "DueTimer.h"
#include "encoder.h"
#include <base.h>
#include "trajectories.h"

#ifndef Motor_h
# define Motor_h
enum MotorStatus { not_defined, idle, running, limit_reached_p, limit_reached_n,
                   homed, homeing_failed };

class Motor {
public:

  Motor();

  Encoder *encoder = NULL;

  DueTimer timer = Timer3;
  bool timer_set = false;

  uint8_t pin_pulse = INVALID_PIN;
  uint8_t pin_dir   = INVALID_PIN;

  uint8_t pin_microstep_0 = INVALID_PIN;
  uint8_t pin_microstep_1 = INVALID_PIN;
  uint8_t pin_microstep_2 = INVALID_PIN;

  uint8_t pin_limit_p = INVALID_PIN;
  uint8_t pin_limit_n = INVALID_PIN;

  uint32_t course = 0;
  uint32_t homing_delay;
  uint32_t home_retract;

  volatile MotorStatus _status = not_defined;
  volatile int32_t _steps;
  volatile bool _value;
  volatile bool _dir;
  uint32_t microstep     = 1;
  uint32_t encoder_ratio = 1;

  void set_pins(uint8_t pin_pulse,
                uint8_t pin_dir,
                uint8_t pin_limit_p,
                uint8_t pin_limit_n,
                uint8_t pin_microstep_0,
                uint8_t pin_microstep_1,
                uint8_t pin_microstep_2
                );
  void set_isr(void (*isr)());
  void set_timer();
  void set_encoder(Encoder *, int32_t);
  void set_microstep(uint32_t);
  void set_homing_params(uint32_t, uint32_t, uint32_t);
  void     home();
  uint32_t go_abs(int32_t  position,
                  uint32_t delay,
                  bool     block);

  uint32_t go_steps(int32_t  steps,
                    uint32_t delay,
                    bool     block);

  uint32_t go_steps_trajectory(int32_t);

  bool limit_not_reached_p() {
    return (pin_limit_p == INVALID_PIN) || !digitalRead(pin_limit_p);
  }

  bool limit_not_reached_n() {
    return (pin_limit_n == INVALID_PIN) || !digitalRead(pin_limit_n);
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

  this->_status = idle;
}

void Motor::set_microstep(uint32_t _microstep) {
  if ((pin_microstep_0 == INVALID_PIN) ||
      (pin_microstep_1 == INVALID_PIN) ||
      (pin_microstep_2 == INVALID_PIN)) return;

  if ((_microstep != 1) &&
      (_microstep != 2) &&
      (_microstep != 4) &&
      (_microstep != 8) &&
      (_microstep != 16) &&
      (_microstep != 32)) return;

  microstep = _microstep;
  digitalWrite(pin_microstep_0, (microstep == 2) ||
               (microstep == 8) ||
               (microstep == 32));
  digitalWrite(pin_microstep_1, (microstep == 4) || (microstep == 8));
  digitalWrite(pin_microstep_2, microstep >= 16);
}

void Motor::set_isr(void (*isr)()) {
  this->isr_ptr = isr;
}

void Motor::set_timer() {
  if (timer_set) return;

  timer_set         = true;
  this->timer.timer = this->timer.getAvailable();
  this->timer.attachInterrupt(this->isr_ptr);
}

void Motor::set_encoder(Encoder *enc, int32_t encoder_ratio) {
  if (this->encoder == enc) return;

  encoder = enc;

  if (enc) { // encoder in not NULL
    this->_status        = homeing_failed;
    this->encoder->ratio = encoder_ratio;
  }
}

void Motor::set_homing_params(uint32_t _course,
                              uint32_t _homing_delay,
                              uint32_t _home_retract) {
  this->course       = _course;
  this->homing_delay = _homing_delay;
  this->home_retract = _home_retract;
}

uint32_t Motor::go_abs(int32_t  position,
                       uint32_t delay,
                       bool     block) {
  if (
    (this->_status == not_defined)
    || (this->_status == running)
    || (this->_status == homeing_failed)
    ) return 0;

  if (this->encoder == NULL) return 0;


  int32_t cur_pos = this->encoder->read();

  if (position < 0) position = 0;

  if (position > (int32_t)this->course) position = (int32_t)this->course;

  int32_t to_go_enc   = position - cur_pos;
  int32_t to_go_steps = to_go_enc;


  Trajectory_1d *trajectory = &TRAJECTORIES_1D[0];

  if ((abs(to_go_steps) > (trajectory->distance_a  + 5)) &&
      block) return this->go_steps_trajectory(to_go_steps);
  else return this->go_steps(to_go_steps, delay, block);
}

uint32_t Motor::go_steps(int32_t  steps_raw,
                         uint32_t delay,
                         bool     block) {
  if (this->_status == not_defined) return 0;

  this->_status = running;
  this->_dir    = steps_raw > 0;
  this->_steps  = abs(steps_raw) << 1;
  this->_value  = 0;

  digitalWrite(this->pin_dir, this->_dir);

  this->timer.start(delay);

  if (block) while (this->_status == running);
  return 0;
}

uint32_t Motor::go_steps_trajectory(int32_t steps_raw) {
  Trajectory_1d *trajectory = &TRAJECTORIES_1D[0];


  this->_status = running;
  this->_dir    = steps_raw > 0;
  digitalWrite(this->pin_dir, this->_dir);
  uint32_t steps = ((uint32_t)abs(steps_raw)) << 1;

  bool value = 0;
  bool lnrn, lnrp, lnr;

  uint8_t   mode  = 0; // enum accel 0 , deaccel 1 , glide 2, done 4
  uint16_t  delay = 0;
  uint32_t  count = 0;
  uint16_t *ptr   = trajectory->curve_a;

  while (steps) {
    lnrn = this->limit_not_reached_n();
    lnrp = this->limit_not_reached_p();
    lnr  = (_dir || lnrn) && (!_dir || lnrp);

    if (!lnr) break;

    if (count == 0) {
      if (mode == 0) {
        delay = *ptr;
        count = *(ptr + 1);
        ptr   = ptr + 2;
      }

      if (mode == 1) {
        delay = *ptr;
        count = *(ptr + 1);
        ptr   = ptr - 2;
      }

      if (mode == 2) {
        count = steps - trajectory->distance_a;
        ptr   = trajectory->curve_a + trajectory->len_a - 2;
        delay--;
        mode = 1;
      }

      if ((mode == 0) && (ptr == (trajectory->curve_a + trajectory->len_a)))
      {
        mode = 2;
      }
    }
    value = !value;
    digitalWrite(this->pin_pulse, value);
    steps--;
    count--;
    delayMicroseconds(delay);
  }


  if (!lnrn) {
    this->_status = limit_reached_n;
  }

  if (!lnrp) {
    this->_status = limit_reached_p;
  }

  if (!steps) {
    this->_status = idle;
  }


  return 0;
}

void Motor::home() {
  if (!this->course) return;

  if ((this->_status == not_defined) || (this->_status == running)) return;

  if ((this->_status == limit_reached_n) || (this->_status == homed) ||
      (!this->limit_not_reached_n()))
  {
    this->go_steps((int32_t)((float)this->course * 0.1), this->homing_delay,
                   true);

    if (!this->limit_not_reached_n()) {
      this->_status = homeing_failed;
      return;
    }
  }

  this->go_steps((int32_t)((float)this->course * -1.5), this->homing_delay, true);

  if (this->_status != limit_reached_n) {
    this->_status = homeing_failed;
    return;
  }
  delay(200);
  this->go_steps((int32_t)(this->home_retract), this->homing_delay * 5, true);

  if (this->_status != idle) {
    this->_status = homeing_failed;
    return;
  }

  this->_status = homed;

  if (this->encoder) this->encoder->reset();
}

void Motor::isr() {
  bool steps = this->_steps;
  bool lnrn  = this->limit_not_reached_n();
  bool lnrp  = this->limit_not_reached_p();

  bool lnr = (_dir || lnrn) && (!_dir || lnrp);

  if (steps && lnr) {
    this->_value = !this->_value;
    digitalWrite(this->pin_pulse, this->_value);
    this->_steps--;
    return;
  }
  this->timer.stop();
  this->_steps = 0;

  if (!lnrn) {
    this->_status = limit_reached_n;
    return;
  }

  if (!lnrp) {
    this->_status = limit_reached_p;
    return;
  }

  if (!steps) {
    this->_status = idle;
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
