from time                       import sleep  # For WaitCommand
from RobotGUI.Logic.Global      import printf
from RobotGUI.Logic             import RobotVision as rv
from RobotGUI.Logic.LogicObject import LogicObject


"""
Example Class Structure


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
        if len(self.errors) > 0: return
        # printf("NameCommand.run(): A quick description, usually using parameters, of the command that is running")
        self.robot.wait()

        coordSave = self.robot.getCurrentCoord()
        self.robot.setPos(z=2, relative=True)
        def swipe(lower, upper, axis):
            self.robot.setSpeed(30)

            self.robot.setPos(**{axis:lower})
            self.robot.refresh()
            sleep(1)
            self.robot.setPos(**{axis:upper})
            self.robot.setSpeed(10)
            self.robot.refresh()
            while self.robot.getMoving():

                robPos   = self.robot.getCurrentCoord()
                age, obj = self.vision.getObjectLatestRecognition(self.rbMarker.name)
                if not age == 0: continue
                print("Appending", robPos, obj.center)
                self.coordCalib["robotPoints"].append(robPos)
                self.coordCalib["cameraPoints"].append(obj.center)

                print("Length", len(self.coordCalib["cameraPoints"]), len(self.coordCalib["robotPoints"]))
                self.vStream.waitForNewFrame()
        swipe(-15, 15, "x")
        self.robot.setPos(x=coordSave[0])
        swipe(-8, -25, "y")
        self.robot.setPos(y=coordSave[1])
        swipe(8, 25, "z")
        self.robot.setPos(z=coordSave[2])
        self.robot.setSpeed(35)
        self.robot.refresh()
        self.robot.wait()

        rv.mountObjectLearn(self.object.name, self.robot, self.vision, self.coordCalib)
        # self.robot.setSpeed(10)
        #
        #
        #
        # self.robot.setSpeed(10)
        # rv.mountObjectLearn(self.object.name, self.robot, self.vision, self.coordCalib)

        # pos = rv.getObjectPosition(self.object.name, self.robot, self.vision, self.coordCalib)
        #
        #
        # if pos is not None:
        #     self.robot.refresh()
        #     self.robot.setPos(x=pos[0], y=pos[1], z=pos[2])
        #     self.robot.refresh()
        #     self.robot.wait()
        #     sleep(2)
        #
        #     pos, rotation = self.vision.getAverageObjectPosition(self.rbMarker.name, 29)
        #     print("Went to: ", pos)
        #     if pos is not None:
        #         self.coordCalib["cameraPoints"].append(pos)
        #         self.coordCalib["robotPoints"].append(self.robot.getCurrentCoord())

            # print("Moved to\t ", self.robot.getCurrentCoord())




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

