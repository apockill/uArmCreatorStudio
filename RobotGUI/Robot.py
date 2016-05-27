import serial
import serial.tools.list_ports
import math
from RobotGUI.UArmTextCommunication_1 import Uarm
from RobotGUI.Global                  import printf
from threading                        import Thread
# from time import sleep  #Only use in refresh() command after attaching servos



def getConnectedRobots():
    #Returns any arduino serial ports in a list [port, port, port]
    #This is used to let the user choose the correct port that is their robot
    ports = list(serial.tools.list_ports.comports())
    return ports


class Robot:

    def __init__(self, comPort):
        self.uArm = None
        self.home = {"x": 0.0, "y": -15.0, "z": 15.0}
        self.pos =     {'x': 0.0, 'y': -15.0, 'z': 15.0}

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
        self.wrist = 180.0             #Angle from 0 to 180 of the robots wrist position
        self.wristChanged = True      #Tracks whether or not the new wrist position has been sent to the robot or not

        self.positionChanged = True
        self.gripperChanged  = False  #This should only be used in Robot.refresh() to activate the gripper
        self.servoAttached   = False  #If True, refresh() will move the robot previous pos before it attached the servo
        self.running         = False  #Wether or not the setupThread is running


    def getMoving(self):
        if not self.connected():
            printf("Robot.getMoving(): Robot not found or setupThread is running, returning False")
            return False
        else:
            return self.uArm.isMoving()

    def getCurrentCoord(self):
        if not self.connected():
            printf("Robot.currentCoord(): Robot not found or setupThread is running, returning 0 for all coordinates..")
            return {"x": 0, "y": 0, "z": 0}
        else:
            print("getting uarm coord")
            return self.uArm.currentCoord()

    def getBaseAngle(self):
        if not self.connected():
            printf("Robot.getBaseAngle(): Robot not found or setupThread is running, returning 90 for base angle...")
            return 90
        else:
            printf("Robot.getBaseAngle(): Getting base servo angle for robot... ERROR this is not implimented yet")
            return self.uArm.readAngle(1)

    def connected(self):
        if self.uArm is None:         return False
        if not self.uArm.connected(): return False
        if self.running:              return False
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

    def setWrist(self, wrist):
        self.wrist = wrist
        self.wristChanged = True

    def setServos(self, **kwargs):
        # If anything changed, set the appropriate newServoStatus to reflect that
        self.newServoStatus[1] = kwargs.get('servo1', self.newServoStatus[1])
        self.newServoStatus[2] = kwargs.get('servo2', self.newServoStatus[2])
        self.newServoStatus[3] = kwargs.get('servo3', self.newServoStatus[3])
        self.newServoStatus[4] = kwargs.get('servo4', self.newServoStatus[4])

    def setGripper(self, status):
        if not self.connected():
            print("status: ", status)
            printf("Robot.setGripper(): ERROR: No uArm connected, could not set gripper to", status)
            return

        if not self.gripperStatus == status:
            self.gripperStatus = status
            if self.gripperStatus:
                self.uArm.pumpOn()
            else:
                self.uArm.pumpOff()



    def getTipSensor(self):
        # If the robots tip sensor is currently being pressed
        # Currently buggy, so not implimented
        return False



    def refresh(self, **kwargs):
        # Custom moveTime
        speed        = kwargs.get("speed", 20)          # Desired speed (cm per second)
        moveTime     = kwargs.get("time", -1)
        overrideMove = kwargs.get("override", False)  # If robot is already moving, set a new path



        # Check that the robot is connected
        if not self.connected():
            printf("Robot.refresh(): ERROR: Tried sending command while uArm not connected, or while setting up.")
            return


        # Wait for robot to be done moving before doing anything
        while not overrideMove and self.getMoving(): pass


        # Attach/Detach servos and prevent weird snaps by setting position when attaching a servo
        if self.__newServoAttached():
            currXYZ  = self.getCurrentCoord()
        self.__updateServos()
        if self.servoAttached:
            self.servoAttached = False
            self.uArm.moveToWithTime(currXYZ['x'], currXYZ['y'], currXYZ['z'], 0)
            self.gripperChanged = False


        if self.wristChanged:
            print(self.servoStatus)
            self.uArm.wrist(self.wrist)
            self.wristChanged = False

        # Perform a moves in self.pos array
        dist = lambda p1, p2: ((p2['x'] - p1['x']) ** 2 + (p2['y'] - p1['y']) ** 2 + (p2['z'] - p1['z']) ** 2) ** .5
        if self.positionChanged:
            if moveTime == -1:
                # Calculate the amount of time the move should take so as to reach an avg speed of cmps (cm per second)
                currXYZ  = self.getCurrentCoord()
                distance = dist(currXYZ, self.pos)
                time     = distance / speed
            else:
                time = moveTime

            try:
                self.uArm.moveToWithTime(self.pos['x'], self.pos['y'], self.pos['z'], time)
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
            printf("Robot.setupThread(): uArm successfully connected")
        except serial.SerialException:
            printf("Robot.setupThread(): ERROR SerialException while setting uArm to ", com)
        self.running = False
        self.refresh(override=True)

    def setUArm(self, com):
        if com is not None and not self.running:
            printf("Robot.setUArm(): Setting uArm to ", com)
            setup = Thread(target=lambda: self.__setupThread(com))
            setup.start()
            #self.uArm    = Uarm(com)  #This will prevent the 'play script' button from activating
        self.setPos(**self.home)





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

