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
import json
__author__ = "Alexander Thiel"



class LogicObject:
    """
        This is a superclass for Command and Event, and thus every command and event out there.
        It contains functions that pertain to both, mainly related to pulling something from the environment
        and returning errors if that thing was not valid, thus appending an "error" to self.errors
    """
    def __init__(self):
        self.errors = []

    def getVerifyJson(self, env, filename):

        if len(filename) == 0:
            self.errors.append("No File Specified")
            return None

        try:
            loadData = json.load( open(filename))
            return loadData
        except IOError as e:
            self.errors.append("Task File Could Not Be Found")
            return None

    def getVerifyRobot(self, env):
        robot = env.getRobot()
        if not robot.connected():
            self.errors.append("Robot is not connected")
        return env.getRobot()

    def getVerifyVStream(self, env):
        vStream = env.getVStream()
        if not vStream.connected():
            self.errors.append("Camera is not connected")

        return vStream

    def getVerifyVision(self, env):
        # Make sure the camera is connected
        self.getVerifyVStream(env)

        return env.getVision()

    def getVerifyMotionCalibrations(self, env):
        calib  = env.getSetting("motionCalibrations")


        # DO ERROR CHECKING
        # If the appropriate motionCalibrations do not exist, add it to the "compile" errors, and set self.calib to None
        if calib["activeMovement"] is None or calib["stationaryMovement"] is None:
            self.errors.append("Motion Detection Calibration has never been run")
        return calib

    def getVerifyObject(self, env, objectID):
        objectManager = env.getObjectManager()
        requestedObj  = objectManager.getObject(objectID)

        if objectID == "":
            self.errors.append("No Object Selected")
        elif requestedObj is None:
            self.errors.append("Resource not found: '" + str(objectID) + "'")

        return requestedObj

    def getVerifyTransform(self, env):
        transform = env.getTransform()
        if transform is None:
            self.errors.append("Camera/Robot Position Calibration has never been run")

        return transform





