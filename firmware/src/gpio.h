#include <Arduino.h>

#ifndef Gpio_h
# define Gpio_h

class Gpio {
public:

  Gpio(uint32_t _mode) {
    mode = _mode;
  }

  void setup(uint8_t pin_no, bool output) {
    pin = pin_no;

    if (output) pinMode(pin,   OUTPUT);
    else pinMode(pin,   INPUT_PULLUP);
  }

  uint8_t pin = 128;
  uint32_t mode;

  bool read() {
    return digitalRead(pin);
  }

  void set(bool value) {
    digitalWrite(pin, value);
  }
};

# define VALVES_NO 10
# define INPUTS_NO 2

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
