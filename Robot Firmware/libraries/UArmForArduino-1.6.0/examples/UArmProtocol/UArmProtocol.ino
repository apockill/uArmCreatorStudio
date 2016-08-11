/******************************************************************************
* File Name          : UArmFirmata.ino
* Author             : Joey Song
* Updated            : Joey Song/Alex Tan
* Email              : joey@ufactory.cc
* Description        :
* License            :
* Copyright(C) 2016 UFactory Team. All right reserved.
*******************************************************************************/

#include <uarm_library.h>
#include <EEPROM.h>


#define MAX_DATA_BYTES                  64 // max number of data bytes in incoming messages

#define UARM_FIRMATA_MAJOR_VERSION 1
#define UARM_FIRMATA_MINOR_VERSION 3
#define UARM_FIRMATA_BUGFIX        1

#define UARM_FIRMWARE_MAJOR_VERSION 1
#define UARM_FIRMWARE_MINOR_VERSION 7
#define UARM_FIRMWARE_BUGFIX        0

#define START_SYSEX             0xF0 // start a MIDI Sysex message
#define END_SYSEX               0xF7 // end a MIDI Sysex message

#define UARM_CODE                   (0XAA)

#define READ_ANGLE                  (0X10)
#define WRITE_ANGLE                 (0X11)
#define READ_COORDS                 (0X12)
#define WRITE_COORDS                (0X13)
#define READ_DIGITAL                (0X14)
#define WRITE_DIGITAL               (0X15)
#define READ_ANALOG                 (0X16)
#define WRITE_ANALOG                (0X17)
#define READ_EEPROM                 (0X1A)
#define WRITE_EEPROM                (0X1B)
#define DETACH_SERVO                (0X1C)
#define PUMP_STATUS                 (0X1D)
#define WRITE_STRETCH               (0X1E)
#define WRITE_LEFT_RIGHT_ANGLE      (0X1F)
#define GRIPPER_STATUS              (0X20)
#define READ_SERIAL_NUMBER          (0x21)
#define WRITE_SERIAL_NUMBER         (0x22)
#define REPORT_FIRMWARE_VERSION     (0x23)
#define BUZZER_ALERT                (0x24)

#define DATA_TYPE_BYTE              1
#define DATA_TYPE_INTEGER           2
#define DATA_TYPE_FLOAT             4




boolean parsingSysex;
byte storedInputData[MAX_DATA_BYTES];
int sysexBytesRead;

void setup()
{
  Serial.begin(57600);
}

void loop()
{
  while(Serial.available())
    processInput();
}


boolean handleSysex(byte command, byte argc, byte *argv)
{
    if (command == UARM_CODE)
    {
        byte uarmCommand;
        uarmCommand = argv[0];

        // CMD 10 Read Angle
        if (uarmCommand == READ_ANGLE)
        {
            byte servo_num = argv[1];
            boolean withOffset = argv[2]; // if servo_offset = 0 there is offset inside
            Serial.write(START_SYSEX);
            Serial.write(UARM_CODE);
            Serial.write(servo_num);
            float angle = uarm.readAngle(servo_num,withOffset);
            sendFloatAsThree7bitBytes(angle);

            Serial.write(END_SYSEX);
            return true;
        }

        // CMD 11 Write Angle
        if (uarmCommand == WRITE_ANGLE)
        {
            byte servo_num = argv[1];
            double servo_angle = argv[2] + (argv[3] << 7) + float(argv[4])/100;
            boolean writeWithOffset = argv[5];
            uarm.writeServoAngle(servo_num,servo_angle,writeWithOffset);
            return true;
        }

        // CMD 12 Read Coords
        if (uarmCommand == READ_COORDS)
        {
            Serial.write(START_SYSEX);
            Serial.write(UARM_CODE);
            Serial.write(READ_COORDS);
            uarm.calXYZ();
            float x = uarm.getCalX();
            float y = uarm.getCalY();
            float z = uarm.getCalZ();
            sendFloatAsFour7bitBytes(x);
            sendFloatAsFour7bitBytes(y);
            sendFloatAsFour7bitBytes(z);
            Serial.write(END_SYSEX);
            return true;
        }

        // CMD 13 Write Coords
        if (uarmCommand == WRITE_COORDS)
        {
            float x = argv[2] + (argv[3] << 7) + float(argv[4])/100;
            if(argv[1] == 1)
            x = -x;
            float y = argv[6] + (argv[7] << 7) + float(argv[8])/100;
            if(argv[5] == 1)
            y = -y;
            float z = argv[10] + (argv[11] << 7) + float(argv[12])/100;
            if(argv[9] == 1)
            z = -z;
            float hand_angle = argv[13] + (argv[14] << 7) + float(argv[15])/100;
            byte relative_flags = argv[16];
            float time_spend = argv[17] + (argv[18] << 7) + float(argv[19])/100;
            byte path_type = argv[20];
            byte ease_type = argv[21];
            // boolean enable_hand = argv[22];
            delay(5);
            uarm.moveToOpts(x,y,z,hand_angle,relative_flags,time_spend,path_type,ease_type);
            delay(10);
        }

        // CMD 14 Read Digital
        if (uarmCommand == READ_DIGITAL)
        {
            byte pin_num = argv[1];
            byte pin_mode = argv[2]; // 0 means input   1 means input_pullup
            {

                Serial.write(START_SYSEX);
                Serial.write(UARM_CODE);
                Serial.write(pin_num);

                pin_mode == 1 ? pinMode(pin_num, INPUT_PULLUP) : pinMode(pin_num, INPUT);

                Serial.write(digitalRead(pin_num));

                Serial.write(END_SYSEX);
            }
            return true;
        }

        // CMD 15 Write Digital
        if (uarmCommand == WRITE_DIGITAL)
        {
            byte pin_num= argv[1];
            pinMode(pin_num, OUTPUT);

            byte pin_mode = argv[2];
            pin_mode == 1 ? digitalWrite(pin_num,HIGH) : digitalWrite(pin_num,LOW);

            return true;
        }

        // CMD 16 Read Analog
        if (uarmCommand == READ_ANALOG)
        {
            byte pin_num = argv[1];
            {

                Serial.write(START_SYSEX);
                Serial.write(UARM_CODE);
                Serial.write(pin_num);
                sendValueAsTwo7bitBytes(analogRead(pin_num));
                Serial.write(END_SYSEX);
            }
            return true;
        }

        // CMD 17 Write Analog
        if (uarmCommand == WRITE_ANALOG)
        {
            byte pin_num= argv[1];
            pinMode(pin_num, OUTPUT);

            double analog_val = argv[2] + (argv[3] << 7);
            analogWrite(pin_num,constrain(analog_val,0,255));

            return true;
        }

        // CMD 1A Read EEPROM
        if (uarmCommand == READ_EEPROM)
        {
            byte data_type = argv[1];
            int eeprom_add = argv[2] + (argv[3] << 7);

            Serial.write(START_SYSEX);
            Serial.write(UARM_CODE);
            Serial.write(READ_EEPROM);
            sendValueAsTwo7bitBytes(eeprom_add);
            switch(data_type)
            {
                case DATA_TYPE_BYTE:
                {
                    sendValueAsTwo7bitBytes(EEPROM.read(eeprom_add));
                    break;
                }
                case DATA_TYPE_INTEGER:
                {
                    int i_val = 0;
                    sendIntegerAsThree7bitBytes(EEPROM.get(eeprom_add, i_val));
                    break;
                }
                case DATA_TYPE_FLOAT:
                {
                    float f_val = 0.0f;
                    sendFloatAsFour7bitBytes(EEPROM.get(eeprom_add,f_val));
                    break;
                }
            }
            Serial.write(END_SYSEX);
            return true;
        }

        // CMD 1B Write EEPROM
        if (uarmCommand == WRITE_EEPROM)
        {
            byte data_type = argv[1];
            byte eeprom_add = argv[2] + (argv[3] << 7);
            // byte eeprom_val = argv[3] + (argv[4] << 7);
            // EEPROM.write(eeprom_add,eeprom_val);
            switch(data_type)
            {
                case DATA_TYPE_BYTE:
                {
                    EEPROM.write(eeprom_add,argv[4] + (argv[5] << 7));
                    break;
                }
                case DATA_TYPE_INTEGER:
                {
                    int int_val = 0;
                    int_val = argv[5] + (argv[6] << 7);
                    int_val = ((argv[4] == 1) ? -int_val : int_val);
                    EEPROM.put(eeprom_add, int_val);
                    break;
                }
                case DATA_TYPE_FLOAT:
                {
                    float f_val = argv[5] + (argv[6] << 7) + float(argv[7])/100;
                    f_val = ((argv[4] == 1) ? -f_val : f_val);
                    EEPROM.put(eeprom_add, f_val);
                    break;
                }
            }
            return true;
        }

        // CMD 1C Servo Attach or Detach
        if (uarmCommand == DETACH_SERVO)
        {
            uarm.detachAll();
            return true;
        }

        // CMD 1D Pump Status
        if (uarmCommand == PUMP_STATUS)
        {
            byte pump_status = argv[1];
            pump_status == 1 ? uarm.pumpOn() : uarm.pumpOff();
            return true;
        }
        // CMD 20 GRIPPER Status
        if (uarmCommand == GRIPPER_STATUS)
        {
            byte gripper_status = argv[1];
            gripper_status == 1 ? uarm.gripperCatch() : uarm.gripperRelease();
            return true;
        }
        //0X1E WRITE_STRETCH
        if (uarmCommand == WRITE_STRETCH)
        {
            double length = argv[2] + (argv[3] << 7) + float(argv[4])/100;
            length = argv[1] == 1 ? -length : length;
            double height = argv[6] + (argv[7] << 7) + float(argv[8])/100;
            height = argv[5] == 1 ? -height : height;
            uarm.writeStretch(length,height);
            return true;
        }
        //0X1F WRITE_LEFT_RIGHT_ANGLE
        if (uarmCommand == WRITE_LEFT_RIGHT_ANGLE)
        {
            double left = argv[1] + (argv[2] << 7) + float(argv[3])/100;
            double right = argv[4] + (argv[5] << 7) + float(argv[6])/100;
            boolean withOffset = argv[7];
            uarm.writeLeftRightServoAngle(left,right, withOffset);
            return true;
        }
        //0X22 WRITE_SERIAL_NUMBER
        if (uarmCommand == WRITE_SERIAL_NUMBER)
        {
            byte sn_array[14];
            for(byte i=0; i<14; i++){
                sn_array[i] = 0;
            }
            for(byte i=0; i<14; i++){
                sn_array[i] = argv[i+1];
            }
            uarm.writeSerialNumber(sn_array);
            return true;
        }
        //0X21 READ_SERIAL_NUMBER
        if (uarmCommand == READ_SERIAL_NUMBER)
        {
            Serial.write(START_SYSEX);
            Serial.write(UARM_CODE);
            Serial.write(READ_SERIAL_NUMBER);
            byte sn_array[14];
            for(byte i=0; i<14; i++){
                sn_array[i] = 0;
            }
            uarm.readSerialNumber(sn_array);
            for(byte i=0; i<14; i++){
                Serial.write(sn_array[i]);
            }
            Serial.write(END_SYSEX);
            return true;
        }
        //0X23 REPORT_FIRMWARE_VERSION
        if (uarmCommand == REPORT_FIRMWARE_VERSION)
        {
            Serial.write(START_SYSEX);
            Serial.write(UARM_CODE);
            Serial.write(REPORT_FIRMWARE_VERSION);
            Serial.write(UARM_FIRMWARE_MAJOR_VERSION);
            Serial.write(UARM_FIRMWARE_MINOR_VERSION);
            Serial.write(UARM_FIRMWARE_BUGFIX);
            Serial.write(END_SYSEX);
            return true;
        }

        if (uarmCommand == BUZZER_ALERT)
        {
            byte times = argv[1];
            byte run_time = argv[2];
            byte stop_time = argv[3];
            uarm.alert(times, run_time, stop_time);
            return true;
        }

    }
    return false;
}

void processInput(void)
{
    int inputData = Serial.read();
    if (inputData != -1) {
      parse(inputData);
    }
}

void parse(byte inputData)
{
    int command;
    if (parsingSysex) {
      if (inputData == END_SYSEX) {
          //stop sysex byte
          parsingSysex = false;
          //fire off handler function
          processSysexMessage();
      } else {
        //normal data byte - add to buffer
        storedInputData[sysexBytesRead] = inputData;
        sysexBytesRead++;
      }
    }
    else {
        // remove channel info from command byte if less than 0xF0
        if (inputData < 0xF0) {
          command = inputData & 0xF0;
        } else {
          command = inputData;
          // commands in the 0xF* range don't use channel data
        }
        switch (command) {
          case START_SYSEX:
            parsingSysex = true;
            sysexBytesRead = 0;
            break;
        }
      }
}

void processSysexMessage(void)
{
  switch (storedInputData[0]) {
    default:
      handleSysex(storedInputData[0], sysexBytesRead - 1, storedInputData + 1);
  }
}

void sendValueAsTwo7bitBytes(int value)
{
    Serial.write(value & 0x7F);
    Serial.write(value >> 7 & 0x7F);
}

void sendFloatAsFour7bitBytes(float val){
    int int_val = val;
    int decimal_val = int(round((val - int_val)*100));
    Serial.write(val > 0 ? 0 : 1);
    Serial.write(abs(int_val) & B01111111 );
    Serial.write(abs(int_val) >> 7 & B01111111);
    Serial.write(abs(decimal_val) & 0x7F );
}

void sendFloatAsThree7bitBytes(float val){
    int int_val = val;
    int decimal_val = int(round((val - int_val)*100));
    Serial.write(abs(int_val) & B01111111 );
    Serial.write(abs(int_val) >> 7 & B01111111);
    Serial.write(abs(decimal_val) & 0x7F );
}

void sendIntegerAsThree7bitBytes(int val){
    int symbol = val > 0 ? 0 : 1;
    Serial.write(symbol);
    Serial.write(abs(val) & B01111111 );
    Serial.write(abs(val) >> 7 & B01111111);
}
