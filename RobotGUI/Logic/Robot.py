import math
import serial
import serial.tools.list_ports
from threading                              import Thread
from RobotGUI.Logic.Global                  import printf
from RobotGUI.Logic.UArmTextCommunication_1 import Uarm
from time import sleep  #Only use in refresh() command while querying robot if it's done moving



def getConnectedRobots():
    # Returns any arduino serial ports in a list [port, port, port]
    # This is used to let the user choose the correct port that is their robot
    ports = list(serial.tools.list_ports.comports())
    return ports


class Robot:

    def __init__(self):
        self.uArm = None

        self.pos   =     {'x': 0.0, 'y': -15.0, 'z': 15.0}
        self.speed = 45     # In cm / second (or XYZ [unit] per second)

        # Every time uArm is connected correctly, all servos are attached. Set the values to match this.
        # These variables are used to keep track of which servos are attached
        self.gripperStatus = False
        self.servoStatus = {1: True,
                            2: True,
                            3: True,
                            4: True}

        # If there is ever a change in a servos status, it is stored in this container until
        # the 'refresh' function is run and the new values are sent to the robot
        self.newServoStatus =   {1: True,
                                 2: True,
                                 3: True,
                                 4: True}

        # Handle the recording of the wrist position, and whether or not it has been changed
        self.wrist           = 90.0      #Angle from 0 to 180 of the robots wrist position
        self.wristChanged    = True      #Tracks whether or not the new wrist position has been sent to the robot or not

        self.positionChanged = True
        self.gripperChanged  = False  #This should only be used in Robot.refresh() to activate the gripper
        self.servoAttached   = False  #If True, refresh() will move the robot previous pos before it attached the servo
        self.running         = False  #Wether or not the setupThread is running


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
            return [0, 0, 0]
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
        if self.running:              return False  # If the setupThread is running
        return True



    def setPos(self, **kwargs):
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
        self.positionChanged = (not (posBefore == self.pos)) or self.positionChanged

    def setWrist(self, angle, relative=False):
        newWrist = self.wrist
        if relative:
            newWrist += angle
        else:
            newWrist  = angle

        if not self.wrist == newWrist:
            self.wrist        = newWrist
            self.wristChanged = True
        else:
            print("WRIST DIDNT CHANGE YO!!!")

    def setServos(self, setAll=None, servo1=None, servo2=None, servo3=None, servo4=None):
        # If anything changed, set the appropriate newServoStatus to reflect that

        if setAll is not None: servo1, servo2, servo3, servo4 = setAll, setAll, setAll, setAll

        if servo1 is not None: self.newServoStatus[1] = servo1
        if servo2 is not None: self.newServoStatus[2] = servo2
        if servo3 is not None: self.newServoStatus[3] = servo3
        if servo4 is not None: self.newServoStatus[4] = servo4



    def setGripper(self, status):
        if not self.connected():
            printf("Robot.setGripper(): ERROR: No uArm connected, could not set gripper to", status)
            return

        if not self.gripperStatus == status:
            self.gripperStatus = status
            if self.gripperStatus:
                self.uArm.pumpOn()
            else:
                self.uArm.pumpOff()

    def setSpeed(self, speed):
        # Changes a class wide variable that affects the move commands in self.refresh()
        self.speed = speed

    def setBuzzer(self, frequency, duration):
        if not self.connected():
            printf("Robot.setBuzzer(): ERROR: No uArm connected, could not set frequency to", frequency, duration)
            return

        self.uArm.setBuzzer(frequency, duration)



    def refresh(self, override=False):

        # Check that the robot is connected
        if not self.connected():
            printf("Robot.refresh(): ERROR: Tried sending command while uArm not connected, or while setting up.")
            return


        # Handle any wrist position changes. Don't wait for robot, since this movement is usually rare and one-off
        if self.wristChanged:
            self.uArm.moveWrist(self.wrist)
            self.wristChanged = False

        # Wait for robot to be done moving before doing anything
        if not override:
            while self.getMoving(): sleep(.1)



        # Attach/Detach servos and prevent weird snaps by setting position when attaching a servo
        if self.__newServoAttached():
            currXYZ  = self.getCurrentCoord()

        self.__updateServos()

        # Move very quickly to the position you were in before servos were attached (reduces jerk)
        if self.servoAttached:
            self.servoAttached = False
            self.uArm.moveToWithTime(currXYZ[0], currXYZ[1], currXYZ[2], 0)
            self.gripperChanged = False


        # Perform a moves in self.pos array
        if self.positionChanged:
            try:
                self.uArm.moveToWithTime(self.pos['x'], self.pos['y'], self.pos['z'], self.speed)
            except ValueError:
                printf("Robot.refresh(): ERROR: Robot out of bounds and the uarm_python library crashed!")

            self.positionChanged = False

    def __updateServos(self):
        for key in self.servoStatus:
            if not self.newServoStatus[key] == self.servoStatus[key]:
                if self.newServoStatus[key]:
                    # Attach the servo
                    self.uArm.servoAttach(key)
                    self.servoStatus[key] = True
                else:
                    # Detach the servo
                    self.uArm.servoDetach(key)
                    self.servoStatus[key] = False

    def __newServoAttached(self):
        # Boolean value that determines if a servo has been attached but this has not been sent to robot
        for key, s in self.servoStatus.items():
            if not self.newServoStatus[key] == s and self.newServoStatus[key]:
                self.servoAttached = True
                return True



    def __setupThread(self, com):
        printf("Robot.setupThread(): Thread Created")

        try:
            self.uArm = Uarm(com)

            # Check if the uArm was able to connect successfully
            if self.uArm.connected():
                printf("Robot.setupThread(): uArm successfully connected")
                self.refresh(override=True)
            else:
                printf("Robot.setupThread(): uArm was unable to connect!")
                self.uArm = None

        except serial.SerialException:
            printf("Robot.setupThread(): ERROR SerialException while setting uArm to ", com)

        self.running = False

    def setUArm(self, com):
        if com is not None and not self.running:
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

