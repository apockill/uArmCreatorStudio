import serial
from RobotGUI.Global import printf


class Uarm:


    def __init__(self, port):
        self.successConnect = False
        self.serial = None
        self.connectToRobot(port)



    def connected(self):
        if self.serial is None:     return False
        if not self.successConnect: return False

        return True


    def currentCoord(self):
        printf("Uarm.currentCoord(): Getting current coordinates of robot")


    def readAngle(self, servo_number):
        printf("Uarm.readAngle(): Error: This function should not be run")


    def pumpOn(self):
        printf("Uarm.pumpOn(): Activating uArm Pump")


    def pumpOff(self):
        printf("Uarm.pumpOn(): Deactivating uArm Pump")


    def moveToWithTime(self, x, y, z, timeSpend):
        #printf("Uarm.moveToWithTime(): Moving to", x, y, z, " in ", timeSpend)
        cmnd = "moveX" + str(x) + "Y" + str(y) + "Z" + str(z) + "T" + str(timeSpend)
        self.send(cmnd)


    def servoAttach(self, servo_number):
        printf("Uarm.servoAttach(): Attaching", servo_number)


    def servoDetach(self, servo_number):
        printf("Uarm.servoDetach(): Detaching", servo_number)


    # Not to be used outside of library
    def connectToRobot(self, port):
        try:
            self.serial = serial.Serial(port=port, baudrate=115200,
                                        parity=serial.PARITY_NONE,
                                        stopbits=serial.STOPBITS_ONE,
                                        bytesize=serial.EIGHTBITS,
                                        timeout=.1)
            self.successConnect = True
        except serial.SerialException as e:
            print("Uarm.connectToRobot(): Could not open ", port)
            self.serial = None
            self.successConnect = False


    def send(self, cmnd):
        if not self.connected(): return None
        print("Sending command: ", cmnd)
        cmndString = bytes("[" + cmnd + "]>", encoding='ascii')

        self.serial.write(cmndString)
        print(self.read())



    def read(self):
        message = ""
        while True:
            message += str(self.serial.read(), 'ascii')
            if "\n" in message:
                message = message[:-1]
                break
        return message



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








