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
import cv2
from time         import time
from threading    import Thread, RLock
from Logic.Global import printf, FpsTimer
__author__ = "Alexander Thiel"


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

        self.cameraID    = None
        self.fps         = fps
        self.cap         = None  # An OpenCV capture object

        self.frame       = None
        self.frameList   = []    # Used in computer vision tasks, this is a list of the last 5 frames (unfiltered)
        self.frameCount  = 0     # Used in waitForNewFrame()

        self.filterFrame = None  # A frame that has gone under all the filters in the self.filters list
        self.filterList  = []    # A list of functions that all input a frame and output a modified frame.
        self.workList    = []    # A list of functions that all input a frame, but don't output anything.

        self.mainThread  = None


    def setNewCamera(self, cameraID):
        """
            Activate a trigger in the mainThread to turn on the camera
            Connecting to camera is run inside the thread because it's a lengthy process (over 1 second)
            This would lock up the GUI
        """

        # Make sure the mainThread is running, so that this trigger will work
        if self.setCamera is None:
            self.startThread()
            self.setCamera = cameraID
        else:
            printf("Video| ERROR: Tried to set camera while camera was already being set! cameraID ", self.setCamera)

    def connected(self):
        # Returns True or False if there is a camera successfully connected
        if self.cap is None:        return False
        return True

    def setFPS(self, fps):
        # Sets how often the main function grabs frames (Default: 24)
        self.fps = fps


    def startThread(self):
        if self.mainThread is None:
            self.running = True
            self.mainThread = Thread(target=self.__videoThread)  # Cannot be Daemon thread
            self.mainThread.start()
        else:
            printf("Video| Tried to create mainThread, but mainThread already existed.")

    def endThread(self):
        self.running = False




    def __videoThread(self):
        """"
            A main thread that focuses soley on grabbing frames from a camera, limited only by self.fps
            Thread is created at startThread, which can be called by setPaused
            Thread is ended only at endThread
        """


        self.frameList = []

        fpsTimer = FpsTimer(self.fps)
        printf("Video| Starting videoStream thread.")

        while self.running:
            fpsTimer.wait()
            if not fpsTimer.ready():       continue
            if self.setCamera is not None: self.__setNewCamera(self.setCamera)
            if self.cap is None:           continue


            # Get a new frame
            ret, newFrame = self.cap.read()

            if not ret:  # If a frame was not successfully returned
                printf("Video| ERROR: while reading frame from Cam. Setting camera again...")
                self.__setNewCamera(self.cameraID)
                cv2.waitKey(1000)
                continue


            # Do frame related work
            with self.frameLock:
                self.frame = newFrame

                # Add a frame to the frameList that records the 5 latest frames for Vision uses
                self.frameList.insert(0, self.frame.copy())

                while len(self.frameList) > 10:
                    del self.frameList[-1]

                # Keep track of new frames by counting them. (100 is an arbitrary number)
                if self.frameCount >= 100:
                    self.frameCount = 0
                else:
                    self.frameCount += 1


            # Run any work functions that must be run. Expect no results. Work should be run before filters.
            if len(self.workList) > 0:
                # print("Work: ", self.workList)
                with self.workLock:
                    for workFunc in self.workList:
                        workFunc(self.frame)



            # Run any filters that must be run, save the results in self.filterFrame
            if len(self.filterList) > 0:
                # print("Filters: ", self.filterList)
                with self.filterLock:
                    filterFrame = self.frame.copy()
                    for filterFunc in self.filterList:
                        filterFrame = filterFunc(filterFrame)

                    # Draw FPS on the screen
                    fps = str(int(round(fpsTimer.currentFPS, 0)))
                    cv2.putText(filterFrame, fps, (10, 20),  cv2.FONT_HERSHEY_PLAIN, 1.25, (255, 255, 255), 2)

                    self.filterFrame = filterFrame
            else:
                self.filterFrame = self.frame

        if self.cap is not None:
            self.cap.release()
        self.mainThread = None


    # Run inside VideoThread only
    def __setNewCamera(self, cameraID):
        # Set or change the current camera to a new one
        printf("Video| Setting camera to cameraID ", cameraID)

        # Gracefully close the current capture if it exists
        if self.cap is not None: self.cap.release()


        # Set the new cameraID and open the capture
        self.cap = cv2.VideoCapture(cameraID)


        # Check if the cap was opened correctly
        if not self.cap.isOpened():
            printf("Video| ERROR: Camera not opened. cam ID: ", cameraID)
            self.cap.release()
            self.cap        = None
            self.setCamera  = None
            return False


        # Try getting a frame
        ret, frame = self.cap.read()
        if not ret:
            printf("Video| ERROR: Camera could not read frame. cam ID: ", cameraID)
            self.cap.release()
            self.cap        = None
            self.setCamera  = None
            return False

        # Since everything worked, save the new cameraID
        self.setCamera = None
        self.cameraID  = cameraID

        printf("Video| SUCCESS: Camera is connected to camera ", self.cameraID)


        # Set the default resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        return True



    # Get Frames and information
    def getFrame(self):
        # Returns the latest frame grabbed from the camera
        if self.frame is not None:
            return self.frame.copy()
        else:
            return None

    def getFilteredFrame(self):
        if self.filterFrame is not None:
            # Filtered frames are not copied, since they are usually not modified after
            return self.filterFrame
        else:
            return None

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
            if filterFunc in self.filterList: return

            self.filterList.append(filterFunc)

    def addWork(self, workFunc):
        # Add some function that has to be run each round. Processing is done after frame get, but before filtering.
        with self.workLock:
            if workFunc in self.workList: return

            self.workList.append(workFunc)

    def removeWork(self, workFunc):
        # Remove a function from the workList
        with self.workLock:
            # Make sure the function is actually in the workList
            if workFunc not in self.workList: return

            self.workList.remove(workFunc)

    def removeFilter(self, filterFunc):
        with self.filterLock:
            # Make sure the function is actually in the workList
            if filterFunc not in self.filterList: return

            self.filterList.remove(filterFunc)



# Possibly useful: Set the resolution, then return the resolution that actually got set
# def set_res(self, cap, x,y):
#     cap.set(cv.CV_CAP_PROP_FRAME_WIDTH, int(x))
#     cap.set(cv.CV_CAP_PROP_FRAME_HEIGHT, int(y))
#     return str(cap.get(cv.CV_CAP_PROP_FRAME_WIDTH)),str(cap.get(cv.CV_CAP_PROP_FRAME_HEIGHT))









