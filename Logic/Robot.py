import math
import serial
import serial.tools.list_ports
from threading    import Thread
from time         import sleep  #Only use in refresh() command while querying robot if it's done moving
from Logic.Global import printf

from Logic.UArmTextCommunication_1 import Uarm


def getConnectedRobots():
    # Returns any arduino serial ports in a list [port, port, port]
    # This is used to let the user choose the correct port that is their robot
    ports = list(serial.tools.list_ports.comports())
    return ports


class Robot:

    def __init__(self):
        self.exiting = False  # When true, any time-taking functions will exit ASAP. Used for quickly ending threads.
        self.uArm    = None
        self.__speed = 10     # In cm / second (or XYZ [unit] per second)

        self.pos   = {'x': None, 'y': None, 'z': None}

        # Convenience function for clamping a number to a range
        self.clamp = lambda lower, num, higher: max(lower, min(num, higher))

        # Keep track of the robots gripper status
        self.__gripperStatus   = False


        # If there is ever a change in a servos status, it is stored in this container until
        # the 'refresh' function is run and the new values are sent to the robot
        # servo1: Base   servo2: Stretch   servo3: Height   servo4: Wrist
        self.__servoStatus     = [True, True, True, True]
        self.__servoAngleCache = [None, None, None, 90.0]  # Wrist is 90 degrees as default



        # Wether or not the setupThread is running
        self.__threadRunning   = False

        # Set up some constants for other functions to use
        self.home      = {'x': 0.0, 'y': -15.0, 'z': 25.0}

        self.xMin, self.xMax = -30, 30
        self.yMin, self.yMax = -30, -5
        self.zMin, self.zMax =  -5, 25


    def getMoving(self):
        if not self.connected() or self.exiting:
            printf("Robot.getMoving(): Robot not found or setupThread is running, returning False")
            return False
        else:
            return self.uArm.getIsMoving()

    def getTipSensor(self):
        if not self.connected() or self.exiting:
            printf("Robot.getTipSensor(): Robot not found or setupThread is running, returning False")
            return False
        else:
            return self.uArm.getTipSensor()

    def getCurrentCoord(self):
        if not self.connected() or self.exiting:
            printf("Robot.getCurrentCoord(): Robot not found or setupThread is running, return 0 for all coordinates")
            return [0.0, 0.0, 0.0]
        else:
            return self.uArm.getCurrentCoord()

    def getServoAngles(self):
        if not self.connected() or self.exiting:
            printf("Robot.getServoAngle(): Robot not found or setupThread is running, returning 0 for angle")
            return [0, 0, 0, 0]
        else:
            return self.uArm.getServoAngles()



    def setPos(self, x=None, y=None, z=None, relative=False, wait=True):
        if not self.connected() or self.exiting:
            printf("Robot.setPos(): Robot not found or setupThread is running, canceling position change")
            return

        def setVal(value, name, relative):
            if value is not None:
                if relative:
                    self.pos[name] += value
                else:
                    self.pos[name] = value

        posBefore = dict(self.pos)  # Make a copy of the pos right now

        setVal(x, 'x', relative)
        setVal(y, 'y', relative)
        setVal(z, 'z', relative)


        # Make sure all X, Y, and Z values are within a reachable range (very primitive- need a permanent solution soon)
        if self.pos['x'] is not None and self.pos['y'] is not None and self.pos['z'] is not None:
            if self.xMin > self.pos['x'] or self.pos['x'] > self.xMax:
                printf("Robot.robot.setPos(): ERROR: X is out of bounds!", self.pos['x'])
                self.pos['x'] = self.clamp(self.xMin, self.pos['x'], self.xMax)

            if self.yMin > self.pos['y'] or self.pos['y'] > self.yMax:
                printf("Robot.robot.setPos(): ERROR: Y is out of bounds!", self.pos['y'])
                self.pos['y'] = self.clamp(self.yMin, self.pos['y'], self.yMax)

            if self.zMin > self.pos['z'] or self.pos['z'] > self.zMax:
                printf("Robot.robot.setPos(): ERROR: Z is out of bounds!", self.pos['z'])
                self.pos['z'] = self.clamp(self.zMin, self.pos['z'], self.zMax)



        # If this command has changed the position, then move the robot
        if not posBefore == self.pos:
            try:
                self.uArm.moveToWithSpeed(self.pos['x'], self.pos['y'], self.pos['z'], self.__speed)
                self.__servoAngleCache = list(self.uArm.getIK(self.pos['x'], self.pos['y'], self.pos['z'])) + [self.__servoAngleCache[3]]
                self.__servoStatus[0]  = True
                self.__servoStatus[1]  = True
                self.__servoStatus[2]  = True
            except ValueError:
                printf("Robot.refresh(): ERROR: Robot out of bounds and the uarm_python library crashed!")

            # Wait for robot to finish move, but if exiting, just continue
            if wait:
                while self.getMoving():
                    if self.exiting:
                        printf("Robot.setPos(): Exiting early!")
                        break
                    sleep(.1)

    def setServoAngles(self, servo0=None, servo1=None, servo2=None, servo3=None, relative=False):
        print("Cache", self.__servoAngleCache)
        if not self.connected() or self.exiting:
            printf("Robot.setWrist(): Robot not found or setupThread is running, canceling wrist change")
            return

        def setServoAngle(servoNum, angle, rel):
            if rel:
                newAngle = angle + self.__servoAngleCache[servoNum]
            else:
                newAngle = angle

            # Clamp the value
            if newAngle > 180: newAngle = 180
            if newAngle <   0: newAngle = 0

            # Set the value and save it in the cache
            self.uArm.setServo(servoNum, newAngle)
            self.__servoAngleCache[servoNum] = newAngle

        if servo0 is not None: setServoAngle(0, servo0, relative)
        if servo1 is not None: setServoAngle(1, servo1, relative)
        if servo2 is not None: setServoAngle(2, servo2, relative)
        if servo3 is not None: setServoAngle(3, servo3, relative)


    def setActiveServos(self, all=None, servo0=None, servo1=None, servo2=None, servo3=None):
        if not self.connected() or self.exiting:
            printf("Robot.setServos(): Robot not found or setupThread is running, canceling servo change")
            return

        def attachServo(servoNum, status):
            if status:
                self.uArm.servoAttach(servoNum)
            else:
                self.uArm.servoDetach(servoNum)
            self.__servoStatus[servoNum] = status

        # If anything changed, set the appropriate newServoStatus to reflect that
        if all is not None: servo0, servo1, servo2, servo3 = all, all, all, all

        if servo0 is not None: attachServo(0, servo0)
        if servo1 is not None: attachServo(1, servo1)
        if servo2 is not None: attachServo(2, servo2)
        if servo3 is not None: attachServo(3, servo3)


    def setGripper(self, status):
        if not self.connected() or self.exiting:
            printf("Robot.setGripper(): Robot not found or setupThread is running, canceling gripper change")
            return

        if not self.__gripperStatus == status:
            self.__gripperStatus  = status
            self.uArm.setGripper(self.__gripperStatus)

    def setBuzzer(self, frequency, duration):
        if not self.connected() or self.exiting:
            printf("Robot.setGripper(): Robot not found or setupThread is running, canceling buzzer change")
            return

        self.uArm.setBuzzer(frequency, duration)

    def setSpeed(self, speed):
        # Changes a class wide variable that affects the move commands in self.refresh()
        self.__speed = speed



    def connected(self):
        if self.uArm is None:         return False  # If the communication protocol class hasn't been created,
        if not self.uArm.connected(): return False  # If the Serial is not connected
        if self.__threadRunning:      return False  # If the setupThread is running
        return True



    def refresh(self, override=False):
        pass



    def __setupThread(self, com):
        printf("Robot.setupThread(): Thread Created")

        try:
            self.uArm = Uarm(com)

            # Check if the uArm was able to connect successfully
            if self.uArm.connected():
                printf("Robot.setupThread(): uArm successfully connected")
                self.__threadRunning = False
                self.setPos(wait=False, **self.home)
                return
            else:
                printf("Robot.setupThread(): uArm was unable to connect!")
                self.uArm = None

        except serial.SerialException:
            printf("Robot.setupThread(): ERROR: SerialException while setting uArm to ", com)

        self.__threadRunning = False

    def setUArm(self, com):
        if com is not None and not self.__threadRunning:
            self.__threadRunning = True
            printf("Robot.setUArm(): Setting uArm to ", com)
            setup = Thread(target=lambda: self.__setupThread(com))
            setup.start()

        else:
            printf("Robot.setUArm(): ERROR: Tried setting uArm when it was already set!")

    def setExiting(self, exiting):
        if exiting:
            printf("Robot.setExiting(): Setting robot to Exiting mode. All commands should be ignored")
        self.exiting = exiting




# Functions that combine the camera and robot
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

    # PERFORM THE MOVE
    if not (abs(xDist) < tolerance and abs(yDist) < tolerance):
        return xMove, -yMove
    else:
        return True


def getRelative(x1, y1, baseAngle):
    angle = math.radians(baseAngle) - math.radians(90)

    x = x1 * math.cos(angle) - y1 * math.sin(angle)
    y = x1 * math.sin(angle) + y1 * math.cos(angle)


    return x, y

