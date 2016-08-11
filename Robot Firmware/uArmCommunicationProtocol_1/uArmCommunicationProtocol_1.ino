#include <uarm_library.h>


/**
This sketch is a communication protocol for uArm using Serial.

All commands must be wrapped in brackets- [command]
Any string of commands must end with an endline char '\n' for the commands to be processed

Commands:
  [moveX#Y#Z#S#]   Where # is a double, This will move the robot to an XYZ position, in S is speed in centimeters / second from the current location to goal location
                  Send Example:   [moveX15Y-15Z20S25]\n  
                  Return Example: [O]
  
  [ssS#V#]        Where S# is the servo number and V# is an angle between 0 and 180. This will set the angle of that particular servo
                  Send Example:   [sssS1V1]\n 
                  Return Example: [O]
                  
  [pumpV#]        Where # is either 1 or 0. 1 means pump on, 0 means pump off.
                  Send Example:   [pumpV1]\n
                  Return Example: [O]
                  
  [attachS#]      Attach servo #. Same as servo #'s in uarm_library.h
                  Send Example:   [attachS1]\n
                  Return Example: [O]
                  
  [detachS#]      Detach servo #. Same as servo #'s in uarm_library.h
                  Send Example:   [detachS1]\n
                  Return Example: [O]
                  
  [buzzF#T#]      Set the buzzer to F Frequency for T time
                  Send Example:   [buzzF261.63T1]\n
                  Return Example: [O]
                  
  [sStp]          Stop any ongoing movement that the robot is performing
                  Send Example:   [sStp]
                  Return Example: [O]
                  
  [gcrd]          Returns the XYZ coordinate position of the robot
                  Send Example:   [gcoords]\n
                  Return Example: [coordsX#Y#Z#]
                  
  
  [gang]        Returns the analog read angle of all the servos in the robot and returns them as angleA#B#C#D# where ABCD are servos 0,1,2,3 respectively
                  Send Example:   [gang]\n
                  Return Example: [angA#B#C#D#]
                  
  [gikX#Y#Z#]     Returns the inverse kinematics for XYZ point in the form A#B#C# where ABC are servos 0,1,2 respectively
                  Send Example:   [gikX0Y-15Z15#]\n
                  Return Example: [ikA90B15C80] 
                  
  [gfkA#B#C#]     Returns the forward kinematics for ABC servo angles in the form X#Y#Z# where ABC are servos 0,1,2 respectively
                  Send Example:   [gfkA90B15C80]\n
                  Return Example: [fkX0Y-15Z15] 
                  
  [gmov]          Returns whether or not the robot is currently moving. Returns either 1 or 0 if it is moving or not.
                  Send Example: [gmov]\n
                  Return Example: [movM1]
  
  [gtip]          Returns whether or not the tip of the robot is currently pressed. Returns either 1 if the tip is pressed, 0 if not.
                  Send Example: [gtip]\n
                  Return Example: [tipV1]
**/

//  The array of 'steps' the robot will take to get to it's desired location
byte currentStep = 255;  //The current 'step' the robot is in, in the movement array. -1 means it is not currently moving


// Set Pin variables
int tipPin    = 2;
int buzzerPin = 3;


// Movement Variables
unsigned int INTERP_INTVLS;
const int    maxIntervals = 60;
long   goalTime;              //  When the robot intends to complete the move
double goalTimeStep;
double x_array[maxIntervals + 1]; // Maximum of maxIntervals interp intervals in any move, so make each arr 80 long
double y_array[maxIntervals + 1]; // The last array is used to store the final position that the user actually wants to arrive to
double z_array[maxIntervals + 1];


// What time, in millis(), that the buzzer should stop. If it's -1, then the buzzer is off.
long buzzerStopTime = -1; 

//  Communication variables
String message = "";



void setup() {
  Serial.begin(115200);
  Serial.setTimeout(30);  //  Makes Serial.parseInt() not wait a long time after an integer has ended

  // Make sure the robots tip sensor can be read
  pinMode(tipPin,INPUT_PULLUP);

  // Make sure the servos have values, so they don't lock up on attachment
  double rot, left, right; 
  uarm.calAngles(0, -15, 15, rot, left, right);
  uarm.writeAngle(rot, left, right, 90);
}


void loop() {
  // Get any commands that have been received and add it to the global message String for processing later
  while (Serial.available() > 0) {
    message = Serial.readStringUntil('\n');
    String cmnd = parseNextCommand();       // Get the command
    Serial.print(runCommand(cmnd));         // Run the command and send back the response
  }


  
  // TODO: Reevaluate the priority of these. Should commands be added to message before processing? Should step be done b4 command is received?
  if(isTimeToMove()){
    moveStep();
  }

  if(buzzerStopTime > 0){
    if(buzzerStopTime < millis()){
      noTone(buzzerPin);
      buzzerStopTime = -1;
    }
  }
}




String runCommand(String cmnd){
    
    // To save memory, create the "[OK" and "]\n" right now, in flash memory
    String ok    = F("[O]\n"); 
    String endB  = F("]\n");


    // Change a servos position value
    if(cmnd.indexOf(F("ss")) >= 0){
       String servoSetParameters[] = {F("S"), F("V")};
       float values[2];
       String errorResponse        = getValues(cmnd, servoSetParameters, 2, values);
       if(errorResponse.length() > 0) {return errorResponse;}
       
        
       //getCommandValues(cmnd, servoSetParameters, 2, values);
       // Clamp the angle between 0 and 180
//       if(values[1] < 0){values[1] = 0;} else if(values[1] > 180) { values[1] = 180;} 
       uarm.writeServoAngle(values[0], values[1], true);

       return ok;
    }else


    
    // Get Inverse Kinematics
    if(cmnd.indexOf(F("gik")) >= 0){
       String IKParameters[] = {F("X"), F("Y"), F("Z")};
       String errorResponse      = isValidCommand(cmnd, IKParameters, 3);
       if(errorResponse.length() > 0) {return errorResponse;}
       
       float values[3];
       getCommandValues(cmnd, IKParameters, 3, values);
       double A, B, C;
       uarm.calAngles(values[0], values[1], values[2], A, B, C);
       return "[ikA" + String(A) + "B" + String(B) + "C" + String(C) + endB;
    }else


    // Get Forward Kinematics
    if(cmnd.indexOf(F("gfk")) >= 0){
       String IKParameters[] = {F("A"), F("B"), F("C")};
       String errorResponse      = isValidCommand(cmnd, IKParameters, 3);
       if(errorResponse.length() > 0) {return errorResponse;}
       
       float values[3];
       getCommandValues(cmnd, IKParameters, 3, values);
       double x, y, z;
       uarm.getCalXYZ(values[0], values[1], values[2], x, y, z);
       return "[fkX" + String(x) + "Y" + String(y) + "Z" + String(z) + endB;
    }else

    
    // Get coords command
    if(cmnd.indexOf(F("gcrd")) >= 0){
      double x = 0;   double y = 0;   double z = 0;
      //uarm.getCalXYZ(x, y, z);
      uarm.getCalXYZ(uarm.readAngle(SERVO_ROT_NUM), uarm.readAngle(SERVO_LEFT_NUM), uarm.readAngle(SERVO_RIGHT_NUM), x, y, z);
      return "[crdX" + String(x) + "Y" + String(y) + "Z" + String(z) + "]\n";
    }else

    
    // Gets the analog read angle of all the servos in the robot and returns them as angleA#B#C#D# where ABCD are servos 0,1,2,3 respectively
    if(cmnd.indexOf(F("gang")) >= 0){
       float A = uarm.readAngle(SERVO_ROT_NUM);
       float B = uarm.readAngle(SERVO_LEFT_NUM);
       float C = uarm.readAngle(SERVO_RIGHT_NUM);
       float D = uarm.readAngle(SERVO_HAND_ROT_NUM);
       return "[angA" + String(A) + "B" + String(B) + "C" + String(C) + "D" + String(D) + endB;
    }else

    
    // Get whether or not the robot is currently moving
    if(cmnd.indexOf(F("gmov")) >= 0){
      int isMoving = 1;
      if(currentStep == 255){ isMoving = 0;}
      return "[movM" + String(isMoving) + endB;
    }else
    
    // Gets whether or not the tip sensor of the robot is pressed
    if(cmnd.indexOf(F("gtip")) >= 0){
      int isTipPressed = digitalRead(2);
      return "[tipV" + String(isTipPressed) + endB;
    }else

    
    // Move Command
    if(cmnd.indexOf(F("move")) >= 0){
      String moveParameters[] = {F("X"), F("Y"), F("Z"), F("S")};
      String errorResponse    = isValidCommand(cmnd, moveParameters, 4);
      if(errorResponse.length() > 0){return errorResponse;}
      
      //  Create action and respond
      float values[4];
      getCommandValues(cmnd, moveParameters, 4, values);
      setMove(values[0], values[1], values[2], values[3]);

      return ok;
    }else

    
    // Set the status of the pump
    if(cmnd.indexOf(F("pump")) >= 0){
      String pumpParameters[] = {F("V")};
       String errorResponse   = isValidCommand(cmnd, pumpParameters, 1);
       if(errorResponse.length() > 0) {return errorResponse;}
       
       float values[1];
       getCommandValues(cmnd, pumpParameters, 1, values);
       if(values[0] > 0){  uarm.pumpOn();  }else if(values[0] <= 0){  uarm.pumpOff();  } 
       return ok;
    }else

    
    // Attach a servo
    if(cmnd.indexOf(F("attach")) >= 0){
      String attachParameters[] = {F("S")};
      String errorResponse = isValidCommand(cmnd, attachParameters, 1);
      if(errorResponse.length() > 0) {return errorResponse;}
      float values[1];
      getCommandValues(cmnd, attachParameters, 1, values);
      if(setServoStatus(true, values[0])){
        return ok;
      }else{ 
        return "[ERROR: Servo number " + String(values[0]) + " does not exist]\n";
      }
       
      return ok;
    }else

    
    // Detach a servo
    if(cmnd.indexOf(F("detach")) >= 0){
      String detachParameters[] = {F("S")};
      String errorResponse      = isValidCommand(cmnd, detachParameters, 1);
      if(errorResponse.length() > 0) {return errorResponse;}
      
      float values[1];
      getCommandValues(cmnd, detachParameters, 1, values);
      if(setServoStatus(false, values[0])){
        return ok;
      }else{ 
        return "[ERROR: Servo number " + String(values[0]) + " does not exist]\n";
      }
    }else


    // Set the Buzzer for a predetermined amount of time
    if(cmnd.indexOf(F("buzz")) >= 0){
       String buzzerParameters[] = {F("F"), F("T")};
       String errorResponse      = isValidCommand(cmnd, buzzerParameters, 2);
       if(errorResponse.length() > 0) {return errorResponse;}
       
       float values[2];
       getCommandValues(cmnd, buzzerParameters, 2, values);
       if(values[0] < 0 || values[1] < 0){
         return F("[ERROR: F & T should be > 0]");
       }
       tone(buzzerPin, values[0]);
       buzzerStopTime = millis() + int(float(values[1]) * float(1000));
       return ok;
    }else


    // Set the Buzzer for a predetermined amount of time
    if(cmnd.indexOf(F("sStp")) >= 0){
       currentStep = 255;
       return ok;
    }
    
     
    if(cmnd.length() > 0){
      return "[ERROR: No such command: " + cmnd + endB;
    }else{
      return F("");
    }
}




void getCommandValues(String cmnd, String parameters[], int parameterCount, float *valueArray){
  int index[parameterCount];
  for(int p = 0; p < parameterCount; p++){
    index[p] = cmnd.indexOf(parameters[p]);
  } 
  
  for(int p = 0; p < parameterCount; p++){
    if(p < parameterCount - 1){
      valueArray[p] = cmnd.substring(index[p] + 1, index[p + 1]).toFloat();
    }else{
      valueArray[p] = cmnd.substring(index[p] + 1).toFloat();
    }
  }
}

String getValues(String cmnd, String parameters[], int parameterCount, float *valueArray){
  int index[parameterCount];

  //  Make sure that each parameter is in the string
  for(int p = 0; p < parameterCount; p++){
      index[p] = cmnd.indexOf(parameters[p]);
      if(index[p] == -1){return "[ERROR: Missing Parameter " + parameters[p] + F(" ") + cmnd + F("]\n");}
  }
  
  
  //  Check that there is something between each parameter (AKA, the value)
  for(int p = 0; p < parameterCount; p++){   
    if(p < parameterCount - 1){
      if((index[p + 1] - index[p]) == 1){
        return "[ERROR: No value for " + parameters[p] + F("]\n");
      }
      valueArray[p] = cmnd.substring(index[p] + 1, index[p + 1]).toFloat();
    }else{ 
      if(index[p] == cmnd.length() - 1){
        return "[ERROR: No value for " + parameters[p] + F("]\n");
      }
      valueArray[p] = cmnd.substring(index[p] + 1).toFloat();
    }
    
  }
  
  return F("");
}

String isValidCommand(String cmnd, String parameters[], int parameterCount){
  int index[parameterCount];
  
  String missingParameter = F("[ERROR: Missing Parameter ");
  String incorrectOrder   = F("[ERROR: Incorrect Parameter order on parameter ");
  String endB = F("]\n");
  //  Get all indexes
  for(int p = 0; p < parameterCount; p++){
      index[p] = cmnd.indexOf(parameters[p]);
      if(index[p] == -1){return missingParameter + parameters[p] + F(" ") + cmnd + endB;}
  }
  
  //  Check that the commands are in the correct order
  for(int p = 0; p < parameterCount; p++){
    if(parameterCount == 1){break;}
    
    if(p < parameterCount - 1){
      if(!(index[p] < index[p + 1])){
        return incorrectOrder + parameters[p] + endB;
      }
    }else if(!(index[p] > index[p-1])){
      return incorrectOrder + parameters[p] + endB;
    }
  }
  
  //  Check that there is something between each parameter (AKA, the value)
  for(int p = 0; p < parameterCount; p++){   
    if(p < parameterCount - 1){
      if((index[p + 1] - index[p]) == 1){
        return missingParameter + parameters[p] + endB;
      }
    }else if(index[p] == cmnd.length() - 1){
      return missingParameter + parameters[p] + endB;
    }
  }
  
  return F("");
}



String parseNextCommand() {

  int cmndStart = message.indexOf('[');
  int cmndEnd   = message.indexOf(']');


  //If message starts with ][
  if (cmndStart == -1 || cmndEnd == -1 || cmndStart > cmndEnd) {  
    return F("");
  }

  // Finally, pull the command out, remove the brackets, and return it
  String cmnd = message.substring(cmndStart + 1, cmndEnd);
  message = F("");  // Free up memory
  return cmnd;
}



boolean setServoStatus(boolean setAttached, int servoNum){
  // Attach or detach a servo, and set the position instantly after doing so to prevent "snap"
  // Returns true or false if the servo was a valid number

  double angleBefore = 90;
  if(servoNum == SERVO_ROT_NUM){
    if(setAttached){
      angleBefore = uarm.readAngle(SERVO_ROT_NUM);
      uarm.g_servo_rot.attach(11);
      uarm.writeServoAngle(servoNum, angleBefore, true);
    }else{
      uarm.g_servo_rot.detach();
    }     
  }else if(servoNum == SERVO_LEFT_NUM){    
    if(setAttached){
      angleBefore = uarm.readAngle(SERVO_LEFT_NUM);
      uarm.g_servo_left.attach(13);
      uarm.writeServoAngle(servoNum, angleBefore, true);
    }else{
      uarm.g_servo_left.detach();
    }     
  }else if(servoNum == SERVO_RIGHT_NUM){   
    if(setAttached){
      angleBefore = uarm.readAngle(SERVO_RIGHT_NUM);
      uarm.g_servo_right.attach(12);
      uarm.writeServoAngle(servoNum, angleBefore, true);
    }else{
      uarm.g_servo_right.detach();
    }  
  }else if(servoNum == SERVO_HAND_ROT_NUM){
    if(setAttached){
      angleBefore = uarm.readAngle(SERVO_HAND_ROT_NUM);
      uarm.g_servo_hand_rot.attach(10);
      uarm.writeServoAngle(servoNum, angleBefore, true);
    }else{
      uarm.g_servo_hand_rot.detach();
    }  
  }else{ 
    return false;
  }
  return true;
}



void setMove(double x, double y, double z, double goalSpeed) {

  // Limit the range of the uArm
  float limit = sqrt((x*x + y*y));
  if (limit > 32)
  {
      float k = 32/limit;
      x = x * k;
      y = y * k;
  }
  
  // find current XYZ position using cached servo values
  double current_x;
  double current_y;
  double current_z;

  uarm.getCalXYZ(uarm.cur_rot,  uarm.cur_left, uarm.cur_right, current_x, current_y, current_z);

  // find target angles
  double tgt_rot;
  double tgt_left;
  double tgt_right;
  uarm.calAngles(x, y, z, tgt_rot, tgt_left, tgt_right);
  
  // calculate the length, to calculate the # of interpolations that will be necessary
  unsigned int delta_rot   = abs(tgt_rot   - uarm.cur_rot);
  unsigned int delta_left  = abs(tgt_left  - uarm.cur_left);
  unsigned int delta_right = abs(tgt_right - uarm.cur_right);

  // CUSTOM: Use the robots current position and its desired destination to calculate the amount of time for the move to occur within
  double distance   = pow(pow(x-current_x, 2) + pow(y-current_y, 2) + pow(z-current_z, 2), .5);


  // Calculate the number of interpolations for this move + " "
  INTERP_INTVLS = max(delta_rot,delta_left);
  INTERP_INTVLS = max(INTERP_INTVLS,delta_right);
  INTERP_INTVLS = (INTERP_INTVLS<maxIntervals) ? INTERP_INTVLS:maxIntervals;  // Max it out at maxIntervals
  INTERP_INTVLS = (INTERP_INTVLS>3)  ? INTERP_INTVLS:3;

  // Create the movement path
  uarm.INTERP_INTVLS = INTERP_INTVLS;
  uarm.interpolate(current_x, x, x_array, INTERP_EASE_INOUT);
  uarm.interpolate(current_y, y, y_array, INTERP_EASE_INOUT);
  uarm.interpolate(current_z, z, z_array, INTERP_EASE_INOUT);

  // Make the final cell of the interpolation be the actual destination
  x_array[INTERP_INTVLS] = x;
  y_array[INTERP_INTVLS] = y;
  z_array[INTERP_INTVLS] = z;
  
  // uarm.interpolate(cur_hand, hand_angle, hand_array, INTERP_LINEAR);  // TODO: ADD WRIST INTERPOLATIONS LATER
  double time_spend = distance / goalSpeed;   // Speed of the robot in cm/s

  currentStep  = 0;
  goalTime     = millis() + ((long) (time_spend * 1000.0));
  goalTimeStep = abs((time_spend * 1000) / INTERP_INTVLS);  // How long each timestep *should* take

}


bool isTimeToMove(){
  // If not currently in "move" mode, return false
  if (currentStep == 255){
    return false;
  }


  // If it's currently due for another step
  double timeLeft = (long) (goalTime - millis());
  if (timeLeft / (INTERP_INTVLS - currentStep)    <     goalTimeStep) {
    return true;
  }


  // If the robot has run out of time, then of course it has to move immediately
  if(timeLeft <= 0){
    return true;
  }

  return false;
}


void moveStep() {
  //  Move one 'step' towards the desired location, but only if the timing is right
  
  
  //Actually perform the step
  double rot, left, right; 
  
  // Find target angle for the step, and write it
  uarm.calAngles(x_array[currentStep], y_array[currentStep], z_array[currentStep], rot, left, right);
   

  uarm.writeAngle(rot, left, right, uarm.cur_hand);
  currentStep += 1;
  

  if (currentStep == INTERP_INTVLS) { 
    // Make the final move, to ensure arrival to the final destination.
    uarm.calAngles(x_array[INTERP_INTVLS], y_array[INTERP_INTVLS], z_array[INTERP_INTVLS], rot, left, right);
    uarm.writeAngle(rot, left, right, uarm.cur_hand);
    currentStep = 255;
  }

  // Just in case something bad happens, make sure currentStep is at 255 so the robot won't move
  if(currentStep > INTERP_INTVLS){
    currentStep = 255;
  }
}
