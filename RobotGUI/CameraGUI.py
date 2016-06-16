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


    def __init__(self, getFrameFunction, parent, fps=50):
        super(CameraWidget, self).__init__(parent)

        # Set up globals
        self.getFrameFunction = getFrameFunction  # This function is given as a parameters, and returns a frame
        self.fps              = fps   # The maximum FPS the widget will update at
        self.paused           = True  # Keeps track of the video's state
        self.timer            = QtCore.QTimer()

        self.timer.timeout.connect(self.nextFrameSlot)

        # Reference to the last object frame. Used to make sure that a frame is new, before repainting
        self.lastFrameID      = None

        # Initialize the UI
        self.frameLbl         = QtWidgets.QLabel("No camera data.")  # Temp label for the frame

        # MainVLayout must be global so that its subclasses can use it to add buttons
        self.mainVLayout = QtWidgets.QVBoxLayout(self)
        self.mainVLayout.addWidget(self.frameLbl)
        self.setLayout(self.mainVLayout)

        # Get one frame and display it, and wait for play to be pressed
        # self.nextFrameSlot()


    def play(self):
        if self.paused:
            self.timer.start(1000. / self.fps)

        self.paused = False

    def pause(self):
        if not self.paused:
            printf("CameraWidget.pause(): Stopping Timer!")
            self.timer.stop()

        self.paused = True


    def setFrame(self, frame):
        # When paused, you might want to have a custom frame showing. This is also useful for CameraSelector
        # The nextFrameSlot also uses it to set frames.


        # Convert a CV2 frame to a QPixMap and set the frameLbl to that
        pixFrame               = cv2.cvtColor(frame.copy(), cv2.COLOR_BGR2RGB)
        height, width, channel = pixFrame.shape
        bytesPerLine           = 3 * width
        img                    = QtGui.QImage(pixFrame, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
        pix                    = QtGui.QPixmap.fromImage(img)

        self.frameLbl.setPixmap(pix)

    def nextFrameSlot(self):
        frameID, frame = self.getFrameFunction()

        # If the frame is different than the one currently on the screen
        if frameID == self.lastFrameID: return None
        self.lastFrameID = frameID
        if frame is None:               return None

        self.setFrame(frame)


    def closeEvent(self, event):
        self.pause()



class CameraSelector(CameraWidget):
    """
    This is a camerawidget that the user can draw rectangles over, and will return the area of the image that the user
    selected.
    """

    # This signal emits only when the user selects an image, or restarts the process.
    # stateChanged = QtCore.pyqtSignal()
    objSelected  = QtCore.pyqtSignal()


    def __init__(self, getFrameFunction, parent):
        super(CameraSelector, self).__init__(getFrameFunction, parent)


        # Set up the rubberBand specific variables (for rectangle drawing)
        self.rubberBand    = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)
        self.origin        = QtCore.QPoint()


        # When the user has something selected, this is a frame. Otherwise, it is None
        self.selectedImage = None
        self.selectedRect  = None  # The coordinates of the object inside of self.selectedImage. (x1,y1,x2,y2) format.


        # Used to "reset" the widget, in case the user was unhappy with the photo they took.
        self.declinePicBtn = QtWidgets.QPushButton("Try Again?")
        self.declinePicBtn.clicked.connect(self.takeAnother)

        self.initUI()

    def initUI(self):
        # Create the buttons for 'selecting' the picture, or 'throwing it away' and returning to the videostream



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
            # self.getPixFrame()

            # height, width, channel = pixFrame.shape
            width  = self.frameLbl.pixmap().width()
            height = self.frameLbl.pixmap().height()
            pos    = (event.pos().x(), event.pos().y())
            if not 0 < pos[0] < width:  return
            if not 0 < pos[1] < height: return


            # Get a frame from OpenCV, so that it can be cropped when the user releases the mouse button
            frameID, self.selectedImage = self.getFrameFunction()

            if self.selectedImage is None:
                printf("CameraSelector.mouseReleaseEvent(): ERROR: getCVFrame() returned None Frame! ")
                return


            # Set the rectangles position and unhide the rectangle
            self.origin = QtCore.QPoint(event.pos())
            self.rubberBand.setGeometry(QtCore.QRect(self.origin, QtCore.QSize()))
            self.rubberBand.show()

    def mouseMoveEvent(self, event):

        if not self.origin.isNull():
            # Make sure the rectangle is bounded by the edge of the frame
            width  = self.frameLbl.pixmap().width()
            height = self.frameLbl.pixmap().height()
            pos    = (event.pos().x(), event.pos().y())

            # If it's not within the boundaries, then nothing will happen
            if not 0 < pos[0] < width:  return
            if not 0 < pos[1] < height: return

            self.rubberBand.setGeometry(QtCore.QRect(self.origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event):

        if event.button() == QtCore.Qt.LeftButton and not self.rubberBand.isHidden():
            self.rubberBand.hide()

            # Get the rectangle geometry
            pt = self.rubberBand.geometry().getCoords()


            # Ensure that the selected area isn't incredibly small (aka, a quick click
            if pt[3] - pt[1] < 10 or pt[2] - pt[0] < 10:
                self.selectedImage = None
                self.selectedRect  = None
                return

            self.selectedRect = pt
            self.declinePicBtn.setDisabled(False)
            self.objSelected.emit()


    def getSelected(self):
        # Returns the image and the rectangle of the selection from the image
        return self.selectedImage, self.selectedRect


    def takeAnother(self, event=None):
        # Return the widget to "take a picture" mode, throw away the old selected frame.
        self.selectedImage = None
        self.selectedRect  = None
        self.declinePicBtn.setDisabled(True)


    def closeEvent(self, event):
        self.pause()




