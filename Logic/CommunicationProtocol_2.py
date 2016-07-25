import serial
import serial.tools.list_ports
from time         import sleep
__author__ = "Alexander Thiel"



def getConnectedRobots():
    ports = list(serial.tools.list_ports.comports())
    return ports


class Device:
    """
      This is a library for controlling uArms that have uFactories communication protocol of version 0.9.6
    """

    def __init__(self, port, printCommands=False, printResponses=False):
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
    def setXYZ(self, x, y, z, speed):  # DONE
        """
        Set the robots current move.
        :param x: millimeters
        :param y: millimeters
        :param z: millimeters
        :param speed: a float between 0 and 1, where 0 is slow and 1 is fast
        """

        # Prepare the values
        x = str(round(    x, 0))
        y = str(round(    y, 0))
        z = str(round(    z, 0))
        v = str(round(speed, 2))

        # Create the command
        cmnd = "sMovX" + x + "Y" + y + "Z" + z + "V" + v

        # Send the command and receive a response
        self.__send(cmnd)

    def setPolar(self, stretch, rotation, height, speed):  # DONE
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
        self.__send(cmnd)

    def setServo(self, servo, angle):  # DONE
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
        self.__send(cmnd)

    def setPump(self, onOff):  # DONE
        """
        Set the pumps value.
        :param onOff: True means turn the gripper on. False means off.
        """

        # Prepare the values
        v = str(int(onOff))

        # Create the command
        cmnd = "sPumV" + v

        # Send the command and receive a response
        self.__send(cmnd)

    def setServoAttach(self, servo):  # DONE
        """
        Attach a certain servo.
        :param servo: The servo's number
        """

        # Prepare the values
        s = str(int(servo))

        # Create the command
        cmnd = "sAttS" + s

        # Send the command and receive a response
        self.__send(cmnd)

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
        self.__send(cmnd)

    def setBuzzer(self, frequency, duration):  # Done
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
        self.__send(cmnd)


    # Get commands
    def getMoving(self):  # Done
        """
        This function will return True if the robot is currently moving, and False if there is no ongoing movement.
        This is used to see when the computer should send another move command. The typical structure is to
        tell the robot to move somewhere, then

        while getMoving(): pass

        then send another move command.
        """

        # Send the command and receive a response
        response  = self.__send("gMov")

        # Create the return
        ret = (False, True)["S" in response]

        return ret

    def getXYZCoords(self):  # Done
        """
        Get the robots XYZ coordinates

        Returns (x, y, z)
        where x, y, and z are in millimeters
        """

        # Send the command and receive a response
        response = self.__send("gCrd")

        # Parse the response
        parsedArgs = self.__parseArgs(response, "S", ["X", "Y", "Z"])

        # Create the return
        ret = (parsedArgs["X"], parsedArgs["Y"], parsedArgs["Z"])

        return ret

    def getPolarCoords(self):  # Done
        """
        Get the robots polar coordinates

        Returns (stretch, rotation, height)
        where stretch and height are in millimeters, and rotation is in degrees
        """

        # Send the command and receive a response
        response = self.__send("gPol")

        # Parse the response
        parsedArgs = self.__parseArgs(response, "S", ["S", "R", "H"])

        # Create the return
        ret = (parsedArgs["S"], parsedArgs["R"], parsedArgs["H"])

        return ret

    def getServoAngles(self):  # TODO: Need to add wrist angle
        """
        Get the robots current servo angles

        Returns (Base servo, left servo, right servo)

        where stretch and height are in millimeters, and rotation is in degrees
        """

        # Send the command and receive a response
        response = self.__send("gAng")

        # Parse the response
        parsedArgs = self.__parseArgs(response, "S", ["T", "L", "R"])

        # Create the return
        ret = (parsedArgs["T"], parsedArgs["L"], parsedArgs["R"])

        return ret

    def getTipSensor(self):  # TODO: Need to add wrist angle
        """
        Get state of the robots tip sensor, on the end effector. R

        Returns True if it is pressed, False if it is not pressed
        """

        # Send the command and receive a response
        response = self.__send("gTip")

        # Parse the response
        parsedArgs = int(self.__parseArgs(response, "", ["S"])["S"])

        # Create the return
        ret = (False, True)[parsedArgs]

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
        response = self.__send(cmnd)

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
        response = self.__send(cmnd)

        # Create the return
        ret = "S" in response

        return ret

    def getIK(self, x, y, z):
        """
        Get inverse kinematics calculations for any XYZ point

        Returns a tuple of angles, in the format: (baseServo, leftServo, rightServo)
        :param x: millimeters
        :param y: millimeters
        :param z: millimeters
        """

        # Prepare the values
        x = str(round(    x, 0))
        y = str(round(    y, 0))
        z = str(round(    z, 0))

        # Create the command
        cmnd = "gIKX" + x + "Y" + y + "Z" + z

        # Send the command and receive a response
        response = self.__send(cmnd)

        # Parse the response
        parsedArgs = self.__parseArgs(response, "S", ["T", "L", "R"])

        # Create the return
        ret = (parsedArgs["T"], parsedArgs["L"], parsedArgs["R"])

        return ret

    def getFK(self, servo0, servo1, servo2):
        """
        Get forward kinematics calculations for any three servo angles

        Returns an XYZ point, in the format: (x, y, z)
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
        response = self.__send(cmnd)

        # Parse the response
        parsedArgs = self.__parseArgs(response, "S", ["X", "Y", "Z"])

        # Create the return
        ret = (parsedArgs["X"], parsedArgs["Y"], parsedArgs["Z"])

        return ret

    def getVersion(self):
        """
        Get the current uArm version

        Returns a string, something like "0.9.6" or another string like that.
        """

        # Send the command and receive a response
        response  = self.__send("gVer")

        # Create the return
        ret = response.replace("S", "")

        return ret


    # Not Implimented Yet
    def getPump(self):
        # This method will be implimented with the next version of the uArm
        pass

    def getGripper(self):
        # This method will be implimented with the next version of the uArm
        pass

    def setGripper(self, onOff):  # DONE
        """
        Set the pumps value.
        :param onOff: True means turn the gripper on. False means off.
        """

        # Prepare the values
        v = str(int(onOff))

        # Create the command
        cmnd = "sGriV" + v

        # Send the command and receive a response
        self.__send(cmnd)


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
            print("Could not connect to robot on port ", port)
            self.serial = None
            self.isConnected = False
        sleep(3)

    def __send(self, cmnd):
        """
        This command will send a command and receive the robots response. There must always be a response!

        :param cmnd: a String command, to send to the robot
        :return: The robots response
        """
        if not self.connected():
            print("Tried to send a command while robot was not connected!")
            return ""

        # Prepare and send the command to the robot
        cmndString = bytes("[" + cmnd + "]", encoding='ascii') #  "[" + cmnd + "]"

        try:
            self.serial.write(cmndString)
        except serial.serialutil.SerialException as e:
            print("ERROR ", e, "while sending command ", cmnd, ". Disconnecting Serial!")
            self.isConnected = False
            return ""


        # Read the response from the robot (THERE MUST ALWAYS BE A RESPONSE!)
        response = ""
        while True:

            try:

                response += str(self.serial.read(), 'ascii')
                response = response.replace(' ', '')

            except serial.serialutil.SerialException as e:
                print("ERROR ", e, "while sending command ", cmnd, ". Disconnecting Serial!")
                self.isConnected = False
                return ""

            if "[" in response and "]" in response:
                response = str(response.replace("\n", ""))
                response = str(response.replace("\r", ""))
                break


        if self.printCommands and self.printResponses:
            print("[" + cmnd + "]" + " " * (30 - len(cmnd)) + response)
        elif self.printCommands:
            print(cmndString)
        elif self.printResponses:
            print(response)


        # Save the response to a log variable, in case it's needed for debugging
        self.communicationLog.append((cmnd[:], response[:]))


        # Clean up the response
        response = response.replace("[", "")
        response = response.replace("]", "")


        # If the robot returned an error, print that out
        if "error" in response:
            print("ERROR: received error from robot: ", response)



        return response

    def __parseArgs(self, message, command, arguments):
        responseDict = {n: 0 for n in arguments}  #Fill the dictionary with zero's


        # Do error checking, in case communication didn't work
        if message is False:
            print("Since an error occured in communication, returning 0's for all arguments!")
            return responseDict

        if command not in message:
            print("ERROR: The message did not come with the appropriate command: ", command)
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
    print("Get Inverse Kinematics (0, 150, 150): ", uarm.getIK(0, 150, 150))


    print("Testing Over")