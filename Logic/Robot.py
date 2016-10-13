"""
This software was designed by Alexander Thiel
Github handle: https://github.com/apockill
Email: Alex.D.Thiel@Gmail.com


The software was designed originaly for use with a robot arm, particularly uArm (Made by uFactory, ufactory.cc)
It is completely open source, so feel free to take it and use it as a base for your own projects.

If you make any cool additions, feel free to share!


License:
    This file is part of uArmCreatorStudio.
    uArmCreatorStudio is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    uArmCreatorStudio is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with uArmCreatorStudio.  If not, see <http://www.gnu.org/licenses/>.
"""
import serial
import serial.tools.list_ports
from time                        import sleep
from threading                   import Thread, RLock
from Logic.Global                import printf
from Logic.CommunicationProtocol import Device
__author__ = "Alexander Thiel"



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



    servo0  ->  Base Servo
    servo1  ->  Stretch Servo
    servo2  ->  Height Servo
    servo3  ->  Wrist Servo
    """

    def __init__(self):
        # Cache Variables that keep track of robot state
        self.speed             = 10                        # In cm / second (or XYZ [unit] per second)
        self.coord             = [None, None, None]        # Keep track of the robots position
        self.gripperStatus     = False                     # Keep track of the robots gripper status
        self.servoAttachStatus = [True, True, True, True]  # Keep track of what servos are attached
        self.servoAngleStatus  = [None, None, None, 90.0]  # Wrist is 90 degrees as default

        # Create some ranges to allow movement within (need to make a better solution)
        # self.xMin, self.xMax =  -35, 35
        # self.yMin, self.yMax =    0, 40
        # self.zMin, self.zMax =  -10, 30

        # Set up some constants for other functions to use
        self.home      = {'x': 0.0, 'y': 15.0, 'z': 15}


        self.__exiting = False    # When true, any time-taking functions will exit ASAP. Used for quickly ending threads
        self.__uArm    = None     # The communication protocol
        self.__lock    = RLock()  # This makes the robot library thread-safe

        # Whether or not the setupThread is running
        self.__threadRunning   = False

        # Convenience function for clamping a number to a range
        self.clamp = lambda lower, num, higher: max(lower, min(num, higher))



    def getMoving(self):
        """
        Check if the robot is currently moving.
        :return: True or False, if robot is moving
        """

        if not self.connected() or self.__exiting:
            printf("Robot| Robot not avaliable, returning False")
            return False

        with self.__lock:
            return self.__uArm.getMoving()

    def getTipSensor(self):
        """
        Get if the robots tip sensor is currently being pressed.
        :return: True or False if the sensor is pressed
        """

        if not self.connected() or self.__exiting:
            printf("Robot| Robot not avaliable, returning False for Tip Sensor")
            return False

        with self.__lock:
            return self.__uArm.getTipSensor()

    def getCoords(self):
        """
        Get the current XYZ coordinates of the robot
        :return: [X, Y, Z] List. If robot is not connect, [0.0, 0.0, 0.0]
        """

        if not self.connected() or self.__exiting:
            printf("Robot| Robot not avaliable, return 0 for all coordinates")
            return [0.0, 0.0, 0.0]

        with self.__lock:
            return self.__uArm.getXYZCoords()

    def getAngles(self):
        """
        Get a list of the robots current servo angle readings
        :return: [servo0, servo1, servo2, servo3] angles
        """

        if not self.connected() or self.__exiting:
            printf("Robot| Robot not avaliable, returning 0 for angle")
            return [0.0, 0.0, 0.0, 0.0]

        with self.__lock:
            return self.__uArm.getServoAngles()

    def getFK(self, servo0, servo1, servo2):
        """
        Get the forward kinematic calculations for the robots servos.
        :return: [X, Y, Z] list
        """
        if not self.connected() or self.__exiting:
            printf("Robot| Robot not avaliable, returning 0 for FK")
            return [0.0, 0.0, 0.0]

        with self.__lock:
            return self.__uArm.getFK(servo0, servo1, servo2)

    def getIK(self, x, y, z):
        """
        Get the inverse kinematic calculations for a certain XYZ location.
        :return: [X, Y, Z] list
        """
        if not self.connected() or self.__exiting:
            printf("Robot| Robot not avaliable, returning 0 for IK")
            return [0.0, 0.0, 0.0]

        with self.__lock:
            return self.__uArm.getIK(x, y, z)



    def setPos(self, x=None, y=None, z=None, coord=None, relative=False, wait=True):
        """
        Set the position of the robot, with many possible parameters and ways of setting.
        This function will not send information to the robot if the robot is already at that desired state.

        :param x: X position
        :param y: Y position
        :param z: Z position
        :param coord: a tuple of (x, y, z)
        :param relative: True or False, if true, the move will be relativ to the robots current position
        :param wait: True or False: If true, the function will wait for the robot to finish the move after sending it
        """

        if not self.connected() or self.__exiting:
            printf("Robot| Robot not avaliable, canceling position change")
            return

        def setVal(value, axis, relative):
            if value is not None:
                if relative:
                    self.coord[axis] += value
                else:
                    self.coord[axis] = value


        # Make sure positional servos are attached, so that the positional cache is updated
        self.setActiveServos(servo0=True, servo1=True, servo2=True)

        if coord is not None:
            x, y, z = coord

        with self.__lock:
            posBefore = self.coord[:]  # Make a copy of the pos right now

            setVal(x, 0, relative)
            setVal(y, 1, relative)
            setVal(z, 2, relative)


            # Make sure all X, Y, and Z values are within a reachable range (not a permanent solution)
            # if self.coord[0] is not None and self.coord[1] is not None and self.coord[2] is not None:
            #     if self.xMin > self.coord[0] or self.coord[0] > self.xMax:
            #         printf("Robot| X is out of bounds. Requested: ", self.coord[0])
            #         self.coord[0] = self.clamp(self.xMin, self.coord[0], self.xMax)
            #
            #     if self.yMin > self.coord[1] or self.coord[1] > self.yMax:
            #         printf("Robot| Y is out of bounds. Requested: ", self.coord[1])
            #         self.coord[1] = self.clamp(self.yMin, self.coord[1], self.yMax)
            #
            #     if self.zMin > self.coord[2] or self.coord[2] > self.zMax:
            #         printf("Robot| Z is out of bounds. Requested: ", self.coord[2])
            #         self.coord[2] = self.clamp(self.zMin, self.coord[2], self.zMax)


            # If this command has changed the position, then move the robot
            if not posBefore == self.coord:

                try:
                    self.__uArm.setXYZ(self.coord[0], self.coord[1], self.coord[2], self.speed)


                    # Update the servoAngleStatus by doing inverse kinematics on the current position to get the new angles
                    posAngles = list(self.__uArm.getIK(self.coord[0], self.coord[1], self.coord[2]))
                    self.servoAngleStatus  = posAngles + [self.servoAngleStatus[3]]

                    # Since moves cause servos to attach, update the servoStatus
                    self.servoAttachStatus = [True, True, True, True]

                except ValueError:
                    printf("Robot| ERROR: Robot out of bounds and the uarm_python library crashed!")


                # Wait for robot to finish move, but if in exiting mode, just continue
                if wait:
                    while self.getMoving():
                        if self.__exiting: break
                        sleep(.1)

    def setServoAngles(self, servo0=None, servo1=None, servo2=None, servo3=None, relative=False):
        """
        Set the angle of a servo, or as many servos as you want.
        :param servo0:
        :param servo1:
        :param servo2:
        :param servo3:
        :param relative: If you want to move to a relative position to the servos current position
        """

        if not self.connected() or self.__exiting:
            printf("Robot| Robot not avaliable, canceling wrist change")
            return

        def setServoAngle(servoNum, angle, rel):
            with self.__lock:
                if rel:
                    newAngle = angle + self.servoAngleStatus[servoNum]
                else:
                    newAngle = angle

                # Clamp the value
                beforeClamp = newAngle

                if newAngle > 180: newAngle = 180
                if newAngle <   0: newAngle = 0
                if not newAngle == beforeClamp:
                    printf("Robot| ERROR: Tried to set angle to a value less than 0 or greater than 180!")


                # Set the value and save it in the cache
                if not self.servoAngleStatus[servoNum] == newAngle:
                    self.__uArm.setServo(servoNum, newAngle)
                    self.servoAngleStatus[servoNum] = newAngle


        if servo0 is not None: setServoAngle(0, servo0, relative)
        if servo1 is not None: setServoAngle(1, servo1, relative)
        if servo2 is not None: setServoAngle(2, servo2, relative)
        if servo3 is not None: setServoAngle(3, servo3, relative)

    def setActiveServos(self, all=None, servo0=None, servo1=None, servo2=None, servo3=None):
        """
        Attach or detach a servo. Simple do True to attach and False to detach. Don't specify any servo you don't
        want to touch.
        :param all: Attach or detach all servos
        :param servo0:
        :param servo1:
        :param servo2:
        :param servo3:
        """

        if not self.connected() or self.__exiting:
            printf("Robot| Robot not avaliable, canceling servo change")
            return


        # If a positional servo is attached, get the robots current position and update the self.pos cache
        oldServoStatus = self.servoAttachStatus[:]

        def setServo(servoNum, status):
            # Verify that it is a dfiferent servo position before sending
            if self.servoAttachStatus[servoNum] == status: return

            with self.__lock:
                if status:
                    self.__uArm.setServoAttach(servoNum)
                else:
                    self.__uArm.setServoDetach(servoNum)
                self.servoAttachStatus[servoNum] = status


        # If anything changed, set the appropriate newServoStatus to reflect that
        if all is not None: servo0, servo1, servo2, servo3 = all, all, all, all


        if servo0 is not None: setServo(0, servo0)
        if servo1 is not None: setServo(1, servo1)
        if servo2 is not None: setServo(2, servo2)
        if servo3 is not None: setServo(3, servo3)

        # Make an array of which servos have been newly attached.
        attached = [oldServoStatus[i] is False and self.servoAttachStatus[i] is True for i in range(3)]

        # If any positional servos have been attached, update the self.pos cache with the robots current position
        if any(attached):
            with self.__lock:
                curr = self.getCoords()
                self.coord =  list(curr)
                self.servoAngleStatus = list(self.__uArm.getServoAngles())

    def setPump(self, status):
        """
        Turn the gripper on or off
        :param status: True or False
        """

        if not self.connected() or self.__exiting:
            printf("Robot| Robot not avaliable, canceling gripper change")
            return

        if not self.gripperStatus == status:
            with self.__lock:
                self.gripperStatus  = status
                self.__uArm.setPump(self.gripperStatus)

    def setBuzzer(self, frequency, duration):
        """
        Set the robots buzzer.
        :param frequency: In HZ
        :param duration:  In seconds
        """

        if not self.connected() or self.__exiting:
            printf("Robot| Robot not avaliable, canceling buzzer change")
            return
        with self.__lock:
            self.__uArm.setBuzzer(frequency, duration)


    def stopMoving(self):
        """
        Stop the robot's ongoing movement
        """
        if not self.connected() or self.__exiting:
            printf("Robot| Robot not avaliable, canceling position change")
            return

        with self.__lock:
            self.__uArm.setStop()


    # Functions that don't send communications to the robot
    def connected(self):
        """
        Check if the robot is currently connected
        :return: Returns True if robot is connected properly. False if not.
        """

        if self.__uArm is None:         return False  # If the communication protocol class hasn't been created,
        if not self.__uArm.connected(): return False  # If the Serial is not connected
        if self.__threadRunning:        return False  # If the setupThread is running
        return True

    def getErrorsToDisplay(self):
        if self.__uArm is not None:
            return self.__uArm.getErrorsToDisplay()
        else:
            return []

    def setSpeed(self, speed):
        """
        Set the speed for future setPos moves, until speed is set again
        :param speed: In cm/s
        """
        # Changes a class wide variable that affects the move commands in self.refresh()
        self.speed = speed



    def __setupThread(self, com):
        """
        This runs a thread for connecting to the robot. During this thread, the robot cannot accept any commands
        :param com: COM port that the robot is connected to
        """

        printf("Robot| Thread Created")


        self.__uArm = Device(com)

        # Check if the uArm was able to connect successfully
        if self.__uArm.connected():
            printf("Robot| SUCCESS: uArm successfully connected")
            # self.__uArm.setXYZ(self.home['x'], self.home['y'], self.home['z'], self.speed)
            self.__threadRunning = False
            self.setPos(**self.home)
            self.setActiveServos(all=False)
            return
        else:
            printf("Robot| FAILURE: uArm was unable to connect!")

        self.__threadRunning = False

    def setUArm(self, com):
        """
        Connect a uArm, at COM port 'com'
        :param com: COM port
        """

        if com is not None and not self.__threadRunning:
            self.__threadRunning = True
            printf("Robot| Setting uArm to ", com)
            setup = Thread(target=lambda: self.__setupThread(com))
            setup.start()

        else:
            printf("Robot| ERROR: Tried setting uArm when it was already set!")

    def setExiting(self, exiting):
        """
        When True, this will prevent the robot from completing any moves or lagging the program. The idea is that
        when you are exiting a script, it has to happen quickly. This prevents any lag for waiting for the robot,
        and cuts all communication. When False everything is normal and the robot communicates normally

        :param exiting: True-> communication with robot is cut off. False -> Everything works normally
        """
        # if exiting:
        #     printf("Robot| Setting Robot to Exiting mode. All commands should be ignored")
        self.__exiting = exiting



