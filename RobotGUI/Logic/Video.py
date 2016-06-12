import cv2
import numpy as np
from threading             import Thread
from PyQt5.QtGui           import QImage, QPixmap  # Used once in VideoStream class to preprocess GUI stuff in thread
from RobotGUI.Logic.Global import printf, FpsTimer


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
    def __init__(self, cameraID, fps=24):
        self.running    = False
        self.paused     = True

        self.cameraID   = cameraID
        self.fps        = fps
        self.cap        = None  # An OpenCV capture object
        self.dimensions = None  # Will be [x dimension, y dimension]


        self.frame = None
        self.pixFrame = None  # Holds a QLabel formatted frame. Is calculated in the thread, and returned in getPixFrame

        self.frameList = []
        self.frameCount = 0  # Used in waitForNewFrame()

        self.mainThread = None

    def setPaused(self, value):
        # Tells the main frunction to grab more frames

        if value is False:  # If you want to play video, make sure everything set for that to occur
            if not self.connected:
                self.setNewCamera(self.cameraID)

            if self.mainThread is None:
                self.startThread()

        self.paused = value


    def videoThread(self):
        # A main thread that focuses soley on grabbing frames from a camera, limited only by self.fps
        # Thread is created at startThread, which can be called by setPaused
        # Thread is ended only at endThread

        self.frame = None
        self.frameList = []
        fpsTimer = FpsTimer(self.fps)
        printf("VideoStream.main(): Starting videoStream thread.")

        while not self.running:
            fpsTimer.wait()
            if not fpsTimer.ready() or self.paused: continue

            # Get a new frame
            ret, newFrame = self.cap.read()

            # If a frame was successfully returned
            if ret:
                self.frame = newFrame.copy()

                # Add a frame to the frameList that records the 5 latest frames for Vision uses
                self.frameList.append(self.frame)
                while len(self.frameList) > 5:
                    del self.frameList[0]

                # Create a pixMap from the new frame (for getPixFrame() method)
                # Having this here means less processing work for the main program to do.
                # TODO: Research if running a QtGui process in a thread will cause crashes
                pixFrame = cv2.cvtColor(newFrame.copy(), cv2.COLOR_BGR2RGB)

                img = QImage(pixFrame, pixFrame.shape[1], pixFrame.shape[0], QImage.Format_RGB888)
                pix = QPixmap.fromImage(img)
                self.pixFrame = pix

                # Keep track of new frames by counting them. (100 is an arbitrary number)
                if self.frameCount >= 100:
                    self.frameCount = 0
                else:
                    self.frameCount += 1

            else:
                printf("VideoStream.main(): ERROR while reading frame from Camera: ", self.cameraID)
                self.setNewCamera(self.cameraID)
                cv2.waitKey(1000)

        printf("VideoStream.main(): Ending videoStream thread")

    def startThread(self):
        if self.mainThread is None:
            self.mainThread = Thread(target=self.videoThread)
            self.mainThread.start()
        else:
            printf("VideoStream.startThread(): ERROR: Tried to create mainThread, but mainThread already existed.")

    def endThread(self):
        self.running = True

        if self.mainThread is not None:
            self.mainThread.join(1000)
            self.mainThread = None

        if self.cap is not None:
            self.cap.release()


    def connected(self):
        # Returns True or False if there is a camera successfully connected
        if self.cap is None:        return False
        if not self.cap.isOpened(): return False
        return True

    def setNewCamera(self, cameraID):
        # Set or change the current camera to a new one
        printf("VideoStream.setNewCamera(): Setting camera to cameraID ", cameraID)

        # When the function is over it will set the camera to its previous state (playing or paused)
        previousState = self.paused

        # Make sure cap won't be called in the main thread while releasing the cap
        self.setPaused(True)

        # Gracefully close the current capture if it exists
        if self.cap is not None: self.cap.release()

        # Set the new cameraID and open the capture
        self.cameraID = cameraID
        self.cap = cv2.VideoCapture(self.cameraID)

        if not self.cap.isOpened():
            printf("VideoStream.setNewCamera(): ERROR: Camera not opened. cam ID: ", cameraID)
            self.dimensions = None
            return False

        # Try getting a frame and setting self.dimensions. If it does not work, return false
        ret, frame = self.cap.read()
        if ret:
            self.dimensions = [frame.shape[1], frame.shape[0]]

        else:
            printf("VideoStream.setNewCamera(): ERROR ERROR: Camera could not read frame. cam ID: ", cameraID)
            self.dimensions = None
            return False

        self.setPaused(previousState)  # Return to whatever state the camera was in before switching
        return True

    def setFPS(self, fps):
        # Sets how often the main function grabs frames (Default: 24)
        self.fps = fps


    def getFrame(self):
        # Returns the latest frame grabbed from the camera
        if self.frame is not None:
            return self.frame.copy()
        else:
            return None

    def getFrameList(self):
        """
        Returns a list of the last x frames
        This is used in functions like Vision.getMotion() where frames are compared
        with past frames
        """
        return self.frameList[:]

    def getPixFrame(self):
        # Returns the latest frame grabbed from the camera, modified to be put in a QLabel
        return self.pixFrame


    def waitForNewFrame(self):
        lastFrame = self.frameCount
        while self.frameCount == lastFrame: pass


class Vision:
    def __init__(self, vStream):
        self.vStream = vStream

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

    def getColor(self, **kwargs):
        # Get the average color of a rectangle in the main frame. If no rect specified, get the whole frame
        p1 = kwargs.get("p1", None)
        p2 = kwargs.get("p2", None)

        frame = self.vStream.getFrame()
        if p1 is not None and p2 is not None:
            frame = frame[p2[1]:p1[1], p2[0]:p1[0]]

        averageColor = cv2.mean(frame)  # RGB
        return averageColor

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

    def cameraConnected(self):
        if self.vStream.mainThread is None:
            return False
        return True


