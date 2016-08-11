/******************************************************************************************
  File Name          : movement.ino
  Author             : Dave Corboy
  Version            : V1.0
  Date               : 24 Feb, 2016
  Modified Date      : 28 Feb, 2016
  Description        : uArm Metal Movement Type Demo
*******************************************************************************************/

#include <Wire.h>
#include <uarm_library.h>

// states
#define MOVEMENT     0
#define SERVO_CACHE  1
#define PATHING      2
#define EASING       3
#define HAND_REL     4

byte state;

void setup() {
  Wire.begin();        // join i2c bus (address optional for master)
  Serial.begin(9600);  // start serial port at 9600 bps

  // uArm init
  pinMode(STOPPER, INPUT_PULLUP);  digitalWrite(STOPPER, HIGH);
  pinMode(BTN_D4,   INPUT_PULLUP);  digitalWrite(BTN_D4,   HIGH);
  pinMode(BTN_D7,   INPUT_PULLUP);  digitalWrite(BTN_D7,   HIGH);
  pinMode(BUZZER,   OUTPUT); digitalWrite(BUZZER,   LOW);
  pinMode(PUMP_EN,  OUTPUT); digitalWrite(PUMP_EN,  LOW);
  pinMode(VALVE_EN, OUTPUT); digitalWrite(VALVE_EN, LOW);
  // uArm init

  alert(2);
  change_state(MOVEMENT);
}

void loop() {
  if (Serial.available() > 0) {
    byte input = Serial.read();
    switch (state) {
      case MOVEMENT :
        if (input == 's') {
          change_state(SERVO_CACHE);
        } else if (input == 'p') {
          change_state(PATHING);
        } else if (input == 'e') {
          change_state(EASING);
        } else if (input == 'h') {
          change_state(HAND_REL);
        }
        break;
      case SERVO_CACHE :
        if (input == 'q') {
          change_state(MOVEMENT);
        } else if (input == 'b') {
          // detaching the servos after each move forces the cache to be recalculated, generating the errors
          many_xyz_start_points(true);
          move_home_position(.5);
        } else if (input == 'a') {
          // without detaching, the servo angle cache remains in place and initial movement has less jitter
          many_xyz_start_points(false);
          move_home_position(.5);
        }
        break;
      case PATHING :
        if (input == 'q') {
          change_state(MOVEMENT);
        } else if (input == 'l') {
          path_moves(PATH_LINEAR); // PATH_LINEAR creates a linear path between the start end and point
        } else if (input == 'a') {
          path_moves(PATH_ANGLES); // PATH_ANGLES instead interpolates the start and ending servos positions
        }
        break;
      case EASING :
        if (input == 'q') {
          change_state(MOVEMENT);
        } else if (input == 'c') {
          ease_moves(INTERP_EASE_INOUT_CUBIC);
        } else if (input == 'e') {
          ease_moves(INTERP_EASE_INOUT);
        } else if (input == 'i') {
          ease_moves(INTERP_EASE_IN);
        } else if (input == 'o') {
          ease_moves(INTERP_EASE_OUT);
        } else if (input == 'l') {
          ease_moves(INTERP_LINEAR);
        }
        break;
      case HAND_REL :
        if (input == 'q') {
          change_state(MOVEMENT);
        } else if (input == 'n') {
          hand_moves(F_ABSOLUTE);
        } else if (input == 'r') {
          hand_moves(F_HAND_ROT_REL);
        }
        break;
    }
  }
}

void change_state(byte new_state) {
  switch (new_state) {
    case MOVEMENT :
      Serial.println(F("This sketch demonstrates the changes added to uArm movement functions."));
      Serial.println(F("Select an item for demonstration:"));
      Serial.println(F("(s) Servo caching"));
      Serial.println(F("(p) Path options"));
      Serial.println(F("(e) Easing of movement"));
      Serial.println(F("(h) Hand-relative orientation"));
      move_home_position(1);
      break;
    case SERVO_CACHE :
      Serial.println(F("Servo values are now cached to remove readAngle error introduced at the beginning of a move."));
      Serial.println(F("(b) Before servo caching"));
      Serial.println(F("(a) After servo caching"));
      Serial.println(F("(q) Quit to top menu"));
      break;
    case PATHING :
      Serial.println(F("In addition to the original linear path, a new option to interpolate"));
      Serial.println(F("servo angles can sometimes offer smoother, non-linear movement."));
      Serial.println(F("(l) Linear path demo"));
      Serial.println(F("(a) Angular path demo"));
      Serial.println(F("(q) Quit to top menu"));
      break;
      break;
    case EASING :
      Serial.println(F("Several new movement easing function have also been added."));
      Serial.println(F("(c) Original cubic easing"));
      Serial.println(F("(e) Quadratic ease-in/ease-out"));
      Serial.println(F("(i) Quadratic ease-in only"));
      Serial.println(F("(o) Quadratic ease-out only"));
      Serial.println(F("(l) Linear (no easing)"));
      Serial.println(F("(q) Quit to top menu"));
      break;
      break;
    case HAND_REL :
      Serial.println(F("Hand rotation can automatically maintain orientation through base rotation."));
      Serial.println(F("(n) No hand orientation"));
      Serial.println(F("(r) Rotation-relative hand"));
      Serial.println(F("(q) Quit to top menu"));
      break;
  }
  Serial.println();
  state = new_state;
}

void alert(byte beeps) {
  uarm.alert(beeps, 50, 50);
}

void move_home_position(float time) {
  uarm.moveToOpts(0, -21, 20, 90, F_ABSOLUTE, time, PATH_ANGLES, INTERP_EASE_INOUT);
}

void many_xyz_start_points(bool recalc_servos) {
  // detaching the servos after each move forces the cache to be recalculated, generating the errors
  // this mimics the previous behavior where positions were always recalculated between moves
  if (recalc_servos) {
    uarm.detachAll();
  }
  uarm.moveToOpts(-14, -19, 20, 90, F_ABSOLUTE, .5, PATH_ANGLES, INTERP_EASE_INOUT);
  if (recalc_servos) {
    uarm.detachAll();
  }
  delay(500);
  uarm.moveToOpts(-7, -26, 14, 90, F_ABSOLUTE, .5, PATH_ANGLES, INTERP_EASE_INOUT);
  if (recalc_servos) {
    uarm.detachAll();
  }
  delay(500);
  uarm.moveToOpts(0, -19, 20, 90, F_ABSOLUTE, .5, PATH_ANGLES, INTERP_EASE_INOUT);
  if (recalc_servos) {
    uarm.detachAll();
  }
  delay(500);
  uarm.moveToOpts(7, -26, 14, 90, F_ABSOLUTE, .5, PATH_ANGLES, INTERP_EASE_INOUT);
  if (recalc_servos) {
    uarm.detachAll();
  }
  delay(500);
  uarm.moveToOpts(14, -19, 20, 90, F_ABSOLUTE, .5, PATH_ANGLES, INTERP_EASE_INOUT);
  if (recalc_servos) {
    uarm.detachAll();
  }
  delay(500);
}

void path_moves(byte path_type) {
  // PATH_LINEAR creates a linear path between the start end and point
  // PATH_ANGLES instead interpolates the start and ending servos positions
  uarm.moveToOpts(-7, -14, 10, 90, F_ABSOLUTE, 1, path_type, INTERP_EASE_INOUT);
  delay(500);
  uarm.moveToOpts(15, -26, 20, 90, F_ABSOLUTE, 1, path_type, INTERP_EASE_INOUT);
  delay(500);
  uarm.moveToOpts(-15, -26, 20, 90, F_ABSOLUTE, 1, path_type, INTERP_EASE_INOUT);
  delay(500);
  uarm.moveToOpts(7, -14, 10, 90, F_ABSOLUTE, 1, path_type, INTERP_EASE_INOUT);
  delay(500);
  uarm.moveToOpts(0, -21, 20, 90, F_ABSOLUTE, 1, path_type, INTERP_EASE_INOUT);
}

void ease_moves(byte ease_type) {
  uarm.moveToOpts(-10, -26, 15, 90, F_ABSOLUTE, 1, PATH_ANGLES, INTERP_EASE_INOUT);
  delay(750);
  uarm.moveToOpts(10, -26, 15, 90, F_ABSOLUTE, .75, PATH_ANGLES, ease_type);
  delay(500);
  uarm.moveToOpts(10, -14, 15, 90, F_ABSOLUTE, .75, PATH_ANGLES, ease_type);
  delay(500);
  uarm.moveToOpts(-10, -14, 15, 90, F_ABSOLUTE, .75, PATH_ANGLES, ease_type);
  delay(500);
  uarm.moveToOpts(-10, -26, 15, 90, F_ABSOLUTE, .75, PATH_ANGLES, ease_type);
  delay(750);
  uarm.moveToOpts(0, -21, 20, 90, F_ABSOLUTE, 1, PATH_ANGLES, INTERP_EASE_INOUT);
}

void hand_moves(byte relative) {
  // F_HAND_ROT_REL will keep the hand orientation contstant through a move
  uarm.moveToOpts(-15, -15, 12, relative ? 0 : 90, relative, 1, PATH_ANGLES, INTERP_EASE_INOUT);
  delay(500);
  uarm.moveToOpts(-15, -15, 8, relative ? 0 : 90, relative, .5, PATH_ANGLES, INTERP_EASE_INOUT);
  delay(500);
  uarm.moveToOpts(-15, -15, 17, relative ? 0 : 90, relative, .5, PATH_ANGLES, INTERP_EASE_INOUT);
  delay(500);
  uarm.moveToOpts(15, -15, 17, relative ? 0 : 90, relative, 2, PATH_ANGLES, INTERP_EASE_INOUT);
  delay(500);
  uarm.moveToOpts(15, -15, 8, relative ? 0 : 90, relative, .5, PATH_ANGLES, INTERP_EASE_INOUT);
  delay(500);
  uarm.moveToOpts(0, -21, 20, 90, F_ABSOLUTE, 1, PATH_ANGLES, INTERP_EASE_INOUT);
}

