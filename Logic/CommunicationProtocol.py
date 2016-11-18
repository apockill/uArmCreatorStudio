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



def getConnectedRobots():
    ports = list(serial.tools.list_ports.comports())
    return ports


class Device:
    """
      This is a library for controlling uArms that have uFactories communication protocol of version 0.9.6
    """

    def __init__(self, port):
        """
        :param port: The COM port that the robot is plugged in to.
        """

        self.__isConnected  = False  # If any connection or communication errors occur, this will turn false.
        self.__serial       = None   # The serial connection to the robot
        self.errors         = []     # A list of errors that have occured. See self.getErrorsToDisplay() for more
        self.__connectToRobot(port)

    #      The following functions are used outside of this library. Make sure they are implimented!     #

    # Functions that don't communicate with the device
    def connected(self):
        # if self.serial is None:     return False
        if self.__isConnected is False: return False
        # if not self.__handshake():  return False
        return True

    def getErrorsToDisplay(self):
        """
        Called by the GUI, this will return any errors that deserve being shown to the user in a dialog box.
        The GUI will querry every five seconds and display any errors that need to be shown.

        WHENEVER THIS FUNCTION IS CALLED, IT MUST CLEAR THE ERROR LIST VARIABLE SO THE GUI DOESN'T DISPLAY THE ERROR
        OVER AND OVER!

        Any error sent to the GUI will make the GUI remove the robot from the settings.txt, causing it to not auto-
        connect when the GUI is opened. Thus, reserve this function for only important errors.

        :return: A list of strings of errors, such as [ErrorString, ErrorString, ErrorString]
        """
        errors = self.errors
        self.errors = []
        return errors

    # Set commands
    def setXYZ(self, x, y, z, speed):
        """
        Set the robots current move.
        :param x: centimeters
        :param y: centimeters
        :param z: centimeters
        :param speed: centimeters per second, how fast the robot should move towards its end point
                      If you have tuning, then just calculate the average speed.
        """

        # Prepare the values (convert from cm to millimeters, that's what uArm accepts)
        x = str(int(round(    x * 10, 0)))
        y = str(int(round(    y * 10, 0)))
        z = str(int(round(    z * 10, 0)))
        v = str(int(round(speed * 10, 0)))

        # Create the command
        cmnd = "sMovX" + x + "Y" + y + "Z" + z + "V" + v

        # Send the command and receive a response
        self.__sendAndRecieve(cmnd)

    def setServo(self, servo, angle):
        """
        Set a servo to a particular angle
        :param servo: A servo ID, a number 0, 1, 2, or 3
        :param angle: An angle in degrees between 0 and 180
        :return:
        """

        # Prepare the values
        s = str(int(servo))
        a = str(float(round(angle, 3)))

        # Create the command
        cmnd = "sSerN" + s + "V" + a

        # Send the command and receive a response
        self.__sendAndRecieve(cmnd)

    def setPump(self, onOff):
        """
        Set the pumps value.
        :param onOff: True means turn the gripper on. False means off.
        """

        # Prepare the values
        v = str(int(onOff))

        # Create the command
        cmnd = "sPumV" + v

        # Send the command and receive a response
        self.__sendAndRecieve(cmnd)

    def setServoAttach(self, servo):
        """
        Attach a certain servo.
        :param servo: The servo's number
        """

        # Prepare the values
        s = str(int(servo))

        # Create the command
        cmnd = "sAttN" + s

        # Send the command and receive a response
        self.__sendAndRecieve(cmnd)

    def setServoDetach(self, servo):  # Done
        """
        Detach a certain servo.
        :param servo: The servo's number
        """

        # Prepare the values
        s = str(int(servo))

        # Create the command
        cmnd = "sDetN" + s

        # Send the command and receive a response
        self.__sendAndRecieve(cmnd)

    def setBuzzer(self, frequency, duration):
        """
        Turn on the robots buzzer
        :param frequency: The frequency, in Hz
        :param duration: The duration of the buzz, in seconds
        """

        # Prepare the values
        f = str(float(frequency))
        d = str(float(duration))

        # Create the command
        cmnd = "sBuzF" + f + "T" + d

        # Send the command and receive a response
        self.__sendAndRecieve(cmnd)

    def setStop(self):
        """
        This command should stop any ongoing movement that the robot is doing.
        """

        # Create the command
        cmnd = "sStp"

        # Send the command and recieve a response
        self.__sendAndRecieve(cmnd)


    # Get commands
    def getMoving(self):
        """
        This function will return True if the robot is currently moving, and False if there is no ongoing movement.
        This is used to see when the computer should send another move command. The typical structure is to
        tell the robot to move somewhere, then

        while getMoving(): pass

        then send another move command.
        """

        # Send the command and receive a response
        response  = self.__sendAndRecieve("gMov")

        # Create the return
        ret = (False, True)["S" in response]

        return ret

    def getXYZCoords(self):
        """
        Get the robots XYZ coordinates

        Returns (x, y, z)
        where x, y, and z are in centimeters
        """

        # Send the command and receive a response
        response = self.__sendAndRecieve("gCrd")

        # Parse the response
        parsedArgs = self.__parseArgs(response, "S", ["X", "Y", "Z"])

        # Create the return
        ret = (parsedArgs["X"] / 10.0, parsedArgs["Y"] / 10.0, parsedArgs["Z"] / 10.0)

        return ret

    def getServoAngles(self):  # TODO: Need to add wrist angle
        """
        Get the robots current servo angles

        Returns (Base servo, left servo, right servo, wrist servo)

        Angles are in degrees
        """

        # Send the command and receive a response
        response = self.__sendAndRecieve("gAng")

        # Parse the response
        parsedArgs = self.__parseArgs(response, "S", ["B", "L", "R", "H"])

        # Create the return
        ret = (parsedArgs["B"], parsedArgs["L"], parsedArgs["R"], parsedArgs["H"])

        return ret

    def getTipSensor(self):  # TODO: Need to add wrist angle
        """
        Get state of the robots tip sensor, on the end effector. R

        Returns True if it is pressed, False if it is not pressed
        """

        # Send the command and receive a response
        response = self.__sendAndRecieve("gTip")

        # Parse the response
        parsedArgs = int(self.__parseArgs(response, "", ["S"])["S"])

        # Create the return
        ret = (False, True)[parsedArgs]

        return ret

    def getIK(self, x, y, z):
        """
        Get inverse kinematics calculations for any XYZ point

        Returns a tuple of angles, in the format: (baseServo, leftServo, rightServo)
        Angles returned are in degrees

        :param x: centimeters
        :param y: centimeters
        :param z: centimeters
        """

        # Prepare the values
        x = str(round(x * 10, 0))
        y = str(round(y * 10, 0))
        z = str(round(z * 10, 0))

        # Create the command
        cmnd = "gIKX" + x + "Y" + y + "Z" + z

        # Send the command and receive a response
        response = self.__sendAndRecieve(cmnd)

        # Parse the response
        parsedArgs = self.__parseArgs(response, "", ["T", "L", "R"])

        # Create the return
        ret = (parsedArgs["T"], parsedArgs["L"], parsedArgs["R"])

        return ret

    def getFK(self, servo0, servo1, servo2):
        """
        Get forward kinematics calculations for any three servo angles
        Angles are in degrees

        Returns an XYZ point, in the format: (x, y, z), where x, y, z are in centimeters
        :param servo0: degrees
        :param servo1: degrees
        :param servo2: degrees
        """

        # Prepare the values
        s1 = str(round(servo0, 2))
        s2 = str(round(servo1, 2))
        s3 = str(round(servo2, 2))

        # Create the command
        cmnd = "gFKT" + s1 + "L" + s2 + "R" + s3

        # Send the command and receive a response
        response = self.__sendAndRecieve(cmnd)

        # Parse the response
        parsedArgs = self.__parseArgs(response, "", ["X", "Y", "Z"])

        # Create the return (convert from milimeters to centimeters)
        ret = (parsedArgs["X"] * 10.0, parsedArgs["Y"] * 10.0, parsedArgs["Z"] * 10.0)

        return ret



    # Functions that are only used inside of this library
    def __connectToRobot(self, port):
        try:
            self.__serial = serial.Serial(port     = port,
                                          baudrate = 115200,
                                          parity   = serial.PARITY_NONE,
                                          stopbits = serial.STOPBITS_ONE,
                                          bytesize = serial.EIGHTBITS,
                                          timeout  = .1)


            sleep(3)
            self.__isConnected = True
            self.__sendAndRecieve("gVer", timeout=1)  # Send a handshake to verify that the robot is indeed connected


        except Exception as e:

            printf("Communication| ERROR: " + type(e).__name__ + " " + str(e) + " while connecting to port ", port)
            self.__serial = None
            self.__isConnected = False
            self.errors.append(type(e).__name__ + " " + str(e))

    def __sendAndRecieve(self, cmnd, timeout=None):
        """
        This command will send a command and receive the robots response. There must always be a response!
        Responses should be recieved immediately after sending the command, after which the robot will proceed to
        perform the action.
        :param cmnd: a String command, to send to the robot
        :return: The robots response
        """

        if not self.connected():
            printf("Communication| Tried to send a command while robot was not connected!")
            return ""

        # Prepare and send the command to the robot
        cmndString = bytes("[" + cmnd + "]", encoding='ascii')  #  "[" + cmnd + "]"


        try:
            self.__serial.write(cmndString)
        except serial.serialutil.SerialException as e:
            printf("Communication| ERROR ", e, "while sending command ", cmnd, ". Disconnecting Serial!")
            self.__isConnected = False
            return ""


        # Read the response from the robot (THERE MUST ALWAYS BE A RESPONSE!)
        response = ""
        startTime = time()
        while True:
            if timeout is not None and time() - startTime > timeout:
                raise Exception("Robot Not Responding")

            try:
                response += str(self.__serial.read(), 'ascii')
                response = response.replace(' ', '')

            except serial.serialutil.SerialException as e:
                printf("Communication| ERROR ", e, "while sending command ", cmnd, ". Disconnecting Serial!")
                self.__isConnected = False
                return ""

            if "[" in response and "]" in response:
                response = str(response.replace("\n", ""))
                response = str(response.replace("\r", ""))
                break



        printf("Communication| ", "[" + cmnd + "]" + " " * (30 - len(cmnd)) + response)


        # Clean up the response
        response = response.replace("[", "")
        response = response.replace("]", "")


        # If the robot returned an error, print that out
        if "error" in response:
            printf("Communication| ERROR: received error from robot: ", response)



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


'''
###### UNUSED FUNCTIONS (from the new firmware on the uArm #####
def setPolar(self, stretch, rotation, height, speed):
    """
    Set the polar coordinates of the robot
    :param stretch: Stretch distance of end effector from base of robot, in millimeters
    :param rotation: Rotation of base servo, in degrees
    :param height: Height of robot end effector, in millimeters
    :param speed: A float between 0 and 1, where 0 is slow and 1 is fast
    :return:
    """

    # Prepare the values
    s = str(round( stretch, 0))
    r = str(round(rotation, 0))
    h = str(round(  height, 2))
    v = str(round(   speed, 2))

    # Create the command
    cmnd = "sPolS" + s + "R" + r + "H" + h + "V" + v

    # Send the command and receive a response
    self.__sendAndRecieve(cmnd)

def getPolarCoords(self):
    """
    Get the robots polar coordinates

    Returns (stretch, rotation, height)
    where stretch and height are in millimeters, and rotation is in degrees
    """

    # Send the command and receive a response
    response = self.__sendAndRecieve("gPol")

    # Parse the response
    parsedArgs = self.__parseArgs(response, "S", ["S", "R", "H"])

    # Create the return
    ret = (parsedArgs["S"], parsedArgs["R"], parsedArgs["H"])

    return ret

def getReachableXYZ(self, x, y, z):
    """
    Get whether or not the robot can reach a certain point
    Input an XYZ coordinate, and it will return True or False if it can get to the final location
    Returns True
    """

    # Prepare the values
    x = str(round(    x, 0))
    y = str(round(    y, 0))
    z = str(round(    z, 0))

    # Create the command
    cmnd = "gSimX" + x + "Y" + y + "Z" + z + "V0"

    # Send the command and receive a response
    response = self.__sendAndRecieve(cmnd)

    # Create the return
    ret = "S" in response

    return response

def getReachablePolar(self, stretch, rotation, height):
    """
    Get whether or not the robot can reach a certain point
    Input a polar coordinate, and it will return True or False if it can get to the final location
    Returns True
    """

    # Prepare the values
    x = str(round( stretch, 0))
    y = str(round(rotation, 2))
    z = str(round(  height, 0))

    # Create the command
    cmnd = "gSimX" + x + "Y" + y + "Z" + z + "V1"

    # Send the command and receive a response
    response = self.__sendAndRecieve(cmnd)

    # Create the return
    ret = "S" in response

    return ret


# Not Implimented Yet
def getPump(self):
    # This method will be implimented with the next version of the uArm
    pass

def getGripper(self):
    # This method will be implimented with the next version of the uArm
    pass

def setGripper(self, onOff):
    """
    Set the pumps value.
    :param onOff: True means turn the gripper on. False means off.
    """

    # Prepare the values
    v = str(int(onOff))

    # Create the command
    cmnd = "sGriV" + v

    # Send the command and receive a response
    self.__sendAndRecieve(cmnd)

def getVersion(self):
    """
    Get the current uArm version

    Returns a string, something like "0.9.6" or another string like that.
    """

    # Send the command and receive a response
    response  = self.__sendAndRecieve("gVer")

    # Create the return
    ret = response.replace("S", "")

    return ret

'''




# TESTING PROTOCOL
if __name__ == "__main__":
    from sys import exit

    connecteduArms = getConnectedRobots()

    print("Open Ports: ", connecteduArms)


    # If no robots were found, exit the script
    if len(connecteduArms) == 0:
        print("No robots found!")
        exit()


    # Connect to the first robot, and make sure it connected correctly
    chosenPort = connecteduArms[0][0]
    print("Attempting to connect to port ", chosenPort)
    uarm = Device(chosenPort)
    if not uarm.connected():
        print("uArm could not connect!")
        exit()
    print("Beginning Testing")



    print("\nTest setMove")
    print("Move To (0, 150, 150)")
    uarm.setXYZ(0, 150, 150, 10)
    while uarm.getMoving(): sleep(.1)

    print("Move To (-150, 150, 150)")
    uarm.setXYZ(-150, 150, 150, 10)
    while uarm.getMoving(): sleep(.1)

    print("Move To (0, 150, 100)")
    uarm.setXYZ(0, 150, 100, 10)
    while uarm.getMoving(): sleep(.1)

    print("Move To (150, 150, 150)")
    uarm.setXYZ(150, 150, 150, 10)
    while uarm.getMoving(): sleep(.1)

    print("Move To (0, 150, 250)")
    uarm.setXYZ(0, 150, 250, 10)
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
    print("Setting Servo 3")
    uarm.setServo(2, 30)
    sleep(.25)
    print("Setting Servo 3")
    uarm.setServo(3, 120)

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
    print("Tip Sensor:   ", uarm.getTipSensor())


    print("\nTest Forward/Backwrd Kinematics")
    print("Get Forward Kinematics  (90, 70, 35): ", uarm.getFK(90, 70, 35))
    print("Get Forward Kinematics  (1000, 1000, 1000): ", uarm.getFK(1000, 1000, 1000))
    print("Get Inverse Kinematics (0, 150, 150): ", uarm.getIK(0, 150, 150))
    print("Get Inverse Kinematics (1000, 1000, 1000): ", uarm.getIK(1000, 1000, 1000))

    print("Testing Over")
