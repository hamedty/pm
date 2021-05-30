#include <Arduino.h>
#include <base.h>
#include "communication.h"

#ifndef Gpio_h
# define Gpio_h

class Gpio {
public:

  Gpio(uint32_t _mode) {
    mode = _mode;
  }

  uint8_t pin = INVALID_PIN;
  uint32_t mode;

  void set_pin(uint8_t pin_no) {
    pin = pin_no;

    if (pin != INVALID_PIN) pinMode(pin, mode);
  }

  bool read() {
    if (pin != INVALID_PIN) return digitalRead(pin);

    return 0;
  }

  void set(bool value) {
    if (pin != INVALID_PIN) digitalWrite(pin, value);
  }
};


Gpio valves[VALVES_NO] = {
  Gpio(OUTPUT), // 0
  Gpio(OUTPUT), // 1
  Gpio(OUTPUT), // 2
  Gpio(OUTPUT), // 3
  Gpio(OUTPUT), // 4
  Gpio(OUTPUT), // 5
  Gpio(OUTPUT), // 6
  Gpio(OUTPUT), // 7
  Gpio(OUTPUT), // 8
  Gpio(OUTPUT)  // 9
};

Gpio inputs[INPUTS_NO] = {
  Gpio(INPUT_PULLUP), // 0
  Gpio(INPUT_PULLUP), // 1
};

#endif // ifndef Motor_h
