import cv2
from PyQt5                      import QtWidgets, QtCore, QtGui
from RobotGUI.Logic.Global      import printf

class CameraWidget(QtWidgets.QWidget):
    """
        Creates a widget that will update 24 times per second, by calling for a new frame from the vStream object.

        :param getFrameFunction: A function that when called will return a frame
                that can be put in a QLabel. In this case the frame will come from
                a VideoStream object's getFrame function.
        :return:
        """
    def __init__(self, getPixFrameFunction, parent):
        super(CameraWidget, self).__init__(parent)

        # Set up globals
        self.getPixFrame = getPixFrameFunction  # This function is given as a parameters, and returns a frame
        self.fps         = 24  # The maximum FPS the camera will
        self.paused      = True  # Keeps track of the video's state
        self.timer       = None

        # Reference to the last object frame. Used to make sure that a frame is new, before repainting
        self.lastFrameID = None

        # Initialize the UI
        self.video_frame = QtWidgets.QLabel("No camera data.")  # Temp label for the frame

        # MainVLayout must be global so that its subclasses can use it to add buttons
        self.mainVLayout = QtWidgets.QVBoxLayout(self)
        self.mainVLayout.addWidget(self.video_frame)
        self.setLayout(self.mainVLayout)

        # Get one frame and display it, and wait for play to be pressed
        self.nextFrameSlot()


    def play(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.nextFrameSlot)
        self.timer.start(1000. / self.fps)

        self.paused = False

    def pause(self):
        if self.timer is not None: self.timer.stop()
        self.paused = True

    def nextFrameSlot(self):
        pixFrame = self.getPixFrame()

        # If the frame is different than the one currently on the screen, or if no frame was returned
        if id(pixFrame) == self.lastFrameID or pixFrame is None: return

        self.lastFrameID = id(pixFrame)
        self.video_frame.setPixmap(pixFrame)



class CameraSelector(CameraWidget):
    """
    This is a camerawidget that the user can draw rectangles over, and will return the area of the image that the user
    selected.
    """

    # This signal emits only when the user has successfully selected an image
    frameSelected = QtCore.pyqtSignal()

    def __init__(self, getCVFrameFunction, getPixFrameFunction, parent):
        super(CameraSelector, self).__init__(getPixFrameFunction, parent)

        # Set up the rubberBand specific variables (for rectangle drawing)
        self.rubberBand    = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)
        self.origin        = QtCore.QPoint()


        # Save the frame getting function. This is not for PixFrame, this is for a cv2 numpy formatted frame
        self.getCVFrame    = getCVFrameFunction


        # When the user has something selected, this is a frame. Otherwise, it is None
        self.selectedImage = None  # A numpy array, cv2 format, image of the cropped area the user selected.


        # Used to "reset" the widget, in case the user was unhappy with the photo they took.
        self.declinePicBtn = QtWidgets.QPushButton("Try Again?")


        self.initUI()

    def initUI(self):
        # Create the buttons for 'selecting' the picture, or 'throwing it away' and returning to the videostream

        self.declinePicBtn.clicked.connect(self.takeAnother)

        # Disable the buttons, only enable them when the user has selected from the picture
        self.declinePicBtn.setDisabled(True)


        # Add these to the superclass layout
        row1 = QtWidgets.QHBoxLayout()
        row1.addWidget(self.declinePicBtn)
        row1.addStretch(1)

        self.mainVLayout.addLayout(row1)
        self.layout().setContentsMargins(0,0,0,0)

    # Selection related events
    def mousePressEvent(self, event):
        # If the user already has selected an image, leave.
        if self.selectedImage is not None: return


        if event.button() == QtCore.Qt.LeftButton:
            # Pause the video so that it's easier to select the object

            # Make sure the click was within the boundaries of the frame
            width  = self.getPixFrame().width()
            height = self.getPixFrame().height()
            pos    = (event.pos().x(), event.pos().y())
            if not 0 < pos[0] < width:  return
            if not 0 < pos[1] < height: return

            # Pause the video to make it easier to select
            self.pause()

            # Set the rectangles position and unhide the rectangle
            self.origin = QtCore.QPoint(event.pos())
            self.rubberBand.setGeometry(QtCore.QRect(self.origin, QtCore.QSize()))
            self.rubberBand.show()

    def mouseMoveEvent(self, event):

        if not self.origin.isNull():
            # Make sure the rectangle is bounded by the edge of the frame
            width  = self.getPixFrame().width()
            height = self.getPixFrame().height()
            pos    = (event.pos().x(), event.pos().y())

            # If it's not within the boundaries, then nothing will happen
            if not 0 < pos[0] < width:  return
            if not 0 < pos[1] < height: return

            self.rubberBand.setGeometry(QtCore.QRect(self.origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event):

        if event.button() == QtCore.Qt.LeftButton and not self.rubberBand.isHidden():
            self.rubberBand.hide()

            # Get a recent frame from OpenCV
            currFrame = self.getCVFrame()


            if currFrame is None:
                printf("CameraSelector.mouseReleaseEvent(): ERROR: getCVFrame() returned None Frame! ")
                self.play()
                return


            # Get the rectangle geometry
            pt = self.rubberBand.geometry().getCoords()


            # Crop the openCV frame, save it as self.selectedImage
            croppedFrame       = currFrame[pt[1]:pt[3], pt[0]:pt[2]].copy()
            self.selectedImage = croppedFrame.copy()


            # Convert the cropped image to a PixMap, and set the widget to that picture.
            pixFrame               = cv2.cvtColor(croppedFrame, cv2.COLOR_BGR2RGB)
            height, width, channel = pixFrame.shape
            bytesPerLine           = 3 * width
            img                    = QtGui.QImage(pixFrame, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
            pix                    = QtGui.QPixmap.fromImage(img)


            self.video_frame.setPixmap(pix)

            # Turn on the "throw away picture" button, and emit a "frameSelected" signal
            self.declinePicBtn.setDisabled(False)

            self.frameSelected.emit()


    def getSelectedFrame(self):
        return self.selectedImage

    def takeAnother(self, event):
        # Event triggered by the "Try Again" button.


        # Return the widget to "take a picture" mode, throw away the old selected frame.
        self.selectedImage = None
        self.declinePicBtn.setDisabled(True)
        self.play()

    def closeEvent(self, event):
        self.camera.pause()



