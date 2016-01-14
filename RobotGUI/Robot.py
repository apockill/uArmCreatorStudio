#test
from threading import Thread
from Global import printf
from UArmForPython.uarm_python import Uarm
import serial
import serial.tools.list_ports
import math


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
                        'y':     -15.0,
                        'z':      15.0,
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
        self.servoAttached    = False  #This should only be used in Robot.refresh() to set movement time to 0
        self.running         = False  #If the setup Thread is running currently



    # def moveTo(self, **kwargs):
    #     relative = kwargs.get('relative',     False)
    #     waitFor  = kwargs.get('waitForRobot', False)  #If true, waitForRobot() will be run at the end of the function
    #
    #     #HANDLE ANY OTHER COMMANDS, INCLUDING POLAR COMMANDS
    #     for name, value in kwargs.items():  #Cycles through any variable that might have been in the kwargs. This is any position command!
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


    def getCurrentCoord(self):
        if not self.connected() or self.running:
            printf("Robot.currentCoord(): Robot not found or setupThread is running, returning 0 for all coordinates..")
            return {1: 0, 2: 0, 3: 0}
        else:
            printf("Robot.currentCoord(): Getting coordinates for robot...")
            return self.uArm.currentCoord()

    def getBaseAngle(self):
        if not self.connected()  or self.running:
            printf("Robot.getBaseAngle(): Robot not found or setupThread is running, returning 90 for base angle...")
            return 90
        else:
            printf("Robot.getBaseAngle(): Getting coordinates for robot...")
            return self.uArm.readAngle(1)

    def connected(self):
        return not self.uArm is None


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

        #printf("setServos run: ", self.newServoStatus, self.servoStatus)

    def setGripper(self, status):
        if not self.gripperStatus == status:
            self.gripperStatus = status

            if self.gripperStatus:
                self.uArm.pumpOn()
            else:
                self.uArm.pumpOff()


    def getTipSensor(self):
        #If the robots tip sensor is currently being pressed
        #Currently buggy, so not implimented
        return False



    def refresh(self, **kwargs):
        #Send information to the robot to perform a move


        #ONLY USE this argumentwhen doing camera calibrations that require reading the camera while the robots moving
        instantMovement = kwargs.get("instant", False)


        #Sends all positional data in self.pos to the robot
        if not self.connected() or self.running:
            printf("Robot.refresh(): ERROR: Tried sending command while uArm is not Connected or setupThread was running")
            return


        currXYZ  = self.getCurrentCoord()
        self.updateServo(1)
        self.updateServo(2)
        self.updateServo(3)
        self.updateServo(4)


        if self.servoAttached:
            self.servoAttached = False
            # currXYZ  = self.getCurrentCoord()
            self.uArm.moveToWithTime(currXYZ[1], currXYZ[2], currXYZ[3], .5)


            self.gripperChanged = False

        dist = lambda p1, p2: ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2 + (p2[2] - p1[2]) ** 2) ** .5

        if self.positionChanged:
            #Calculate the amount of time the move should take so as to reach an avg speed of cmps (cm per second)
            currXYZ  = self.getCurrentCoord()
            currXYZ  = [currXYZ[1], currXYZ[2], currXYZ[3]]
            setXYZ   = [self.pos["x"], self.pos["y"], self.pos["z"]]
            distance = dist(currXYZ, setXYZ)

            cmps     = 40   #Desired centimeters/per/second of average speed from the robot
            time     = distance / cmps

            if instantMovement: time = 0

            try:
                print "moving uarm"
                self.uArm.moveToWithTime(self.pos['x'], self.pos['y'], self.pos['z'], time)
            except ValueError:
                printf("Robot.refresh(): ERROR: Robot out of bounds and the uarm_python library crashed!")

            self.positionChanged = False

    def updateServo(self, num):
        if not self.newServoStatus[num] == self.servoStatus[num]:
            if self.newServoStatus[num]:
                #Attach the servo
                self.uArm.servoAttach(num)
                self.servoStatus[num] = True
                self.servoAttached     = True  #This prompts the robot to "moveToWithTime" with 0 as time
                printf("Robot.updateServo(): Servo", num, "attached")
            else:
                #Detach the servo
                self.uArm.servoDetach(num)
                self.servoStatus[num] = False
                printf("Robot.updateServo(): Servo", num, "detached")



    def setupThread(self, com):
        printf("Robot.setupThread(): Thread Created")
        try:
            self.uArm = Uarm(com)
            #self.servoDetach()
            printf("Robot.setupThread(): uArm successfully connected")

        except serial.SerialException:
            printf("Robot.setupThread(): ERROR SerialException while setting uArm to ", com)
        self.running = False
        self.refresh()

    def setUArm(self, com):
        if com is not None and not self.running:
            printf("Robot.setUArm(): Setting uArm to com", com, "...")
            self.uArm    = None  #This will prevent the 'play script' button from activating
            setupThread  = Thread(target=lambda: self.setupThread(com))
            self.running = True
            setupThread.start()

        else:
            if self.running: printf("Robot.setUArm() ERROR: setUArm() run while setupThread was already running!")
        self.setPos(**self.home)




#Functions that combine the camera and robot
def getDirectionToTarget(targetPos, screenDimensions, tolerance):
    """
    Returns what direction in the x and y (relative) the robot should move
    """
    targetFocus = [screenDimensions[0] / 2, screenDimensions[1] / 2]
    sign        = lambda x: (1.0, -1.0)[x < 0]  #sign(x) will return the sign of a number'


    ##Calculate the pixel distance from the target focus to the target object
    #distance = ((targetPos[0] - targetFocus[0]) ** 2 + (targetPos[1] - targetFocus[1]) ** 2) ** 0.5
    yMove = 0.0
    xMove = 0.0
    xDist = targetFocus[0] - targetPos[0]
    yDist = targetFocus[1] - targetPos[1]

    #Figure out what direction to move and how much
    if abs(yDist) >= tolerance:
        yMove  = sign(yDist)


    if abs(xDist) >= tolerance:
        xMove  = sign(xDist)

    #PERFORM THE MOVE
    if not (abs(xDist) < tolerance and abs(yDist) < tolerance):
        return xMove, -yMove
    else:
        return True


def getRelative(x1, y1, baseAngle):
    angle = math.radians(baseAngle) - math.radians(90)

    x = x1 * math.cos(angle) - y1 * math.sin(angle)
    y = x1 * math.sin(angle) + y1 * math.cos(angle)
    return  x, y

