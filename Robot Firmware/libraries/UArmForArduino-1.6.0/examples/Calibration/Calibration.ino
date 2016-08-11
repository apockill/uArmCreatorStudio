/******************************************************************************************
* File Name          : Calibration.ino
* Author             : Joey Song
* Update             : Alex Tan
* Version            : V2.0
* Description        : This documents is for calibration with uArm Metal version
* Copyright(C) 2016 uArm Team. All right reserved.
*******************************************************************************************/

#include "uarm_library.h"

int value;        // value is the data recevied

void setup() {

      Serial.begin(9600);  // start serial port at 9600 bps

}


void loop() {

      if(Serial.available()>0)
      {

          char readSerial = Serial.read();
          Serial.println(readSerial);

          // Input c to start calibrate automatically
          if (readSerial == 'c') {
            calibration_start();
            delay(1000);
            uarm.moveTo(0,-15,6);
          }

          //----------------------------------  Test Function  ------------------------------------
          if (readSerial == '1') {
            uarm.moveTo(15,-15,5);
            delay(1000);
           }


          if (readSerial == '2') {
            uarm.moveTo(-15,-15,5);
            delay(1000);
           }

          if (readSerial == 's') {
            Serial.println("linear offset:");
            for(byte i = 0;i < 4; i++)
            {
              Serial.print("Linear Offset Servo ");
              Serial.println(i);
              double a = 0.0f;
              double b = 0.0f;
              uarm.readLinearOffset(i,a,b);
              Serial.print("A: ");
              Serial.print(a);
              Serial.print(", B: ");
              Serial.println(b);
              Serial.print("Manual Offset: ");
              Serial.print(uarm.readServoOffset(i));
              Serial.println("");
            }
            delay(1000);
           }           
        }
}


/** Start Calibration all section
**/
void calibration_start(){

        cleanEEPROM();

        for (int k = 0; k < 4; k++) {

                linear_calibration_servo(k);
                delay(2000);
        }
        EEPROM.write(CALIBRATION_LINEAR_FLAG, CONFIRM_FLAG);
        manual_calibration_section();
        EEPROM.write(CALIBRATION_MANUAL_FLAG, CONFIRM_FLAG);
        EEPROM.write(CALIBRATION_FLAG, CONFIRM_FLAG);

        Serial.println("All done!");
}

/** Calibrate each servo for linear offset
**/
void linear_calibration_servo(byte servo_num)
{
        const byte kServoRangeIni = 20;
        const byte kServoRangeFin = 100;
        double l_angle_analog;
        double arr_real[16];
        double arr_input[16];
        int intercept_address =  LINEAR_INTERCEPT_START_ADDRESS;
        int slope_address = LINEAR_SLOPE_START_ADDRESS;
        Serial.print("intercept_address: ");
        Serial.println(intercept_address);
        Serial.print("slope_address: ");
        Serial.println(slope_address);
        Serial.print("servo ");
        Serial.println(servo_num);

        byte l_analog_pin;

        for (byte i = 0; i < (((kServoRangeFin-kServoRangeIni)/5)+1); i++)
        {
                byte dot_i = 5*i;
                float angle = kServoRangeIni+dot_i;
                switch(servo_num)
                {
                case SERVO_ROT_NUM:
                        l_analog_pin = SERVO_ROT_ANALOG_PIN;
                        uarm.writeServoAngle(SERVO_ROT_NUM, angle, false);
                        uarm.writeLeftRightServoAngle(60, 30, false);
                        break;

                case SERVO_LEFT_NUM:
                        l_analog_pin = SERVO_LEFT_ANALOG_PIN;
                        uarm.writeServoAngle(SERVO_ROT_NUM, 90, false);
                        uarm.writeLeftRightServoAngle(angle, 30, false);
                        break;

                case SERVO_RIGHT_NUM:
                        l_analog_pin = SERVO_RIGHT_ANALOG_PIN;
                        uarm.writeServoAngle(SERVO_ROT_NUM, 90, false);
                        uarm.writeLeftRightServoAngle(30, angle, false);
                        break;

                case SERVO_HAND_ROT_NUM:
                        l_analog_pin = SERVO_HAND_ROT_ANALOG_PIN;
                        uarm.writeServoAngle(SERVO_ROT_NUM, 90, false);
                        uarm.writeLeftRightServoAngle(60, 30, false);
                        uarm.writeServoAngle(SERVO_HAND_ROT_NUM, angle, false);
                        break;
                default:

                        break;
                }

                if(i == 0) {
                        delay(1000);
                }

                for (int l = 0; l<3; l++) {
                        l_angle_analog = analogRead(l_analog_pin);
                        delay(50);
                }

                arr_real[i] = kServoRangeIni + dot_i;
                arr_input[i] = l_angle_analog;

                delay(100);

        }
        arr_real[0] = kServoRangeIni;

        LinearRegression lr(arr_input, arr_real, 16);
        Serial.print("lr.getA():");
        Serial.println(lr.getA());
        Serial.print("lr.getB():");
        Serial.println(lr.getB());
        save_linear_servo_offset(servo_num, lr.getA(), lr.getB());
}

/** Clean EEPROM before calibration
**/
void cleanEEPROM(){
        for(int p = 0; p<EEPROM.length(); p++) {
                EEPROM.write(p,0);
        }
}

/**  Manual Calibration Section
**/
void manual_calibration_section()
{
        int setLoop = 1;

        uarm.detachAll();

        Serial.println("Put uarm in calibration posture (servo 1 to 3: 45, 130, 20 degree respectively), then input 1");
        while (setLoop) {

                if (Serial.available()>0) {

                        char inputChar = Serial.read();

                        if (inputChar=='1')
                        {
                                double offsetRot = uarm.readAngle(SERVO_ROT_NUM,true) - 45;
                                double offsetL = uarm.readAngle(SERVO_LEFT_NUM,true) - 130;
                                double offsetR = uarm.readAngle(SERVO_RIGHT_NUM,true) - 20;

                                Serial.print("Offsets for servo 1 to 3 are ");
                                Serial.println(offsetRot);
                                Serial.println(offsetL);
                                Serial.println(offsetR);


                                // if (abs(offsetRot)>25.4||abs(offsetL)>25.4||abs(offsetR)>25.4)
                                // {
                                //         Serial.print("Check posture");
                                // }
                                // else{
                                save_manual_servo_offset(SERVO_ROT_NUM, offsetRot);
                                save_manual_servo_offset(SERVO_LEFT_NUM, offsetL);
                                save_manual_servo_offset(SERVO_RIGHT_NUM, offsetR);
                                setLoop = 0;
                                Serial.println("Save offset done! ");
                                // }


                        }
                        else if(inputChar== 'e')
                        {
                                Serial.println("exit");
                                setLoop = 0;
                        }

                        else{
                                Serial.println("Incorrect, input again, or e to exit");
                        }

                }

        }
}

/** Save Manual Servo Offset
*
**/
void save_manual_servo_offset(byte servo_num, double offset)
{
        EEPROM.put(MANUAL_OFFSET_ADDRESS + servo_num * sizeof(offset), offset);
}

/** Save Linear Servo Offset intercept & slope
**/
void save_linear_servo_offset(byte servo_num, double intercept_val, double slope_val){
        EEPROM.put(LINEAR_INTERCEPT_START_ADDRESS + servo_num * sizeof(intercept_val), intercept_val);
        EEPROM.put(LINEAR_SLOPE_START_ADDRESS + servo_num * sizeof(slope_val), slope_val);
}
