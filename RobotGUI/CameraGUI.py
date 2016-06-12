from PyQt5 import QtWidgets, QtCore


class CameraWidget(QtWidgets.QWidget):
    def __init__(self, getFrameFunction):
        """
        :param cameraID:
        :param getFrameFunction: A function that when called will return a frame
                that can be put in a QLabel. In this case the frame will come from
                a VideoStream object's getFrame function.
        :return:
        """
        super(CameraWidget, self).__init__()

        # Set up globals
        self.getFrame = getFrameFunction  # This function is given as a parameters, and returns a frame
        self.fps      = 24  # The maximum FPS the camera will
        self.paused   = True  # Keeps track of the video's state
        self.timer    = None

        # Initialize the UI
        self.initUI()

        # Get one frame and display it, and wait for play to be pressed
        self.nextFrameSlot()


    def initUI(self):
        # self.setMinimumWidth(640)
        # self.setMinimumHeight(480)
        self.video_frame = QtWidgets.QLabel("No camera data.")  # Temp label for the frame
        self.vbox = QtWidgets.QVBoxLayout(self)
        self.vbox.addWidget(self.video_frame)
        self.setLayout(self.vbox)

    def play(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.nextFrameSlot)
        self.timer.start(1000. / self.fps)

        self.paused = False

    def pause(self):
        if self.timer is not None: self.timer.stop()
        self.paused = True

    def nextFrameSlot(self):

        pixFrame = self.getFrame()

        # If a frame was returned correctly
        if pixFrame is None: return

        self.video_frame.setPixmap(pixFrame)



