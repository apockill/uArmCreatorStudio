#uArm Communication Protocol
## Protocol rules
- Baudrate: 115200
- All Commands must include in \[\], end with line break
- Response messages: start with **s** means succeed, **f** means failed.
- Two types of commands, **set** commands and **get** commands.

## Commands Format
-  \[sMovX#Y#Z#V#\]  Set the coordinates
	Where # is a double, This will move the robot to an XYZ position, in S is speed in  mm/s from the current location to goal location
				  Send Example:   \[sMovX150Y150Z100V300\]\\n   //y is positive  xyz are in mm,V from 100-1000mm/s
				  Return Example: \[S\]\\n or \[F\]  S:SUCCEED F:OUT OF RANGE(but will go to the closest point)

-  \[sPolS#R#H#V#\]  Set the polar coordinates
				  Send Example:   \[sPolS150R50H100V300\]\\n  S&H MEANS STRETCH AND HEIGHT(in mm),R MEANS ROT(in degree),V from 100-1000mm/s
		  Return Example: \[S\] or \[F\]

 - \[gPol\]          Get the polar coordinates
				  Send Example:   \[gPol\]\\n
		  Return Example: \[SS100R50H100\]\\n   S&H MEANS STRETCH AND HEIGHT(in mm),R MEANS ROT(in degree)

  - \[gSimX#Y#Z#V#\]  Validate the coordinate
	Where # is a double, This will caculate if the robot can arrive the XYZ position
		  Send Example:   \[gSimX0Y120Z100V0\]\\n          V1 MEANS THE POLAR COORDINATES TRUE(stretch height and rot)
  		  Return Example: \[S0\]\\n or \[F0\]\\n or \[F1\]\\n    F1:FAIL IN THE PATH   F0:FAIL IN THE DESTINATION   S0:SUCCEED

 - \[gVer\]          Return the version of the firmware
				  Send Example:   \[gVer\]\\n
		  Return Example: \[vH2-1.3.4\]\\n

  - \[sSerN#V#\]      Set Raw Servo Angle no offset
	Where S# is the servo number and V# is an angle between 0 and 180. This will set the angle of that particular servo
				  Send Example:   \[sSerN1V10\]\\n
				  Return Example: \[S\]

	- \[sAngN#V#\]      Set  Servo Angle with offset
	Where S# is the servo number and V# is an angle between 0 and 180. This will set the angle of that particular servo
				  Send Example:   \[sAngN1V10\]\\n
				  Return Example: \[S\]					

 - \[sPumV#\]       Set Pump
	 Where # is either 1 or 0. 1 means pump on, 0 means pump off.
				  Send Example:   \[sPumV1\]\\n
				  Return Example: \[S\]

 - \[gPum\]	  Get back the status of the pump
				  Send Example:   \[gPum\]\\n
				  Return Example: \[S0\]\\n or \[S1\]\\n or \[S2\]\\n   S0:GRAB THE THINGS   S1:PUMP ON   S2:PUMP OFF

  - \[sGriV#\]        Set Gripper
		Where # is either 1 or 0. 1 means gripper on, 0 means gripper off.
				  Send Example:   \[sGriV1\]\\n
				  Return Example: \[S\]

  - \[gGri\]	  Get back the status of the gripper
				  Send Example:   \[gGri\]\\n
				  Return Example: \[S0\]\\n or \[S1\]\\n or \[S2\]\\n   S0:GRAB THE THINGS   S1:GRIPPER ON   S2:GRIPPER OFF

  - \[sAttN#\]        Attach servo #. Same as servo #'s in uarm_library.h
				  Send Example:   \[sAttN1\]\\n
				  Return Example: \[S\]\\n or \[F\]\\n  S:SUCCESS   F:WRONG NUMBER

 - \[sDetN#\]      Detach servo #. Same as servo #'s in uarm_library.h
				  Send Example:   \[sDetN1\]\\n
				  Return Example: \[S\]\\n or \[F\]\\n   S:SUCCESS   F:WRONG NUMBER

  - \[gCrd\]          Returns the XYZ coordinate position of the robot
				  Send Example:   \[gCrd\]\\n
				  Return Example: \[SX#Y#Z#\]

  - \[gAng\]          Returns the servo angles with offset of all the servos in the robot and returns them as angleA#B#C#D# where ABCD are servos 0,1,2,3 respectively
				  Send Example:   \[gAng\]\\n
				  Return Example: \[SB#L#R#H#\]

	- \[gSer\]          Returns the RAW angle no offset of all the servos in the robot and returns them as angleA#B#C#D# where ABCD are servos 0,1,2,3 respectively
				  Send Example:   \[gAng\]\\n
				  Return Example: \[SB#L#R#H#\]					

 - \[gIKX#Y#Z#\]     Returns the inverse kinematics for XYZ point in the form A#B#C# where ABC are servos 0,1,2 respectively
				  Send Example:   \[gIKX0Y150Z150\]\\n
				  Return Example: \[ST90L15R80\]

  - \[gFKT#L#R#\]     Returns the forward kinematics for TLR servo angles in the form X#Y#Z# where TLR are servos 0,1,2 respectively
				  Send Example:   \[gFKT190L150R80\]\\n
				  Return Example: \[SX0Y-15Z15\]

  - \[gMov\]          Returns whether or not the robot is currently moving. Returns either 1 or 0 if it is moving or not.
				  Send Example: \[gMov\]\\n
				  Return Example: \[S\] or \[F\]  S:PROCESSING F:FREE

  - \[gTip\]          Returns whether or not the tip of the robot is currently pressed. Returns either 1 if the tip is pressed, 0 if not.
				  Send Example: \[gTip\]\\n
				  Return Example: \[S0\] or \[S1\]  S0:OFF S1:ON

  - \[sBuzF#T#\]      Set the buzzer to F Frequency for T time
				  Send Example:   \[sBuzzF1000T1\]\\n
				  Return Example: \[S\] or \[F\]  S:SUCCESS  F:WRONG NUMBER

  - \[sStp\]          Stop the movement immediately
				  Send Example:   \[sStp\]\\n
				  Return Example: \[S\]

  - \[gPow\]          Get the status of power connection
				  Send Example:   \[gPow\]\\n
				  Return Example: \[S\] or \[F\]
 - \[gEEPA#T#\]   Get data from EEPROM
				A# means address, address between 0 and 64 \* 1024
				T# means data type, **1** means Byte, **2** means Integer, **4** means float
				Send Example: \[gEEPRA1000T1\]\\n
				Return Example: \[S100\]\\n
- \[sEEPA#T#V#\] Set Data to EEPROM
				A# Means Address, address between 0 and 64 \* 1024
				T# means data type, **1** means Byte, **2** means Integer, **4** means float
				V#, if T is 1, V data type is byte, if T is 2, V data type is Integer, if T is 4, V data type is float
				Send Example: \[sEEPRA1000T1V20\]\n
				return Example: \[S\]
	- \[gAnaN#\] Get Analog value from PIN
				N# Means Pin, from 1 to 13.
				Send Examples: \[gAnaN7\]\\n
				Return Examples: \[S435\]\\n


## ERRORS:
 - \[ERR1\]          Your command was missing a parameter

  - \[ERR2\]          Your command was missing a value for a parameter

  - \[ERR3\]	  The command does not exist
