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
import math
import cv2
import numpy as np
from time         import time, sleep
from Logic.Global import printf, waitUntilTime
__author__ = "Alexander Thiel"


"""
This module is basically a set of functions that use Robot and Vision classes to perform a task, all in tandem.
It combines with things like calibrations as well. It was created because I didn't want to put too much non-specific
logic code in Commands.py, because a lot of these functions could be reused. So in this module there are functions
that can work as long as you have all the necessary arguments. It might seem a bit verbose, but it's a worthy
tradeoff to allow anyone to use a pickupObject function, for example.
"""


# Minimum amount of tracking points to decide to attempt to pick up an object
MIN_POINTS_TO_LEARN_OBJECT = 150  # Minimum number of points to decide an object is valid for creating
MAX_FRAME_AGE_MOVE         = 5    # Maximum age of a tracked object to move the robot towards it
MIN_POINTS_PICKUP_OBJECT   = 50   # Minimum points on an object for the robot to see an object and pick it up
MIN_POINTS_FOCUS           = 25   # Minimum tracking points to just move the robot over an object
MAX_FRAME_FAIL             = 15   # Maximum times a function will get a new frame to recognize an object before quitting


# General Use Functions (May or may not use vision or robot)



def playMotionPath(motionPath, robot, exitFunc, speedMultiplier=1, reverse=False):
    """
    Play a motion recording.
    :param motionPath: The motionpath array, with format [[TIME, GRIPPER, SERVO0, SERVO1, SERVO2, SERVO3]... []]
    :param robot: Robot object
    :param speedMultiplier: a number > 0 that will change the speed the path is played at
    :param reverse: whether or not to play the motionPath in reverse
    :param exitFunc: If this function ever returns true, the function will exit as quickly as possible
    """

    # Modify the motionPath so that it fits the Speed and Reversed parameters
    # Since x2 should mean twice as fast, and .5 should mean twice as slow, inverse the speed
    speedMultiplier = 1.0 / speedMultiplier


    # Multiply the motionPath by newSpeed, to change how fast it replays
    mp         = np.asarray(motionPath[:])
    timeColumn = mp[:, [0]] * speedMultiplier
    actions    = mp[:, 1:]

    # If reversed, flip the "actions" array
    if reverse:
        actions = actions.tolist()
        actions = np.flipud(actions)  # Reverse the actions


    # Put the "time" and "actions" array back together and return it to a list
    motionPath = np.hstack((timeColumn, actions))
    motionPath = motionPath.tolist()


    # Now that the modifications are done, start the process for begining the motionPath
    TIME    = 0
    GRIPPER = 1
    SERVO0  = 2
    SERVO1  = 3
    SERVO2  = 4
    SERVO3  = 5


    # Convenience function. Example:  setServo(0, 90) will set servo #0 to 90 degrees
    def setServo(servoNumber, angle):
        if servoNumber == 0: robot.setServoAngles(servo0 = angle)
        if servoNumber == 1: robot.setServoAngles(servo1 = angle)
        if servoNumber == 2: robot.setServoAngles(servo2 = angle)
        if servoNumber == 3: robot.setServoAngles(servo3 = angle)




    # Get the first move of the motionPath
    action = motionPath[0]


    # Get the start position and the current position. If the distance is too high, move there slowly
    startPos    = robot.getFK(action[SERVO0], action[SERVO1], action[SERVO2])
    currentPos  = robot.getCoords()
    if dist(startPos, currentPos) > 5:
        robot.setPos(coord=startPos)


    # Set the first position, to make sure the recording starts off on correct position
    lastVal = [action[SERVO0], action[SERVO1], action[SERVO2], action[SERVO3]]
    gripper = False
    setServo(0, lastVal[0])
    setServo(1, lastVal[1])
    setServo(2, lastVal[2])
    setServo(3, lastVal[3])


    # Start running through motionPath, starting on the 2nd step
    startTime = time() + action[TIME]


    for i, action in enumerate(motionPath[1:-1]):
        if exitFunc(): return
        actTime = action[TIME]

        now = time() - startTime

        lastTime  = motionPath[i][TIME]                 # Previous move time
        nextTime  = motionPath[i + 2][TIME]             # Next move time
        startMove = (actTime - lastTime) / 2 + lastTime     # When to start sending this move
        endMove   = (nextTime   - actTime)  / 2 + actTime  # When to no longer send this move
        tSpan     = endMove - startMove

        # If its too late to even start, skip it
        if now > nextTime: continue


        # If its absolutely not time to start moving yet, wait.
        if now < startMove:
            waitUntilTime(startMove + startTime, exitFunc)


        # Get a list of how far each servo is from its desired position, then sort it by furthest to closest
        diffS = [(abs(lastVal[0] - action[SERVO0]), 0),
                 (abs(lastVal[1] - action[SERVO1]), 1),
                 (abs(lastVal[2] - action[SERVO2]), 2),
                 (abs(lastVal[3] - action[SERVO3]), 3)]
        diffS = sorted(diffS, key=lambda d: d[0], reverse=True)


        # Update the gripper
        if not gripper == action[GRIPPER]:
            gripper = action[GRIPPER]
            robot.setGripper(gripper)


        # Update each servo, in order of most needy to least needy
        for difference, servo in diffS:

            # Adjust the servo position for a derived position between now and endTime
            servoIndex = 2 + servo
            now       = time() - startTime
            tIn       = now - startMove
            if tIn < 0: tIn = 0
            percentIn = tIn / tSpan

            pastPos   = motionPath[i][servoIndex]
            nextPos   = motionPath[i + 2][servoIndex]
            diff      = nextPos - pastPos
            modified  = diff * percentIn + pastPos
            modified  = round(modified, 1)

            # Make sure there's still time to send another servo command
            if now > endMove: break


            # Send the command as long as there's actually a difference in the old position and the new position
            if abs(modified - lastVal[servo]) > 0:
                setServo(servo, modified)
                lastVal[servo] = modified


# Transform math``
def createTransformFunc(ptPairs, direction):
    """
    Returns a function that takes a point (x,y,z) of a camera coordinate, and returns the robot (x,y,z) for that point
    Direction is either "toRob" or "toCam".
    If "toCam" it will return a Robot-->Camera transform
    If "toRob" it will return a Camera-->Robot transform
    """


    ptPairArray = np.asarray(ptPairs)
    if direction == "toRob":
        pts1 = ptPairArray[:, 0]
        pts2 = ptPairArray[:, 1]

    if direction == "toCam":
        pts1 = ptPairArray[:, 1]
        pts2 = ptPairArray[:, 0]


    # Generate the transformation matrix
    ret, M, mask = cv2.estimateAffine3D(np.float32(pts1),
                                        np.float32(pts2),
                                        confidence = .9999999)

    if not ret: printf("ERROR: Transform failed!")

    # Returns a function that will perform the transformation between pointset 1 and pointset 2 (if direction is == 1)

    transformFunc = lambda x: np.array((M * np.vstack((np.matrix(x).reshape(3, 1), 1)))[0:3, :].reshape(1, 3))[0]


    """
    Breakdown of function. Here's an example of transforming [95, -35, 530] cam which is [5, 15, 15] in the robot grid

    First:
    [95, -35, 530]

    np.vstack((np.matrix(input).reshape(3, 1), 1))  is applied, converts it to a vertical array
    [[ 95]
     [-35]
     [530]
     [  1]]

    M * np.vstack((np.matrix(x).reshape(3, 1), 1))  (transformation matrix multiplied by the previous number)
    [[  5.8371337 ]
     [ 15.72722685]
     [ 14.5007519 ]]

     There you go. The rest of it is simply converting that matrix into
     [5.83, 15.72, 14.5]

     but you know, without the rounding.

    """

    return transformFunc

def getPositionTransform(posToTransform, direction, ptPairs):
    transform = createTransformFunc(ptPairs, direction)
    return transform(posToTransform)








# Coordinate math
def dist(p1, p2):
    return ((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2 + (p2[2] - p1[2])**2)**.5

def unitVector(point):
    magnitude = sum(point**2)**.5
    unitVec   = np.array(point) / magnitude
    return unitVec

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
    # Translation -> [xTranslation, yTranslation]
    newPoints = []
    for pt in points:
        newPoints.append((pt[0] + translation[0], pt[1] + translation[1]))
    return newPoints

def rotatePoints(origin, points, theta):
    """Rotates the given polygon which consists of corners represented as (x,y),
    around the ORIGIN, clock-wise, theta degrees"""

    def rotatePoint(centerPoint, point, angle):
        """Rotates a point around another centerPoint. Angle is in degrees.
        Rotation is counter-clockwise"""
        temp_point = point[0] - centerPoint[0], point[1] - centerPoint[1]
        temp_point = (temp_point[0] * math.cos(angle) - temp_point[1] * math.sin(angle),
                      temp_point[0] * math.sin(angle) + temp_point[1] * math.cos(angle))

        temp_point = temp_point[0] + centerPoint[0], temp_point[1] + centerPoint[1]
        return temp_point

    # center = findCentroid(points)

    newPoints = []
    for pt in points:
        newPoints.append(rotatePoint(origin, pt, theta))

    return newPoints

def pointInPolygon(point, poly):
    # Determine if a point is inside a given polygon or not
    # Polygon is a list of (x,y) pairs.
    # Point is an (x,y) or (x,y,z) coordinate. Z is never considered.

    n = len(poly)
    inside = False
    x = point[0]
    y = point[1]

    p1x, p1y = poly[0]
    for i in range(n + 1):
        p2x, p2y = poly[i % n]

        if max(p1y, p2y) >= y > min(p1y, p2y):
            if x <= max(p1x, p2x):
                if p1y != p2y:
                    xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x

                if p1x == p2x or x <= xinters:
                    inside = not inside

        p1x, p1y = p2x, p2y

    return inside

def smoothListGaussian(list1, degree):
    """
    Smooth a list using guassian smoothing, with degree Degree. Lists are smoothed by columns, not rows.
    :param list1:  [[column1, column2, column3... column n], ... [element n]]
    :param degree: The gaussian smoothing constant.
    """

    window = degree * 2 - 1


    if len(list1) < window:
        printf("ERROR: Attempted to smooth list that was too small to be smoothed")
        return None


    weight = np.array([1.0] * window)
    # print(weight)

    weightGauss = []

    for i in range(window):

        i = i - degree + 1

        frac = i / float(window)

        gauss = 1 / (np.exp((4 * frac) ** 2))

        weightGauss.append(gauss)


    weight = np.array(weightGauss) * weight


    smoothed = [0.0] * (len(list1) - window)


    for i in range(len(smoothed)):
        smoothing = [0.0 for i in range(len(list1[i]))]  # [0.0, 0.0, 0.0]
        for e, w in zip(list1[i:i + window], weight):
            smoothing = smoothing + np.multiply(e, w)

        smoothed[i] = smoothing / sum(weight)

    return smoothed


# Long form functions with lots of steps
def pickupObject(trackable, rbMarker, ptPairs, groundHeight, robot, vision):
    """
    This will pick up an object, or detect that it failed and turn off the gripper

    :param trackable: Any ObjectManager.Trackable object
    :param rbMarker: A trackable object representing some kind of marker that is on top of the robots end effector
    :param ptPairs: The data inside of Environment.__settings["coordCalibrations"]["ptPairs"]
    :param groundHeight: The data inside of Environment.__settings["coordCalibrations"]["groundPos"]
    :param robot: The Robot.Robot object which controls the robot
    :param vision: The Vision.Vision object which handles computer vision operations
    :return: True or False, True if it successfuly picked up the object, otherwise False
    """
    def getRobotAccurate(trackable, vision, maxAttempts=10):
        # A little convenience function that is used several times in the pickup
        moveThresh  = 15
        lowest      = [None, None]  # [coordinates of object, the speed at which it was going at]
        for s in range(0, maxAttempts):
            vision.waitForNewFrames()
            # trackRob = vision.getObjectBruteAccurate(rbMarker, minPoints   = MIN_POINTS_PICKUP_MARKER,
            #                                                    maxFrameAge = 0,
            #                                                    maxAttempts = MAX_FRAME_FAIL)
            avgPos, avgMag, avgDir = vision.getObjectSpeedDirectionAvg(trackable)

            if avgPos is None: continue

            if avgMag < moveThresh:
                print("Got acceptable value, returning now")
                return avgPos

            if lowest[1] is None or avgMag < lowest[1]:
                lowest[0] = avgPos
                print("Saving lowest")
        print("Never found acceptable value, returning best of: ", lowest[0])
        return lowest[0]


    # If the object hasn't been seen recently, then don't even start the pickup procedure
    frameAge, _ = vision.getObjectLatestRecognition(trackable)
    if frameAge is None or frameAge > 30:
        printf("The object is not on screen. Aborting pickup.")
        return False


    # Get a super recent frame of the object with high point count and accuracy
    trackedObj = vision.getObjectBruteAccurate(trackable,
                                               minPoints   = MIN_POINTS_PICKUP_OBJECT,
                                               maxAge= 0,
                                               maxAttempts = MAX_FRAME_FAIL)

    if trackedObj is None:
        printf("Couldn't get the object accurately!")
        return False

    """
        The following code blob does the following:

        Get the position of the object in the robot coordinate array
        Add the height of the object to the z position of the object
        Check that the object is below ground level. if not, set the Z to be ground level
        Convert the changed position of the object back to the camera array
        Save the new Z position of the camera, to be used later
    """
    # center = trackedObj.center
    center    = trackedObj.center
    posRob    = getPositionTransform((center[0], center[1], center[2]), direction="toRob", ptPairs=ptPairs)
    posCam    = getPositionTransform(posRob, direction="toCam", ptPairs=ptPairs)
    staticErr = center - posCam
    posRob    = getPositionTransform((center[0], center[1], center[2]), direction="toRob", ptPairs=ptPairs)
    posRob[2] += trackedObj.view.height + 5
    if posRob[2] < groundHeight + 1:
        printf("Predicted position was below groundheight. Moving to groundheight instead.")
        posRob[2] = groundHeight + 1
    posCam    = getPositionTransform(posRob, direction="toCam", ptPairs=ptPairs)
    posCam   += staticErr
    objCamZ   = posCam[2]



    # Get the pickupRect, translate it, rotate it, and place it on the correct place
    x0, y0, x1, y1 = trackedObj.view.pickupRect
    pickupRect     = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
    rect = trackedObj.view.rect
    w, h = rect[2] - rect[0], rect[3] - rect[1]
    c    = trackedObj.center
    translation  = [c[0] - 1 / 2 * w, c[1] - 1 / 2 * h]
    pickupRect   = translatePoints(pickupRect, translation)
    pickupRect   = rotatePoints(trackedObj.center[:2], pickupRect, trackedObj.rotation[2])


    # Get the actual position that the robot will be aiming for during the entire function (the center of pickupRect)
    targetCamPos = findCentroid(pickupRect)
    targetCamPos = [targetCamPos[0], targetCamPos[1], objCamZ]
    print("Final center: ", targetCamPos)

    # Move to the objects position
    pos = getPositionTransform(targetCamPos, direction="toRob", ptPairs=ptPairs)


    robot.setPos(z=pos[2])
    robot.setPos(x=pos[0], y=pos[1])



    # # Try to "Jump" towards the object by measuring the desired pos and the offset
    # lastCoord = getRobotAccurate(rbMarker, vision)
    # if lastCoord is None:
    #     printf("Could not find robot before jump! Exiting pickup")
    #     return False
    #
    # camPos  = getPositionCorrection(targetCamPos, lastCoord)
    # jumpPos = getPositionTransform(camPos, ptPairs, 1)
    # if jumpPos[2] < groundHeight: jumpPos[2] = groundHeight
    #
    # print("Jumping robot: ", jumpPos)
    # if abs(jumpPos[1] - robot.coord[1]) < 7 and abs(jumpPos[0] - robot.coord[0]) < 7:
    #     robot.setPos(x=jumpPos[0], y=jumpPos[1])


    robot.setPos(y=3, relative=True)
    # Slowly move onto the target moving 1 cm towards it per move
    lastHeight     = -1
    smallStepCount = 0  # If more than 1 z moves result in little movement, quit the function
    lastCoord      = None
    failTrackCount = 0
    robot.setGripper(True)
    for i in range(0, 15):
        print("DownMove ", i)

        # Check the robots tip to make sure that the robot hasn't hit the object or ground and is pressing down on it
        if robot.getTipSensor():
            printf("The robots tip was hit, it must have touched the object. ")
            break
        print("smallstepcount: ", smallStepCount)

        # Height Method: Original
        # Check if the robot has hit the object by seeing if the robots height is less than before, as per the camera
        robCoord = robot.getCoords()
        heightDiff = robCoord[2] - lastHeight

        if heightDiff >= -1.1 and i > 4:
            smallStepCount += 1
        else:
            smallStepCount = 0

        # If the robot has moved up, or it has had various small down moves in a row, quit the loop
        if (heightDiff >= 0 or smallStepCount >= 3) and not lastHeight == -1 and i >= 4:
            printf("Height has stopped decreasing- assuming robot has hit object. Leaving down-move loop")
            break

        lastHeight = robCoord[2]


        # Get the robots marker through the camera by taking the average position of 5 recognitions
        if failTrackCount >= 3:
            printf("Could not find robot for too many down-steps. Exiting pickup")
            robot.setGripper(False)
            return False


        # Actually find the robot using the camera
        newCoord = getRobotAccurate(rbMarker, vision)

        # Check that the robot was found. If not, tally it up and move down anyways
        if newCoord is None:
            printf("Camera was unable to see marker. Moving anyways!")
            failTrackCount += 1
            robot.setPos(z=-1.25, relative=True)
            continue

        lastCoord = newCoord


        # TEST 2
        # If its still moving down, then perform a down-move. JumpSize is how far it will jump to get closer to the obj
        if failTrackCount > 0:
            jumpSize = 2.0
        else:
            jumpSize = 1.0

        # Get the relative move, multiply
        relMove   = getRelativeMoveTowards(lastCoord, targetCamPos, ptPairs)
        unitVec   = unitVector(relMove)
        finalMove = unitVec * jumpSize
        print("Final move: ", finalMove)

        robot.setPos(x=finalMove[0], y=finalMove[1], relative=True)

        robot.setPos(z=-1.25, relative=True)

        failTrackCount = 0

    # Try to get a new view of the robot to test if the pickup was successfull
    newCoord = getRobotAccurate(rbMarker, vision, maxAttempts=1)
    if newCoord is not None:
        lastCoord = newCoord



    if lastCoord is not None and pointInPolygon(lastCoord, pickupRect):
        printf("PICKUP WAS SUCCESSFUL!")

        # Slowly lift the robots head
        while robot.getTipSensor():
            robot.setPos(z=1, relative=True)

        robot.setPos(z=8, relative=True)
        return True
    else:
        printf("PICKUP WAS NOT SUCCESSFUL!")
        robot.setGripper(False)
        robot.setPos(z=8, relative=True)
        return False

def getRelativeMoveTowards(robotCamCoord, destCamCoord, ptPairs):
    """
    :param robotCoord: Cameras coordinate for the robot
    :param destCoord:  Cameras coordinate for the destination
    :param distance:   How far it will move towards the object, in robot coordinates (cm)
    :param robot:      Robot obj
    """

    print("Robot cam coord: ", robotCamCoord, "Destination cam coord: ", destCamCoord)
    camToRobTrans = createTransformFunc(ptPairs, direction="toRob")
    robotRobCoord = camToRobTrans(robotCamCoord)
    destRobCoord  = camToRobTrans(destCamCoord)

    print("Current robot position: ", robotRobCoord, "Destination robot position: ", destRobCoord)
    offset = np.asarray(destRobCoord) - np.asarray(robotRobCoord)
    print("Final robot offset", offset)


    # Actually move the robot
    # If there is no z coordinate, then just don't move along the z

    return offset













# DEPRECATED
# def searchForNearestCamPt(robCoord, ptPairs):
#
#     closestDist  = -1
#     closestIndex = -1
#     print("Testing coord", robCoord)
#     for i, ptPair in enumerate(ptPairs):
#         distance = dist(robCoord, ptPair[1])
#
#         #                ((robCoord[0] - ptPair[1][0])**2 +
#         #         (robCoord[1] - ptPair[1][1])**2 +
#         #         (robCoord[2] - ptPair[1][2])**2)**.5
#         #
#         if distance < closestDist or closestIndex == -1:
#             print(ptPair, distance)
#             closestDist  = distance
#             closestIndex = i
#
#     return ptPairs[closestIndex]

# def sortPointsByDistance(camPos, ptPairs):
#     # Sorts the camPts and robPts simultaneously by the distance from camPos
#     sortedPairs = sorted(ptPairs, key=lambda pointPair: dist(camPos, pointPair[0]))
#     return sortedPairs





# NOT USED
def getPositionCorrection(destPos, actualPos):
    # Returns the destination position offset by the difference between actualPos and destPos
    offset = np.asarray(destPos) - np.asarray(actualPos)
    newPos =  np.asarray(destPos) + offset
    return newPos.tolist()

def getRelativePosition(camPos, robRelative, ptPairs):
    """
    Insert a camera position of something, then offest it by coordinates in the robots coordinate field.
    :param camPos: Location to be offset
    :param robRelative: The offset, using robot coordinate points
    :param ptPairs: Calibration info
    :return:
    """

    posRob    = getPositionTransform((camPos[0], camPos[1], camPos[2]), direction="toRob", ptPairs=ptPairs)
    posCam    = getPositionTransform(posRob, direction="toCam", ptPairs=ptPairs)
    staticErr = camPos - posCam

    posRob    = getPositionTransform((camPos[0], camPos[1], camPos[2]), direction="toRob", ptPairs=ptPairs)
    posRob[0] += robRelative[0]
    posRob[1] += robRelative[1]
    posRob[2] += robRelative[2]

    posCam  = getPositionTransform(posRob, direction="toCam", ptPairs=ptPairs)
    posCam += staticErr

    return posCam



