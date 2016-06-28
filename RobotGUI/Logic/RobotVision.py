import numpy as np
import cv2
import math
from time                  import sleep
from RobotGUI.Logic.Global import printf


"""
A set of functions that use Robot and Vision classes to perform a task, all in tandem.

This combines with things like calibrations as well.
"""


# Minimum amount of tracking points to decide to attempt to pick up an object
MIN_POINTS_TO_LEARN_OBJECT = 150  # Minimum number of points to decide an object is valid for creating
MAX_FRAME_AGE_MOVE         = 5    # Maximum age of a tracked object to move the robot towards it
MIN_POINTS_PICKUP          = 45   # Minimum tracking points to perform a pickup operation on an object
MIN_POINTS_FOCUS           = 15   # Minimum tracking points to just move the robot over an object
TRACK_FAIL_MAX             = 30   # Maximum times a function will fail to find an object before quitting
MAX_PICKUP_DIST_THRESHOLD  = 15   # Maximum "camera distance" from an object to allow the pickup to continue

def createCameraToRobotTransformFunc(ptPairs, direction):
    # Returns a function that takes a point (x,y,z) of a camera coordinate, and returns the robot (x,y,z) for that point
    # Direction is either 1 or -1. If -1, then it will go backwards on the ptPairs, create a Robot-->Camera transform
    ptPairArray = np.asarray(ptPairs)
    if direction == 1:
        pts1 = ptPairArray[:, 0]
        pts2 = ptPairArray[:, 1]
    elif direction == -1:
        pts1 = ptPairArray[:, 1]
        pts2 = ptPairArray[:, 0]

    # Generate the transformation matrix
    ret, M, mask = cv2.estimateAffine3D(np.float32(pts1),
                                        np.float32(pts2),
                                        confidence = .999999)

    # Returns a numpy array of [x, y, z]
    transform = lambda x: np.array((M * np.vstack((np.matrix(x).reshape(3, 1), 1)))[0:3, :].reshape(1,3))[0]

    return transform


def dist(p1, p2):
    return ((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2 + (p2[2] - p1[2])**2)**.5

def getPositionTransform(posToTransform, ptPairs, direction):
    transform = createCameraToRobotTransformFunc(ptPairs, direction)
    return transform(posToTransform)

def getPositionCorrection(destPos, actualPos):
    # Returns the destination position offset by the difference between actualPos and destPos
    offset = np.asarray(destPos) - np.asarray(actualPos)
    newPos =  np.asarray(destPos) + offset
    return newPos.tolist()


def findCentroid(points):
    # For any array of format [[x, y], [x, y], [x,y], ... [x, y]]
    totalSum = [0, 0]
    samples  = 0

    for pt in points:
        totalSum[0] += pt[0]
        totalSum[1] += pt[1]
        samples += 1
    centroid = (totalSum[0] / samples, totalSum[1] / samples)
    return centroid

def translatePoints(points, translation):
    # oldCenter      = getCentroid(points)
    # trans       = [newCenter[0] - oldCenter[0], newCenter[1] - oldCenter[1]]

    newPoints = []
    for pt in points:
        newPoints.append((pt[0] + translation[0], pt[1] + translation[1]))
    return newPoints

def rotatePoints(points, theta):
    """Rotates the given polygon which consists of corners represented as (x,y),
    around the ORIGIN, clock-wise, theta degrees"""

    def rotatePoint(centerPoint, point, angle):
        """Rotates a point around another centerPoint. Angle is in degrees.
        Rotation is counter-clockwise"""
        temp_point = point[0]-centerPoint[0], point[1] - centerPoint[1]
        temp_point = (temp_point[0] * math.cos(angle) - temp_point[1] * math.sin(angle),
                      temp_point[0] * math.sin(angle) + temp_point[1] * math.cos(angle))

        temp_point = temp_point[0] + centerPoint[0], temp_point[1] + centerPoint[1]
        return temp_point

    center = findCentroid(points)

    newPoints = []
    for pt in points:
        newPoints.append(rotatePoint(center, pt, theta))

    return newPoints


# Long form functions with lots of steps
def pickupObject(targetObj, rbMarker, robot, vision, ptPairs):

    # Get a super recent frame of the object
    frameAge, trackedObj = vision.getObjectLatestRecognition(targetObj)

    # If the frame is too old or doesn't exist or doesn't have enough points, exit the function
    if trackedObj is None or frameAge > MAX_FRAME_AGE_MOVE or trackedObj.ptCount < MIN_POINTS_PICKUP:
        printf("PickupObjectCommand.run(): Couldn't get the object!")
        return False

    pickupRect = trackedObj.target.pickupRect[:2], trackedObj.target.pickupRect[2:]
    print("pickupRect: ", pickupRect)

    rect = trackedObj.target.rect
    w    = rect[2] - rect[0]
    h    = rect[3] - rect[1]
    c    = trackedObj.center
    translation  = [c[0] - 1 / 2 * w, c[1] - 1 / 2 * h]
    pickupRect   = translatePoints(pickupRect, translation)
    pickupRect   = rotatePoints(pickupRect, trackedObj.rotation[2])
    targetCamPos = findCentroid(pickupRect)
    targetCamPos = [targetCamPos[0], targetCamPos[1], trackedObj.center[2]]
    print("old center", trackedObj.center)

    print("new Center", targetCamPos)



    # Move to the objects position
    pos = getPositionTransform(targetCamPos, ptPairs, direction=1)
    robot.setPos(x=pos[0], y=pos[1], z=pos[2])
    robot.refresh()
    robot.wait()


    # Do the final focusing in on the object
    moveAttemptCount = 0  # How many "readjustments" the robot has performed.
    trackFailCount   = 0  # If the robot marker cannot be seen for a certain amount of time, then exit the function



    while True:
        # Get a super recent frame of the object
        frameAge, trackRob = vision.getObjectLatestRecognition(rbMarker)


        # If the frame is too old or marker doesn't exist or doesn't have enough points, exit the function
        if trackRob is None or frameAge > MAX_FRAME_AGE_MOVE or trackRob.ptCount < MIN_POINTS_PICKUP:
            if trackRob is not None: print("points: ", trackRob.ptCount)
            printf("RobotVision.moveToCamPosition.run(): Couldn't get the robot marker! ")
            trackFailCount += 1
            if trackFailCount > TRACK_FAIL_MAX:
                return False

            vision.waitForNewFrames(numFrames=MAX_FRAME_AGE_MOVE)
            continue

        robPos = trackRob.center

        distance = ((targetCamPos[0] - robPos[0])**2 + (targetCamPos[1] - robPos[1])**2) ** .5
        print("DISTANCE!", distance)
        if distance <= MAX_PICKUP_DIST_THRESHOLD:
            print("SUCCEEDED!", distance)
            return True



        trackFailCount = 0

        camPos = getPositionCorrection(targetCamPos, robPos)
        pos    = getPositionTransform(camPos, ptPairs, 1)

        robot.setPos(z=3, relative=True)
        robot.refresh()
        robot.wait()

        robot.setPos(x=pos[0], y=pos[1])  # z=pos[2])
        robot.refresh()
        robot.wait()

        robot.setPos(z=pos[2])
        robot.refresh()
        robot.wait()

        moveAttemptCount += 1
        sleep(1)





# NOT USED (YET)
# def searchForNearestRobPt(objPt, coordCalib):
#     return # So I don't accidentally use it...
#     camPts = coordCalib["camPts"]
#
#     closestDist  = -1
#     closestIndex = -1
#
#     for i, camPt in enumerate(camPts):
#         dist = ((objPt[0] - camPt[0])**2 +
#                 (objPt[1] - camPt[1])**2 +
#                 (objPt[2] - camPt[2])**2)**.5
#
#         if dist < closestDist or closestIndex == -1:
#             closestDist  = dist
#             closestIndex = i
#     print("Actual cam location at that point", camPts[closestIndex])
#     return coordCalib["robPts"][closestIndex]

# def sortPointsByDistance(camPos, ptPairs):
#     # Sorts the camPts and robPts simultaneously by the distance from camPos
#     sortedPairs = sorted(ptPairs, key=lambda pointPair: dist(camPos, pointPair[0]))
#     return sortedPairs