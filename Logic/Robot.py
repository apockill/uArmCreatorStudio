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
        self.uArm    = None
        self.__speed = 10     # In cm / second (or XYZ [unit] per second)

        self.pos   = {'x': 0.0, 'y': -15.0, 'z': 15.0}
        self.__positionChanged = True


        # Keep track of the robots gripper status
        self.__gripperStatus   = False
        self.__gripperChanged  = True  # This should only be used in Robot.refresh() to activate the gripper


        # If there is ever a change in a servos status, it is stored in this container until
        # the 'refresh' function is run and the new values are sent to the robot
        self.__newServoStatus  = [True, True, True, True]
        self.__servoStatus     = [True, True, True, True]


        # Handle the recording of the wrist position, and whether or not it has been changed
        self.__wrist           = 90.0  # Angle from 0 to 180 of the robots wrist position
        self.__wristChanged    = True  # Tracks whether or not the new wrist position has been sent to the robot or not



        self.__threadRunning   = False  # Wether or not the setupThread is running

        # Set up some constants for other functions to use
        self.home      = {'x': 0.0, 'y': -15.0, 'z': 15.0}
        self.maxHeight = 25


    def getMoving(self):
        if not self.connected():
            printf("Robot.getMoving(): Robot not found or setupThread is running, returning False")
            return False
        else:
            return self.uArm.getIsMoving()

    def getTipSensor(self):
        if not self.connected():
            printf("Robot.getTipSensor(): Robot not found or setupThread is running, returning False")
            return False
        else:
            return self.uArm.getTipSensor()

    def getCurrentCoord(self):
        if not self.connected():
            printf("Robot.getCurrentCoord(): Robot not found or setupThread is running, return 0 for all coordinates")
            return [0.0, 0.0, 0.0]
        else:
            return self.uArm.getCurrentCoord()

    def getServoAngle(self, servoNumber):
        if not self.connected():
            printf("Robot.getServoAngle(): Robot not found or setupThread is running, returning 0 for angle")
            return 0
        else:
            return self.uArm.getServoAngle(servoNumber)


    def connected(self):
        if self.uArm is None:         return False  # If the communication protocol class hasn't been created,
        if not self.uArm.connected(): return False  # If the Serial is not connected
        if self.__threadRunning:        return False  # If the setupThread is running
        return True



    def setPos(self, **kwargs):
        if not self.connected():
            printf("Robot.setPos(): ERROR: Robot not found or setupThread is running, canceling position change")
            return

        relative = kwargs.get('relative', False)
        posBefore = dict(self.pos)

        for name, value in kwargs.items():  # Cycles through any variable that might have been in the kwargs. This is any position command!
            if name in self.pos:  #If it is a position statement.
                if self.pos[name] is "": continue
                if relative:
                    self.pos[name] += value
                else:
                    self.pos[name] = value

        # If this command has changed the position, or if the position was changed earlier
        self.__positionChanged = (not (posBefore == self.pos)) or self.__positionChanged

    def setWrist(self, angle, relative=False):
        if not self.connected():
            printf("Robot.setWrist(): ERROR: Robot not found or setupThread is running, canceling wrist change")
            return

        newWrist = self.__wrist
        if relative:
            newWrist += angle
        else:
            newWrist  = angle

        if not self.__wrist == newWrist:
            self.__wrist        = newWrist
            self.__wristChanged = True

    def setServos(self, all=None, servo1=None, servo2=None, servo3=None, servo4=None):
        if not self.connected():
            printf("Robot.setServos(): ERROR: Robot not found or setupThread is running, canceling servo change")
            return

        # If anything changed, set the appropriate newServoStatus to reflect that

        if all is not None: servo1, servo2, servo3, servo4 = all, all, all, all

        if servo1 is not None: self.__newServoStatus[0] = servo1
        if servo2 is not None: self.__newServoStatus[1] = servo2
        if servo3 is not None: self.__newServoStatus[2] = servo3
        if servo4 is not None: self.__newServoStatus[3] = servo4

    def setGripper(self, status):
        if not self.connected():
            printf("Robot.setGripper(): ERROR: Robot not found or setupThread is running, canceling gripper change")
            return

        if not self.__gripperStatus == status:
            self.__gripperStatus  = status
            self.__gripperChanged = True

    def setBuzzer(self, frequency, duration):
        if not self.connected():
            printf("Robot.setGripper(): ERROR: Robot not found or setupThread is running, canceling buzzer change")
            return

        self.uArm.setBuzzer(frequency, duration)

    def setSpeed(self, speed):
        # Changes a class wide variable that affects the move commands in self.refresh()
        printf("Robot.setSpeed(): ERROR: Setting speed to ", speed)
        self.__speed = speed




    def wait(self):
        # Waits until the robot completes its move or whatever it's doing
        while self.getMoving(): sleep(.1)

    def refresh(self, override=False):

        # Check that the robot is connected
        if not self.connected():
            printf("Robot.refresh(): ERROR: Tried sending command while uArm not connected, or while setting up.")
            return


        # Handle any wrist position changes. Don't wait for robot, since this movement is usually rare and one-off
        if self.__wristChanged:
            self.uArm.moveWrist(self.__wrist)
            # Make sure that the wrist servo is marked down as attached. Robot does this automatically
            self.__servoStatus[3], self.__newServoStatus[3] = True, True
            self.__wristChanged = False


        # Wait for robot to be done moving before doing anything
        if not override:
            self.wait()



        # Handle any gripper changes. Make sure it happens after the wait command
        if self.__gripperChanged:
            if self.__gripperStatus:
                self.uArm.gripperOn()
            else:
                self.uArm.gripperOff()
            self.__gripperChanged = False


        # The robot has an implimented feature to prevent the servos from "snapping" back
        self.__updateServos()


        # Perform a moves in self.pos array
        if self.__positionChanged:
            try:
                self.uArm.moveToWithSpeed(self.pos['x'], self.pos['y'], self.pos['z'], self.__speed)
                self.__servoStatus[0], self.__newServoStatus[0] = True, True
                self.__servoStatus[1], self.__newServoStatus[1] = True, True
                self.__servoStatus[2], self.__newServoStatus[2] = True, True
            except ValueError:
                printf("Robot.refresh(): ERROR: Robot out of bounds and the uarm_python library crashed!")

            self.__positionChanged = False

    def __updateServos(self):
        if not self.connected():
            printf("Robot.setServos(): ERROR: Robot not found or setupThread is running, canceling servo update")
            return

        for i, servoVal in enumerate(self.__servoStatus):
            if not self.__newServoStatus[i] == self.__servoStatus[i]:
                if self.__newServoStatus[i]:
                    # Attach the servo
                    self.uArm.servoAttach(i)
                    self.__servoStatus[i] = True
                else:
                    # Detach the servo
                    self.uArm.servoDetach(i)
                    self.__servoStatus[i] = False


    def __newServoAttached(self):
        # Boolean value that determines if a servo has been attached but this has not been sent to robot
        for i, servoVal in enumerate(self.__servoStatus):
            if not self.__newServoStatus[i] == servoVal and self.__newServoStatus[i]:
                return True



    def __setupThread(self, com):
        printf("Robot.setupThread(): Thread Created")

        try:
            self.uArm = Uarm(com)

            # Check if the uArm was able to connect successfully
            if self.uArm.connected():
                printf("Robot.setupThread(): uArm successfully connected")
            else:
                printf("Robot.setupThread(): uArm was unable to connect!")
                self.uArm = None

        except serial.SerialException:
            printf("Robot.setupThread(): ERROR SerialException while setting uArm to ", com)

        self.__threadRunning = False

    def setUArm(self, com):
        if com is not None and not self.__threadRunning:
            self.__threadRunning = True
            printf("Robot.setUArm(): Setting uArm to ", com)
            setup = Thread(target=lambda: self.__setupThread(com))
            setup.start()

        else:
            printf("Robot.setUArm(): ERROR: Tried setting uArm when it was already set!")





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

