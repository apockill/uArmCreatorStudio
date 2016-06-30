

"""
    This is a superclass for Command and Event, and thus every command and event out there.
    It contains functions that pertain to both, mainly related to pulling something from the environment
    and returning errors if that thing was not valid, thus appending an "error" to self.errors
"""

class LogicObject:
    def __init__(self):
        self.errors = []

    def getVerifyRobot(self, env):
        robot = env.getRobot()
        if not robot.connected():
            self.errors.append("Robot is not connected")
        return env.getRobot()

    def getVerifyVision(self, env):
        vStream = env.getVStream()
        if not vStream.connected():
            self.errors.append("Camera is not connected")
        return env.getVision()

    def getVerifyMotionCalibrations(self, env):
        calib  = env.getSettings()["motionCalibrations"]


        # DO ERROR CHECKING
        # If the appropriate motionCalibrations do not exist, add it to the "compile" errors, and set self.calib to None
        if calib["activeMovement"] is None or calib["stationaryMovement"] is None:
            self.errors.append("Motion Detection Calibration has never been run")
        return calib

    def getVerifyCoordCalibrations(self, env):
        calib  = env.getSettings()["coordCalibrations"]

        # DO ERROR CHECKING
        # If the appropriate motionCalibrations do not exist, add it to the "compile" errors, and set self.calib to None
        if calib["ptPairs"] is None or calib["failPts"] is None:
            self.errors.append("Camera/Robot Position Calibration has never been run")

        return calib

    def getVerifyObject(self, env, objectID):
        objectManager = env.getObjectManager()
        requestedObj  = objectManager.getObject(objectID)

        if requestedObj is None:
            self.errors.append("Object '" + str(objectID) + "' not found")

        return requestedObj







