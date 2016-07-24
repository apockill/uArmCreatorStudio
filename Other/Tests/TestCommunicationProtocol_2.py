from Logic import CommunicationProtocol_2 as UArmLibrary
from time import sleep
import sys

# Get all plugged in uArms
connecteduArms = UArmLibrary.getConnectedRobots()
sleep(.1)
print("Open Ports: ", connecteduArms)


# If no robots were found, exit the script
if len(connecteduArms) == 0:
    print("No robots found!")
    sys.exit()


# Connect to the first robot, and make sure it connected correctly
chosenPort = connecteduArms[0][0]
print("Attempting to connect to port ", chosenPort)
uarm = UArmLibrary.Device(chosenPort) # , printCommands=True, printResponses=True)
if not uarm.connected():
    print("uArm could not connect!")
    sys.exit()
print("Beginning Testing")




print("\nTest setMove")
print("Move To (0, 150, 150)")
uarm.setXYZ(0, 150, 150, .7)
while uarm.getMoving(): sleep(.1)

print("Move To (-150, 150, 150)")
uarm.setXYZ(-150, 150, 150, .7)
while uarm.getMoving(): sleep(.1)

print("Move To (0, 150, 100)")
uarm.setXYZ(0, 150, 100, .7)
while uarm.getMoving(): sleep(.1)

print("Move To (150, 150, 150)")
uarm.setXYZ(150, 150, 150, .7)
while uarm.getMoving(): sleep(.1)

print("Move To (0, 150, 250)")
uarm.setXYZ(0, 150, 250, .7)
while uarm.getMoving(): sleep(.1)


print("\nTest setPolar")
print("Move To (200, 30, 200))")
uarm.setPolar(200, 30, 200, .7)
while uarm.getMoving(): sleep(.1)
print("Move To (200, 150, 200))")
uarm.setPolar(200, 150, 200, .7)
while uarm.getMoving(): sleep(.1)
print("Move To (200, 90, 200))")
uarm.setPolar(200, 110, 200, .7)
while uarm.getMoving(): sleep(.1)


print("\nTesting SetServo")
print("Setting Servo 0")
uarm.setServo(0, 100)
print("Setting Servo 1")
uarm.setServo(1, 80)
print("Setting Servo 2")
uarm.setServo(2, 45)
sleep(.5)
print("Setting Servo 0")
uarm.setServo(0, 90)
print("Setting Servo 1")
uarm.setServo(1, 70)
print("Setting Servo 2")
uarm.setServo(2, 35)
sleep(.5)


print("\nTesting setPump")
print("Turning on Pump")
uarm.setPump(True)
sleep(.5)
print("Turning off Pump")
uarm.setPump(False)
sleep(.5)


print("\nTesting Detach Servos")
uarm.setServoDetach(0)
uarm.setServoDetach(1)
uarm.setServoDetach(2)
uarm.setServoDetach(3)
sleep(.5)


print("\nTesting Attach Servos")
uarm.setServoAttach(0)
uarm.setServoAttach(1)
uarm.setServoAttach(2)
uarm.setServoAttach(3)
sleep(.5)


print("\nTesting Buzzer")
uarm.setBuzzer(1500, .15)
sleep(.15)


print("\nTest Various 'get' Commands")
print("Servo Angles: ", uarm.getServoAngles())
print("XYZ Coords:   ", uarm.getXYZCoords())
print("Polar Coords: ", uarm.getPolarCoords())
print("Tip Sensor:   ", uarm.getTipSensor())
print("Version:      ", uarm.getVersion())

print("\nTest XYZ Coordinate Simulation, Good and Bad values")
print("Test XYZ       (  0, 150, 150): ", uarm.getReachableXYZ(0, 150, 150))
print("Test XYZ   (1000, 1000, 1000): ", uarm.getReachableXYZ(1000, 1000, 1000))

print("\nTest Polar Coordinate Simulation, Good and Bad values")
print("Test Polar     (150,  90, 150): ", uarm.getReachablePolar(150, 90, 150))
print("Test Polar (1000, 1000, 1000): ", uarm.getReachablePolar(1000, 1000, 1000))

print("\nTest Forward/Backwrd Kinematics")
print("Get Forward Kinematics  (90, 70, 35): ", uarm.getFK(90, 70, 35))
print("Get Inverse Kinematics (0, 150, 150): ", uarm.getIK(0, 150, 150))


print("Testing Over")




