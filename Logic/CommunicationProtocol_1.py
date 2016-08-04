"""
This software was designed by Alexander Thiel
Github handle: https://github.com/apockill
Email: Alex.D.Thiel@Gmail.com


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
import serial
import serial.tools.list_ports
from time         import sleep, time  # Used only in connecting to the robot, while waiting for serial to connect.
from Logic.Global import printf
__author__ = "Alexander Thiel"

# This is a library for controlling uArms that have Alex Thiel's Arduino communication protocol uploaded
def getConnectedRobots():
    # Returns any arduino serial ports in a list [port, port, port]
    # This is used to let the user choose the correct port that is their robot
    ports = list(serial.tools.list_ports.comports())
    return ports


class Device:

    def __init__(self, port, printCommands=True, printResponses=True):
        """
        :param port: The COM port that the robot is plugged in to.
        :param printCommands: If true, then print any strings that are sent to the robot
        :param printResponses: If true, then print the responses from the robot.
        """
        self.printCommands  = printCommands
        self.printResponses = printResponses
        self.isConnected    = False
        self.serial         = None
        self.__connectToRobot(port)

        # For debug logs
        # An array of tuples, of what was sent, what was recieved
        # [(sent, recieved), (sent, recieved), (sent, recieved)]
        self.communicationLog = []


    ######      The following functions are used outside of this library. Make sure they are implimented!     #####
    def connected(self):
        # if self.serial is None:     return False
        if self.isConnected is False: return False
        # if not self.__handshake():  return False
        return True


    # Action commands
    def setXYZ(self, x, y, z, speed):
        """
        Set the robots current move.
        :param x: centimeters
        :param y: centimeters
        :param z: centimeters
        :param speed: centimeters per second, how fast the robot should move towards its end point
                      If you have tuning, then just calculate the average speed.
        """

        # Flip the Y axis to keep the coordinates somewhat sane
        x = str(round(   -x, 2))
        y = str(round(   -y, 2))
        z = str(round(    z, 2))
        t = str(round(speed, 2))
        cmnd = "moveX" + x + "Y" + y + "Z" + z + "S" + t
        # return
        return self.__send(cmnd)

    def setServo(self, servo, angle):
        """
        Set a servo to a particular angle
        :param servo: A servo ID, a number 0, 1, 2, or 3
        :param angle: An angle in degrees between 0 and 180
        :return:
        """

        # Set a servo to an angle #
        angle = str(float(round(angle, 3)))
        cmnd = "ssS" + str(int(servo)) + "V" + angle
        return self.__send(cmnd)


    def setPump(self, onOff):
        """
        Set the pumps value.
        :param onOff: True means turn the gripper on. False means off.
        """

        # Set the gripper to a value 1 or 0, where 1 means "gripping" and 0 mean "off"
        cmnd = "pumpV" + str(int(onOff))
        return self.__send(cmnd)


    def setServoAttach(self, servo_number):
        """
        Attach a certain servo.
        :param servo: The servo's number

        0 should be the base servo. Anything else might vary depending on the arm.
        """

        servo_number = str(int(servo_number))
        cmnd = "attachS" + servo_number
        return self.__send(cmnd)

    def setServoDetach(self, servo_number):
        """
        Detach a certain servo.
        :param servo: The servo's number
        """

        servo_number = str(int(servo_number))
        cmnd = "detachS" + servo_number
        return self.__send(cmnd)

    def setBuzzer(self, frequency, duration):
        """
        Turn on the robots buzzer
        :param frequency: The frequency, in Hz
        :param duration: The duration of the buzz, in seconds
        """

        cmnd = "buzzF" + str(frequency) + "T" + str(duration)
        return self.__send(cmnd)


    # Get commands
    def getMoving(self):
        """
        This function will return True if the robot is currently moving, and False if there is no ongoing movement.
        This is used to see when the computer should send another move command. The typical structure is to
        tell the robot to move somewhere, then

        while getMoving(): pass

        then send another move command.
        """

        # Find out if the robot is currently moving
        response  = self.__send("gmov")
        parsedArgs = self.__parseArgs(response, "mov", ["M"])


        # Return True if moving, False if not moving
        return (False, True)[int(parsedArgs['M'])]

    def getXYZCoords(self):
        """
        Get the robots XYZ coordinates

        Returns (x, y, z)
        where x, y, and z are in millimeters
        """

        # Returns an array of the format [x, y, z] of the robots current location
        response  = self.__send("gcrd")
        parsedArgs = self.__parseArgs(response, "crd", ["X", "Y", "Z"])

        # Return (currX, currY, currZ)
        return -parsedArgs["X"], -parsedArgs["Y"], parsedArgs["Z"]

    def getServoAngles(self):
        """
        Get the robots current servo angles

        Returns (Base servo, left servo, right servo)

        where stretch and height are in millimeters, and rotation is in degrees
        """

        # Get the angles of each servo

        cmnd = "gang"
        response = self.__send(cmnd)
        parsedArgs = self.__parseArgs(response, "ang", ["A", "B", "C", "D"])

        # Return angles of each servo in order
        return parsedArgs["A"], parsedArgs["B"], parsedArgs["C"], parsedArgs["D"]

    def getTipSensor(self):
        """
        Get state of the robots tip sensor, on the end effector. R

        Returns True if it is pressed, False if it is not pressed
        """

        # Find out if the robot is currently moving
        response  = self.__send("gtip")
        parsedArgs = self.__parseArgs(response, "tip", ["V"])

        # Returns 0 or 1, whether or not the tip sensor is currently activated
        return (True, False)[int(parsedArgs['V'])]  # Return True or False

    def getIK(self, x, y, z):
        """
        Get inverse kinematics calculations for any XYZ point

        Returns a tuple of angles, in the format: (baseServo, leftServo, rightServo)
        :param x: millimeters
        :param y: millimeters
        :param z: millimeters
        """

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
        """
        Get forward kinematics calculations for any three servo angles

        Returns an XYZ point, in the format: (x, y, z)
        :param servo0: degrees
        :param servo2: degrees
        :param servo3: degrees
        """

        # Gets the X, Y, and Z calculated positions for the servo angles servo0, servo1, servo2

        servo0 = str(round(servo0, 2))
        servo1 = str(round(servo1, 2))
        servo2 = str(round(servo2, 2))
        cmnd = "gfkA" + servo0 + "B" + servo1 + "C" + servo2
        response = self.__send(cmnd)
        parsedArgs = self.__parseArgs(response, "fk", ["X", "Y", "Z"])

        # Return (X, Y, Z)
        return -parsedArgs["X"], -parsedArgs["Y"], parsedArgs["Z"]


    # Functions that are only used inside of this library
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
            printf("Communication| Could not connect to robot on port ", port)
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
            printf("Communication| ERROR ", e, "while sending command ", cmnd, ". Disconnecting Serial!")
            self.isConnected = False
            return ""


        # Read the response from the robot (THERE MUST ALWAYS BE A RESPONSE!)
        response = ""
        while True:

            try:
                response += str(self.serial.read(), 'ascii')
            except serial.serialutil.SerialException as e:
                printf("Communication| ERROR ", e, "while sending command ", cmnd, ". Disconnecting Serial!")
                self.isConnected = False
                return ""

            if "\n" in response:
                response = response[:-1]
                break


        # If the setting is enabled, print commands and responses (in the same line, if both are enabled)
        if self.printCommands and self.printResponses:
            printf("Communication| [" + cmnd + "]" + " " * (30 - len(cmnd)) + response)
        elif self.printCommands:
            printf("Communication| ", cmndString)
        elif self.printResponses:
            printf("Communication| ", response)


        # Save the response to a log variable, in case it's needed for debugging
        self.communicationLog.append((cmnd, response))

        # Make sure the respone has the valid start and end characters
        if not (response.count('[') == 1 and response.count(']') == 1):
            printf("Communication| ERROR: The message ", response, " did not come with proper formatting!")


        # Clean up the response
        response = response.replace("[", "")
        response = response.replace("]", "")



        # If the robot returned an error, print that out
        if "error" in response:
            printf("Communication| ERROR: Recieved error from robot: ", response)


        return response

    def __parseArgs(self, message, command, arguments):
        """
        This is a utility function for the uArm com protocol that parses arguments.

        :param message: The full string that was returned by the robot
        :param command: The first part of the string, that needs to be stripped and is not relevent
        :param arguments: A list of ["X", "Y", "Z"] or whatever arguments are in the string returned back that are
        followed by a number.
        """
        responseDict = {n: 0 for n in arguments}  #Fill the dictionary with zero's


        # Do error checking, in case communication didn't work
        if message is False:
            printf("Communication| Since an error occured in communication, returning 0's for all arguments!")
            return responseDict

        if command not in message:
            printf("Communication| ERROR: The message did not come with the appropriate command: ", command)
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



