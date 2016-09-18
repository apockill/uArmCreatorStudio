// test by John Feng

//#define LATEST_HARDWARE
#include "uarm_library.h"

void setup() {
  Serial.begin(115200);
  //uarm.attach_all();
  //uarm.move_to(70,70,150,false);
  uarm.arm_setup();
  //uarm.detach_servo(SERVO_HAND_ROT_NUM);
  // Serial.println(current_ver);
  // Serial.println("start");
  //float intercept_val = 0.00f;
  //float slope_val = 0.00f;
  //LEFT_SERVO_OFFSET = read_servo_offset(SERVO_LEFT_NUM);
  //RIGHT_SERVO_OFFSET = read_servo_offset(SERVO_RIGHT_NUM);
  //ROT_SERVO_OFFSET = read_servo_offset(SERVO_ROT_NUM);
  /*
  Serial.println(uarm.read_servo_offset(SERVO_LEFT_NUM                                       ));
  Serial.println(uarm.read_servo_offset(SERVO_RIGHT_NUM));
  Serial.println(uarm.read_servo_offset(SERVO_ROT_NUM));
  EEPROM.get(LINEAR_INTERCEPT_START_ADDRESS , intercept_val);
  EEPROM.get(LINEAR_SLOPE_START_ADDRESS, slope_val);
  Serial.println(intercept_val);
  Serial.println(slope_val);
  */
}

void loop() {
  uarm.arm_process_commands();

}
