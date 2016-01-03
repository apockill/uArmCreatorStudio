import cv2
import time
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
        self.exitApp  = False
        self.cameraID = cameraID
        self.paused   = True
        self.frame    = None
        self.pixFrame = None  #Holds a QLabel formatted frame. Is calculated in the thread, and returned in getPixFrame
        self.cap      = None
        self.fps      = 24.0

        self.millis     = lambda: int(round(time.time() * 1000))  #Create function that gets current time in millis
        self.mainThread = None

    def main(self):
        #A main thread that focuses soley on grabbing frames from a camera, limited only by self.fps
        #Thread is created at startThread, which can be called by setPaused
        #Thread is ended only at endThread

        print "VideoStream.main():\t Starting videoStream thread."
        lastMillis = self.millis()
        while not self.exitApp:

            if self.paused: continue

            newMillis = self.millis()
            if newMillis - lastMillis >= (1 / self.fps) * 1000:
                lastMillis = newMillis

                ret, newFrame = self.cap.read()
                if ret:  #If a frame was successfully returned
                    self.frame = newFrame.copy()

                    #Create a pixMap from the new frame (for getPixFrame() method)
                    #Having this here means less processing work for the main program to do.
                    pixFrame = cv2.cvtColor(newFrame.copy(),
                                            cv2.cv.CV_BGR2RGB)
                    img      = QtGui.QImage(pixFrame, pixFrame.shape[1],
                                            pixFrame.shape[0], QtGui.QImage.Format_RGB888)
                    pix      = QtGui.QPixmap.fromImage(img)
                    self.pixFrame = pix

                else:
                    print "VideoStream.main():\t ERROR while reading frame from Camera: ", self.cameraID
                    self.setNewCamera(self.cameraID)
                    cv2.waitKey(1000)


        print "VideoStream.main():\t Ending videoStream thread"


    def setPaused(self, value):
        #Tells the main frunction to grab more frames
        if value is False:  #If you want to play video
            if self.cap is None:
                self.setNewCamera(self.cameraID)
            if self.mainThread is None:
                self.startThread()

        self.paused = value


    def startThread(self):
        if self.mainThread is None:
            self.mainThread = Thread(target=self.main)
            self.mainThread.start()
        else:
            print "VideoStream.startThread(): ERROR: Tried to create mainThread, but mainThread already existed."

    def endThread(self):
        self.exitApp = True

        if self.mainThread is not None:
            self.mainThread.join(1000)
            self.mainThread = None

        if self.cap is not None:
            self.cap.release()


    def setNewCamera(self, cameraID):
        #Set or change the current camera to a new one
        print "VideoStream.setNewCamera():\t Setting camera to cameraID ", cameraID
        paused = self.paused
        self.setPaused(True)  #Make sure cap won't be called in the main thread while releasing the cap

        if self.cap is not None: self.cap.release()  #Gracefully close the current capture

        self.cameraID = cameraID
        self.cap = cv2.VideoCapture(self.cameraID)

        if not self.cap.isOpened():
            print "VideoStream.setNewCamera():\t ERROR: Camera not opened. cam ID: ", cameraID
            return False

        self.setPaused(paused)  #Return to whatever state the camera was in before switching
        print "done"
        return True


    def setFPS(self, fps):
        #Sets how often the main function grabs frames (Default: 24)
        self.fps = fps


    def getFrame(self):
        #Returns the latest frame grabbed from the camera
        return self.frame

    def getPixFrame(self):
        #Returns the latest frame grabbed from the camera, modified to be put in a QLabel
        return self.pixFrame


class Vision:
    def __init__(self, vStream):

        pass

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
        self.getFrame = getFrameFunction
        self.fps      = 24     #The maximum FPS the camera will
        self.paused   = True   #Keeps track of the video's state
        self.timer    = None

        #Initialize the UI
        self.initUI()

        #Get one frame and display it, and wait for play to be pressed
        self.nextFrameSlot()

    def initUI(self):
        self.video_frame = QtGui.QLabel("ERROR: Could not open camera.")  #Temp label for the frame
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

