from RobotGUI.Logic.Global import printf


class Command:
    def __init__(self):
        pass

    def run(self):
        pass


class MoveXYZCommand(Command):

    def __init__(self, parameters=None):
        super(MoveXYZCommand, self).__init__()

        # Get the parameters for this command
        self.parameters = parameters

    def run(self, shared):
        printf("MoveXYZCommand.run(): Moving robot to ",
               self.parameters['x'], " ",
               self.parameters['y'], " ",
               self.parameters['z'], " ")

        shared.getRobot().setPos(x=self.parameters['x'],
                                 y=self.parameters['y'],
                                 z=self.parameters['z'],
                                 relative=self.parameters['rel'])


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
