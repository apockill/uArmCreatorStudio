import cv2
import time
from PyQt4 import QtGui
from threading import Thread


def getConnectedCameras():
    tries = 10
    cameraList = []

    for i in range(0, tries):
        print "getting ",i
        testCap = cv2.VideoCapture(i)
        print "got ",i


        if testCap.isOpened():
            print "releasing ", i
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

        self.millis     = lambda: int(round(time.time() * 1000))  #Get current time in millis
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
            self.mainThread = Thread(target = self.main)
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
        paused = self.paused
        self.setPaused(True)  #Make sure cap won't be called in the main thread while releasing the cap

        if self.cap is not None: self.cap.release()  #Gracefully close the current capture

        self.cameraID = cameraID
        self.cap = cv2.VideoCapture(self.cameraID)

        if not self.cap.isOpened():
            print "VideoStream.setNewCamera():\t ERROR: Camera not opened. cam ID: ", cameraID

        self.setPaused(paused)  #Return to whatever state the camera was in before switching

    def setFPS(self, fps):
        #Sets how often the main function grabs frames (Default: 24)
        self.fps = fps


    def getFrame(self):
        #Returns the latest frame grabbed from the camera
        return self.frame

    def getPixFrame(self):
        #Returns the latest frame grabbed from the camera, modified to be put in a QLabel
        return self.pixFrame




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

