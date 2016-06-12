from RobotGUI.Logic.Global import printf
from time import sleep  # For WaitCommand

"""
Example Class Structure


class NameCommand(Command):

    def __init__(self, env, parameters=None):
        super(NameCommand, self).__init__(parameters)

        # Load any objects that will be used in the run Section here
        self.robot   = env.getRobot()
        self.vstream = env.getVStream()

        # Set any errors that may have occured while creation
        if not self.robot.connected():
            self.errors.append("Robot Not Connected")

    def run(self, env):
        pass

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
        return robot


class MoveXYZCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(MoveXYZCommand, self).__init__(parameters)

        # Load necessary objects
        self.interpreter = interpreter
        self.robot       = self.getVerifyRobot(env)


    def run(self):
        printf("MoveXYZCommand.run(): Moving robot to ",
               self.parameters['x'], " ",
               self.parameters['y'], " ",
               self.parameters['z'], " ")

        newX, successX = self.interpreter.evaluateExpression(self.parameters['x'])
        newY, successY = self.interpreter.evaluateExpression(self.parameters['y'])
        newZ, successZ = self.interpreter.evaluateExpression(self.parameters['z'])

        if successX and successY and successZ:
            self.robot.setPos(x=newX, y=newY, z=newZ,
                                  relative=self.parameters['relative'])
        else:
            print("ERROR in parsing either X Y or Z: ", successX, successY, successZ)

        self.robot.refresh(override=self.parameters['override'])


class MoveWristCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(MoveWristCommand, self).__init__(parameters)

        self.interpreter = interpreter
        self.robot       = self.getVerifyRobot(env)

    def run(self):


        newAngle, success = self.interpreter.evaluateExpression(self.parameters['angle'])

        if success:
            self.robot.setWrist(newAngle, relative=self.parameters['relative'])
            self.robot.refresh()
        else:
            print("MoveWristCommand.run(): ERROR in parsing new wrist angle. Expression: ", self.parameters['angle'])


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


class SetVariableCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(SetVariableCommand, self).__init__(parameters)

        self.interpreter = interpreter

    def run(self):
        success = self.interpreter.setVariable(self.parameters["variable"],
                                               self.parameters["expression"])
        return success


class TestVariableCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(TestVariableCommand, self).__init__(parameters)
        self.interpreter = interpreter

    def run(self):
        interpreter   = self.interpreter

        variableValue, successVar = interpreter.getVariable(self.parameters['variable'])

        # If the variable doesn't exist, don't even bother evaluating the expression
        if not successVar: return False

        compareValue, successExp = interpreter.evaluateExpression(self.parameters['expression'])

        if not successExp: return False

        operations = ['==', '!=', '>', '<']

        expressionString = str(variableValue) + operations[self.parameters['test']] + self.parameters["expression"]
        testResult, success = interpreter.evaluateExpression(expressionString)

        # print("Expression tested: ", expressionString, " output", testResult and success)
        return testResult and success


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

        printf("WaitCommand.run(): Waiting for", waitTime, "seconds")

        # Split the wait into incriments of 0.1 seconds each, and check if the thread has been stopped at each incriment
        if success:
            sleep(waitTime)
        else:
            printf("WaitCommand.run(): ERROR: Expression failed to evaluate correctly!")


class GripCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(GripCommand, self).__init__(parameters)

        self.robot = self.getVerifyRobot(env)

    def run(self):
        self.robot.setGripper(True)


class DropCommand(Command):

    def __init__(self, env, interpreter, parameters=None):
        super(DropCommand, self).__init__(parameters)

        self.robot = self.getVerifyRobot(env)

    def run(self):
        self.robot.setGripper(False)
