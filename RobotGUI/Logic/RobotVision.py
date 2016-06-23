import  numpy as np
import  cv2
from    time import sleep
"""
A set of functions that use Robot and Vision classes to perform a task, all in tandem.

This combines with things like calibrations as well.
"""


def createCameraToRobotTransformFunc(coordCalib):
    # Returns a function that takes a point (x,y,z) of a camera coordinate, and returns the robot (x,y,z) for that point

    # Generate the transformation matrix
    ret, M, mask = cv2.estimateAffine3D(np.float32(coordCalib["cameraPoints"]),
                                        np.float32(coordCalib["robotPoints"]),
                                        confidence = .999999)
    # print(coordCalibrations)
    print("success transform?", ret)
    # # Format it so there's a [0, 0, 0, 1] on the bottom row
    # M = np.float32([M[0], M[1], M[2], [0 ,0, 0, 1]])
    # print("1st", ret, M)
    #
    #
    # ret, M, mask = cv2.estimateAffine3D(np.float32(coordCalibrations["cameraPoints"][:50]),
    #                                     np.float32(coordCalibrations["robotPoints"][:50]))
    # print("2nd", ret, M)

    # Create a function that takes (x,y,z) camera coordinates and returns (x, y, z) robot coordintes

    # Returns a numpy array of [x, y, z]
    transform = lambda x: np.array((M * np.vstack((np.matrix(x).reshape(3, 1), 1)))[0:3, :].reshape(1,3))[0]

    return transform

def getObjectPosition(objectID, robot, vision, coordCalibrations):
    transform = createCameraToRobotTransformFunc(coordCalibrations)

    pos, rotation = vision.getAverageObjectPosition(objectID, 29)


    if pos is not None:
        pos = (pos[0], pos[1], pos[2])
        print("Going to: ", pos)
        moveTo = transform(tuple(pos))
        return moveTo

    return None


def mountObjectLearn(objectID, robot, vision, coordCalib):
    sleep(1)
    target, _ = vision.getAverageObjectPosition(objectID, 5)
    if target is None: return False

    transform = createCameraToRobotTransformFunc(coordCalib)
    robEstPos = transform(target)

    robot.setPos(x=robEstPos[0], y=robEstPos[1], z=robEstPos[2])
    robot.refresh()

    return True








