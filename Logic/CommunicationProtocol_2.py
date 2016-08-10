import serial
import serial.tools.list_ports
from time         import sleep
from Logic.Global import printf
__author__ = "Alexander Thiel"



def getConnectedRobots():
    ports = list(serial.tools.list_ports.comports())
    return ports


class Device:
    """
      This is a library for controlling uArms that have uFactories communication protocol of version 0.9.6
    """

    def __init__(self, port, printCommands=True, printResponses=True):
        self.printCommands  = printCommands
        self.printResponses = printResponses
        self.isConnected    = False
        self.serial         = None
        self.__connectToRobot(port)

        # For debug logs
        # An array of tuples, of what was sent, what was received
        # [(sent, received), (sent, received), (sent, received)]
        self.communicationLog = []

    def connected(self):
        """
        Returns True if a connection to the robot has been established, and is maintained.
        If the robot is ever unplugged and a command is sent, then this will return False.
        """

        return self.isConnected


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

        # Prepare the values (convert from cm to milimeters, that's what uArm accepts)
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
        cmnd = "sAttS" + s

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
        cmnd = "sDetS" + s

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
        parsedArgs = self.__parseArgs(response, "S", ["T", "L", "R", "F"])

        # Create the return
        ret = (parsedArgs["T"], parsedArgs["L"], parsedArgs["R"], parsedArgs["F"])

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
        :param servo2: degrees
        :param servo3: degrees
        """

        # Prepare the values
        s1 = str(round( servo0, 2))
        s2 = str(round( servo1, 2))
        s3 = str(round( servo2, 2))

        # Create the command
        cmnd = "gFKT" + s1 + "L" + s2 + "R" + s3

        # Send the command and receive a response
        response = self.__sendAndRecieve(cmnd)

        # Parse the response
        parsedArgs = self.__parseArgs(response, "", ["X", "Y", "Z"])

        # Create the return (convert from milimeters to centimeters)
        ret = (parsedArgs["X"] * 10.0, parsedArgs["Y"] * 10.0, parsedArgs["Z"] * 10.0)

        return ret





    # Not to be used outside of library
    def __connectToRobot(self, port):
        try:
            self.serial = serial.Serial(port     = port,
                                        baudrate = 115200,
                                        # parity   = serial.PARITY_NONE,
                                        # stopbits = serial.STOPBITS_ONE,
                                        # bytesize = serial.EIGHTBITS,
                                        timeout  = .1)
            self.isConnected = True
        except serial.SerialException as e:
            printf("Communication| Could not connect to robot on port ", port)
            self.serial = None
            self.isConnected = False
        sleep(3.5)

    def __sendAndRecieve(self, cmnd):
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
                response = response.replace(' ', '')

            except serial.serialutil.SerialException as e:
                printf("Communication| ERROR ", e, "while sending command ", cmnd, ". Disconnecting Serial!")
                self.isConnected = False
                return ""

            if "[" in response and "]" in response:
                response = str(response.replace("\n", ""))
                response = str(response.replace("\r", ""))
                break


        if self.printCommands and self.printResponses:
            printf("Communication| ", "[" + cmnd + "]" + " " * (30 - len(cmnd)) + response)
        elif self.printCommands:
            printf("Communication| ", cmndString)
        elif self.printResponses:
            printf("Communication| ", response)


        # Save the response to a log variable, in case it's needed for debugging
        self.communicationLog.append((cmnd[:], response[:]))


        # Clean up the response
        response = response.replace("[", "")
        response = response.replace("]", "")


        # If the robot returned an error, print that out
        if "error" in response:
            printf("Communication| ERROR: received error from robot: ", response)



        return response

    def __parseArgs(self, message, command, arguments):
        """
        This will parse a response form the robot, one that comes in the format that the uArms communication protocol
        uses. If you are making a custom protocol, this likely is not relevant to you.

        For example, if you send a getXYZCoords command to the robot [gCrd] the robot might respond
        with [SX0.0Y100Z200]

        You can then pass this to __parseArgs("[SX0.0Y100Z200]", "S", ["X", "Y", "Z"]) and parseargs will return
        a dictionary of this format: {"X": 0.0, "Y": 100.0, "Z": 200}

        Essentially, parseArgs will find the arguments that were passed by the robot.


        :param message: What the robot responded with. ie, [SX0.0Y100Z200]
        :param command: The "header" for the command (this gets thrown away). For example, "S"
        :param arguments: The values to extract, in a list. For example, ["X", "Y", "Z"]

        :return: A dictionary of format {"argument": float value, "argument": float value, "argument": float value}
        """
        responseDict = {n: 0 for n in arguments}  #Fill the dictionary with zero's


        # Do error checking, in case communication didn't work
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
    uarm = Device(chosenPort, True, True)
    if not uarm.connected():
        print("uArm could not connect!")
        exit()
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
    print("Get Forward Kinematics  (1000, 1000, 1000): ", uarm.getFK(1000, 1000, 1000))
    print("Get Inverse Kinematics (0, 150, 150): ", uarm.getIK(0, 150, 150))
    print("Get Inverse Kinematics (1000, 1000, 1000): ", uarm.getIK(1000, 1000, 1000))

    print("Testing Over")