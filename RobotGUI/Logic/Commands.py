from RobotGUI.Logic.Global import printf


"""
class NameCommand(Command):

    def __init__(self, parameters=None):
        super(NameCommand, self).__init__()
        self.parameters = parameters

    def run(self, env):
        # If the function ran incorrectly
        return False
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

        if newX and newY and newZ:
            env.getRobot().setPos(x=newX, y=newY, z=newZ, relative=self.parameters['override'])
        else:
            print("ERROR LOL")

        env.getRobot().refresh()


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

        operations = ['==', '>', '<']

        expressionString = str(variableValue) + operations[self.parameters['test']] + self.parameters["expression"]
        testResult, success = interpreter.evaluateExpression(expressionString)

        print("Expression tested: ", expressionString, " output", testResult and success)
        return testResult and success

