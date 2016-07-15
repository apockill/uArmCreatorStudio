from Logic import CommunicationProtocol as UArmLibrary
from collections import Counter  # For debugging
from time import sleep
import sys

# Get all plugged in uArms
connecteduArms = UArmLibrary.getConnectedRobots()


# If no robots were found, exit the script
if len(connecteduArms) == 0:
    print("No robots found!")
    sys.exit()


# Connect to the first robot, and make sure it connected correctly
uarm = UArmLibrary.Device(connecteduArms[0][0], printResponses=True)
if not uarm.connected():
    print("uArm could not connect!")
    sys.exit()


print("Starting various tests!")

# Pump commands
uarm.setGripper(True)
sleep(1)
uarm.setGripper(False)



# Move to XYZ (0, -15, 15) at a speed of 20 centimeters per second
print("Moving to 0, 15, 15")
uarm.moveToWithSpeed(  0, 15, 15, 20)


while uarm.getIsMoving(): sleep(.1)
uarm.moveToWithSpeed(-10, 15, 15, 20)


while uarm.getIsMoving(): sleep(.1)
uarm.moveToWithSpeed( 10, 15, 15, 20)


while uarm.getIsMoving(): sleep(.1)
uarm.moveToWithSpeed( 0, 10, 20, 20)



# Turn on the buzzer for .5 seconds, at a frequency of 500 Hz
uarm.setBuzzer(500, .05)


# Test gripper on/off commands
uarm.setGripper(True)
sleep(1)
uarm.setGripper(False)

# Test attach/detach commands
uarm.servoDetach(0)
uarm.servoDetach(1)
uarm.servoDetach(2)
uarm.servoDetach(3)
sleep(1)
uarm.servoAttach(0)
uarm.servoAttach(1)
uarm.servoAttach(2)
uarm.servoAttach(3)
sleep(.5)

# Test "Get" commands
print("IK for X0Y-15Z15:        ", uarm.getIK(0, 15, 15))
print("FK for A90B85.15Z43.45:  ", uarm.getFK(90, 85.15, 43.45))
print("Current XYZ:             ", uarm.getCurrentCoord())
print("Is Moving:               ", uarm.getIsMoving())
print("Tip Sensor Pressed:      ", uarm.getTipSensor())
print("Servo angles:            ", uarm.getServoAngles())



# Test "setServo" command by moving the wrist around a bit
uarm.setServo(3, 180)
sleep(1)
uarm.setServo(3, 0)
sleep(1)
uarm.setServo(3, 90)


# Print a list of "Call" and "Response" for this test
print("Response Log: ", uarm.communicationLog)