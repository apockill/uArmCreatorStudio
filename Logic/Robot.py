import math
import serial
import serial.tools.list_ports
from threading    import Thread, RLock
from time         import sleep  #Only use in refresh() command while querying robot if it's done moving
from Logic.Global import printf

from Logic.UArmTextCommunication_1 import Uarm


def getConnectedRobots():
    # Returns any arduino serial ports in a list [port, port, port]
    # This is used to let the user choose the correct port that is their robot
    ports = list(serial.tools.list_ports.comports())
    return ports


class Robot:
    """
    'Robot' Class is intended to be a thread-safe wrapper for whatever communication protocol your robot arm uses,
    as long as it has 4 servos and the communication protocol returns the same format that this class expects.

    The connection is threaded, so that you can connect to your robot via serial while doing other things.
    This comes in handy when using the GUI, so connecting to your robot doesn't lock things up.

    Furthermore, by being thread-safe there will never be issues of communicating with the robot via two different
    threads.

    The biggest advantage of this class is that it avoids communication with the robot at all costs. What this means
    is that it caches all information and commands sent to robot, and will NOT send two commands that are the same.
    So if you tell it to go to X0Y0Z0 (for example) then tell it to go to X0Y0Z0 again, it will not send the second
    command, unless something has occured that would prompt that (like servo detach/attach).

    Furthermore this class will allow you to cut off communication with the robot with the "setExiting" command.
    This allows the user to exit a thread very quickly by no longer allowing the robot to send commands or wait,
    thus speeding up the process of leaving a thread.
    """
    def __init__(self):
        self.exiting = False   # When true, any time-taking functions will exit ASAP. Used for quickly ending threads.
        self.uArm    = None    # The communication protocol
        self.lock    = RLock() # This makes the robot library thread-safe


        # Cache Variables that keep track of robot state
        self.__speed = 10                                  # In cm / second (or XYZ [unit] per second)
        self.pos   = {'x': None, 'y': None, 'z': None}     # Keep track of the robots position
        self.__gripperStatus   = False                     # Keep track of the robots gripper status
        self.__servoStatus     = [True, True, True, True]
        self.__servoAngleCache = [None, None, None, 90.0]  # Wrist is 90 degrees as default


        # Wether or not the setupThread is running
        self.__threadRunning   = False

        # Set up some constants for other functions to use
        self.home      = {'x': 0.0, 'y': -15.0, 'z': 25.0}


        # Convenience function for clamping a number to a range
        self.clamp = lambda lower, num, higher: max(lower, min(num, higher))

        # Create some ranges to allow movement within (need to make a better solution)
        self.xMin, self.xMax = -30, 30
        self.yMin, self.yMax = -30, -5
        self.zMin, self.zMax =  -5, 25


    def getMoving(self):
        if not self.connected() or self.exiting:
            printf("Robot.getMoving(): Robot not found or setupThread is running, returning False")
            return False

        with self.lock:
            return self.uArm.getIsMoving()

    def getTipSensor(self):
        if not self.connected() or self.exiting:
            printf("Robot.getTipSensor(): Robot not found or setupThread is running, returning False")
            return False

        with self.lock:
            return self.uArm.getTipSensor()

    def getCurrentCoord(self):
        if not self.connected() or self.exiting:
            printf("Robot.getCurrentCoord(): Robot not found or setupThread is running, return 0 for all coordinates")
            return [0.0, 0.0, 0.0]

        with self.lock:
            return self.uArm.getCurrentCoord()

    def getServoAngles(self):
        if not self.connected() or self.exiting:
            printf("Robot.getServoAngle(): Robot not found or setupThread is running, returning 0 for angle")
            return [0, 0, 0, 0]

        with self.lock:
            return self.uArm.getServoAngles()

    def getFK(self, servo0, servo1, servo2):
        if not self.connected() or self.exiting:
            printf("Robot.getServoAngle(): Robot not found or setupThread is running, returning 0 for angle")
            return [0, 0, 0]

        with self.lock:
            return self.uArm.getFK(servo0, servo1, servo2)


    def setPos(self, x=None, y=None, z=None, coord=None, relative=False, wait=True):
        """

        :param x: X position
        :param y: Y position
        :param z: Z position
        :param coord: a tuple of (x, y, z)
        :param relative: True or False, if true, the move will be relativ to the robots current position
        :param wait: True or False: If true, the function will wait for the robot to finish the move after sending it
        """
        if not self.connected() or self.exiting:
            printf("Robot.setPos(): Robot not found or setupThread is running, canceling position change")
            return

        def setVal(value, name, relative):
            if value is not None:
                if relative:
                    self.pos[name] += value
                else:
                    self.pos[name] = value


        # Make sure positional servos are attached, so that the positional cache is updated
        self.setActiveServos(servo0=True, servo1=True, servo2=True)

        if coord is not None:
            x, y, z = coord

        self.lock.acquire()
        posBefore = dict(self.pos)  # Make a copy of the pos right now

        setVal(x, 'x', relative)
        setVal(y, 'y', relative)
        setVal(z, 'z', relative)


        # Make sure all X, Y, and Z values are within a reachable range (not a permanent solution)
        if self.pos['x'] is not None and self.pos['y'] is not None and self.pos['z'] is not None:
            if self.xMin > self.pos['x'] or self.pos['x'] > self.xMax:
                printf("Robot.robot.setPos(): X is out of bounds. Requested: ", self.pos['x'])
                self.pos['x'] = self.clamp(self.xMin, self.pos['x'], self.xMax)

            if self.yMin > self.pos['y'] or self.pos['y'] > self.yMax:
                printf("Robot.robot.setPos(): Y is out of bounds. Requested: ", self.pos['y'])
                self.pos['y'] = self.clamp(self.yMin, self.pos['y'], self.yMax)

            if self.zMin > self.pos['z'] or self.pos['z'] > self.zMax:
                printf("Robot.robot.setPos(): Z is out of bounds. Requested: ", self.pos['z'])
                self.pos['z'] = self.clamp(self.zMin, self.pos['z'], self.zMax)


        # If this command has changed the position, then move the robot
        if not posBefore == self.pos:

            try:
                self.uArm.moveToWithSpeed(self.pos['x'], self.pos['y'], self.pos['z'], self.__speed)
                self.__servoAngleCache = list(self.uArm.getIK(self.pos['x'], self.pos['y'], self.pos['z'])) + [self.__servoAngleCache[3]]

                # Since moves cause servos to lock, update the servoStatus
                self.__servoStatus[0], self.__servoStatus[1], self.__servoStatus[2]  = True, True, True
            except ValueError:
                printf("Robot.refresh(): ERROR: Robot out of bounds and the uarm_python library crashed!")

            # Wait for robot to finish move, but if exiting, just continue
            if wait:
                while self.getMoving():
                    if self.exiting:
                        printf("Robot.setPos(): Exiting early!")
                        break
                    sleep(.1)

        self.lock.release()

    def setServoAngles(self, servo0=None, servo1=None, servo2=None, servo3=None, relative=False):

        if not self.connected() or self.exiting:
            printf("Robot.setWrist(): Robot not found or setupThread is running, canceling wrist change")
            return

        def setServoAngle(servoNum, angle, rel):
            with self.lock:
                if rel:
                    newAngle = angle + self.__servoAngleCache[servoNum]
                else:
                    newAngle = angle

                # Clamp the value
                beforeClamp = newAngle
                if newAngle > 180: newAngle = 180
                if newAngle <   0: newAngle = 0
                if not newAngle == beforeClamp:
                    printf("Robot.setServoAngles(): Tried to set angle to a value less than 0 or greater than 180!")


                # Set the value and save it in the cache
                if not self.__servoAngleCache[servoNum] == newAngle:
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

        # If a positional servo is attached, get the robots current position and update the self.pos cache
        oldServoStatus = self.__servoStatus[:]

        def setServo(servoNum, status):
            with self.lock:
                if status:

                    self.uArm.servoAttach(servoNum)
                else:
                    self.uArm.servoDetach(servoNum)
                self.__servoStatus[servoNum] = status


        # If anything changed, set the appropriate newServoStatus to reflect that
        if all is not None: servo0, servo1, servo2, servo3 = all, all, all, all


        if servo0 is not None: setServo(0, servo0)
        if servo1 is not None: setServo(1, servo1)
        if servo2 is not None: setServo(2, servo2)
        if servo3 is not None: setServo(3, servo3)

        # Make an array of which servos have been newly attached.
        attached = [oldServoStatus[i] is False and self.__servoStatus[i] is True for i in range(3)]

        # If any positional servos have been attached, update the self.pos cache with the robots current position
        if any(attached):
            curr = self.getCurrentCoord()
            oldPos = dict(self.pos)
            print("old")
            self.pos['x'], self.pos['y'], self.pos['z'] =  curr
            print("new", self.pos)
            print("old servo pos: ", self.__servoAngleCache)
            self.__servoAngleCache = list(self.uArm.getServoAngles())
            print("new servo pos: ", self.__servoAngleCache)

    def setGripper(self, status):
        if not self.connected() or self.exiting:
            printf("Robot.setGripper(): Robot not found or setupThread is running, canceling gripper change")
            return

        if not self.__gripperStatus == status:
            with self.lock:
                self.__gripperStatus  = status
                self.uArm.setGripper(self.__gripperStatus)

    def setBuzzer(self, frequency, duration):
        if not self.connected() or self.exiting:
            printf("Robot.setGripper(): Robot not found or setupThread is running, canceling buzzer change")
            return
        with self.lock:
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
                self.uArm.moveToWithSpeed(self.home['x'], self.home['y'], self.home['z'], self.__speed)
                self.__threadRunning = False
                self.setPos(**self.home)
                self.setActiveServos(all=False)
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

