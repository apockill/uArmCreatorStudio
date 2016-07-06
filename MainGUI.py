# import qdarkstyle
import json         # For saving and loading settings and tasks
import sys          # For GUI, and overloading the default error handling
import webbrowser   # For opening the uFactory forums under the "file" menu
import ControlPanelGUI, Paths
from copy              import deepcopy                  # For copying saves and comparing later
from PyQt5             import QtCore, QtWidgets, QtGui  # All GUI things
from CameraGUI         import CameraWidget              # General GUI purposes
from ObjectManagerGUI  import ObjectManagerWindow       # For opening ObjectManager window
from CalibrationsGUI   import CalibrateWindow           # For opening Calibrate window
from Logic             import Global                    # For keeping track of keypresses
from Logic.Environment import Environment, Interpreter  # For Logic purposes
from Logic.Global      import printf                    # For my personal printing format
from Logic.Robot       import getConnectedRobots        # For settingsWindow
from Logic.Video       import getConnectedCameras       # For settingsWindow



########## MAIN WINDOW ##########
class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        # This is the format of an empty settings variable. It is filled in self.loadSettings() if settings exist.
        self.settings       = {
                                 # LOGIC RELATED SETTINGS
                                 "robotID":            None,                     # COM port of the robot

                                 "cameraID":           None,                     # The # of the camera for cv to connect

                                 "objectsDirectory":   Paths.objects_dir,    # Default directory for saving objects

                                 "motionCalibrations": {"stationaryMovement": None,
                                                        "activeMovement": None},

                                 "coordCalibrations":  {"ptPairs":   None,   # Pairs of Camera pts and Robot pts
                                                        "failPts":   None,   # Coordinate's where robot can't be seen
                                                        "groundPos": None},  # The "Ground" position, in [x,y,z]

                                 # GUI RELATED SETTINGS
                                 "lastOpenedFile":      None
                               }

        # Load settings
        configExists = self.loadSettings()


        # Init self and objects. All objects should be capable of being started w/o filled out settings
        self.fileName    = None
        self.loadData    = []  #Set when file is loaded. Used to check if the user has changed anything and prompt
        self.env         = Environment(self.settings)
        self.interpreter = Interpreter()


        # Set Global UI Variables
        self.programTitle    = 'uArm Creator Studio'
        self.scriptToggleBtn = QtWidgets.QAction(QtGui.QIcon(Paths.run_script), 'Run', self)
        self.videoToggleBtn  = QtWidgets.QAction(QtGui.QIcon(Paths.play_video), 'Video', self)
        self.centralWidget   = QtWidgets.QStackedWidget()
        self.controlPanel    = ControlPanelGUI.ControlPanel(self.env, self.settings, parent=self)
        self.dashboardView   = DashboardView(self.controlPanel,
                                             CameraWidget(self.env.getVStream().getFilteredWithID, parent=self),
                                             parent=self)


        # Create Menu items, and set the Dashboard as the main widget
        self.initUI()
        self.setVideo("play")


        # If any file is specified in "lastOpenedFile" then load it.
        if self.settings["lastOpenedFile"] is not None:
            self.loadTask(filename=self.settings["lastOpenedFile"])


        # If there is no settings File, then open the settings window first thing
        if not configExists:
            self.openSettingsWindow()

    def initUI(self):
        # Create "File" Menu
        menuBar      = self.menuBar()
        fileMenu     = menuBar.addMenu('File')

        newAction    = QtWidgets.QAction(QtGui.QIcon(Paths.new_file), "New Task", self)
        saveAction   = QtWidgets.QAction(QtGui.QIcon(Paths.save_file), "Save Task", self)
        saveAsAction = QtWidgets.QAction(QtGui.QIcon(Paths.save_file), "Save Task As", self)
        loadAction   = QtWidgets.QAction(QtGui.QIcon(Paths.load_file), "Load Task", self)
        forumAction  = QtWidgets.QAction(QtGui.QIcon(Paths.taskbar), "Visit the forum!", self)
        redditAction = QtWidgets.QAction(QtGui.QIcon(Paths.reddit_link), "Visit our subreddit!", self)

        newAction.triggered.connect(    lambda: self.newTask(promptSave=True))
        saveAction.triggered.connect(   self.saveTask)
        saveAsAction.triggered.connect( lambda: self.saveTask(True))
        loadAction.triggered.connect(   self.loadTask)
        forumAction.triggered.connect(  lambda: webbrowser.open("https://forum.ufactory.cc/", new=0, autoraise=True))
        redditAction.triggered.connect(lambda: webbrowser.open("https://www.reddit.com/r/uArm/", new=0, autoraise=True))



        fileMenu.addAction(newAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(saveAsAction)
        fileMenu.addAction(loadAction)
        fileMenu.addAction(forumAction)
        fileMenu.addAction(redditAction)
        menuBar.addMenu(fileMenu)


        # Create Toolbar
        toolbar = self.addToolBar("MainToolbar")
        toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

        settingsBtn  = QtWidgets.QAction(QtGui.QIcon(Paths.settings), 'Settings', self)
        calibrateBtn = QtWidgets.QAction(QtGui.QIcon(Paths.calibrate), 'Calibrate', self)
        objMngrBtn   = QtWidgets.QAction(QtGui.QIcon(Paths.objectManager), 'Resources', self)

        self.scriptToggleBtn.setToolTip('Run/Pause the command script (Ctrl+R)')
        self.videoToggleBtn.setToolTip('Play/Pause the video stream (Ctrl+P)')
        settingsBtn.setToolTip('Open Camera and Robot settings (Ctrl+T)',)
        calibrateBtn.setToolTip('Open Robot and Camera Calibration Center')
        objMngrBtn.setToolTip('Open Resource Manager')

        self.scriptToggleBtn.setShortcut('Ctrl+R')
        self.videoToggleBtn.setShortcut( 'Ctrl+P')
        settingsBtn.setShortcut('Ctrl+S')
        calibrateBtn.setShortcut('Ctrl+C')
        objMngrBtn.setShortcut('Ctrl+O')

        self.scriptToggleBtn.triggered.connect( lambda: self.setScript("toggle"))
        self.videoToggleBtn.triggered.connect(  lambda: self.setVideo("toggle"))
        settingsBtn.triggered.connect(self.openSettingsWindow)
        calibrateBtn.triggered.connect(self.openCalibrationsWindow)
        objMngrBtn.triggered.connect(self.openObjectManagerWindow)

        toolbar.addAction(self.scriptToggleBtn)
        toolbar.addAction(self.videoToggleBtn)
        toolbar.addAction(settingsBtn)
        toolbar.addAction(calibrateBtn)
        toolbar.addAction(objMngrBtn)

        # Create the main layout
        self.setCentralWidget(self.dashboardView)


        # Final touches
        self.setWindowTitle(self.programTitle)
        self.setWindowIcon(QtGui.QIcon(Paths.taskbar))
        self.show()


    def setSettings(self, newSettings):
        # Apply settings

        # Create a quick function that will check if a setting has been changed. If it has, an action will be taken.
        isNew = lambda key: (key in newSettings) and (newSettings[key] is not None) and \
                            (not self.settings[key] == newSettings[key])

        # If settings change, then save the changes to the config file
        settingsChanged = False


        # If camera has been changed
        if isNew("cameraID"):
            settingsChanged = True
            printf("MainWindow.setSettings(): Changing cameraID from ",
                  self.settings["cameraID"], "to", newSettings["cameraID"])
            self.settings["cameraID"] = newSettings["cameraID"]


        # If a new robot has been set, set it and reconnect to the new robot.
        if isNew("robotID"):
            settingsChanged = True
            printf("MainWindow.setSettings(): Changing robotID from ",
                  self.settings["robotID"], "to", newSettings["robotID"])
            self.settings["robotID"] = newSettings["robotID"]



        # If a new file has been opened, change the Settings file to reflect that so next time GUI is opened, so is file
        if isNew("lastOpenedFile"):
            settingsChanged = True
            printf("MainWindow.setSettings(): Loading file ", str(newSettings["lastOpenedFile"]))
            self.settings["lastOpenedFile"] = newSettings["lastOpenedFile"]
            # self.loadTask(filename=self.settings["lastOpenedFile"])


        # If a calibration of type Motion has been changed, reflect this in the settings
        if isNew("motionCalibrations"):
            settingsChanged = True
            printf("MainWindow.setSettings(): Updating Motion Calibrations!")
            self.settings["motionCalibrations"] = newSettings["motionCalibrations"]

        if isNew("coordCalibrations"):
            settingsChanged = True
            self.settings["coordCalibrations"] = newSettings["coordCalibrations"]

        # Save settings to a config file
        if settingsChanged:
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
            self.videoToggleBtn.setIcon(QtGui.QIcon(Paths.pause_video))
            self.videoToggleBtn.setText("Pause")

        if state == "pause":
            self.dashboardView.cameraWidget.pause()
            vStream.setPaused(True)
            self.videoToggleBtn.setIcon(QtGui.QIcon(Paths.play_video))
            self.videoToggleBtn.setText("Play")

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


        # Make sure the vision filters are activated
        vision = self.env.getVision()
        vision.clearTargets()
        vision.addTrackerFilter()

        # Load the script, and get any relevant errors
        errors = self.interpreter.loadScript(self.env, self.controlPanel.getSaveData())


        # If there were during loading, present the user with the option to continue anyways
        if len(errors):
            errorText = ""
            for error, errorObjects in errors.items():
                errorText += "" + str(error) + "\n"
                for errObject in list(set(errorObjects)):
                    errorText += "     " + str(errObject) + "\n"
                errorText += '\n'

            # Generate a message for the user to explain what parameters are missing
            errorStr = 'Certain Events and Commands are missing the following requirements to work properly: \n\n' + \
                       ''.join(errorText) + \
                       '\nWould you like to continue anyways? Certain events and commands may not activate.'
            # # .join(map(lambda err: '   -' + str(err) + '\n', errors)) + \
            # Ask the user
            reply = QtWidgets.QMessageBox.question(self, 'Warning', errorStr,
                                QtWidgets.QMessageBox.Cancel | QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.Cancel:
                printf("MainWindow.startScript(): Script run canceled by user before starting.")
                return

        # Stop you from moving stuff around while script is running, and activate the visual cmmnd highlighting
        self.controlPanel.setScriptModeOn(self.interpreter.getStatus, self.endScript)
        self.interpreter.startThread(self.env.getRobot(), self.env.getVision())



        # Make sure the UI matches the state of the script
        self.scriptToggleBtn.setIcon(QtGui.QIcon(Paths.pause_script))
        self.scriptToggleBtn.setText("Stop")

    def endScript(self):
        vision = self.env.getVision()

        robot = self.env.getRobot()
        self.interpreter.endThread(robot, vision)
        self.controlPanel.setScriptModeOff()

        # Turn off the gripper, just in case. Do this AFTER interpreter ends, so as to not use Serial twice...
        robot.setGripper(False)
        robot.setActiveServos(all=False)
        # Make sure vision filters are stopped

        vision.endTrackerFilter()


        self.scriptToggleBtn.setIcon(QtGui.QIcon(Paths.run_script))
        self.scriptToggleBtn.setText("Run")


    def openSettingsWindow(self):
        # This handles the opening and closing of the Settings window.
        printf("MainWindow.openSettings(): Opening Settings Window")

        self.endScript()
        self.setVideo("pause")  # If you don't pause video, scanning for cameras may crash the program

        settingsWindow = SettingsWindow(parent=self)
        accepted       = settingsWindow.exec_()

        self.setVideo("play")
        if not accepted:
            printf('MainWindow.closeSettings(): "Cancel" clicked, no settings applied.')
            return

        printf('MainWindow.closeSettings(): "Apply" clicked, applying settings...')
        self.setSettings(settingsWindow.getSettings())

        vStream = self.env.getVStream()
        vStream.setNewCamera(self.settings['cameraID'])


        # If the robots not connected, attempt to reestablish connection
        robot   = self.env.getRobot()
        if not robot.connected():
            robot.setUArm(self.settings['robotID'])



        self.setVideo("play")

    def openCalibrationsWindow(self):
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

    def openObjectManagerWindow(self):
        # This handles the opening and closing of the ObjectManager window
        printf("MainWindow.openCalibrations(): Opening ObjectManager Window")

        self.endScript()

        # Make sure video thread is active and playing, but that the actual cameraWidget
        self.setVideo("play")
        self.dashboardView.cameraWidget.pause()
        objMngrWindow = ObjectManagerWindow(self.env, self)
        accepted      = objMngrWindow.exec_()
        objMngrWindow.close()
        objMngrWindow.deleteLater()
        self.setVideo("play")


    def newTask(self, promptSave):
        if promptSave:
            self.promptSave()

        self.dashboardView.controlPanel.loadData([])
        self.fileName = None
        self.loadData = deepcopy(self.controlPanel.getSaveData())

    def saveTask(self, promptSaveLocation):
        printf("MainWindow.saveTask(): Saving project")

        # If there is no filename, ask for one
        if promptSaveLocation or self.fileName is None:
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Task", "MyTask", "Task (*.task)")
            if filename == "": return  #If user hit cancel
            self.fileName = filename
            self.setSettings({'lastOpenedFile': self.fileName})


        # Update the save file
        saveData = self.controlPanel.getSaveData()
        json.dump(saveData, open(self.fileName, 'w'), sort_keys=False, indent=3, separators=(',', ': '))

        self.loadData = deepcopy(saveData)  #Update what the latest saved changes are


        printf("MainWindow.saveTask(): Project Saved")

        self.setWindowTitle(self.programTitle + '       ' + self.fileName)
        # self.saveSettings()

    def loadTask(self,  **kwargs):
        # Load a save file

        self.endScript()  # Make sure a script isn't running while you try to load something

        printf("MainWindow.loadTask(): Loading project")

        filename = kwargs.get("filename", None)

        # If there's no filename given, then prompt the user for what to name the task
        if filename is None:  #If no filename was specified, prompt the user for where to save
            filename, filetype = QtWidgets.QFileDialog.getOpenFileName(self, "Load Task", "", "*.task")
            if filename == "": return  #If user hit cancel
            printf("MainWindow.save(): Project Loaded:")

        try:
            self.loadData = json.load( open(filename))
        except IOError:
            printf("MainWindow.loadTask(): ERROR: Task file ", filename, "not found!")
            self.fileName = None
            self.setSettings({"lastOpenedFile": None})
            return






        # Load the data- BUT MAKE SURE TO DEEPCOPY otherwise any change in the program will change in self.loadData
        try:
            self.dashboardView.controlPanel.loadData(deepcopy(self.loadData))
            self.fileName = filename
            self.setSettings({"lastOpenedFile": filename})
            self.setWindowTitle(self.programTitle + '      ' + self.fileName)
        except Exception as e:
            printf("Mainwindow.loadTask(): ERROR: Could not load task: ", e)
            self.newTask(promptSave=False)
            QtWidgets.QMessageBox.question(self, 'Warning', "The program was unable to load the following script:\n" +
                                           filename, QtWidgets.QMessageBox.Ok)


    def saveSettings(self):
        printf("MainWindow.saveSettings(): Saving Settings")
        json.dump(self.settings, open(Paths.settings_txt, 'w'), sort_keys=False, indent=3, separators=(',', ': '))

    def loadSettings(self):
        # Load the settings config and set them
        printf("MainWindow.loadSettings(): Loading Settings")

        try:
            newSettings = json.load(open(Paths.settings_txt))
            # printf("MainWindow.loadSettings(): Loading settings: ", newSettings, "...")
            self.setSettings(newSettings)
            return True
        except IOError as e:
            printf("MainWindow.loadSettings(): No settings file detected. Using default values.")
            return False
        except ValueError as e:
            printf("MainWindow.loadSettings(): Error while loading an existing settings file. Using default values.")
            QtWidgets.QMessageBox.question(self, 'Error', "Could not load existing settings file."
                                                          "\nCreating a new one.", QtWidgets.QMessageBox.Ok)
            return False

    def promptSave(self):
        # Prompts the user if they want to save, but only if they've changed something in the program
        # Returns True if the user presses Cancel or "X", and wants the window to stay open.


        if not self.loadData == self.controlPanel.getSaveData():
            printf("MainWindow.promptSave(): Prompting user to save changes")
            reply = QtWidgets.QMessageBox.question(self, 'Warning',
                                    "You have unsaved changes. Would you like to save before continuing?",
                                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |QtWidgets.QMessageBox.Cancel,
                                    QtWidgets.QMessageBox.Yes)

            if reply == QtWidgets.QMessageBox.Yes:
                printf("MainWindow.promptSave():Saving changes")
                self.saveTask(False)

            if reply == QtWidgets.QMessageBox.No:
                printf("MainWindow.promptSave(): Not saving changes")

            if reply == QtWidgets.QMessageBox.Cancel:
                printf("MainWindow.promptSave(): User canceled- aborting close!")
                return True


    def closeEvent(self, event):
        # When window is closed, prompt for save, close the video stream, and close the control panel (thus script)


        # Ask the user they want to save before closing anything
        cancelPressed = self.promptSave()
        if cancelPressed:  # If the user cancelled the close
            event.ignore()
            return

        robot = self.env.getRobot()
        robot.setActiveServos(all=False)

        # Close and delete GUI objects, to stop their events from running
        self.dashboardView.close()
        self.dashboardView.deleteLater()
        self.centralWidget.close()
        self.centralWidget.deleteLater()


        # Close threads
        self.endScript()
        self.env.close()

        printf("MainWindow.close(): Done closing all objects and threads.")



##########    VIEWS    ##########
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
        robotScanBtn.clicked.connect(self.scanForRobotsClicked)
        cameraScanBtn.clicked.connect(self.scanForCamerasClicked)
        applyBtn.clicked.connect(self.accept)
        cancelBtn.clicked.connect(self.reject)


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
        self.setWindowIcon(QtGui.QIcon(Paths.settings))


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

    def closeEvent(self, event):
        self.cameraWidget.close()
        self.controlPanel.close()



##########    OTHER    ##########
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

    # Apply a theme of choice here
    # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    # Set Application Font
    font = QtGui.QFont()
    font.setFamily("Verdana")
    font.setPixelSize(12)
    app.setFont(font)


    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())





