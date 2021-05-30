#include <Arduino.h>
#include "DueTimer.h"
#include "encoder.h"
#include <base.h>
#include "trajectories.h"
#include "communication.h"

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
  void home();
  void move_motor(MoveMotor *command);
  void go_abs(int32_t  position,
              uint32_t delay_);

  void go_steps(int32_t  steps,
                uint32_t delay_,
                bool     block);

  void go_steps_trajectory(int32_t);

  bool limit_not_reached_p() {
    return (pin_limit_p == INVALID_PIN) || !digitalRead(pin_limit_p);
  }

  bool limit_not_reached_n() {
    return (pin_limit_n == INVALID_PIN) || !digitalRead(pin_limit_n);
  }

  void isr();
  void (*isr_ptr)();
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

void Motor::move_motor(MoveMotor *command)
{
  // # define MOVE_MOTOR_FLAGS_ENABLED 1
  // # define MOVE_MOTOR_FLAGS_BLOCK 2
  // # define MOVE_MOTOR_FLAGS_ABSOLUTE 4
  // typedef struct MoveMotor {
  //   int32_t  steps;
  //   int32_t  delay;
  //   uint32_t flags; // block - absolute
  //   uint32_t settling_delay;
  //   uint32_t telorance_soft;
  //   uint32_t telorance_hard;
  // } MoveMotor;

  if (CHECK_FLAG(command->flags, MOVE_MOTOR_FLAGS_ABSOLUTE)) {
    // absolute move - move will be certainly blocking
    if (this->encoder == NULL) return;

    if (
      (this->_status == not_defined)
      || (this->_status == running)
      || (this->_status == homeing_failed)
      ) return;

    int32_t position = command->steps;

    if (position < 0) position = 0;

    if (position > (int32_t)this->course) position = (int32_t)this->course;

    this->go_abs(position, command->delay);

    if (command->settling_delay > 0) delay(command->settling_delay);
    int32_t cur_pos     = this->encoder->read();
    int32_t to_go_enc   = position - cur_pos;
    int32_t to_go_steps = to_go_enc;

    if (abs(to_go_steps) > command->telorance_hard) return;

    if (abs(to_go_steps) < command->telorance_soft) return;

    this->go_steps(to_go_steps, command->delay, 1);

    if (command->settling_delay > 0) delay(command->settling_delay);
    return;
  } else {
    // relative move - no encoder check
    bool block = CHECK_FLAG(command->flags, MOVE_MOTOR_FLAGS_BLOCK);
    this->go_steps(command->steps, command->delay, block);
  }
}

void Motor::go_abs(int32_t  position,
                   uint32_t delay_) {
  int32_t cur_pos     = this->encoder->read();
  int32_t to_go_enc   = position - cur_pos;
  int32_t to_go_steps = to_go_enc;


  Trajectory_1d *trajectory = &TRAJECTORIES_1D[0];

  if (abs(to_go_steps) > (trajectory->distance_a  + 5)) this->go_steps_trajectory(
      to_go_steps);
  else this->go_steps(to_go_steps, delay_, 1);
}

void Motor::go_steps(int32_t  steps_raw,
                     uint32_t delay_,
                     bool     block) {
  if (this->_status == not_defined) return;

  this->_status = running;
  this->_dir    = steps_raw > 0;
  this->_steps  = abs(steps_raw) << 1;
  this->_value  = 0;

  digitalWrite(this->pin_dir, this->_dir);

  this->timer.start(delay_);

  if (block) while (this->_status == running);
}

void Motor::go_steps_trajectory(int32_t steps_raw) {
  Trajectory_1d *trajectory = &TRAJECTORIES_1D[0];


  this->_status = running;
  this->_dir    = steps_raw > 0;
  digitalWrite(this->pin_dir, this->_dir);
  uint32_t steps = ((uint32_t)abs(steps_raw)) << 1;

  bool value = 0;
  bool lnrn, lnrp, lnr;

  uint8_t   mode   = 0; // enum accel 0 , deaccel 1 , glide 2, done 4
  uint16_t  delay_ = 0;
  uint32_t  count  = 0;
  uint16_t *ptr    = trajectory->curve_a;

  while (steps) {
    lnrn = this->limit_not_reached_n();
    lnrp = this->limit_not_reached_p();
    lnr  = (_dir || lnrn) && (!_dir || lnrp);

    if (!lnr) break;

    if (count == 0) {
      if (mode == 0) {
        delay_ = *ptr;
        count  = *(ptr + 1);
        ptr    = ptr + 2;
      }

      if (mode == 1) {
        delay_ = *ptr;
        count  = *(ptr + 1);
        ptr    = ptr - 2;
      }

      if (mode == 2) {
        count = steps - trajectory->distance_a;
        ptr   = trajectory->curve_a + trajectory->len_a - 2;
        delay_--;
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
    delayMicroseconds(delay_);
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

  this->go_steps((int32_t)((float)this->course * -1.5), this->homing_delay,
                 true);

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

Motor *motors[MOTORS_NO] = {
  &Motor0,
  &Motor1,
  &Motor2,
  &Motor3,
};

#endif // ifndef Motor_h
