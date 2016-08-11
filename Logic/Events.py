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
from Logic             import Global
from Logic.LogicObject import LogicObject
__author__ = "Alexander Thiel"


"""
Example Event

-----------------------------------------------TEMPLATE-----------------------------------------------------------------
class NameEvent(Event):

    def __init__(self, env, interpreter, parameters):
        super(NameEvent, self).__init__(parameters)

        # Get what is needed from the environment by requesting it through self.getVerifyXXXX(env)
        self.vision = self.getVerifyVision(env)
        self.calib  = env.getSettings()["motionCalibrations"]


    def isActive(self):
        # Make sure the event won't crash if there were errors

        if len(self.errors): return False  # If it did not compile without errors, don't run
------------------------------------------------------------------------------------------------------------------------
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
        self.high = self.stationary + diff * 4

    def isActive(self):
        if len(self.errors): return False  # If it did not compile without errors, don't run

        currentMotion = self.vision.getMotion()

        active = True

        if self.parameters["low"] == "Low":
            active = active and self.low < currentMotion

        if self.parameters["low"] == "High":
            active = active and self.high < currentMotion

        if self.parameters["high"] == "Low":
            active = active and currentMotion < self.low

        if self.parameters["high"] == "High":
            active = active and currentMotion < self.high

        return active  #self.parameters["lowThreshold"] < motion < self.parameters["upperThreshold"]


class RecognizeObjectEvent(Event):

    def __init__(self, env, interpreter, parameters):
        super(RecognizeObjectEvent, self).__init__(parameters)

        # Get what is needed from the environment by requesting it through self.getVerifyXXXX(env)
        self.vision     = self.getVerifyVision(env)
        self.object     = self.getVerifyObject(env, self.parameters["objectID"])


        # Make sure initialization can continue
        if len(self.errors): return

        # Turn on tracking and add the target. DO NOT TURN ON FILTERS, that's only for GUI to do, which it will.
        self.vision.addTarget(self.object)

    def isActive(self):
        # Make sure the event won't crash if there were errors
        if len(self.errors): return False  # If it did not compile without errors, don't run


        tracked = self.vision.searchTrackedHistory(trackable=self.object, maxAge=0)

        ret = tracked is not None

        # If object was "not" seen
        if self.parameters["not"]:
            ret = not ret

        return ret


class RecognizeCascadeEvent(Event):
    """
    For tracking cascades like "Face" or "Smile" using visions CascadeTracker features
    """

    def __init__(self, env, interpreter, parameters):
        super(RecognizeCascadeEvent, self).__init__(parameters)

        # Get what is needed from the environment by requesting it through self.getVerifyXXXX(env)
        self.vision     = self.getVerifyVision(env)

        # Make sure initialization can continue
        if len(self.errors): return

        # Turn on tracking and add the target. DO NOT TURN ON FILTERS, that's only for GUI to do, which it will.
        self.vision.addCascadeTarget(self.parameters["objectID"])

    def isActive(self):
        # Make sure the event won't crash if there were errors
        if len(self.errors): return False  # If it did not compile without errors, don't run

        frameAge, location  = self.vision.getCascadeLatestRecognition(self.parameters["objectID"])

        if not frameAge == 0: return False

        ret = location is not None

        # If target was "not" seen
        if self.parameters["not"]:
            ret = not ret

        return ret


class TipEvent(Event):
    """
    This event activates when the sensor on the tip of the robots sucker is pressed/triggered
    """

    def __init__(self, env, interpreter, parameters):
        super(TipEvent, self).__init__(parameters)

        self.robot = self.getVerifyRobot(env)

    def isActive(self):
        return self.robot.getTipSensor()



