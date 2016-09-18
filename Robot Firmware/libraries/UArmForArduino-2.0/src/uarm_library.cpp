/*!
   \file uarm_library.cpp
   \brief uArm Library for Arduino
   license GNU
   copyright(c) 2016 UFactory Team. All right reserved
   \author Joe Song, Alex Tan and Dave Corboy
   \version MKII: H3-S2.0.9a  uArm Metal: H2-S2.0.9a
   \date 08/30/2016
 */
#include "uarm_library.h"

uArmClass uarm;

String message = "";
uArmClass::uArmClass()
{

}

/*!
   \brief check the arm status
   \return true: free, false: busy
 */
bool uArmClass::available()
{
        if(move_times!=255)
        {
                return false;
        }

        return true;
}

/*!
   \brief process the uarm movement
 */
void uArmClass::arm_process_commands()
{
        //get the uart command
        if(Serial.available())
        {
                message = Serial.readStringUntil(']');
                // message.trim();
                message += ']';
                runCommand(message); // Run the command and send back the response
        }

        //movement function
        if(move_times!=255)
        {

                //if(move_times <= INTERP_INTVLS)--------------------------------------------------------------
                if((millis() - moveStartTime) >= (move_times * microMoveTime))// detect if it's time to move
                {
                        cur_rot = x_array[move_times];
                        cur_left = y_array[move_times];
                        cur_right = z_array[move_times];
                        //add offset
                        y_array[move_times] = y_array[move_times] - LEFT_SERVO_OFFSET; //assembling offset
                        z_array[move_times] = z_array[move_times] - RIGHT_SERVO_OFFSET; //assembling offset
                        x_array[move_times] = x_array[move_times] - ROT_SERVO_OFFSET; //rot offset
                        write_servo_angle(x_array[move_times], y_array[move_times], z_array[move_times]);// let servo run - John Feng

                        //hand rot as hand rot do not have the smooth array
                        if(move_times == (INTERP_INTVLS / 4))
                        {
                                write_servo_angle(SERVO_HAND_ROT_NUM, cur_hand);
                        }

                        move_times++;
                        if(move_times >= INTERP_INTVLS)
                        {
                                move_times = 255;//disable the move
                        }
                }
        }

        //buzzer work------------------------------------------------------------------------------------
        if(buzzerStopTime != 0)
        {
                if(millis() >= buzzerStopTime)
                {
                        noTone(BUZZER);
                        buzzerStopTime = 0;
                }
        }

        //check the button4 status------------------------------------------------------------------------
        if(digitalRead(BTN_D4)==LOW)//check the D4 button
        {
                delay(50);
                //Serial.println("Test: whether get into learning mode");
                if(digitalRead(BTN_D4)==LOW)
                {
                        switch(sys_status)
                        {
                        case NORMAL_MODE:
                        case NORMAL_BT_CONNECTED_MODE:
                                sys_status = LEARNING_MODE;
                                addr = 0;//recording/playing address
                                g_servo_rot.detach();
                                g_servo_left.detach();
                                g_servo_right.detach();
                                g_servo_hand_rot.detach();
                                break;
                        case LEARNING_MODE:
                                //LEARNING_MODE_STOP is just used to notificate record() function to stop, once record() get it then change the sys_status to normal_mode
                                sys_status = LEARNING_MODE_STOP;//do not detec if BT is connected here, will do it seperatly
                                break;
                        default: break;
                        }
                }
                while(digitalRead(BTN_D4)==LOW) ; // make sure button is released
        }

        //check the button7 status-------------------------------------------------------------------------
        if(digitalRead(BTN_D7)==LOW)//check the D7 button
        {
                delay(50);
                if(digitalRead(BTN_D7)==LOW)
                {
                        //Serial.println("Test: whether BTN_D7 useful");
                        switch(sys_status)
                        {
                        case NORMAL_MODE:
                        case NORMAL_BT_CONNECTED_MODE:
                                delay(1000);
                                addr = 0;//recording/playing address
                                if(digitalRead(BTN_D7)==LOW)
                                        sys_status = LOOP_PLAY_MODE;
                                else
                                        sys_status = SINGLE_PLAY_MODE;
                                break;
                        case SINGLE_PLAY_MODE:
                        case LOOP_PLAY_MODE:
                                sys_status = NORMAL_MODE;
                                break;
                        case LEARNING_MODE:
                                break;
                        }
                }
                while(digitalRead(BTN_D7)==LOW) ; // make sure button is released
        }

        //sys led function detec every 0.05s-----------------------------------------------------------------
        if(time_50ms != millis()%50)
        {
                time_50ms = millis()%50;
                if(time_50ms == 0)
                {
                        //learning&playing mode function****************
                        switch(sys_status)//every 0.125s per point
                        {
                        case SINGLE_PLAY_MODE:
                                if(play() == false)
                                {
                                        sys_status = NORMAL_MODE;
                                        addr = 0;
                                }
                                break;
                        case LOOP_PLAY_MODE:
                                //Serial.println("Test: whether loop play mode");
                                if(play() == false)
                                {
                                        //sys_status = LOOP_PLAY_MODE;
                                        addr = 0;

                                }
                                break;
                        case LEARNING_MODE:
                        case LEARNING_MODE_STOP:
                                if(record() == false)
                                {
                                        sys_status = NORMAL_MODE;
                                        addr = 0;
                                        attach_servo(SERVO_ROT_NUM);
                                        attach_servo(SERVO_LEFT_NUM);
                                        attach_servo(SERVO_RIGHT_NUM);
                                        attach_servo(SERVO_HAND_ROT_NUM);
                                        // attach_all();

                                }
                                break;
                        default: break;
                        }
                        //learning mode function end*******************
                }
        }
//#endif

}

/*!
   \brief uArm initial setup
 */
void uArmClass::arm_setup()
{
        // set the initial point - John Feng
        if (EEPROM.read(CALIBRATION_FLAG) != CONFIRM_FLAG)
        {
                tone(BUZZER, 1000);
                delay(1000);
                noTone(BUZZER);
        }
        pinMode(BTN_D4,INPUT_PULLUP);        //special mode for calibration
        pinMode(BUZZER,OUTPUT);
        pinMode(LIMIT_SW, INPUT_PULLUP);
        pinMode(BTN_D7, INPUT_PULLUP);
        pinMode(PUMP_EN,OUTPUT);
        pinMode(VALVE_EN,OUTPUT);
        pinMode(GRIPPER,OUTPUT);
        LEFT_SERVO_OFFSET = read_servo_offset(SERVO_LEFT_NUM);
        RIGHT_SERVO_OFFSET = read_servo_offset(SERVO_RIGHT_NUM);
        ROT_SERVO_OFFSET = read_servo_offset(SERVO_ROT_NUM);
        HAND_ROT_SERVO_OFFSET = read_servo_offset(SERVO_HAND_ROT_NUM);
        // attach_all();
        // move_to(10,100,150,false);
        delay(1000);
        attach_servo(SERVO_ROT_NUM);
        attach_servo(SERVO_LEFT_NUM);
        attach_servo(SERVO_RIGHT_NUM);
        attach_servo(SERVO_HAND_ROT_NUM);

}

/*!
   \brief Write 3 Servo Angles, servo_rot, servo_left, servo_right
   \param servo_rot_angle SERVO_ROT_NUM
   \param servo_left_angle SERVO_LEFT_NUM
   \param servo_right_angle SERVO_RIGHT_NUM
   \return SUCCESS, FAILED
 */
int uArmClass::write_servo_angle(double servo_rot_angle, double servo_left_angle, double servo_right_angle)
{
        write_servo_angle(SERVO_ROT_NUM,servo_rot_angle);
        write_servo_angle(SERVO_LEFT_NUM,servo_left_angle);
        write_servo_angle(SERVO_RIGHT_NUM,servo_right_angle);
        // refresh logical servo angle cache
        //cur_rot = servo_rot_angle;
        //cur_left = servo_left_angle;
        //cur_right = servo_right_angle;
}

/*!
   \brief Write the angle to Servo
   \param servo_number SERVO_ROT_NUM, SERVO_LEFT_NUM, SERVO_RIGHT_NUM, SERVO_HAND_ROT_NUM
   \param servo_angle Servo target angle, 0.00 - 180.00
 */
void uArmClass::write_servo_angle(byte servo_number, double servo_angle)
{
        write_servo_angle(servo_number,servo_angle,false);
}

/*!
   \brief Write the angle to one Servo
   \param servo_number SERVO_ROT_NUM, SERVO_LEFT_NUM, SERVO_RIGHT_NUM, SERVO_HAND_ROT_NUM
   \param servo_angle Servo target angle, 0.00 - 180.00
   \param writeWithoffset True: with Offset, False: without Offset
 */
void uArmClass::write_servo_angle(byte servo_number, double servo_angle, boolean writeWithoffset)
{
        // attach_servo(servo_number);
        servo_angle = writeWithoffset ? (servo_angle + read_servo_offset(servo_number)) : servo_angle;
        // servo_angle = constrain(servo_angle,0.0,180.0);
        switch(servo_number)
        {
        case SERVO_ROT_NUM:       g_servo_rot.write(servo_angle);
                // cur_rot = servo_angle - ROT_SERVO_OFFSET;
                break;
        case SERVO_LEFT_NUM:      g_servo_left.write(servo_angle);
                // cur_left = servo_angle - LEFT_SERVO_OFFSET;
                break;
        case SERVO_RIGHT_NUM:     g_servo_right.write(servo_angle);
                // cur_right = servo_angle - RIGHT_SERVO_OFFSET;
                break;
        case SERVO_HAND_ROT_NUM:  g_servo_hand_rot.write(servo_angle);
                // cur_hand = servo_angle - HAND_ROT_SERVO_OFFSET;
                break;
        default:                  break;
        }
}

/*!
   \brief Attach Servo, if servo has not been attached, attach the servo, and read the current Angle
   \param servo_number SERVO_ROT_NUM, SERVO_LEFT_NUM, SERVO_RIGHT_NUM, SERVO_HAND_ROT_NUM
 */
void uArmClass::attach_servo(byte servo_number)
{
        if (EEPROM.read(CALIBRATION_LINEAR_FLAG) != CONFIRM_FLAG)
        {
                return;
        }
        switch(servo_number) {
        case SERVO_ROT_NUM:
                if (analogRead(SERVO_ROT_ANALOG_PIN) > 50) { // Servo Protection
                        g_servo_rot.attach(SERVO_ROT_PIN);
                        read_servo_angle(SERVO_ROT_NUM);
                        g_servo_rot.write(cur_rot);
                }
                break;
        case SERVO_LEFT_NUM:
                if (analogRead(SERVO_LEFT_ANALOG_PIN) > 50) { // Servo Protection
                        g_servo_left.attach(SERVO_LEFT_PIN);
                        read_servo_angle(SERVO_LEFT_NUM);
                        g_servo_left.write(cur_left);
                }
                break;
        case SERVO_RIGHT_NUM:
                if (analogRead(SERVO_RIGHT_ANALOG_PIN) > 50) { // Servo Protection
                        g_servo_right.attach(SERVO_RIGHT_PIN);
                        read_servo_angle(SERVO_RIGHT_NUM);
                        g_servo_right.write(cur_right);
                }
                break;
        case SERVO_HAND_ROT_NUM:
                if (analogRead(SERVO_HAND_ROT_ANALOG_PIN) > 100) { // Servo Protection
                        g_servo_hand_rot.attach(SERVO_HAND_ROT_PIN,600,2400);
                        read_servo_angle(SERVO_HAND_ROT_NUM);
                        g_servo_hand_rot.write(cur_hand);
                }
                break;
        }
}

/*!
   \brief Detach Servo by Servo Number, SERVO_ROT_NUM, SERVO_LEFT_NUM, SERVO_RIGHT_NUM, SERVO_HAND_ROT_NUM
   \param servo_number SERVO_ROT_NUM, SERVO_LEFT_NUM, SERVO_RIGHT_NUM, SERVO_HAND_ROT_NUM
 */
void uArmClass::detach_servo(byte servo_number)
{
        switch(servo_number) {
        case SERVO_ROT_NUM:
                g_servo_rot.detach();
                break;
        case SERVO_LEFT_NUM:
                g_servo_left.detach();
                break;
        case SERVO_RIGHT_NUM:
                g_servo_right.detach();
                break;
        case SERVO_HAND_ROT_NUM:
                g_servo_hand_rot.detach();
                break;
        }
}

/*!
   \brief Convert the Analog to Servo Angle, by this formatter, angle = intercept + slope * analog
   \param input_analog Analog Value
   \param servo_num SERVO_ROT_NUM, SERVO_LEFT_NUM, SERVO_RIGHT_NUM, SERVO_HAND_ROT_NUM
   \param withOffset true, false
   \return Servo Angle
 */
double uArmClass::analog_to_angle(int input_analog, byte servo_num)
{
        double intercept = 0.0f;
        double slope = 0.0f;
        read_linear_offset(servo_num, intercept, slope);
        double angle = intercept + slope*input_analog;
        // Serial.println(angle);
        return angle;
}

/*!
   \brief Calculate the angles from given coordinate x, y, z to theta_1, theta_2, theta_3
   \param x X axis
   \param y Y axis
   \param z Z axis
   \param theta_1 SERVO_ROT_NUM servo angles
   \param theta_2 SERVO_LEFT_NUM servo angles
   \param theta_3 SERVO_RIGHT_NUM servo angles
   \return IN_RANGE, OUT_OF_RANGE
 */
unsigned char uArmClass::coordinate_to_angle(double x, double y, double z, double *theta_1, double *theta_2, double *theta_3, bool data_constrain)//theta_1:rotation angle   theta_2:the angle of lower arm and horizon   theta_3:the angle of upper arm and horizon
{
        double x_in = 0.0;
        double z_in = 0.0;
        double right_all = 0.0;
        double sqrt_z_x = 0.0;
        double phi = 0.0;
        x = constrain(x,-3276,3276);
        y = constrain(y,-3276,3276);
        z = constrain(z,-3276,3276);
        x = (double)((int)(x*10)/10.0);
        y = (double)((int)(y*10)/10.0);
        z = (double)((int)(z*10)/10.0);

        z_in = (z - MATH_L1) / MATH_LOWER_ARM;
        if(move_to_the_closest_point == false)//if need the move to closest point we have to jump over the return function
        {
                //check the range of x
                if(y<0)
                {
                        return OUT_OF_RANGE_NO_SOLUTION;
                }
        }
        // Calculate value of theta 1: the rotation angle
        if(x==0)
        {
                (*theta_1) = 90;
        }
        else
        {
                if (x > 0)
                {
                        *theta_1 = atan(y / x)*MATH_TRANS;//angle tranfer 0-180 CCW
                }
                if (x < 0)
                {
                        (*theta_1) = 180 + atan(y / x)*MATH_TRANS;//angle tranfer  0-180 CCW
                }
        }
        // Calculate value of theta 3
        if((*theta_1)!=90)//x_in is the stretch
        {
                x_in = (x / cos((*theta_1) / MATH_TRANS) - MATH_L2 - MATH_FRONT_HEADER) / MATH_LOWER_ARM;
        }
        else
        {
                x_in = (y - MATH_L2 - MATH_FRONT_HEADER) / MATH_LOWER_ARM;
        }

        /*if(write_stretch_height_rot(x_in,z_in,theta_1,theta_2,theta_3)==IN_RANGE)
           {
           return IN_RANGE;
           }
           else
           {
           return OUT_OF_RANGE;
           }*/
        phi = atan(z_in / x_in)*MATH_TRANS;//phi is the angle of line (from joint 2 to joint 4) with the horizon

        sqrt_z_x = sqrt(z_in*z_in + x_in*x_in);

        right_all = (sqrt_z_x*sqrt_z_x + MATH_UPPER_LOWER * MATH_UPPER_LOWER  - 1) / (2 * MATH_UPPER_LOWER  * sqrt_z_x);//cosin law
        (*theta_3) = acos(right_all)*MATH_TRANS;//cosin law

        // Calculate value of theta 2
        right_all = (sqrt_z_x*sqrt_z_x + 1 - MATH_UPPER_LOWER * MATH_UPPER_LOWER ) / (2 * sqrt_z_x);//cosin law
        (*theta_2) = acos(right_all)*MATH_TRANS;//cosin law

        (*theta_2) = (*theta_2) + phi;
        (*theta_3) = (*theta_3) - phi;
        //determine if the angle can be reached
        return limit_range(theta_1, theta_2, theta_3, data_constrain);
}

unsigned char uArmClass::limit_range(double *rot, double *left, double *right, bool data_constrain)
{
        //determine if the angle can be reached
        if(isnan(*rot)||isnan(*right)||isnan(*left))
        {
                return OUT_OF_RANGE_NO_SOLUTION;
        }
        if(((*left - LEFT_SERVO_OFFSET) < LOWER_ARM_MIN_ANGLE)||((*left - LEFT_SERVO_OFFSET) > LOWER_ARM_MAX_ANGLE))//check the right in range
        {
                return OUT_OF_RANGE;
        }
        if(((*right - RIGHT_SERVO_OFFSET) < UPPER_ARM_MIN_ANGLE)||((*right - RIGHT_SERVO_OFFSET) > UPPER_ARM_MAX_ANGLE))//check the left in range
        {
                return OUT_OF_RANGE;
        }
        if(((180 - *left - *right)>LOWER_UPPER_MAX_ANGLE)||((180 - *left - *right)<LOWER_UPPER_MIN_ANGLE))//check the angle of upper arm and lowe arm in range
        {
                return OUT_OF_RANGE;
        }

        return IN_RANGE;
}

//#ifndef PRODUCT_MKII
/*!
   \brief Calculate X,Y,Z to g_current_x,g_current_y,g_current_z
 */
/*
   void uArmClass::get_current_xyz()
   {
       double theta_1 = analog_to_angle(analogRead(SERVO_ROT_ANALOG_PIN),SERVO_ROT_NUM, false);
       double theta_2 = analog_to_angle(analogRead(SERVO_LEFT_ANALOG_PIN),SERVO_LEFT_NUM, false);
       double theta_3 = analog_to_angle(analogRead(SERVO_RIGHT_ANALOG_PIN),SERVO_RIGHT_NUM, false);
       get_current_xyz(theta_1, theta_2, theta_3);
   }

   /*!
   \brief Calculate X,Y,Z to g_current_x,g_current_y,g_current_z
   \param theta_1 Rot Servo Angle
   \param theta_2 Left Servo Angle
   \param theta_3 Right Servo Angle
 */
/*
   void uArmClass::get_current_xyz(double theta_1, double theta_2, double theta_3)
   {
       double l5 = (MATH_L2 + MATH_L3*cos(theta_2 / MATH_TRANS) + MATH_L4*cos(theta_3 / MATH_TRANS));

       g_current_x = -cos(abs(theta_1 / MATH_TRANS))*l5;
       g_current_y = -sin(abs(theta_1 / MATH_TRANS))*l5;
       g_current_z = MATH_L1 + MATH_L3*sin(abs(theta_2 / MATH_TRANS)) - MATH_L4*sin(abs(theta_3 / MATH_TRANS));
   }
 #endif
 */
/*!
   \brief get the current rot left right angles
 */
void uArmClass::get_current_rotleftright()
{
        read_servo_angle(SERVO_ROT_NUM);
        read_servo_angle(SERVO_LEFT_NUM);
        read_servo_angle(SERVO_RIGHT_NUM);
        read_servo_angle(SERVO_HAND_ROT_NUM);
}

void uArmClass::read_servo_angle(byte servo_number, boolean with_offset)
{
        // double angle = 0;
        // unsigned int address;
        double *data;

        switch(servo_number) {
        case SERVO_ROT_NUM:
                // address = ROT_SERVO_ADDRESS;
                data = &cur_rot;
                break;
        case SERVO_LEFT_NUM:
                // address = LEFT_SERVO_ADDRESS;
                data = &cur_left;
                break;
        case SERVO_RIGHT_NUM:
                // address = RIGHT_SERVO_ADDRESS;
                data = &cur_right;
                break;
        case SERVO_HAND_ROT_NUM:
                cur_hand = map(analogRead(SERVO_HAND_ROT_ANALOG_PIN), SERVO_9G_MIN, SERVO_9G_MAX, 0, 180); //g_servo_hand_rot.read();  // SERVO_HAND_ROT_ANALOG_PIN),SERVO_HAND_ROT_NUM);
                return;
                break;
        }

        unsigned int dat[8], temp;
        unsigned char i=0,j=0;
        for(i=0; i<8; i++)
        {
                switch(servo_number)
                {
                case SERVO_ROT_NUM: dat[i] = analogRead(SERVO_ROT_ANALOG_PIN); break;
                case SERVO_LEFT_NUM: dat[i] = analogRead(SERVO_LEFT_ANALOG_PIN); break;
                case SERVO_RIGHT_NUM: dat[i] = analogRead(SERVO_RIGHT_ANALOG_PIN); break;
                default: break;
                }
        }
        for(i=0; i<8; i++) {//BULB to get the most accuracy data
                for(j=0; i+j<7; j++) {
                        if(dat[j]>dat[j+1]) {
                                temp = dat[j];
                                dat[j] = dat[j+1];
                                dat[j+1] = temp;
                        }
                }
        }
        switch(servo_number)
        {
        case SERVO_ROT_NUM: (*data) = analog_to_angle((dat[2]+dat[3]+dat[4]+dat[5])/4,SERVO_ROT_NUM); break;
        case SERVO_LEFT_NUM: (*data) = analog_to_angle((dat[2]+dat[3]+dat[4]+dat[5])/4,SERVO_LEFT_NUM); break;
        case SERVO_RIGHT_NUM: (*data) = analog_to_angle((dat[2]+dat[3]+dat[4]+dat[5])/4,SERVO_RIGHT_NUM); break;
        default: break;
        }
        if (with_offset == true)
        {
                switch(servo_number) {
                case SERVO_ROT_NUM:       cur_rot   -= ROT_SERVO_OFFSET;      break;
                case SERVO_LEFT_NUM:      cur_left  -= LEFT_SERVO_OFFSET;     break;
                case SERVO_RIGHT_NUM:     cur_right -= RIGHT_SERVO_OFFSET;    break;
                case SERVO_HAND_ROT_NUM:  cur_hand  -= HAND_ROT_SERVO_OFFSET; break;

                }
        }
}

/*!
   \brief read Angle by servo_num without offset
   \param servo_num SERVO_ROT_NUM, SERVO_LEFT_NUM, SERVO_RIGHT_NUM, SERVO_HAND_ROT_NUM
   \return Return servo_num Angle
 */
// void uArmClass::read_servo_angle(byte servo_num)
// {
//         read_servo_angle(servo_num, true);
// }

/*!
   \brief read Angle by servo_num
   \param servo_num SERVO_ROT_NUM, SERVO_LEFT_NUM, SERVO_RIGHT_NUM, SERVO_HAND_ROT_NUM
   \param withOffset true, false
   \return Return servo_num Angle
 */
// double uArmClass::read_servo_angle(byte servo_num, boolean withOffset)
// {
//         double angle = 0;
//         for (byte i = 0; i < 5; i++) {
//                 switch (servo_num)
//                 {
//                 case SERVO_ROT_NUM:
//                         angle += analog_to_angle(analogRead(SERVO_ROT_ANALOG_PIN),SERVO_ROT_NUM,withOffset);
//                         break;
//
//                 case SERVO_LEFT_NUM:
//                         angle += analog_to_angle(analogRead(SERVO_LEFT_ANALOG_PIN),SERVO_LEFT_NUM,withOffset);
//                         break;
//
//                 case SERVO_RIGHT_NUM:
//                         angle += analog_to_angle(analogRead(SERVO_RIGHT_ANALOG_PIN),SERVO_RIGHT_NUM,withOffset);
//                         break;
//
//                 case SERVO_HAND_ROT_NUM:
//                         angle += analog_to_angle(analogRead(SERVO_HAND_ROT_ANALOG_PIN),SERVO_HAND_ROT_NUM,withOffset);
//                         break;
//
//                 default:
//                         break;
//
//                 }
//                 delay(10);
//         }
//         return angle/5;
// }

/*!
   \brief read Linear Offset from EEPROM, From LINEAR_INTERCEPT_START_ADDRESS & LINEAR_SLOPE_START_ADDRESS, each offset occupy 4 bytes in rom
   \param servo_num SERVO_ROT_NUM, SERVO_LEFT_NUM, SERVO_RIGHT_NUM, SERVO_HAND_ROT_NUM
   \param intercept_val get intercept_val
   \param slope_val get slope_val
 */
void uArmClass::read_linear_offset(byte servo_num, double& intercept_val, double& slope_val){
        EEPROM.get(LINEAR_INTERCEPT_START_ADDRESS + servo_num * sizeof(intercept_val), intercept_val);
        EEPROM.get(LINEAR_SLOPE_START_ADDRESS + servo_num * sizeof(slope_val), slope_val);
}

/*!
   \brief Read Servo Offset from EEPROM. From OFFSET_START_ADDRESS, each offset occupy 4 bytes in rom
   \param servo_num SERVO_ROT_NUM, SERVO_LEFT_NUM, SERVO_RIGHT_NUM, SERVO_HAND_ROT_NUM
   \return Return servo offset
 */
double uArmClass::read_servo_offset(byte servo_num)
{
        double manual_servo_offset = 0.0f;
        EEPROM.get(MANUAL_OFFSET_ADDRESS + servo_num * sizeof(manual_servo_offset), manual_servo_offset);
        return manual_servo_offset;
}

/*!
   \brief Use BUZZER for Alert
   \param times Beep Times
   \param runTime How Long from High to Low
   \param stopTime How Long from Low to High
 */
// void uArmClass::alert(byte times, int runTime, int stopTime)
// {
//         for(int ct=0; ct < times; ct++)
//         {
//                 delay(stopTime);
//                 digitalWrite(BUZZER, HIGH);
//                 delay(runTime);
//                 digitalWrite(BUZZER, LOW);
//         }
// }

/*!
   \brief Calculate X,Y,Z to g_current_x,g_current_y,g_current_z
   \param cur_rot the address of value we want to caculate
   \param cur_left the address of value we want to caculate
   \param cur_right the address of value we want to caculate
   \param g_current_x the address of value we want to caculate
   \param g_current_y the address of value we want to caculate
   \param g_current_z the address of value we want to caculate
   \param for_movement the flage to detect if we should get the real current angle of the uarm
 */
unsigned char uArmClass::get_current_xyz(double *cur_rot, double *cur_left, double *cur_right, double *g_current_x, double *g_current_y, double *g_current_z, bool for_movement )
{
        if(for_movement==true) {
                get_current_rotleftright();
        }
        double stretch = MATH_LOWER_ARM * cos((*cur_left) / MATH_TRANS) + MATH_UPPER_ARM * cos((*cur_right) / MATH_TRANS) + MATH_L2;
        double height = MATH_LOWER_ARM * sin((*cur_left) / MATH_TRANS) - MATH_UPPER_ARM * sin((*cur_right) / MATH_TRANS) + MATH_L1;
        *g_current_x = stretch * cos((*cur_rot) / MATH_TRANS);
        *g_current_y = stretch * sin((*cur_rot) / MATH_TRANS);
        *g_current_z = height;

        mechanical_valid_coordinates = true;
        //used in FK
        if(for_movement == false)
        {

        }
        return IN_RANGE;
}
/*!
   \brief Genernate the position array
   \param start_val Start Position
   \param end_val End Position
   \param interp_vals interpolation array
   \param ease_type INTERP_EASE_INOUT_CUBIC, INTERP_LINEAR, INTERP_EASE_INOUT, INTERP_EASE_IN, INTERP_EASE_OUT
 */
void uArmClass::interpolate(double start_val, double end_val, double *interp_vals, byte ease_type)
{

        start_val = start_val/10.0;
        end_val = end_val/10.0;

        double delta = end_val - start_val;
        for (byte f = 1; f <= INTERP_INTVLS; f++)
        {
                float t = (float)f / INTERP_INTVLS;
                //*(interp_vals+f) = 10.0*(start_val + (3 * delta) * (t * t) + (-2 * delta) * (t * t * t));
                *(interp_vals+f-1) = 10.0 * (start_val + t* t * delta * (3 + (-2) * t));
        }
}

/*!
   \brief Move To, Action Control Core Function
   \param x X Axis Value if polar is true then x is the stretch
   \param y Y Axis Value if polar is true then y is the rot angle
   \param z Z Axis Value if polar is true then z is the height
   \param hand_angle Hand Axis
   \param relative_flags ABSOLUTE, RELATIVE
   \param times speed
   \param ease_type interpolate type
   \param enable_hand Enable Hand Axis
   \param polar false: xyz coordinates, true: stretch&height&rot
 */

unsigned char uArmClass::move_to(double x, double y, double z, double hand_angle, byte relative_flags, double times, byte ease_type, boolean enable_hand, bool polar) {
        if (EEPROM.read(CALIBRATION_LINEAR_FLAG) != CONFIRM_FLAG)
        {
                tone(BUZZER, 10000);
                delay(50);
                noTone(BUZZER);
                return FAILED;
        }
        if(polar == true)//change the stretch rot and height to xyz coordinates
        {
                double stretch = x;
                //Z and height is the same
                //transfer stretch to xy
                x = stretch * cos(y / MATH_TRANS);
                y = stretch * sin(y / MATH_TRANS);
        }
        // get current angles of servos

        // find current position using cached servo values
        //double current_x;
        //double current_y;
        //double current_z;
        //angle_to_coordinate(cur_rot, cur_left, cur_right, current_x, current_y, current_z);

        // deal with relative xyz positioning
        if(relative_flags == RELATIVE)
        {
                x = g_current_x + x;
                y = g_current_x + y;
                z = g_current_z + z;
                //hand_angle = current_hand + hand_angle;
        }

        // find target angles
        double tgt_rot;
        double tgt_left;
        double tgt_right;

        unsigned char destination_status = 0;
        //  detect if the xyz coordinate are in the range
        destination_status = coordinate_to_angle(x, y, z, &tgt_rot, &tgt_left, &tgt_right, false);
        if(destination_status != IN_RANGE)
        {
                //check if need to check the out_of_range
                if(move_to_the_closest_point==false) {
                        return OUT_OF_RANGE;
                }
        }
        if(destination_status != OUT_OF_RANGE_NO_SOLUTION)
        {
                //calculate the length and use the longest to determine the numbers of interpolation
                unsigned int delta_rot=abs(tgt_rot-cur_rot);
                unsigned int delta_left=abs(tgt_left-cur_left);
                unsigned int delta_right=abs(tgt_right-cur_right);

                INTERP_INTVLS = max(delta_rot,delta_left);
                INTERP_INTVLS = max(INTERP_INTVLS,delta_right);

                INTERP_INTVLS = (INTERP_INTVLS<60) ? INTERP_INTVLS : 60;
                //INTERP_INTVLS =1;// INTERP_INTVLS * (10 / times);// speed determine the number of interpolation
                times = constrain(times, 100, 1000);
                hand_speed = times;//set the had rot speed

                interpolate(g_current_x, x, x_array, ease_type);// /10 means to make sure the t*t*t is still in the range
                interpolate(g_current_y, y, y_array, ease_type);
                interpolate(g_current_z, z, z_array, ease_type);


                double rot, left, right;
                double x_backup, y_backup, z_backup;
                unsigned char i, status;
                for (i = 0; i < INTERP_INTVLS; i++)//planning the line trajectory
                {
                        //check if all the data in range and give the tlr angles to the xyz array
                        status = coordinate_to_angle(x_array[i], y_array[i], z_array[i], &rot, &left, &right, true);
                        if(status != IN_RANGE)
                        {
                                i = 0;
                                break;//break the for loop since there are some poisition unreachable, and use point to point method to move
                        }
                        else
                        {
                                //change to the rot/left/right angles
                                x_array[i] = rot;
                                y_array[i] = left;
                                z_array[i] = right;
                        }
                }

                for (; i < INTERP_INTVLS; i++)//planning the p2p trajectory
                {
                        if(i == 0)//do the interpolation in first cycle
                        {
                                interpolate(cur_rot, tgt_rot, x_array, ease_type);
                                interpolate(cur_left, tgt_left, y_array, ease_type);
                                interpolate(cur_right, tgt_right, z_array, ease_type);
                        }
                        status = limit_range(&x_array[i], &y_array[i], &z_array[i], true);
                        if((status != IN_RANGE)&&(mechanical_valid_coordinates == false))
                        {
                                //if out of range then break and adjust the value of INTERP_INTVLS
                                INTERP_INTVLS = i;
                                break;
                        }
                }
                //caculate the distance from the destination
                double distance = sqrt((x-g_current_x) * (x-g_current_x) + (y-g_current_y) * (y-g_current_y) + (z-g_current_z) * (z-g_current_z));
                moveStartTime = millis();// Speed of the robot in mm/s
                microMoveTime = distance / times * 1000.0 / INTERP_INTVLS;//the time for every step
        }
        else
        {
                INTERP_INTVLS = 0;//no solution no move
        }
        if(INTERP_INTVLS > 0)
        {
                g_current_x = x;
                g_current_y = y;
                g_current_z = z;
                mechanical_valid_coordinates = false;
                move_times = 0;//start the moving
        }
        else
        {
                move_times = 255;
        }

        return IN_RANGE;
}

/*!
   \brief Gripper catch
   \param value true, false
 */
void uArmClass::gripper_catch(bool value)
{
        if(value)
        {
                digitalWrite(GRIPPER, LOW); // gripper and pump catch
        }
        else
        {
                digitalWrite(GRIPPER, HIGH); // gripper and pump off
        }
}
/*!
   \brief Pump catch
   \param value true, false
 */
void uArmClass::pump_catch(bool value)
{
        if(value)
        {
                digitalWrite(PUMP_EN, HIGH); // pump catch
                digitalWrite(VALVE_EN, LOW);
        }
        else
        {
                digitalWrite(PUMP_EN, LOW); // pump catch
                digitalWrite(VALVE_EN, HIGH);
        }
}
/*!
   \brief Get Gripper Status
 */
unsigned char uArmClass::gripper_status()
{
        if(digitalRead(GRIPPER) == HIGH)
        {
                return STOP;
        }
        else
        {
                if(analogRead(GRIPPER_FEEDBACK) > 600)
                {
                        return WORKING;
                }
                else
                {
                        return GRABBING;
                }
        }
}

//*************************************uart communication**************************************//
void uArmClass::runCommand(String cmnd){

        // To save memory, create the "OK" and "]\n" right now, in flash memory
        // //get the first 4 command and compare it below
        String cmd = cmnd.substring(1,5);
        // Serial.println(cmd);
        // cmnd = String(cmnd[1])+String(cmnd[2])+String(cmnd[3])+String(cmnd[4]);
        double values[4];
        bool success;

        // sMov Command----------------------------------------------------------
        //if(cmnd.indexOf(F("sPol"))>=0){
        if(cmd == "sMov") {
                const char parameters[4] = {'X', 'Y', 'Z', 'V'};
                //errorResponse = getValues(cmnd, parameters, 4, values);
                if(getValue(cmnd, parameters, 4, values) == OK) {     //means no err
                        Serial.println(SS);// successful feedback send it immediately
                        //limit the speed
                        move_to_the_closest_point = true;
                        move_to(values[0], values[1], values[2], values[3], false);
                        move_to_the_closest_point = false;
                }

        }else

        //sPolS#H#R#--------------------------------------------------------------
        //if(cmnd.indexOf(F("sPol")) >= 0){
        if(cmd == "sPol") {
                const char parameters[4] = {'S', 'R', 'H', 'V'};
                //errorResponse = getValues(cmnd, parameters, 4, values);
                if(getValue(cmnd, parameters, 4, values) == OK) {
                        Serial.println(SS);// successful feedback send it immediately
                        //limit the speed
                        move_to_the_closest_point = true;
                        move_to(values[0], values[1], values[2], values[3], true);
                        move_to_the_closest_point = false;
                }
        }else

        // sAttachS#----------------------------------------------------------------
        //if(cmnd.indexOf(F("sAtt")) >= 0){
        if(cmd == "sAtt") {
                const char parameters[1] = {'N'};
                //String errorResponse        = getValues(cmnd, parameters, 1, values);
                if(getValue(cmnd, parameters, 1, values) == OK) {
                        Serial.println(SS);// successful feedback send it immediately
                        attach_servo(values[0]);
                        if((g_servo_rot.attached())&&(g_servo_left.attached())&&(g_servo_right.attached()))
                        {
                                //Serial.println("Attached");
                                get_current_xyz(&cur_rot, &cur_left, &cur_right, &g_current_x, &g_current_y, &g_current_z, true);
                        }
                }
        }else

        // sDetachS#----------------------------------------------------------------
        //if(cmnd.indexOf(F("sDet")) >= 0){
        if(cmd == "sDet") {
                const char parameters[1] = {'N'};
                //String errorResponse        = getValues(cmnd, parameters, 1, values);
                if(getValue(cmnd, parameters, 1, values) == OK) {
                        Serial.println(SS);// successful feedback send it immediately
                        detach_servo(values[0]);
                }
        }else
        // sServoN#V#--------------------------------------------------------------
        //if(cmnd.indexOf(F("sSer")) >= 0){
        if(cmd == "sSer") {
                const char parameters[2] = {'N', 'V'};
                if(getValue(cmnd, parameters, 2, values) == OK) {
                        Serial.println(SS);// successful feedback send it immediately
                        // in write_servo_angle function, add offset
                        write_servo_angle(byte(values[0]), values[1], false);
                }
        }
        // sAngN#V#--------------------------------------------------------------
        if(cmd == "sAng") {
                const char parameters[2] = {'N', 'V'};

                if(getValue(cmnd, parameters, 2, values) == OK) {
                        Serial.println(SS);// successful feedback send it immediately
                        // in write_servo_angle function, add offset
                        write_servo_angle(byte(values[0]), values[1], true);
                }
        }else

        //sPumpV#------------------------------------------------------------------
        //if(cmnd.indexOf(F("sPum")) >= 0){
        if(cmd == "sPum") {
                const char parameters[1] = {'V'};
                //String errorResponse        = getValues(cmnd, parameters, 1, values);
                if(getValue(cmnd, parameters, 1, values) == OK) {
                        Serial.println(SS);// successful feedback send it immediately

                        if(values[0] == 0)//off
                        {
                                pump_catch(false);
                        }else//on
                        {
                                pump_catch(true);
                        }
                }
        }else

        //sGripperV#----------------------------------------------------------------
        //if(cmnd.indexOf(F("sGri")) >= 0){
        if(cmd == "sGri") {
                const char parameters[1] = {'V'};
                //String errorResponse        = getValues(cmnd, parameters, 1, values);
                if(getValue(cmnd, parameters, 1, values) == OK) {
                        Serial.println(SS);// successful feedback send it immediately
                        if(values[0]==0)//release
                        {
                                gripper_catch(false);
                        }else//catch
                        {
                                gripper_catch(true);
                        }
                }
        }else

        //sBuzzF#T#-----------------------------------------------------------------
        //if(cmnd.indexOf(F("sBuz")) >= 0){
        if(cmd == "sBuz") {
                const char parameters[2] = {'F','T'};
                //String errorResponse        = getValues(cmnd, parameters, 2, values);
                if(getValue(cmnd, parameters, 2, values) == OK) {
                        Serial.println(SS);// successful feedback send it immediately
                        // alert(values[0],values[1], values[2]);
                        tone(BUZZER, values[0]);
                        buzzerStopTime = millis() + int(values[1] * 1000.0); //sys_tick + values[1];
                }
        }else

        //sStp-------------------------------------------------------------------------
        //if (cmnd.indexOf(F("sStp")) >= 0){
        if(cmd == "sStp") {
                Serial.println(SS);// successful feedback send it immediately
                move_times = 255; //stop the movement
        }else

        //gVer----------------------------------------------------------------------
        //if(cmnd.indexOf(F("gVer")) >= 0){
        if(cmd == "gVer") {
                Serial.println(current_ver);
                // Serial.print(F("["));
                // Serial.print(current_ver);
                // Serial.println(F("]"));
        }else

        //gSimuX#Y#Z#V#-------------------------------------------------------------
        //if(cmnd.indexOf(F("gSim")) >= 0){
        if(cmd == "gSim") {
                const char parameters[3] = {'X', 'Y', 'Z'};
                //errorResponse = getValues(cmnd, parameters, 3, values);
                if(getValue(cmnd, parameters, 3, values) == OK)
                {
                        bool polar;
                        move_to_the_closest_point = false;//make sure move_to_the_closest_point is false so that we can get the out_of_range feedback
                        if(values[3]==1)
                                polar = true;
                        else
                                polar = false;
                        move_times=255;//disable move
                        switch(move_to(values[0], values[1], values[2], polar))
                        {
                        case IN_RANGE: Serial.println(S0);
                                break;
                        case OUT_OF_RANGE: Serial.println(F0);
                                break;
                        case OUT_OF_RANGE_NO_SOLUTION: Serial.println(F1);
                                break;
                        default:                break;
                        }
                }
        }else

        //gCrd---------------------------------------------------------------------
        if(cmd == "gCrd") {
                get_current_xyz(&cur_rot, &cur_left, &cur_right, &g_current_x, &g_current_y, &g_current_z, true);
                char letters[3] = {'X','Y','Z'};
                values[0] = g_current_x;
                values[1] = g_current_y;
                values[2] = g_current_z;
                printf(true, values, letters, 3);
        }else

        //gPolS#R#H#--------------------------------------------------------------
        if(cmd == "gPol") {
                get_current_xyz(&cur_rot, &cur_left, &cur_right, &g_current_x, &g_current_y, &g_current_z, true);
                double stretch;
                stretch = sqrt(g_current_x * g_current_x + g_current_y * g_current_y);
                char letters[3] = {'S','R','H'};
                values[0] = stretch;
                values[1] = cur_rot;
                values[2] = g_current_z;
                printf(true, values, letters, 3);
        }else

        //gAng---------------------------------------------------------------------
        //if(cmnd.indexOf(F("gAng")) >= 0){
        if(cmd == "gAng") {
                get_current_rotleftright();
                // read_servo_angle(SERVO_HAND_ROT_NUM);
                char letters[4] = {'B','L','R','H'};
                values[0] = cur_rot;
                values[1] = cur_left;
                values[2] = cur_right;
                values[3] = cur_hand;
                printf(true, values, letters, 4);
                //Serial.println("ST" + String(cur_rot) + "L" + String(cur_left) + "R" + String(cur_right) + "F" + String(cur_hand) + "");
        }else

        //gSer---------------------------------------------------------------------
        if(cmd == "gSer") {
                // get_current_rotleftright();
                read_servo_angle(SERVO_ROT_NUM, false);
                read_servo_angle(SERVO_LEFT_NUM, false);
                read_servo_angle(SERVO_RIGHT_NUM, false);
                read_servo_angle(SERVO_HAND_ROT_NUM, false);
                values[0] = cur_rot;
                values[1] = cur_left;
                values[2] = cur_right;
                values[3] = cur_hand;
                char letters[4] = {'B','L','R','H'};
                printf(true, values, letters, 4);
                //Serial.println("ST" + String(cur_rot) + "L" + String(cur_left) + "R" + String(cur_right) + "F" + String(cur_hand) + "");
        }else

        //gIKX#Y#Z#----------------------------------------------------------------
        //if(cmnd.indexOf(F("gIK")) >= 0){
        if(cmd == "gIKX") {
                const char parameters[3] = {'X', 'Y', 'Z'};
                //errorResponse = getValues(cmnd, parameters, 3, values);
                if(getValue(cmnd, parameters, 3, values) == OK) {

                        double rot, left, right;
                        move_to_the_closest_point = false;
                        if(coordinate_to_angle(values[0], values[1], values[2], &rot, &left, &right, false) != IN_RANGE)
                        {
                                success = false;
                        }
                        else{
                                success = true;
                                left = left - LEFT_SERVO_OFFSET;//assembling offset
                                right = right - RIGHT_SERVO_OFFSET;//assembling offset
                        }
                        char letters[3] = {'T','L','R'};
                        values[0]=rot;
                        values[1]=left;
                        values[2]=right;
                        printf(success,values,letters,3);
                        //Serial.println("ST" + String(rot) + "L" + String(left) + "R" + String(right) + "");
                }
        }else

        //gFKT#L#R#-----------------------------------------------------------------
        // Get Forward Kinematics
        //if(cmnd.indexOf(F("gFK")) >= 0){
        if(cmd == "gFKT") {
                const char parameters[3] = {'T', 'L', 'R'};
                //errorResponse = getValues(cmnd, parameters, 3, values);
                if(getValue(cmnd, parameters, 3, values) == OK) {

                        double x, y, z;
                        if(get_current_xyz(&values[0], &values[1], &values[2], &x, &y, &z, false) == OUT_OF_RANGE)
                        {
                                success = false;
                        }
                        else{
                                success = true;
                        }
                        char letters[3] = {'X','Y','Z'};
                        values[0]=x;
                        values[1]=y;
                        values[2]=z;
                        printf(success,values,letters,3);
                        //Serial.println(letter + "X" + String(x) + "Y" + String(y) + "Z" + String(z) + "");

                }
        }else

        //gMov-----------------------------------------------------------------------
        //if(cmnd.indexOf(F("gMov")) >= 0){
        if(cmd == "gMov") {
                if(available()==false)
                {
                        Serial.println(SS);
                }
                else
                {
                        Serial.println(FF);
                }

        }else

        //gTip-----------------------------------------------------------------------
        //if(cmnd.indexOf(F("gTip")) >= 0){
        if(cmd == "gTip") {
                if(digitalRead(LIMIT_SW))
                {
                        Serial.println(S0);
                }
                else
                {
                        Serial.println(S1);
                }
        }else

        // gDigN# Command----------------------------------------------------------
        if(cmd == "gDig") {
                const char parameters[1] = {'N'}; // digit PIN: 10-13
                //double values[1];
                if(getValue(cmnd, parameters, 1, values) == OK) {     //means no err
                        // read the digit value
                        //int val_d;
                        int val = digitalRead(values[0]);
                        //values[0] = double(val_d);
                        printf(true, val);
                }
        }else

        // sDigN#V# Command----------------------------------------------------------
        if(cmd == "sDig") {
                // 1 means to put PIN HIGH; 0 means LOW
                const char parameters[2] = {'N', 'V'};
                //errorResponse = getValues(cmnd, parameters, 4, values);
                if(getValue(cmnd, parameters, 2, values) == OK) {
                        Serial.println(SS);// successful feedback send it immediately
                        // write the digit value
                        values[1] == 1 ? digitalWrite(values[0], HIGH) : digitalWrite(values[0], LOW);
                }
        }else

        // gAnaN# Command----------------------------------------------------------
        if(cmd == "gAna") {
                const char parameters[1] = {'N'}; // digit PIN: 0-3
                //double values[1];
                if(getValue(cmnd, parameters, 1, values) == OK) {     //means no err
                        // read the digit value
                        //int val_d;
                        int val = analogRead(values[0]);
                        //values[0] = double(val_d);
                        printf(true, val);
                }
        }else

        // gEEPRA#T# Command----------------------------------------------------------
        if(cmd == "gEEP") {
                const char parameters[2] = {'A', 'T'}; // A: adress 0~2048 T: data type 1 or 2 or 4 bytes
                if(getValue(cmnd, parameters, 2, values) == OK) {   //means no err
                        //Serial.println("test"+String(int(values[0]))+"test"+String(int(values[1])));
                        // read the EEPROM value

                        switch(int(values[1]))
                        {
                        case DATA_TYPE_BYTE:
                        {
                                int val = EEPROM.read(values[0]);
                                printf(true, val);
                                break;
                        }
                        case DATA_TYPE_INTEGER:
                        {
                                int i_val = 0;
                                EEPROM.get(values[0], i_val);
                                printf(true, i_val);
                                //Serial.println("S" + String(i_val) + "");
                                break;
                        }
                        case DATA_TYPE_FLOAT:
                        {
                                double f_val = 0.0f;
                                EEPROM.get(values[0],f_val);
                                printf(true, f_val);
                                //Serial.println("S" + String(f_val) + "");
                                break;
                        }
                        }

                }
        }else

        // sEEPRA#T#V# Command----------------------------------------------------------
        if(cmd == "sEEP") {
                const char parameters[3] = {'A', 'T', 'V'}; // A: adress 0~2048 T: data type 1 or 2 or 4 bytes V: value
                if(getValue(cmnd, parameters, 3, values) == OK) {       //means no err
                        Serial.println(SS);// successful feedback send it immediately
                        // write the EEPROM value
                        switch(int(values[1]))
                        {
                        case DATA_TYPE_BYTE:
                        {
                                byte b_val;
                                b_val = byte(values[2]);
                                EEPROM.write(values[0], b_val);
                                break;
                        }
                        case DATA_TYPE_INTEGER:
                        {
                                int i_val = 0;
                                i_val = int(values[2]);
                                EEPROM.put(values[0], i_val);
                                break;
                        }
                        case DATA_TYPE_FLOAT:
                        {
                                float f_val = 0.0f;
                                f_val = float(values[2]);
                                EEPROM.put(values[0],f_val);
                                // Serial.println(f_val);
                                break;
                        }
                        }
                }
        }
}

void uArmClass::printf(bool success, double *dat, char *letters, unsigned char num)
{
        if(success == true)
                Serial.print(F("[S"));
        else
                Serial.print(F("[F"));
        //print the parameter
        for(unsigned char i = 0; i < num; i++)
        {
                Serial.print(letters[i]);
                Serial.print(dat[i]);
        }
        Serial.println(F("]"));

}

void uArmClass::printf(bool success, double dat)
{
        if(success == true)
                Serial.print(F("[S"));
        else
                Serial.print(F("[F"));

        Serial.print(dat);
        Serial.println(F("]"));

}

void uArmClass::printf(bool success, int dat)
{
        if(success == true)
                Serial.print(F("[S"));
        else
                Serial.print(F("[F"));

        Serial.print(dat);
        Serial.println(F("]"));
}
/*!
 */
char uArmClass::getValue(String cmnd, const char *parameters, int parameterCount, double valueArray[])
{
        for (byte i = 0; i < parameterCount; i++) {
                char start_index = cmnd.indexOf(parameters[i]) + 1;
                if (start_index == -1)
                {
                        Serial.println(F("F1"));
                        return ERR1;
                }
                char end_index = 0;
                if (i != parameterCount-1) {
                        end_index = cmnd.indexOf(parameters[i+1]);
                        if (end_index == -1)
                        {
                                Serial.println(F("F1"));
                                return ERR1;
                        }
                }
                else{
                        end_index = cmnd.length() - 1;
                }
                valueArray[i] = cmnd.substring(start_index, end_index).toFloat();
        }
        return OK;
}


//*************************************private functions***************************************//
//**just used by the 512k external eeprom**//

void uArmClass::delay_us(){
}

void uArmClass::iic_start()
{
        PORTC |= 0x20;//  SCL=1
        delay_us();
        PORTC |= 0x10;//  SDA=1
        delay_us();
        PORTC &= 0xEF;//  SDA=0
        delay_us();
        PORTC &= 0xDF;//  SCL=0
        delay_us();
}

void uArmClass::iic_stop()
{
        PORTC &= 0xDF;//  SCL=0
        delay_us();
        PORTC &= 0xEF;//  SDA=0
        delay_us();
        PORTC |= 0x20;//  SCL=1
        delay_us();
        PORTC |= 0x10;//  SDA=1
        delay_us();
}

//return 0:ACK=0
//return 1:NACK=1
unsigned char uArmClass::read_ack()
{
        unsigned char old_state;
        old_state = DDRC;
        DDRC = DDRC & 0xEF;//SDA INPUT
        PORTC |= 0x10;//  SDA = 1;
        delay_us();
        PORTC |= 0x20;//  SCL=1
        delay_us();
        if((PINC&0x10) == 0x10) // if(SDA)
        {
                PORTC &= 0xDF;//  SCL=0
                iic_stop();
                return 1;
        }
        else{
                PORTC &= 0xDF;//  SCL=0
                DDRC = old_state;
                return 0;
        }
}

//ack=0:send ack
//ack=1:do not send ack
void uArmClass::send_ack()
{
        unsigned char old_state;
        old_state = DDRC;
        DDRC = DDRC | 0x10;//SDA OUTPUT
        PORTC &= 0xEF;//  SDA=0
        delay_us();
        PORTC |= 0x20;//  SCL=1
        delay_us();
        PORTC &= 0xDF;//  SCL=0
        delay_us();
        DDRC = old_state;
        PORTC |= 0x10;//  SDA=1
        delay_us();
}

void uArmClass::iic_sendbyte(unsigned char dat)
{
        unsigned char i;
        for(i = 0; i < 8; i++)
        {
                if(dat & 0x80)
                        PORTC |= 0x10; //  SDA = 1;
                else
                        PORTC &= 0xEF; //  SDA = 0;
                dat <<= 1;
                delay_us();
                PORTC |= 0x20;//  SCL=1
                delay_us();
                PORTC &= 0xDF;//  SCL=0
        }
}

unsigned char uArmClass::iic_receivebyte()
{
        unsigned char i,byte = 0;
        unsigned char old_state;
        old_state = DDRC;
        DDRC = DDRC & 0xEF;//SDA INPUT
        for(i = 0; i < 8; i++)
        {
                PORTC |= 0x20;//  SCL=1
                delay_us();
                byte <<= 1;
                if((PINC&0x10) == 0x10) // if(SDA)
                        byte |= 0x01;
                delay_us();
                PORTC &= 0xDF;//  SCL=0
                DDRC = old_state;
                delay_us();
        }
        return byte;
}

unsigned char uArmClass::iic_writebuf(unsigned char *buf,unsigned char device_addr,unsigned int addr,unsigned char len)
{
        DDRC = DDRC | 0x30;
        PORTC = PORTC | 0x30;
        unsigned char length_of_data=0;//page write
        length_of_data = len;
        iic_start();
        iic_sendbyte(device_addr);
        if(read_ack()) return 1;
        iic_sendbyte(addr>>8);
        if(read_ack()) return 1;
        iic_sendbyte(addr%256);
        if(read_ack()) return 1;
        while(len != 0)
        {
                iic_sendbyte(*(buf + length_of_data - len));
                len--;
                if(read_ack()) return 1;
                delay(5);
        }
        iic_stop();

        return 0;
}

unsigned char uArmClass::iic_readbuf(unsigned char *buf,unsigned char device_addr,unsigned int addr,unsigned char len)
{
        DDRC = DDRC | 0x30;
        PORTC = PORTC | 0x30;
        unsigned char length_of_data=0;
        length_of_data = len;
        iic_start();
        iic_sendbyte(device_addr);
        if(read_ack()) return 1;
        iic_sendbyte(addr>>8);
        if(read_ack()) return 1;
        iic_sendbyte(addr%256);
        if(read_ack()) return 1;
        iic_start();
        iic_sendbyte(device_addr+1);
        if(read_ack()) return 1;

        while(len != 0)
        {
                *(buf + length_of_data - len) = iic_receivebyte();

                len--;
                if(len != 0) {
                        send_ack();
                }
        }
        iic_stop();
        return 0;
}

// #ifdef LATEST_HARDWARE
bool uArmClass::play()
{
        unsigned char data[5]; // 0: L  1: R  2: Rotation 3: hand rotation 4:gripper
        recording_read(addr, data, 5);
        if(data[0]!=255)
        {
                write_servo_angle((double)data[2] - ROT_SERVO_OFFSET, (double)data[0] - LEFT_SERVO_OFFSET, (double)data[1] - RIGHT_SERVO_OFFSET);
        }
        else
        {
                return false;
        }

        addr += 5;
        return true;
}

bool uArmClass::record()
{
        if(addr <= 65530)
        {
                unsigned char data[5]; // 0: L  1: R  2: Rotation 3: hand rotation 4:gripper
                if((addr != 65530)&&(sys_status != LEARNING_MODE_STOP))
                {
                        get_current_rotleftright();
                        data[0] = (unsigned char)cur_left;
                        data[1] = (unsigned char)cur_right;
                        data[2] = (unsigned char)cur_rot;
                        //data[3] = (unsigned char)cur_hand;
                }
                else
                {
                        data[0] = 255;//255 is the ending flag
                        //Serial.println(data[0]);
                        recording_write(addr, data, 5);
                        /*if(sys_status == LEARNING_MODE_STOP)//LEARNING_MODE_STOP is just used to notificate record() function to stop, once record() get it then change the sys_status to normal_mode
                           {
                           sys_status = NORMAL_MODE;
                           }*/
                        return false;
                }
                recording_write(addr, data, 5);
                addr += 5;
                return true;
        }
        else
        {
                return false;
        }

}

void uArmClass::recording_write(unsigned int address, unsigned char * data_array, int num)
{
        unsigned char i=0;
        i=(address%128);
        // Since the eeprom's sector is 128 byte, if we want to write 5 bytes per cycle we need to care about when there's less than 5 bytes left
        if((i>=124)&&(num==5))
        {
                i=128-i;
                iic_writebuf(data_array, EXTERNAL_EEPROM_USER_ADDRESS, address, i);// write data
                delay(5);
                iic_writebuf(data_array + i, EXTERNAL_EEPROM_USER_ADDRESS, address + i, num - i);// write data
        }
        //if the left bytes are greater than 5, just do it
        else
        {
                iic_writebuf(data_array, EXTERNAL_EEPROM_USER_ADDRESS, address, num);// write data
        }
}

void uArmClass::recording_read(unsigned int address, unsigned char * data_array, int num)
{
        unsigned char i=0;
        i=(address%128);
        // Since the eeprom's sector is 128 byte, if we want to write 5 bytes per cycle we need to care about when there's less than 5 bytes left
        if((i>=124)&&(num==5))
        {
                i=128-i;
                iic_readbuf(data_array, EXTERNAL_EEPROM_USER_ADDRESS, address, i);// write data
                delay(5);
                iic_readbuf(data_array + i, EXTERNAL_EEPROM_USER_ADDRESS, address + i, num - i);// write data
        }
        //if the left bytes are greater than 5, just do it
        else
        {
                iic_readbuf(data_array, EXTERNAL_EEPROM_USER_ADDRESS, address, num);// write data
        }
}
//#endif
//*************************************end***************************************//
