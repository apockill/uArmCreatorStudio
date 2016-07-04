import time
import cv2
import numpy as np
from collections  import namedtuple
from Logic.Global import printf


class Vision:

    def __init__(self, vStream):

        self.vStream    = vStream
        self.tracker    = PlaneTracker(25.0)

        # Use these on any work functions that are intended for threading
        self.filterLock = self.vStream.filterLock
        self.workLock   = self.vStream.workLock


    # Wrappers for the VideoStream object
    def waitForNewFrames(self, numFrames=1):
        # Useful for situations when you need x amount of new frames after the robot moved, before doing vision
        # printf("Vision.waitForNewFrames(): Waiting for ", numFrames, " frames!")
        for i in range(0, numFrames):

            self.vStream.waitForNewFrame()


    # Object tracker control functions
    def addTrackable(self, trackable):
        views = trackable.getViews()
        with self.workLock:
            for view in views:
                self.tracker.addView(view)

    def clearTargets(self):
        with self.workLock:
            self.tracker.clear()

    def startTracker(self):
        # Adds a worker function to the videoStream to track all the time
        self.vStream.addWork(self.tracker.track)

    def endTracker(self):
        # Removes a worker function from the videoStream, to stop any ongoing tracking
        self.vStream.removeWork(self.tracker.track)


    # Object recognition functions

    def getObjectLatestRecognition(self, trackable):
        # Returns the latest successful recognition of objectID, so the user can pull the position from that
        # it also returns the age of the frame where the object was found (0 means most recently)

        with self.workLock:
            trackHistory = self.tracker.trackedHistory[:]

        for frameID, historyFromFrame in enumerate(trackHistory):
            for tracked in historyFromFrame:
                if trackable.equalTo(tracked.view.name):
                    return frameID, tracked
        return None, None

    def getObjectBruteAccurate(self, trackableObj, minPoints=-1, maxFrameAge=0, maxAttempts=1):
        """
        This will brute-force the object finding process somewhat, and ensure a good recognition, or nothing at all.

        :param trackableObj: The TrackableObject you intend to find
        :param minPoints:    Minimum amount of recognition points that must be found in order to track. -1 means ignore
        :param maxFrameAge:  How recent the recognition was, in "frames gotten from camera"
        :param maxAttempts:  How many frames it should wait for before quitting the search.
        :return:
        """


        # Get a super recent frame of the object
        for i in range(0, maxAttempts):
            # If the frame is too old or marker doesn't exist or doesn't have enough points, exit the function
            frameAge, trackedObj = self.getObjectLatestRecognition(trackableObj)

            if trackedObj is None or frameAge > maxFrameAge or trackedObj.ptCount < minPoints:
                if i == maxAttempts - 1: break

                self.waitForNewFrames()
                continue

            # If the object was successfully found with the correct attributes, return it
            return trackedObj

        return None

    def isRecognized(self, trackableObject, numFrames=1):
        # numFrames is the amount of frames to check in the history
        if numFrames >= self.tracker.historyLen:
            printf("Vision.isRecognized(): ERROR: Tried to look further in the history than was possible!")
            numFrames = self.tracker.historyLen


        # Safely pull the relevant trackedHistory from the tracker object
        trackHistory = []
        with self.workLock:
            trackHistory = self.tracker.trackedHistory[:numFrames]


        # Check if the object was recognized in the most recent frame. Check most recent frames first.
        for historyFromFrame in trackHistory:

            for tracked in historyFromFrame:
                if trackableObject.equalTo(tracked.target.view.name):
                    return True
        return False


    # vStream related functions
    def addTrackerFilter(self):
        self.vStream.addFilter(self.tracker.drawTracked)

    def endTrackerFilter(self):
        self.vStream.removeFilter(self.tracker.drawTracked)

    def trackerAddStartTrack(self, trackable):
        # Convenience function that adds an object to the tracker, starts the tracker, and starts the filter
        self.addTrackable(trackable)
        self.startTracker()
        self.addTrackerFilter()

    def trackerEndStopClear(self):
        # Convenience function to clear the tracked objects, stop tracking, and stop the tracking filter

        self.endTracker()
        self.endTrackerFilter()
        self.clearTargets()


    # General use computer vision functions
    def getMotion(self):

        # GET TWO CONSECUTIVE FRAMES
        frameList = self.vStream.getFrameList()
        if len(frameList) < 10:  # Make sure there are enough frames to do the motion comparison
            printf("getMovement():Not enough frames in self.vid.previousFrames")
            return 0  # IF PROGRAM IS RUN BEFORE THE PROGRAM HAS EVEN 10 FRAMES

        frame0 = frameList[0]
        frame1 = frameList[5]


        movementImg = cv2.absdiff(frame0, frame1)
        avgDifference = cv2.mean(movementImg)[0]

        return avgDifference

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


class PlaneTracker:
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
    Target  = namedtuple('PlaneTarget', 'view, keypoints, descrs')

    # target: the "sample" object of the tracked object. Center: [x,y,z] Rotation[xr, yr, zr], ptCount: matched pts
    TrackedTarget = namedtuple('TrackedTarget', 'view, target, quad, ptCount, center, rotation, p0, p1, H,')

    # Tracker parameters
    FLANN_INDEX_KDTREE = 1
    FLANN_INDEX_LSH    = 6
    MIN_MATCH_COUNT    = 10
    flanParams         = dict(algorithm         = FLANN_INDEX_LSH,
                              table_number      =               6,  # 12
                              key_size          =              12,  # 20
                              multi_probe_level =               1)  #  2


    def __init__(self, focalLength):
        self.focalLength  = focalLength
        self.detector     = cv2.ORB_create(nfeatures = 8500)
        self.matcher      = cv2.FlannBasedMatcher(self.flanParams, {})  # bug : need to pass empty dict (#1329)
        self.targets      = []
        self.framePoints  = []


        # trackHistory is an array of arrays, that keeps track of tracked objects in each frame, for hstLen # of frames
        # Format example [[PlanarTarget, PlanarTarget], [PlanarTarget], [PlanarTarget...]...]
        # Where trackedHistory[0] is the most recent frame, and trackedHistory[-1] is about to be deleted.
        self.historyLen = 30
        self.trackedHistory = [[] for i in range(self.historyLen)]



    def createTarget(self, view):
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
        target = self.Target(view=view, keypoints=points, descrs=descs)

        # If it was possible to add the target
        return target

    def addView(self, view):
        # This function checks if a view is currently being tracked, and if not it generates a target and adds it

        for target in self.targets:
            if view == target.view:
                printf("PlaneTracker.addTarget(): Rejected: Attempted to add two targets of the same name: ", view.name)
                return

        planarTarget = self.createTarget(view)

        descrs = planarTarget.descrs
        self.matcher.add([descrs])
        self.targets.append(planarTarget)


    def clear(self):
        # Remove all targets
        self.targets = []
        self.matcher.clear()

    def track(self, frame):
        # updates self.tracked with a list of detected TrackedTarget objects
        self.framePoints, frame_descrs = self.__detectFeatures(frame)

        tracked = []


        # If no keypoints were detected, then don't update the self.trackedHistory array
        if len(self.framePoints) < self.MIN_MATCH_COUNT:
            self.__addTracked(tracked)
            return


        matches = self.matcher.knnMatch(frame_descrs, k = 2)
        matches = [m[0] for m in matches if len(m) == 2 and m[0].distance < m[1].distance * 0.75]

        if len(matches) < self.MIN_MATCH_COUNT:
            self.__addTracked(tracked)
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


            # if target.pickupRect is not None:
            #     pickRect = target.pickupRect
            #     x0, y0, x1, y1 = x0 + pickRect[0], y0 + pickRect[1], x0 + pickRect[2], y0 + pickRect[3]
            #     pickupQuad = np.float32([[x0, y0], [x1, y0], [x1, y1], [x0, y1]])
            #     pickupQuad = cv2.perspectiveTransform(pickupQuad.reshape(1, -1, 2), H).reshape(-1, 2)
            # else:
            #     pickupQuad = None

            # Calculate the 3d coordinates of the object
            center, rotation = self.get3DCoordinates(frame, target.view.rect, quad)

            track = self.TrackedTarget(target=target,
                                       view=target.view,
                                       quad=quad,
                                       ptCount=len(matches),
                                       center=center,
                                       rotation=rotation,
                                       p0=p0, p1=p1, H=H,)
            tracked.append(track)


        tracked.sort(key = lambda t: len(t.p0), reverse=True)

        self.__addTracked(tracked)

    def __addTracked(self, trackedArray):
        # Add an array of detected objects to the self.trackedHistory array, and shorten the trackedHistory array
        # so that it always remains self.historyLength long
        start = time.time()


        self.trackedHistory.insert(0, trackedArray)

        while len(self.trackedHistory) > self.historyLen:
            del self.trackedHistory[-1]


    def __detectFeatures(self, frame):
        cv2.ocl.setUseOpenCL(False)  # THIS FIXES A ERROR BUG: "The data should normally be NULL!"

        # detect_features(self, frame) -> keypoints, descrs
        keypoints, descrs = self.detector.detectAndCompute(frame, None)
        if descrs is None:  # detectAndCompute returns descs=None if not keypoints found
            descrs = []
        return keypoints, descrs

    def drawTracked(self, frame):
        filterFnt   = cv2.FONT_HERSHEY_PLAIN
        filterColor = (255, 255, 255)

        for tracked in self.trackedHistory[0]:
            quad = np.int32(tracked.quad)
            cv2.polylines(frame, [quad], True, (255, 255, 255), 2)

            # Figure out how much the text should be scaled (depends on the different in curr side len, and orig len)
            rect          = tracked.view.rect
            origLength    = rect[2] - rect[0] + rect[3] - rect[1]
            currLength    = np.linalg.norm(quad[1] - quad[0]) + np.linalg.norm(quad[2] - quad[1])  # avg side len
            scaleFactor   = currLength / origLength

            # Draw the name of the object, and coordinates
            cv2.putText(frame, tracked.view.name, tuple(quad[1]),  filterFnt, scaleFactor, color=filterColor, thickness=1)

            # FOR DEUBGGING ONLY: TODO: Remove this when deploying final product
            try:
                coordText =  "X " + str(int(tracked.center[0])) + \
                            " Y " + str(int(tracked.center[1])) + \
                            " Z " + str(int(tracked.center[2])) + \
                            " R " + str(round(tracked.rotation[2], 2))
                cv2.putText(frame, coordText, (quad[1][0], quad[1][1] + int(15*scaleFactor)),  filterFnt, scaleFactor, color=filterColor, thickness=1)
            except:
                pass

            for (x, y) in np.int32(tracked.p1):
                cv2.circle(frame, (x, y), 2, (255, 255, 255))

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
        fx              = 0.5 + self.focalLength / 50.0
        dist_coef       = np.zeros(4)
        h, w            = frame.shape[:2]

        K = np.float64([[fx * w,      0, 0.5 * (w - 1)],
                        [     0, fx * w, 0.5 * (h - 1)],
                        [   0.0,    0.0,          1.0]])
        ret, rotation, center = cv2.solvePnP(quad3d, quad, K, dist_coef)
        return list(map(float,center)), list(map(float,rotation))



# def getMotionDirection(self):
    #     frameList = self.vStream.getFrameList()
    #
    #     frame0 = cv2.cvtColor(frameList[-1].copy(), cv2.COLOR_BGR2GRAY)
    #     frame1 = cv2.cvtColor(frameList[-2].copy(), cv2.COLOR_BGR2GRAY)
    #
    #     flow = cv2.calcOpticalFlowFarneback(frame1, frame0, 0.5,   1,  5,              1,             5,  5, 2)
    #
    #     avg = cv2.mean(flow)
    #     copyframe = frameList[-1].copy()
    #     cv2.line(copyframe, (320, 240), (int(avg[0] * 100 + 320), int(avg[1] * 100 + 240)), (0, 0, 255), 5)
    #     cv2.imshow("window", copyframe)
    #     cv2.waitKey(1)
    #     return avg



"""
# DEPRECATED VISION FUNCTIONS
    def getAverageObjectPosition(self, objectID, numFrames):
        # Finds the object in the latest numFrames from the tracking history, and returns the average pos and rot

        if numFrames >= self.tracker.historyLen:
            printf("Vision.getAverageObjectPosition(): ERROR: Tried to look further in the history than was possible!")
            numFrames = self.tracker.historyLen


        trackHistory = []
        with self.workLock:
            trackHistory = self.tracker.trackedHistory[:numFrames]

        # Set up variables
        samples       = 0
        locationSum   = np.float32([0, 0, 0])
        rotationSum   = np.float32([0, 0, 0])

        # Look through the history range and collect the object center and rotation
        for frameID, historyFromFrame in enumerate(trackHistory):

            for obj in historyFromFrame:

                if obj.target.name == objectID:
                    locationSum += np.float32(obj.center)
                    rotationSum += np.float32(obj.rotation)
                    samples     += 1

        # If object was not found, None will be returned for the frame and the object
        if samples == 0:
            return None, None

        return tuple(map(float, locationSum/samples)), tuple(map(float, rotationSum/samples))

"""