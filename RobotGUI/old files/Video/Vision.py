__author__ = 'AlexThiel'
import math
import numpy as np
import Common
import cv2
from cv2 import cv
from collections import namedtuple

#Constants
FLANN_INDEX_LSH    = 6
flann_params = dict(algorithm         = FLANN_INDEX_LSH,
                    table_number      = 6,
                    key_size          = 12,
                    multi_probe_level = 1)
"""
  image     - image to track`
  rect      - tracked rectangle (x1, y1, x2, y2)`
  keypoints - keypoints detected inside rect`
  descrs    - their descriptors`
  data      - some user-provided data`
"""
PlanarTarget = namedtuple('PlaneTarget', 'image, rect, keypoints, descrs, data')
"""
  target - reference to PlanarTarget`
  p0     - matched points coords in target image`
  p1     - matched points coords in input frame`
  H      - homography matrix from p0 to p1`
  quad   - target boundary quad in input frame`
"""
TrackedTarget = namedtuple('TrackedTarget', 'target, p0, p1, H, quad')
"""
    Shape array: Holds information for the shapes found in a screen at a particular frame
    quad - target boundary quad (4 points deliniating the size of the object) [[x,y], [x,y], [x,y], [x,y]]
    center - center of the boundary quad [x,y]
"""
ShapeTarget   = namedtuple('ShapeTarget', 'vertices, area, center, perimeter')  #Any shape with x amount of sides

CircleTarget  = namedtuple('CircleTarget', 'radius, area, center, color')


class Video:  #Handles basic video functions

    def __init__(self, **kwargs):
        recordFrames = kwargs.get('recordFrames', 2)

        print "Video.__init():\tSetting up video capture..."
        self.cap = cv2.VideoCapture(1)
        self.frame = None
        self.previousFrames = []  #Useful for some object recognition purposes. Keeps only stock frames
        self.windowFrame = {}  #Has the frames for every window saved. Example: {"Main": mainFrame, "Edged": edgedFrame} These are added in createNewWindow()
        self.paused = False
        self.frameCount = 0  #This helps other functions test if there has been a new, processed frame yet. It counts up to 100 then stops

    def createNewWindow(self, name, **kwargs):
        """
        Args:
            name: the name of the window, in order to be accessed later.
            kwargs: "frame" (decides which frame to put on the window. Can be used for screenshots, or video)
                    "xPos"   The x position on the screen to create the window
                    "yPos"  The y position on the screen to create the window
        """
        #SET UP VARIABLES
        frameForWindow = kwargs.get("frame", self.frame)
        if frameForWindow is None:
            blankFrame = np.zeros((640, 480, 3), np.uint8)
            #self.getVideo()
            frameForWindow = blankFrame  #In case this is the first window opened, and no frames have been read yet.

        xPos = kwargs.get("xPos", 20)
        yPos = kwargs.get("yPos", 20)

        #CREATE AND SET UP WINDOW
        cv2.namedWindow(name)
        cv2.moveWindow(name, xPos, yPos)
        self.windowFrame[name] = frameForWindow[1]  #Add a frame for the window to show.

    def isCameraConnected(self):
        return self.cap.isOpened()

    def getVideo(self, **kwargs):
        returnFrame = kwargs.get('returnFrame', False)
        numberOfFrames = kwargs.get('readXFrames', 1)  #Read multiple frames in one go. These all get recorded on the previousFrames list
        if not self.paused:
            for i in range(numberOfFrames):
                ret, newFrame = self.cap.read()

                if ret:  #If there was no frame captured
                    try:  #CHECK IF CAP SENT AN IMAGE BACK. If not, this will throw an error, and the "frame" image will not be replaced
                        self.frame = newFrame.copy()                    #If it is indeed a frame, put it into self.frame, which all the programs use.
                        self.previousFrames.append(self.frame.copy())   #Add the frame to the cache of 10 frames in previousFrames
                    except:
                        print "ERROR: getVideo(XXX): Frame has no attribute copy."
                else:
                    print "getVideo():\tError while capturing frame. Attempting to reconnect..."
                    cv2.waitKey(1000)
                    self.cap = cv2.VideoCapture(1)
                    self.getVideo(**kwargs)
                    return

                #self.frame= cv2.Canny(self.frame,100,200)



        #HANDLE RECORDING OF FRAMES. RECORDS ONLY 10 OF THE PREVIOUS FRAMES
        while len(self.previousFrames) > 10:
            del self.previousFrames[0]

        if self.frameCount >= 100:  #Keeps the framecount to under 100
            self.frameCount = 0
        else:
            self.frameCount += 1

        if returnFrame:
            print "returning frame"
            return self.frame

    def setCamResolution(self, width, height):

        originalWidth  = self.cap.get(cv.CV_CAP_PROP_FRAME_WIDTH)
        originalHeight = self.cap.get(cv.CV_CAP_PROP_FRAME_HEIGHT)

        successWidth   = self.cap.set(cv.CV_CAP_PROP_FRAME_WIDTH,  width)
        successHeight  = self.cap.set(cv.CV_CAP_PROP_FRAME_HEIGHT, height)

        finalWidth     = self.cap.get(cv.CV_CAP_PROP_FRAME_WIDTH)
        finalHeight    = self.cap.get(cv.CV_CAP_PROP_FRAME_HEIGHT)

        if not successWidth or not successHeight:
            print "Video.setResolution():\tError in setting resolution using cap.set()"

        if not width == finalWidth or not height == finalHeight:
            print "Video.setResolution():\tError in setting resolution. Final width: ", finalWidth, " Final Height: ", finalHeight

    def resizeFrame(self, frameToResize, finalWidth):
        if frameToResize.shape[1] == finalWidth:
            return frameToResize
        r = finalWidth / float(frameToResize.shape[1])
        dim = (finalWidth, int(float(frameToResize.shape[0]) * r))
        resized = cv2.resize(frameToResize, dim, interpolation = cv2.INTER_AREA)
        return resized

    def display(self, window, **kwargs):
        """
        Args:
            window: The string name of the window to display the image
        KWARGS:
            "frame" : The frame to display. Defaults to the frame corrosponding to this window in the array self.windowFrame
        """

        cv2.imshow(window, self.windowFrame[window])

    def getDimensions(self):
        return [self.cap.get(3), self.cap.get(4)]



class ObjectTracker:

    def __init__(self, video, **kwargs):

        print "ObjTracker():\tSetting up objectTracker..."

        minMatchCount =  kwargs.get("minPointsToMatch", 10)       #Number of keypoints that must match for an object to be "recognized"
        trackingPoints = kwargs.get("pointsToTrack", 500)         #Number of keypoints to find per frame
        selectorWindow = kwargs.get("rectSelectorWindow", "Main")

        self.vid = video  #Passes the video class/window/webcam that the object tracker will be analyzing.
        self.tracker = PlaneTracker(minMatchCount, trackingPoints)  #Does all the tracking. The ObjectTracker class is simply to simplify things.
        self.keyPointsColor = (0, 255, 0)
        self.rectSel = Common.RectSelector(selectorWindow, self.onRect)

    def onRect(self, rect):
        self.tracker.addTarget(self.vid.frame, rect)
        print "onRect():\ttracker.targets: ", self.tracker.targets[len(self.tracker.targets) - 1]
        self.vid.paused = not self.vid.paused  #unpause video after drawing rectangle


    #DRAWING FUNCTIONS (GIVE FRAME, GET FRAME)
    def drawTargets(self, **kwargs):
        """
        Draws targets found through PlaneTracker, using a keyPoint algorithm
        :param kwargs:
            frameToDraw: defaults to self.vid.frame.copy, but allows you to draw over a different frame. (Useful if drawing over a frame with other drawings on it)
            frameToAnalyze: defaults to self.vid.frame.copy, but allows you to analyze an already-processed frame. Might be useful if you are inputting a grayscale frame.
        :return:
        """

        frameToDraw =    kwargs.get("frameToDraw",    self.vid.frame.copy())
        frameToAnalyze = kwargs.get("frameToAnalyze", self.vid.frame.copy())

        if not self.vid.paused:
            tracked = self.tracker.track(frameToAnalyze)
            for t in range(0, len(tracked)):
                currentTracked = tracked[t]
                centerXY = self.getTargetCenter(t)
                cv2.circle(frameToDraw, centerXY, 10, (0, 0, 255), -1)
                cv2.polylines(frameToDraw, [np.int32(currentTracked.quad)], True, (255, 255, 255), 2)
        self.rectSel.draw(frameToDraw)  #Draws rectangles when you click on the screen.
        if self.rectSel.dragging: self.vid.paused = True
        return frameToDraw

    def drawKeypoints(self, **kwargs):
        """
        Draws targets found through PlaneTracker, using a keyPoint algorithm
        :param kwargs:
            frameToDraw: defaults to self.vid.frame.copy, but allows you to draw over a different frame. (Useful if drawing over a frame with other drawings on it)
            frameToAnalyze: defaults to self.vid.frame.copy, but allows you to analyze an already-processed frame. Might be useful if you are inputting a grayscale frame.
        :return:
        """

        frameToDraw =    kwargs.get("frameToDraw",    self.vid.frame.copy())
        frameToAnalyze = kwargs.get("frameToAnalyze", self.vid.frame.copy())

        self.tracker.track(frameToAnalyze)
        keypoints = self.tracker.frame_points
        for kp in keypoints:
            x, y = kp.pt
            cv2.circle(frameToDraw, (int(x), int(y)), 3, (0, 0, 255), 2)
        return frameToDraw

    def drawEdged(self, **kwargs):
        """
        Gets the contours and draws them on the frame and returns the frame.
        :param bilateralConstant: Increases how well the image is blurred before analyzed for edges.
        :param kwargs:
        :return:
        """
        frameToAnalyze    = kwargs.get('frameToAnalyze',    self.vid.frame.copy())
        bilateralConstant = kwargs.get('bilateralConstant', 10)
        thresholdMethod  = kwargs.get('threshold',          cv2.THRESH_BINARY)
        returnContours    = kwargs.get('returnContours',    False)
        contourMethod     = kwargs.get('contourMethod',     cv2.RETR_EXTERNAL)  #RETR_EXTERNAL makes sure that only 'outmost' contours are counted

        gray = cv2.cvtColor(frameToAnalyze, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, bilateralConstant, bilateralConstant, 27)  #Blurs photo while maintaining edge integrity. Up the 2nd number for more lag but accuracy
        #self.vid.windowFrame["Main"] = gray
        ret, gray = cv2.threshold(gray, 115, 255, thresholdMethod)                  #Use a threshold on the image (black and white)
        edged = cv2.Canny(gray, 100, 130)                                           #Gets edged version of photo. 2nd and 3rd numbers are the thresholds (100,130 for optimal)
        cnts, _ = cv2.findContours(edged.copy(), contourMethod, cv2.CHAIN_APPROX_SIMPLE  )
        cv2.drawContours(edged, cnts, -1, (255, 255, 255), 3)

        if returnContours:
            return cnts, edged
        else:
            return edged

    def drawShapes(self, shapeTargets, **kwargs):  #RETURNS A FRAME WITH THE SHAPES DRAWN ON IT
        """
        Draws circles on every center of the shapes in the shapeArray

        frameToDraw: What frame to draw on top of.
        """

        frameToDraw = kwargs.get('frameToDraw', self.vid.frame.copy())
        color       = kwargs.get('color', (0, 255, 0))

        for shapeTarget in shapeTargets:
            if hasattr(shapeTarget, 'center'):
                cv2.circle(frameToDraw, tuple(shapeTarget.center), 10, (0, 0, 255), -1)
                cv2.polylines(frameToDraw, [np.asarray(shapeTarget.vertices)], True, color, 4)

        return frameToDraw

    def drawCircles(self, circleTargets, **kwargs):
        """

        :param circleTargets: a list of circleTargets should be sent in.
        :param kwargs:
        :return:
        """
        frameToDraw = kwargs.get('frameToDraw', self.vid.frame.copy())
        color       = kwargs.get('color', (0, 255, 0))

        for circle in circleTargets:
            if hasattr(circle, "center"):
                cv2.circle(frameToDraw, tuple(circle.center), circle.radius, color, 3, 3)  #Draw outline of circle
                #cv2.circle(frameToDraw, tuple(circle.center),             2, (0, 255, 0), 3, 2)  #Draw center of circle

        return frameToDraw



    #VISION FUNCTIONS
    def getShapes(self, sides, **kwargs):
        """
        WHAT IT DOES:   Finds all shapes that have 'sides' sides, and returns an array of the coordinates of these arrays.

        INPUT
        KWARGS:
        "bilateralConstant" :   (default 15), and increases how well the image is blurred before analyzed for edges.
        "returnFrame" :         (default: False) If true, the function will ONLY return an edged frame of the object, and stop halfway.
        "minArea"      :        (default: 600) This defines the minimum amount of pixels in a shape to be considered as a shape. (Stops small contours
                                    From being mistaken as shapes)

        OUTPUT:
        if returnFrame is true, then it will output: shapeArray, edgedFrame
        edgedFrame: the processed frame before contours are drawn and shapes are found.
        SHAPETARGET:
         shapeArray structure: (for a rectangle)
            shapeArray[0] returns 4 coordinates (points of a shape) of shape 0 out of len(shapeArray)
            shapeArray[0][0] would return the [x,y] of point 1 of shape 0 of the array of shapes.
            [
                [
                array([249, 229]),
                array([227, 372]),
                array([275, 378]),
                array([296, 237])
                ],

                [
                array([250, 229]),
                array([296, 237]),
                array([274, 378]),
                array([227, 371])
                ],

                [
                array([ 43, 258]),
                array([ 36, 298]),
                array([  1, 331]),
                array([ 36, 299])
                ]
            ]
        """

        #SETUP:
        bilateralConstant = kwargs.get('bilateralConstant', 13)
        returnFrame       = kwargs.get('returnFrame',       False)
        periTolerance     = kwargs.get('peri',              .05)                #Percent "closeness" to being flat edged

        minArea           = kwargs.get('minArea',           10)
        maxArea           = kwargs.get('maxArea',           100000000)
        minPerimeter      = kwargs.get('minPerimeter',      10)
        maxPerimeter      = kwargs.get('maxPerimeter',      100000000)

        frameToAnalyze    = kwargs.get('frameToAnalyze',    self.vid.frame.copy())
        thresholdMethod  = kwargs.get('threshold',          cv2.THRESH_BINARY)
        contourMethod     = kwargs.get('contourMethod',     cv2.RETR_EXTERNAL)  #RETR_EXTERNAL makes sure that only 'outmost' contours are counted
        deleteSimilar     = kwargs.get('deleteSimilar',     True)               #Deletes squares that are almost the same coordinates. Might cause lag

        ################################GET SHAPE CONTOUR ARRAYS##############################################
        #Get edged version of image
        cnts, edged = self.drawEdged(frameToAnalyze = frameToAnalyze, bilateralConstant = bilateralConstant, threshold = thresholdMethod,
                                     returnContours = True, contourMethod = contourMethod)

        #Find contours in the edged image, keep only the largest ones (the [:x] in sorted cnts line)
        #cnts, _ = cv2.findContours(edged.copy(), contourMethod, cv2.CHAIN_APPROX_SIMPLE  )
        cnts = sorted(cnts, key = cv2.contourArea, reverse = True)  #to limit, add [:20] to the end of the array

        #OPTIONAL: DRAW THE CONTOURS
        #cv2.drawContours(edged, cnts, -1, (255, 255, 255), 3)

        #RECORD ALL CONTOURS WITH ONLY 'sides' SIDES
        shapesDetected = []                                  #Array of all 'shape' contours found in the image so far
        for c in cnts:
            peri = cv2.arcLength(c, True)                              #  Perimeter of the contour
            approx = cv2.approxPolyDP(c, periTolerance * peri, True)   #  This is how precise you want it to look at the contours. (Aka, the curvature of 2%)
            if len(approx) == sides:
                if  minArea < cv2.contourArea(approx) < maxArea and minPerimeter < peri < maxPerimeter:        #  Get rid of small anomalies that were mistakenly recognized as contours (size)
                    shapesDetected.append(approx)


        if len(shapesDetected) == 0:  #If no shapes detected, end function.
            if returnFrame:
                return [], edged
            else:
                return []

        ################################BEGIN ARRAY MODIFICATIONS TO MAKE IT USEFUL################################
        #CONVERT ARRAY TO THE PREDEFINED STRUCTURE (DOCUMENTED ABOVE)
        shapeArray = []
        for  shape in range(0, len(shapesDetected)):
            shapeArray.append([])
            for value in range(0, len(shapesDetected[shape])):
                shapeArray[shape].append(shapesDetected[shape][value][0])  #adds an [x, y] to the array of shape. There should be 'sides' amount of cells in each shape cell.


        ##############################GET RID OF DUPLICATE OBJECTS BY COMPARING COORDINATES#########################
        tolerance = 2  #How many pixels two coordinates in a shape must be away in order to be considered different shapes
        shapeTargets = []  #Creates an array of ShapeTargets

        for shape in range(len(shapeArray)):  #Gets rid of weird overlapping shapes and also finished making the shapeTargets array

            similarCoords = 0  #Keeps track of how many coordinates were within the tolerance
            if deleteSimilar:
                for otherShape in range(shape + 1, len(shapeArray)):
                    for coordShape in range(len(shapeArray[shape])):
                        for coordOtherShape in range(len(shapeArray[otherShape])):
                            shapeX = shapeArray[shape][coordShape][0]
                            shapeY = shapeArray[shape][coordShape][1]
                            otherShapeX = shapeArray[otherShape][coordOtherShape][0]
                            otherShapeY = shapeArray[otherShape][coordOtherShape][1]
                            if (shapeX - tolerance) < otherShapeX < (shapeX + tolerance):  #not within tolerance
                                if (shapeY - tolerance) < otherShapeY < (shapeY + tolerance):
                                    similarCoords += 1

            if similarCoords < 3 or not deleteSimilar:

                shapeTargets.append(ShapeTarget(vertices  = shapeArray[shape],
                                                area      = cv2.contourArea(shapesDetected[shape]),
                                                center    = np.sum(shapeArray[shape], axis          = 0) / len(shapeArray[shape]),
                                                perimeter = cv2.arcLength(shapesDetected[shape], True)))



        if returnFrame:
            return (shapeTargets, edged)
        return shapeTargets

    def getCircles(self, **kwargs):
        frameToAnalyze  = kwargs.get('frameToAnalyze', self.vid.frame.copy())
        minRadius       = kwargs.get('minRadius', 1)
        maxRadius       = kwargs.get('maxRadius', 100)
        strictness      = kwargs.get('strictness', 30)
        gray = cv2.cvtColor(frameToAnalyze.copy(), cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 5)

        circles = cv2.HoughCircles(gray,       3,  1,       20, np.array([]), param1=100, param2=strictness, minRadius=int(minRadius), maxRadius=int(maxRadius))
        #         cv2.HoughCircles(image, method, dp, minDist[,     circles[,    param1[,   param2[,               minRadius[, maxRadius]]]]])
        if not circles is None:
            circles = circles[0]
        else:
            return []

        #Circles come in this format [x,y,radius] in an array of these. I change them to CircleTarget tuple format, for consistency
        circleArray = []

        for circle in circles:

            #  GET AVERAGE COLOR OF CIRCLE
            fromX = int(circle[0] - circle[2] / 2)
            toX   = int(circle[0] + circle[2] / 4)
            fromY = int(circle[1] - circle[2] / 4)
            toY   = int(circle[1] + circle[2] / 4)

            rect = frameToAnalyze[fromY:toY, fromX:toX]
            avgColor = cv2.mean(rect)
            circleArray.append(CircleTarget(radius = circle[2], area = math.pi * circle[2] ** 2, center = [int(circle[0]), int(circle[1])], color = avgColor))

        return circleArray

    def bruteGetFrame(self, getFunc, **kwargs):
        """
        This function recieves a function (getFunc) that is supposed to return a value (usually coordinates of a target).
        It then will, for maxAttempts, run that function and test if it is returning a value (anything but an empty list).
        If it gets a value it will return it immediately, if it doesn't it will get new camera frames and try again until
        maxAttempts is reaches, when it will then raise an error.
==
        """
        maxAttempts = kwargs.get("maxAttempts", 15)

        for a in range(maxAttempts):
            #Get function value and test the validity
            try:
                values = getFunc()
            except:
                values = []

            if len(values):
                return values
            #print "bruteGetFrame():\tTrying again..."

            #If validity false (empty array), get a new frame then try it again
            lastFrame = self.vid.frameCount
            while self.vid.frameCount == lastFrame:
                pass



        print "bruteGetFrame():\tFailed at", maxAttempts, "attempts. Raising Error..."
        raise NameError("ObjNotFound")

    def getMovement(self, **kwargs):
        """
        :param kwargs:
            "returnFrame": (Default: False) Means that getMovement will return the movementImg frame it recieves, as well as the mean movement.
        :return:
            Returns the average pixel value of the difference between two frames
            if "returnFrame" is True, then it will also return the frame showing movement.
        """
        returnFrame = kwargs.get("returnFrame", False)

        #GET TWO CONSECUTIVE FRAMES
        if self.vid.previousFrames < 10:
            print "getMovement():\tNot enough frames in self.vid.previousFrames"
            return 0    #IF PROGRAM IS RUN BEFORE THE PROGRAM HAS EVEN 10 FRAMES


        frame0 = self.vid.previousFrames[len(self.vid.previousFrames) - 1]
        frame1 = self.vid.previousFrames[len(self.vid.previousFrames) - 2]
        movementImg = cv2.absdiff(frame0, frame1).copy()  # syntax: (most recent, least recent)
        avgDifference = cv2.mean(movementImg)[0]
        if returnFrame:
            return avgDifference, movementImg
        return  avgDifference

    def getBlur(self, **kwargs):
        """
        Returns a number that stands for how blurry the image is. Unintuitively, lower numbers mean
        more blurry. A number of 100 is a good threshold to tell if an image is blurry or not.
        :param kwargs:
        :return:
        """

        frameToAnalyze = kwargs.get('frameToAnalyze', self.vid.frame.copy())
        return cv2.Laplacian(frameToAnalyze, cv2.CV_64F).var()

    def getTransform(self, shapeTarget, **kwargs):

        frameToTransform = kwargs.get('frameToAnalyze',  self.vid.frame.copy())
        imgW =             kwargs.get('transformWidth',  frameToTransform.shape[0])  #The target transformation width and height
        imgH =             kwargs.get('transformHeight', frameToTransform.shape[1])


        #ptsFrom = np.float32(shapeTarget.vertices)

        #FIND THE TOP LEFT, BOTTOM LEFT, TOP RIGHT, AND BOTTOM RIGHT POINTS THROUGH SORTING
        #[[TOP LEFT], [BOTTOM LEFT], [TOP RIGHT], [BOTTOM RIGHT]]
        vertices = shapeTarget.vertices
        tL = sorted(vertices, key = lambda s: (s[0])        ** 2 + (s[1])        ** 2)[0]
        bL = sorted(vertices, key = lambda s: (s[0] - imgH) ** 2 + (s[1])        ** 2)[0]
        tR = sorted(vertices, key = lambda s: (s[0])        ** 2 + (s[1] - imgW) ** 2)[0]
        bR = sorted(vertices, key = lambda s: (s[0] - imgH) ** 2 + (s[1] - imgW) ** 2)[0]


        ptsFrom = np.float32([tL, bL, tR, bR])
        #ptsFrom = np.float32([[56,65],[368,52],[28,387],[389,390]])
        ptsTo   = np.float32([[0, 0],   [imgW, 0],  [0, imgH],  [imgW, imgH]])

        M = cv2.getPerspectiveTransform(ptsFrom, ptsTo)
        dst = cv2.warpPerspective(frameToTransform, M, (imgW, imgH))

        return dst

    def getTargetCoords(self, target):  #Returns 4 xy coordinates that make up the object's rectangle
        try:
            return self.tracker.track(self.vid.frame)[target].quad
        except IndexError:
            return []



    #Color Operations
    def hsv2bgr(self, colorHSV):
        isList = colorHSV is tuple

        h, s, v = colorHSV[0], colorHSV[1], colorHSV[2]

        h = float(h)
        s = float(s)
        v = float(v)
        h60 = h / 60.0
        h60f = math.floor(h60)
        hi = int(h60f) % 6
        f = h60 - h60f
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)
        r, g, b = 0, 0, 0
        if hi == 0: r, g, b = v, t, p
        elif hi == 1: r, g, b = q, v, p
        elif hi == 2: r, g, b = p, v, t
        elif hi == 3: r, g, b = p, q, v
        elif hi == 4: r, g, b = t, p, v
        elif hi == 5: r, g, b = v, p, q
        r, g, b = int(r * 255), int(g * 255), int(b * 255)

        if isList:
            return [b, g, r]
        else:
            return b, g, r

    def bgr2hsv(self, colorBGR):
        """
        Input: A tuple OR list of the format (h, s, v)
        OUTPUT: A tuple OR list (depending on what was sent in) of the fromat (r, g, b)
        """
        isList = colorBGR is list

        r, g, b = colorBGR[2], colorBGR[1], colorBGR[0]

        r, g, b = r / 255.0, g / 255.0, b / 255.0
        mx = max(r, g, b)
        mn = min(r, g, b)
        df = mx - mn
        if mx == mn:
            h = 0
        elif mx == r:
            h = (60 * ((g - b) / df) + 360) % 360
        elif mx == g:
            h = (60 * ((b - r) / df) + 120) % 360
        elif mx == b:
            h = (60 * ((r - g) / df) + 240) % 360
        if mx == 0:
            s = 0
        else:
            s = df/mx
        v = mx

        if isList:
            return [h, s, v]
        else:
            return h, s, v



    #COORDINATE MATH FUNCTIONS
    def getShapesCentroid(self, shapeArray):
        """
            Returns the average coordinate in an array of ShapeTargets
        """
        if len(shapeArray) == 0:
            return []
        shapeCenters = [s.center for i, s in enumerate(shapeArray)]
        avgCenters = np.mean(shapeCenters, axis = 0).astype(int)
        return avgCenters

    def getTargetCenter(self, target):
        coords = self.getTargetCoords(target)  #coordinate array
        if len(coords) == 0:  #If it could not get target center
            return []

        xyAvg = np.sum(coords, axis = 0) / len(coords)
        return xyAvg[0], xyAvg[1]

    def getTargetAvgCoords(self, target, uniqueFrames):
        array = []                                              #Fills the array with the same centerCoords. Later, it will get unique ones.
        lastFrame = self.vid.frameCount                         #gets the last frame read
        arraySum = [[0, 0], [0, 0], [0, 0], [0, 0]]             #Everything is added here, and is divided by uniqueFrames at the end.
        while len(array) < uniqueFrames:                        #Until we get individual coords for the amount we asked...
            while self.vid.frameCount == lastFrame: pass        #waits till a new frame is avaliable
            lastFrame = self.vid.frameCount                     #gets the last frame read
            nextCoords = self.getTargetCoords(target)           #If no target found, it returns an array of None's
            if (len(array) == 0 or not np.array_equal(nextCoords, array[len(array) - 1])) and len(nextCoords) == 4:
                array.append(nextCoords)
                for coord in range(0, len(arraySum)):           #adds each individual cell of nextCoords to the arraySum
                    for xy in range(0, len(arraySum[coord])):
                        arraySum[coord][xy] += int(round(nextCoords[coord][xy]))

        arrayAvg = np.array(arraySum)
        arrayAvg = arrayAvg / uniqueFrames

        #arrayAvg = [[int(y/uniqueFrames) for y in arraySum[x]] for x in arraySum]
        return arrayAvg

    def getTargetAvgCenter(self, target, uniqueFrames):
        avgCoords = self.getTargetAvgCoords(target, uniqueFrames)
        x = (avgCoords[0][0] + avgCoords[1][0] + avgCoords[2][0] + avgCoords[3][0]) / 4  #(x1+x2)/2
        y = (avgCoords[0][1] + avgCoords[1][1] + avgCoords[2][1] + avgCoords[3][1]) / 4  #(y1+y2)/2
        return [int(x), int(y)]

    def sortShapesByDistance(self, shapeArray, **kwargs):  #Returns the shape nearest to coords
        """
        :param sides: How many sides does the object have that is being searched for?
        :param kwargs:
            "nearestTo": (Defaults to the [x,y] of the center of the screen. This means that the function will return shapes closest to these coordinates
        :return:
        """

        #SET UP VARIABLES
        screenDimensions = self.vid.getDimensions()
        coords           = kwargs.get("nearestTo", [screenDimensions[0] / 2, screenDimensions[1] / 2])
        maxDist          = kwargs.get('maxDist', 100000)    #For cases where you want it to return an empty list if nothing within maxDist was found near coords
        returnNearest = kwargs.get("returnNearest", False)  #If true, it will return only the first index of the array


        #SORT THE SHAPES IN THE ARRAY BY HOW FAR THEY ARE FROM THE "COORDS" VARIABLE
        shapeTargets = sorted(shapeArray, key = lambda s: (s.center[0] - coords[0]) ** 2 + (s.center[1] - coords[1]) ** 2)
        if len(shapeTargets) == 0:  #If no shapes found
            #print "getNearestShape():\tNo shapes found"
            return []

        shapesWithinDist = []

        for index, shape in enumerate(shapeTargets):
            distFromCoords = ((shape.center[0] - coords[0]) ** 2 + (shape.center[1] - coords[1]) ** 2) ** .5

            if distFromCoords < maxDist:
                shapesWithinDist.append(shape)


        if len(shapesWithinDist) == 0:
            return []


        if returnNearest:
            return shapesWithinDist[0]  #Return nearest shape
        else:
            return shapesWithinDist     #Return shapes in order from nearest to furthest



class PlaneTracker:

    def __init__(self, minMatchCount, trackingPoints):
        self.detector = cv2.ORB(nfeatures = trackingPoints)  #CHANGES THE NUMBER OF DOT THINGS ON SCREEN!

        self.matcher = cv2.FlannBasedMatcher(flann_params, {})  # bug : need to pass empty dict (#1329)
        self.targets = []
        self.minMatchCount = minMatchCount

    def addTarget(self, image, rect, data = None):
        #Add a new tracking target.
        x0, y0, x1, y1 = rect
        raw_points, raw_descrs = self.detect_features(image)
        points, descs = [], []
        for kp, desc in zip(raw_points, raw_descrs):
            x, y = kp.pt
            if x0 <= x <= x1 and y0 <= y <= y1:
                points.append(kp)
                descs.append(desc)
        descs = np.uint8(descs)
        self.matcher.add([descs])
        target = PlanarTarget(image = image, rect = rect, keypoints = points, descrs=descs, data=None)
        self.targets.append(target)

    def clear(self):
        #Remove all targets
        self.targets = []
        self.matcher.clear()

    def track(self, frame):
        #Returns a list of detected TrackedTarget objects
        self.frame_points, self.frame_descrs = self.detect_features(frame)
        if len(self.frame_points) < self.minMatchCount:
            return []
        matches = self.matcher.knnMatch(self.frame_descrs, k = 2)
        matches = [m[0] for m in matches if len(m) == 2 and m[0].distance < m[1].distance * 0.75]
        if len(matches) < self.minMatchCount:
            return []
        matches_by_id = [[] for _ in xrange(len(self.targets))]
        for m in matches:
            matches_by_id[m.imgIdx].append(m)
        tracked = []
        for imgIdx, matches in enumerate(matches_by_id):
            if len(matches) < self.minMatchCount:
                continue
            target = self.targets[imgIdx]
            p0 = [target.keypoints[m.trainIdx].pt for m in matches]
            p1 = [self.frame_points[m.queryIdx].pt for m in matches]
            p0, p1 = np.float32((p0, p1))
            H, status = cv2.findHomography(p0, p1, cv2.RANSAC, 3.0)
            prestatus = status
            if status == None: continue  #Code written when I transitioned to openCV 3.0, for some reason cv2.findHomography was giving issues, and was returning noneTypes at times when object not found.

            status = status.ravel() != 0

            if status.sum() < self.minMatchCount:
                continue
            p0, p1 = p0[status], p1[status]

            x0, y0, x1, y1 = target.rect
            quad = np.float32([[x0, y0], [x1, y0], [x1, y1], [x0, y1]])
            quad = cv2.perspectiveTransform(quad.reshape(1, -1, 2), H).reshape(-1, 2)

            track = TrackedTarget(target=target, p0=p0, p1=p1, H=H, quad=quad)
            tracked.append(track)
        tracked.sort(key = lambda t: len(t.p0), reverse=True)
        return tracked

    def detect_features(self, frame):
        #detect_features(self, frame) -> keypoints, descrs
        keypoints, descrs = self.detector.detectAndCompute(frame, None)

        if descrs is None:  # detectAndCompute returns descs=None if not keypoints found
            descrs = []
        return keypoints, descrs