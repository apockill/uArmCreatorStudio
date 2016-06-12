from RobotGUI.Logic        import Global
from RobotGUI.Logic.Global import printf

class Event:
    def __init__(self, parameters):
        self.parameters  = parameters
        self.commandList = []
        self.errors      = []

    def addCommand(self, command):
        self.commandList.append(command)

    def getVerifyVision(self, env):
        return env.getVision()

    def getVerifyRobot(self, env):
        return env.getRobot()

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
        self.calib  = env.getSettings()["motionCalibrations"]


        # DO ERROR CHECKING
        # If the appropriate motionCalibrations do not exist, add it to the "compile" errors, and set self.calib to None
        if self.calib is None or not ("stationaryMovement" and "activeMovement") in self.calib:
            self.errors.append("Motion Calibrations not found in settings")
        else:
            self.stationary = self.calib["stationaryMovement"]
            self.active     = self.calib["activeMovement"]


        # PREPARE CONSTANTS
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


class TipEvent(Event):
    """
    This event activates when the sensor on the tip of the robots sucker is pressed/triggered
    """

    def __init__(self, env, interpreter, parameters):
        super(TipEvent, self).__init__(parameters)

        self.robot = self.getVerifyRobot(env)

    def isActive(self):
        return self.robot.getTipSensor()



