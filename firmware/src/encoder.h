#include <Arduino.h>
#ifndef Encoder_h
# define Encoder_h
class Encoder {
public:

  bool index; // Encoder 0(2,13) or 1(5,4)
  bool initialized = false;
  Encoder(bool index) {
    this->index = index;
  }

  void init() {
    initialized = true;

    if (index == 0) {
      pinMode( 2, INPUT_PULLUP);
      pinMode(13, INPUT_PULLUP);

      REG_PMC_PCER0 = PMC_PCER0_PID27;   // activate clock for TC0
      REG_TC0_CMR0  = TC_CMR_TCCLKS_XC0; // select XC0 as clock source
      REG_TC0_BMR   = TC_BMR_QDEN  | TC_BMR_POSEN | TC_BMR_EDGPHA;
      REG_TC0_CCR0  = TC_CCR_CLKEN | TC_CCR_SWTRG;
    } else {
      pinMode(4, INPUT_PULLUP);
      pinMode(5, INPUT_PULLUP);

      REG_PMC_PCER1 = PMC_PCER1_PID33;
      REG_TC2_CMR0  = TC_CMR_TCCLKS_XC0;
      REG_TC2_BMR   = TC_BMR_QDEN | TC_BMR_POSEN  | TC_BMR_EDGPHA;
      REG_TC2_CCR0  = TC_CCR_CLKEN | TC_CCR_SWTRG;
    }
  }

  void reset() {
    if (this->index == 0) {
      REG_TC0_CCR0 = TC_CCR_CLKEN | TC_CCR_SWTRG;
    } else {
      REG_TC2_CCR0 = TC_CCR_CLKEN | TC_CCR_SWTRG;
    }
  }

  uint32_t read() {
    if (this->index == 0) {
      return REG_TC0_CV0;
    } else {
      return REG_TC2_CV0;
    }
  }
};

# define ENCODER_NO 2
Encoder encoders[ENCODER_NO] = {
  Encoder(0),
  Encoder(1),
};

#endif /* ifndef Encoder_h */
