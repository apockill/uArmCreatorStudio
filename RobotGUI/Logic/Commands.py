from time                       import sleep  # For WaitCommand
from RobotGUI.Logic.Global      import printf
from RobotGUI.Logic             import RobotVision as rv
from RobotGUI.Logic.LogicObject import LogicObject


"""
Example Class Structure
EVERY COMMAND MUST RETURN FALSE IF IT FAILS TO RUN
If it fails to run, return False. The idea is that users will know that any command will return false if it fails,
and thus have contingencies. Plus its a feature that is useful only if you know about it, and doesn't add complexity
otherwise!

class NameCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(NameCommand, self).__init__(parameters)

        # Load any objects that will be used in the run Section here
        self.robot   = self.getVerifyRobot(env)
        self.vision  = self.getVerifyVision(env)


        # For any objects that don't have a "getVerify####" on them, add the error here specifically for them
        self.errors.append("Error message about what's missing")

    def run(self):
        printf("NameCommand.run(): A quick description, usually using parameters, of the command that is running")
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

        printf("MoveXYZCommand.run(): Moving robot to ", newX, " ", newY, " ", newZ, " ")

        if successX and successY and successZ:
            self.robot.setPos(x=newX, y=newY, z=newZ,
                                  relative=self.parameters['relative'])
            self.robot.refresh(override=self.parameters['override'])
            return True
        else:
            printf("MoveXYZCommand.run(): ERROR in parsing either X Y or Z: ", successX, successY, successZ)
            return False




class MoveWristCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(MoveWristCommand, self).__init__(parameters)

        self.interpreter = interpreter
        self.robot       = self.getVerifyRobot(env)

    def run(self):


        newAngle, success = self.interpreter.evaluateExpression(self.parameters['angle'])

        if success:
            printf("MoveWristCommand.run(): Moving robot wrist to ", newAngle)
            self.robot.setWrist(newAngle, relative=self.parameters['relative'])
            self.robot.refresh()
            return True
        else:
            print("MoveWristCommand.run(): ERROR in parsing new wrist angle. Expression: ", self.parameters['angle'])
            return False


class SpeedCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(SpeedCommand, self).__init__(parameters)

        # Load any objects that will be used in the run Section here
        self.robot       = env.getRobot()
        self.interpreter = interpreter

    def run(self):
        speed, success = self.interpreter.evaluateExpression(self.parameters['speed'])

        printf("SpeedCommand.run(): Setting robot speed to ", speed, "cm/s")

        # Split the wait into incriments of 0.1 seconds each, and check if the thread has been stopped at each incriment
        if success:
            printf("SpeedCommand.run(): Setting speed to ", speed)
            self.robot.setSpeed(speed)
            return True
        else:
            printf("SpeedCommand.run(): ERROR: Expression ", self.parameters['speed'], " failed to evaluate correctly!")
            return False


class DetachCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(DetachCommand, self).__init__(parameters)

        self.robot = self.getVerifyRobot(env)

    def run(self):
        printf("DetachCommand.run(): Detaching servos ",
               self.parameters['servo1'],
               self.parameters['servo2'],
               self.parameters['servo3'],
               self.parameters['servo4'])


        printf("DetachCommand.run(): Detaching certain servos")
        if self.parameters['servo1']: self.robot.setServos(servo1=False)
        if self.parameters['servo2']: self.robot.setServos(servo2=False)
        if self.parameters['servo3']: self.robot.setServos(servo3=False)
        if self.parameters['servo4']: self.robot.setServos(servo4=False)

        self.robot.refresh()
        return True


class AttachCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(AttachCommand, self).__init__(parameters)

        self.robot = self.getVerifyRobot(env)

    def run(self):
        printf("AttachCommand.run(): Attaching servos ", self.parameters['servo1'],
                                                         self.parameters['servo2'],
                                                         self.parameters['servo3'],
                                                         self.parameters['servo4'])

        printf("AttachCommand.run(): Attaching certain servos")
        if self.parameters['servo1']: self.robot.setServos(servo1=True)
        if self.parameters['servo2']: self.robot.setServos(servo2=True)
        if self.parameters['servo3']: self.robot.setServos(servo3=True)
        if self.parameters['servo4']: self.robot.setServos(servo4=True)

        self.robot.refresh()
        return True

class WaitCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(WaitCommand, self).__init__(parameters)

        self.interpreter = interpreter

    def run(self):

        waitTime, success = self.interpreter.evaluateExpression(self.parameters['time'])


        # Split the wait into incriments of 0.1 seconds each, and check if the thread has been stopped at each incriment
        if success:
            printf("WaitCommand.run(): Waiting for", waitTime, "seconds")
            sleep(waitTime)
            return True
        else:
            printf("WaitCommand.run(): ERROR: Expression ", self.parameters['time'], " failed to evaluate correctly!")
            return False


class GripCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(GripCommand, self).__init__(parameters)

        self.robot = self.getVerifyRobot(env)

    def run(self):
        printf("GripCommand.run(): Setting gripper to True")
        self.robot.setGripper(True)
        return True


class DropCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(DropCommand, self).__init__(parameters)

        self.robot = self.getVerifyRobot(env)

    def run(self):
        printf("DropCommand.run(): Setting gripper to False")
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
            printf("BuzzerCommand.run(): Playing frequency", self.parameters['frequency'], " for ", self.parameters['time'])
            self.robot.setBuzzer(frequency, duration)

            # If the user wants to sleep while the buzzer is running, then sleep.
            if self.parameters["waitForBuzzer"]:
                sleep(duration)

            return True
        else:
            printf("BuzzerCommand.run(): ERROR: ", self.parameters['frequency'],
                   " or ", self.parameters["time"], "failed to evaluate correctly!")
            return False






#   Robot + Vision Commands
class FocusOnObjectCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(FocusOnObjectCommand, self).__init__(parameters)

        # Load any objects that will be used in the run Section here
        self.robot      = self.getVerifyRobot(env)
        self.vision     = self.getVerifyVision(env)
        self.vStream    = self.getVerifyVStream(env)
        self.coordCalib = self.getVerifyCoordCalibrations(env)
        self.object     = self.getVerifyObject(env, self.parameters["objectID"])
        self.rbMarker   = self.getVerifyObject(env, "Robot Marker")

        print(self.errors)
        if len(self.errors): return

        # Turn on tracking for the relevant object
        self.vision.addTargetSamples(self.object.getSamples())
        self.vision.addTargetSamples(self.rbMarker.getSamples())
        self.vision.startTracker()

    def run(self):
        if len(self.errors) > 0: return False
        frameAge, trackObj = self.vision.getObjectLatestRecognition(self.object.name)
        if trackObj is None or frameAge > 5 or trackObj.ptCount < 30:
            printf("FocusOnObjectCommand.run(): FrameAge was too old or pointCount was too low, returning false!")
            return False

        pos = rv.getRobotPositionTransform(trackObj.center, self.coordCalib)
        self.robot.setPos(x=pos[0], y=pos[1])  # z=pos[2])
        self.robot.refresh()
        return True

#   Robot + Vision Commands
class PickupObjectCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(PickupObjectCommand, self).__init__(parameters)

        # Load any objects that will be used in the run Section here
        self.robot      = self.getVerifyRobot(env)
        self.vision     = self.getVerifyVision(env)
        self.vStream    = self.getVerifyVStream(env)
        self.coordCalib = self.getVerifyCoordCalibrations(env)
        self.object     = self.getVerifyObject(env, self.parameters["objectID"])
        self.rbMarker   = self.getVerifyObject(env, "Robot Marker")

        print(self.errors)
        if len(self.errors): return

        # Turn on tracking for the relevant object
        self.vision.addTargetSamples(self.object.getSamples())
        self.vision.addTargetSamples(self.rbMarker.getSamples())
        self.vision.startTracker()

    def run(self):
        if len(self.errors) > 0: return False

        frameAge, trackObj = self.vision.getObjectLatestRecognition(self.object.name)

        if trackObj is None or frameAge > 5 or trackObj.ptCount < 30:
            printf("PickupObjectCommand.run(): FrameAge was too old or pointCount was too low, returning false!")
            return False

        pos = rv.getRobotPositionTransform(trackObj.center, self.coordCalib)
        self.robot.setPos(x=pos[0], y=pos[1], z=rv.PICKUP_HEIGHT)  # z=pos[2])
        self.robot.refresh()
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

    def __init__(self, env, interpreter, parameters=None):
        super(SetVariableCommand, self).__init__(parameters)

        self.interpreter = interpreter

    def run(self):
        printf("SetVariableCommand.run(): Setting ", self.parameters["variable"], " to ", self.parameters["expression"])
        success = self.interpreter.setVariable(self.parameters["variable"],
                                               self.parameters["expression"])
        return success


class TestVariableCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(TestVariableCommand, self).__init__(parameters)
        self.interpreter = interpreter

    def run(self):
        interpreter   = self.interpreter

        # Get the variable. If that doesn't work, quit
        variableValue, successVar = interpreter.getVariable(self.parameters['variable'])
        if not successVar: return False


        # Evaluate the expression. If that doesn't work, quit
        compareValue, successExp = interpreter.evaluateExpression(self.parameters['expression'])
        if not successExp: return False

        # Compare the value of the expression using the operator from the parameters
        operations = ['==', '!=', '>', '<']
        expressionString = str(variableValue) + operations[self.parameters['test']] + self.parameters["expression"]
        testResult, success = interpreter.evaluateExpression(expressionString)

        printf("TestVariableCommand.run(): Testing if ", self.parameters['variable'],
                                                         operations[self.parameters['test']],
                                                         self.parameters["expression"])

        # If the expression was evaluated correctly, then return the testResult. Otherwise, return False
        return testResult and success


class EndProgramCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(EndProgramCommand, self).__init__(parameters)

        # Load any objects that will be used in the run Section here
        self.interpreter = interpreter

    def run(self):
        printf("EndProgramCommand.run(): Attempting to shut down program now...")
        self.interpreter.killApp = True
        return True


class EndEventCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(EndEventCommand, self).__init__(parameters)

        # Load any objects that will be used in the run Section here
        self.interpreter = interpreter


    def run(self):
        printf("EndEventCommand.run(): Exiting current event")
        return "Exit"

