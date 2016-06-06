from RobotGUI.Logic.Global import printf
from time import sleep  # For WaitCommand

"""
class NameCommand(Command):

    def __init__(self, parameters=None):
        super(NameCommand, self).__init__()
        self.parameters = parameters

    def run(self, env):
        pass

"""



class Command:
    def __init__(self):
        pass

    def run(self, environment):
        pass


class MoveXYZCommand(Command):

    def __init__(self, parameters=None):
        super(MoveXYZCommand, self).__init__()

        # Get the parameters for this command
        self.parameters = parameters

    def run(self, env):
        printf("MoveXYZCommand.run(): Moving robot to ",
               self.parameters['x'], " ",
               self.parameters['y'], " ",
               self.parameters['z'], " ")

        interpreter = env.getInterpreter()

        newX, successX = interpreter.evaluateExpression(self.parameters['x'])
        newY, successY = interpreter.evaluateExpression(self.parameters['y'])
        newZ, successZ = interpreter.evaluateExpression(self.parameters['z'])

        if successX and successY and successZ:
            env.getRobot().setPos(x=newX, y=newY, z=newZ,
                                  relative=self.parameters['relative'])
        else:
            print("ERROR in parsing either X Y or Z: ", successX, successY, successZ)

        env.getRobot().refresh(override=self.parameters['override'])


class MoveWristCommand(Command):

    def __init__(self, parameters=None):
        super(MoveWristCommand, self).__init__()
        self.parameters = parameters

    def run(self, env):
        interpreter = env.getInterpreter()
        robot       = env.getRobot()

        newAngle, success = interpreter.evaluateExpression(self.parameters['angle'])

        if success:
            robot.setWrist(newAngle)
            robot.refresh()
        else:
            print("MoveWristCommand.run(): ERROR in parsing new wrist angle. Expression: ", self.parameters['angle'])


class StartBlockCommand(Command):
    """
    Mark the start a block of code with this command
    """

    def __init__(self, parameters=None):
        super(StartBlockCommand, self).__init__()


class EndBlockCommand(Command):
    """
    Mark the end a block of code with this command
    """

    def __init__(self, parameters=None):
        super(EndBlockCommand, self).__init__()


class SetVariableCommand(Command):

    def __init__(self, parameters=None):
        super(SetVariableCommand, self).__init__()
        self.parameters = parameters

    def run(self, env):

        interpreter = env.getInterpreter()
        success = interpreter.setVariable(self.parameters["variable"], self.parameters["expression"])

        return success


class TestVariableCommand(Command):

    def __init__(self, parameters=None):
        super(TestVariableCommand, self).__init__()
        self.parameters = parameters

    def run(self, env):
        interpreter   = env.getInterpreter()

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

    def __init__(self, parameters=None):
        super(DetachCommand, self).__init__()
        self.parameters = parameters

    def run(self, env):
        printf("DetachCommand.run(): Detaching servos ",
               self.parameters['servo1'],
               self.parameters['servo2'],
               self.parameters['servo3'],
               self.parameters['servo4'])

        robot = env.getRobot()

        if self.parameters['servo1']: robot.setServos(servo1=False)
        if self.parameters['servo2']: robot.setServos(servo2=False)
        if self.parameters['servo3']: robot.setServos(servo3=False)
        if self.parameters['servo4']: robot.setServos(servo4=False)

        robot.refresh()


class AttachCommand(Command):

    def __init__(self, parameters=None):
        super(AttachCommand, self).__init__()
        self.parameters = parameters


    def run(self, env):
        printf("AttachCommand.run(): Attaching servos ", self.parameters['servo1'],
                                                         self.parameters['servo2'],
                                                         self.parameters['servo3'],
                                                         self.parameters['servo4'])

        robot = env.getRobot()

        if self.parameters['servo1']: robot.setServos(servo1=True)
        if self.parameters['servo2']: robot.setServos(servo2=True)
        if self.parameters['servo3']: robot.setServos(servo3=True)
        if self.parameters['servo4']: robot.setServos(servo4=True)

        robot.refresh()


class WaitCommand(Command):

    def __init__(self, parameters=None):
        super(WaitCommand, self).__init__()
        self.parameters = parameters

    def run(self, env):

        interpreter       = env.getInterpreter()
        waitTime, success = interpreter.evaluateExpression(self.parameters['time'])

        printf("WaitCommand.run(): Waiting for", waitTime, "seconds")

        # Split the wait into incriments of 0.1 seconds each, and check if the thread has been stopped at each incriment
        if success:
            sleep(waitTime)
        else:
            printf("WaitCommand.run(): ERROR: Expression failed to evaluate correctly!")


class GripCommand(Command):

    def __init__(self, parameters=None):
        super(GripCommand, self).__init__()

    def run(self, env):
        robot = env.getRobot()
        robot.setGripper(True)


class DropCommand(Command):

    def __init__(self, parameters=None):
        super(DropCommand, self).__init__()

    def run(self, env):
        robot = env.getRobot()
        robot.setGripper(False)
