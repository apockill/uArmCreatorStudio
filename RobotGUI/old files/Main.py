import math
import cv2
import Common
import Robot
import CheckersAI
import Variables as V
import numpy as np
from Video import Vision
from Video import ImageStitching
from  time import sleep
from threading import Thread



#GENERIC FUNCTIONS
def focusOnTarget(getTargetCoords, **kwargs):
    """
    :param getTargetCoords: FOCUSES ON TARGET
    :param kwargs:
        "targetFocus":  (Default [screenXDimension, screenYdimension]) HOLDS AN ARRAY THAT TELLS YOU WHERE ON THE SCREEN TO FOCUS THE OBJECT
        "tolerance":    (defaults to Variables default) How many pixels away till the object is considered "focused" on.
        "ppX":          (Default -1) The amount of pixels that one "stretch" move of the robot will move. This changes according to what height the robot is at
                                    Which is the reason it is even adjustable. If this is not put in, the robot will target very slowly, but be most likely
                                    to reach the target. So you are trading reliability (at all heights) for speed at a specific situation. Same for ppY, except
                                    relating to the "rotation" movement of the robot.
        "ppY":          (Default -1)
    :return: THE ROBOT WILL HAVE THE OBJECT FOCUSED ON THE PIXEL OF TARGETFOCUS

    RECOMMENDED ppX and ppY VALUES FOR DIFFERENT HEIGHTS:
        HEIGHT = MAX: ppX = 3,    ppY = 12  (avg 3-4 moves)
        HEIGHT = 70:  ppX = 3.75  ppY = 15  (avg 2-4 moves)
        HEIGHT = 0:   ppx = 5.3   ppy = 38  (avg 3-5 moves)
    """

    ppX           = kwargs.get("ppX",           -1)     #Pixels per X move
    ppY           = kwargs.get("ppY",           -1)     #Pixels per Y move
    targetFocus   = kwargs.get("targetFocus",   [screenDimensions[0] / 2, screenDimensions[1] / 2])   #The XY value of WHERE on the screen we want the robot to focus on.
    tolerance     = kwargs.get("tolerance",     15)
    maxMoves      = kwargs.get("maxMoves",      1000)
    jump          = kwargs.get("jump",          0)      #jump several incriments at once when far from the target area
    waitTime      = kwargs.get("wait",          0)     #Miliseconds to wait between moves
    targetSamples = kwargs.get('targetSamples', 1)

    sign        = lambda x: (1.0, -1.0)[x < 0]  #sign(x) will return the sign of a number'
    moveCount   = 0                         #The amount of moves that it took to focus on the object

    while True:  #Robot arm will slowly approach the target
        try: #GET THE POSITION OF THE TARGET ON THE SCREEEN. IF TARGETSAMPLES > 1, GET THE AVERAGE OF THE SAMPLES
            avgCoords = [0, 0]
            for s in range(targetSamples):
                coords = getTargetCoords()
                avgCoords = [a + b for a, b in zip(coords, avgCoords)] #Sum the lists
                lastFrame = vid.frameCount
                while lastFrame == vid.frameCount and not s == targetSamples - 1: pass  #Wait for new frame
            coords = [n / targetSamples for n in avgCoords]

        except NameError as e:  #IF TARGET NOT FOUND, THROW AN ERROR
            print "ERROR: focusOnTarget(): error (", e, "). Object not found. Leaving Function..."
            return
            #raise  #RE-Raise the exception for some other program to figure out


        #CALCULATE THE DISTANCE FROM THE TARGETFOCUS TO THE TARGET COORDINATES
        distance = ((coords[0] - targetFocus[0]) ** 2 + (coords[1] - targetFocus[1]) ** 2) ** 0.5  #For debugging
        xMove = 0.0
        yMove = 0.0
        yDist = targetFocus[0] - coords[0]
        xDist = targetFocus[1] - coords[1]

        #FIGURE OUT WHAT DIRECTION TO MOVE, AND HOW MUCH
        if abs(xDist) > tolerance:
            xMove  = sign(xDist) * 1.0
            xMove += sign(xDist) * jump * (abs(xDist) > tolerance * 5)  #If far from the target, then move a little faster
            xMove += (xDist / ppX)   * (abs(xDist) > tolerance * 2     and not ppX == -1)  #If a pp? setting was sent in kwArgs, then perform it.

        if abs(yDist) > tolerance:
            yMove  = sign(yDist) * .5
            yMove += sign(yDist) * jump * (abs(yDist) > tolerance * 5)
            yMove += (yDist / ppY)   * (abs(yDist) > tolerance * 2     and not ppY == -1)

        print "(x,y) move: ", xMove, yMove," (x,y) Dist: ", xDist, yDist, " Tolerance: ", tolerance

        #PERFORM THE MOVE
        if not (abs(xDist) < tolerance and abs(yDist) < tolerance):
            moveCount += 1
            Robot.moveTo(rotation = -yMove, stretch = xMove)  #TODO: make a variable that flips these around according to orientation of camera
            #print Robot.getPosArgsCopy()
            if yDist < tolerance * 1.5 or xDist < tolerance * 1.5:  #Slow down a bit when approaching the target
               sleep(.1 + waitTime)
            else:
               sleep(waitTime)

            if Robot.pos["stretch"] == Robot.stretchMax or Robot.pos["stretch"] == Robot.stretchMin:
                print "stretch at max or min"
                if abs(yDist) < tolerance:  #If the robot can still focus more on the rotation
                    print "focusOnTarget():\tObject out of Stretching reach, but Rotation was focused"
                    break

                if Robot.pos["rotation"] == Robot.rotationMax or Robot.pos["rotation"] == Robot.rotationMin:
                    print "focusOnTarget():\tObject out of BOTH Stretching and Rotation Reach. Quiting Targeting..."
                    break

            if Robot.pos["rotation"] == Robot.rotationMax or Robot.pos["rotation"] == Robot.rotationMin:
                print "rot at max or min"
                if abs(xDist) < tolerance:  #If the robot can still focus more on the rotation
                    print "focusOnTarget():\tObject out of Rotating reach, but Stretch was focused"
                    break


            if moveCount >= maxMoves:
                print "focusOnTarget():\tERROR: Robot moved ", moveCount, " which is over the move limit."
                break

        else:
            print "focusOnTarget():\tObject Targeted in ", moveCount, "moves.", " Final distance from target: ", distance, 'xDist: ', xDist, 'yDist: ', yDist, 'tolerance: ', tolerance
            break

def focusOnCoord(coords, **kwargs):  #Arguments: targetFocus (The pixel location where you want the target to be alligned. Default is the center of the screen
    targetFocus = kwargs.get('targetFocus', [screenDimensions[0] / 2, screenDimensions[1] / 2])
    if len(coords) == 0:
        print "Trouble focusing on coord:", coords
        return
    diffX = coords[0] - targetFocus[0]
    diffY = coords[1] - targetFocus[1]
    #ratio = (Robot.pos['height'] + 60.0) / (Robot.heightMax + 60.0)
    #print Robot.pos['height']
    #ratio = 1  #for not, while I get THAT working...
    xMove = (diffX / (V.pixelsPerX ))
    yMove = (diffY / (V.pixelsPerY  ))
    print "Xmove: ", xMove, "Ymove: ", yMove
    Robot.moveTo(rotation = yMove / 2, stretch = xMove * 2, waitForRobot = True)
    #Robot.moveTo(x = xMove, y = -yMove, waitForRobot = True)

def calibrateRobotCamera(target):
    """
        Figures out important variables for the robot from a series of trials and repeats and then averaging the result
    avgPixelPerX    Using cartesian coordinates, how many pixels (at max height) does an object move per unit x move of the robot?
    avgPixelPerY    Same as above, but for y
    """
    xToMove             = 110.0   #How many degrees to turn during the rotation test.
    yToMove             = 75.0   #How many 'units' to stretch
    avgPixelPerX        = 0.0
    avgPixelPerY        = 0.0
    #Robot.moveTo(height = 90, relative = False, wiatForRobot = True)#(V.heightMax - V.heightMin) / 2)
    for x in range(0, V.trialsForCalibration):
        focusOnTargetManual(target)

        #X CALIBRATION: GO TO COORD 1
        Robot.moveTo(x = xToMove / 2, waitForRobot = True)
        coords1 = objTracker.getTargetAvgCenter(target, V.framesForCalibration)
        #GO TO COORD 2
        Robot.moveTo(x = -xToMove, waitForRobot = True)
        coords2 = objTracker.getTargetAvgCenter(target, V.framesForCalibration)
        #GO TO COORD 3
        Robot.moveTo(x = xToMove, waitForRobot = True)
        coords3 = objTracker.getTargetAvgCenter(target, V.framesForCalibration)

        Robot.moveTo(x = -xToMove / 2)                       #Return robot
        avgPositiveX =  (coords2[0] - coords1[0]) / xToMove
        avgNegativeX =  (coords2[0] - coords3[0]) / xToMove
        avgPixelPerX += (avgPositiveX + avgNegativeX) / 2.0
        print 'Avg Positive X: %s' % avgPositiveX
        print 'Avg Negative X: %s' % avgNegativeX

        #Y CALIBRATION: GO TO COORD 1
        focusOnTargetManual(target)
        Robot.moveTo(y = yToMove / 2, waitForRobot = True)
        coords1 = objTracker.getTargetAvgCenter(target, V.framesForCalibration)
        #GO TO COORD 2
        Robot.moveTo(y = -yToMove, waitForRobot = True)
        coords2 = objTracker.getTargetAvgCenter(target, V.framesForCalibration)
        #GO TO COORD 3
        Robot.moveTo(y = yToMove, waitForRobot = True)
        coords3 = objTracker.getTargetAvgCenter(target, V.framesForCalibration)

        Robot.moveTo(y = -yToMove / 2)                       #Return robot
        avgPositiveY =  (coords1[1] - coords2[1]) / yToMove
        avgNegativeY =  (coords3[1] - coords2[1]) / yToMove
        avgPixelPerY += (avgPositiveY + avgNegativeY) / 2.0

        print 'Avg Positive Y: %s' % avgPositiveY
        print 'Avg Negative Y: %s' % avgNegativeY

    print 'Calibration over'
    return avgPixelPerX / V.trialsForCalibration, avgPixelPerY / V.trialsForCalibration

def waitTillStill(**kwargs):
    maxTime     = kwargs.get("timeout", 1)  #If it goes over maxTime seconds, the function will quit
    maxMovement = kwargs.get("movement", 8)
    if maxMovement <= 5:
        print "waitTillStill(", locals().get("args"), "): It is unwise to set the movement parameter to < than 4. It is set at ", maxMovement

    timer = Common.Timer(maxTime)  #Will wait one second max before continuing
    while objTracker.getMovement() > maxMovement:
        if timer.timeIsUp():
            print "waitTillStill():\tTimer has timed out. Consider lowering acceptableMovement. Continuing...", objTracker.getMovement()
            break

def getAngle(quad):
    """
    :param quad: The 4 coordinate point array
    :return: Returns the angle of the block in the long side, which can be used to orient the wrist of the robot.
    """
    side1 = ((quad[0][0] - quad[1][0]) ** 2.0 + (quad[0][1] - quad[1][1]) ** 2.0) ** 0.5
    side2 = ((quad[1][0] - quad[2][0]) ** 2.0 + (quad[1][1] - quad[2][1]) ** 2.0) ** 0.5
    if side2 < side1:
        angle = math.atan((quad[0][1] - quad[1][1]) * 1.0 / (quad[0][0] - quad[1][0]) * 1.0)
    else:
        angle = math.atan((quad[1][1] - quad[2][1]) * 1.0 / (quad[1][0] - quad[2][0]) * 1.0 )

    angle = math.degrees(angle)
    return angle



###########  JENGA FUNCTIONS ###########
def stackJenga():
  #Main Function
    print "Playing Jenga!"
    #SET UP VARIABLES AND RESET ROBOT POSITION
    blocks = (1, 0, 2)  #The order to place the blocks
    markerLKP = {"rotation": 30, "stretch": 100}  #Keep track of the "marker block"'s "Last Known Position" (LKP)
    searchPos = {'rotation': -15, 'stretch': Robot.stretchMax / 2.5, 'height': Robot.heightMax, 'wrist': 0}
    originalMarker = markerLKP.copy()
    originalSearchPos = searchPos.copy()
    Robot.moveTo(relative = False, waitForRobot = True, **searchPos)  #Get robot in position before testing movementConstant
    movementConstant = (isObjectGrabbed() + isObjectGrabbed() + isObjectGrabbed()) / 3  #Get an average of how much movement there is when there is no block


    for l in (1, 2, 3, 4, 5):  #For each layer
        #FIND A BLOCK, PICK UP THE BLOCK, AND PLACE IT IN THE CORRECT SPOT
        b = 0  #Current block you are putting. THE ORDER IS IN THE "blocks" ARRAY, HOWEVER!!!

        while b in blocks:  #Blocks to place, in order
            print "stackJenga(XXX): Currently on layer ", l, " and on block ", b

            #GO TO POSITION FOR SEARCHING FOR BLOCKS, BUT DO IT SLOWLY AS TO NOT MOVE ROBOT'S BASE
            sleep(.2)
            Robot.moveTo(relative = False, waitForRobot = True, **searchPos)


            #START SEARCHING FOR BLOCKS
            while len(objTracker.getShapes(4)) == 0:  #Search for a view that has a block in it
                if Robot.pos["rotation"] > -69:
                    Robot.moveTo(rotation = -10)
                    waitTillStill()
                else:
                    print "stackJenga():\tNo shapes found after one sweep."
                    searchPos = originalSearchPos.copy()
                    Robot.moveTo(rotation = -15, stretch = V.stretchMax / 2.5, height = V.heightMax, relative = False)  #Go back and sweep again
            searchPos = {"rotation": Robot.pos["rotation"], "stretch": V.stretchMax / 2.5, "height": V.heightMax}


            #PICK UP A BLOCK
            try:
                pickUpBlock(movementConstant, Robot.getPosArgsCopy())  #IF pickUpBlock() FAILS 3 ATTEMPTS, RESTART THIS FOR LOOP
            except Exception as e:
                Robot.setGrabber(0)
                print "ERROR: stackJenga(XXX): ", e, " while picking up block. Restarting for loop and attempting again.."
                continue  #Since b never got upped one, then there is no harm in using continue


            #MOVE TO, FOCUS ON, AND RECORD NEW POSITION, OF THE MARKER BLOCK
            Robot.moveTo(rotation = markerLKP["rotation"] / 2, height = 70, relative = False)
            sleep(.2)
            Robot.moveTo(rotation = markerLKP["rotation"], stretch = markerLKP["stretch"], height = 70, relative = False, waitForRobot = True)
            waitTillStill()
            error = False

            if len(objTracker.getShapes(4)) == 0:  #If marker not seen in the middle, go to the right and check for it
                Robot.moveTo(rotation = markerLKP["rotation"] + 10, stretch = 100, relative = False, waitForRobot = True)
            if len(objTracker.getShapes(4)) == 0:  #If marker still not to the right, move to the left and check for it
                Robot.moveTo(rotation = markerLKP["rotation"] - 10, stretch = 100, relative = False, waitForRobot = True)

            if len(objTracker.getShapes(4)) > 0:  #If the marker HAS been seen, then focus on it.
                try:
                    targetFocus = [screenDimensions[0] * .75, screenDimensions[1] / 2]  #The right edge of the screen
                    focusOnTarget(lambda: objTracker.bruteGetFrame(lambda: objTracker.getNearestShape(4, nearestTo = targetFocus ).center), targetFocus = targetFocus, tolerance = 9, **{"ppX": 3.7, "ppY": 15})
                    print "stackJenga(XXX): Successfully focused on marker block"
                except Exception as e:
                    print "ERROR: stackJenga(XXX): ", e, " while searching for marker."
                    error = True
            else:
                error = True  #If the marker has NOT been seen, catch it right below
            if error:  #If the robot messed up either focusing on the object or having never seen it, then...
                print "stackJenga(XXX): Failed too many times searching for marker. Placing current off to the side, RESETTING markerLKP"
                placeBlock(searchPos, 0, 0)
                markerLKP = originalMarker.copy()
                continue
            waitTillStill()


            #RECORD NEW ADJUSTED "LAST KNOWN POSITION" OF markerLKP, THROUGH AN AVG OF LAST AND CURRENT.
            if abs(Robot.pos["rotation"] - markerLKP["rotation"]) < 20 and abs(Robot.pos["stretch"] - markerLKP["stretch"]) < 30 and not (l == 1 and b == 0):  #If the marker is in a semi-valid position, then RECORD that position. (used to be a big issue)
                markerLKP = {"rotation": (markerLKP["rotation"] + Robot.pos["rotation"]) / 2, "stretch": (markerLKP["stretch"] + Robot.pos["stretch"]) / 2}  #Get avg of last known position and new known position (messes things up less)
                print "stackJenga(XXX): New location of markerLKP: ", markerLKP  #Print new location of the marker
            else:
                print "stackJenga(XXX): SOMETHINGS GONE WRONG with markerLKP! markerLKP: ", markerLKP


            #PLACE BLOCK ONTO THE CORRECT POSITION ON THE STACK
            placeBlockAtPosition(l, blocks[b])
            b += 1  #Mark block on layer as completed, so for loop will move on to next block.

    #MISSION COMPLETE! INITIATE DANCE SEQUENCE!
    Robot.moveTo(relative = False, **Robot.home)
    sleep(.6)
    Robot.moveTo(rotation = -30)
    sleep(.3)
    Robot.moveTo(rotation = 30)
    sleep(.3)
    Robot.moveTo(height = 0)
    sleep(.3)
    Robot.moveTo(height = Robot.heightMax)
    sleep(.3)

def isObjectGrabbed():
    currentWrist = Robot.pos["wrist"]
    Robot.moveTo(wrist = -40, relative = False)
    Robot.moveTo(wrist = 20, relative = False)
    sleep(.01)
    movement = objTracker.getMovement()

    Robot.moveTo(wrist = currentWrist, relative = False)
    print "isObjectGrabbed():\tMovement = ", movement
    return movement

def pickUpBlock(movConstant, objectLastSeen, **kwargs):
    """
    Robot will attempt to pick up block. If it fails, it will RECURSIVELY attempt to pick it up again from the last known position. kwarg "attempts" is used to cut off the robot after
    the 3rd (configurable) attempt.
    :param movementConstant: this is the average pixel change per frame when the robot is stationary and there is no jenga block in it's grabber when the grabber moves.
                            It is used with isObjectGrabbed to detect if the robot successfuly grabbed a jenga block
    :param startingPos:     Self explanatory. String of robot position, from where to start
    :return:
    kwargs:
        attempts: Counts how many times before this program has run itself recursively, in order to determine if it should stop attempting and return an error.
        attemptRefocus: (Defaults to true). If this is true, the robot will attempt to refocus on the block using a different manner if it is >50 or <-50 degrees position.
    """
    attempts = kwargs.get("attempts", 0)                                                                            #Total times this func has been run recursively (at 3, it raises an error)
    attemptRefocus = kwargs.get("attemptRefocus", True)                                                             #Should robot attempt to do fancy refocusing on certain blocks
    targetCenter = [screenDimensions[0] / 2, screenDimensions[1] / 2]                                               #Target center of screen
    heightSettings = {"150": {"ppX": 3, "ppY": 12}, "70": {"ppX": 3.7, "ppY": 15}, "0": {"ppX": 5.3, "ppY": -1}}    #Holds the best ppX ppY settings for different heights.
    getShapeCenter = lambda: objTracker.bruteGetFrame(lambda: objTracker.getNearestShape(4).center)                 #This function is used a lot, so it was useful to save as a variable.

    #CHECK IF THIS FUNCTION HAS BEEN RUN RECURSIVELY MORE THAN THE SET LIMIT, AND QUIT IF IT HAS
    print "pickUpPiece():\tAttempt number: ", attempts
    if attempts == 3:  #If max attempts have been hit
        print "pickUpPiece():\tToo many recursive attempts. Raising error"
        raise Exception("BlockNotGrabbed")


    #GET ROBOT INTO POSITION AND CHECK IF THE OBJECT IS STILL THERE. QUIT IF IT IS NOT.
    waitTillStill()
    Robot.setGrabber(0)
    Robot.moveTo(relative = False, **objectLastSeen)
    waitTillStill()
    sleep(.1)
    if len(objTracker.getShapes(4)) == 0:  #If no objects in view
        print "pickUpPiece():\tNo objects seen at start. Raising error..."
        raise NameError("ObjNotFound")


    #BEGIN FOCUSING PROCESS UNTIL ROBOT IS AT 0 HEIGHT AND COMPLETELY FOCUSED ON OBJECT
    try:
        if Robot.pos["height"] == 150:
            print "pickUpBlock():\tFocus at height 150"
            objectLastSeen = Robot.getPosArgsCopy(dontRecord = ["wrist, grabber, height"])
            focusOnTarget(getShapeCenter, **heightSettings["150"])  #Tries many times (brute) to get the nearest shapes .center coords & focus
            objectLastSeen = Robot.getPosArgsCopy(dontRecord = ["wrist, grabber, height"])
            Robot.moveTo(height = 70, relative = False)
            waitTillStill()

        if Robot.pos["height"] == 70:
            print "pickUpBlock():\tFocus at height 70"
            focusOnTarget(getShapeCenter, **heightSettings["70"])
            objectLastSeen = Robot.getPosArgsCopy(dontRecord = ["wrist, grabber, height"])
            Robot.moveTo(height = 0, relative = False)
            waitTillStill()

        if Robot.pos["height"] == 0:
            print "pickUpBlock():\tFocus at height 0"
            focusOnTarget(getShapeCenter,  tolerance = 7, **heightSettings["0"])
            objectLastSeen = Robot.getPosArgsCopy(dontRecord = ["wrist, grabber, height"])

        shape = objTracker.bruteGetFrame(lambda: objTracker.getNearestShape(4)).vertices
    except NameError as e:
        print "ERROR: pickUpBlock():\t", e
        pickUpBlock(movConstant, objectLastSeen, attempts = attempts + 1)
        return False
        #raise Exception("PickupFailed")


    #IF THE OBJECT IS > 50 OR < -50 DEGREES, DO ANOTHER ROUND OF FOCUSING ON IT, AND PERFORM A DIFFERENT "DROP DOWN" MANUEVER
    angle = getAngle(shape)  #Get angle of object in camera
    if (angle > 50 or angle < -50) and attemptRefocus:
        try:
            print "pickUpBlock():\tPerforming re-focusing manuever on block of angle: ", angle
            targetFocus = [screenDimensions[0] / 3.5, screenDimensions[1] / 2]
            focusOnTarget(lambda: objTracker.bruteGetFrame(lambda: objTracker.getNearestShape(4, nearestTo = targetFocus).center),  tolerance = 8, targetFocus = targetFocus, **heightSettings["0"])
            objectLastSeen = Robot.getPosArgsCopy(dontRecord = ["wrist, grabber, height"])
        except NameError as e:  #Since it failed, try again but this time send the function a "normalPickup = True", so it won't attempt to do it again
            print "ERROR: pickUpBlock():\t", e, " when trying to RE-FOCUS on a >50 <-50 block"
            pickUpBlock(movConstant, objectLastSeen, attempts = attempts + 1, attemptRefocus = False)
            return False

        #MOVE SO OBJECT IS UNDER GRABBER
        Robot.moveTo(height = -05, relative = False)  #Ease into it
        waitTillStill()
        Robot.moveTo(stretch = 26)
        waitTillStill()

    else:
        #MOVE SO OBJECT IS UNDER GRABBER
        Robot.moveTo(stretch = 52, rotation = 2.25)  #Added a rotation to fix weird issues that had been occurring...
        waitTillStill()


    #MOVE WRIST, AND DESCEND ONTO OBJECT AND PICK IT UP
    Robot.moveTo(wrist = angle, height = -20, relative = False)
    sleep(.075)
    Robot.moveTo(height = -38, relative = False)
    sleep(.05)
    Robot.setGrabber(1)  #Pick up object
    sleep(.125)
    Robot.moveTo(height = -5, relative = False)
    sleep(.2)


    #MEASURE THE MOVEMENT OF THE OBJECT AS THE WRIST MOVES
    Robot.moveTo(wrist = -40, relative = False)  #Start rotating the wrist
    Robot.moveTo(wrist = 20, relative = False)
    timer = Common.Timer(.4)
    highestMovement = 0
    while not timer.timeIsUp(): #Gets the highest measured movement in .3 seconds, to DEFINITELY catch the wrist moving. Eliminates problems.
        newMovement = objTracker.getMovement()
        if newMovement > highestMovement: highestMovement = newMovement
        if highestMovement > movConstant + 1.5: break
    print "pickUpBlock():\thighestMovement: ", highestMovement


    #IF MOVEMENT IS < MOVCONSTANT, THEN NO OBJECT WAS PICKED UP. RE-RUN FUNCTION.
    if highestMovement < movConstant + 3:
        print "pickUpBlock():\tFailed to suck in object. Retrying..."
        pickUpBlock(movConstant, objectLastSeen, attempts = attempts + 1, attemptRefocus = not attemptRefocus)
        return False

    Robot.moveTo(wrist = 0, relative = False)  #Return wrist
    return True

def placeBlock(position, height, wrist):
    currentPosition = Robot.getPosArgsCopy()
    Robot.moveTo(rotation = position["rotation"], stretch = position["stretch"], relative = False)  #GET IN POSITION OVER DROP ZONE
    Robot.moveTo(height = height, wrist = wrist, waitForRobot = True, relative = False)
    Robot.setGrabber(0)
    Robot.moveTo(height = currentPosition["height"], relative = False)
    Robot.moveTo(relative = False, **currentPosition)

def placeBlockAtPosition(layer, position):
    """
    FOR THE TOWER BUILDING. Aligns the brick to either a horizontal or vertical position, determined mathematically by the "layer" variable.
    The "layer" variable determines the height.
    The "position" variable is a string- it is either 0, 1, 2 determining where on the current layer of the tower (1 = left, 2 = middle, or something akin).
    that the brick should go on.
    :param layer: Layer on the building. Starts at 1. 1st layer is horizontal.
    :param position: "right", "left
    :return: A brick placed
    """
    #SET UP VARIABLES
    currentPosition = Robot.getPosArgsCopy()  #Back up the position in case of error
    heightForLayer = {"1": -32, "2": -15, "3": 3, "4": 24, "5": 40.5}
    print "placeBlockAtPosition():\tCurrent pos: ", currentPosition

    #PICK THE RELEVANT MOVEMENTS FOR EACH LAYER/POSITION, AND PERFORM IT
    if not layer % 2:  #IF THIS IS THE VERTICAL LAYER
        print "PLACING DOWN VERTICAL BLOCK ON POSITION ", position, "ON LAYER ", layer
        #HOW MUCH STRETCH / ROTATION IS NECESSARY FOR EACH POSITION. [POSITION]
        rotToMoveSide     = [19,  0, -19]
        rotToMoveSlip     = [-12, 0,   10]
        stretchToMove     = [-2,  0,  -2]  #Adjust the angle so it is truly vertical.
        wristToMove       = [-10, 0,  10]
        Robot.moveTo(height = heightForLayer[str(layer)] + 34, wrist = wristToMove[position], relative = False)  #Move Wrist BEFORE going all the way down, or else you might knock some blocks
        Robot.moveTo(rotation =  rotToMoveSide[position], stretch = stretchToMove[position])  #Go besides (but offset) to the end position of the block
        sleep(.1)
        Robot.moveTo(height = heightForLayer[str(layer)], relative = False)  #Finish going down
        waitTillStill()
        Robot.moveTo(rotation = rotToMoveSlip[position] * .75)  #Slip block in to the correct position sideways (Hopefully pushing other blocks into a better position
        sleep(.1)
        Robot.moveTo(rotation = rotToMoveSlip[position] * .25)  #Slip block in to the correct position sideways (Hopefully pushing other blocks into a better position

    else:           #IF THIS IS THE HORIZONTAL LAYER
        stretchToMoveSide = [-45, 0, 49]  #To get parallel to the part
        stretchToMoveSlip = [25, 0, -25]  #To slip it in all the way
        wristToMove = 73.5  #Equivalent to 90 degrees, for some reason
        Robot.moveTo(height = heightForLayer[str(layer)] + 34, wrist = wristToMove, relative = False)  #Move Wrist BEFORE going all the way down, or else you might knock some blocks
        Robot.moveTo(stretch = stretchToMoveSide[position])
        sleep(.1)
        Robot.moveTo(height = heightForLayer[str(layer)], relative = False)  #Finish going down
        waitTillStill()
        Robot.moveTo(stretch = stretchToMoveSlip[position] * .75)  #Ease into the correct position by splitting it into two moves
        sleep(.1)
        Robot.moveTo(stretch = stretchToMoveSlip[position] * .25)

    #DROP BRICK AND GO BACK TO ORIGINAL POSITION
    sleep(.1)
    print Robot.pos
    Robot.setGrabber(0)
    Robot.moveTo(height = currentPosition["height"], relative = False)
    sleep(.2)
    Robot.moveTo(relative = False, **currentPosition)
    waitTillStill()



########### Checkers FUNCTIONS ###########
def playCheckers():
    global streamVideo
    global blurThreshold   #Set below using getMotionAndBlur()
    print "playCheckers():\tBeginning Checkers!"
    streamVideo = True

    allCornerInfo = [{'corners': [{'y': -41.972018918482874, 'x': 184.6128341478034},  {'y': 111.52539890583479, 'x': 147.98033756199985}, {'y': 152.0544435459012,  'x': 302.5572020482049},  {'y': -4.934192457477108, 'x': 339.1830450141577}], 'distFromBase': 154.3,  'height': 100},
                     {'corners': [{'y': -36,                 'x': 174.5993467309843},  {'y': 109.14998136887112, 'x': 147.50773392325937}, {'y': 147.77390766522245, 'x': 290.02262362331373}, {'y': -3.572950570828457, 'x': 327.387773929495}],   'distFromBase': 166.5, 'height':  37},
                     {'corners': [{'y': -44.42989761657374,  'x': 201.10998137167255}, {'y': 121.99579037334762, 'x': 158.98800939436353}, {'y': 154.00209457831087, 'x': 330.25855759615524}, {'y': -0.0, 'x': 363.4}],                            'distFromBase': 195.5, 'height':   5},
                     {'corners': [{'y': -36.10085759999442,  'x': 194.78279718841944}, {'y': 123.32014951791244, 'x': 155.03467587246323}, {'y': 152.15862505048878, 'x': 311.9714134704409},  {'y': 3.1075192909709584, 'x': 356.08644080315145}], 'distFromBase': 191.1, 'height':  -6},
                     {'corners': [{'y': -41.53086900143339,  'x': 199.1986171540355},  {'y': 118.55853582603964, 'x': 156.600958599777},   {'y': 152.57652616058105, 'x': 318.5839365574957},  {'y': -4.100538062572259,  'x': 360.2864712647001}],  'distFromBase': 196.5, 'height': -15}]

    ppXYInfo      = [{'xSamples': 3, 'ppY': -1, 'ppX': 2.458974358974359, 'ySamples': 1, 'height': 100},
                     {'xSamples': 4, 'ppY': 6.7, 'ppX': 5.0015262515262515, 'ySamples': 4, 'height': 37},
                     {'xSamples': 3, 'ppY': -18.933333333333334, 'ppX': -2.801587301587302, 'ySamples': 3, 'height': 5},
                     {'xSamples': 4, 'ppY': -23.866666666666664, 'ppX': 4.196428571428571, 'ySamples': 3, 'height': -6},
                     {'xSamples': 2, 'ppY': -1, 'ppX': 5.875, 'ySamples': 1, 'height': -15}]


    #RUN CALIBRATION FUNCTIONS
    avgMotion, avgBlur  = getMotionAndBlur()
    #avgMotion, avgBlur  = 1.5, 280
    blurThreshold       = avgBlur / 4.35       #Its important to set the thresholds first, before other functions run
    motionThreshold     = avgMotion * 3.25     #that use them (such as getBoardCorners()
    #ppXYInfo, allCornerInfo       = getBoardCorners()    #Get the location of the boards corners at two different robot heights
    #groundFormula      = getGroundFormula(cornerInfoLow['corners'])
    groundFormula       = lambda stretch: -0.0994149347433  * stretch + -45.0


    #SET UP VARIABLES
    cornerInfoHigh = allCornerInfo[0]
    cornerInfoLow  = allCornerInfo[-1]
    ppXYInfoHigh   = ppXYInfo[0]
    ppXYInfoLow    = ppXYInfo[-1]
    jumpFormula    = getJumpFormula(allCornerInfo)
    kingLocation   = [8, 2.5]   #Where the kings are stored relative to the boards grid.
    dumpLocation   = [-3, 2.5]  #Where captured pieces are thrown away



    colorThreshold = 0     #Used to measure what piece is pink and what piece is green. This constant is set later on using getAvgColor()
    kingThreshold  = 0
    firstLoop      = True  #This will tell the robot to calibrate the average color on the first round of the game.
    AI = CheckersAI.DraughtsBrain({'PIECE':    15,  #Checkers AI class. These values decide how the AI will play
                                   'KING':     30,
                                   'BACK':      3,
                                   'KBACK':     3,
                                   'CENTER':    6,
                                   'KCENTER':   7,
                                   'FRONT':     6,
                                   'KFRONT':    3,
                                   'MOB':       6}, 15)

    while not exitApp:
        #MOVE ROBOT OUT OF WAY FOR HUMAN TO MAKE THEIR MOVE
        Robot.moveTo(relative=False, waitForRobot=True, stretch=0, height=150)
        Robot.moveTo(relative=False, waitForRobot=True, rotation=-75)
        cv2.waitKey(3000)

        #WAIT FOR PERSON TO WAVE HAND IN FRONT OF CAMERA BEFORE STARTING MOVE (GIVE PLAYER TIME TO MAKE THEIR MOVE)
        print "playCheckers():\tWaiting for player to signal!"
        while objTracker.getMovement() < motionThreshold: pass
        Robot.moveTo(relative=False, waitForRobot=True, stretch=0, height = 150)


        stitchedFrame = None
        while stitchedFrame is None:
            #stitchedFrame = cv2.imread("F:\Google Drive\Projects\Git Repositories\RobotStorage\RobotArm\stitched.png")

            #GET A STITCHED IMAGE THAT IS AN OVERVIEW OF THE BOARD AREA
            stitchedFrame = getBoardOverview(cornerInfoHigh, finalImageWidth = 1000)
            #cv2.imwrite('F:\Google Drive\Projects\Git Repositories\RobotStorage\RobotArm\stitched.png', stitchedFrame)  #TODO: REMOVE THIS, ITS FOR DEBUGGING ONLY


            #Display the latest stitchedframe on the perspective window
            vid.windowFrame['Perspective'] = stitchedFrame.copy()
            cv2.waitKey(1)


            #FIND THE BOARD IN THE STITCHED IMAGE
            shapeArray, edgedFrame = objTracker.getShapes(sides=4, peri=0.05,  minArea= (stitchedFrame.shape[0] * stitchedFrame.shape[1]) / 4,
                                                          threshHold=cv2.THRESH_OTSU, frameToAnalyze=stitchedFrame, returnFrame = True)


            if len(shapeArray) == 0:  #Make sure that the board was correctly found. If not, restart the loop and try again.
                print "playCheckers():\tNo board Found"
                stitchedFrame = None

        #Display the stitchedframe with the board highlighted
        vid.windowFrame['Perspective'] = objTracker.drawShapes(shapeArray, frameToDraw=stitchedFrame.copy())
        cv2.waitKey(1)



        #ISOLATE THE BOARD AND FIND THE CIRCLES IN IT
        boardFrame  = objTracker.getTransform(shapeArray[0], frameToAnalyze=stitchedFrame, transformHeight=600, transformWidth=600)  #Isolate board
        circleArray = objTracker.getCircles(frameToAnalyze = boardFrame, minRadius = 40)  #Get circles on screen


        #GET THE BOARD STATE
        if firstLoop:
            colorThreshold = getAvgColor(circleArray)[0]  #  If this is the first time being run, get the average color of the pieces on board
            kingThreshold = getHighestSTD(circleArray, boardFrame) * 2
            firstLoop = False
            print "playCheckers():\tColorThreshold: ", colorThreshold, " KingThreshold: ", kingThreshold
        boardState, boardFrame     = getBoardState(boardFrame, circleArray, [600, 600], colorThreshold, kingThreshold)  #Find and label all circles with team, color, and location


        #GET BEST MOVE FROM ROBOT
        print 'playCheckers():\t Calculating best move...'
        move        = AI.best_move(board=boardState[:])  #Get the best possible move for the robot to perform
        moveFrom    = move.getSource()
        moveTo      = move.getDestination()
        moveCapture = move.getCapture()
        print 'playCheckers():\t Move from: ', moveFrom, ' Move to: ', moveTo, ' Capture: ', moveCapture


        #SET FRAMES FOR THE WINDOWS:
        boardFrame  = drawMove(moveFrom, moveTo, moveCapture, circleArray, boardFrame)  #DRAW WHAT PIECE IS MOVING WHERE
        vid.windowFrame['Perspective'] = boardFrame


        #CHECK IF THE MOVE PRODUCED A NEW KING FOR THE ROBOT
        if moveTo[1] == 0:
            if not boardState[moveFrom[1]][moveFrom[0]] == 3:
                newKing = True
            else:
                newKing = False
                print 'playCheckers(): No new king, only king returning to end.'
        else:
            print 'NO NEW KING!'
            newKing = False


        #MOVE ALL THE APPROPRIATE PIECES
        pickUpPiece(moveFrom, cornerInfoLow, ppXYInfoLow, groundFormula, jumpFormula, precision = 11)
        if newKing:
            placePiece(dumpLocation, cornerInfoLow, groundFormula, jumpFormula)
            pickUpPiece(kingLocation, cornerInfoLow, ppXYInfoLow, groundFormula, jumpFormula)

        placePiece(moveTo, cornerInfoLow, groundFormula, jumpFormula)

            #Move captured piece
        if moveCapture is not None:
            pickUpPiece(moveCapture, cornerInfoLow, ppXYInfoLow, groundFormula, jumpFormula, precision = 11)
            placePiece(dumpLocation, cornerInfoLow, groundFormula, jumpFormula)

def getBoardState(frame, circleArray, screenDimensions, colorThreshold, kingThreshold):
    """
    Analyzes the frame and returns an array of where the pieces are in the board

    :param frame: The board frame (Already cropped and warped)
    :param circleArray: The array of circles that have been found on the screen
    :param screenDimensions:
    :param colorThreshold: Helps determine if a piece is red or green
    :param kingThreshold: The standard deviation of color of a piece that determines whether a "k" is written on it.
    :return: A 2d array where 2 and 4 are green pieces (4 is king) and 1 and 3 are red pieces (3 is king)
    """
    global boardSize

    board = [[0 for i in range(boardSize)] for j in range(boardSize)]
    squareSize = (screenDimensions[0] / boardSize)
    dist       = lambda a, b: ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** .5  #sign(x) will return the sign of a number'


    frameToDraw = frame.copy()

    for row in range(boardSize):
        for column in range(boardSize):
           # print 'row: ', row, 'column: ', column, 'squareSize: ', squareSize
            location = [squareSize * column + squareSize / 2, squareSize * row + squareSize / 2]
           # print location
            if len(circleArray) == 0: continue

            circleArray = sorted(circleArray, key = lambda c: (c.center[0] - location[0]) ** 2 + (c.center[1] - location[1]) ** 2)
            nearest     = circleArray[0]


            if dist(nearest.center, location) < squareSize / 2:

                pieceColor = objTracker.bgr2hsv(nearest.color)[0]
                if pieceColor < colorThreshold:
                    if getCircleSTD(nearest, frame) < kingThreshold:
                        board[row][column] = 2  #IF IS GREEN PIECE
                        color = (0, 255, 0)
                    else:
                        board[row][column] = 4  #IF IS GREEN PIECE
                        color = (255, 255, 0)
                else:
                    if getCircleSTD(nearest, frame) < kingThreshold:
                        board[row][column] = 1  #IF IS RED PIECE
                        color = (0, 0, 255)
                    else:
                        board[row][column] = 3  #IF IS RED PIECE
                        color = (0, 255, 255)
                print 'PieceColor: ', pieceColor


                objTracker.drawCircles([nearest], frameToDraw=frameToDraw, color=color)

                #cv2.rectangle(frameToDraw, tuple([fromX, fromY]), tuple([toX, toY]), color, 3)
                cv2.putText(frameToDraw, str(column) + ',' + str(row), (nearest.center[0] - 25, nearest.center[1] + 10), cv2.FONT_HERSHEY_SIMPLEX, 1, 0)
                del circleArray[0]
        #print board[column]

    return board, frameToDraw

def getBoardOverview(cornerInfo, **kwargs):
    """
    Gets several images of the board and stitches them together to return a stitched image of the whole board.
    It then resizes the image if the appropriate kwarg is set.
    """

    corners = cornerInfo['corners']
    finalWidth = kwargs.get("finalImageWidth", -1)
    Robot.moveTo(height=150, relative=False)

    #Location of the top middle of the board and the bottom middle of the board
    picturePositions = [getSquarePosition(2.5, 1, corners),
                        getSquarePosition(2.5, 4, corners)]

    images_array = []
    for index, position in enumerate(picturePositions):
        Robot.moveTo(stretchDistFromBase=cornerInfo['distFromBase'], relative = False, **position)
        sleep(1.5)
        focusCamera()



        images_array.append(vid.frame)

    final_img = ImageStitching.stitchImages(images_array[0], images_array[1:], 0)


    # RESIZE THE IMAGE IF THE finalWidth FUNCTION AN ARGUMENT
    if not finalWidth == -1:
        resized = vid.resizeFrame(final_img, finalWidth)
        return resized

    return final_img

def getSquarePosition(column, row, corners):
    """
    This function returns the estimated robot rotation/stretch that a board square is located in.
    It does this by using the cornerLocations information to estimate the location of a square on the board.
    May not always work accurately, but should speed things up.

    This function will return a coordinate in this format: {"x": ?, "y": ?}
    This format can be sent to Robot.moveTo() command easily.

    Row and column: Where on the board you wish the camera to jump to
    :param corners: The array gotten from getBoardCorners()
    """

    global boardSize

    #For simplicity, get the bottom Right (bR) bottom Left (bL) and so on for each corner.
    ptDist = lambda d, a, b: [a[0] + ((b[0] - a[0]) / dist(a, b)) * d, a[1] + ((b[1] - a[1]) / dist(a, b)) * d]

    #GET [x,y] FORMAT COORDINATES FOR EACH CORNER OF THE CHECKERBOARD
    bR = [float(corners[0]['x']), float(corners[0]['y'])]
    bL = [float(corners[1]['x']), float(corners[1]['y'])]
    tR = [float(corners[3]['x']), float(corners[3]['y'])]
    tL = [float(corners[2]['x']), float(corners[2]['y'])]

    #GET LENGTH OF EACH SIDE
    lenBot = dist(bR, bL)
    lenTop = dist(tR, tL)
    lenRit = dist(bR, tR)
    lenLef = dist(bL, tL)


    #GET POINTS ON EACH SIDE THAT ARE CLOSEST TO THE DESIRED SPOT. ADD .5 TO ROW AND COLUMN CENTER VIEW ON THE MIDDLE OF THE SQUARE
    ptTop = ptDist((lenTop / boardSize) * (column + .5), tL, tR)
    ptBot = ptDist((lenBot / boardSize) * (column + .5), bL, bR)
    ptLef = ptDist((lenLef / boardSize) * (row + .5),    tL, bL)
    ptRit = ptDist((lenRit / boardSize) * (row + .5),    tR, bR)


    #GET THE POINT OF INTERSECTION, WHICH WILL BE THE FINAL POINT FOR THE ROBOT TO GO TO
    s1_x = ptBot[0] - ptTop[0]
    s1_y = ptBot[1] - ptTop[1]
    s2_x = ptRit[0] - ptLef[0]
    s2_y = ptRit[1] - ptLef[1]
    t = (s2_x * (ptTop[1] - ptLef[1]) - s2_y * (ptTop[0] - ptLef[0])) / (-s2_x * s1_y + s1_x * s2_y)
    #cornerOfSquare = [ptTop[0] + (t * s1_x), ptTop[1] + (t * s1_y)]

    finalCoords = {'x': ptTop[0] + (t * s1_x), 'y': ptTop[1] + (t * s1_y)}

    #print 'getSquarePosition():\tbottomL: ', lenBot, ' topL: ', lenTop, ' rightL: ', lenRit, ' leftL: ', lenLef
    #print 'getSquarePosition():\ttopPoint: ', ptTop, ' botPoint: ', ptBot, ' lefPoint: ', ptLef, ' ritPoint: ', ptRit
    #print 'getSquarePosition():\ttopLeft: ', tL, ' topRight: ', tR, ' bottomRight: ', bR, ' bottomLeft: ', bL

    #print 'getSquarePosition():\tFor Row: ', row, ' Col: ', column, ' FinalCoords: ', finalCoords
    return finalCoords


#   #GENERAL USE FUNCTIONS
def focusCamera(**kwargs):
    """
    This function moves the camera closer to the ground forcing it (hopefully) to refocus.
    It then goes back up and tests the blurriness of the camera.
    """

    attempts = 0
    maxAttempts = 3

    if 'blurThreshold' in globals():  #Check that blurThreshold has been defined
        threshold = kwargs.get('threshold', blurThreshold)
    else:
        threshold = kwargs.get('threshold', 200)

    height = Robot.pos['height']
    heightToDrop = 0
    if height >= 100:
        heightToDrop = 100
    elif 0 < height < 100:
        heightToDrop = 50
    else:
        heightToDrop = 10


    while objTracker.getBlur() < threshold and attempts < maxAttempts:  #If the image is too blurry still, keep attempting to focus
        Robot.moveTo(height=-heightToDrop)
        sleep(2)
        Robot.moveTo(height=heightToDrop - 15)
        sleep(.05)
        Robot.moveTo(height=heightToDrop + 30)
        sleep(.05)
        Robot.moveTo(height=heightToDrop, relative=False)
        sleep(2.5)
        attempts += 1

    Robot.moveTo(height=height, relative=False)  #Make 100% sure that the robot is back at its starting height

    if not attempts < maxAttempts:
        print 'focusCamera(): Attempts over ', attempts, ' giving up on focusing... Threshold: ', threshold, "Current blur: ", objTracker.getBlur()
    else:
        print 'focusCamera(): Successfully focused camera.'

#   #DRAW FUNCTIONS
def drawMove(moveFrom, moveTo, capture, circleArray, boardFrame):
    frameToDraw = boardFrame.copy()

    imgWidth = boardFrame.shape[0]  #Get height of image (which should be square)
    squareSize = imgWidth / boardSize

    fromLoc = [squareSize * moveFrom[0] + squareSize / 2, squareSize * moveFrom[1] + squareSize / 2]
    toLoc   = [squareSize * moveTo[0]   + squareSize / 2, squareSize * moveTo[1]   + squareSize / 2]


    circleFrom = sorted(circleArray, key = lambda c: (c.center[0] - fromLoc[0]) ** 2 + (c.center[1] - fromLoc[1]) ** 2)[0]
    #circleTo   = sorted(circleArray, key = lambda c: (c.center[0] -   toLoc[0]) ** 2 + (c.center[1] -   toLoc[1]) ** 2)[0]
    if capture is not None:
        capLoc  = [squareSize * capture[0]  + squareSize / 2, squareSize * capture[1]  + squareSize / 2]
        capLoc = [squareSize * capture[0] + squareSize / 2, squareSize * capture[1] + squareSize / 2]
        circleCapture = sorted(circleArray, key = lambda c: (c.center[0] - capLoc[0]) ** 2 + (c.center[1] - capLoc[1]) ** 2)[0]
        frameToDraw = objTracker.drawCircles([circleCapture], frameToDraw=frameToDraw, color=(0, 0, 255))


    frameToDraw = objTracker.drawCircles([circleFrom], frameToDraw=frameToDraw, color=(255, 255, 255))


    cv2.arrowedLine(frameToDraw, tuple(fromLoc), tuple(toLoc), (255, 255, 255), thickness=3)
    return frameToDraw


#   #PICKUP/PLACEMENT FUNCTIONS
def pickUpPiece(coords, cornerInfo, ppXYInfo, groundHeightFormula, jumpStretchFormula, **kwargs):
    global averageArea   #TODO: delete later, for testing only

    precision = kwargs.get('precision', 9)
    #GET ROBOT INTO POSITION AND CHECK IF THE OBJECT IS STILL THERE. QUIT IF IT IS NOT.
    #Robot.moveTo(stretchDistFromBase=location['distFromBase'], relative=False, **getSquarePosition(location[0], location[1], corners))
    location                        = getSquarePosition(coords[0], coords[1], cornerInfo['corners'])
    location['height']              = cornerInfo['height']
    location['stretchDistFromBase'] = cornerInfo['distFromBase']

    Robot.moveTo(relative=False, **location)
    sleep(.2)



    #SETUP UP VARIABLES FOR THE NEXT SECTION
                     #Each dictionary in this array is a 'setting' for the robot to use when focusing in on the piece. It will
                     #focus on the piece and move down each time for each setting. Meanwhile, it will record the 'focused' pos
                     #for each setting inside of focusPos (it records height, stretch, and rotation.
    settings  = [{'height': location['height'] + 15, 'focusTolerance':     precision,  'avgSampleSize':  25, 'targetSamples':  4},
                 #{'height':      location['height'], 'focusTolerance': 6,  'avgSampleSize':  50, 'targetSamples':   1},
                 {'height': location['height'] - 15, 'focusTolerance': precision + 3,  'avgSampleSize': 25,  'targetSamples':  4}]
    focusPos  = []
    avgRadius = (screenDimensions[0] / 10)  #Default value to start searching for the piece


    #IN THIS SECTION, THE ROBOT WILL FOCUS ON THE PIECE FOR EACH SETTING IN SETTINGS[], AND RECORD THE FOCUSED POSITION ON FOCUS POSTION.
    #ON THE FINAL POSITION IT SHOULD BE PRETTY CLOSE TO THE OBJECT. IT WILL THEN CALCULATE THE CORRECT JUMP TO REACH THE OBJECT,
    #AND PERFORM THE PICKUP MANUEVER.
    for index, s in enumerate(settings):
        Robot.moveTo(height=s['height'], relative=False)
        sleep(1)

        #Get the average radius of the piece, which will be used to focusTarget on the piece accurately
        totalRadius = 0
        i = 0
        searchTolerance = 0.7  #It will search for the circle nearest to the center and find its average radius. This search tolerance will widen each time it doesn't find the target.
        print 'pickUpPiece():\t Getting average radius of circle target. Starting searchTolerance: ', searchTolerance, ' Starting radius: ', avgRadius

        focusCamera()
        while i < s['avgSampleSize']:

            getAllPieces = lambda: objTracker.getCircles(minRadius=avgRadius * searchTolerance, maxRadius=avgRadius / searchTolerance)

            try:
                newRadius = objTracker.bruteGetFrame(lambda: [objTracker.sortShapesByDistance(getAllPieces(), returnNearest=True).radius], maxAttempts=5)[0]
                totalRadius +=  newRadius
                #print 'avgRadius right now', newRadius

            except NameError as e:
                #Loosen the searchTolerance and try again
                print 'pickUpPiece():\t Could not find circle. Broadening search.. Curr. iteration: ', i, ' Curr. avgRadius: ', totalRadius / (i + 1), 'Curr. searchTolerance: ', searchTolerance
                i -= 1
                searchTolerance *= .9

            #WAIT FOR NEW FRAME FOR THE NEXT SAMPLE
            lastFrame = vid.frameCount
            while lastFrame == vid.frameCount: pass
            i += 1

        avgRadius = totalRadius / s['avgSampleSize']
        averageArea = avgRadius
        print 'pickUpPiece():\t Updated avgRadius: ', avgRadius


        #Set up the function for finding the checkerpiece for the focusOnTarget function
        getAllPiecesAccurate = lambda: objTracker.getCircles(minRadius=avgRadius * .8, maxRadius=avgRadius / .8)
        getNearestPiece      = lambda: objTracker.bruteGetFrame(lambda: objTracker.sortShapesByDistance(getAllPiecesAccurate(), returnNearest=True).center, maxAttempts=100)
        #Focus on the target for this setting, then record the final position on focusPos
        focusOnTarget(getNearestPiece, tolerance=s['focusTolerance'], targetSamples = s['targetSamples'])#, ppX = ppXYInfo['ppX'] * 2.5)
        focusPos.append(Robot.getPosArgsCopy(onlyRecord=['height', 'rotation', 'stretch']))




    lastSeenPos       = Robot.getPosArgsCopy()
    pickupHeight      = groundHeightFormula(Robot.pos['stretch']) - 5  #The plus 2 makes it so the sucker isn't firmly pressed against the ground/piece, but more lightly so.

    print 'pickupHeight = ', pickupHeight
    stretchPerHeight  = (focusPos[0]['stretch']   - focusPos[-1]['stretch'])  / (focusPos[0]['height']  - focusPos[-1]['height'])
    rotationPerHeight = (focusPos[0]['rotation']  - focusPos[-1]['rotation']) / (focusPos[0]['height']  - focusPos[-1]['height'])
    stretchAdjust     = (Robot.pos['height'] - pickupHeight) * stretchPerHeight
    rotationAdjust    = (Robot.pos['height'] - pickupHeight) * rotationPerHeight

    #NOW THAT CAMERA IS CENTERED ON OBJECT, JUMP OVER IT AND MOVE DOWN
    print 'stretchBefore: ',  focusPos[0]['stretch'], '\tstretchAfter: ', focusPos[-1]['stretch'],  '\tstretchPerHeight: ', stretchPerHeight
    print '     rhBefore: ', focusPos[0]['rotation'], '\t      rAfter: ', focusPos[-1]['rotation'], '\t      rPerHeight: ', rotationPerHeight


    stretchFromSucker = jumpStretchFormula(pickupHeight)
    print 'Moving an adjuststretch of: ', stretchAdjust, 'Moving an adjustRotate of: ', rotationAdjust, 'Moving a stretchFromSucker of: ', stretchFromSucker
    Robot.moveTo(stretch=stretchFromSucker, rotation=rotationAdjust)

    sleep(.1)
    Robot.moveTo(height=pickupHeight, relative=False)


    #PICK UP THE PIECE
    pickupLocation = Robot.getPosArgsCopy(onlyRecord=['rotation', 'stretch'])
    #x = raw_input('Press Enter to continue')
    Robot.setGrabber(True)
    sleep(.5)


    #CHECK TO SEE IF THE PIECE HAS BEEN PICKED UP BY SEEING IF THERE ARE ANY CIRCLES WHERE THE PIECE USED TO BE
    Robot.moveTo(height=20)
    sleep(.1)
    Robot.moveTo(relative=False, **lastSeenPos)
    sleep(.1)

    getAllPiecesAccurate = lambda: objTracker.getCircles(minRadius=avgRadius * .8, maxRadius=avgRadius / .8)
    getNearestPiece      = lambda: objTracker.bruteGetFrame(lambda: objTracker.sortShapesByDistance(getAllPiecesAccurate(), returnNearest=True).center, maxAttempts=10)
    try:  #See if there is a piece there
        getNearestPiece()
        print 'pickUpPiece():\t ERROR: Failed to pick up piece'
    except NameError as e:  #If no piece is found, an error is thrown- meaning that the robot has successfully found the piece
        print 'pickUpPiece():\t Successfully picked up piece'

def placePiece(coords, cornerInfo, groundHeightFormula, jumpStretchFormula):

    location                        = getSquarePosition(coords[0], coords[1], cornerInfo['corners'])
    location['height']              = cornerInfo['height']
    location['stretchDistFromBase'] = cornerInfo['distFromBase']

    dropRotation, dropStretch = Robot.convertToPolar(location['x'], location['y'], location['stretchDistFromBase'])

    #DROP PIECE IN CORRECT LOCATION
    dropoffHeight = groundHeightFormula(dropStretch) + 15
    jumpStretch   = jumpStretchFormula(dropoffHeight)

    print 'dropoffHeight: ', dropoffHeight, ' jumpstretch: ', jumpStretch
    Robot.moveTo(height=0, relative=False)
    sleep(.1)
    Robot.moveTo(relative=False, **location)
    Robot.moveTo(stretch=jumpStretch)
    sleep(.5)

    Robot.moveTo(height = (dropoffHeight * 3) / 5)
    sleep(.2)
    Robot.moveTo(height = (dropoffHeight * 1) / 5)
    sleep(.2)
    Robot.moveTo(height = (dropoffHeight * 1) / 5)
    sleep(.2)
    Robot.setGrabber(0)
    Robot.moveTo(height = 5)
    sleep(.1)
    Robot.moveTo(height = 10)
    sleep(.1)
    Robot.moveTo(height = 15)
    sleep(.1)


#   #CALIBRATION FUNCTIONS
def getBoardCorners():
    """
        Get the robots cartesian locations centered on each corner of the board in this format:
    cornerInfo = [{'corners': [{'y': -33.77319218164843,  'x': 173.74801147023652}, {'y': 120.71486133425334, 'x': 138.86656276099006}, {'y': 154.45614415655808, 'x': 290.489758050587},   {'y': 16.956849822713803, 'x': 323.5559692604819}],  'distFromBase': 144, 'height': 100},
                  {'corners': [{'y': -33.77319218164843,  'x': 173.74801147023652}, {'y': 114.53631117107041, 'x': 141.4405649851687},  {'y': 153.51720103098629, 'x': 288.72386286486915}, {'y':               -0.0, 'x': 324.0}],              'distFromBase': 158, 'height': 40},
                  {'corners': [{'y': -35.87209113079042,  'x': 184.5459104881608},  {'y': 124.05800866950207, 'x': 147.84657752196276}, {'y': 156.62672241014363, 'x': 307.3972508449869},  {'y': 5.9512705951136775, 'x': 340.9480640483294}],  'distFromBase': 181, 'height': 8},
                  {'corners': [{'y': -37.207754098426236, 'x': 191.41730077229448}, {'y': 129.2003095469944,  'x': 153.9749330669146},  {'y': 162.98258940649728, 'x': 319.87134218362405}, {'y': 6.195604285235647,  'x': 354.9459317805189}],  'distFromBase': 195, 'height': -4},
                  {'corners': [{'y': -36.062900126166966, 'x': 185.52753767160848}, {'y': 125.34358388887516, 'x': 149.3786664082007},  {'y': 163.37610384949,    'x': 307.26576231490657}, {'y': 6.055985033737379,  'x': 346.94715021926777}], 'distFromBase': 189, 'height': -13}]


        This function allows the robot to find the corners of the board by looking for the tiny square markers.
        It first finds the bottom right corner, where it looks for 4 squares of similar sizes. Now that it knows
        the approximate size of the squares, it is able to find the rest of the corners with ease, by looking for
        squares of the same shape.
    :param vid:
    :return:
    """

    global streamVideo
    streamVideo = True


    #This defines the area where the robot will look for corners of the board. TODO: move these constants somewhere in the main program, or prompt user for them
    ## It will then find the marker and refine that to an exact location.
    searchPositions = [{'stretch':  29, 'rotation':  13},
                       {'stretch':  32, 'rotation': -37},
                       {'stretch': 176, 'rotation': -26},
                       {'stretch': 173, 'rotation':   0}]


    #This defines the settings the robot should use when targeting the markers at different heights.
    setting = [{'height': 100, 'tolerance': 7},
               {'height':  37, 'tolerance': 6},
               {'height':  5, 'tolerance':  5},
               {'height':  -6, 'tolerance': 5},
               {'height': -15, 'tolerance': 4}]

    tolerance       = 0.3                       #Find 4 shapes (a marker) that are [tolerance]% different
    cornerPositions = [{'corners': [], 'height': 0, 'distFromBase':0} for i in range(0, len(setting))]  #Corner positions at each height. There are 4 heights, thus 4 sets of 4 corners.
    cornerPosPolar  = [{'corners': [], 'height': 0, 'distFromBase':0} for i in range(0, len(setting))]
    ppXY            = [{'height': 0, 'ppX': 0, 'ppY': 0, 'xSamples': 0, 'ySamples': 0}              for i in range(0, len(setting))]  #Pixels per 'X' movement. This is a parameter for focusOnTarget that increases speed.



    #GET THE POSITION OF EACH CORNER AT EACH HEIGHT, AND FILL OUT cornerPosPolar
    for index, position in enumerate(searchPositions):  #For each corner
        Robot.moveTo(relative = False, **searchPositions[index])
        sleep(.25)


        for i, s in enumerate(setting):  #For each height find the marker, focus on it, and record the position of the corners
            Robot.moveTo(height=s['height'], relative=False, waitForRobot=True)

            #WAIT FOR CAMERA TO FOCUS
            focusCamera()

            #Find the marker and set up a function for finding it
            markerArea = getMarkerPerimeter(tolerance)
            markerCoordinate = lambda: getMarker(markerArea, tolerance)

            #For calculating the ppX and ppY, you have to record the position of the robot and the
            #position of the target on camera before and after the manuver
            posBefore    = Robot.getPosArgsCopy(onlyRecord=['rotation', 'stretch'])
            coordsBefore = markerCoordinate()

            #Actually focus on the marker
            focusOnTarget(markerCoordinate, tolerance=s['tolerance'])


            #DO CALCULATIONS FOR PPX AND PPY
            posAfter = Robot.getPosArgsCopy(onlyRecord=['rotation', 'stretch'])
            coordsAfter = markerCoordinate()
            rotDifference     = (posAfter['rotation'] - posBefore['rotation'])
            strDifference     = (posAfter['stretch']  - posBefore['stretch'])
            xDifference       = float((coordsAfter[1] - coordsBefore[1]))
            yDifference       = float((coordsAfter[0] - coordsBefore[0]))
            #print 'rotD', rotDifference, 'strD', strDifference, 'xD', xDifference, 'yD', yDifference
            if not strDifference == 0 and not xDifference == 0: #This ensures that only good samples are considered
                ppXY[i]['ppX'] += (xDifference / strDifference)
                ppXY[i]['xSamples'] += 1
            if not rotDifference == 0 and not yDifference == 0:
                ppXY[i]['ppY'] += (yDifference / rotDifference)
                ppXY[i]['ySamples'] += 1

            ppXY[i]['height'] = s['height']
            #print 'ppXY so far: ', ppXY


            #RECORD THE CORNER POSITION
            cornerPosPolar[i]['height'] = s['height']
            cornerPosPolar[i]['corners'].append(Robot.getPosArgsCopy(onlyRecord=['rotation', 'stretch']))



    #CONVERT CORNERPOSPOLAR TO CARTESIAN BY FILLING OUT CORNERPOSITIONS AND AVERAGE PPXY
    for index, height in enumerate(cornerPosPolar):
        cornerPositions[index]['height']       = cornerPosPolar[index]['height']
        cornerPositions[index]['distFromBase'] = getStretchFromBase(cornerPosPolar[index]['corners'])

        #AVERAGE THE PPX AND PPY VALUES
        if not ppXY[index]['xSamples'] == 0:
            ppXY[index]['ppX'] /= ppXY[index]['xSamples']

            #If there wasn't enough samples, make it -1 so focusOnTarget will ignore the value
            if ppXY[index]['xSamples'] < 2:
                ppXY[index]['ppX'] = -1

        if not ppXY[index]['ySamples'] == 0:
            ppXY[index]['ppY'] /= ppXY[index]['ySamples']

            if ppXY[index]['ySamples'] < 2:
                ppXY[index]['ppY'] = -1

        #CONVERT ALL THE CORNERPOSPOLAR TO CARTESIAN
        for i, corner in enumerate(cornerPosPolar[index]['corners']):
            cartesian = Robot.convertToCartesian(corner['rotation'], corner['stretch'], cornerPositions[index]['distFromBase'])
            cartesianDictionary = {'x': cartesian[0], 'y': cartesian[1]}
            cornerPositions[index]['corners'].append(cartesianDictionary)


    print 'getBoardCorners():\t ppXY: ', ppXY
    print 'getBoardCorners():\t Polar Corners: ', cornerPosPolar
    print 'getBoardCorners():\t Corners: ', cornerPositions

    return ppXY, cornerPositions

def getAvgColor(circleArray):
    """
    The pieces on the board are determined to be one side or another by their color. Since color can be be read differently
    in different lightings, this function can be used to calibrate at the start of the game.

    What it does is it takes the average color of each circle and returns it. This is then used to find the "midpoint"
    for determining if one piece is from player A or player B. It must only be run when there is an equal number
    of each type of piece on the board, or it will skew the results.
    """
    avgColor = [0, 0, 0]
    for circle in circleArray:
        hsv = objTracker.bgr2hsv(circle.color)  #Convert form bgr to hsv
        avgColor = [avgColor[0] + hsv[0],
                    avgColor[1] + hsv[1],
                    avgColor[2] + hsv[2]]
    avgColor = [avgColor[0] / len(circleArray), avgColor[1] / len(circleArray), avgColor[2] / len(circleArray)]
    print 'getAvgColor():\t ', avgColor
    return avgColor

def getMotionAndBlur(**kwargs):
    """
    Get a sample of frames and analyze them for the average Motion and the average blur in the image
    :return:
    """

    global blurThreshold
    sample    = kwargs.get('sample', 50)
    avgMotion = 0
    avgBlur   = 0

    print 'getMotionAndBlur():\tGetting average motion and average blur. ', sample, 'samples.'


    #MOVE TO POSITION
    Robot.moveTo(relative=False, **Robot.home)
    Robot.moveTo(height = -15, relative=False)
    sleep(2)

    focusCamera(threshold=230)

    #READ -SAMPLE- FRAMES AND GET THE AVERAGE, THEN RETURN IT
    for s in range(0, sample):
        avgMotion += objTracker.getMovement()
        avgBlur   += objTracker.getBlur()
        #Get new frame
        lastFrame = vid.frameCount
        while lastFrame == vid.frameCount: pass

    avgMotion /= sample
    avgBlur   /= sample

    print 'getMotionAndBlur():\tAvgMotion: ', avgMotion, 'AvgBlur: ', avgBlur
    return avgMotion, avgBlur

def getHighestSTD(circleArray, boardFrame):
    """
    To determine whether a piece on the board is a king or a normal piece, I used the standard deviation of the colors of the piece.
    This is because the kings are marked with a big black "K" on the center of the piece, which would make the standard
    deviation of the colors go up radically.

    By getting the average std at the start of a game of all the pieces (that are, obviously, not kings yet) I can use it as a
    threshold to identify which pieces are indeed kings later in the game.
    """
    avgStd = 0
    highest = 0
    for i, circle in enumerate(circleArray):
        std = getCircleSTD(circle, boardFrame)
        if std > highest:
            highest = std
        avgStd +=  std

    avgStd /= len(circleArray)
    #print 'highestSTD: ', highest
    #print 'avgSTD: ', avgStd
    return highest

def getGroundFormula(cornersLow):
    """
    Move the robot to the bottom of the board and move down until the robots touch sensor triggers
    and then record that spot. Do the same for the top of the board. Use this information to calculate
    the "height" of the ground anywhere along the board, to be used when picking up pieces.

    The function returns another lambda function, which has one parameter: stretch, and returns one parameter: height
    :return:
    """
    groundHeight = {'bottom': {'stretch': 0, 'height': 0}, 'top': {'stretch': 0, 'height': 0}}  #Ground height at the bottom and top of the board

    #Location of the top middle of the board and the bottom middle of the board
    heightPositions = [getSquarePosition(2.5, 5.5, cornersLow),
                       getSquarePosition(2.5, -.5, cornersLow)]

    Robot.moveTo(relative=False, height=0, **heightPositions[0])
    sleep(.2)
    while Robot.pos['height'] > -45 and Robot.getOutput('touch')['touch']:
        Robot.moveTo(height = -5)
        sleep(.2)
    groundHeight['bottom']['stretch'] = Robot.pos['stretch']
    groundHeight['bottom']['height']  = Robot.pos['height']




    Robot.moveTo(height=0, relative = False)
    sleep(.1)
    Robot.moveTo(relative=False, **heightPositions[1])
    sleep(.1)
    while Robot.pos['height'] > -75 and Robot.getOutput('touch')['touch']:
        Robot.moveTo(height = -7.5)
        sleep(.2)

    groundHeight['top']['stretch'] = Robot.pos['stretch']
    groundHeight['top']['height']  = Robot.pos['height']

    Robot.moveTo(height=0, relative=False)
    sleep(.1)
    Robot.moveTo(stretch = 0, relative=False)
    sleep(.5)

    slope = (groundHeight['top']['height']  - groundHeight['bottom']['height']) / \
            (groundHeight['top']['stretch'] - groundHeight['bottom']['stretch'])

    intercept = groundHeight['bottom']['height'] - slope * groundHeight['bottom']['stretch']

    print 'getGroundFormula():\t GroundHeight: ', groundHeight
    print 'getGroundFormula():\t Final formula:  lambda stretch:', slope, ' * stretch +', intercept
    return lambda stretch: slope * stretch + intercept

def getStretchFromBase(polarCorners):
    """
    The purpose of this function is difficult to explain, but I'll give it a try. A problem I ran into with cartesian coordinates was that the uArm's 0 stretch point
    was not exactly 0 distance from the pivot of the robot. To find the exact distance in "stretch" units, I modified the Robot.convertCartesian functions to use a
    distFromBase and add that on. However, this distance from the base must be found- and even worse, its different at different heights!!!

    How to fix this? You use the checker board corners. We know the corners at various heights, in 'stretch, rotation' form. We know that the checkerboard is
    completely square, thus the cartesian coordinates must reflect this fact. By testing many values (0 to 250) of possible distFromBase and comparing how
    'square' the cartesian coordinates are, you can find the optimal distFromBase.

    This function returns this optimal distFromBase for any set of corners at a certain height.

    polarCorners should be in this format:
        polarCorners = [{'stretch':  0, 'rotation': 12}, {'stretch':  6, 'rotation': -39}, {'stretch': 157, 'rotation': -27}, {'stretch': 157, 'rotation': 1}]

        The values will be different, of course.
    """

    #polarCorners = [{'stretch':  0, 'rotation': 12}, {'stretch':  6, 'rotation': -39}, {'stretch': 157, 'rotation': -27}, {'stretch': 157, 'rotation': 1}]

                    #[{'stretch':  0, 'rotation': 12}, {'stretch':  6, 'rotation': -39}, {'stretch': 157, 'rotation': -27}, {'stretch': 157, 'rotation': 1}]

    #GET [rotation,stretch] FORMAT COORDINATES FOR EACH CORNER OF THE CHECKERBOARD
    bR = [float(polarCorners[0]['rotation']), float(polarCorners[0]['stretch'])]
    bL = [float(polarCorners[1]['rotation']), float(polarCorners[1]['stretch'])]
    tR = [float(polarCorners[3]['rotation']), float(polarCorners[3]['stretch'])]
    tL = [float(polarCorners[2]['rotation']), float(polarCorners[2]['stretch'])]

    bestDist = 0      #Best value of testDist so far
    bestDev  = 10000  #Lowest standard deviation so far
    step     = .1     #How accurate you want to be

    for testDist in range(0, int(250 / step)):  #Try each stretch value from 0 to 200 to see which one will make each side equal to eachother in polar coordinates

        bRCart = list(Robot.convertToCartesian(bR[0], bR[1], testDist * step))
        bLCart = list(Robot.convertToCartesian(bL[0], bL[1], testDist * step))
        tRCart = list(Robot.convertToCartesian(tR[0], tR[1], testDist * step))
        tLCart = list(Robot.convertToCartesian(tL[0], tL[1], testDist * step))

        bRbL = dist(bRCart, bLCart)
        bLtL = dist(bLCart, tLCart)
        tLtR = dist(tLCart, tRCart)
        tRbR = dist(tRCart, bRCart)

        stDev = np.std([bRbL, bLtL, tLtR, tRbR], axis=0)

        if stDev < bestDev:
            bestDev  = stDev
            bestDist = testDist * step
            #print 'Distances of each side with testDist of ', testDist, ' : ', bRbL, bLtL, tLtR, tRbR, 'stDev: ', stDev

    return bestDist

def getJumpFormula(allCornerInfo):
    """
    This function returns a function that when height is plugged into it, it will return how far the camera is from the
    sucker of the robot in 'stretch' units.

    TThis function can be used as such:

        stretchJumpFormula = getJumpFormula(allCornerInfo)
        jumpStretch = stretchJumpFormula(height)
        Robot.move(stretch = jumpStretch)

    The reason for this is that the amount the robot moves per unit of 'stretch' changes depending on the height of the robot.
    This function will help with that.

    :param allCornerInfo: The information given by getBoardCorners()
    :return:
    """

    global camDistFromGrabber
    global boardLength

    firstLastCornerInfo = [allCornerInfo[0], allCornerInfo[-1]]
    data = [[0, 0], [0, 0]]  #Will be filled out below, and has this information: [[height, stretch], [height2, stretch2]

    for i, cornerSet in enumerate(firstLastCornerInfo):
        #DETERMINE MATHEMATICALLY THE 'STRETCH' DIST BETWEEN THE CAMERA AND THE SUCKER
            #GET [x,y] FORMAT COORDINATES FOR EACH CORNER OF THE CHECKERBOARD
        corners = cornerSet['corners']
        bR = [float(corners[0]['x']), float(corners[0]['y'])]
        bL = [float(corners[1]['x']), float(corners[1]['y'])]
        tR = [float(corners[3]['x']), float(corners[3]['y'])]
        tL = [float(corners[2]['x']), float(corners[2]['y'])]
            #GET LENGTH OF EACH SIDE
        avgLen            = (dist(bR, bL) + dist(tR, tL) + dist(bR, tR) + dist(bL, tL)) / 4
        stretchPerInch    = avgLen / boardLength
        stretchFromSucker = stretchPerInch * camDistFromGrabber
        data[i] = [cornerSet['height'], stretchFromSucker]

    slope     = (data[0][1] - data[1][1]) / (data[0][0] - data[1][0])
    intercept = data[1][1] - slope * data[1][0]


    print 'getJumpFormula():\tFinal formula:  lambda height:', slope, ' * height +', intercept

    #return lambda height: height * slope + intercept
    return lambda height: data[1][1]

def getCircleSTD(circle, frame):
    """
    Used in getHighestStd and getBoardState, this will help assist in telling "King" Pieces apart from normal ones.

    It returns the average standard deviation of the colors.
    """
    analyzeFrame = frame.copy()
    fromX = int(circle.center[0] - circle.radius / 2)
    toX   = int(circle.center[0] + circle.radius / 2)
    fromY = int(circle.center[1] - circle.radius / 2)
    toY   = int(circle.center[1] + circle.radius / 2)

    circleSample = analyzeFrame[fromY:toY, fromX:toX]

    #cnts, edged = objTracker.drawEdged(frameToAnalyze=circleSample, returnContours=True, contourMethod=cv2.RETR_LIST)
    #cv2.imshow('main', circleSample)
    #cv2.waitKey(1000)
    std = cv2.meanStdDev(circleSample)[1]
    avgStd = (std[0] + std[1] + std[2]) / 3  #Add the average std of all colors to the total average
    #print 'avgStd: ', avgStd
    return avgStd[0]



#   #OTHER
def getMarkerPerimeter(tolerance, **kwargs):
    """
    This function searches for 4 nearby squares that are of similar size.
    There are 4 squares at each corner, and they represent "markers".
    The key to identifying a marker is knowing the pixel area that it takes up, otherwise its
    possible to confuse the big checkerboard squares as markers, despite how much bigger they are.
    This function will find the smalles 4 similar squares and return their average area.
    :return:
    """
    #compareRange = kwargs.get('compareRange', True)
    accuracyAttempts  = kwargs.get('accuracyAttempts', 50)
    attempts = 0

    #print "CompareRange: ", compareRange
    #  TODO: Make sure that if it doesn't see 4 small blocks, that it doesn't confuse the big ones as the markers

    avgPerimeter    = 0    #The average pixel area of the markers.
    similarShapeSets = []  #Records sets of 4 shapes that are similar in size, later to be whittled down more.

    while avgPerimeter == 0:
        shapeArray = objTracker.getShapes(4, minArea = 500, maxArea = (vid.frame.shape[0] * vid.frame.shape[1]) / 3)[::-1]
        shapeArray = sorted(shapeArray, key = lambda s: s.perimeter)
        shapeArrayCopy = shapeArray[:]

        vid.windowFrame['Perspective'] = objTracker.drawShapes(shapeArray, color=(0, 0, 255))
        cv2.waitKey(1)

        for shapeIndex, shape in enumerate(shapeArray):
            shapeArrayCompare = shapeArray[:shapeIndex] + shapeArray[(shapeIndex + 1):]  #Get shapeArray without the current shape being analyzed
            similarShapes     = [shape]
            for compareIndex, shapeToCompare in enumerate(shapeArrayCompare):
                if shape.perimeter - shape.perimeter * tolerance < shapeToCompare.perimeter < shape.perimeter + shape.perimeter * tolerance:
                    similarShapes.append(shapeToCompare)


            if len(similarShapes) >= 4:  #If more than 4 shapes have been found of similar size
                similarShapeSets.append(similarShapes)


        if len(similarShapeSets) >= 1:
            similarShapeSets = sorted(similarShapeSets, key = lambda ss: sum(ss[i].perimeter for i in range(len(ss))) / len(ss))  #Sort by perimeter smallest to largest

            sizeRange        = shapeArray[-1].perimeter / (sum(similarShapeSets[0][i].perimeter for i in range(len(similarShapeSets[0]))) / len(similarShapeSets[-1]))  #How much smaller the last similarShapeSet is compared to the first one

            #print 'shapeArray: ', shapeArray, '\n'
            #print 'similarShapeSets Sorted', similarShapeSets,
            #print 'Difference between areas: ', sizeRange, '\n'

            if len(similarShapeSets[0]) >= 4 and (sizeRange > 1.5 or attempts > accuracyAttempts):  #if have passed accuracyAttempts, stop trying to compare the size
                avgPerimeter = sum([s.perimeter for i, s in enumerate(similarShapeSets[0])]) / len(similarShapeSets[0])
                print 'getMarkerPerimeter():\t avgPerimeter of markers found to be: ', avgPerimeter, ' sizeRange: ', sizeRange

        if avgPerimeter == 0:  #If the 4 markers were never identified
            #print 'getMarkerPerimeter():\t ERROR: Marker not found! Trying again...'
            #WAIT FOR NEW FRAME
            lastFrame = vid.frameCount
            while lastFrame == vid.frameCount:
                pass

        attempts += 1

    return avgPerimeter

def getMarker(avgPerimeter, tolerance, **kwargs):


    maxAttempts = kwargs.get('maxAttempts', 1000)

    squaresInMarker = 4  #The camera must detect exactly 4 squares of the same size to consider it to be a marker
    attempts = 0

    shapes = []
    while attempts <= maxAttempts:  #Find at least 4 squares of the correct shape and size

        shapes = objTracker.getShapes(4, minPerimeter = avgPerimeter - avgPerimeter * tolerance * 2, maxPerimeter = avgPerimeter + avgPerimeter * tolerance * 2)

        shapes = objTracker.sortShapesByDistance(shapes)[:4]

        markerCentroid = tuple(objTracker.getShapesCentroid(shapes))

        #shapes = objTracker.getShapes(4, minArea = avgArea - avgArea * tolerance * 2, maxArea = avgArea + avgArea * tolerance * 2)
        attempts += 1

        #IF NOT SUCCESSFULL, PULL ANOTHER FRAME
        if len(shapes) < squaresInMarker:

            if attempts != maxAttempts:
                lastFrame = vid.frameCount
                while lastFrame == vid.frameCount:
                    pass
            else:
                print 'getMarker:() ERROR: ATTEMPTS OVER ', maxAttempts, ' AT HEIGHT', Robot.pos['height']
                raise NameError('ObjNotFound')
        else:
            break  #IF it found the marker, leave the loop

    #Shorten the list to the squares closest to center screen (Most likely to be relevant markers)
    shapes = objTracker.sortShapesByDistance(shapes)[:4]
    vid.windowFrame['Perspective'] = objTracker.drawShapes(shapes)
    cv2.waitKey(1)
    markerCentroid = tuple(objTracker.getShapesCentroid(shapes))

    if len(markerCentroid) == 0:
        print 'getMarker:():\t ERROR: No marker centroid detected'
        raise NameError('ObjNotFound')

    return markerCentroid

def dist(p1, p2):
    #Return the distance between two points of format p1 = [x,y] and p2 = [x,y]
    return ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2) ** .5





########### MAIN THREADS ###########
def runRobot():
    #SET UP VARIABLES AND RESET ROBOT POSITION
    print 'runRobot():\t Setting up Robot Thread....'
    #global exitApp
    global keyPressed  #Is set in the main function, because CV2 can only read keypresses in the main function. Is a character.

    Robot.moveTo(relative = False, waitForRobot = True, **Robot.home)
    Robot.setGrabber(0)

    playCheckers()

    #MAIN ROBOT FUNCTION
    while not exitApp:

        if keyPressed == 'h':  #HELP COMMAND
            print 'Help: \n x: MOVETOXY'


        if keyPressed == 'x':  #MOVE TO XY
            #Robot.moveTo(height = float(raw_input('Height?:')), rotation = float(raw_input('Rotation?:')), stretch = float(raw_input('Stretch:')), relative = False)
            #Robot.moveTo(height = 150, rotation = float(raw_input('Rotation?:')), stretch = float(raw_input('Stretch:')), relative = False)
            #Robot.moveTo(height = 150, stretch = float(raw_input('Stretch:')), relative = False)
            #Robot.moveTo(x=float(raw_input('X?: ')), y=float(raw_input('Y?: ')), relative=False)
            Robot.moveTo(stretch=float(raw_input('Stretch?:')))
            #Robot.moveTo(height=float(raw_input('height?:')), relative=False)

        if keyPressed == 'p':  #PLAY CHECKERS
            playCheckers()

        if keyPressed == 'c':  #PLAY CHECKERS
            cornerInfo = [{'corners': [{'y': -40.972018918482874, 'x': 184.8128341478034},  {'y': 114.52539890583479, 'x': 151.98033756199985}, {'y': 150.0544435459012,  'x': 307.6572020482049},  {'y': -8.934192457477108, 'x': 341.1830450141577}], 'distFromBase': 158.3,  'height': 100},
                     {'corners': [{'y': -37.112236810970046, 'x': 174.5993467309843},  {'y': 109.14998136887112, 'x': 147.50773392325937}, {'y': 147.77390766522245, 'x': 290.02262362331373}, {'y': -8.572950570828457, 'x': 327.387773929495}],   'distFromBase': 162.5, 'height':  37},
                     {'corners': [{'y': -46.42989761657374,  'x': 201.10998137167255}, {'y': 121.99579037334762, 'x': 158.98800939436353}, {'y': 154.00209457831087, 'x': 330.25855759615524}, {'y': -0.0, 'x': 363.4}],                            'distFromBase': 198.4, 'height':   5},
                     {'corners': [{'y': -36.10085759999442,  'x': 194.78279718841944}, {'y': 123.32014951791244, 'x': 155.03467587246323}, {'y': 152.15862505048878, 'x': 311.9714134704409},  {'y': 3.1075192909709584, 'x': 356.08644080315145}], 'distFromBase': 191.1, 'height':  -6},
                     {'corners': [{'y': -40.73086900143339,  'x': 200.1986171540355},  {'y': 117.35853582603964, 'x': 158.600958599777},   {'y': 154.87652616058105, 'x': 317.5439365574957},  {'y': 3.100538062572259,  'x': 355.2864712647001}],  'distFromBase': 197.3, 'height': -15}]
            corners = cornerInfo[-1]

            sqrPos  =  getSquarePosition(int(raw_input('Column?')), int(raw_input('Row?')), corners['corners'])
            Robot.moveTo(relative=False, height=corners['height'], stretchDistFromBase=corners['distFromBase'], **sqrPos)

if '__main__' == __name__:
    print 'Start!'
    #SET UP VIDEO CLASS AND WINDOWS VARIABLES
    vid = Vision.Video()
    vid.createNewWindow('Main',             xPos = 0,   yPos = 10)
    vid.createNewWindow('Perspective',      xPos = 1020, yPos = 10)
    sleep(3)
    vid.getVideo()      #Get the first few frames
    vid.setCamResolution(1000, 1000)  #Sets the resolution as high as the camera allows
    #vid.setCamResolution(1000, 1000)  #Sets the resolution as high as the camera allows

    #SETUP UP OTHER VARIABLES/CLASSES
    objTracker          = Vision.ObjectTracker(vid, rectSelectorWindow = 'KeyPoints')
    screenDimensions    = vid.getDimensions()
    keyPressed          = ''   #Keeps track of the latest key pressed

    global averageArea  #TODO: DELETE NOW
    averageArea = 1000

    global exitApp
    global streamVideo         #RobotThread communicates using this. It tells main thread to stream video onto window or to hold on a particular frame.
    global camDistFromGrabber
    global boardLength
    global boardSize


    camDistFromGrabber = 1.4   #(inches) Horizontal inches from the camera to the sucker of the robot. Used later for picking up checker pieces  #TODO: put in setup somewhere
    boardLength        = 6.5   #(inches) Side length of board in inches
    boardSize          = 6     #Squares per side of board

    exitApp            = False
    streamVideo        = True  #If true, then the camera will stream video. If not, then the camera will wait for new frames to be called for from the runCheckers() thread


    #START SEPERATE THREAD FOR MOVING ROBOT
    robotThread = Thread(target = runRobot)
    robotThread.start()


    #DISPLAY VIDEO/IMAGE REC. MAIN THREAD.
    while not exitApp:
        vid.getVideo()


        #DETECT IF CAMERA HAS BEEN UNPLUGGED, AND IF SO TRY TO RECONNECT EVERYTHING:
        #if objTracker.getMovement() == 0:
        #    print 'ERROR: __main__(XXX): Camera NOT detected.'
        #    sleep(1)
        #    print '__main(XXX)__: Attempting to reconnect...'
        #    vid.cap = cv2.VideoCapture(1)

        if streamVideo:
            markedUpFrame = vid.frame.copy()
            if True:
                pass
                getAllPieces    = lambda: objTracker.getCircles(minRadius = averageArea * .7, maxRadius = averageArea / .7)
                getNearestPiece = lambda: [objTracker.sortShapesByDistance(getAllPieces(), returnNearest = True)]
                cv2.circle(markedUpFrame, (int(screenDimensions[0] / 2), int(screenDimensions[1] / 2)), 6, (0, 255, 0), 3, 255)  #Draw center of screen
                markedUpFrame = objTracker.drawCircles(getNearestPiece(), frameToDraw = markedUpFrame)


            if False:
                getAllSquares   = lambda: objTracker.getShapes(4)  #, minArea=averageArea * .8, maxArea=averageArea * (1 / .8), bilateralConstant=1)
                getNearestPiece = lambda: [objTracker.sortShapesByDistance(getAllSquares(), returnNearest=True, maxDist=300)]
                cv2.circle(markedUpFrame, (int(screenDimensions[0] / 2), int(screenDimensions[1] / 2)), 6, (0, 255, 0), 3, 255)  #Draw center of screen
                markedUpFrame = objTracker.drawShapes(getNearestPiece(), frameToDraw = markedUpFrame)
                #markedUpFrame = objTracker.drawShapes(getAllSquares(), frameToDraw=markedUpFrame)

            vid.windowFrame['Main'] = markedUpFrame





        #DISPLAY WHATEVER FRAME IS NEXT
        vid.display('Main')
        vid.display('Perspective')

        #RECORD KEYPRESSES AS A CHARACTER IN A STRING
        ch = cv2.waitKey(90)                                     #Wait between frames, and also check for keys pressed.
        keyPressed = chr(ch + (ch == -1) * 256).lower().strip()  #Convert ascii to character, and the (ch == -1)*256 is to fix a bug. Used mostly in runRobot() function
        if keyPressed == chr(27): exitApp = True                 #If escape has been pressed, close program
        if keyPressed == 'p':                                    #Pause and unpause when spacebar has been pressed
            vid.paused = not vid.paused
            print '__main(XXX)__: PAUSED: ', vid.paused


    #CLOSE EVERYTHING CORRECTLY
    robotThread.join(1)  #Ends the robot thread, waits 1 second to do so.
    Robot.setGrabber(1)
    cv2.destroyWindow('window')


print 'End!'