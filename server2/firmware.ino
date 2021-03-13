#include <Arduino.h>

#define N_OUT 6
int pins_out[N_OUT] = {8,7,6,5,4,3};

#define N_IN 4
int pins_in[N_IN] = {22,24,26,28};

int m4_dir = 33;
int m4_step = 35;

void setup() {
        // SerialUSB.begin(115200);

        // pinMode(LED_BUILTIN, OUTPUT);
        // digitalWrite(LED_BUILTIN, 0);

        pinMode(m4_dir, OUTPUT);
        digitalWrite(m4_dir, 0);

        pinMode(m4_step, OUTPUT);
        digitalWrite(m4_step, 0);


        // for (int i =0; i<N_OUT; i++) {
        //         pinMode(pins_out[i], OUTPUT);
        //         digitalWrite(pins_out[i], 0);
        // }
        //
        // for (int i =0; i<N_IN; i++) {
        //         pinMode(pins_in[i], INPUT);
        //         digitalWrite(pins_in[i], 0);
        // }

        // // Setup the quadrature encoder
        // // For more information see http://forum.arduino.cc/index.php?topic=140205.30
        // REG_PMC_PCER0 = PMC_PCER0_PID27;     // activate clock for TC0
        // REG_TC0_CMR0 = TC_CMR_TCCLKS_XC0;    // select XC0 as clock source
        //
        // // activate quadrature encoder and position measure mode, no filters
        // REG_TC0_BMR = TC_BMR_QDEN
        //               | TC_BMR_POSEN
        //               | TC_BMR_EDGPHA;
        //
        // // enable the clock (CLKEN=1) and reset the counter (SWTRG=1)
        // REG_TC0_CCR0 = TC_CCR_CLKEN | TC_CCR_SWTRG;

}

void loop() {
        delay(50);

        for (int i =0; i<1000; i++) {
                digitalWrite(m4_step, !digitalRead(m4_step));
                delay(1);
        }
        digitalWrite(m4_dir, !digitalRead(m4_dir));


        // int newPosition = REG_TC0_CV0; // Read the encoder position from register
        // SerialUSB.println(newPosition);

        // digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));

        // for (int i =0; i<N_OUT; i++) {
        //         digitalWrite(pins_out[i], !digitalRead(pins_out[i]));
        // }

        // for (int i =0; i<N_IN; i++) {
        //         digitalWrite(pins_out[i], digitalRead(pins_in[i]));
        //
        //         SerialUSB.print(digitalRead(pins_in[i]));
        // }
        // SerialUSB.println("");
}
