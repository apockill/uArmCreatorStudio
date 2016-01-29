import serial
import math
from time import sleep


print "Setting up serial"
ser1 = serial.Serial("COM11", 115200, timeout=0)
sleep(1)


def moveTo(**kwargs):
    """
    Accepts inputs of X, Y, and Z
    """
    x = kwargs.get("x", None)
    y = kwargs.get("y", None)
    z = kwargs.get("z", None)

    buildString = "G0"
    if not x is None and isinstance(x, int):
        buildString += "X" + str(x)
    if not y is None and isinstance(y, int):
        buildString += "Y" + str(y)
    if not z is None and isinstance(z, int):
        buildString += "Z" + str(z)

    print "Sending ", buildString
    ser1.write(buildString + "\n")

def setColor(r, g, b, servos):
    """
    Servos is a list [] where [0, 1, 2] would be servos 0, 1, and 2, and would be setting the RGB for
    those servos to the r, g, b, variables.
    """

    buildString = ""
    for servo in servos:
        buildString += "S15 I" + str(servo) + " V" + str(r) + "\n"
        buildString += "S16 I" + str(servo) + " V" + str(g) + "\n"
        buildString += "S17 I" + str(servo) + " V" + str(b) + "\n"

    print "Final string: ", buildString
    ser1.write(buildString + "\n")

def getResponse():
    noResponse = 0   #How many times serial.readAll() has returned nothing. 3 times and the function will quit

    buildString = ""  #A string of all responses recieved
    while noResponse < 10:
        sleep(.1)
        response = ser1.readall()

        if response == "":
            noResponse += 1
        else:
            buildString += response + "     |     "

    return buildString





print "Connecting to robot"
ser1.write("M105\n")
sleep(1)


print "Sending Test Command"
ser1.write("G0X0Y0Z0F20000\n")


print "Beginning Loop"
while True:
    ser1.write(raw_input("Command? "))
    #moveTo(y=int(raw_input("Y: ")), z=int(raw_input("Z: ")))
    #setColor(int(raw_input("R: ")), int(raw_input("G: ")), int(raw_input("B: ")), [1, 2])

    print "Prompting Current angles: "
    ser1.write("S25I0\nS25I1\nS25I2\n")
    sleep(.1)
    print "Response: ", getResponse()