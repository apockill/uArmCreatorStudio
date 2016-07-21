"""
This software was designed by Alexander Thiel
Github handle: https://github.com/apockill

The software was designed originaly for use with a robot arm, particularly uArm (Made by uFactory, ufactory.cc)
It is completely open source, so feel free to take it and use it as a base for your own projects.

If you make any cool additions, feel free to share!


License:
    This file is part of uArmCreatorStudio.
    uArmCreatorStudio is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    uArmCreatorStudio is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with uArmCreatorStudio.  If not, see <http://www.gnu.org/licenses/>.
"""
__author__ = "Alexander Thiel"

import serial
import serial.tools.list_ports
from time         import sleep, time  # Used only in connecting to the robot, while waiting for serial to connect.
from Logic.Global import printf

# This is a library for controlling uArms that have Alex Thiel's Arduino communication protocol uploaded
def getConnectedRobots():
    # Returns any arduino serial ports in a list [port, port, port]
    # This is used to let the user choose the correct port that is their robot
    ports = list(serial.tools.list_ports.comports())
    return ports


class Device:

    def __init__(self, port, printCommands=True, printResponses=True):
        self.printCommands  = printCommands
        self.printResponses = printResponses
        self.isConnected    = False
        self.serial         = None
        self.__connectToRobot(port)

        # For debug logs
        # An array of tuples, of what was sent, what was recieved
        # [(sent, recieved), (sent, recieved), (sent, recieved)]
        self.communicationLog = []

    def connected(self):
        # if self.serial is None:     return False
        if self.isConnected is False: return False
        # if not self.__handshake():  return False
        return True


    # Action commands
    def moveToWithSpeed(self, x, y, z, speed):
        # Flip the Y axis to keep the coordinates somewhat sane
        x = str(round(   -x, 2))
        y = str(round(   -y, 2))
        z = str(round(    z, 2))
        t = str(round(speed, 2))
        cmnd = "moveX" + x + "Y" + y + "Z" + z + "S" + t
        # return
        return self.__send(cmnd)

    def setGripper(self, onOff):
        # Set the gripper to a value 1 or 0, where 1 means "gripping" and 0 mean "off"
        cmnd = "pumpV" + str(int(onOff))
        return self.__send(cmnd)

    def setServo(self, servo, angle):
        # Set a servo to an angle #
        angle = str(float(round(angle, 3)))
        cmnd = "ssS" + str(int(servo)) + "V" + angle
        return self.__send(cmnd)

    def servoAttach(self, servo_number):

        servo_number = str(int(servo_number))
        cmnd = "attachS" + servo_number
        return self.__send(cmnd)

    def servoDetach(self, servo_number):
        servo_number = str(int(servo_number))
        cmnd = "detachS" + servo_number
        return self.__send(cmnd)

    def setBuzzer(self, frequency, duration):
        cmnd = "buzzF" + str(frequency) + "T" + str(duration)
        return self.__send(cmnd)


    # Get commands
    def getIK(self, x, y, z):
        # Gets the servo1, servo2, and servo3 calculated positions for the XYZ position

        x = str(round(   -x, 2))
        y = str(round(   -y, 2))
        z = str(round(    z, 2))
        cmnd = "gikX" + x + "Y" + y + "Z" + z
        response = self.__send(cmnd)
        parsedArgs = self.__parseArgs(response, "ik", ["A", "B", "C"])

        # Return (servo1Angle, servo2Angle, servo3Angle)
        return parsedArgs["A"], parsedArgs["B"], parsedArgs["C"]

    def getFK(self, servo0, servo1, servo2):
        # Gets the X, Y, and Z calculated positions for the servo angles servo0, servo1, servo2

        servo0 = str(round(servo0, 2))
        servo1 = str(round(servo1, 2))
        servo2 = str(round(servo2, 2))
        cmnd = "gfkA" + servo0 + "B" + servo1 + "C" + servo2
        response = self.__send(cmnd)
        parsedArgs = self.__parseArgs(response, "fk", ["X", "Y", "Z"])

        # Return (X, Y, Z)
        return parsedArgs["X"], -parsedArgs["Y"], parsedArgs["Z"]

    def getCurrentCoords(self):
        # Returns an array of the format [x, y, z] of the robots current location
        response  = self.__send("gcrd")
        parsedArgs = self.__parseArgs(response, "crd", ["X", "Y", "Z"])

        # Return (currX, currY, currZ)
        return -parsedArgs["X"], -parsedArgs["Y"], parsedArgs["Z"]

    def getIsMoving(self):
        # Find out if the robot is currently moving
        response  = self.__send("gmov")
        parsedArgs = self.__parseArgs(response, "mov", ["M"])


        # Return True if moving, False if not moving
        return (False, True)[int(parsedArgs['M'])]

    def getServoAngles(self):
        # Get the angles of each servo

        cmnd = "gang"
        response = self.__send(cmnd)
        parsedArgs = self.__parseArgs(response, "ang", ["A", "B", "C", "D"])

        # Return angles of each servo in order
        return parsedArgs["A"], parsedArgs["B"], parsedArgs["C"], parsedArgs["D"]

    def getTipSensor(self):
        # Find out if the robot is currently moving
        response  = self.__send("gtip")
        parsedArgs = self.__parseArgs(response, "tip", ["V"])

        # Returns 0 or 1, whether or not the tip sensor is currently activated
        return (True, False)[int(parsedArgs['V'])]  # Return True or False


    # Not to be used outside of library
    def __connectToRobot(self, port):
        try:
            self.serial = serial.Serial(port     = port,
                                        baudrate = 115200,
                                        parity   = serial.PARITY_NONE,
                                        stopbits = serial.STOPBITS_ONE,
                                        bytesize = serial.EIGHTBITS,
                                        timeout  = .1)
            self.isConnected = True
        except serial.SerialException as e:
            printf("Could not connect to robot on port ", port)
            self.serial = None
            self.isConnected = False
        sleep(3)

    def __send(self, cmnd):
        # This command will send a command and recieve the robots response. There must always be a response!
        if not self.connected(): return ""

        # Prepare and send the command to the robot
        cmndString = bytes("[" + cmnd + "]\n", encoding='ascii')

        try:
            self.serial.write(cmndString)
        except serial.serialutil.SerialException as e:
            printf("ERROR ", e, "while sending command ", cmnd, ". Disconnecting Serial!")
            self.isConnected = False
            return ""


        # Read the response from the robot (THERE MUST ALWAYS BE A RESPONSE!)
        response = ""
        while True:

            try:
                response += str(self.serial.read(), 'ascii')
            except serial.serialutil.SerialException as e:
                printf("ERROR ", e, "while sending command ", cmnd, ". Disconnecting Serial!")
                self.isConnected = False
                return ""

            if "\n" in response:
                response = response[:-1]
                break

        if self.printCommands and self.printResponses:
            printf("[" + cmnd + "]" + " " * (30 - len(cmnd)) + response)
        elif self.printCommands:
            printf(cmndString)
        elif self.printResponses:
            printf(response)


        # Save the response to a log variable, in case it's needed for debugging
        self.communicationLog.append((cmnd, response))

        # Make sure the respone has the valid start and end characters
        if not (response.count('[') == 1 and response.count(']') == 1):
            printf("ERROR: The message ", response, " did not come with proper formatting!")


        # Clean up the response
        response = response.replace("[", "")
        response = response.replace("]", "")



        # If the robot returned an error, print that out
        if "error" in response:
            printf("ERROR: Recieved error from robot: ", response)


        return response

    def __parseArgs(self, message, command, arguments):
        responseDict = {n: 0 for n in arguments}  #Fill the dictionary with zero's


        # Do error checking, in case communication didn't work
        if message is False:
            printf("Since an error occured in communication, returning 0's for all arguments!")
            return responseDict

        if command not in message:
            printf("ERROR: The message did not come with the appropriate command: ", command)
            return responseDict


        # Get rid of the "command" part of the message, so it's just arguments and their numbers
        message = message.replace(command, "")


        # Get the arguments and place them into the array
        for i, arg in enumerate(arguments):
            if i < len(arguments) - 1:
                responseDict[arg] = message[message.find(arg) + 1: message.find(arguments[i + 1])]
            else:
                responseDict[arg] = message[message.find(arg) + 1:]

            responseDict[arg] = float(responseDict[arg])

        return responseDict

    def __strAndRound(self, num, roundTo):
        # Parses a number so it takes the fewest amount of bits (Trailing zero's are removed
        num = float(round(num, roundTo))

    # def __uploadCode(self):
    #     self.serial.setDTR(0)
    #     sleep(0.1)
    #     self.serial.setDTR(1)



