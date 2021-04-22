/*
   DueTimer.h - DueTimer header file, definition of methods and attributes...
   For instructions, go to https://github.com/ivanseidel/DueTimer

   Created by Ivan Seidel Gomes, March, 2013.
   Modified by Philipp Klaus, June 2013.
   Released into the public domain.
 */

#include "Arduino.h"
#include <inttypes.h>


#ifndef DueTimer_h
# define DueTimer_h


# define NUM_TIMERS  6

class DueTimer {
public:

  // Represents the timer id (index for the array of Timer structs)
  unsigned short timer;

protected:

  // Stores the object timer frequency
  // (allows to access current timer period and frequency):
  static double _frequency[NUM_TIMERS];

  // Picks the best clock to lower the error
  static uint8_t bestClock(double    frequency,
                           uint32_t& retRC);

  // Make Interrupt handlers friends, so they can use callbacks
  friend void TC3_Handler(void);
  friend void TC4_Handler(void);
  friend void TC5_Handler(void);
  friend void TC6_Handler(void);
  friend void TC7_Handler(void);
  friend void TC8_Handler(void);

  static void (*callbacks[NUM_TIMERS])();

  struct Timer
  {
    Tc       *tc;
    uint32_t  channel;
    IRQn_Type irq;
  };

  // Store timer configuration (static, as it's fixed for every object)
  static const Timer Timers[NUM_TIMERS];

public:

  int                                        getAvailable(void);

  DueTimer(unsigned short _timer);
  DueTimer                                 & attachInterrupt(void (*isr)());
  DueTimer                                 & detachInterrupt(void);
  DueTimer                                 & start(double microseconds = -1);
  DueTimer                                 & stop(void);
  DueTimer                                 & setFrequency(double frequency);
  DueTimer                                 & setPeriod(double microseconds);

  double                                     getFrequency(void) const;
  double                                     getPeriod(void) const;

  inline __attribute__((always_inline)) bool operator==(const DueTimer& rhs) const
  {
    return timer == rhs.timer;
  }

  inline __attribute__((always_inline)) bool operator!=(const DueTimer& rhs) const
  {
    return timer != rhs.timer;
  }
};
extern DueTimer Timer3;
extern DueTimer Timer4;
extern DueTimer Timer5;
extern DueTimer Timer6;
extern DueTimer Timer7;
extern DueTimer Timer8;

#endif // ifndef DueTimer_h
