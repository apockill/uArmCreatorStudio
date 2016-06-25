import  numpy as np
import  cv2
from    time import sleep
"""
A set of functions that use Robot and Vision classes to perform a task, all in tandem.

This combines with things like calibrations as well.
"""


# Minimum amount of tracking points to decide to attempt to pick up an object
MIN_MATCH_POINTS_FOR_PICKUP = 50
PICKUP_HEIGHT = 25  # For pickup operations, what should the Z be

def createCameraToRobotTransformFunc(fromPts, toPts):
    # Returns a function that takes a point (x,y,z) of a camera coordinate, and returns the robot (x,y,z) for that point

    # Generate the transformation matrix
    ret, M, mask = cv2.estimateAffine3D(np.float32(fromPts),
                                        np.float32(toPts),
                                        confidence = .999999)

    # Returns a numpy array of [x, y, z]
    transform = lambda x: np.array((M * np.vstack((np.matrix(x).reshape(3, 1), 1)))[0:3, :].reshape(1,3))[0]

    return transform

def getRobotPositionTransform(camPos, coordCalib):
    transform = createCameraToRobotTransformFunc(coordCalib["camPts"], coordCalib["robPts"])

    return transform(camPos)


def searchForNearestRobPt(objPt, coordCalib):
    camPts = coordCalib["camPts"]

    closestDist  = -1
    closestIndex = -1

    for i, camPt in enumerate(camPts):
        dist = ((objPt[0] - camPt[0])**2 +
                (objPt[1] - camPt[1])**2 +
                (objPt[2] - camPt[2])**2)**.5

        if dist < closestDist or closestIndex == -1:
            closestDist  = dist
            closestIndex = i
    print("Actual cam location at that point", camPts[closestIndex])
    return coordCalib["robPts"][closestIndex]

def mountObjectLearn(objectID, robot, vision, coordCalib):
    sleep(1)
    target, _ = vision.getAverageObjectPosition(objectID, 5)
    if target is None: return False

    transform = createCameraToRobotTransformFunc(coordCalib["camPts"], coordCalib["robPts"])
    robEstPos = transform(target)

    robot.setPos(x=robEstPos[0], y=robEstPos[1], z=robEstPos[2])
    robot.refresh()

    return True








