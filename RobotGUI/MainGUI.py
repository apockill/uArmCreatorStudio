import json
import sys
import webbrowser
from copy                  import deepcopy
from PyQt5                 import QtCore, QtWidgets, QtGui
from RobotGUI              import Video, ControlPanelGUI, Icons
from RobotGUI.Logic        import Global, Robot
from RobotGUI.Logic.Global import printf


########## WIDGETS ##########
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
        self.fps = 24  # The maximum FPS the camera will
        self.paused = True  # Keeps track of the video's state
        self.timer = None

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
        if pixFrame is None:
            return

        self.video_frame.setPixmap(pixFrame)


########## VIEWS ##########
class CalibrateView(QtWidgets.QWidget):
    """
    This is the dashboard where the user can calibrate different aspects of their robot.
    Things like motion calibration for the camera, color calibration, focus calibration, and maybe even eventually
    visual servo-ing calibrations
    """

    def __init__(self, vision, robot, parent):
        super(CalibrateView, self).__init__(parent)

        self.newSettings    = {"motionCalibrations": {"stationaryMovement": None, "activeMovement": None}}

        # These buttons are connected in Main.MainWindow.__init__()
        self.cancelBtn = QtWidgets.QPushButton("Cancel")
        self.applyBtn  = QtWidgets.QPushButton("Apply")
        self.vision = vision
        self.robot = robot

        # The label for the current known information for each calibration test. Label is changed in updateLabels()
        self.motionLbl = QtWidgets.QLabel("No information for this calibration")

        self.initUI()


    def initUI(self):

        motionBtn = QtWidgets.QPushButton("Calibrate Motion")


        maxWidth  = 130
        motionBtn.setFixedWidth(maxWidth)
        self.cancelBtn.setFixedWidth(maxWidth)
        self.applyBtn.setFixedWidth(maxWidth)



        row1 = QtWidgets.QHBoxLayout()
        row1.addWidget(     motionBtn, QtCore.Qt.AlignLeft)
        row1.addWidget(self.motionLbl, QtCore.Qt.AlignRight)

        middleVLayout = QtWidgets.QVBoxLayout()
        middleVLayout.addLayout(row1)
        middleVLayout.addStretch(1)

        # Set up Cancel and Apply buttons
        leftVLayout = QtWidgets.QVBoxLayout()
        leftVLayout.addStretch(1)
        leftVLayout.addWidget(self.cancelBtn, QtCore.Qt.AlignRight)
        rightVLayout = QtWidgets.QVBoxLayout()
        rightVLayout.addStretch(1)
        rightVLayout.addWidget(self.applyBtn, QtCore.Qt.AlignLeft)


        # Create the final layout with the leftVLayout, middleVLayout, and rightVLayout
        mainHLayout = QtWidgets.QHBoxLayout()
        mainHLayout.addStretch(3)
        mainHLayout.addLayout(leftVLayout)
        mainHLayout.addLayout(middleVLayout)
        mainHLayout.addLayout(rightVLayout)
        mainHLayout.addStretch(3)

        self.setLayout(mainHLayout)

        motionBtn.clicked.connect(self.calibrateMotion)

    def updateLabels(self):
        movCalib = self.newSettings["motionCalibrations"]
        if movCalib["stationaryMovement"] is not None:
            self.motionLbl.setText(" Stationary Movement: " + str(movCalib["stationaryMovement"]) +
                                   "     Active Movement: " + str(movCalib["activeMovement"]))

    def calibrateMotion(self):
        # Shake the robot left and right while getting frames to get a threshold for "high" movement between frames

        # Check that there is a valid robot connected
        if not self.robot.connected():
            printf("CalibrateView.calibrateMotion(): No uArm connected!")
            return

        # Check that there is a valid camera connected
        if not self.vision.cameraConnected():
            printf("CalibrateVIew.calibrateMotion(): No Camera Connected!")
            return

        # Make sure VideoStream is collecting new frames
        self.vision.vStream.setPaused(False)


        # Get movement while nothing is happening
        totalMotion = 0.0
        samples     = 50
        for i in range(0, samples):
            self.vision.vStream.waitForNewFrame()
            totalMotion += self.vision.getMotion()
        noMovement = totalMotion / samples


        # Get movement while robot is moving
        totalMotion = 0.0
        moves       = 10
        samples     = 0
        direction   = 1  #If the robot is going right or left next

        # Start position
        self.robot.setPos( x=-15, y=-15, z=20)
        self.robot.refresh()

        # Move robot left and right while getting new frames for "moves" amount of samples
        for move in range(0, moves):
            self.robot.setPos(x=30 * direction, y=0, z=0, relative=True)   #end position
            self.robot.refresh(speed=30)

            while self.robot.getMoving():
                self.vision.vStream.waitForNewFrame()
                totalMotion += self.vision.getMotion()
                samples += 1

            direction *= -1

        # Calculate average amount of motion when robot is moving rapidly
        highMovement = totalMotion / samples


        self.newSettings["motionCalibrations"]["stationaryMovement"] = round(  noMovement, 1)
        self.newSettings["motionCalibrations"]["activeMovement"]     = round(highMovement, 1)

        # Return the vStream to paused
        self.vision.vStream.setPaused(True)
        self.updateLabels()
        printf("CalibrateView.calibrateMotion(): Function complete! New motion settings: ", self.newSettings)

    def getSettings(self):
        return self.newSettings


class SettingsView(QtWidgets.QWidget):
    """
    Simple view that lets you select your robot and camera.
    The Apply/Cancel buttons are connected in the MainWindow class, which is why they are 'self' variables
    """

    def __init__(self, parent):
        super(SettingsView, self).__init__(parent)
        self.settings  = {"robotID": None, "cameraID": None}

        # Init UI Globals
        self.cameraButtonGroup = None
        self.robotButtonGroup  = None
        self.robVBox   = QtWidgets.QVBoxLayout()
        self.camVBox   = QtWidgets.QVBoxLayout()
        self.applyBtn  = QtWidgets.QPushButton("Apply")  #Gets connected with a method from MainWindow
        self.cancelBtn = QtWidgets.QPushButton("Cancel")

        self.initUI()

    def initUI(self):
        # Create Text
        selectRobotTxt  = QtWidgets.QLabel('Please select the robot you will be using:')
        selectCameraTxt = QtWidgets.QLabel('Please select the camera you will be using:')

        # CREATE BUTTONS
        robotScanBtn  = QtWidgets.QPushButton("Scan for Robots")
        cameraScanBtn = QtWidgets.QPushButton("Scan for Cameras")

        # Set max widths of buttons
        maxWidth = 130
        robotScanBtn.setFixedWidth(maxWidth)
        cameraScanBtn.setFixedWidth(maxWidth)
        self.applyBtn.setFixedWidth(maxWidth)
        self.cancelBtn.setFixedWidth(maxWidth)


        # Create the rows and fill them up
        row1 = QtWidgets.QHBoxLayout()
        row1.addWidget(selectRobotTxt, QtCore.Qt.AlignLeft)
        row1.addWidget(robotScanBtn, QtCore.Qt.AlignRight)

        row2 = QtWidgets.QHBoxLayout()
        row2.addLayout(self.robVBox, QtCore.Qt.AlignLeft)


        row3 = QtWidgets.QHBoxLayout()
        row3.addWidget(selectCameraTxt, QtCore.Qt.AlignLeft)
        row3.addWidget(cameraScanBtn, QtCore.Qt.AlignRight)

        row4 = QtWidgets.QHBoxLayout()
        row4.addLayout(self.camVBox)


        # Place the rows ito the middleVLayout
        middleVLayout = QtWidgets.QVBoxLayout()
        middleVLayout.addLayout(row1)
        middleVLayout.addLayout(row2)
        middleVLayout.addLayout(row3)
        middleVLayout.addLayout(row4)
        middleVLayout.addStretch(1)


        # Set up Cancel and Apply buttons
        leftVLayout  = QtWidgets.QVBoxLayout()
        leftVLayout.addStretch(1)
        leftVLayout.addWidget(self.cancelBtn, QtCore.Qt.AlignRight)
        rightVLayout = QtWidgets.QVBoxLayout()
        rightVLayout.addStretch(1)
        rightVLayout.addWidget(self.applyBtn, QtCore.Qt.AlignLeft)

        # Build the final layout
        mainHLayout = QtWidgets.QHBoxLayout()
        mainHLayout.addStretch(1)
        mainHLayout.addLayout(leftVLayout)
        mainHLayout.addLayout(middleVLayout)
        mainHLayout.addLayout(rightVLayout)
        mainHLayout.addStretch(1)

        self.setLayout(mainHLayout)

        # Connect Buttons
        robotScanBtn.clicked.connect(self.scanForRobotsClicked)
        cameraScanBtn.clicked.connect(self.scanForCamerasClicked)


    def scanForRobotsClicked(self):
        connectedDevices = Robot.getConnectedRobots()
        printf("SettingsView.scanForRobots(): Connected Devices: ", connectedDevices)
        self.robotButtonGroup = QtWidgets.QButtonGroup()

        #Update the list of found devices
        self.clearLayout(self.robVBox)  #  Clear robot list
        for i, port in enumerate(connectedDevices):
            newButton = QtWidgets.QRadioButton(port[0])
            self.robVBox.addWidget(newButton)                        # Add the button to the button layout
            self.robotButtonGroup.addButton(newButton, i)            # Add the button to a group, with an ID of i
            newButton.clicked.connect(self.robButtonClicked) # Connect each radio button to a method


        if len(connectedDevices) == 0:
            notFoundTxt = QtWidgets.QLabel('No devices were found.')
            self.robVBox.addWidget(notFoundTxt)

    def scanForCamerasClicked(self):

        # Get all of the cameras connected to the computer and list them
        connectedCameras = Video.getConnectedCameras()

        self.cameraButtonGroup = QtWidgets.QButtonGroup()

        # Update the list of found cameras
        self.clearLayout(self.camVBox)  #  Clear camera list
        for i in range(len(connectedCameras)):
            newButton = QtWidgets.QRadioButton("Camera " + str(i))
            self.camVBox.addWidget(newButton)                  # Add the button to the button layout
            self.cameraButtonGroup.addButton(newButton, i)     # Add the button to a group, with an ID of i
            newButton.clicked.connect(self.camButtonClicked)   # Connect each radio button to a method


        if len(connectedCameras) == 0:
            notFoundTxt = QtWidgets.QLabel('No cameras were found.')
            self.camVBox.addWidget(notFoundTxt)


    def camButtonClicked(self):
        self.settings["cameraID"] = self.cameraButtonGroup.checkedId()

    def robButtonClicked(self):
        self.settings["robotID"] = str(self.robotButtonGroup.checkedButton().text())


    def clearLayout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            child.widget().deleteLater()

    def getSettings(self):
        return self.settings


class DashboardView(QtWidgets.QWidget):
    def __init__(self, controlPanel, cameraWidget, parent):
        super(DashboardView, self).__init__(parent)

        # UI Globals setup
        self.controlPanel   = controlPanel
        self.cameraWidget   = cameraWidget

        self.initUI()

    def initUI(self):

        # Create main layout
        mainHLayout = QtWidgets.QHBoxLayout()
        mainVLayout = QtWidgets.QVBoxLayout()
        mainVLayout.addLayout(mainHLayout)

        mainHLayout.addWidget(self.controlPanel)
        mainHLayout.addWidget(self.cameraWidget)    #Create Camera view (RIGHT)

        self.setLayout(mainVLayout)




########## MAIN WINDOW ##########
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.settings  = {"robotID": None, "cameraID": None, "lastOpenedFile": None,
                          "motionCalibrations": None}

        # Init self variables
        self.fileName    = None
        self.loadData    = None  #Set when file is loaded. Used to check if the user has changed anything and prompt
        self.keysPressed = None
        self.vStream     = Video.VideoStream(None)
        self.vision      = Video.Vision(self.vStream)
        self.robot       = Robot.Robot(None)



        # Set Global UI Variables
        self.centralWidget   = QtWidgets.QStackedWidget()
        self.controlPanel    = ControlPanelGUI.ControlPanel(self.robot, self.vision, self.settings, parent=self)
        cameraWidget         = CameraWidget(self.vStream.getPixFrame)

        self.dashboardView   = DashboardView(self.controlPanel, cameraWidget, parent=self)
        self.settingsView    = SettingsView(parent=self)  #'self' so that StackedWidget can be used
        self.calibrateView   = CalibrateView(self.vision, self.robot, parent=self)

        self.scriptToggleBtn = QtWidgets.QAction(QtGui.QIcon(Icons.run_script),
                               'Run/Pause the command script (Ctrl+R)', self)
        self.videoToggleBtn  = QtWidgets.QAction(QtGui.QIcon(Icons.play_video),
                               'Play/Pause the video stream (Ctrl+P)', self)


        # Connect Cancel/Apply Buttons from various views
        self.settingsView.applyBtn.clicked.connect(  lambda: self.closeSettingsView("Apply"))
        self.settingsView.cancelBtn.clicked.connect( lambda: self.closeSettingsView("Cancel"))
        self.calibrateView.applyBtn.clicked.connect( lambda: self.closeCalibrateView("Apply"))
        self.calibrateView.cancelBtn.clicked.connect(lambda: self.closeCalibrateView("Cancel"))


        # Now that objects have been created, load the settings
        configExists = self.loadSettings()

        self.initUI()

        # If any file is specified in "lastOpenedFile" then load it.
        if self.settings["lastOpenedFile"] is not None:
            self.loadTask(filename=self.settings["lastOpenedFile"])
        else:
            self.newTask()

        if not configExists:
            self.setView(self.settingsView)

    def initUI(self):
        # Create "File" Menu
        menuBar      = self.menuBar()
        fileMenu     = menuBar.addMenu('File')

        newAction    = QtWidgets.QAction( QtGui.QIcon(Icons.new_file), "New Task",     self)
        saveAction   = QtWidgets.QAction(QtGui.QIcon(Icons.save_file), "Save Task",    self)
        saveAsAction = QtWidgets.QAction(QtGui.QIcon(Icons.save_file), "Save Task As", self)
        loadAction   = QtWidgets.QAction(QtGui.QIcon(Icons.load_file), "Load Task",    self)
        forumAction  = QtWidgets.QAction("Visit the forum!", self)

        newAction.triggered.connect(self.newTask)
        saveAction.triggered.connect(self.saveTask)
        saveAsAction.triggered.connect(lambda: self.saveTask(True))
        loadAction.triggered.connect(self.loadTask)
        forumAction.triggered.connect(lambda: webbrowser.open("https://forum.ufactory.cc/", new=0, autoraise=True))

        fileMenu.addAction(newAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(saveAsAction)
        fileMenu.addAction(loadAction)
        fileMenu.addAction(forumAction)
        menuBar.addMenu(fileMenu)


        # Create Toolbar
        toolbar = self.addToolBar("MainToolbar")

        settingsBtn  = QtWidgets.QAction(QtGui.QIcon(Icons.settings),  'Open Camera and Robot settings (Ctrl+T)', self)
        calibrateBtn = QtWidgets.QAction(QtGui.QIcon(Icons.calibrate), 'Open Robot and Camera Calibration Center', self)

        self.scriptToggleBtn.setShortcut('Ctrl+R')
        self.videoToggleBtn.setShortcut('Ctrl+P')
        settingsBtn.setShortcut('Ctrl+S')

        self.scriptToggleBtn.triggered.connect( lambda: self.setScript("toggle"))
        self.videoToggleBtn.triggered.connect(  lambda: self.setVideo("toggle"))
        settingsBtn.triggered.connect(          lambda: self.setView(self.settingsView))
        calibrateBtn.triggered.connect(         lambda: self.setView(self.calibrateView))

        toolbar.addAction(self.scriptToggleBtn)
        toolbar.addAction(self.videoToggleBtn)
        toolbar.addAction(settingsBtn)
        toolbar.addAction(calibrateBtn)


        # Create the main layout
        self.setCentralWidget(self.centralWidget)
        self.centralWidget.addWidget(self.dashboardView)
        self.centralWidget.addWidget(self.settingsView)
        self.centralWidget.addWidget(self.calibrateView)


        # Final touches
        self.setWindowTitle('uArm Creator Dashboard')
        self.setWindowIcon(QtGui.QIcon(Icons.taskbar))
        QtWidgets.QApplication.setStyle(QtWidgets.QStyleFactory.create('Plastique'))  #TODO updgrade to pyQt5
        self.setStyle(QtWidgets.QStyleFactory.create('Plastique'))
        self.show()




    def setSettings(self, newSettings):
        # Apply settings

        # Create a quick function that will check if a setting has been changed. If it has, an action will be taken.
        isNew = lambda key: (key in newSettings) and (newSettings[key] is not None) and \
                            (not self.settings[key] == newSettings[key])

        # If camera has been changed
        if isNew("cameraID"):
            printf("MainWindow.closeSettingsView(): Changing cameraID from ",
                  self.settings["cameraID"], "to", newSettings["cameraID"])

            self.settings["cameraID"] = newSettings["cameraID"]

            # Set the new camera in the VideoStream object
            success = self.vStream.setNewCamera(self.settings["cameraID"])
            if success:
                self.setVideo("play")
            else:
                self.setVideo("pause")


        # If a new robot has been set, or the robot has been changed
        if isNew("robotID") or not self.robot.connected():  #If robot is not connected, try connecting
            printf("MainWindow.closeSettingsView(): Changing robotID from ",
                  self.settings["robotID"], "to", newSettings["robotID"])
            self.settings["robotID"] = newSettings["robotID"]
            self.robot.setUArm(self.settings["robotID"])


        # If a new file has been opened, change the Settings file to reflect that so next time GUI is opened, so is file
        if isNew("lastOpenedFile"):
            printf("MainWindow.setSettings(): Loading file ", str(newSettings["lastOpenedFile"]))
            self.settings["lastOpenedFile"] = newSettings["lastOpenedFile"]
            self.loadTask(filename=self.settings["lastOpenedFile"])


        # If a calibration of type Motion has been changed, reflect this in the settings
        if isNew("motionCalibrations"):
            self.settings["motionCalibrations"] = newSettings["motionCalibrations"]
            self.calibrateView.newSettings["motionCalibrations"] = self.settings["motionCalibrations"]
            self.calibrateView.updateLabels()


        # Save settings to a config file
        self.saveSettings()

    def setVideo(self, state):
        # Change the state of the videostream. The state can be play, pause, or simply "toggle"

        printf("MainWindow.setVideo(): Setting video to state: ", state)

        # Don't change anything if no camera ID has been added yet
        if self.settings["cameraID"] is None: return


        if state == "play":
            self.dashboardView.cameraWidget.play()
            self.vStream.setPaused(False)
            self.videoToggleBtn.setIcon(QtGui.QIcon(Icons.pause_video))


        if state == "pause":
            self.dashboardView.cameraWidget.pause()
            self.vStream.setPaused(True)
            self.videoToggleBtn.setIcon(QtGui.QIcon(Icons.play_video))


        if state == "toggle":
            if self.vStream.paused:
                self.setVideo("play")
            else:
                self.setVideo("pause")

    def setScript(self, state):
        # Run/pause the main script

        if state == "play":
            printf("MainWindow.setScript(): Setting script to ", state)
            self.controlPanel.startThread()
            self.scriptToggleBtn.setIcon(QtGui.QIcon(Icons.pause_script))

        if state == "pause":
            printf("MainWindow.setScript(): Setting script to ", state)
            self.controlPanel.endThread()
            self.scriptToggleBtn.setIcon(QtGui.QIcon(Icons.run_script))


        if state == "toggle":
            if self.controlPanel.running:
                self.setScript("pause")
            else:
                self.setScript("play")



    def setView(self, viewWidget):
        # Change between the main view, settings, and calibrations view.

        printf("MainWindow.openSettingsView(): Opening Settings!")
        self.setScript("pause")
        self.setVideo("pause")
        self.centralWidget.setCurrentWidget(viewWidget)

    def closeSettingsView(self, buttonClicked):
        newSettings = self.settingsView.getSettings()

        if buttonClicked == "Apply":
            printf('MainWindow.closeSettingsView(): "Apply" clicked, applying settings...')
            self.setSettings(newSettings)

        if buttonClicked == "Cancel":
            printf('MainWindow.closeSettingsView(): "Cancel" clicked, no settings applied.')

        # Go back to dashboard
        self.setVideo("play")
        self.centralWidget.setCurrentWidget(self.dashboardView)

    def closeCalibrateView(self, buttonClicked):
        self.centralWidget.setCurrentWidget(self.dashboardView)

        newSettings = self.calibrateView.getSettings()
        printf("new settings: ", newSettings)
        if buttonClicked == "Apply":
            printf('MainWindow.closeCalibrateView(): Apply" clicked, applying settings...')
            self.setSettings(newSettings)

        if buttonClicked == "Cancel":
            printf('MainWindow.closeCalibrateView(): "Cancel" clicked, no calibrations applied...')

        #Go back to dashboard
        self.setVideo("play")
        self.centralWidget.setCurrentWidget(self.dashboardView)



    def promptSave(self):
        # Prompts the user if they want to save, but only if they've changed something in the program


        if self.loadData is not None and not self.loadData == self.controlPanel.getSaveData():
            printf("MainWindow.promptSave(): Prompting user to save changes")
            reply = QtWidgets.QMessageBox.question(self, 'Warning',
                                       "You have unsaved changes. Would you like to save before continuing?",
                                       QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.Yes)
            if reply == QtWidgets.QMessageBox.Yes:
                printf("MainWindow.promptSave():Saving changes")

                self.saveTask(False)

    def newTask(self):
        self.promptSave()
        self.dashboardView.controlPanel.loadData([])
        self.fileName = None
        self.loadData = deepcopy(self.controlPanel.getSaveData())



    def saveTask(self, promptSave):
        printf("MainWindow.saveTask(): Saving project")

        # If there is no filename, ask for one
        if promptSave or self.fileName is None:
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Task", "MyTask", "Task (*.task)")
            if filename == "": return  #If user hit cancel
            self.fileName = filename


        # Update the save file
        saveData = self.controlPanel.getSaveData()
        json.dump(saveData, open(self.fileName, 'w'), sort_keys=False, indent=3, separators=(',', ': '))

        self.loadData = deepcopy(saveData)  #Update what the latest saved changes are


        printf("MainWindow.saveTask(): Project Saved")

        self.setWindowTitle('uArm Creator Dashboard       ' + self.fileName)
        self.saveSettings()

    def loadTask(self,  **kwargs):
        # Load a save file

        printf("MainWindow.loadTask(): Loading project")

        filename = kwargs.get("filename", None)

        # If there's no filename given, then prompt the user for what to name the task
        if filename is None:  #If no filename was specified, prompt the user for where to save
            filename, filetype = QtWidgets.QFileDialog.getOpenFileName(self, "Load Task", "", "*.task")
            if filename == "": return  #If user hit cancel

        try:
            self.loadData = json.load( open(filename))
        except IOError:
            printf("MainWindow.loadTask(): ERROR: Task file ", filename, "not found!")
            self.settings["lastOpenedFile"] = None
            return

        printf("MainWindow.save(): Project Loaded:")
        self.fileName = filename


        # Load the data- BUT MAKE SURE TO DEEPCOPY otherwise any change in the program will change in self.loadData
        self.dashboardView.controlPanel.loadData(deepcopy(self.loadData))
        self.setWindowTitle('uArm Creator Dashboard      ' + self.fileName)

        self.saveSettings()


    def saveSettings(self):
        printf("MainWindow.saveSettings(): Saving Settings")
        self.settings["lastOpenedFile"] = self.fileName
        json.dump(self.settings, open("Settings.txt", 'w'), sort_keys=False, indent=3, separators=(',', ': '))


    def loadSettings(self):
        # Load the settings config and set them

        printf("MainWindow.loadSettings(): Loading Settings")
        # newSettings = json.load(open( "Settings.txt"))
        try:
            newSettings = json.load(open( "Settings.txt"))
            # printf("MainWindow.loadSettings(): Loading settings: ", newSettings, "...")
            self.setSettings(newSettings)
            return True
        except IOError:
            printf("MainWindow.loadSettings(): No settings file detected. Using default values.")
            return False


    def closeEvent(self, event):
        # When window is closed, prompt for save, close the video stream, and close the control panel (thus script)
        self.promptSave()

        self.vStream.endThread()
        self.controlPanel.close()


#  Application subclass, to record key presses/releases
class Application(QtWidgets.QApplication):
    """
        I modified the QtGui.QApplication class slightly in order to intercept keypress events
        and write them in the Global.keysPressed list
    """

    def __init__(self, args):
        super(Application, self).__init__(args)

    def notify(self, receiver, event):
        # Add any keys that are pressed to keysPressed
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() not in Global.keysPressed:
                Global.keysPressed.append(event.key())


        # Remove any keys that are released from self.keysPressed
        if event.type() == QtCore.QEvent.KeyRelease:
            if event.key() in Global.keysPressed:
                Global.keysPressed = [k for k in Global.keysPressed if k != event.key()]


        # Call Base Class Method to Continue Normal Event Processing
        return super(Application, self).notify(receiver, event)




if __name__ == '__main__':
    Global.init()

    # Install a global exception hook to catch pyQt errors that fall through (helps with debugging a ton)
    # TODO: Remove this when development is finished.
    sys.__excepthook = sys.excepthook
    sys._excepthook  = sys.excepthook

    def exception_hook(exctype, value, traceback):
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)

    sys.excepthook   = exception_hook

    # Actually start the application
    app = Application(sys.argv)

    # DO THEMING STUFF NOW
    # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    # Set Application Font
    font = QtGui.QFont()
    font.setFamily("Verdana")
    font.setPixelSize(12)
    app.setFont(font)


    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())

    #app.exec_()





