/******************************************************************************
 * File Name          : uArm_library.cpp
 * Author             : Joey Song
 * Updated            : Joey Song, Alex Tan, Dave Corboy
 * Email              : joey@ufactory.cc
 * Description        :
 * License            :
 * Copyright(C) 2016 UFactory Team. All right reserved.
 *******************************************************************************/

#include "uarm_library.h"

uArmClass uarm;

uArmClass::uArmClass()
{
        // read Attach Setting from EEPROM Address: 07
        // if (EEPROM.read(INIT_ATTACH_FLAG_ADDRESS) == CONFIRM_FLAG)
        // {
        //     g_servo_speed = 10;
        //     attachAll();
        //     servoL.write(map(readAngle(SERVO_L), SERVO_MIN, SERVO_MAX, 0, 180));
    	// 	servoR.write(map(readAngle(SERVO_R), SERVO_MIN, SERVO_MAX, 0, 180));
    	// 	servoRot.write(map(readAngle(SERVO_ROT), SERVO_MIN, SERVO_MAX, 0, 180));
        //     writeServoAngle(SERVO_ROT_NUM, INIT_SERVO_ROT, false);
        //     writeServoAngle(SERVO_LEFT_NUM, INIT_SERVO_LEFT, false);
        //     writeServoAngle(SERVO_RIGHT_NUM, INIT_SERVO_RIGHT, false);
        // }
        // read Servo Speed Setting from EEPROM Address: 05
        // g_servo_speed = DEFAULT_SERVO_SPEED;
        // if (EEPROM.read(SERVO_SPEED_FLAG_ADDRESS) == CONFIRM_FLAG)
        // {
        //     EEPROM.get(SERVO_SPEED_ADDRESS, g_servo_speed);
        // }


}

/* Read Serial Number from EEPROM
 * SERIAL NUMBER ADDRESS : 1024, Size: 14
 */
void uArmClass::readSerialNumber(byte (&byte_sn_array)[14]){
        if (EEPROM.read(SERIAL_NUMBER_ADDRESS) == CONFIRM_FLAG) {
                for(byte i=0; i<14; i++) {
                        byte_sn_array[i] = EEPROM.read(SERIAL_NUMBER_ADDRESS+i+1);
                }
        }
}

/* Write Serial Number to EEPROM
 * SERIAL NUMBER ADDRESS : 1024, Size: 14
 */
void uArmClass::writeSerialNumber(byte (&byte_sn_array)[14]){
        for(byte i=0; i<14; i++) {
                EEPROM.write(SERIAL_NUMBER_ADDRESS+i+1, byte_sn_array[i]);
        }
        EEPROM.write(SERIAL_NUMBER_ADDRESS, CONFIRM_FLAG);
}

/* Use BUZZER for Alert
 * times - how many times
 * runTime - how long one time last when BUZZER speak
 * stopTime - Close BUZZER time
 */
void uArmClass::alert(byte times, byte runTime, byte stopTime)
{
        for(int ct=0; ct < times; ct++)
        {
                delay(stopTime);
                digitalWrite(BUZZER, HIGH);
                delay(runTime);
                digitalWrite(BUZZER, LOW);
        }
}

void uArmClass::writeAngle(double servo_rot_angle, double servo_left_angle, double servo_right_angle, double servo_hand_rot_angle)
{
        attachAll();

        if(servo_left_angle < 10) servo_left_angle = 10;
        if(servo_left_angle > 120) servo_left_angle = 120;
        if(servo_right_angle < 10) servo_right_angle = 10;
        if(servo_right_angle > 110) servo_right_angle = 110;

        if(servo_left_angle + servo_right_angle > 160)
        {
                servo_right_angle = 160 - servo_left_angle;
                return;
        }
        writeServoAngle(SERVO_ROT_NUM,servo_rot_angle,true);
        writeServoAngle(SERVO_LEFT_NUM,servo_left_angle,true);
        writeServoAngle(SERVO_RIGHT_NUM,servo_right_angle,true);
        writeServoAngle(SERVO_HAND_ROT_NUM,servo_hand_rot_angle,true);


        // refresh logical servo angle cache
        cur_rot = servo_rot_angle;
        cur_left = servo_left_angle;
        cur_right = servo_right_angle;
        cur_hand = servo_hand_rot_angle;
}

/* Write the angle to Servo
 * servo_number - SERVO_ROT_NUM, SERVO_LEFT_NUM, SERVO_RIGHT_NUM, SERVO_HAND_ROT_NUM
 * servo_angle  - Servo target angle
 * writeWithoffset - True: with Offset, False: without Offset
 */
void uArmClass::writeServoAngle(byte servo_number, double servo_angle, boolean writeWithoffset)
{
        attachServo(servo_number);
    servo_angle = writeWithoffset ? inputToReal(servo_number,servo_angle) : servo_angle;
    servo_angle = constrain(servo_angle,0.0,180.0);
        switch(servo_number)
        {
        case SERVO_ROT_NUM:       g_servo_rot.write(servo_angle);
                cur_rot = servo_angle;
                break;
        case SERVO_LEFT_NUM:      g_servo_left.write(servo_angle);
                cur_left = servo_angle;
                break;
        case SERVO_RIGHT_NUM:     g_servo_right.write(servo_angle);
                cur_right = servo_angle;
                break;
        case SERVO_HAND_ROT_NUM:  g_servo_hand_rot.write(servo_angle);
                cur_hand = servo_angle;
                break;
        default:                  break;
        }
}


/* Write the left Servo & Right Servo in the same time (Avoid demage the Servo)
 * servo_left_angle - left servo target angle
 * servo_right_angle  - right servo target angle
 * writeWithoffset - True: with Offset, False: without Offset
 */
void uArmClass::writeLeftRightServoAngle(double servo_left_angle, double servo_right_angle, boolean writeWithoffset)
{
        servo_left_angle = constrain(servo_left_angle,0,150);
        servo_right_angle = constrain(servo_right_angle,0,120);
        servo_left_angle = writeWithoffset ? round(inputToReal(SERVO_LEFT_NUM,servo_left_angle)) : round(servo_left_angle);
        servo_right_angle = writeWithoffset ? round(inputToReal(SERVO_RIGHT_NUM,servo_right_angle)) : round(servo_right_angle);
        if(servo_left_angle + servo_right_angle > 180) // if left angle & right angle exceed 180 degree, it might be caused damage
        {
                alert(1, 10, 0);
                return;
        }
        attachServo(SERVO_LEFT_NUM);
        attachServo(SERVO_RIGHT_NUM);
        g_servo_left.write(servo_left_angle);
        g_servo_right.write(servo_right_angle);
}

/* Warning, if you attach left servo & right servo without a movement, it might be caused a demage
 */
void uArmClass::attachAll()
{
        attachServo(SERVO_ROT_NUM);
        attachServo(SERVO_LEFT_NUM);
        attachServo(SERVO_RIGHT_NUM);
        attachServo(SERVO_HAND_ROT_NUM);
}

/* Attach Servo by given servo number, SERVO_ROT_NUM, SERVO_LEFT_NUM, SERVO_RIGHT_NUM
 * if servo has not been attached, attach the servo, and read the current Angle
 */
void uArmClass::attachServo(byte servo_number)
{
        switch(servo_number) {
        case SERVO_ROT_NUM:
                if(!g_servo_rot.attached()) {
                        g_servo_rot.attach(SERVO_ROT_PIN);
                        cur_rot = readAngle(SERVO_ROT_NUM);
                }
                break;
        case SERVO_LEFT_NUM:
                if (!g_servo_left.attached()) {
                        g_servo_left.attach(SERVO_LEFT_PIN);
                        cur_left = readAngle(SERVO_LEFT_NUM);
                }
                break;
        case SERVO_RIGHT_NUM:
                if (!g_servo_right.attached()) {
                        g_servo_right.attach(SERVO_RIGHT_PIN);
                        cur_right = readAngle(SERVO_RIGHT_NUM);
                }
                break;
        case SERVO_HAND_ROT_NUM:
                if (!g_servo_hand_rot.attached()) {
                        g_servo_hand_rot.attach(SERVO_HAND_PIN);
                        cur_hand = readAngle(SERVO_HAND_ROT_NUM);
                }
                break;
        }
}

/* Detach All servo, you could move the arm
 */
void uArmClass::detachAll()
{
        g_servo_rot.detach();
        g_servo_left.detach();
        g_servo_right.detach();
        g_servo_hand_rot.detach();
}

/* get a input angle with servo Offset
 */
byte uArmClass::inputToReal(byte servo_num,byte input_angle)
{
        return (byte)constrain(round((input_angle + readServoOffset(servo_num))),0,180);
}

/* Read the servo offset from EEPROM, From OFFSET_START_ADDRESS, each offset occupy 4 bytes in rom
 */
double uArmClass::readServoOffset(byte servo_num)
{
        double manual_servo_offset = 0.0f;
        EEPROM.get(MANUAL_OFFSET_ADDRESS + servo_num * sizeof(manual_servo_offset), manual_servo_offset);
        return manual_servo_offset;
}

/** read Linear Offset from EEPROM,
** From LINEAR_INTERCEPT_START_ADDRESS & LINEAR_SLOPE_START_ADDRESS, each offset occupy 4 bytes in rom
**/
void uArmClass::readLinearOffset(byte servo_num, double& intercept_val, double& slope_val){
        EEPROM.get(LINEAR_INTERCEPT_START_ADDRESS + servo_num * sizeof(intercept_val), intercept_val);
        EEPROM.get(LINEAR_SLOPE_START_ADDRESS + servo_num * sizeof(slope_val), slope_val);
}

/** Convert the Analog to Servo Angle, by this formatter
** angle = intercept + slope * analog
**/
double uArmClass::analogToAngle(int input_analog, byte servo_num, boolean withOffset)
{
        double intercept = 0.0f;
        double slope = 0.0f;
        readLinearOffset(servo_num, intercept, slope);
        double angle = intercept + slope*input_analog;
        return withOffset ? angle - readServoOffset(servo_num) : angle;
}

/** read Angle by servo_num, SERVO_ROT_NUM, SERVO_LEFT_NUM, SERVO_RIGHT_NUM, SERVO_HAND_ROT_NUM
** without offset
**/
double uArmClass::readAngle(byte servo_num)
{
        return readAngle(servo_num, false);
}

/** read Angle by servo_num, SERVO_ROT_NUM, SERVO_LEFT_NUM, SERVO_RIGHT_NUM, SERVO_HAND_ROT_NUM
** withOffset - True: with Offset, False: Without Offset
**/
double uArmClass::readAngle(byte servo_num, boolean withOffset)
{
        switch (servo_num)
        {
        case SERVO_ROT_NUM:
                return analogToAngle(analogRead(SERVO_ROT_ANALOG_PIN),SERVO_ROT_NUM,withOffset);
                break;

        case SERVO_LEFT_NUM:
                return analogToAngle(analogRead(SERVO_LEFT_ANALOG_PIN),SERVO_LEFT_NUM,withOffset);
                break;

        case SERVO_RIGHT_NUM:
                return analogToAngle(analogRead(SERVO_RIGHT_ANALOG_PIN),SERVO_RIGHT_NUM,withOffset);
                break;

        case SERVO_HAND_ROT_NUM:
                return analogToAngle(analogRead(SERVO_HAND_ROT_ANALOG_PIN),SERVO_HAND_ROT_NUM,withOffset);
                break;

        default:
                break;

        }
}

/*Action control */

/** Calculate the angles from given coordinate x, y, z to theta_1, theta_2, theta_3
**/
void uArmClass::calAngles(double x, double y, double z, double& theta_1, double& theta_2, double& theta_3)
{
        if (z > (MATH_L1 + MATH_L3 + TopOffset))
        {
                z = MATH_L1 + MATH_L3 + TopOffset;
        }

        if (z < (MATH_L1 - MATH_L4 + BottomOffset))
        {
                z = MATH_L1 - MATH_L4 + BottomOffset;
        }


        double x_in = 0.0;
        double y_in = 0.0;
        double z_in = 0.0;
        double right_all = 0.0;
        double right_all_2 = 0.0;
        double sqrt_z_x = 0.0;
        double sqrt_z_y = 0.0;
        double phi = 0.0;

        y_in = (-y-MATH_L2)/MATH_L3;
        z_in = (z - MATH_L1) / MATH_L3;
        right_all = (1 - y_in*y_in - z_in*z_in - MATH_L43*MATH_L43) / (2 * MATH_L43);
        sqrt_z_y = sqrt(z_in*z_in + y_in*y_in);

        // get rid of divide by zero errors.
        // Because x is a double we need to check a range
        if (x <= 0.005 && x >= -0.005)
        {
                // Calculate value of theta 1
                theta_1 = 90;

                // Calculate value of theta 3
                if (z_in == 0) {
                        phi = 90;
                }

                else {
                        phi = atan(-y_in / z_in)*MATH_TRANS;
                }

                if (phi > 0) phi = phi - 180;

                theta_3 = asin(right_all / sqrt_z_y)*MATH_TRANS - phi;
                if(theta_3<0)
                {
                        theta_3 = 0;
                }

                // Calculate value of theta 2
                theta_2 = asin((z + MATH_L4*sin(theta_3 / MATH_TRANS) - MATH_L1) / MATH_L3)*MATH_TRANS;
        }
        else
        {
                // Calculate value of theta 1

                theta_1 = atan(y / x)*MATH_TRANS;

                if (y / x > 0) {
                        theta_1 = theta_1;
                }
                if (y / x < 0) {
                        theta_1 = theta_1 + 180;
                }
                if (y == 0) {
                        if (x > 0) theta_1 = 180;
                        else theta_1 = 0;
                }

                // Calculate value of theta 3

                x_in = (-x / cos(theta_1 / MATH_TRANS) - MATH_L2) / MATH_L3;

                if (z_in == 0) { phi = 90; }

                else{ phi = atan(-x_in / z_in)*MATH_TRANS; }

                if (phi > 0) {phi = phi - 180; }

                sqrt_z_x = sqrt(z_in*z_in + x_in*x_in);

                right_all_2 = -1 * (z_in*z_in + x_in*x_in + MATH_L43*MATH_L43 - 1) / (2 * MATH_L43);
                theta_3 = asin(right_all_2 / sqrt_z_x)*MATH_TRANS;
                theta_3 = theta_3 - phi;

                if (theta_1 <0 ) {
                        theta_1 = 0;
                }

                // Calculate value of theta 2
                theta_2 = asin(z_in + MATH_L43*sin(abs(theta_3 / MATH_TRANS)))*MATH_TRANS;
        }

        theta_1 = abs(theta_1);
        theta_2 = abs(theta_2);

        if (theta_3 < 0 ) {}
        else{
                if ((calYonly(theta_1,theta_2, theta_3)>y+0.1)||(calYonly(theta_1,theta_2, theta_3)<y-0.1))
                {
                        theta_2 = 180 - theta_2;
                }
        }

        if(isnan(theta_1)||isinf(theta_1))
        {theta_1 = uarm.readAngle(SERVO_ROT_NUM); }
        if(isnan(theta_2)||isinf(theta_2))
        {theta_2 = uarm.readAngle(SERVO_LEFT_NUM); }
        if(isnan(theta_3)||isinf(theta_3)||(theta_3<0))
        {theta_3 = uarm.readAngle(SERVO_RIGHT_NUM); }
}

/** This is an old control method to uArm.
** Using uarm's Stretch and height
** Stretch from 0 to 195
** Height from -180 to 150
**/
void uArmClass::writeStretch(double armStretch, double armHeight){
        if(EEPROM.read(CALIBRATION_STRETCH_FLAG) != CONFIRM_FLAG) {
                alert(3, 200, 200);
                return;
        }
        double offsetL = 0;
        double offsetR = 0;

        EEPROM.get(OFFSET_STRETCH_START_ADDRESS, offsetL);
        EEPROM.get(OFFSET_STRETCH_START_ADDRESS + 4, offsetR);
        armStretch = constrain(armStretch, ARM_STRETCH_MIN, ARM_STRETCH_MAX) + 68;
        armHeight  = constrain(armHeight, ARM_HEIGHT_MIN, ARM_HEIGHT_MAX);
        double xx = armStretch*armStretch + armHeight*armHeight;
        double xxx = ARM_B2 - ARM_A2 + xx;
        double angleB = acos((armStretch*xxx+armHeight*sqrt(4.0*ARM_B2*xx-xxx*xxx))/(xx*2.0*ARM_B))* RAD_TO_DEG;
        double yyy = ARM_A2-ARM_B2+xx;
        double angleA =acos((armStretch*yyy-armHeight*sqrt(4.0*ARM_A2*xx-yyy*yyy))/(xx*2.0*ARM_A))* RAD_TO_DEG;
        int angleR =(int)(angleB + offsetR - 4);//int angleR =angleB + 40 + offsetR;
        int angleL =(int)(angleA + offsetL + 16);//int angleL =25 + angleA + offsetL;
        angleL = constrain(angleL, 5 + offsetL, 145 + offsetL);
        writeLeftRightServoAngle(angleL,angleR,true);
}

/** Calculate the X Y Z by given theta_1, theta_2, theta_3
**
**/
void uArmClass::calXYZ(double theta_1, double theta_2, double theta_3)
{
        double l5 = (MATH_L2 + MATH_L3*cos(theta_2 / MATH_TRANS) + MATH_L4*cos(theta_3 / MATH_TRANS));

        g_cal_x = -cos(abs(theta_1 / MATH_TRANS))*l5;
        g_cal_y = -sin(abs(theta_1 / MATH_TRANS))*l5;
        g_cal_z = MATH_L1 + MATH_L3*sin(abs(theta_2 / MATH_TRANS)) - MATH_L4*sin(abs(theta_3 / MATH_TRANS));
}

/** Overload calXYZ()
**/
void uArmClass::calXYZ()
{
        calXYZ(
                uarm.analogToAngle(analogRead(SERVO_ROT_ANALOG_PIN),SERVO_ROT_NUM,false),
                uarm.analogToAngle(analogRead(SERVO_LEFT_ANALOG_PIN),SERVO_LEFT_NUM,false),
                uarm.analogToAngle(analogRead(SERVO_RIGHT_ANALOG_PIN),SERVO_RIGHT_NUM,false));
}

/** Action Control: Genernate the position array
**/
    void uArmClass::interpolate(double start_val, double end_val, double *interp_vals, byte ease_type) {
        double delta = end_val - start_val;
        for (byte f = 0; f < INTERP_INTVLS; f++) {
                switch (ease_type) {
                case INTERP_LINEAR:
                *(interp_vals+f) = delta * f / INTERP_INTVLS + start_val;
                        break;
                case INTERP_EASE_INOUT:
                {
                        float t = f / (INTERP_INTVLS / 2.0);
                        if (t < 1) {
                        *(interp_vals+f) = delta / 2 * t * t + start_val;
                        } else {
                                t--;
                        *(interp_vals+f)= -delta / 2 * (t * (t - 2) - 1) + start_val;
                        }
                }
                break;
                case INTERP_EASE_IN:
                {
                        float t = (float)f / INTERP_INTVLS;
                    *(interp_vals+f) = delta * t * t + start_val;
                }
                break;
                case INTERP_EASE_OUT:
                {
                    float t = (float)f / INTERP_INTVLS;
                    *(interp_vals+f) = -delta * t * (t - 2) + start_val;
                }
                break;
                case INTERP_EASE_INOUT_CUBIC: // this is a compact version of Joey's original cubic ease-in/out
                {
                        float t = (float)f / INTERP_INTVLS;
                    *(interp_vals+f) = start_val + (3 * delta) * (t * t) + (-2 * delta) * (t * t * t);
                }
                break;
                }
        }
}

int uArmClass::moveToOpts(double x, double y, double z, double hand_angle, byte relative_flags, double time, byte path_type, byte ease_type) {
        float limit = sqrt((x*x + y*y));
        if (limit > 32)
        {
            float k = 32/limit;
            x = x * k;
            y = y * k;
        }
        attachAll();

        // find current position using cached servo values
        double current_x;
        double current_y;
        double current_z;
        getCalXYZ(cur_rot, cur_left, cur_right, current_x, current_y, current_z);


        // deal with relative xyz positioning
        byte posn_relative = (relative_flags & F_POSN_RELATIVE) ? 1 : 0;
        x = current_x * posn_relative + x;
        y = current_y * posn_relative + y;
        z = current_z * posn_relative + z;

        // find target angles
        double tgt_rot;
        double tgt_left;
        double tgt_right;
        calAngles(x, y, z, tgt_rot, tgt_left, tgt_right);

        //calculate the length
        unsigned int delta_rot=abs(tgt_rot-cur_rot);
        unsigned int delta_left=abs(tgt_left-cur_left);
        unsigned int delta_right=abs(tgt_right-cur_right);

        //Serial.println(tgt_rot,DEC);

        INTERP_INTVLS = max(delta_rot,delta_left);
        INTERP_INTVLS = max(INTERP_INTVLS,delta_right);

        //Serial.println(INTERP_INTVLS,DEC);
        INTERP_INTVLS=(INTERP_INTVLS<80)?INTERP_INTVLS:80;

        // deal with relative hand orientation
        if (relative_flags & F_HAND_RELATIVE) {
                hand_angle += cur_hand;             // rotates a relative amount, ignoring base rotation
        } else if (relative_flags & F_HAND_ROT_REL) {
                hand_angle = hand_angle + cur_hand + (tgt_rot - cur_rot); // rotates relative to base servo, 0 value keeps an object aligned through movement
        }


        if (time > 0) {
                if (path_type == PATH_ANGLES) {
                        // we will calculate angle value targets
                        double rot_array[INTERP_INTVLS];
                        double left_array[INTERP_INTVLS];
                        double right_array[INTERP_INTVLS];
                        double hand_array[INTERP_INTVLS];

                        interpolate(cur_rot, tgt_rot, rot_array, ease_type);
                        interpolate(cur_left, tgt_left, left_array, ease_type);
                        interpolate(cur_right, tgt_right, right_array, ease_type);
                        interpolate(cur_hand, hand_angle, hand_array, ease_type);

                        for (byte i = 0; i < INTERP_INTVLS; i++)
                        {

                                writeAngle(rot_array[i], left_array[i], right_array[i], hand_array[i]);
                                //writeServoAngle(SERVO_ROT_NUM, rot_array[i], true);
                                // writeServoAngle(SERVO_LEFT_NUM, left_array[i],true);
                                // writeServoAngle(SERVO_RIGHT_NUM, right_array[i],true);
                                //writeLeftRightServoAngle(left_array[i], right_array[i], true);
                                //writeServoAngle(SERVO_HAND_ROT_NUM, hand_array[i],true);
                                delay(time * 1000 / INTERP_INTVLS);
                        }
                } else if (path_type == PATH_LINEAR) {
                        // we will calculate linear path targets
                        double x_array[INTERP_INTVLS];
                        double y_array[INTERP_INTVLS];
                        double z_array[INTERP_INTVLS];
                        double hand_array[INTERP_INTVLS];

                        interpolate(current_x, x, x_array, ease_type);
                        interpolate(current_y, y, y_array, ease_type);
                        interpolate(current_z, z, z_array, ease_type);
                        interpolate(cur_hand, hand_angle, hand_array, ease_type);

                        for (byte i = 0; i < INTERP_INTVLS; i++)
                        {
                                // double rot;
                                double rot,left, right;
                                calAngles(x_array[i], y_array[i], z_array[i], rot, left, right);
                                // Serial.println(rot);
                                // Serial.println(left);
                                // Serial.println(right);
                                // Serial.println();
                                //writeServoAngle(SERVO_ROT_NUM, rot,true);
                                // writeServoAngle(SERVO_LEFT_NUM, tgt_left,true);
                                // writeServoAngle(SERVO_RIGHT_NUM, tgt_right,true);
                                //writeLeftRightServoAngle(left, right, true);
                                // if(enable_hand)
                                //writeServoAngle(SERVO_HAND_ROT_NUM, hand_array[i], true);
                                writeAngle(rot, left, right, hand_array[i]);
                                delay(time * 1000 / INTERP_INTVLS);
                        }
                }
        }

        // set final target position at end of interpolation or "atOnce"
        //writeServoAngle(SERVO_ROT_NUM, tgt_rot, true);
        // writeServoAngle(SERVO_LEFT_NUM, tgt_left, true);
        // writeServoAngle(SERVO_RIGHT_NUM, tgt_right, true);
        //writeLeftRightServoAngle(tgt_left, tgt_right, true);
        //writeServoAngle(SERVO_HAND_ROT_NUM, hand_angle, true);
        writeAngle(tgt_rot, tgt_left, tgt_right, hand_angle);
}

double uArmClass::calYonly(double theta_1, double theta_2, double theta_3)
{
        double l5_2 = (MATH_L2 + MATH_L3*cos(theta_2 / MATH_TRANS) + MATH_L4*cos(theta_3 / MATH_TRANS));

        return -sin(abs(theta_1 / MATH_TRANS))*l5_2;
}

/**
   Control the Gripper Catch
 **/
void uArmClass::gripperCatch()
{
        pinMode(GRIPPER, OUTPUT);
        digitalWrite(GRIPPER, LOW); // gripper catch
        g_gripper_reset = true;
}

/**
   Control the Gripper Release
 **/
void uArmClass::gripperRelease()
{
        if(g_gripper_reset)
        {
                pinMode(GRIPPER, OUTPUT);
                digitalWrite(GRIPPER, HIGH); // gripper release
                g_gripper_reset= false;
        }
}

/**
   Turn on the Pump
 **/
void uArmClass::pumpOn()
{

        pinMode(PUMP_EN, OUTPUT);
        pinMode(VALVE_EN, OUTPUT);
        digitalWrite(VALVE_EN, LOW);
        digitalWrite(PUMP_EN, HIGH);
}

/**
   Turn off the Pump
 **/
void uArmClass::pumpOff()
{
        pinMode(PUMP_EN, OUTPUT);
        pinMode(VALVE_EN, OUTPUT);
        digitalWrite(VALVE_EN, HIGH);
        digitalWrite(PUMP_EN, LOW);
        delay(50);
        digitalWrite(VALVE_EN,LOW);
}
