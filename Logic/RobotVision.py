import math
import cv2
import numpy as np
from time         import time, sleep
from Logic.Global import printf

"""
A set of functions that use Robot and Vision classes to perform a task, all in tandem.

This combines with things like calibrations as well.
"""


# Minimum amount of tracking points to decide to attempt to pick up an object
MIN_POINTS_TO_LEARN_OBJECT = 150  # Minimum number of points to decide an object is valid for creating
MAX_FRAME_AGE_MOVE         = 5    # Maximum age of a tracked object to move the robot towards it
MIN_POINTS_PICKUP_OBJECT   = 50   # Minimum points on an object for the robot to see an object and pick it up
MIN_POINTS_FOCUS           = 40   # Minimum tracking points to just move the robot over an object
MAX_FRAME_FAIL             = 15   # Maximum times a function will get a new frame to recognize an object before quitting

# General Use Functions (May or may not use vision or robot)
def wait(waitTime, exitFunc):
    """
    This is a convenience function for waiting a certain amount of time. The idea is that the exitFunc will
    quit the wait at any point that it returns True. This is so that when the interpreter is stopped, all
    commands will exit quickly and easily.
    """

    waitedTime = 0

    # While sleeping, make sure that the script has not been shut down
    start = time()
    while time() - start < waitTime - .05:
        if exitFunc(): return
        sleep(.05)


    sleep(waitTime - (time() - start))

def waitUntilTime(timeMS, exitFunc):
    # Waits until a certain time is reached, where timeMS is the time in miliseconds since some 1970

    if exitFunc(): return

    while time() < timeMS - 0.055:
        if exitFunc(): return
        sleep(.05)


    # Sleep the last little bit, for extra accuracy
    now = time()
    if now < timeMS:
        sleep(timeMS - now)



def playMotionPath(motionPath, robot, exitFunc):
    TIME    = 0
    GRIPPER = 1
    SERVO0  = 2
    SERVO1  = 3
    SERVO2  = 4
    SERVO3  = 5


    setServo = lambda num, val: (lambda: robot.setServoAngles(servo0=val),
                                 lambda: robot.setServoAngles(servo1=val),
                                 lambda: robot.setServoAngles(servo2=val),
                                 lambda: robot.setServoAngles(servo3=val))[num]()



    # On the first iteration, move to the start position using a slow move
    action = motionPath[0]

    lastVal = [action[SERVO0], action[SERVO1], action[SERVO2], action[SERVO3]]
    setServo(0, lastVal[0])
    setServo(1, lastVal[1])
    setServo(2, lastVal[2])
    setServo(3, lastVal[3])


    # Start running through motionPath
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







# Transform math
def createTransformFunc(ptPairs, direction):
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
                                        confidence = .9999999)

    if not ret: printf("RobotVision.createCameraToRobotTransformFunc(): ERROR: Transform failed!")

    # Returns a function that will perform the transformation between pointset 1 and pointset 2 (if direction is == 1)

    transformFunc = lambda x: np.array((M * np.vstack((np.matrix(x).reshape(3, 1), 1)))[0:3, :].reshape(1, 3))[0]

    return transformFunc

def getPositionTransform(posToTransform, ptPairs, direction):
    transform = createTransformFunc(ptPairs, direction)
    return transform(posToTransform)

def getPositionCorrection(destPos, actualPos):
    # Returns the destination position offset by the difference between actualPos and destPos
    offset = np.asarray(destPos) - np.asarray(actualPos)
    newPos =  np.asarray(destPos) + offset
    return newPos.tolist()

def getRelativePosition(camPos, robRelative, ptPairs):

    posRob    = getPositionTransform((camPos[0], camPos[1], camPos[2]), ptPairs, direction=1)
    posCam    = getPositionTransform(posRob, ptPairs, direction=-1)
    staticErr = camPos - posCam

    posRob    = getPositionTransform((camPos[0], camPos[1], camPos[2]), ptPairs, direction=1)
    posRob[0] += robRelative[0]
    posRob[1] += robRelative[1]
    posRob[2] += robRelative[2]

    posCam  = getPositionTransform(posRob, ptPairs, direction=-1)
    posCam += staticErr

    return posCam





# Coordinate math
def dist(p1, p2):
    return ((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2 + (p2[2] - p1[2])**2)**.5

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
        temp_point = point[0]-centerPoint[0], point[1] - centerPoint[1]
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


    window = degree * 2 - 1


    if len(list1) < window:
        printf("RobotVision.smoothListGaussian(): ERROR: Attempted to smooth list that was too small to be smoothed")
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
        smoothing = [0.0 for i in range(len(list1[i]))] # [0.0, 0.0, 0.0]
        for e, w in zip(list1[i:i + window], weight):
            smoothing = smoothing + np.multiply(e, w)

        smoothed[i] = smoothing / sum(weight)

    return smoothed

# Long form functions with lots of steps
def pickupObject(trackable, rbMarker, ptPairs, groundHeight, robot, vision, exitFunc):
    def getRobotAccurate(rbMarker, vision, maxAttempts=10):
        # A little convenience function that is used several times in the pickup
        moveThresh  = 10
        lowest      = [None, None]
        for s in range(0, maxAttempts):
            vision.waitForNewFrames()
            # trackRob = vision.getObjectBruteAccurate(rbMarker, minPoints   = MIN_POINTS_PICKUP_MARKER,
            #                                                    maxFrameAge = 0,
            #                                                    maxAttempts = MAX_FRAME_FAIL)
            avgPos, avgMag, avgDir = vision.getObjectSpeedDirectionAvg(rbMarker)

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
        printf("RobotVision.pickupObject(): The object is not on screen. Aborting pickup.")
        return False


    # Get a super recent frame of the object with high point count and accuracy
    trackedObj = vision.getObjectBruteAccurate(trackable,
                                               minPoints   = MIN_POINTS_PICKUP_OBJECT,
                                               maxFrameAge = 0,
                                               maxAttempts = MAX_FRAME_FAIL)
    if trackedObj is None:
        printf("PickupObjectCommand.run(): Couldn't get the object accurately!")
        return False

    center = trackedObj.center
    posRob    = getPositionTransform((center[0], center[1], center[2]), ptPairs, direction=1)
    print("zeroPosRob: ", posRob)
    posCam    = getPositionTransform(posRob, ptPairs, direction=-1)
    print("zeroPosCam: ", posCam)
    print("original: ", center)
    staticErr = center - posCam
    print("StaticErr", staticErr, "\n\n")
    posRob    = getPositionTransform((center[0], center[1], center[2]), ptPairs, direction=1)
    print("NewPosRob", posRob)
    posRob[2] += trackedObj.view.height + 5
    if posRob[2] < groundHeight + 1:
        printf("RobotVision.pickupObject(): Predicted position was below groundheight. Moving to groundheight instead.")
        posRob[2] = groundHeight + 1
    print("WithHeight", posRob)
    posCam    = getPositionTransform(posRob, ptPairs, direction=-1)
    print("NewPosCam", posCam)
    posCam += staticErr
    objCamZ = posCam[2]



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
    pos = getPositionTransform(targetCamPos, ptPairs, direction=1)
    # if pos[2] + 5 < groundHeight: pos[2] = groundHeight - 5  # TODO: Fix this bug

    robot.setPos(z=pos[2])
    robot.setPos(x=pos[0], y=pos[1])



    # Try to "Jump" towards the object by measuring the desired pos and the offset
    lastCoord = getRobotAccurate(rbMarker, vision)
    if lastCoord is None:
        printf("RobotVision.pickupObject(): Could not find robot before jump! Exiting pickup")
        return False

    camPos  = getPositionCorrection(targetCamPos, lastCoord)
    jumpPos = getPositionTransform(camPos, ptPairs, 1)
    if jumpPos[2] < groundHeight: jumpPos[2] = groundHeight  # TODO: Fix this bug

    print("Jumping robot: ", jumpPos)
    if abs(jumpPos[1] - robot.pos['y']) < 7 and abs(jumpPos[0] - robot.pos['x']) < 7:
        robot.setPos(x=jumpPos[0], y=jumpPos[1])
    # if jumpPos[2] < robot.pos['z'] - 3: jumpPos[2] = robot.pos['z'] - 3
    # print("Actually jumping to: ", jumpPos)
    # Jump downwards, but constrain it between two values
    # robot.setPos(z=jumpPos[2])

    # self.clamp = lambda lower, num, higher: max(lower, min(num, higher))

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
            printf("RobotVision.pickupObject(): The robots tip was hit, it must have touched the object. ")
            break
        print("smallstepcount: ", smallStepCount)

        # Height Method: Original
        # Check if the robot has hit the object by seeing if the robots height is less than before, as per the camera
        robCoord = robot.getCurrentCoord()
        heightDiff = robCoord[2] - lastHeight
        print("heightdiff", heightDiff, "lastHeight", lastHeight, "currheight", robCoord[2], "sentHeight: ", robot.pos['z'])
        if heightDiff >= -1.1 and i > 4:
            smallStepCount += 1
        else:
            smallStepCount = 0
        if (smallStepCount >= 3 or heightDiff >= 0) and not lastHeight == -1 and i >= 4:
            printf("RobotVision.pickupObject(): Robot has hit the object. Leaving down-move loop")
            break

        lastHeight = robCoord[2]


        # Get the robots marker through the camera by taking the average position of 5 recognitions
        if failTrackCount >= 3:
            printf("RobotVision.pickupObject(): Could not find robot for too many down-steps. Exiting pickup")
            robot.setGripper(False)
            robot.refresh()
            return False

        # Actually find the robot using the camera
        newCoord = getRobotAccurate(rbMarker, vision)


        # Get the robots current height
        if newCoord is None:
            printf("RobotVision.pickupObject(): Camera was unable to see marker. Moving anyways!")
            failTrackCount += 1
            robot.setPos(z=-1.25, relative=True)
            # if lastCoord is None:
            #     robot.setPos(z=-1.25, relative=True)
            continue

        lastCoord = newCoord


        # TEST 2
        # If its still moving down, then perform a down-move
        if failTrackCount > 0:
            jumpSize = 1.75
        else:
            jumpSize = 1
        relMove = getRelativeMoveTowards(lastCoord, targetCamPos, jumpSize, ptPairs)
        # if robot.pos['z'] < groundHeight - 1.25:
        #     printf("RobotVision.pickupObject(): Robot is below groundHeight. Quiing downmoves")
        #     break
        robot.setPos(x=relMove[0], y=relMove[1], relative=True)
        robot.setPos(z=-1.25, relative=True)
        print("Moving to  z: ", robot.pos["z"])
        robot.refresh()

        failTrackCount = 0

    # Try to get a new view of the robot to test if the pickup was successfull
    newCoord = getRobotAccurate(rbMarker, vision, maxAttempts=1)
    if newCoord is not None:
        lastCoord = newCoord


    if not lastCoord is None and pointInPolygon(lastCoord, pickupRect):
        print("PICKUP WAS SUCCESSFUL!!!")
        robot.setPos(z=8, relative=True)
        return True
    else:
        print("PICKUP WAS NOT SUCCESSFUL!")
        robot.setGripper(False)
        robot.setPos(z=8, relative=True)
        return False

def getRelativeMoveTowards(robotCamCoord, destCamCoord, distance, ptPairs):
    """
    :param robotCoord: Cameras coordinate for the robot
    :param destCoord:  Cameras coordinate for the destination
    :param distance:   How far it will move towards the object, in robot coordinates (cm)
    :param robot:      Robot obj
    """

    transform = createTransformFunc(ptPairs, direction=-1)
    robotRobCoord = transform(robotCamCoord)
    destRobCoord  = transform(destCamCoord)
    offset = np.asarray(destRobCoord) - np.asarray(robotRobCoord)
    # print("Offset: ", offset)
    magnitude = sum(offset**2)**.5
    # print("Magnitude", magnitude)
    unitVec = offset / magnitude
    # print("unit", unitVec)
    relMove = unitVec * distance
    # print("Final relative move: ", relMove)
    # Actually move the robot
    # If there is no z coordinate, then just don't move along the z

    return relMove













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





