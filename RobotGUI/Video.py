import cv2
import time
import numpy as np
import Global
from PyQt4 import QtGui, QtCore
from threading import Thread


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
    def __init__(self, cameraID):
        self.running    = False
        self.cameraID   = cameraID
        self.paused     = True
        self.frame      = None
        self.frameList  = []
        self.frameCount = 0     #Used in waitForNewFrame()
        self.pixFrame   = None  #Holds a QLabel formatted frame. Is calculated in the thread, and returned in getPixFrame
        self.cap        = None
        self.fps        = 24.0
        self.dimensions = None  #Will be [x dimension, y dimension]

        self.millis     = lambda: int(round(time.time() * 1000))  #Create function that gets current time in millis
        self.mainThread = None

    def setPaused(self, value):
        #Tells the main frunction to grab more frames
        if value is False:  #If you want to play video
            if self.cap is None:
                self.setNewCamera(self.cameraID)
            if self.mainThread is None:
                self.startThread()

        self.paused = value


    def videoThread(self):
        #A main thread that focuses soley on grabbing frames from a camera, limited only by self.fps
        #Thread is created at startThread, which can be called by setPaused
        #Thread is ended only at endThread

        self.frame     = None
        self.frameList = []

        print "VideoStream.main():\t Starting videoStream thread."
        lastMillis = self.millis()
        while not self.running:

            if self.paused: continue

            newMillis = self.millis()
            if newMillis - lastMillis >= (1 / self.fps) * 1000:
                lastMillis = newMillis

                #Get a new frame
                ret, newFrame = self.cap.read()


                #If a frame was successfully returned
                if ret:
                    self.frame = newFrame.copy()

                    #Add a frame to the frameList that records the 5 latest frames for Vision uses
                    self.frameList.append(self.frame)
                    while len(self.frameList) > 5:
                        del self.frameList[0]

                    #Create a pixMap from the new frame (for getPixFrame() method)
                    #Having this here means less processing work for the main program to do.
                    #TODO: Research if running a QtGui process in a thread will cause crashes
                    pixFrame = cv2.cvtColor(newFrame.copy(),
                                            cv2.cv.CV_BGR2RGB)
                    img      = QtGui.QImage(pixFrame, pixFrame.shape[1],
                                            pixFrame.shape[0], QtGui.QImage.Format_RGB888)
                    pix      = QtGui.QPixmap.fromImage(img)
                    self.pixFrame = pix


                    #Keep track of new frames by counting them. (100 is an arbitrary number)
                    if self.frameCount >= 100:
                        self.frameCount = 0
                    else:
                        self.frameCount += 1

                else:
                    print "VideoStream.main():\t ERROR while reading frame from Camera: ", self.cameraID
                    self.setNewCamera(self.cameraID)
                    cv2.waitKey(1000)


        print "VideoStream.main():\t Ending videoStream thread"

    def startThread(self):
        if self.mainThread is None:
            self.mainThread = Thread(target=self.videoThread)
            self.mainThread.start()
        else:
            print "VideoStream.startThread():\t ERROR: Tried to create mainThread, but mainThread already existed."

    def endThread(self):
        self.running = True

        if self.mainThread is not None:
            self.mainThread.join(1000)
            self.mainThread = None

        if self.cap is not None:
            self.cap.release()


    def setNewCamera(self, cameraID):
        #Set or change the current camera to a new one
        print "VideoStream.setNewCamera():\t Setting camera to cameraID ", cameraID
        previousState = self.paused  #When the function is over it will set the camera to its previous state

        self.setPaused(True)  #Make sure cap won't be called in the main thread while releasing the cap

        if self.cap is not None: self.cap.release()  #Gracefully close the current capture

        self.cameraID = cameraID
        self.cap = cv2.VideoCapture(self.cameraID)

        if not self.cap.isOpened():
            print "VideoStream.setNewCamera():\t ERROR: Camera not opened. cam ID: ", cameraID
            self.dimensions = None
            return False


        #Try getting a frame and setting self.dimensions. If it does not work, return false
        ret, frame = self.cap.read()
        if ret:
            self.dimensions = [frame.shape[1], frame.shape[0]]
            print "dimensions", self.dimensions
        else:
            print "VideoStream.setNewCamera():\t ERROR ERROR: Camera could not read frame. cam ID: ", cameraID
            self.dimensions = None
            return False


        self.setPaused(previousState)  #Return to whatever state the camera was in before switching
        return True

    def setFPS(self, fps):
        #Sets how often the main function grabs frames (Default: 24)
        self.fps = fps


    def getFrame(self):
        #Returns the latest frame grabbed from the camera
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
        #Returns the latest frame grabbed from the camera, modified to be put in a QLabel
        return self.pixFrame

    def waitForNewFrame(self):
        lastFrame = self.frameCount
        while self.frameCount == lastFrame: pass


class Vision:
    def __init__(self, vStream):
        self.vStream = vStream

    def getMotion(self):
        #GET TWO CONSECUTIVE FRAMES
        frameList = self.vStream.getFrameList()
        if len(frameList) < 5:  #Make sure there are enough frames to do the motion comparison
            print "getMovement():\tNot enough frames in self.vid.previousFrames"
            return 0    #IF PROGRAM IS RUN BEFORE THE PROGRAM HAS EVEN 10 FRAMES

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
        #Get the average color of a rectangle in the main frame. If no rect specified, get the whole frame
        p1 = kwargs.get("p1", None)
        p2 = kwargs.get("p2", None)

        frame = self.vStream.getFrame()
        if p1 is not None and p2 is not None:
            frame = frame[p2[1]:p1[1], p2[0]:p1[0]]


        averageColor = cv2.mean(frame)       #RGB
        return averageColor


    def findObjectColor(self, hue, tolerance, lowSat, highSat, lowVal, highVal):
        low, high = self.getRange(hue, tolerance)

        hue         = int(hue)
        tolerance   = int(tolerance)
        lowSat      = int( lowSat * 255)
        highSat     = int(highSat * 255)
        lowVal      = int( lowVal * 255)
        highVal     = int(highVal * 255)

        frame       = self.vStream.getFrame()
        hsv         = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)


        if hue - tolerance < 0 or hue + tolerance > 180:
            #If the color crosses 0, you have to do two thresholds
            lowThresh   = cv2.inRange(hsv,    np.array((0, lowSat, lowVal)), np.array((low, highSat, highVal)))
            upperThresh = cv2.inRange(hsv, np.array((high, lowSat, lowVal)), np.array((180, highSat, highVal)))
            finalThresh = upperThresh + lowThresh
        else:
            finalThresh  = cv2.inRange(hsv, np.array((low, lowSat, lowVal)), np.array((high, highSat, highVal)))

        contours, hierarchy = cv2.findContours(finalThresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        cv2.imshow("frame", finalThresh)
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
            #cv2.circle(frame, (cx, cy), 5, 255, -1)
            return [cx, cy]
        return None


    def getRange(self, hue, tolerance):
        #Input an HSV, get a range
        low  = hue - tolerance / 2
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





########## WIDGETS ##########
class CameraWidget(QtGui.QWidget):
    def __init__(self, getFrameFunction):
        """
        :param cameraID:
        :param getFrameFunction: A function that when called will return a frame
                that can be put in a QLabel. In this case the frame will come from
                a VideoStream object's getFrame function.
        :return:
        """
        super(CameraWidget, self).__init__()

        #Set up globals
        self.getFrame = getFrameFunction  #This function is given as a parameters, and returns a frame
        self.fps      = 24     #The maximum FPS the camera will
        self.paused   = True   #Keeps track of the video's state
        self.timer    = None

        #Initialize the UI
        self.initUI()

        #Get one frame and display it, and wait for play to be pressed
        self.nextFrameSlot()

    def initUI(self):
        #self.setMinimumWidth(640)
        #self.setMinimumHeight(480)
        self.video_frame = QtGui.QLabel("No camera data.")  #Temp label for the frame
        self.vbox        = QtGui.QVBoxLayout(self)
        self.vbox.addWidget(self.video_frame)
        self.setLayout(self.vbox)

    def play(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.nextFrameSlot)
        self.timer.start(1000./self.fps)

        self.paused = False

    def pause(self):
        if self.timer is not None: self.timer.stop()
        self.paused = True

    def nextFrameSlot(self):

        pixFrame = self.getFrame()

        #If a frame was returned correctly
        if pixFrame is None:
            return

        self.video_frame.setPixmap(pixFrame)

