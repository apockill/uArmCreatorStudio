import serial
import serial.tools.list_ports
import Global
from threading import Thread
from UArmForPython.uarm_python import Uarm


def getConnectedRobots():
    #Returns any arduino serial ports in a list [port, port, port]
    #This is used to let the user choose the correct port that is their robot
    ports = list(serial.tools.list_ports.comports())
    return ports


class Robot():
    """
    X:
    Y:
    Z: Ground level is at 6.5cm
    """
    def __init__(self, comPort):
        self.uArm = None
        self.home = {"x": 0, "y": -15, "z": 15}
        self.pos =     {'x':       0.0,
                        'y':       0.0,
                        'z':       0.0,
                        'wrist':   0.0,
                        'touch':     0}

        #Every time uArm is connected correctly, all servos are attached. Update the values to match this.
            #Keep track of which servos are attached
        self.gripperStatus = False
        self.servoStatus = {1: True,
                            2: True,
                            3: True,
                            4: True}
            #If there is ever a change in a servos status, it is stored in this container until
            #the 'refresh' function is run
        self.newServoStatus =   {1: True,
                                 2: True,
                                 3: True,
                                 4: True}

        self.positionChanged = True
        self.gripperChanged  = False  #This should only be used in Robot.refresh() to activate the gripper
        self.servoChanged    = False  #This should only be used in Robot.refresh() to set movement time to 0
        self.running         = False  #If the setup Thread is running currently



    # def moveTo(self, **kwargs):
    #     relative = kwargs.get('relative',     False)
    #     waitFor  = kwargs.get('waitForRobot', False)  #If true, waitForRobot() will be run at the end of the function
    #
    #     #HANDLE ANY OTHER COMMANDS, INCLUDING POLAR COMMANDS
    #     for name, value in kwargs.items():\t  #Cycles through any variable that might have been in the kwargs. This is any position command!
    #
    #         if name in self.pos:  #If it is a position statement.
    #             if self.pos[name] is "": continue
    #             if relative:
    #                 self.pos[name] += value
    #             else:
    #                 self.pos[name] = value
    #
    #
    #     success = self.refreshPos()
    #
    #     if waitFor and success: self.waitForRobot()
        # def setDetached(self, **kwargs):


    def currentCoord(self):
        if self.uArm is None or self.running:
            print "Robot.currentCoord():\t Robot not found or setupThread is running, returning 0 for all coordinates.."
            return {1: 0, 2: 0, 3: 0}
        else:
            print "Robot.currentCoord():\t Getting coordinates for robot..."
            return self.uArm.currentCoord()



    def setPos(self, **kwargs):
        relative = kwargs.get('relative', False)
        posBefore = dict(self.pos)

        for name, value in kwargs.items():  #Cycles through any variable that might have been in the kwargs. This is any position command!
            if name in self.pos:  #If it is a position statement.
                if self.pos[name] is "": continue
                if relative:
                    self.pos[name] += value
                else:
                    self.pos[name] = value

        #If this command has changed the position, or if the position was changed earlier
        self.positionChanged = (not (posBefore == self.pos)) or self.positionChanged

    def setServos(self, **kwargs):
        #If anything changed, set the appropriate newServoStatus to reflect that
        self.newServoStatus[1] = kwargs.get('servo1', self.newServoStatus[1])
        self.newServoStatus[2] = kwargs.get('servo2', self.newServoStatus[2])
        self.newServoStatus[3] = kwargs.get('servo3', self.newServoStatus[3])
        self.newServoStatus[4] = kwargs.get('servo4', self.newServoStatus[4])

        #print "setServos run: ", self.newServoStatus, self.servoStatus

    def setGripper(self, status):
        if not self.gripperStatus == status:
            self.gripperChanged = True
            self.gripperStatus = status


    def getTipSensor(self):
        #If the robots tip sensor is currently being pressed
        return False



    def refresh(self, **kwargs):
        #ONLY USE when doing camera calibrations that require reading the camera while the robots moving
        instantMovement = kwargs.get("instant", False)


        #Sends all positional data in self.pos to the robot
        if self.uArm is None or self.running:
            print "Robot.refresh():\t ERROR: Tried sending command while uArm is None or setupThread was running"
            return

        self.updateServo(1)
        self.updateServo(2)
        self.updateServo(3)
        self.updateServo(4)


        if self.servoChanged:
            self.servoChanged = False
            currXYZ  = self.currentCoord()
            self.uArm.moveToWithTime(currXYZ[1], currXYZ[2], currXYZ[3], 0)

        if self.gripperChanged:
            if self.gripperStatus:
                self.uArm.pumpOn()
            else:
                self.uArm.pumpOff()
            self.gripperChanged = False

        dist = lambda p1, p2: ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2 + (p2[2] - p1[2]) ** 2) ** .5

        if self.positionChanged:
            #Calculate the amount of time the move should take so as to reach an avg speed of cmps (cm per second)
            currXYZ  = self.currentCoord()
            currXYZ  = [currXYZ[1], currXYZ[2], currXYZ[3]]
            setXYZ   = [self.pos["x"], self.pos["y"], self.pos["z"]]
            distance = dist(currXYZ, setXYZ)

            cmps     = 35   #Desired centimeters/per/second of average speed from the robot
            time     = distance / cmps

            if instantMovement: time = 0

            try:
                self.uArm.moveToWithTime(self.pos['x'], self.pos['y'], self.pos['z'], time)
            except ValueError:
                print "Robot.refresh():\t ERROR: Robot out of bounds and the uarm_python library crashed!"

            self.positionChanged = False

    def updateServo(self, num):
        if not self.newServoStatus[num] == self.servoStatus[num]:
            if self.newServoStatus[num]:
                #Attach the servo
                self.uArm.servoAttach(num)
                self.servoStatus[num] = True
                self.servoChanged     = True  #This prompts the robot to "moveToWithTime" with 0 as time
                print "Robot.updateServo():\t Servo", num, "attached"
            else:
                #Detach the servo
                self.uArm.servoDetach(num)
                self.servoStatus[num] = False
                print "Robot.updateServo():\t Servo", num, "detached"



    def setupThread(self, com):
        print "Robot.setupThread():\t Thread Created"
        try:
            self.uArm = Uarm(com)
            #self.servoDetach()
            print "Robot.setupThread():\t uArm successfully connected"

        except serial.SerialException:
            print "Robot.setupThread():\t ERROR SerialException while setting uArm to ", com
        self.running = False
        #self.refresh()

    def setUArm(self, com):
        if com is not None and not self.running:
            print "Robot.setUArm():\t Setting uArm to com", com, "..."
            self.uArm    = None  #This will prevent the 'play script' button from activating
            setupThread  = Thread(target=lambda: self.setupThread(com))
            self.running = True
            setupThread.start()

        else:
            if self.running: print "Robot.setUArm()\t ERROR: setUArm() run while setupThread was already running!"
        self.setPos(**self.home)





