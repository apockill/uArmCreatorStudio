#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
ZetCode PyQt4 tutorial 

In this example, we position two push
buttons in the bottom-right corner 
of the window. 

author: Jan Bodnar
website: zetcode.com 
last edited: October 2011
"""

import sys
import cv2
import Robot
import Video
from PyQt4 import QtGui, QtCore




class MainWindow(QtGui.QWidget):


    def __init__(self):
        super(MainWindow, self).__init__()
        self.cameraID = 0
        self.initUI()

    def initUI(self):
        self.dashboard = DashboardView(self.cameraID)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.dashboard)
        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox)

        self.setLayout(vbox)
        self.setGeometry(600, 600, 640, 480)
        self.setWindowTitle('uArm Creator Dashboard')
        self.show()

class Example(QtGui.QWidget):

    def __init__(self):
        super(Example, self).__init__()
        self.initUI()

    def initUI(self):
        #Create Text
        selectRobotTxt = QtGui.QLabel('Please select the robot you will be using:')
        selectCameraTxt = QtGui.QLabel('Please select the camera you will be using:')

        #CREATE BUTTONS
        nextBtn = QtGui.QPushButton("Next")
        backBtn = QtGui.QPushButton("Back")
        robotScanBtn = QtGui.QPushButton("Scan for Robots")
        cameraScanBtn = QtGui.QPushButton("Scan for Cameras")
            #Set max widths of buttons
        maxWidth = 100
        robotScanBtn.setMaximumWidth(maxWidth)
        cameraScanBtn.setMaximumWidth(maxWidth)
        nextBtn.setMaximumWidth(maxWidth)
        backBtn.setMaximumWidth(maxWidth)
            #Connect Buttons
        robotScanBtn.clicked.connect(self.scanForRobotsClicked)
        cameraScanBtn.clicked.connect(self.scanForCamerasClicked)
        nextBtn.clicked.connect(self.nextClicked)

        #CREATE VBOXES FOR ROBOTS AND CAMERAS TO FILL INTO
        self.robVBox = QtGui.QVBoxLayout()
        #self.robVBox.addStretch(1)
        self.camVBox = QtGui.QVBoxLayout()
        self.robVBox.setSpacing(1)
        self.camVBox.setSpacing(1)

        #CREATE GRID
        grid = QtGui.QGridLayout()
        grid.setSpacing(20)
            #Add Widgets
        grid.addWidget(selectRobotTxt,  0, 0, QtCore.Qt.AlignLeft)
        grid.addWidget(robotScanBtn,    0, 1, QtCore.Qt.AlignRight)
        grid.addLayout(self.robVBox,    1, 0, QtCore.Qt.AlignTop)

        grid.addWidget(selectCameraTxt, 2, 0, QtCore.Qt.AlignLeft)
        grid.addWidget(cameraScanBtn,   2, 1, QtCore.Qt.AlignRight)
        grid.addLayout(self.camVBox,    3, 0, QtCore.Qt.AlignTop)

        grid.addWidget(backBtn,         4, 0, QtCore.Qt.AlignBottom)
        grid.addWidget(nextBtn,         4, 1, QtCore.Qt.AlignBottom)

        self.setLayout(grid)

        #self.setGeometry(300, 300, 350, 300)
        self.setWindowTitle('Initial Setup')



    def scanForRobotsClicked(self):
        self.clearLayout(self.robVBox)  #  Clear robot list

        #  Get all devices connected to COM ports and list them out
        connectedDevices = Robot.getConnectedRobots()
        for index, port in enumerate(connectedDevices):
            robotButton = QtGui.QRadioButton(port[2])
            self.robVBox.addWidget(robotButton)


        if len(connectedDevices) == 0:
            notFoundTxt = QtGui.QLabel('No devices were found.')
            self.robVBox.addWidget(notFoundTxt)

    def scanForCamerasClicked(self):
        self.clearLayout(self.camVBox)  #  Clear camera list

        #  Get all of the cameras connected to the computer and list them
        connectedCameras = Video.getConnectedCameras()
        cameraButtons = []
        for i in connectedCameras:
            cameraButtons.append(QtGui.QRadioButton("Camera " + str(i)))

        self.cameraButtonGroup = QtGui.QButtonGroup()

        for i in xrange(len(cameraButtons)):
            # Add each radio button to the button layout
            self.camVBox.addWidget(cameraButtons[i])
            # Add each radio button to the button group & give it an ID of i
            self.cameraButtonGroup.addButton(cameraButtons[i], i)
            # Connect each radio button to a method to run when it's clicked
            cameraButtons[i].clicked.connect(lambda: self.radioButtonClicked(i))

        if len(connectedCameras) == 0:
            notFoundTxt = QtGui.QLabel('No cameras were found.')
            self.camVBox.addWidget(notFoundTxt)


    def nextClicked(self):
        buttonName = "Camera 0"
        if buttonName.isChecked():
            print buttonName, "is checked!"

    def camButtonClicked(self, text):
        print text

    def radioButtonClicked(self, text):
        print text

    def clearLayout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            child.widget().deleteLater()

"""
class MainWindow(QtGui.QMainWindow):
    count = 0

    def __init__(self, parent=None):

        super(MainWindow, self).__init__(parent)
        self.mdi = QtGui.QMdiArea()
        self.setCentralWidget(self.mdi)
        bar = self.menuBar()

        fileMnu = bar.addMenu("Windows")
        fileMnu.addAction("New")
        fileMnu.addAction("cascade")
        fileMnu.addAction("Tiled")
        fileMnu.triggered[QtGui.QAction].connect(self.windowaction)

        self.setWindowTitle("uArm Creator Dashboard")

    def windowaction(self, q):
        print "triggered"

        if q.text() == "New":
            MainWindow.count = MainWindow.count+1  #Only for naming the window
            sub = Example()
            # sub = QMdiSubWindow()
            # sub.setWidget(QTextEdit())
            # sub.setWindowTitle("subwindow" + str(MainWindow.count))

            self.mdi.addSubWindow(sub)
            sub.show()

        if q.text() == "cascade":
            self.mdi.cascadeSubWindows()

        if q.text() == "Tiled":
            self.mdi.tileSubWindows()

class MainWindow(QtGui.QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.initUI()

    def initUI(self):
        tabs	= QtGui.QTabWidget()
        pushButton1 = QtGui.QPushButton("QPushButton 1")
        pushButton2 = QtGui.QPushButton("QPushButton 2")

        tab1	= Example()


        #Resize width and height
        tabs.resize(250, 150)

        #Move QTabWidget to x:300,y:300
        tabs.move(300, 300)

        tabs.addTab(tab1, "Tab 1")

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(tabs)
        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox)

        self.setLayout(vbox)
        self.setGeometry(600, 600, 640, 480)
        self.setWindowTitle("Tabs and classes test!")
        self.show()
"""

class DashboardView(QtGui.QWidget):
    def __init__(self, cameraID):
        super(DashboardView, self).__init__()
        self.cameraID = cameraID
        self.initUI()

    def initUI(self):

        camera = CameraWidget(self.cameraID)

        hbox = QtGui.QHBoxLayout()
        vbox = QtGui.QVBoxLayout()

        hbox.addStretch()

        hbox.addWidget(camera)
        vbox.addLayout(hbox)

        self.setLayout(vbox)


class CameraWidget(QtGui.QWidget):
    def __init__(self, cameraID):
        super(CameraWidget, self).__init__()

        #Set up globals
        self.cameraID = cameraID
        self.capture = None
        self.fps = 24
        #self.video_frame
        #self.cap
        #self.vbox

        #Start video without using initializeVideo. Any other times though, do use initialize video.
        self.cap = cv2.VideoCapture(self.cameraID)

        #Initialize the UI
        self.video_frame = QtGui.QLabel("ERROR: Could not open camera.")
        self.vbox = QtGui.QVBoxLayout(self)
        self.vbox.addWidget(self.video_frame)
        self.setLayout(self.vbox)

        self.play()



    #Integral functions
    def initializeVideo(self):
        #Initialize the camera
        self.cap = cv2.VideoCapture(self.cameraID)
        if self.cap.isOpened():
            print "CameraWidget.init(): Camera", self.cameraID, " successfully opened."
        else:
            print "CameraWidget.init(): ERROR while opening Camera", self.cameraID

    def play(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.nextFrameSlot)
        self.timer.start(1000./self.fps)

    def pause(self):
        self.timer.stop()

    def nextFrameSlot(self):

        ret, frame = self.cap.read()
        if ret:
            #If a frame was returned correctly
            frame = cv2.cvtColor(frame, cv2.cv.CV_BGR2RGB)
            img = QtGui.QImage(frame, frame.shape[1], frame.shape[0], QtGui.QImage.Format_RGB888)
            pix = QtGui.QPixmap.fromImage(img)
            self.video_frame.setPixmap(pix)
        else:
            print "nextFrameSlot(): ERROR reading camera. Attempting to reconnect..."
            self.initializeVideo()





    #Other functions
    def setFPS(self, fps):
        self.fps = fps

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())