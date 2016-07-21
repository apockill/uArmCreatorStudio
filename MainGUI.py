"""
This software was designed by Alexander Thiel
Github handle: https://github.com/apockill

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
__author__ = "Alexander Thiel"


import json         # For saving and loading settings and tasks
import sys          # For GUI, and overloading the default error handling
import webbrowser   # For opening the uFactory forums under the "file" menu
import ControlPanelGUI
from CommonGUI         import Console
from copy              import deepcopy                  # For copying saves and comparing later
from PyQt5             import QtCore, QtWidgets, QtGui  # All GUI things
from CalibrationsGUI   import CalibrateWindow           # For opening Calibrate window
from CameraGUI         import CameraWidget              # General GUI purposes
from Logic             import Global, Paths             # For keeping track of keypresses
from Logic.Environment import Environment               # Contains important variables
from Logic.Interpreter import Interpreter               # For actually starting/stopping the script
from Logic.Global      import printf                    # For my personal printing format
from Logic.Robot       import getConnectedRobots        # For settingsWindow
from Logic.Video       import getConnectedCameras       # For settingsWindow
from ObjectManagerGUI  import ObjectManagerWindow       # For opening ObjectManager window


########## MAIN WINDOW ##########
class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        # This is the format of an empty settings variable. It is filled in self.loadSettings() if settings exist.



        self.settings = None
        # Init self and objects.
        self.fileName    = None
        self.loadData    = []  #Set when file is loaded. Used to check if the user has changed anything and prompt
        self.env         = Environment()
        self.interpreter = Interpreter(self.env)


        # Set Global UI Variables
        self.programTitle    = 'uArm Creator Studio'
        self.scriptToggleBtn = QtWidgets.QAction(QtGui.QIcon(Paths.run_script), 'Run', self)
        self.videoToggleBtn  = QtWidgets.QAction(QtGui.QIcon(Paths.play_video), 'Video', self)
        self.centralWidget   = QtWidgets.QStackedWidget()
        self.controlPanel    = ControlPanelGUI.ControlPanel(self.env, parent=self)
        self.cameraWidget    = CameraWidget(self.env.getVStream().getFilteredWithID, parent=self)
        self.consoleWidget   = Console(self.env.getSetting('consoleSettings'), parent=self)


        # Connect the consoleWidget with the global print function, so the consoleWidget prints everything
        Global.printRedirectFunc = self.consoleWidget.write
        self.consoleWidget.setExecFunction(self.interpreter.evaluateExpression)


        # Create Menu items, and set the Dashboard as the main widget
        self.initUI()
        self.setVideo("play")


        # If any file is specified in "lastOpenedFile" then load it.
        if self.env.getSetting("lastOpenedFile") is not None:
            self.loadTask(filename=self.env.getSetting("lastOpenedFile"))

    def initUI(self):
        # Create "File" Menu
        menuBar       = self.menuBar()

        # Connect any slots that need connecting
        self.consoleWidget.settingsChanged.connect(lambda: self.env.updateSettings("consoleSettings",
                                                                                   self.consoleWidget.settings))

        # Create File Menu and actions
        fileMenu      = menuBar.addMenu('File')
        newAction     = QtWidgets.QAction( QtGui.QIcon(Paths.file_new),     "New Task", self)
        saveAction    = QtWidgets.QAction(QtGui.QIcon(Paths.file_save),    "Save Task", self)
        saveAsAction  = QtWidgets.QAction(QtGui.QIcon(Paths.file_save), "Save Task As", self)
        loadAction    = QtWidgets.QAction(QtGui.QIcon(Paths.file_load),    "Load Task", self)

        saveAction.setShortcut("Ctrl+S")

        # Connect file menu actions
        newAction.triggered.connect(    lambda: self.newTask(promptSave=True))
        saveAction.triggered.connect(   self.saveTask)
        saveAsAction.triggered.connect( lambda: self.saveTask(True))
        loadAction.triggered.connect(   self.loadTask)

        # Add file menu actions
        fileMenu.addAction(newAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(saveAsAction)
        fileMenu.addAction(loadAction)



        # Create Community Menu
        communityMenu = menuBar.addMenu('Community')
        forumAction   = QtWidgets.QAction(QtGui.QIcon(Paths.taskbar), "Visit the forum!", self)
        redditAction  = QtWidgets.QAction(QtGui.QIcon(Paths.reddit_link), "Visit our subreddit!", self)

        # Connect community menu actions
        forumAction.triggered.connect(  lambda: webbrowser.open("https://forum.ufactory.cc/", new=0, autoraise=True))
        redditAction.triggered.connect(lambda: webbrowser.open("https://www.reddit.com/r/uArm/", new=0, autoraise=True))

        # Add community menu actions
        communityMenu.addAction(forumAction)
        communityMenu.addAction(redditAction)



        # Add menus to menuBar
        menuBar.addMenu(fileMenu)
        menuBar.addMenu(communityMenu)



        # Create Toolbar
        toolbar = self.addToolBar("MainToolbar")
        toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

        settingsBtn  = QtWidgets.QAction(QtGui.QIcon(Paths.settings), 'Settings', self)
        calibrateBtn = QtWidgets.QAction(QtGui.QIcon(Paths.calibrate), 'Calibrate', self)
        objMngrBtn   = QtWidgets.QAction(QtGui.QIcon(Paths.objectManager), 'Resources', self)

        self.scriptToggleBtn.setToolTip('Run/Pause the command script (Ctrl+R)')
        self.videoToggleBtn.setToolTip('Play/Pause the video stream and Vision tracking')
        settingsBtn.setToolTip('Open Camera and Robot settings',)
        calibrateBtn.setToolTip('Open Robot and Camera Calibration Center')
        objMngrBtn.setToolTip('Open Resource Manager')

        self.scriptToggleBtn.setShortcut('Ctrl+R')


        self.scriptToggleBtn.triggered.connect(self.toggleScript)
        self.videoToggleBtn.triggered.connect(lambda: self.setVideo("toggle"))
        settingsBtn.triggered.connect(self.openSettings)
        calibrateBtn.triggered.connect(self.openCalibrations)
        objMngrBtn.triggered.connect(self.openObjectManager)

        toolbar.addAction(self.scriptToggleBtn)
        toolbar.addAction(self.videoToggleBtn)
        toolbar.addAction(settingsBtn)
        toolbar.addAction(calibrateBtn)
        toolbar.addAction(objMngrBtn)



        # TEST QDOCKWIDGETS HEERE
        cameraDock = QtWidgets.QDockWidget()
        cameraDock.setWidget(self.cameraWidget)
        cameraDock.setWindowTitle("Camera")
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, cameraDock)


        consoleDock = QtWidgets.QDockWidget()
        consoleDock.setWidget(self.consoleWidget)
        consoleDock.setWindowTitle("Console")
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, consoleDock)

        self.tabifyDockWidget(consoleDock, cameraDock)


        # Create the main layout
        self.setCentralWidget(self.controlPanel)


        # Final touches
        self.setWindowTitle(self.programTitle)
        self.setWindowIcon(QtGui.QIcon(Paths.taskbar))
        self.show()



    def setVideo(self, state):
        """
        Change the state of the videostream. The state can be play, pause, or simply "toggle
        :param state: "play", "pause", or "toggle"
        :return:
        """

        printf("Setting video to state: ", state)

        # Don't change anything if no camera ID has been added yet
        cameraID = self.env.getSetting("cameraID")
        if cameraID is None: return


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
            if not vStream.connected() or not vStream.cameraID == cameraID:
                vStream.setNewCamera(cameraID)

            self.cameraWidget.play()
            vStream.setPaused(False)
            self.videoToggleBtn.setIcon(QtGui.QIcon(Paths.pause_video))
            self.videoToggleBtn.setText("Pause")

        if state == "pause":
            self.cameraWidget.pause()
            vStream.setPaused(True)
            self.videoToggleBtn.setIcon(QtGui.QIcon(Paths.play_video))
            self.videoToggleBtn.setText("Play")


    def toggleScript(self):
        # Run/pause the main script
        if self.interpreter.threadRunning():
            self.endScript()
        else:
            self.startScript()

    def startScript(self):
        if self.interpreter.threadRunning():
                printf("ERROR: Tried to start interpreter while it was already running.")
                return
        printf("Interpreter is ready. Loading script and starting program")

        # Make sure the vision filters are activated
        vision = self.env.getVision()


        # Load the script, and get any relevant errors
        errors = self.interpreter.loadScript(self.controlPanel.getSaveData())


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
                       '\nWould you like to continue anyways? Events and commands with errors may not activate.'
            # # .join(map(lambda err: '   -' + str(err) + '\n', errors)) + \
            # Ask the user
            reply = QtWidgets.QMessageBox.question(self, 'Warning', errorStr,
                                QtWidgets.QMessageBox.Cancel | QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.Cancel:
                printf("Script run canceled by user before starting.")
                vision.endAllTrackers()
                return



        # Stop you from moving stuff around while script is running, and activate the visual cmmnd highlighting
        self.controlPanel.setScriptModeOn(self.interpreter.getStatus, self.endScript)
        self.interpreter.startThread()



        # Make sure the UI matches the state of the script
        self.scriptToggleBtn.setIcon(QtGui.QIcon(Paths.pause_script))
        self.scriptToggleBtn.setText("Stop")

    def endScript(self):
        vision = self.env.getVision()
        robot = self.env.getRobot()

        self.interpreter.endThread()
        self.controlPanel.setScriptModeOff()

        # Turn off the gripper, just in case. Do this AFTER interpreter ends, so as to not use Serial twice...
        robot.setGripper(False)
        robot.setActiveServos(all=False)

        # Make sure vision filters are stopped
        vision.endAllTrackers()


        self.scriptToggleBtn.setIcon(QtGui.QIcon(Paths.run_script))
        self.scriptToggleBtn.setText("Run")



    def openSettings(self):
        # This handles the opening and closing of the Settings window.
        printf("Opening Settings Window")

        self.endScript()
        self.setVideo("pause")  # If you don't pause video, scanning for cameras may crash the program

        settingsWindow = SettingsWindow(parent=self)
        accepted       = settingsWindow.exec_()

        self.setVideo("play")
        if not accepted:
            printf("Cancel clicked, no settings applied.")
            return

        printf("Apply clicked, applying settings...")
        self.env.updateSettings("robotID", settingsWindow.getRobotSetting())
        self.env.updateSettings("cameraID", settingsWindow.getCameraSetting())

        vStream = self.env.getVStream()
        vStream.setNewCamera(self.env.getSetting('cameraID'))


        # If the robots not connected, attempt to reestablish connection
        robot   = self.env.getRobot()
        if not robot.connected():
            robot.setUArm(self.env.getSetting('robotID'))



        self.setVideo("play")

    def openCalibrations(self):
        # This handles the opening and closing of the Calibrations window
        printf("Opening Calibrations Window")

        self.endScript()
        self.setVideo("pause")

        coordSettings = self.env.getSetting("coordCalibrations")
        motionSettings = self.env.getSetting("motionCalibrations")
        calibrationsWindow = CalibrateWindow(coordSettings, motionSettings, self.env, parent=self)
        accepted           = calibrationsWindow.exec_()

        if accepted:
            # Update all the settings
            printf("Apply clicked, applying calibrations...")

            # Update the settings
            self.env.updateSettings("coordCalibrations", calibrationsWindow.getCoordSettings())
            self.env.updateSettings("motionCalibrations", calibrationsWindow.getMotionSettings())

        else:
            printf("Cancel clicked, no calibrations applied.")

        self.setVideo("play")

    def openObjectManager(self):
        # This handles the opening and closing of the ObjectManager window
        printf("Opening ObjectManager Window")

        self.endScript()

        # Make sure video thread is active and playing, but that the actual cameraWidget
        self.setVideo("play")
        self.cameraWidget.pause()
        objMngrWindow = ObjectManagerWindow(self.env, self)
        accepted      = objMngrWindow.exec_()
        objMngrWindow.close()
        objMngrWindow.deleteLater()
        self.setVideo("play")



    def newTask(self, promptSave):
        if promptSave:
            cancelPressed = self.promptSave()
            if cancelPressed:  # If the user cancelled the close
                return

        self.controlPanel.loadData([])
        self.fileName = None
        self.loadData = deepcopy(self.controlPanel.getSaveData())

    def saveTask(self, promptSaveLocation):
        printf("Saving project")

        # If there is no filename, ask for one
        if promptSaveLocation or self.fileName is None:
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Task", "MyTask", "Task (*.task)")
            if filename == "": return False  #If user hit cancel
            self.fileName = filename
            self.env.updateSettings("lastOpenedFile", self.fileName)


        # Update the save file
        saveData = self.controlPanel.getSaveData()
        json.dump(saveData, open(self.fileName, 'w'), sort_keys=False, indent=3, separators=(',', ': '))

        self.loadData = deepcopy(saveData)  #Update what the latest saved changes are


        printf("Project Saved")

        self.setWindowTitle(self.programTitle + '       ' + self.fileName)

        return True

    def loadTask(self,  **kwargs):
        # Load a save file

        self.endScript()  # Make sure a script isn't running while you try to load something

        printf("Loading project")

        filename = kwargs.get("filename", None)

        # If there's no filename given, then prompt the user for what to name the task
        if filename is None:  #If no filename was specified, prompt the user for where to save
            filename, filetype = QtWidgets.QFileDialog.getOpenFileName(self, "Load Task", "", "*.task")
            if filename == "": return  #If user hit cancel
            printf("Project Loaded:")

        try:
            self.loadData = json.load( open(filename))
        except IOError:
            printf("ERROR: Task file ", filename, "not found!")
            self.fileName = None
            self.env.updateSettings("lastOpenedFile", None)
            return






        # Load the data- BUT MAKE SURE TO DEEPCOPY otherwise any change in the program will change in self.loadData
        try:
            self.controlPanel.loadData(deepcopy(self.loadData))
            self.fileName = filename
            self.env.updateSettings("lastOpenedFile", filename)
            self.setWindowTitle(self.programTitle + '      ' + self.fileName)
        except Exception as e:
            printf("ERROR: Could not load task: ", e)
            self.newTask(promptSave=False)
            QtWidgets.QMessageBox.question(self, 'Warning', "The program was unable to load the following script:\n" +
                                    filename + "\n\n The following error occured: " + str(e), QtWidgets.QMessageBox.Ok)



    def promptSave(self):
        # Prompts the user if they want to save, but only if they've changed something in the program
        # Returns True if the user presses Cancel or "X", and wants the window to stay open.


        if not self.loadData == self.controlPanel.getSaveData():
            printf("Prompting user to save changes")
            reply = QtWidgets.QMessageBox.question(self, 'Warning',
                                    "You have unsaved changes. Would you like to save before continuing?",
                                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel,
                                    QtWidgets.QMessageBox.Yes)

            if reply == QtWidgets.QMessageBox.Yes:
                printf("Saving changes")
                success = self.saveTask(False)
                return not success

            if reply == QtWidgets.QMessageBox.No:
                printf("Not saving changes")

            if reply == QtWidgets.QMessageBox.Cancel:
                printf("User canceled- aborting close!")
                return True

    def closeEvent(self, event):
        # When window is closed, prompt for save, close the video stream, and close the control panel (thus script)
        self.endScript()

        # Ask the user they want to save before closing anything
        cancelPressed = self.promptSave()
        if cancelPressed:  # If the user cancelled the close
            event.ignore()
            return

        robot = self.env.getRobot()
        robot.setActiveServos(all=False)

        # Close and delete GUI objects, to stop their events from running
        self.cameraWidget.close()
        self.controlPanel.close()
        self.centralWidget.close()
        self.centralWidget.deleteLater()


        # Close threads
        self.env.close()

        printf("Done closing all objects and threads.")



##########    VIEWS    ##########
class SettingsWindow(QtWidgets.QDialog):
    """
    Simple view that lets you select your robot and camera.
    The Apply/Cancel buttons are connected in the MainWindow class, which is why they are 'self' variables
    """

    def __init__(self, parent):
        super(SettingsWindow, self).__init__(parent)
        self.robSetting = None  # New robotID
        self.camSetting = None  # New cameraID
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
        printf("Connected Devices: ", connectedDevices)
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
        self.camSetting = self.cameraButtonGroup.checkedId()

    def robButtonClicked(self):
        self.robSetting = str(self.robotButtonGroup.checkedButton().text())


    def clearLayout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            child.widget().deleteLater()

    def getRobotSetting(self):
        return self.robSetting

    def getCameraSetting(self):
        return self.camSetting


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
    # app.setStyleSheet(fancyqt.firefox.style)


    # Set Application Font
    font = QtGui.QFont()
    font.setFamily("Verdana")
    font.setPixelSize(12)
    app.setFont(font)

    # Initialize global variables
    Global.init()

    # Start application
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())





