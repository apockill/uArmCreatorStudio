import serial
from time                  import sleep
from RobotGUI.Logic.Global import printf


# This is a library for controlling uArms that have Alex Thiel's Arduino communication protocol uploaded

class Uarm:

    def __init__(self, port):
        self.successConnect = False
        self.serial = None
        self.__connectToRobot(port)

    def connected(self):
        if self.serial is None:     return False
        if not self.successConnect: return False
        if not self.__handshake():  return False
        return True


    # Action commands

    def moveToWithTime(self, x, y, z, timeSpend):
        x = str(round(x, 3))
        y = str(round(y, 3))
        z = str(round(z, 3))
        t = str(round(timeSpend, 3))
        cmnd = "moveX" + x + "Y" + y + "Z" + z + "S" + t
        response = self.__send(cmnd)

    def moveWrist(self, angle):
        angle = str(round(angle, 3))
        cmnd = "handV" + angle
        response = self.__send(cmnd)

    def pumpOn(self):
        printf("Uarm.pumpOn(): Activating uArm Pump")
        cmnd = "pumpV1"
        response = self.__send(cmnd)

    def pumpOff(self):
        printf("Uarm.pumpOn(): Deactivating uArm Pump")
        cmnd = "pumpV0"
        response = self.__send(cmnd)

    def servoAttach(self, servo_number):
        servo_number = str(int(servo_number))
        cmnd = "attachS" + servo_number
        response = self.__send(cmnd)

    def servoDetach(self, servo_number):
        servo_number = str(int(servo_number))
        cmnd = "detachS" + servo_number
        response = self.__send(cmnd)


    # Get commands
    def getCurrentCoord(self):
        # printf("Uarm.currentCoord(): Getting current coordinates of robot")
        response  = self.__send("gcoords")
        parsedArgs = self.__parseArgs(response, "coords", ["x", "y", "z"])
        return parsedArgs

    def getIsMoving(self):
        response  = self.__send("gmoving")
        parsedArgs = self.__parseArgs(response, "moving", ["m"])
        return parsedArgs['m']

    def getServoAngle(self, servo_number):
        cmnd = "gAngleS" + str(servo_number)
        response = self.__send(cmnd)
        parsedArgs = self.__parseArgs(response, "angle", ["a"])

        return parsedArgs["a"]

    def getTipSensor(self):
        # Returns whether or not the tip sensor is currently activated
        response  = self.__send("gtip")
        parsedArgs = self.__parseArgs(response, "tip", ["v"])
        print("Final", parsedArgs)
        return (True, False)[int(parsedArgs['v'])]  # Flip the value and turn it into a boolean

    # Not to be used outside of library
    def __connectToRobot(self, port):
        try:
            self.serial = serial.Serial(port     = port,
                                        baudrate = 115200,
                                        parity   = serial.PARITY_NONE,
                                        stopbits = serial.STOPBITS_ONE,
                                        bytesize = serial.EIGHTBITS,
                                        timeout  = .1)
            self.successConnect = True
        except serial.SerialException as e:
            printf("Uarm.connectToRobot(): Could not connect to robot on port ", port)
            self.serial = None
            self.successConnect = False
        sleep(3)

    def __handshake(self):
        return True

    def __send(self, cmnd):
        if not self.connected(): return None
        cmndString = bytes("[" + cmnd + "]>", encoding='ascii')
        self.serial.write(cmndString)
        response = self.__read()
        return response

    def __read(self):
        message = ""
        while True:
            message += str(self.serial.read(), 'ascii')
            if "\n" in message:
                message = message[:-1]
                break

        if "ERROR" in message:
            printf("Uarm.read(): ERROR: Recieved error from robot: ", message)

        if not (message.count('[') == 1 and message.count(']') == 1):
            print("Uarm.read(): ERROR: The message did not come with propper formatting!")

        message = message.replace("[", "")
        message = message.replace("]", "")
        return message.lower()

    def __parseArgs(self, message, command, arguments):
        responseDict = {n: 0 for n in arguments}  #Fill the dictionary with zero's

        if command not in message:
            printf("Uarm.read(): ERROR: The message did not come with the appropriate command!")
            return responseDict

        message = message.replace(command, "")

        for i, arg in enumerate(arguments):
            if i < len(arguments) - 1:
                responseDict[arg] = message[message.find(arg) + 1: message.find(arguments[i + 1])]
            else:
                responseDict[arg] = message[message.find(arg) + 1:]

            responseDict[arg] = float(responseDict[arg])

        return responseDict











# def stopperStatus(self):
#     printf("Uarm.stopperStatus(): Getting Stopper Status")

# Not used outside of library:

#
#
# def currentX(self):
#     printf("Uarm.currentX(): Getting current x coordinate of robot")
#
#
# def currentY(self):
#     printf("Uarm.currentY(): Getting current y coordinate of robot")
#
#
# def currentZ(self):
#     printf("Uarm.currentZ(): Getting current z coordinate of robot")
#
#
# def uarmDisconnect(self):
#     printf("Uarm.uarmDisconnect(): Disconnecting uArm")
#
#
# def uarmAttach(self):
#     printf("Uarm.uarmAttach(): Attaching All Servos In uArm")
#
#
# def uarmDetach(self):
#     printf("Uarm.uarmDetach(): Detaching All Servos In uArm")
#

# def angleConstrain(self, Angle):
#     printf("Uarm.angleConstrain(): Error: This function should not be run")
#
#
# def writeServoAngleRaw(self, servo_number, Angle):
#     printf("Uarm.writeServoAngleRaw(): Error: This function should not be run")
#
#
# def writeServoAngle(self, servo_number, Angle):
#     printf("Uarm.writeServoAngle(): Error: This function should not be run")
#
#
# def writeAngle(self, servo_1, servo_2, servo_3, servo_4):
#     printf("Uarm.writeAngle(): Error: This function should not be run")
#
#
# def writeAngleRaw(self, servo_1, servo_2, servo_3, servo_4):
#     printf("Uarm.writeAngleRaw(): Error: This function should not be run")
#
#
# def readAnalog(self, servo_number):
#     printf("Uarm.readAnalog(): Error: This function should not be run")
#
#
# def readServoOffset(self, servo_number):
#     printf("Uarm.readServoOffset(): Error: This function should not be run")
#
#
# def readToAngle(self, input_analog, servo_number, tirgger):
#     printf("Uarm.readToAngle(): Error: This function should not be run")
#
#
# def fwdKine(self, theta_1, theta_2, theta_3):
#     printf("Uarm.fwdKine(): Error: This function should not be run")
#
#
# def readAngle(self, servo_number):
#     printf("Uarm.readAngle(): Error: This function should not be run")
#
#
# def readAngleRaw(self, servo_number):
#     printf("Uarm.readAngleRaw(): Error: This function should not be run")
#
#
# def interpolation(self, init_val, final_val):
#     printf("Uarm.interpolation(): Error: This function should not be run")
#
#
# def ivsKine(self, x, y, z):
#     printf("Uarm.ivsKine(): Error: This function should not be run")
#
#
# def moveToWithS4(self, x, y, z, timeSpend, servo_4_relative, servo_4):
#     printf("Uarm.moveToWithS4(): Error: This function should not be run")
#
#
# def moveTo(self, x, y, z):
#     printf("Uarm.moveTo(): Error: This function should not be run")
#
#
# def moveRelative(self, x, y, z, time, servo_4_relative, servo_4):
#     printf("Uarm.moveRelative(): Error: This function should not be run")








