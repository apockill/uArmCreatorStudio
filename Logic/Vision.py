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
import os
import cv2
import numpy as np
import math
from Logic.Global import printf
from collections  import namedtuple
from time         import sleep
__author__ = "Alexander Thiel"


class Vision:
    """
    This class is for all computer vision and frame processing that needs doing. Vision does not do any changes on
    the video stream, that's done in the VideoStream class. What vision does is handle object tracking,
    filters, threading locks, and handing work off to be done by the VideoStream class.

    The typical workflow for Vision is to:
        vision.addTarget(trackable)    # Start tracking some object

        # Some time later in the program, look for the object. There are multiple search functions
        getMostAccurateRecognition(trackable)  # Find the object with the highest pt count in the tracked history

        searchTrackedHistory(trackable, maxAge, minPtCount

        getObjectSpeedDirectionAvg(trackable, maxAge,
    """

    def __init__(self, vStream, cascadePath):
        """
        :param vStream: A VideoStream object from Video.py
        :param cascadePath: The path to the directory that holds the cascade.xml files
        :return:
        """

        # How long the "tracker history" array is (how many frames of tracked data are kept)
        self.historyLen = 60

        self.vStream        = vStream
        self.exiting        = False
        self.planeTracker   = PlaneTracker(25.0, self.historyLen)
        self.cascadeTracker = CascadeTracker(self.historyLen, cascadePath)


        # Use these on any work functions that are intended for threading
        self.filterLock  = self.vStream.filterLock
        self.workLock    = self.vStream.workLock

    # Wrappers for the VideoStream object
    def waitForNewFrames(self, numFrames=1):
        # Useful for situations when you need x amount of new frames after the robot moved, before doing vision
        for i in range(0, numFrames):

            lastFrame = self.vStream.frameCount
            while self.vStream.frameCount == lastFrame:
                if self.exiting:
                    printf("Vision| Exiting early!")
                    break

                sleep(.01)



    # All Tracker Controls
    def addTarget(self, trackable):
        """
        Add a target to the PlaneTracker class
        """

        if trackable is None:
            printf("Vision| ERROR: Tried to add nonexistent trackable to the tracker!")
            return

        views = trackable.getViews()
        with self.workLock:
            for view in views:
                self.planeTracker.addView(view)

        # Make sure that the work and filter trackers are present
        self.vStream.addWork(self.planeTracker.track)
        self.vStream.addFilter(self.planeTracker.drawTracked)

    def addCascadeTarget(self, targetID):
        self.cascadeTracker.addTarget(targetID)

        # Make sure that the tracker and filter are activated
        self.vStream.addWork(self.cascadeTracker.track)
        self.vStream.addFilter(self.cascadeTracker.drawTracked)

    def endAllTrackers(self):
        # End all trackers and clear targets
        with self.workLock:
            self.planeTracker.clear()
            self.cascadeTracker.clear()

        # Shut down and reset any cascade tracking
        self.vStream.removeWork(self.cascadeTracker.track)
        self.vStream.removeFilter(self.cascadeTracker.drawTracked)

        # Shut down and reset any planeTracking
        self.vStream.removeWork(self.planeTracker.track)
        self.vStream.removeFilter(self.planeTracker.drawTracked)


    # PlaneTracker Search Functions
    def getObjectLatestRecognition(self, trackable):
        """
            Returns the latest successful recognition of the trackable, so the user can pull the position from that
            it also returns the age of the frame where the object was found (0 means most recently)
        """

        with self.workLock:
            trackHistory = self.planeTracker.trackedHistory[:]

        for frameID, historyFromFrame in enumerate(trackHistory):
            for tracked in historyFromFrame:
                if trackable.equalTo(tracked.view.name):
                    return frameID, tracked
        return None, None

    def getMostAccurateRecognition(self, trackable, maxAge):
        """
        This will find the best ptCount of any recognitions of trackable

        :param trackable: The TrackableObject you intend to find
        :param maxAge:  How recent the recognition was, in "frames gotten from camera"
        :param maxAttempts:  How many frames it should wait for before quitting the search.
        :return:
        """

        with self.workLock:
            trackHistory = self.planeTracker.trackedHistory[:]

        best = None

        # Check if the object was recognized in the most recent frame. Check most recent frames first.
        for age, historyFromFrame in enumerate(trackHistory):
            if maxAge is not None and age > maxAge: return best

            for tracked in historyFromFrame:
                # If the object meets the criteria
                if trackable is None: continue
                if not trackable.equalTo(tracked.view.name): continue

                if best is None or tracked.ptCount > best.ptCount:
                    best = tracked

        return best

    def getObjectSpeedDirectionAvg(self, trackable, samples=3, maxAge=20, isSameObjThresh=50):
        """
        This is an interesting function. So a lot of the time there might be more than one object of the same type
        in the cameras view, for example, two playing cards with the backs facing the camera. Since the keypoint matcher
        can't recognize the same object twice, I need a way to get several samples of an object and make sure that it
        wasn't multiple frames where some frames are of object 1 and some frames are of identicle object 2.

        This function will try to find "samples" amount of frames in the last "maxAge" frames of an object that hasn't
        moved to much- this should effectively find only one of the identicle objects, and return the average position,
        and how much it's "moving".

        isSameObjThresh is how many pixels the object can move between frames for it to still be considered the
        same object.

        :param trackable: A trackable object from Resources.py
        :param samples: Amount of samples to find of the object
        :param maxAge: How many frames to look back into history for searching for samples
        :param isSameObjThresh: Amount of pixels the object can move between samples to still be considered the same
        object.

        :return: avgPos of object [x,y,z], avgMag (magnitude amount of pixels moved per frame), avgDir, direction of
        movement in [xdir, ydir, zdir]
        """
        with self.workLock:
            trackHistory = self.planeTracker.trackedHistory[:maxAge]

        hst      = []
        # Get 'samples' amount of tracked object from history, and the first sample has to be maxAge less then the last
        for frameAge, historyFromFrame in enumerate(trackHistory):

            for tracked in historyFromFrame:
                if trackable.equalTo(tracked.view.name):
                    # If it's the first object
                    if len(hst) == 0:
                        hst.append(tracked.center)
                        break

                    c = tracked.center
                    dist = ((hst[0][0] - c[0]) ** 2 + (hst[0][1] - c[1]) ** 2 + (hst[0][2] - c[2]) ** 2) ** .5


                    if dist < isSameObjThresh:
                        hst.append(tracked.center)
                        break
            if len(hst) >= samples: break

        if len(hst) == 0: return None, None, None

        # Get the "noise" of the sample
        hst     = np.float32(hst)
        avgPos  = hst[0]
        avgDir  = np.float32([0, 0, 0])
        for i, pt in enumerate(hst[1:]):
            avgDir += np.float32(hst[i]) - pt
            avgPos += pt

        avgDir /= samples - 1
        avgMag  = sum(avgDir ** 2) ** .5
        avgPos /= samples
        return avgPos, avgMag, avgDir

    def searchTrackedHistory(self, trackable=None, maxAge=0, minPoints=None):
        """
        Search through trackedHistory to find an object that meets the criteria

        :param trackableObject: Specify if you want to find a particular object
        :param maxAge:        Specify if you wannt to find an object that was found within X frames ago
        :param minPoints:      Specify if you want to find an object with a minimum amount of tracking points
        """

        maxFrame = maxAge + 1
        if maxFrame is None or maxFrame >= self.historyLen:
            printf("Vision| ERROR: Tried to look further in the history than was possible!")
            maxFrame = self.historyLen

        # Safely pull the relevant trackedHistory from the tracker object
        with self.workLock:
            trackHistory = self.planeTracker.trackedHistory[:maxFrame]


        # Check if the object was recognized in the most recent frame. Check most recent frames first.
        for historyFromFrame in trackHistory:
            for tracked in historyFromFrame:
                # If the object meets the criteria
                if trackable is not None and not trackable.equalTo(tracked.view.name): continue
                if minPoints is not None and not tracked.ptCount > minPoints: continue

                return tracked
        return None



    # Cascade Tracker Search Functions
    def getCascadeLatestRecognition(self, cascadeName):
        """
        This will get the latest recognition of that cascade, and return the age of the cascade, and the
        [x1, y1, x2, y2] bounding box of the cascade's location.

        :param cascadeName: This is a string, either "Smile", "Face", "Eye", or any custom cascades loaded into
        CascadeTracker

        :return: frameage, location
        """

        # Safely pull the relevant trackedHistory from the tracker object
        with self.workLock:
            trackHistory = self.cascadeTracker.trackedHistory[:]


        for frameID, historyFromFrame in enumerate(trackHistory):
            for tracked in historyFromFrame:
                if tracked.target.name == cascadeName:
                    return frameID, tracked
        return None, None


    # General use computer vision functions
    def getMotion(self):

        # GET TWO CONSECUTIVE FRAMES
        frameList = self.vStream.getFrameList()
        if len(frameList) < 10:  # Make sure there are enough frames to do the motion comparison
            printf("Vision| Not enough frames in self.vid.previousFrames")
            return 0  # IF PROGRAM IS RUN BEFORE THE PROGRAM HAS EVEN 10 FRAMES

        frame0 = frameList[0]
        frame1 = frameList[5]


        movementImg = cv2.absdiff(frame0, frame1)
        avgDifference = cv2.mean(movementImg)[0]

        return avgDifference


    # Vision specific functions
    def setExiting(self, exiting):
        """
            Used for closing threads quickly, when this is true any time-taking functions will skip through quickly
            and return None or False or whatever their usual failure mode is. ei, waitForFrames() would exit immediately

        :param exiting: A boolean
        """


        self.exiting = exiting


    '''     OLD (NO LONGER USED) VISION FUNCTIONS
    def findObjectColor(self, hue, tolerance, lowSat, highSat, lowVal, highVal):
        low, high = self.getRange(hue, tolerance)

        hue = int(hue)
        tolerance = int(tolerance)
        lowSat = int(lowSat * 255)
        highSat = int(highSat * 255)
        lowVal = int(lowVal * 255)
        highVal = int(highVal * 255)

        frame = self.vStream.getFrame()
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        if hue - tolerance < 0 or hue + tolerance > 180:
            # If the color crosses 0, you have to do two thresholds
            lowThresh = cv2.inRange(hsv, np.array((0, lowSat, lowVal)), np.array((low, highSat, highVal)))
            upperThresh = cv2.inRange(hsv, np.array((high, lowSat, lowVal)), np.array((180, highSat, highVal)))
            finalThresh = upperThresh + lowThresh
        else:
            finalThresh = cv2.inRange(hsv, np.array((low, lowSat, lowVal)), np.array((high, highSat, highVal)))

        cv2.imshow(str(lowSat), finalThresh.copy())
        cv2.waitKey(1)

        contours, hierarchy = cv2.findContours(finalThresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        cv2.imshow("frame", finalThresh)
        cv2.waitKey(1)
        # Find the contour with maximum area and store it as best_cnt
        max_area = 0
        best_cnt = None
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > max_area:
                max_area = area
                best_cnt = cnt

        if best_cnt is not None:
            M = cv2.moments(best_cnt)
            cx, cy = int(M['m10'] / M['m00']), int(M['m01'] / M['m00'])
            # cv2.circle(frame, (cx, cy), 5, 255, -1)
            return [cx, cy]
        return None

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
            s = df / mx
        v = mx

        if isList:
            return [h, s, v]
        else:
            return h, s, v

    def crop(self, image, rect):
        # Just pass an image, and a tuple/list of (x1,y1, x2,y2)
        return image[rect[1]:rect[3], rect[0]:rect[2]]

        def getColor(self, **kwargs):
        # Get the average color of a rectangle in the main frame. If no rect specified, get the whole frame
        p1 = kwargs.get("p1", None)
        p2 = kwargs.get("p2", None)

        frame = self.vStream.getFrame()
        if p1 is not None and p2 is not None:
            frame = frame[p2[1]:p1[1], p2[0]:p1[0]]

        averageColor = cv2.mean(frame)  # RGB
        return averageColor

    def getRange(self, hue, tolerance):
        # Input an HSV, get a range
        low = hue - tolerance / 2
        high = hue + tolerance / 2

        if low < 0:   low += 180
        if low > 180: low -= 180

        if high < 0:   high += 180
        if high > 180: high -= 180

        if low > high:
            return int(high), int(low)
        else:
            return int(low), int(high)

    '''


class Tracker:
    """
        This is the base class for any object tracker.
        All object trackers carry a "history" of tracked objects, in an array called trackedHistory.
        This is later searched through to find objects that have been tracked.
    """

    def __init__(self, historyLength):
        self.historyLen = historyLength
        self.targets      = []
        self.trackedHistory = [[] for i in range(self.historyLen)]

        self.fFnt       = cv2.FONT_HERSHEY_PLAIN  # Font for filter functions
        self.fColor     = (255, 255, 255)  # Default color for filter functions
        self.fThickness = 2  # Thickness of lines


    def _addToHistory(self, trackedArray):
        # Add an array of detected objects to the self.trackedHistory array, and shorten the trackedHistory array
        # so that it always remains self.historyLength long
        self.trackedHistory.insert(0, trackedArray)

        while len(self.trackedHistory) > self.historyLen:
            del self.trackedHistory[-1]

    def clear(self):
        self.trackedHistory = [[] for i in range(self.historyLen)]
        self.targets = []


class PlaneTracker(Tracker):
    """
    PlanarTarget:
        image     - image to track
        rect      - tracked rectangle (x1, y1, x2, y2)
        keypoints - keypoints detected inside rect
        descrs    - their descriptors
        data      - some user-provided data

    TrackedTarget:
        target - reference to PlanarTarget
        p0     - matched points coords in target image
        p1     - matched points coords in input frame
        H      - homography matrix from p0 to p1
        quad   - target bounary quad in input frame
    """
    PlaneTarget  = namedtuple('PlaneTarget', 'view, keypoints, descrs')

    # target: the "sample" object of the tracked object. Center: [x,y,z] Rotation[xr, yr, zr], ptCount: matched pts
    TrackedPlane = namedtuple('TrackedPlane', 'view, target, quad, ptCount, center, rotation, p0, p1, H,')

    # Tracker parameters
    FLANN_INDEX_KDTREE = 1
    FLANN_INDEX_LSH    = 6
    MIN_MATCH_COUNT    = 15

    # Check Other\Notes\FlanParams Test Data to see test data for many other parameters I tested for speed and matching
    flanParams         = dict(algorithm         = FLANN_INDEX_LSH,
                              table_number      =              6,  #  3,  #  6,  # 12,
                              key_size          =             12,  # 19,  # 12,  # 20,
                              multi_probe_level =              1)  # 1)   #  1)  #  2)

    K = None  # Set in get3DCoordinates
    distCoeffs = np.zeros(4)

    def __init__(self, focalLength, historyLength):
        super(PlaneTracker, self).__init__(historyLength)
        self.focalLength  = focalLength
        self.detector     = cv2.ORB_create(nfeatures = 9000)

        # For ORB
        self.matcher      = cv2.FlannBasedMatcher(self.flanParams, {})  # bug : need to pass empty dict (#1329)
        self.framePoints  = []

    def createTarget(self, view):
        """
        There's a specific function for this so that the GUI can pull the objects information and save it as a file
        using objectManager. Other than that special case, this function is not necessary for normal tracker use
        """

        # Get the PlanarTarget object for any name, image, and rect. These can be added in self.addTarget()
        x0, y0, x1, y1         = view.rect
        points, descs          = [], []

        raw_points, raw_descrs = self.__detectFeatures(view.image)

        for kp, desc in zip(raw_points, raw_descrs):
            x, y = kp.pt
            if x0 <= x <= x1 and y0 <= y <= y1:
                points.append(kp)
                descs.append(desc)


        descs  = np.uint8(descs)
        target = self.PlaneTarget(view=view, keypoints=points, descrs=descs)

        # If it was possible to add the target
        return target

    def addView(self, view):
        # This function checks if a view is currently being tracked, and if not it generates a target and adds it

        for target in self.targets:
            if view == target.view: return

        planarTarget = self.createTarget(view)

        descrs = planarTarget.descrs
        self.matcher.add([descrs])
        self.targets.append(planarTarget)


    def clear(self):
        super().clear()

        # Remove all targets
        self.matcher.clear()

    def track(self, frame):
        # updates self.tracked with a list of detected TrackedTarget objects
        self.framePoints, frame_descrs = self.__detectFeatures(frame)
        tracked = []


        # If no keypoints were detected, then don't update the self.trackedHistory array
        if len(self.framePoints) < self.MIN_MATCH_COUNT:
            self._addToHistory(tracked)
            return


        matches = self.matcher.knnMatch(frame_descrs, k = 2)
        matches = [m[0] for m in matches if len(m) == 2 and m[0].distance < m[1].distance * 0.75]

        if len(matches) < self.MIN_MATCH_COUNT:
            self._addToHistory(tracked)
            return


        matches_by_id = [[] for _ in range(len(self.targets))]
        for m in matches:
            matches_by_id[m.imgIdx].append(m)

        tracked = []

        for imgIdx, matches in enumerate(matches_by_id):

            if len(matches) < self.MIN_MATCH_COUNT:
                continue

            target = self.targets[imgIdx]

            p0 = [target.keypoints[m.trainIdx].pt for m in matches]
            p1 = [self.framePoints[m.queryIdx].pt for m in matches]
            p0, p1 = np.float32((p0, p1))
            H, status = cv2.findHomography(p0, p1, cv2.RANSAC, 3.0)

            status = status.ravel() != 0
            if status.sum() < self.MIN_MATCH_COUNT: continue


            p0, p1 = p0[status], p1[status]

            x0, y0, x1, y1 = target.view.rect
            quad = np.float32([[x0, y0], [x1, y0], [x1, y1], [x0, y1]])
            quad = cv2.perspectiveTransform(quad.reshape(1, -1, 2), H).reshape(-1, 2)



            # Calculate the 3d coordinates of the object
            center, rotation = self.get3DCoordinates(frame, target.view.rect, quad)

            track = self.TrackedPlane(target=target,
                                      view=target.view,
                                      quad=quad,
                                      ptCount=len(matches),
                                      center=center,
                                      rotation=rotation,
                                      p0=p0, p1=p1, H=H, )
            tracked.append(track)


        tracked.sort(key = lambda t: len(t.p0), reverse=True)

        self._addToHistory(tracked)


    def __detectFeatures(self, frame):
        cv2.ocl.setUseOpenCL(False)  # THIS FIXES A ERROR BUG: "The data should normally be NULL!"

        # detect_features(self, frame) -> keypoints, descrs
        keypoints, descrs = self.detector.detectAndCompute(frame, None)
        if descrs is None:  # detectAndCompute returns descs=None if not keypoints found
            descrs = []
        return keypoints, descrs

    def drawTracked(self, frame):

        # Sort the objects from lowest (z) to highest Z, so that they can be drawn one on top of the other
        drawObjects = self.trackedHistory[0]
        drawObjects = sorted(drawObjects, key=lambda obj: obj.center[2], reverse=True)

        mask  = np.zeros_like(frame)
        tMask = np.zeros_like(frame)  # Used to show transparent shapes


        for tracked in drawObjects:
            quad = np.int32(tracked.quad)

            # If this object is definitely higher than the other, erase everything beneath it to give the "3D" effect
            cv2.fillConvexPoly(mask, quad, 0)


            # Draw the tracked points
            for (x, y) in np.int32(tracked.p1):
                    cv2.circle(tMask, (x, y), 2, (255, 255, 255))


            # Draw the rectangle around the object- in both the normal mask and the transparent one
            cv2.polylines( mask, [quad], True, (255, 255, 255), 3)
            cv2.polylines(tMask, [quad], True, (255, 255, 255), 2)


            # Draw coordinate grids on each object with a red, green, and blue arrow
            rect          = tracked.view.rect
            x0, y0, x1, y1 = rect
            width  = (x1 - x0) / 2
            height = (y1 - y0) / 2
            x0, y0, x1, y1 = -width, -height, width, height


            #                       Line start  Triangle tip  Triangle vert1   Triangle vert2
            ar_verts = np.float32([[.5,  0, 0], [.5,  1, 0], [.45, .95,   0], [.55, .95,   0],      # Y
                                   [ 0, .5, 0], [ 1, .5, 0], [.95, .45,   0], [.95, .55,   0],      # X
                                   [.5, .5, 0], [.5, .5, 1], [.45,  .5, .90], [.55,  .5, .90]])     # Z axis

            # Color of each arrow
            red      = (   1,   1, 255)
            green    = (   1, 255,   1)
            blue     = ( 255,   1,   1)

            # Which elements in ar_verts are to be connected with eachother as a line
            ar_edges = [( 0, 1,   red),  # ( 2, 1,   red), ( 3, 1,    red),
                        ( 4, 5,  blue),  # ( 6, 5,  blue), ( 7, 5,   blue),
                        ( 8, 9, green)]  # , (10, 9, green), (11, 9,  green)]

            verts = ar_verts * [(x1 - x0), (y1 - y0), -(x1 - x0) * 0.3] + (x0, y0, 0)

            # Project the arrows in 3D
            center = np.array(tracked.center).reshape(-1, 1)
            rotation = np.array(tracked.rotation).reshape(-1, 1)
            verts = cv2.projectPoints(verts, rotation, center, self.K, self.distCoeffs)[0].reshape(-1, 2)


            # Draw lines for the arrows
            for i, j, color in ar_edges:
                (x0, y0), (x1, y1) = verts[i], verts[j]
                cv2.line(mask, (int(x0), int(y0)), (int(x1), int(y1)), color, 2)

            # Draw triangles for the arrows
            for i in range(0, 3):
                row = i * 4
                cv2.fillConvexPoly(mask, np.int32([verts[row + 1], verts[row + 2], verts[row + 3]]), ar_edges[i][2])





        # Draw the text seperately, so it's always on top of everything
        for tracked in drawObjects:
            quad = np.int32(tracked.quad)
            rect = tracked.view.rect
            
            # Create the text that will be drawn
            nameText  = tracked.view.name

            coordText =  "("  + str(int(tracked.center[0])) + \
                         "," + str(int(tracked.center[1])) + \
                         "," + str(int(tracked.center[2])) + \
                         ") R" + str(int(math.degrees(tracked.rotation[2]) + 180))

            # Figure out how much the text should be scaled (depends on the different in curr side len, and orig len)
            origLength    = rect[2] - rect[0] + rect[3] - rect[1]
            currLength    = np.linalg.norm(quad[1] - quad[0]) + np.linalg.norm(quad[2] - quad[1])  # avg side len
            scaleFactor   = currLength / origLength + .35


            # Find a location on screen to draw the name of the object
            size, _    = cv2.getTextSize(nameText, self.fFnt, scaleFactor, thickness=self.fThickness)
            txtW, txtH = size
            h, w, _ = mask.shape
            validCorners = [c for c in quad if 0 < c[1] < h]
            validCorners = [c for c in validCorners if (0 < c[0] and c[0] + txtW < w)]

            dist = 10 * scaleFactor

            # If a corner was found, draw the name on that corner
            if len(validCorners):
                chosenCorner = tuple(validCorners[0])

                # Draw the name of the object
                mask  = drawOutlineText(mask, nameText, chosenCorner,
                            self.fFnt, scaleFactor, color=self.fColor, thickness=self.fThickness)
                tMask = drawOutlineText(tMask, nameText, chosenCorner,
                            self.fFnt, scaleFactor, color=self.fColor, thickness=self.fThickness)

                try:
                    # Draw the coordinates of the object
                    chosenCorner = chosenCorner[0], int(chosenCorner[1] + dist)
                    mask  = drawOutlineText(mask, coordText, chosenCorner,
                                self.fFnt, scaleFactor - .6, color=self.fColor, thickness=1)
                    tMask = drawOutlineText(tMask, coordText, chosenCorner,
                                self.fFnt, scaleFactor - .6, color=self.fColor, thickness=1)
                except ValueError as e:
                    printf("Vision| ERROR: Drawing failed because a None was attempted to be turned into int", e)



        # Apply the semi-transparent mask to the frame, with translucency
        frame[tMask > 0] = tMask[tMask > 0] * .7 + frame[tMask > 0] * .3


        # Apply the normal mask to the frame
        frame[mask > 0] = mask[mask > 0]   #  *= mask == 0


        return frame


    # Thread safe
    def get3DCoordinates(self, frame, rect, quad):
        # Do solvePnP on the tracked object
        x0, y0, x1, y1 = rect
        width  = (x1 - x0) / 2
        height = (y1 - y0) / 2
        quad3d = np.float32([[     -width,      -height, 0],
                              [     width,      -height, 0],
                              [     width,       height, 0],
                              [    -width,       height, 0]])

        if self.K is None:
            fx              = 0.5 + self.focalLength / 50.0
            h, w            = frame.shape[:2]
            self.K = np.float64([[fx * w,      0, 0.5 * (w - 1)],
                                 [     0, fx * w, 0.5 * (h - 1)],
                                 [   0.0,    0.0,          1.0]])



        ret, rotation, center = cv2.solvePnP(quad3d, quad, self.K, self.distCoeffs)
        # print(rotation)
        # Convert every element to floats and return int in List form
        return tuple(map(float, center)), tuple(map(float, rotation))


class CascadeTracker(Tracker):
    # This tracker is intended for tracking Haar cascade objects that are loaded with the program
    CascadeTarget  = namedtuple('CascadeTarget', 'name, classifier, minPts, minSize')
    CascadeTracked = namedtuple('CascadeTracked', 'target, quad, center')

    def __init__(self, historyLength, cascadePath):
        super(CascadeTracker, self).__init__(historyLength)

        self.cascades = [self.CascadeTarget(name       = "Face",
                                    classifier = cv2.CascadeClassifier(os.path.join(cascadePath, "face_cascade.xml")),
                                    minPts     = 20,
                                    minSize    = (30, 30)),

                         self.CascadeTarget(name       = "Smile",
                                    classifier = cv2.CascadeClassifier(os.path.join(cascadePath, "smile_cascade.xml")),
                                    minPts     = 325,
                                    minSize    = (80, 50)),

                         self.CascadeTarget(name       = "Eye",
                                    classifier = cv2.CascadeClassifier(os.path.join(cascadePath, "eye_cascade.xml")),
                                    minPts     = 30,
                                    minSize    = (40, 40))]


    def addTarget(self, targetName):
        for target in self.cascades:
            if targetName == target.name:

                # Make sure the target is not already being tracked
                if target not in self.targets:
                    self.targets.append(target)

    def track(self, frame):
        gray  = cv2.cvtColor(frame.copy(), cv2.COLOR_BGR2GRAY)

        tracked = []
        # Track any cascades that have been added to self.targets
        for target in self.targets:
            quads = target.classifier.detectMultiScale(gray,
                                                       scaleFactor  = 1.1,
                                                       minNeighbors = target.minPts,
                                                       minSize      = target.minSize)


            # If faces were found, create seperate "tracked" objects for them here
            for xywh in quads:
                # Convert xywh to a more readable set of points
                x0, y0, x1, y1 = xywh[0], xywh[1], xywh[0] + xywh[2], xywh[1] + xywh[3]

                # Make quad, a 4 point list of [p1, p2, p3, and p4]
                quad = np.array([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])

                # X, Y
                center = [int(xywh[2] / 2 + xywh[0]),
                          int(xywh[3] / 2 + xywh[1])]



                trackedObj = self.CascadeTracked(target=target, quad=quad, center=center)
                tracked.append(trackedObj)


        self._addToHistory(tracked)

    def drawTracked(self, frame):
        for tracked in self.trackedHistory[0]:
            quad = tracked.quad
            currLength    = np.linalg.norm(quad[1] - quad[0]) + np.linalg.norm(quad[2] - quad[1])  # avg side len
            scaleFactor   = currLength / 210

            cv2.rectangle(frame, tuple(quad[0]), tuple(quad[2]), (255, 255, 255), 2)

            frame = drawOutlineText(frame, tracked.target.name, (tracked.quad[1][0], tracked.quad[1][1] + int(15)),
                        self.fFnt, scaleFactor, color=self.fColor, thickness=self.fThickness)

        return frame



def drawOutlineText(frame, text, point, font, scale, color, thickness):
    """
        This function draws text twice, with a color on front and a color on the back
    """
    frame = cv2.putText(frame, text, tuple(point), font, scale, color=(1, 1, 1), thickness=thickness + 1)
    frame = cv2.putText(frame, text, tuple(point), font, scale, color=color, thickness=thickness)

    return frame
