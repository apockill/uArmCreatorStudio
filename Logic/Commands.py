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
import math
from Logic             import RobotVision as rv
from Logic.Global      import printf, wait
from Logic.LogicObject import LogicObject
__author__ = "Alexander Thiel"



"""
Example Class Structure
EVERY COMMAND MUST RETURN FALSE IF IT FAILS TO RUN
If it fails to run, return False. The idea is that users will know that any command will return false if it fails,
and thus have contingencies. Plus its a feature that is useful only if you know about it, and doesn't add complexity
otherwise!

class NameCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(NameCommand, self).__init__(parameters)

        # Load any objects, modules, calibrations, etc  that will be used in the run Section here. Use getVerifyXXXX()
        self.robot   = self.getVerifyRobot(env)
        self.vision  = self.getVerifyVision(env)

        if len(self.errors): return

        # Here, start tracking if your command requires it
        # Add any objects to be tracked

    def run(self):
        printf("A quick description, usually using parameters, of the command that is running")
        return True
"""


class Command(LogicObject):
    def __init__(self, parameters):
        super(Command, self).__init__()
        self.parameters = parameters

    def run(self):
        pass




#   BASIC CONTROL COMMANDS
class MoveXYZCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(MoveXYZCommand, self).__init__(parameters)

        # Load necessary objects
        self.interpreter = interpreter
        self.robot       = self.getVerifyRobot(env)

    def run(self):
        newX, successX = self.interpreter.evaluateExpression(self.parameters['x'])
        newY, successY = self.interpreter.evaluateExpression(self.parameters['y'])
        newZ, successZ = self.interpreter.evaluateExpression(self.parameters['z'])


        # Special case: If the parameter is "" set the new val to None and success to True
        if self.parameters['x'] == "": newX, successX = None, True
        if self.parameters['y'] == "": newY, successY = None, True
        if self.parameters['z'] == "": newZ, successZ = None, True



        printf("Moving robot to ", newX, " ", newY, " ", newZ, " ")
        if successX and successY and successZ:
            self.robot.setPos(x=newX, y=newY, z=newZ, relative=self.parameters['relative'])
            return True
        else:
            printf("ERROR in evaluating either X Y or Z: ", successX, successY, successZ)
            return False


class MoveWristCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(MoveWristCommand, self).__init__(parameters)

        self.interpreter = interpreter
        self.robot       = self.getVerifyRobot(env)

    def run(self):


        newAngle, success = self.interpreter.evaluateExpression(self.parameters['angle'])

        if success:
            # If relative, get the current wrist angle then add that to newAngle

            printf("Moving robot wrist to ", newAngle)
            self.robot.setServoAngles(servo3=newAngle, relative=self.parameters['relative'])
            return True
        else:
            printf("ERROR in parsing new wrist angle. Expression: ", self.parameters['angle'])
            return False


class MotionRecordingCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(MotionRecordingCommand, self).__init__(parameters)

        # Load any objects, modules, calibrations, etc  that will be used in the run Section here. Use getVerifyXXXX()
        self.robot       = self.getVerifyRobot(env)
        self.pathObj     = self.getVerifyObject(env, self.parameters["objectID"])
        self.interpreter = interpreter
        self.exitFunc    = interpreter.isExiting

        if len(self.errors): return

        self.motionPath = self.pathObj.getMotionPath()

    def run(self):
        if len(self.errors): return

        printf("Playing motionPath ", self.parameters["objectID"])

        # Evaluate the "Speed" variable
        newSpeed, success = self.interpreter.evaluateExpression(self.parameters['speed'])

        if not success or newSpeed <= 0:
            printf("ERROR: In evaluating 'speed' parameter for motionpath")
            return False


        # Send the path to the "path player"
        rv.playMotionPath(self.motionPath, self.robot, self.exitFunc, speedMultiplier=newSpeed, reversed=self.parameters["reversed"])
        return True


class SpeedCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(SpeedCommand, self).__init__(parameters)

        # Load any objects that will be used in the run Section here
        self.robot       = env.getRobot()
        self.interpreter = interpreter

    def run(self):
        speed, success = self.interpreter.evaluateExpression(self.parameters['speed'])

        printf("Setting robot speed to ", speed, "cm/s")

        # Split the wait into incriments of 0.1 seconds each, and check if the thread has been stopped at each incriment
        if success:
            printf("Setting speed to ", speed)
            self.robot.setSpeed(speed)
            return True
        else:
            printf("ERROR: Expression ", self.parameters['speed'], " failed to evaluate correctly!")
            return False


class DetachCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(DetachCommand, self).__init__(parameters)

        self.robot = self.getVerifyRobot(env)

    def run(self):
        printf("Detaching servos ",
               self.parameters['servo1'],
               self.parameters['servo2'],
               self.parameters['servo3'],
               self.parameters['servo4'])


        printf("Detaching certain servos")
        if self.parameters['servo1']: self.robot.setActiveServos(servo0=False)
        if self.parameters['servo2']: self.robot.setActiveServos(servo1=False)
        if self.parameters['servo3']: self.robot.setActiveServos(servo2=False)
        if self.parameters['servo4']: self.robot.setActiveServos(servo3=False)

        return True


class AttachCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(AttachCommand, self).__init__(parameters)

        self.robot = self.getVerifyRobot(env)

    def run(self):
        printf("Attaching servos ", self.parameters['servo1'],
                                                         self.parameters['servo2'],
                                                         self.parameters['servo3'],
                                                         self.parameters['servo4'])

        printf("Attaching certain servos")
        if self.parameters['servo1']: self.robot.setActiveServos(servo0=True)
        if self.parameters['servo2']: self.robot.setActiveServos(servo1=True)
        if self.parameters['servo3']: self.robot.setActiveServos(servo2=True)
        if self.parameters['servo4']: self.robot.setActiveServos(servo3=True)

        return True


class WaitCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(WaitCommand, self).__init__(parameters)

        self.interpreter = interpreter

    def run(self):

        waitTime, success = self.interpreter.evaluateExpression(self.parameters['time'])


        # Split the wait into incriments of 0.1 seconds each, and check if the thread has been stopped at each incriment
        if success:
            printf("Waiting for ", waitTime, " seconds")
            wait(waitTime, self.interpreter.isExiting)

            return True
        else:
            printf("ERROR: Expression ", self.parameters['time'], " failed to evaluate correctly!")
            return False


class GripCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(GripCommand, self).__init__(parameters)

        self.robot = self.getVerifyRobot(env)

    def run(self):
        printf("Setting gripper to True")
        self.robot.setGripper(True)
        return True


class DropCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(DropCommand, self).__init__(parameters)

        self.robot = self.getVerifyRobot(env)

    def run(self):
        printf("Setting gripper to False")
        self.robot.setGripper(False)
        return True


class BuzzerCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(BuzzerCommand, self).__init__(parameters)

        # Load any objects that will be used in the run Section here
        self.robot       = self.getVerifyRobot(env)
        self.interpreter = interpreter

    def run(self):

        frequency, fSuccess = self.interpreter.evaluateExpression(self.parameters['frequency'])
        duration,  dSuccess = self.interpreter.evaluateExpression(self.parameters['time'])

        # Check if evaluation worked
        if fSuccess and dSuccess:
            # Send buzzer command
            printf("Playing frequency", self.parameters['frequency'], " for ", self.parameters['time'])
            self.robot.setBuzzer(frequency, duration)

            # If the user wants to sleep while the buzzer is running, then sleep.
            if self.parameters["waitForBuzzer"]:
                wait(duration, self.interpreter.isExiting)

            return True
        else:
            printf("ERROR: ", self.parameters['frequency'],
                   " or ", self.parameters["time"], "failed to evaluate correctly!")
            return False







#   Robot + Vision Commands
class MoveRelativeToObjectCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(MoveRelativeToObjectCommand, self).__init__(parameters)

        self.interpreter = interpreter

        # Load any objects that will be used in the run Section here
        self.robot      = self.getVerifyRobot(env)
        self.vision     = self.getVerifyVision(env)
        self.trackable  = self.getVerifyObject(env, self.parameters["objectID"])
        coordCalib      = self.getVerifyCoordCalibrations(env)


        if len(self.errors): return
        self.ptPairs = coordCalib["ptPairs"]

        # Turn on tracking for the relevant object
        self.vision.addTarget(self.trackable)

    def run(self):
        if len(self.errors) > 0: return False

        newX, successX = self.interpreter.evaluateExpression(self.parameters['x'])
        newY, successY = self.interpreter.evaluateExpression(self.parameters['y'])
        newZ, successZ = self.interpreter.evaluateExpression(self.parameters['z'])


        # Special case: If the parameter is "" set the new val to None and success to True
        if self.parameters['x'] == "": newX, successX = None, True
        if self.parameters['y'] == "": newY, successY = None, True
        if self.parameters['z'] == "": newZ, successZ = None, True



        # If X Y and Z could not be evaluated correctly, quit
        if not successX or not successY or not successZ:
            printf("ERROR in parsing either X Y or Z: ", successX, successY, successZ)
            return False


        printf("Moving robot to obj, relative XYZ is:  ", newX, " ", newY, " ", newZ)


        # Get a super recent frame of the object
        trackedObj = self.vision.getObjectBruteAccurate(self.trackable,
                                                        minPoints   = rv.MIN_POINTS_FOCUS,
                                                        maxAge= rv.MAX_FRAME_AGE_MOVE)
        if trackedObj is None: return False



        # Get the object position
        printf("Found object. Moving to XY Location now.")
        pos     = rv.getPositionTransform(trackedObj.center, direction="toRob", ptPairs=self.ptPairs)
        pos[2] += trackedObj.view.height



        # Create a function that will return "None" if new val is None, and otherwise it will sum pos and new val
        printf(newX is None, newX)
        noneSum = lambda objPos, newPos: None if newPos is None else objPos + newPos



        # Set the robots position. Any "None" values simply don't change anything
        self.robot.setPos(x=noneSum(pos[0], newX),
                          y=noneSum(pos[1], newY),
                          z=noneSum(pos[2], newZ))
        return True


class MoveWristRelativeToObjectCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(MoveWristRelativeToObjectCommand, self).__init__(parameters)
        self.interpreter = interpreter
        coordCalib       = self.getVerifyCoordCalibrations(env)
        self.robot       = self.getVerifyRobot(env)
        self.vision      = self.getVerifyVision(env)
        self.trackable   = self.getVerifyObject(env, self.parameters["objectID"])
        self.relToBase   = self.parameters["relToBase"]

        if len(self.errors): return
        # Turn on tracking for the relevant object

        self.ptPairs = coordCalib["ptPairs"]
        self.vision.addTarget(self.trackable)

    def run(self):
        if len(self.errors): return

        # Before doing any tracking, evaluate the "Relative" number to make sure its valid
        relativeAngle, success = self.interpreter.evaluateExpression(self.parameters["angle"])
        if not success:
            printf("Could not determine the relative angle for the wrist. Canceling command. ")
            return False


        # Find the object using vision
        _, tracked = self.vision.getObjectLatestRecognition(self.trackable)
        if tracked is None:
            printf("Could not find ", self.trackable.name, " in order to set wrist relative")
            return False


        # This is the rotation of the object in degrees, derived from the camera
        targetAngle = math.degrees(tracked.rotation[2])




        cntr = tracked.center
        if self.relToBase:
            # If the angle is relative to the base angle, do the math here and add it to target angle.

            TOCC = cntr   # Tracked Object Camera Coordinates
            ROCC = rv.getPositionTransform((0, 0, 0), "toCam", self.ptPairs)  # Robot Origin Camera Coordinates
            baseAngle = 90 - math.degrees(math.atan( (ROCC[1] - TOCC[1]) / (ROCC[0] - TOCC[0])))
            targetAngle += baseAngle - 90
        else:
            # If the angle is relative to x Axis, do different math and add it to target angle
            a = rv.getPositionTransform((0, 0, 0), "toCam", self.ptPairs)
            b = rv.getPositionTransform((10, 0, 0), "toCam", self.ptPairs)

            # TORC    = rv.getPositionTransform(cntr, "toRob", self.ptPairs)  # Tracked Object Robot Coordinates
            # RXCC    = rv.getPositionTransform((0, cntr[1], cntr[2]), "toCam", self.ptPairs)  # Robot XAxis Camera Coordinates
            xOffset =  math.degrees(math.atan( (a[1] - b[1]) / (a[0] - b[0])))
            targetAngle += 90 - xOffset
            print("XOffset: ", xOffset)
            print("Target: ", targetAngle)

        # Add the "Relative" angle to the wrist
        targetAngle += relativeAngle

        # Normalize the value so that it's between 0 and 180
        while targetAngle < 0: targetAngle += 180
        while targetAngle > 180: targetAngle -= 180



        # Set the robots wrist to the new value
        self.robot.setServoAngles(servo3 = targetAngle)


        return True


class PickupObjectCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(PickupObjectCommand, self).__init__(parameters)

        coordCalib      = self.getVerifyCoordCalibrations(env)
        self.robot      = self.getVerifyRobot(env)
        self.vision     = self.getVerifyVision(env)
        self.trackable  = self.getVerifyObject(env, self.parameters["objectID"])
        self.rbMarker   = self.getVerifyObject(env, "Robot Marker")
        self.exitFunc   = interpreter.isExiting

        if len(self.errors): return

        self.ptPairs    = coordCalib["ptPairs"]
        self.grndHeight = coordCalib["groundPos"][2]

        # Turn on tracking for the relevant object
        self.vision.addTarget(self.trackable)
        self.vision.addTarget(self.rbMarker)

    def run(self):
        if len(self.errors) > 0: return False

        ret = rv.pickupObject(self.trackable, self.rbMarker, self.ptPairs, self.grndHeight,
                              self.robot, self.vision, self.exitFunc)

        return ret


class TestObjectSeenCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(TestObjectSeenCommand, self).__init__(parameters)

        # Load any objects, modules, calibrations, etc  that will be used in the run Section here. Use getVerifyXXXX()
        self.vision  = self.getVerifyVision(env)
        self.trackable = self.getVerifyObject(env, self.parameters["objectID"])


        if len(self.errors): return

        self.vision.addTarget(self.trackable)


        self.maxAge = self.parameters["age"]
        self.minPts = self.vision.planeTracker.MIN_MATCH_COUNT * (self.parameters["ptCount"] + 1)

    def run(self):
        if len(self.errors): return

        printf("Testing if ", self.parameters["objectID"], " was seen")
        tracked = self.vision.searchTrackedHistory(trackable  = self.trackable,
                                                   maxAge= self.maxAge,
                                                   minPoints= self.minPts)

        # Return if an object that matched that criteria was tracked
        if self.parameters["not"]:
            return tracked is None
        else:
            return tracked is not None


class TestObjectLocationCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(TestObjectLocationCommand, self).__init__(parameters)

        # Load any objects, modules, calibrations, etc  that will be used in the run Section here. Use getVerifyXXXX()
        self.vision    = self.getVerifyVision(env)
        self.trackable = self.getVerifyObject(env, self.parameters["objectID"])
        vStream   = self.getVerifyVStream(env)


        if len(self.errors): return
        self.vision.addTarget(self.trackable)

        # Get the dimensions of the frame
        frame = vStream.getFrame()
        self.height, self.width, _ = frame.shape

        # Create the location "quad" for simplicity
        p1, p2      = self.parameters["location"]
        self.quad   = np.float32([[p1[0], p1[1]], [p2[0], p1[1]], [p2[0], p2[1]], [p1[0], p2[1]]])


    def run(self):
        if len(self.errors): return False

        # printf("Testing if ", self.parameters["objectID"], " is at location ", self.parameters["location"])

        tracked = self.vision.searchTrackedHistory(trackable=self.trackable)



        # If the object was not seen, exit
        if tracked is None: return False

        # print("Center: ", tracked.center, "Quad", tracked.quad)


        inCount = 0
        for coord in tracked.quad:
            if rv.pointInPolygon(coord, self.quad):
                inCount += 1




        # Check if the appropriate part of the object is within the boundaries
        ret = False
        if self.parameters["part"] == "any":
            ret =  inCount > 0

        if self.parameters["part"] == "all":
            ret =  inCount == 4

        if self.parameters["part"] == "center":
            center = sum(tracked.quad) / 4
            ret =  rv.pointInPolygon(center, self.quad)




        if self.parameters['not']: ret = not ret

        if ret:
            printf("Tested ", self.parameters["objectID"], " location. ", inCount, " points were in location. ")
        # If 'not', flip the return value
        return ret


class VisionMoveXYZCommand(MoveXYZCommand):

    def __init__(self, env, interpreter, parameters=None):
        super(VisionMoveXYZCommand, self).__init__(env, interpreter, parameters)

        self.interpreter = interpreter

        coordCalib       = self.getVerifyCoordCalibrations(env)
        self.vision      = self.getVerifyVision(env)
        self.rbMarker    = self.getVerifyObject(env, "Robot Marker")


        if len(self.errors): return
        self.ptPairs    = coordCalib["ptPairs"]

        # Turn on tracking for the relevant object
        self.vision.addTarget(self.rbMarker)

    def run(self):
        if len(self.errors): return

        # First, move to the position like the normal MoveXYZ command does
        success = super(VisionMoveXYZCommand, self).run()

        # Check if the parent couldn't run correctly. If not, exit
        if not success: return False


        # Get the new position that the robot should be at
        destRobCoord = self.robot.coord[:]


        # Get the robots new position
        currentCamCoord, avgMag, avgDir = self.vision.getObjectSpeedDirectionAvg(self.rbMarker)

        # If the robot couldn't be seen, exit
        if currentCamCoord is None:
            printf("Could not find robot marker after move. Exiting without Vision adjustment.")
            return False


        # Get the robots "True" position from the cameras point of view
        currentRobPos = rv.getPositionTransform(currentCamCoord, "toRob", self.ptPairs)


        # Find the move offset (aka, the error and how to correct it)
        offset        = np.asarray(destRobCoord) - np.asarray(currentRobPos)
        magnitude = np.linalg.norm(offset)


        # If there's too much error, something bad must have happened. Avoid doing any corrections
        if magnitude > 5:
            printf("Correction magnitude too high. Canceling move. Offset: ", offset, "Magnitude: ", magnitude)
            return False


        # Move the offset amount
        printf("Correcting move. Offset: ", offset, " Magnitude: ", magnitude)
        self.robot.setPos(coord=offset, relative=True)

        return True






#   LOGIC COMMANDS
class StartBlockCommand(Command):
    """
    Mark the start a block of code with this command
    """

    def __init__(self, env, interpreter, parameters=None):
        super(StartBlockCommand, self).__init__(parameters)


class EndBlockCommand(Command):
    """
    Mark the end a block of code with this command
    """

    def __init__(self, env, interpreter, parameters=None):
        super(EndBlockCommand, self).__init__(parameters)


class ElseCommand(Command):
    """
    Mark the end a block of code with this command
    """

    def __init__(self, env, interpreter, parameters=None):
        super(ElseCommand, self).__init__(parameters)


class SetVariableCommand(Command):
    """
        Sets a variable to an expression in the interpreter. It will first check if the variable exists, if not, it will
         hen set the variable to zero. After that it will set the variable to the expression to the new value.

         If the expression did not evaluate (If an error occured) it will simply not set the variable
        to the new value.
    """

    def __init__(self, env, interpreter, parameters=None):
        super(SetVariableCommand, self).__init__(parameters)

        self.interpreter = interpreter

    def run(self):
        # If the variable does not exist yet, add it to the namespace with a value of 0
        if self.parameters["variable"] not in self.interpreter.nameSpace:
            script = str(self.parameters["variable"]) + " = 0"
            self.interpreter.evaluateScript(script)


        # Set the value of the variable by building a string of "variable = value" and running it in exec
        script = self.parameters["variable"] + " = " + self.parameters["expression"]
        self.interpreter.evaluateScript(script)

        printf("Setting ", self.parameters["variable"], " to ", self.parameters["expression"])

        return True


class TestVariableCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(TestVariableCommand, self).__init__(parameters)
        self.interpreter = interpreter

    def run(self):
        interpreter   = self.interpreter

        # Get the variable. If that doesn't work, quit
        # variableValue, successVar = interpreter.getVariable(self.parameters['variable'])
        # if not successVar: return False


        # Evaluate the expression. If that doesn't work, quit
        # compareValue, successExp = interpreter.evaluateExpression(self.parameters['expression'])
        # print("Compare value: ", compareValue)
        # if not successExp: return False

        # Compare the value of the expression using the operator from the parameters
        operations   = ['==', '!=', '>', '<']
        variable     = self.parameters['variable']
        operation    = operations[self.parameters['test']]
        expression   = self.parameters["expression"]
        scriptString = variable + operation + expression  #

        testResult, success = interpreter.evaluateExpression(scriptString)

        if not success: return False

        printf("Testing: ", scriptString)
        print(testResult, success)
        # If the expression was evaluated correctly, then return the testResult. Otherwise, return False
        return testResult


class ScriptCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(ScriptCommand, self).__init__(parameters)

        # Load any objects, modules, calibrations, etc  that will be used in the run Section here. Use getVerifyXXXX()
        self.interpreter = interpreter
        self.env = env
        if len(self.errors): return

        # Here, start tracking if your command requires it
        # Add any objects to be tracked

    def run(self):
        if len(self.errors): return
        # printf("Running a custom script by user...")

        return self.interpreter.evaluateScript(self.parameters["script"])


class EndProgramCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(EndProgramCommand, self).__init__(parameters)

    def run(self):
        printf("Attempting to shut down program now...")
        return "Kill"


class EndEventCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(EndEventCommand, self).__init__(parameters)

        # Load any objects that will be used in the run Section here
        self.interpreter = interpreter


    def run(self):
        printf("Exiting current event")
        return "Exit"


class RunTaskCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(RunTaskCommand, self).__init__(parameters)
        self.env          = env
        self.interpreter = interpreter


        # # Load any objects, modules, calibrations, etc  that will be used in the run Section here. Use getVerifyXXXX()
        # self.robot   = self.getVerifyRobot(env)
        # self.vision  = self.getVerifyVision(env)

        if len(self.errors): return

        # Here, start tracking if your command requires it
        # Add any objects to be tracked

    def run(self):
        printf("This ")
        exitFunc = self.interpreter.parentExiting
        if self.interpreter.parentExiting is None:
            exitFunc = self.interpreter.isExiting

        try:
            self.interpreter.createChildInterpreter(self.parameters["filename"],
                                                        exitFunc)
            return True
        except RuntimeError as e:
            printf("ERROR: MAXIMUM RECURSION DEPTH EXCEEDED. ")
            return False







