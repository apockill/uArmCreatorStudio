import json
import sys
import webbrowser
# import qdarkstyle
from RobotGUI.CameraGUI         import CameraWidget
from RobotGUI.ObjectManagerGUI  import ObjectManager
from copy                       import deepcopy
from PyQt5                      import QtCore, QtWidgets, QtGui
from RobotGUI                   import ControlPanelGUI, Icons
from RobotGUI.Logic             import Global
from RobotGUI.Logic.Environment import Environment, Interpreter
from RobotGUI.Logic.Robot       import getConnectedRobots
from RobotGUI.Logic.Video       import getConnectedCameras
from RobotGUI.Logic.Global      import printf



########## VIEWS ##########
class CalibrateWindow(QtWidgets.QDialog):
    """
    This is the dashboard where the user can calibrate different aspects of their robot.
    Things like motion calibration for the camera, color calibration, focus calibration, and maybe even eventually
    visual servo-ing calibrations
    """

    def __init__(self, environment, parent):
        super(CalibrateWindow, self).__init__(parent)

        self.env            = environment
        self.newSettings    = self.env.getSettings()

        # The label for the current known information for each calibration test. Label is changed in updateLabels()
        self.motionLbl = QtWidgets.QLabel("No information for this calibration")

        self.initUI()

        self.updateLabels()

    def initUI(self):

        motionBtn = QtWidgets.QPushButton("Calibrate Motion")
        cancelBtn = QtWidgets.QPushButton("Cancel")
        applyBtn  = QtWidgets.QPushButton("Apply")

        motionBtn.clicked.connect(self.calibrateMotion)

        applyBtn.clicked.connect(self.accept)
        cancelBtn.clicked.connect(self.reject)


        maxWidth  = 130
        motionBtn.setFixedWidth(maxWidth)
        cancelBtn.setFixedWidth(maxWidth)
        applyBtn.setFixedWidth(maxWidth)


        row1 = QtWidgets.QHBoxLayout()
        row1.addWidget(     motionBtn, QtCore.Qt.AlignLeft)
        row1.addWidget(self.motionLbl, QtCore.Qt.AlignRight)


        middleVLayout = QtWidgets.QVBoxLayout()
        middleVLayout.addLayout(row1)
        middleVLayout.addStretch(1)


        # Set up Cancel and Apply buttons
        leftVLayout = QtWidgets.QVBoxLayout()
        leftVLayout.addStretch(1)
        leftVLayout.addWidget(cancelBtn, QtCore.Qt.AlignRight)
        rightVLayout = QtWidgets.QVBoxLayout()
        rightVLayout.addStretch(1)
        rightVLayout.addWidget(applyBtn, QtCore.Qt.AlignLeft)


        # Create the final layout with the leftVLayout, middleVLayout, and rightVLayout
        mainHLayout = QtWidgets.QHBoxLayout()
        mainHLayout.addStretch(3)
        mainHLayout.addLayout(leftVLayout)
        mainHLayout.addLayout(middleVLayout)
        mainHLayout.addLayout(rightVLayout)
        mainHLayout.addStretch(3)

        self.setMinimumHeight(400)
        self.setLayout(mainHLayout)
        self.setWindowTitle('Calibrations')
        self.setWindowIcon(QtGui.QIcon(Icons.calibrate))



    def updateLabels(self):
        print(self.newSettings)
        movCalib = self.newSettings["motionCalibrations"]


        # Check if motionCalibrations already exist
        if movCalib["stationaryMovement"] is not None:
            self.motionLbl.setText(" Stationary Movement: " + str(movCalib["stationaryMovement"]) +
                                   "     Active Movement: " + str(movCalib["activeMovement"]))

    def calibrateMotion(self):
        # Shake the robot left and right while getting frames to get a threshold for "high" movement between frames
        displayError = lambda message: QtWidgets.QMessageBox.question(self, 'Error', message, QtWidgets.QMessageBox.Ok)

        vStream = self.env.getVStream()
        vision  = self.env.getVision()
        robot   = self.env.getRobot()

        # Check that there is a valid robot connected
        if not robot.connected():
            printf("CalibrateView.calibrateMotion(): No uArm connected!")
            displayError("A robot must be connected to run this calibration.")
            return

        # Check that there is a valid camera connected
        if not vision.cameraConnected():
            printf("CalibrateVIew.calibrateMotion(): No Camera Connected!")
            displayError("A camera must be connected to run this calibration.")
            return

        # Make sure VideoStream is collecting new frames
        vStream.setPaused(False)


        # Get movement while nothing is happening
        totalMotion = 0.0
        samples     = 75
        for i in range(0, samples):
            vStream.waitForNewFrame()
            totalMotion += vision.getMotion()
        noMovement = totalMotion / samples


        # Get movement while robot is moving
        totalMotion = 0.0
        moves       = 10
        samples     = 0
        direction   = 1  #If the robot is going right or left next

        # Start position
        robot.setPos( x=-15, y=-15, z=20)
        robot.refresh()

        # Move robot left and right while getting new frames for "moves" amount of samples
        for move in range(0, moves):
            robot.setPos(x=30 * direction, y=0, z=0, relative=True)   #end position
            robot.refresh(speed=30)

            while robot.getMoving():
                vStream.waitForNewFrame()
                totalMotion += vision.getMotion()
                samples += 1

            direction *= -1

        # Calculate average amount of motion when robot is moving rapidly
        highMovement = totalMotion / samples


        self.newSettings["motionCalibrations"]["stationaryMovement"] = round(  noMovement, 1)
        self.newSettings["motionCalibrations"]["activeMovement"]     = round(highMovement, 1)

        # Return the vStream to paused
        vStream.setPaused(True)
        self.updateLabels()
        printf("CalibrateView.calibrateMotion(): Function complete! New motion settings: ", self.newSettings)

    def getSettings(self):
        print("GETSETTINGS RUNNING")
        return self.newSettings


class SettingsWindow(QtWidgets.QDialog):
    """
    Simple view that lets you select your robot and camera.
    The Apply/Cancel buttons are connected in the MainWindow class, which is why they are 'self' variables
    """

    def __init__(self, parent):
        super(SettingsWindow, self).__init__(parent)
        self.settings  = {"robotID": None, "cameraID": None}

        # Init UI Globals
        self.cameraButtonGroup = None  # Radio buttons require a "group"
        self.robotButtonGroup  = None
        self.robVBox           = QtWidgets.QVBoxLayout()
        self.camVBox           = QtWidgets.QVBoxLayout()

        self.initUI()

    def initUI(self):

        # Create Text
        selectRobotTxt  = QtWidgets.QLabel('Please select the robot you will be using:')
        selectCameraTxt = QtWidgets.QLabel('Please select the camera you will be using:')


        # CREATE BUTTONS
        robotScanBtn  = QtWidgets.QPushButton("Scan for Robots")
        cameraScanBtn = QtWidgets.QPushButton("Scan for Cameras")
        applyBtn      = QtWidgets.QPushButton("Apply")
        cancelBtn     = QtWidgets.QPushButton("Cancel")

        # Connect Buttons
        robotScanBtn.clicked.connect(   self.scanForRobotsClicked)
        cameraScanBtn.clicked.connect(  self.scanForCamerasClicked)
        applyBtn.clicked.connect(       self.accept)
        cancelBtn.clicked.connect(      self.reject)


        # Set max widths of buttons
        maxWidth = 130
        robotScanBtn.setFixedWidth(maxWidth)
        cameraScanBtn.setFixedWidth(maxWidth)
        applyBtn.setFixedWidth(maxWidth)
        cancelBtn.setFixedWidth(maxWidth)


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
        leftVLayout.addWidget(cancelBtn, QtCore.Qt.AlignRight)
        rightVLayout = QtWidgets.QVBoxLayout()
        rightVLayout.addStretch(1)
        rightVLayout.addWidget(applyBtn, QtCore.Qt.AlignLeft)


        # Build the final layout
        mainHLayout = QtWidgets.QHBoxLayout()
        mainHLayout.addStretch(1)
        mainHLayout.addLayout(leftVLayout)
        mainHLayout.addLayout(middleVLayout)
        mainHLayout.addLayout(rightVLayout)
        mainHLayout.addStretch(1)

        self.setLayout(mainHLayout)
        self.setMinimumHeight(400)
        self.setWindowTitle('Settings')
        self.setWindowIcon(QtGui.QIcon(Icons.settings))




    def scanForRobotsClicked(self):
        connectedDevices = getConnectedRobots()  # From Robot.py
        printf("SettingsView.scanForRobots(): Connected Devices: ", connectedDevices)
        self.robotButtonGroup = QtWidgets.QButtonGroup()

        # Update the list of found devices
        self.clearLayout(self.robVBox)  #  Clear robot list
        for i, port in enumerate(connectedDevices):
            newButton = QtWidgets.QRadioButton(port[0])
            self.robVBox.addWidget(newButton)                        # Add the button to the button layout
            self.robotButtonGroup.addButton(newButton, i)            # Add the button to a group, with an ID of i
            newButton.clicked.connect(self.robButtonClicked)         # Connect each radio button to a method


        if len(connectedDevices) == 0:
            notFoundTxt = QtWidgets.QLabel('No devices were found.')
            self.robVBox.addWidget(notFoundTxt)

    def scanForCamerasClicked(self):

        # Get all of the cameras connected to the computer and list them
        connectedCameras = getConnectedCameras()  # From the Video.py module

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
                          "motionCalibrations": {"stationaryMovement": None, "activeMovement": None}}

        # Init self variables
        self.fileName    = None
        self.loadData    = None  #Set when file is loaded. Used to check if the user has changed anything and prompt
        self.keysPressed = None
        self.env         = Environment(self.settings)
        self.interpreter = Interpreter()

        # Set Global UI Variables
        self.centralWidget   = QtWidgets.QStackedWidget()
        self.controlPanel    = ControlPanelGUI.ControlPanel(self.env, self.settings, parent=self)
        self.dashboardView   = DashboardView(self.controlPanel,
                                             CameraWidget(self.env.getVStream().getPixFrame, parent=self),
                                             parent=self)


        self.scriptToggleBtn = QtWidgets.QAction(QtGui.QIcon(Icons.run_script),
                               'Run/Pause the command script (Ctrl+R)', self)
        self.videoToggleBtn  = QtWidgets.QAction(QtGui.QIcon(Icons.play_video),
                               'Play/Pause the video stream (Ctrl+P)', self)



        # Now that objects have been created, load the settings
        configExists = self.loadSettings()
        self.setVideo("play")  # This has to be done before self.initUI() to avoid window opening up and seeming lag
        self.initUI()


        # If any file is specified in "lastOpenedFile" then load it.
        if self.settings["lastOpenedFile"] is not None:
            self.loadTask(filename=self.settings["lastOpenedFile"])
        else:
            self.newTask()

        # If there is no settings File, then open the settings window first thing
        if not configExists:
            self.openSettings()


        self.openObjectManager()  # For debugging

    def initUI(self):
        # Create "File" Menu
        menuBar      = self.menuBar()
        fileMenu     = menuBar.addMenu('File')

        newAction    = QtWidgets.QAction( QtGui.QIcon(Icons.new_file), "New Task",     self)
        saveAction   = QtWidgets.QAction(QtGui.QIcon(Icons.save_file), "Save Task",    self)
        saveAsAction = QtWidgets.QAction(QtGui.QIcon(Icons.save_file), "Save Task As", self)
        loadAction   = QtWidgets.QAction(QtGui.QIcon(Icons.load_file), "Load Task",    self)
        forumAction  = QtWidgets.QAction("Visit the forum!", self)

        newAction.triggered.connect(    self.newTask)
        saveAction.triggered.connect(   self.saveTask)
        saveAsAction.triggered.connect( lambda: self.saveTask(True))
        loadAction.triggered.connect(   self.loadTask)
        forumAction.triggered.connect(  lambda: webbrowser.open("https://forum.ufactory.cc/", new=0, autoraise=True))

        fileMenu.addAction(newAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(saveAsAction)
        fileMenu.addAction(loadAction)
        fileMenu.addAction(forumAction)
        menuBar.addMenu(fileMenu)


        # Create Toolbar
        toolbar = self.addToolBar("MainToolbar")

        settingsBtn  = QtWidgets.QAction( QtGui.QIcon(Icons.settings), 'Open Camera and Robot settings (Ctrl+T)', self)
        calibrateBtn = QtWidgets.QAction(QtGui.QIcon(Icons.calibrate), 'Open Robot and Camera Calibration Center', self)
        objMngrBtn   = QtWidgets.QAction(QtGui.QIcon(Icons.objectManager), 'Open Computer Vision Object Manager', self)

        self.scriptToggleBtn.setShortcut('Ctrl+R')
        self.videoToggleBtn.setShortcut( 'Ctrl+P')
        settingsBtn.setShortcut('Ctrl+S')
        calibrateBtn.setShortcut('Ctrl+C')
        objMngrBtn.setShortcut('Ctrl+O')

        self.scriptToggleBtn.triggered.connect( lambda: self.setScript("toggle"))
        self.videoToggleBtn.triggered.connect(  lambda: self.setVideo("toggle"))
        settingsBtn.triggered.connect( self.openSettings)
        calibrateBtn.triggered.connect(self.openCalibrations)
        objMngrBtn.triggered.connect(self.openObjectManager)

        toolbar.addAction(self.scriptToggleBtn)
        toolbar.addAction(self.videoToggleBtn)
        toolbar.addAction(settingsBtn)
        toolbar.addAction(calibrateBtn)
        toolbar.addAction(objMngrBtn)

        # Create the main layout
        self.setCentralWidget(self.dashboardView)


        # Final touches
        self.setWindowTitle('uArm Creator Dashboard')
        self.setWindowIcon(QtGui.QIcon(Icons.taskbar))
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


        # If a new robot has been set, set it and reconnect to the new robot.
        if isNew("robotID"):
            printf("MainWindow.closeSettingsView(): Changing robotID from ",
                  self.settings["robotID"], "to", newSettings["robotID"])
            self.settings["robotID"] = newSettings["robotID"]
            self.env.getRobot().setUArm(self.settings["robotID"])


        # If a new file has been opened, change the Settings file to reflect that so next time GUI is opened, so is file
        if isNew("lastOpenedFile"):
            printf("MainWindow.setSettings(): Loading file ", str(newSettings["lastOpenedFile"]))
            self.settings["lastOpenedFile"] = newSettings["lastOpenedFile"]
            self.loadTask(filename=self.settings["lastOpenedFile"])


        # If a calibration of type Motion has been changed, reflect this in the settings
        if isNew("motionCalibrations"):
            print("Motioncalibrations asked!")
            self.settings["motionCalibrations"] = newSettings["motionCalibrations"]


        # Save settings to a config file
        self.saveSettings()

    def setVideo(self, state):
        # Change the state of the videostream. The state can be play, pause, or simply "toggle
        printf("MainWindow.setVideo(): Setting video to state: ", state)

        # Don't change anything if no camera ID has been added yet
        if self.settings["cameraID"] is None: return


        if state == "toggle":
            if self.env.getVStream().paused:
                self.setVideo("play")
                return
            else:
                self.setVideo("pause")
                return


        vStream = self.env.getVStream()
        if state == "play":
            # Make sure the videoStream object has a camera, or if the cameras changed, change it
            if not vStream.connected() or not vStream.cameraID == self.settings["cameraID"]:
                success = vStream.setNewCamera(self.settings["cameraID"])
            # if not vStream.cameraID == self.settings["cameraID"]"


            self.dashboardView.cameraWidget.play()
            vStream.setPaused(False)
            self.videoToggleBtn.setIcon(QtGui.QIcon(Icons.pause_video))

        if state == "pause":
            self.dashboardView.cameraWidget.pause()
            vStream.setPaused(True)
            self.videoToggleBtn.setIcon(QtGui.QIcon(Icons.play_video))

    def setScript(self, state):
        # Run/pause the main script

        if state == "toggle":
            if self.interpreter.isRunning():
                self.endScript()
            else:
                self.startScript()
            return


    def startScript(self):
        if self.interpreter.isRunning():
                printf("MainWindow.setScript(): ERROR: Tried to start interpreter while it was already running.")
                return
        printf("MainWindow.setScript(): Interpreter is ready. Loading script and starting program")


        # Load the script, and get any relevant errors
        errors = self.interpreter.loadScript(self.env, self.controlPanel.getSaveData())


        # If there were during loading, present the user with the option to continue anyways
        if len(errors):
            # Generate a message for the user to explain what parameters are missing
            errorStr = 'Certain Events and Commands are missing the following requirements to work properly: \n\n' + \
                       ''.join(map(lambda err: '   -' + str(err) + '\n', errors)) + \
                       '\nWould you like to continue anyways? This may cause the program to behave erratically.'

            # Ask the user
            reply = QtWidgets.QMessageBox.question(self, 'Warning', errorStr,
                                QtWidgets.QMessageBox.Cancel | QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.Cancel:
                printf("MainWindow.startScript(): Script run canceled by user before starting.")
                return

        # Stop you from moving stuff around while script is running, and activate the visual cmmnd highlighting
        self.controlPanel.setScriptMode(True, self.interpreter.getStatus)
        self.interpreter.startThread()

        self.scriptToggleBtn.setIcon(QtGui.QIcon(Icons.pause_script))

    def endScript(self):
        self.interpreter.endThread()
        self.controlPanel.setScriptMode(False, self.interpreter.getStatus)

        self.scriptToggleBtn.setIcon(QtGui.QIcon(Icons.run_script))


    def openSettings(self):
        # This handles the opening and closing of the Settings window.
        printf("MainWindow.openSettings(): Opening Settings Window")

        self.endScript()
        self.setVideo("pause")  # If you don't pause video, scanning for cameras may crash the program

        settingsWindow = SettingsWindow(parent=self)
        accepted       = settingsWindow.exec_()

        if not accepted:
            printf('MainWindow.closeSettings(): "Cancel" clicked, no settings applied.')
            return

        printf('MainWindow.closeSettings(): "Apply" clicked, applying settings...')
        self.setSettings(settingsWindow.getSettings())

        # if success:
        #     self.setVideo("play")
        # else:
        #     self.setVideo("pause")


        self.setVideo("play")

    def openCalibrations(self):
        # This handles the opening and closing of the Calibrations window
        printf("MainWindow.openCalibrations(): Opening Calibrations Window")

        self.endScript()
        self.setVideo("pause")

        calibrationsWindow = CalibrateWindow(self.env, parent=self)
        accepted           = calibrationsWindow.exec_()

        if accepted:
            printf('MainWindow.openCalibrations(): "Apply" clicked, applying calibrations...')
            self.setSettings(calibrationsWindow.getSettings())
        else:
            printf('MainWindow.openCalibrations(): "Cancel" clicked, no calibrations applied.')

        self.setVideo("play")

    def openObjectManager(self):
        # This handles the opening and closing of the ObjectManager window
        printf("MainWindow.openCalibrations(): Opening ObjectManager Window")

        self.endScript()

        # Make sure video thread is active and playing, but that the actual cameraWidget
        self.setVideo("play")
        self.dashboardView.cameraWidget.pause()
        objMngrWindow = ObjectManager(self.env, parent=self)
        accepted      = objMngrWindow.exec_()

        self.setVideo("play")


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
        self.endScript()  # Make sure a script isn't running while you try to load something

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

    def closeEvent(self, event):
        # When window is closed, prompt for save, close the video stream, and close the control panel (thus script)
        self.interpreter.endThread()
        self.promptSave()
        self.env.close()



class Application(QtWidgets.QApplication):
    """
        Application subclass, to record key presses/releases
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





