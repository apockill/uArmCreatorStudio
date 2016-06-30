from Logic             import Global
from Logic.Global      import printf
from Logic.LogicObject import LogicObject

"""
Example Event

class NameEvent(Event):

    def __init__(self, env, interpreter, parameters):
        super(NameEvent, self).__init__(parameters)

        # Get what is needed from the environment by requesting it through self.getVerifyXXXX(env)
        self.vision = self.getVerifyVision(env)
        self.calib  = env.getSettings()["motionCalibrations"]


    def isActive(self):
        # Make sure the event won't crash if there were errors

        if len(self.errors): return False  # If it did not compile without errors, don't run

"""


class Event(LogicObject):
    def __init__(self, parameters):
        super(Event, self).__init__()

        self.parameters  = parameters
        self.commandList = []

    def addCommand(self, command):
        self.commandList.append(command)

    def isActive(self):
        pass


class InitEvent(Event):
    def __init__(self, env, interpreter, parameters):
        super(InitEvent, self).__init__(parameters)
        self.hasBeenRun = False

    def isActive(self):
        # Returns true or false if this event should be activated

        if self.hasBeenRun:
            return False
        else:
            self.hasBeenRun = True
            return True


class DestroyEvent(Event):
    def __init__(self, env, interpreter, parameters):
        super(DestroyEvent, self).__init__(parameters)

    def isActive(self):
        # This event always returns false, because it is run DIRECTLY by the ControlPanel.programThread()
        # programThread() will check if the event exists. If it does, it will run all of its commands.
        # Otherwise, this event will never run while the program is running.
        return False


class StepEvent(Event):
    def __init__(self, env, interpreter, parameters):
        super(StepEvent, self).__init__(parameters)

    def isActive(self):
        # Since this is a "step" event, it will run each time the events are checked
        return True


class KeypressEvent(Event):

    def __init__(self, env, interpreter, parameters):
        super(KeypressEvent, self).__init__(parameters)


        # Constants for movement. These are set the first time isActive() is run
        self.low  = None
        self.med  = None
        self.high = None

    def isActive(self):
        if ord(self.parameters["checkKey"]) in Global.keysPressed:
            return True
        else:
            return False


class MotionEvent(Event):
    """
    This event activates when the sensor on the tip of the robots sucker is pressed/triggered
    """

    def __init__(self, env, interpreter, parameters):
        super(MotionEvent, self).__init__(parameters)

        self.vision = self.getVerifyVision(env)
        self.calib  = self.getVerifyMotionCalibrations(env)


        # If the necessary calibrations don't exist, leave now. The isActive has a check to not run.
        if self.calib["activeMovement"] is None or self.calib["stationaryMovement"] is None:
            return


        self.stationary = self.calib["stationaryMovement"]
        self.active     = self.calib["activeMovement"]

        # Scale the movement thresholds and set a low, medium, and high threshold
        diff      = (self.active - self.stationary)
        self.low  = self.stationary + diff
        self.med  = self.stationary + diff * 3
        self.high = self.stationary + diff * 6

    def isActive(self):
        if len(self.errors): return False  # If it did not compile without errors, don't run

        currentMotion = self.vision.getMotion()

        active = True

        if self.parameters["low"] == "Low":
            active = active and self.low < currentMotion
        if self.parameters["low"] == "Med":
            active = active and self.med < currentMotion
        if self.parameters["low"] == "High":
            active = active and self.high < currentMotion

        if self.parameters["high"] == "Low":
            active = active and currentMotion < self.low
        if self.parameters["high"] == "Med":
            active = active and currentMotion < self.med
        if self.parameters["high"] == "High":
            active = active and currentMotion < self.high

        return active  #self.parameters["lowThreshold"] < motion < self.parameters["upperThreshold"]


class RecognizeEvent(Event):

    def __init__(self, env, interpreter, parameters):
        super(RecognizeEvent, self).__init__(parameters)

        # Get what is needed from the environment by requesting it through self.getVerifyXXXX(env)
        self.vision     = self.getVerifyVision(env)
        self.object     = self.getVerifyObject(env, self.parameters["objectID"])


        # Make sure initialization can continue
        if len(self.errors): return

        # Turn on tracking and add the target. DO NOT TURN ON FILTERS, that's only for GUI to do, which it will.
        self.vision.addTargetSamples(self.object)
        self.vision.startTracker()

    def isActive(self):
        # Make sure the event won't crash if there were errors
        if len(self.errors): return False  # If it did not compile without errors, don't run

        recognized = self.vision.isRecognized(self.object)

        return recognized


class TipEvent(Event):
    """
    This event activates when the sensor on the tip of the robots sucker is pressed/triggered
    """

    def __init__(self, env, interpreter, parameters):
        super(TipEvent, self).__init__(parameters)

        self.robot = self.getVerifyRobot(env)

    def isActive(self):
        return self.robot.getTipSensor()



