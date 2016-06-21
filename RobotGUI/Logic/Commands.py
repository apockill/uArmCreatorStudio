from RobotGUI.Logic.Global import printf
from time                  import sleep  # For WaitCommand

"""
Example Class Structure


class NameCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(NameCommand, self).__init__(parameters)

        # Load any objects that will be used in the run Section here
        self.robot   = self.getVerifyRobot(env)
        self.vstream = self.getVerifyVision(env)


        # For any objects that don't have a "getVerify####" on them, add the error here specifically for them
        self.errors.append["Error message about what's missing"]

    def run(self):
        printf("NameCommand.run(): A quick description, usually using parameters, of the command that is running"

"""



class Command:
    def __init__(self, parameters):
        self.parameters = parameters
        self.errors     = []  # Errors are created in the "getXXX(env)" functions, and are strings

    def run(self):
        pass

    # By having functions to pull things from env, I can automatically generate Error messages for things that go wrong
    def getVerifyRobot(self, env):
        robot = env.getRobot()
        if not robot.connected():
            self.errors.append("Robot")
        return env.getRobot()

    def getVerifyVision(self, env):
        vStream = env.getVStream()
        if not vStream.connected():
            self.errors.append("Camera")
        return env.getVision()


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
        else:
            printf("MoveXYZCommand.run(): ERROR in parsing either X Y or Z: ", successX, successY, successZ)

        self.robot.refresh(override=self.parameters['override'])


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
        else:
            print("MoveWristCommand.run(): ERROR in parsing new wrist angle. Expression: ", self.parameters['angle'])


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
        else:
            printf("SpeedCommand.run(): ERROR: Expression ", self.parameters['speed'], " failed to evaluate correctly!")


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
        else:
            printf("WaitCommand.run(): ERROR: Expression ", self.parameters['time'], " failed to evaluate correctly!")


class GripCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(GripCommand, self).__init__(parameters)

        self.robot = self.getVerifyRobot(env)

    def run(self):
        printf("GripCommand.run(): Setting gripper to True")
        self.robot.setGripper(True)


class DropCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(DropCommand, self).__init__(parameters)

        self.robot = self.getVerifyRobot(env)

    def run(self):
        printf("DropCommand.run(): Setting gripper to False")
        self.robot.setGripper(False)


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
        if not fSuccess or not dSuccess:
            printf("BuzzerCommand.run(): ERROR: ", self.parameters['frequency'],
                   " or ", self.parameters["time"], "failed to evaluate correctly!")
            return


        # Send buzzer command
        printf("BuzzerCommand.run(): Playing frequency", self.parameters['frequency'], " for ", self.parameters['time'])
        self.robot.setBuzzer(frequency, duration)

        # If the user wants to sleep while the buzzer is running, then sleep.
        if self.parameters["waitForBuzzer"]:
            sleep(duration)


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


        operations = ['==', '!=', '>', '<']
        expressionString = str(variableValue) + operations[self.parameters['test']] + self.parameters["expression"]
        testResult, success = interpreter.evaluateExpression(expressionString)

        printf("TestVariableCommand.run(): Testing if ", self.parameters['variable'],
                                                         operations[self.parameters['test']],
                                                         self.parameters["expression"])

        return testResult and success


class EndProgramCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(EndProgramCommand, self).__init__(parameters)

        # Load any objects that will be used in the run Section here
        self.interpreter = interpreter


    def run(self):
        printf("EndProgramCommand.run(): Attempting to shut down program now...")
        self.interpreter.killApp = True


class EndEventCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(EndEventCommand, self).__init__(parameters)

        # Load any objects that will be used in the run Section here
        self.interpreter = interpreter


    def run(self):
        printf("EndEventCommand.run(): Exiting current event")
        return "Exit"

