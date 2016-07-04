from RobotGUI.Logic import UArmTextCommunication_1 as UArmLibrary
from time import sleep
import sys

# Get all plugged in uArms
connecteduArms = UArmLibrary.getConnectedRobots()


# If no robots were found, exit the script
if len(connecteduArms) == 0:
    print("No robots found!")
    sys.exit()


# Connect to the first robot, and make sure it connected correctly
uarm = UArmLibrary.Uarm(connecteduArms[0][0], printResponses=True)
if not uarm.connected():
    print("uArm could not connect!")
    sys.exit()


print("Starting various tests!")

# Pump commands
uarm.gripperOn()
sleep(1)
uarm.gripperOff()



# Move to XYZ (0, -15, 15) at a speed of 20 centimeters per second
print("Moving to 0, -15, 15")
uarm.moveToWithSpeed(  0, -15, 15, 20)


while uarm.getIsMoving(): sleep(.1)
uarm.moveToWithSpeed(-10, -15, 15, 20)


while uarm.getIsMoving(): sleep(.1)
uarm.moveToWithSpeed( 10, -15, 15, 20)


while uarm.getIsMoving(): sleep(.1)
uarm.moveToWithSpeed( 0, -10, 20, 20)



# Turn on the buzzer for .5 seconds, at a frequency of 500 Hz
print("Turning on buzzer")
uarm.setBuzzer(500, .5)


# "Get" commands
print("Current XYZ:        ", uarm.getCurrentCoord())
print("Tip Sensor Pressed: ", uarm.getTipSensor())
print("Servo 0 angle:      ", uarm.getServoAngle(0))
print("Servo 1 angle:      ", uarm.getServoAngle(1))
print("Servo 2 angle:      ", uarm.getServoAngle(2))
print("Servo 3 angle:      ", uarm.getServoAngle(3))


print("Moving wrist")
uarm.moveWrist(180)
sleep(1)
uarm.moveWrist(0)
sleep(1)
uarm.moveWrist(90)