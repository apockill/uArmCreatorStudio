#define PRODUCT_MKII
#include "uarm_library.h"

void setup() {
  Serial.begin(115200);  // start serial port at 115200 bps
  uarm.arm_setup();
  uarm.move_to(0,200,100,10,false);
}

void loop() {
  uarm.arm_process_commands();
}
