# uArm Arduino Library Release Note

## [2.0.12] - 2016-09-13

## Fix
- Fix uArm in extreme position.
- Encapsulate limit_range function to validate if coordinate is out of range.

## [2.0.11] - 2016-09-08

## Fix
- Fix Attach issue when unplug DC adapter
- Change sAtt sDet paramenter to 'N'

## [2.0.9] - 2016-09-01

## Changes
- Brand New Communication Protocol

## [1.7.3] - 2016-07-07

### Fix
- Fix write serial number CONFIRM_FLAG
- uArm won't move if no LINEAR Calibration

## [1.7.2] - 2016-06-30

### Fix
- attach servo even not calibrate
- rewrite set_servo_status replace attach_servo detach_servo
- execute write_stretch_height event not calibrate
- Doxygen Document Support

## [1.7.1] - 2016-06-28

### Fix
- Set Current angle after attach servo
- rewrite set_servo_status replace attach_servo detach_servo

## [1.7.0] - 2016-06-24

### Fix
- Update examples Calibration.ino, movement.ino, Add new UArmTextControl2.0.ino
- Update uarm_library.h make some protected value be public
- Move All source code to src folder
- Create Docs folder to store Doxygen Configure & Html header footer files

## [1.6.2] - 2016-06-24

### Fix
- Change Lots of function names according to Programming Rules

## [1.6.1] - 2016-06-22

### Fix
- Fix MoveTo Lock Hand Servo issue.


## [1.6.0] - 2016-06-20

### Fix
- Add Limit for x*x + y*y < 32, Fix When x*x + y*y > 32 uArm will get wired position

### Changes

- Rewrite Servo.h to UFServo.h, using float when servo.write(), increase accuracy
- Rewrite uArmFimata to UArmProtocol.ino   


## [1.5.11] - 2016-06-07

### Fix
- Fix Test.ino unused function
- Update Code Format

## [1.5.10] - 2016-06-07

### Fix
- At moveToAtOnce(x,y,z)

## [1.5.9] - 2016-06-01

### Fix
- Fix writeStretch() offset address not correct

## [1.5.8] - 2016-05-07

### Fix
- Speed up Calibration, reduce delay
- Use writeAngle() Function in MoveTo

### Changes

- Add Calibration.ino into examples


## [1.5.6] - 2016-05-06

### Fix

- Update SERIAL_NUMBER_ADDRESS to 100, Update CALIBRATION_STRETCH_FLAG mark value is CONFIRM_FLAG

## [1.5.5] - 2016-05-05

### Fix

- if SERIAL_NUMBER_ADDRESS equal CONFIRM_FLAG 0x80, then Serial Number exist in EEPROM

## [1.5.4] - 2016-05-02

### Fix

- if SERIAL_NUMBER_ADDRESS equal SERIAL_NUMBER_ADDRESS, then Serial Number exist in EEPROM

## [1.5.3] - 2016-05-02

### Changes

- Add readSerialNumber & writeSerialNumber function (Serial Number: Address 1024, size:14)


## [1.5.2] - 2016-04-29

### Changes

- Add Example, MoveTest, GetXYZ, Recording Mode


## [1.5.2] - 2016-04-29

### Changes

- Cancel v.1.5.0 read offset from EEPROM.


## [1.5.0] - 2016-04-14

### Changes

- Initialize servo offset & linear offset from EEPROM to global values, prevent read EEPROM every time

- Use [EEPROM.get()][a4e46a5d] & [EEPROM.put()][275bf48d] to read & write value in EEPROM instead of saveDataToRom()

  [a4e46a5d]: https://www.arduino.cc/en/Reference/EEPROMGet "EEPROM.get()"
  [275bf48d]: https://www.arduino.cc/en/Reference/EEPROMPut "EEPROM.put()"

- rename function readToAngle to analogToAngle
- Change Offset address in EEPROM

## [1.4.0] - 2016-04-12

### Changes

- uarm_library.cpp writeServoAngle resume LEFT & RIGHT ANGLE

- ToDo: remove LEFT & RIGHT ANGLE from WriteServoAngle (For Safety)


## [1.3.1] - 2016-04-12

### Changes

- uarm_library.cpp writeLeftRightServoAngle() Update the angle between left & right  

- Change Folder examples folder & stretch name From UarmFirmata to UArmFirmata  
