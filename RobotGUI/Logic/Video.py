import cv2
import numpy as np
from threading             import Thread, RLock
from RobotGUI.Logic.Global import printf, FpsTimer
from collections           import namedtuple


def getConnectedCameras():
    tries = 10
    cameraList = []

    for i in range(0, tries):
        testCap = cv2.VideoCapture(i)

        if testCap.isOpened():
            cameraList.append(i)
            testCap.release()

    return cameraList



class VideoStream:
    """
    VideoStream is a threaded video-getter that doubles as a processing unit for repetative computer vision tasks.
    Some computer vision tasks require real-time tracking and fast results. With this system, you can add "tasks"
    for the VideoStream to complete.

    For example, if you are tracking objects, an "objectTracker" filter will be added to the VideoStream

    Repetative tasks include:
        - Adding filters to videoStreams (like contours, keypoints, or outlining tracked objects)
        - Getting tracked objects
    """

    def __init__(self, fps=24):
        self.frameLock   = RLock()  # Lock for any frame get/copy/read operations
        self.filterLock  = RLock()  # Lock for any filtering operations, added under self.addFilter()
        self.workLock    = RLock()  # Lock for any "Work" functions, added under self.addWork()

        self.running     = False
        self.setCamera   = None     # When this is a number and videoThread is on, it will attempt to setNewCamera(new)
        self.paused      = True

        self.cameraID    = None
        self.fps         = fps
        self.cap         = None  # An OpenCV capture object
        self.dimensions  = None  # Will be [x dimension, y dimension]


        self.frame       = None
        self.frameList   = []    # Used in computer vision tasks, this is a list of the last 5 frames (unfiltered)
        self.frameCount  = 0     # Used in waitForNewFrame()

        self.filterFrame = None  # A frame that has gone under all the filters in the self.filters list
        self.filterList  = []    # A list of functions that all input a frame and output a modified frame.
        self.workList    = []    # A list of functions that all input a frame, but don't output anything.

        self.mainThread  = None


    def setNewCamera(self, cameraID):
        # Activate a trigger in the mainThread to turn on the camera
        # Connecting to camera is run inside the thread because it's a lengthy process (over 1 second)
        # This would lock up the GUI
        self.setCamera = cameraID

    def setPaused(self, value):
        # Tells the main frunction to grab more frames
        if value is False:  # If you want to play video, make sure everything set for that to occur
            # if not self.connected():
            #     self.setNewCamera(self.cameraID)

            if self.mainThread is None:
                self.startThread()

        self.paused = value

    def connected(self):
        # Returns True or False if there is a camera successfully connected
        if self.cap is None:        return False
        if not self.cap.isOpened(): return False
        return True

    def setFPS(self, fps):
        # Sets how often the main function grabs frames (Default: 24)
        self.fps = fps


    def startThread(self):
        if self.mainThread is None:
            self.running = True
            self.mainThread = Thread(target=self.__videoThread)
            self.mainThread.start()
        else:
            printf("VideoStream.startThread(): ERROR: Tried to create mainThread, but mainThread already existed.")

    def endThread(self):
        self.running = False

        if self.mainThread is not None:
            printf("VideoStream.endThread(): Ending main thread")
            self.mainThread.join(500)
            self.mainThread = None

        if self.cap is not None:
            printf("VideoStream.endThread(): Thread ended. Now gracefully closing Cap")
            self.cap.release()

    def __videoThread(self):
        """"
            A main thread that focuses soley on grabbing frames from a camera, limited only by self.fps
            Thread is created at startThread, which can be called by setPaused
            Thread is ended only at endThread
        """

        self.frameList = []

        fpsTimer = FpsTimer(self.fps)
        printf("VideoStream.videoThread(): Starting videoStream thread.")
        while self.running:
            fpsTimer.wait()
            if not fpsTimer.ready():       continue
            if self.setCamera is not None: self.__setNewCamera(self.setCamera)
            if self.paused:                continue
            if self.cap is None:           continue


            # Get a new frame
            ret, newFrame = self.cap.read()

            if not ret:  # If a frame was not successfully returned
                printf("VideoStream.videoThread(): ERROR while reading frame from Camera: ", self.cameraID)
                self.__setNewCamera(self.cameraID)
                cv2.waitKey(1000)
                continue


            # Do frame related work
            with self.frameLock:
                self.frame = newFrame

                # Add a frame to the frameList that records the 5 latest frames for Vision uses
                self.frameList.append(self.frame.copy())
                while len(self.frameList) > 5:
                    del self.frameList[0]

                # Keep track of new frames by counting them. (100 is an arbitrary number)
                if self.frameCount >= 100:
                    self.frameCount = 0
                else:
                    self.frameCount += 1


            # Run any work functions that must be run. Expect no results. Work should be run before filters.
            if len(self.workList) > 0:
                with self.workLock:
                    for workFunc in self.workList:
                        workFunc(self.frame)



            # Run any filters that must be run, save the results in self.filterFrame
            if len(self.filterList) > 0:
                with self.filterLock:
                    filterFrame = self.getFrame()
                    for filterFunc in self.filterList:
                        filterFrame = filterFunc(filterFrame)
                    self.filterFrame = filterFrame
            else:
                self.filterFrame = self.frame



        printf("VideoStream.videoThread(): VideoStream Thread has ended")

    def __setNewCamera(self, cameraID):
        self.setCamera = None


        # Set or change the current camera to a new one
        printf("VideoStream.setNewCamera(): Setting camera to cameraID ", cameraID)


        # Gracefully close the current capture if it exists
        if self.cap is not None: self.cap.release()


        # Set the new cameraID and open the capture
        self.cap = cv2.VideoCapture(cameraID)


        # Check if the cap was opened correctly
        if not self.cap.isOpened():
            printf("VideoStream.setNewCamera(): ERROR: Camera not opened. cam ID: ", cameraID)
            self.cap.release()
            self.dimensions = None
            self.cap        = None
            return False


        # Try getting a frame and setting self.dimensions. If it does not work, return false
        ret, frame = self.cap.read()
        if ret:
            self.dimensions = [frame.shape[1], frame.shape[0]]
        else:
            printf("VideoStream.setNewCamera(): ERROR ERROR: Camera could not read frame. cam ID: ", cameraID)
            self.cap.release()
            self.dimensions = None
            self.cap        = None
            return False

        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 10)

        # Since everything worked, save the new cameraID
        self.cameraID = cameraID
        return True


    # Called from outside thread
    def getFrame(self):
        # Returns the latest frame grabbed from the camera
        # with self.frameLock:
        if self.frame is not None:
            return self.frame.copy()
        else:
            return None

    def getFilteredWithID(self):
        # with self.frameLock:
        if self.filterFrame is not None:
            # Frames are copied because they are generally modified.
            return self.frameCount, self.filterFrame.copy()
        else:
            return None, None

    def getFrameList(self):
        """
        Returns a list of the last x frames
        This is used in functions like Vision.getMotion() where frames are compared
        with past frames
        """
        with self.frameLock:
            return list(self.frameList)



    def addFilter(self, filterFunc):
        # Add a filter to put on top of the self.filteredFrame each round
        with self.filterLock:
            if filterFunc in self.filterList:
                printf("VideoStream.addFilter(): ERROR: Tried to add work function that already existed: ", filterFunc)
                return

            self.filterList.append(filterFunc)

    def addWork(self, workFunc):
        # Add some function that has to be run each round. Processing is done after frame get, but before filtering.
        with self.workLock:
            if workFunc in self.workList:
                printf("VideoStream.addWork(): ERROR: Tried to add work function that already existed: ", workFunc)
                return

            self.workList.append(workFunc)

    def removeWork(self, workFunc):
        # Remove a function from the workList

        with self.workLock:
            # Make sure the function is actually in the workList
            if workFunc not in self.workList:
                printf("VideoStream.addWork(): ERROR: Tried to remove a work function that didn't exist: ", workFunc)
                return

            self.workList.remove(workFunc)

    def removeFilter(self, filterFunc):
        with self.filterLock:
            # Make sure the function is actually in the workList
            if filterFunc not in self.filterList:
                printf("VideoStream.addFilter(): ERROR: Tried to remove a nonexistent filter: ", filterFunc)
                return

            self.filterList.remove(filterFunc)

    def waitForNewFrame(self):
        lastFrame = self.frameCount
        while self.frameCount == lastFrame: pass



class Vision:

    def __init__(self, vStream):

        self.vStream    = vStream
        self.tracker    = PlaneTracker()

        # Use these on any work functions that are intended for threading
        self.filterLock = self.vStream.filterLock
        self.workLock   = self.vStream.workLock




    # Tracker related functions
    def getTarget(self, image, rect, name=None, pickupRect=None):
        # Interfaces with the tracker, using workLocks for safety
        with self.workLock:
            target = self.tracker.getTarget(image, rect, name, pickupRect)
        return target

    def addTarget(self, planarTarget):
        with self.workLock:
            self.tracker.addTarget(planarTarget)

    def clearTargets(self):
        with self.workLock:
            self.tracker.clear()

    def startTracker(self):
        # Adds a worker function to the videoStream to track all the time
        self.vStream.addWork(self.tracker.track)

    def endTracker(self):
        # Removes a worker function from the videoStream, to stop any ongoing tracking
        self.vStream.removeWork(self.tracker.track)


    # vStream related functions
    def addTrackerFilter(self):
        self.vStream.addFilter(self.tracker.drawTracked)

    def endTrackerFilter(self):
        self.vStream.removeFilter(self.tracker.drawTracked)

    def trackerAddStartTrack(self, planarTarget):
        # Convenience function that adds an object to the tracker, starts the tracker, and starts the filter
        self.addTarget(planarTarget)
        self.startTracker()
        self.addTrackerFilter()

    def trackerEndStopClear(self):
        # Convenience function to clear the tracked objects, stop tracking, and stop the tracking filter

        self.endTracker()
        self.endTrackerFilter()
        self.clearTargets()

    # Useful computer vision functions
    def getMotion(self):

        # GET TWO CONSECUTIVE FRAMES
        frameList = self.vStream.getFrameList()
        if len(frameList) < 5:  # Make sure there are enough frames to do the motion comparison
            printf("getMovement():Not enough frames in self.vid.previousFrames")
            return 0  # IF PROGRAM IS RUN BEFORE THE PROGRAM HAS EVEN 10 FRAMES

        frame0 = frameList[len(frameList) - 1]
        frame1 = frameList[len(frameList) - 3]
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

    def resizeToMax(self, image, maxWidth, maxHeight):
        # Makes sure an image is within the bounds of maxHeight and maxWidth, and resizes to make sure

        height, width, _ = image.shape

        if height > maxHeight:
            image = cv2.resize(image, (int(float(maxHeight)/height*width), maxHeight))

        height, width, _ = image.shape

        if width > maxWidth:
            image = cv2.resize(image, (maxWidth, int(float(maxWidth)/width*height)))

        height, width, _ = image.shape

        return image



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
    PlanarTarget  = namedtuple(  'PlaneTarget',   'name, image, rect, pickupRect, keypoints, descrs')
    TrackedTarget = namedtuple('TrackedTarget', 'target,    p0,   p1,         H,   quad')

    # Tracker parameters
    FLANN_INDEX_KDTREE = 1
    FLANN_INDEX_LSH    = 6
    MIN_MATCH_COUNT    = 10
    flanParams         = dict(algorithm         = FLANN_INDEX_LSH,
                              table_number      =               6,  # 12
                              key_size          =              12,  # 20
                              multi_probe_level =               1)  #  2


    def __init__(self):
        self.detector     = cv2.ORB_create(nfeatures = 1000)
        self.matcher      = cv2.FlannBasedMatcher(self.flanParams, {})  # bug : need to pass empty dict (#1329)
        self.targets      = []
        self.framePoints  = []

        self.tracked      = []

    def getTarget(self, image, rect, name=None, pickupRect=None):
        # Get the PlanarTarget object for any name, image, and rect. These can be added in self.addTarget()
        x0, y0, x1, y1         = rect
        points, descs          = [], []

        raw_points, raw_descrs = self.detectFeatures(image)

        for kp, desc in zip(raw_points, raw_descrs):
            x, y = kp.pt
            if x0 <= x <= x1 and y0 <= y <= y1:
                points.append(kp)
                descs.append(desc)


        descs  = np.uint8(descs)
        target = self.PlanarTarget(name=name, image = image, rect=rect, pickupRect=pickupRect,
                                   keypoints = points, descrs=descs)

        # If it was possible to add the target
        return target

    def addTarget(self, planarTarget):
        descrs = planarTarget.descrs
        self.matcher.add([descrs])
        self.targets.append(planarTarget)


    def clear(self):
        # Remove all targets
        self.targets = []
        self.matcher.clear()

    def track(self, frame):
        # updates self.tracked with a list of detected TrackedTarget objects

        self.framePoints, frame_descrs = self.detectFeatures(frame)


        # If no keypoints were detected, then don't update the self.tracked array
        if len(self.framePoints) < self.MIN_MATCH_COUNT:
            self.tracked = []
            return


        matches = self.matcher.knnMatch(frame_descrs, k = 2)
        matches = [m[0] for m in matches if len(m) == 2 and m[0].distance < m[1].distance * 0.75]
        if len(matches) < self.MIN_MATCH_COUNT:
            self.tracked = []
            return


        matches_by_id = [[] for _ in range(len(self.targets))]
        for m in matches: matches_by_id[m.imgIdx].append(m)


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

            x0, y0, x1, y1 = target.rect
            quad = np.float32([[x0, y0], [x1, y0], [x1, y1], [x0, y1]])
            quad = cv2.perspectiveTransform(quad.reshape(1, -1, 2), H).reshape(-1, 2)

            track = self.TrackedTarget(target=target, p0=p0, p1=p1, H=H, quad=quad)
            tracked.append(track)


        tracked.sort(key = lambda t: len(t.p0), reverse=True)

        self.tracked = tracked

    def detectFeatures(self, frame):
        cv2.ocl.setUseOpenCL(False)  # THIS FIXES A ERROR BUG: "The data should normally be NULL!"

        # detect_features(self, frame) -> keypoints, descrs
        keypoints, descrs = self.detector.detectAndCompute(frame, None)
        if descrs is None:  # detectAndCompute returns descs=None if not keypoints found
            descrs = []
        return keypoints, descrs

    def drawTracked(self, frame):
        for tr in self.tracked:
            cv2.polylines(frame, [np.int32(tr.quad)], True, (255, 255, 255), 2)

            for (x, y) in np.int32(tr.p1):
                cv2.circle(frame, (x, y), 2, (255, 255, 255))

        return frame

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

