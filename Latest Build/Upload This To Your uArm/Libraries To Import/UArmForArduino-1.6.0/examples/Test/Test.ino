/******************************************************************************************
* File Name          : Test.ino
* Author             : Joey Song
* Version            : V1.0
* Date               : 26 Aug, 2014
* Modified Date      : 19 Nov, 2015
* Description        : This documents is for quick start with uArm Metal version
* Copyright(C) 2015 uArm Team. All right reserved.
*******************************************************************************************/

/*
 * Table of Content

 * Function 1 - 4 :    move to a certain point (f)
 * Fucntion 5 - 6 :    move a Rectangle or a curve (function 5-6)
 * Function 7 - 8 :    attach or detach all servos (function 7-8)
 * Function 9     :    uArm calibration
 * Function 10    :    read current coordinate x,y,z
 * Function 11    :    recording mode

*/

// headers should must include these four headers

#include <EEPROM.h>
#include <Wire.h>
#include "uarm_library.h"
#include <Servo.h>

// define a uArm
//uArmLibrary uArm;
int value;        // value is the data recevied

void setup() {

      Wire.begin();        // join i2c bus (address optional for master)
      Serial.begin(9600);  // start serial port at 9600 bps
}


void loop() {

  if(Serial.available()>0)
  {

      char readSerial = Serial.read();
      Serial.println(readSerial);

      //----------------------------------  function 1  ------------------------------------
      // function below is for move uArm from current position to absolute coordinate
      // x = 13, y = -13, z = 3

      if (readSerial == '1') {
        uarm.moveTo(13,-13,3);
        delay(1000);
       }

      //----------------------------------  function 2  ------------------------------------
      // function below is for move uArm from current position to absolute coordinate
      // x = -13, y = -13, z = 3

      if (readSerial == '2') {
        uarm.moveTo(-13,-13,3);
        delay(1000);
       }

      //----------------------------------  function 3  ------------------------------------
      // function below is for move uArm from current position to relatvie coordinate
      // (dot) dx = 4, dy = -3, dz = 2 in 5 seconds

      if (readSerial == '3') {
        uarm.moveTo(1,1,1,RELATIVE,2);
        delay(1000);
       }

      //----------------------------------  function 4  ------------------------------------
      // function below is for move uArm from current position to relatvie coordinate
      // (dot) dx = -4, dy = 3, dz = -2 in 5 seconds

      if (readSerial == '4') {
        uarm.moveTo(-4,3,-2,RELATIVE,5);
        delay(1000);
       }

      //----------------------------------  function 5  ------------------------------------
      // function below is for move uArm to draw a Rectangle with 10 cm long and 5 cm
      // width in 2 seconds for one arm ( 8s totally)

//      if (readSerial == '5') {
//        uarm.drawRec(10,5,2);
//        delay(1000);
//       }
//
//      //----------------------------------  function 6  ------------------------------------
//      // function below is for move uArm to draw a ellipse with 10 cm long and 10 cm
//      // width (circle) for full 360 degree in 2 seconds
//
//      if (readSerial == '6') {
//        uarm.drawCur(6,6,360,2);
//        delay(1000);
//       }

      //----------------------------------  function 7  ------------------------------------
      // function below is atach all servos

//      if (readSerial == 'a') {
//        uarm.attachAll();
//      }

      //----------------------------------  function 8  ------------------------------------
      // function below is detach all servos

      if (readSerial == 'd') {
        uarm.detachAll();
      }

      //----------------------------------  function 9  ------------------------------------
      // function below is for calibrate uArm

      // if (readSerial == 'c') {
      //   calib.calibrations();
      // }

      //----------------------------------  function 10  ------------------------------------
      // function below is for print current x,y,z absolute location

      if (readSerial == 'g') {
        Serial.print("The current location is ");
        Serial.print(uarm.getCalX());
        Serial.print(" , ");
        Serial.print(uarm.getCalY());
        Serial.print(" , ");
        Serial.print(uarm.getCalZ());
        Serial.println();
        delay(1000);
      }

      if (readSerial == 'k') {
        Serial.print("SERVO_ROT_NUM offset:");
        Serial.println(uarm.readServoOffset(SERVO_ROT_NUM));
        Serial.print("SERVO_LEFT_NUM offset:");
        Serial.println(uarm.readServoOffset(SERVO_LEFT_NUM));
        Serial.print("SERVO_RIGHT_NUM offset:");
        Serial.println(uarm.readServoOffset(SERVO_RIGHT_NUM));
        Serial.print("SERVO_HAND_ROT_NUM offset:");
        Serial.println(uarm.readServoOffset(SERVO_HAND_ROT_NUM));
      }

      if (readSerial == 'o') {
        uarm.pumpOn();
      }

      if (readSerial == 'f') {
        uarm.pumpOff();
      }

      //----------------------------------  function 11  ------------------------------------
      // function below is for record a 20 seconds trajactory for uArm
      // must put recordingMode in a loop

      // if (readSerial == 'r') {
      //   while(1){
      //     uArm.recordingMode(10);
      //   }
      // }

  } // close read available
}
