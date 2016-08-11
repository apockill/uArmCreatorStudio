/******************************************************************************
 * File Name          : uArm_library.h
 * Author             : Joey Song
 * Updated            : Joey Song, Alex Tan, Dave Corboy
 * Email              : joey@ufactory.cc
 * Date               : 12 Dec, 2014
 * Description        :
 * License            :
 * Copyright(C) 2016 UFactory Team. All right reserved.
 *******************************************************************************/

#include <Arduino.h>
#include <EEPROM.h>
#include <Wire.h>
#include "UFServo.h"
#include "linreg.h"

#ifndef uArm_library_h
#define uArm_library_h

#define UARM_MAJOR_VERSION      1
#define UARM_MINOR_VERSION      6
#define UARM_BUGFIX             0 

#define SUCCESS                 1
#define FAILED                  -1

#define SERVO_ROT_NUM           0
#define SERVO_LEFT_NUM          1
#define SERVO_RIGHT_NUM         2
#define SERVO_HAND_ROT_NUM      3

#define SERVO_ROT_PIN           11
#define SERVO_LEFT_PIN          13
#define SERVO_RIGHT_PIN         12
#define SERVO_HAND_PIN          10

#define SERVO_ROT_ANALOG_PIN 2
#define SERVO_LEFT_ANALOG_PIN 0
#define SERVO_RIGHT_ANALOG_PIN 1
#define SERVO_HAND_ROT_ANALOG_PIN 3

// Old Control method Stretch / Height

#define ARM_STRETCH_MIN   0
#define ARM_STRETCH_MAX   195
#define ARM_HEIGHT_MIN   -150
#define ARM_HEIGHT_MAX   160
#define ARM_A      148
#define ARM_B      160
#define ARM_2AB     47360
#define ARM_A2      21904
#define ARM_B2      25600
#define ARM_A2B2     47504

#define LIMIT_SW                2    // LIMIT Switch Button
#define PUMP_EN                 6    // HIGH = Valve OPEN
#define VALVE_EN                5    // HIGH = Pump ON
#define STOPPER                 2    // LOW = Pressed
#define BUZZER                  3    // HIGH = ON
#define BTN_D4                  4    // LOW = Pressed
#define BTN_D7                  7    // LOW = Pressed
#define GRIPPER                 9    // LOW = Catch

#define MATH_PI 3.141592653589793238463
#define MATH_TRANS  57.2958
#define MATH_L1 (10.645+0.6)
#define MATH_L2 2.117
#define MATH_L3 14.825
#define MATH_L4 16.02
#define MATH_L43 MATH_L4/MATH_L3

#define RELATIVE 1
#define ABSOLUTE 0

#define TopOffset -1.5
#define BottomOffset 1.5

// Calibration Flag & OFFSET EEPROM ADDRESS
#define CALIBRATION_FLAG                    10
#define CALIBRATION_LINEAR_FLAG             11
#define CALIBRATION_MANUAL_FLAG             12
#define CALIBRATION_STRETCH_FLAG            13

#define LINEAR_INTERCEPT_START_ADDRESS      70
#define LINEAR_SLOPE_START_ADDRESS          50
#define MANUAL_OFFSET_ADDRESS               30
#define OFFSET_STRETCH_START_ADDRESS        20
#define SERIAL_NUMBER_ADDRESS               100

#define CONFIRM_FLAG                        0x80

// #define D090M_SERVO_MIN_PUL     500
// #define D090M_SERVO_MAX_PUL     2500
// #define D009A_SERVO_MIN_PUL     600
// #define D009A_SERVO_MAX_PUL     2550


// movement path types
#define PATH_LINEAR     0   // path based on linear interpolation
#define PATH_ANGLES     1   // path based on interpolation of servo angles

// movement absolute/relative flags
#define F_ABSOLUTE      0
#define F_POSN_RELATIVE 1
#define F_HAND_RELATIVE 2   // standard relative, current + hand parameter
#define F_HAND_ROT_REL  4   // hand keeps orientation relative to rotation servo (+/- hand parameter)
// #define F_NEXT_OPT   8   // these are flags, next option is next available bit

// interpolation intervals
//#define INTERP_INTVLS 100

// interpolation types
#define INTERP_EASE_INOUT_CUBIC 0  // original cubic ease in/out
#define INTERP_LINEAR           1
#define INTERP_EASE_INOUT       2  // quadratic easing methods
#define INTERP_EASE_IN          3
#define INTERP_EASE_OUT         4

#define LINEAR_INTERCEPT        1
#define LINEAR_SLOPE            2

// Setting parameters
// Servo Speed
// #define SERVO_SPEED_FLAG_ADDRESS     5
// #define SERVO_SPEED_ADDRESS          6
// #define DEFAULT_SERVO_SPEED          2

// // init postion when plug in
// #define INIT_ATTACH_FLAG_ADDRESS     7
// #define INIT_SERVO_ROT               90
// #define INIT_SERVO_LEFT              90
// #define INIT_SERVO_RIGHT             65
// #define INIT_SERVO_HAND              10

class uArmClass
{
public:
        uArmClass();

        double readServoOffset(byte servo_num);
        void readSerialNumber(byte (&byte_sn_array)[14]);
        void writeSerialNumber(byte (&byte_sn_array)[14]);
        void readLinearOffset(byte servo_num, double& intercept_val, double& slope_val);
        void detachServo(byte servo_num);
        void alert(byte times, byte runTime, byte stopTime);
        void detachAll();
        void writeServoAngle(byte servoNumber, double servoAngle,  boolean writeWithoffset);
        void writeLeftRightServoAngle(double servo_left_angle, double servo_right_angle, boolean writeWithoffset);
        byte inputToReal(byte servo_num, byte input_angle);
        double readAngle(byte servo_num);
        double readAngle(byte servo_num, boolean withOffset);
        double analogToAngle(int input_angle, byte servo_num, boolean withOffset);
        void writeAngle(byte servo_rot_angle, byte servo_left_angle, byte servo_right_angle, byte servo_hand_rot_angle, byte trigger);

        int moveToOpts(double x, double y, double z, double hand_angle, byte relative_flags, double time, byte path_type, byte ease_type);
        void moveTo(double x, double y,double z) {
                moveToOpts(x, y, z, 0, F_HAND_RELATIVE, 1.0, PATH_LINEAR, INTERP_EASE_INOUT_CUBIC);
        }
        void moveTo(double x, double y,double z,int relative, double time) {
                moveToOpts(x, y, z, 0, F_HAND_RELATIVE | (relative ? F_POSN_RELATIVE : 0), time, PATH_LINEAR, INTERP_EASE_INOUT_CUBIC);
        }
        void moveTo(double x, double y,double z,int relative, double time, double servo_4_angle) {
                moveToOpts(x, y, z, servo_4_angle, relative ? F_POSN_RELATIVE : 0, time, PATH_LINEAR, INTERP_EASE_INOUT_CUBIC);
        }
        void moveTo(double x, double y, double z, int relative, double time, int servo_4_relative, double servo_4_angle) {
                moveToOpts(x, y, z, servo_4_angle, (relative ? F_POSN_RELATIVE : 0) | (servo_4_relative ? F_HAND_RELATIVE : 0), time, PATH_LINEAR, INTERP_EASE_INOUT_CUBIC);
        }

        void moveToAtOnce(double x, double y, double z) {
                moveToOpts(x, y, z, 0, F_HAND_RELATIVE, 0.0, PATH_LINEAR, INTERP_LINEAR);
        }
        void moveToAtOnce(double x, double y, double z, int relative, double servo_4_angle) {
                moveToOpts(x, y, z, servo_4_angle, relative ? F_POSN_RELATIVE : 0, 0.0, PATH_LINEAR, INTERP_LINEAR);
        }

        void writeStretch(double armStretch, double armHeight);
        void writeAngle(double servo_rot_angle, double servo_left_angle, double servo_right_angle, double servo_hand_rot_angle);

        double getCalX() {
                return g_cal_x;
        }
        double getCalY() {
                return g_cal_y;
        }
        double getCalZ() {
                return g_cal_z;
        }
        void getCalXYZ(double& x, double& y, double &z) {
                calXYZ(); x = g_cal_x; y = g_cal_y; z = g_cal_z;
        }
        void getCalXYZ(double theta_1, double theta_2, double theta_3, double& x, double& y, double &z) {
                calXYZ(theta_1, theta_2, theta_3); x = g_cal_x; y = g_cal_y; z = g_cal_z;
        }

        void calAngles(double x, double y, double z, double& theta_1, double& theta_2, double& theta_3);

        void calXYZ(double theta_1, double theta_2, double theta_3);
        void calXYZ();

        void gripperCatch();
        void gripperRelease();
        void interpolate(double start_val, double end_val, double *interp_vals, byte ease_type);
        void pumpOn();
        void pumpOff();

        // Servo g_servo_rot;
        // Servo g_servo_left;
        // Servo g_servo_right;
        // Servo g_servo_hand_rot;
        // Servo g_servo_hand;
        Servo g_servo_rot;
        Servo g_servo_left;
        Servo g_servo_right;
        Servo g_servo_hand_rot;
        Servo g_servo_hand;

        // byte g_servo_speed;

        // CHANGES: 
         
        unsigned int INTERP_INTVLS;
        double cur_rot;
        double cur_left;
        double cur_right;
        double cur_hand;
protected:
        void attachAll();
        void attachServo(byte servo_num);
         
        
        double calYonly(double theta_1, double theta_2, double theta_3);

        double g_cal_x;
        double g_cal_y;
        double g_cal_z;

        boolean g_gripper_reset;
         

};

extern uArmClass uarm;

#endif
