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
import json            # For saving and loading settings and tasks
import sys             # For GUI, and overl`oading the default error handling
import webbrowser      # For opening the uFactory forums under the "file" menu
import ControlPanelGUI
import Paths
from CommonGUI         import Console
from copy              import deepcopy                  # For copying saves and comparing later
from PyQt5             import QtCore, QtWidgets, QtGui  # All GUI things
from CalibrationsGUI   import CalibrateWindow           # For opening Calibrate window
from CameraGUI         import CameraWidget              # General GUI purposes
from Logic             import Global                    # For keeping track of keypresses
from Logic.Environment import Environment               # Contains important variables
from Logic.Global      import printf                    # For my custom printing function
from Logic.Interpreter import Interpreter               # For actually starting/stopping the script
from Logic.Robot       import getConnectedRobots        # For deviceWindow
from Logic.Video       import getConnectedCameras       # For deviceWindow
from ObjectManagerGUI  import ObjectManagerWindow       # For opening ObjectManager window
from ObjectManagerGUI  import MakeGroupWindow           # For creating various resources
from ObjectManagerGUI  import MakeRecordingWindow
from ObjectManagerGUI  import MakeFunctionWindow
from ObjectManagerGUI  import MakeObjectWindow
__author__ = "Alexander Thiel"


########## MAIN WINDOW ##########
class MainWindow(QtWidgets.QMainWindow):
    # For debugging object count, use: print("CHILDREN: ", len(self.findChildren(QtCore.QObject)))
    def __init__(self):
        super(MainWindow, self).__init__()


        # Initialize the environment. Robot, camera, and objects will be loaded into the "logic" side of things
        self.env         = Environment(Paths.settings_txt, Paths.objects_dir, Paths.cascade_dir)
        self.interpreter = Interpreter(self.env)



        # Set the ConsoleWidget parameters immediately, so even early prints are captured
        self.consoleWidget       = Console(self.env.getSetting('consoleSettings'), parent=self)
        Global.printRedirectFunc = self.consoleWidget.write
        self.consoleWidget.setExecFunction(self.interpreter.evaluateExpression)


        # Create GUI related class variables
        self.fileName        = None
        self.loadData        = []  #Set when file is loaded. Used to check if the user has changed anything when closing
        self.programTitle    = 'uArm Creator Studio'
        self.scriptToggleBtn = QtWidgets.QAction(QtGui.QIcon(Paths.run_script), 'Run', self)
        self.devicesBtn      = QtWidgets.QAction(QtGui.QIcon(Paths.devices_neither), 'Devices', self)
        self.centralWidget   = QtWidgets.QStackedWidget()
        self.controlPanel    = ControlPanelGUI.ControlPanel(self.env, parent=self)
        self.cameraWidget    = CameraWidget(self.env.getVStream(), parent=self)
        self.floatingHint    = QtWidgets.QLabel()  # Used to display floating banners to inform the user of something


        # Create Menu items and set up the GUI
        self.cameraWidget.play()
        self.initUI()



        # After initUI: Restore the window geometry to the state it was when the user last closed the window
        if self.env.getSetting("windowGeometry") is not None:
            state = self.env.getSetting("windowGeometry")
            state = bytearray(state, 'utf-8')
            bArr = QtCore.QByteArray.fromHex(state)
            self.restoreGeometry(bArr)


        # After initUI: Restore size and position of dockwidgets to their previous state
        if self.env.getSetting("windowState") is not None:
            state = self.env.getSetting("windowState")
            state = bytearray(state, 'utf-8')
            bArr = QtCore.QByteArray.fromHex(state)
            self.restoreState(bArr)


        # If any file is specified in "lastOpenedFile" then load it.
        if self.env.getSetting("lastOpenedFile") is not None:
            self.loadTask(filename=self.env.getSetting("lastOpenedFile"))
        else:
            self.newTask(False)


        # Create a timer that checks the connected devices and updates the icon to reflect what is connected correctly
        self.refreshTimer = QtCore.QTimer()
        self.refreshTimer.timeout.connect(self.refreshDevicesIcon)
        self.refreshTimer.start(5000)  # Once every five seconds


    def initUI(self):
        # Create "File" Menu
        menuBar       = self.menuBar()

        # Connect any slots that need connecting
        self.consoleWidget.settingsChanged.connect(lambda: self.env.updateSettings("consoleSettings",
                                                                                   self.consoleWidget.settings))

        # Create File Menu and actions
        fileMenu      = menuBar.addMenu('File')
        newAction     = QtWidgets.QAction(QtGui.QIcon(Paths.file_new), "New Task", self)
        saveAction    = QtWidgets.QAction(QtGui.QIcon(Paths.file_save), "Save Task", self)
        saveAsAction  = QtWidgets.QAction(QtGui.QIcon(Paths.file_save), "Save Task As", self)
        loadAction    = QtWidgets.QAction(QtGui.QIcon(Paths.file_load), "Load Task", self)

        saveAction.setShortcut("Ctrl+S")

        newAction.triggered.connect(    lambda: self.newTask(promptSave=True))
        saveAction.triggered.connect(   self.saveTask)
        saveAsAction.triggered.connect( lambda: self.saveTask(True))
        loadAction.triggered.connect(   self.loadTask)


        fileMenu.addAction(newAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(saveAsAction)
        fileMenu.addAction(loadAction)



        # Create Community Menu
        communityMenu = menuBar.addMenu('Community')
        forumAction   = QtWidgets.QAction(QtGui.QIcon(Paths.taskbar), "Visit the forum!", self)
        redditAction  = QtWidgets.QAction(QtGui.QIcon(Paths.reddit_link), "Visit our subreddit!", self)

        forumAction.triggered.connect(  lambda: webbrowser.open("https://forum.ufactory.cc/", new=0, autoraise=True))
        redditAction.triggered.connect(lambda: webbrowser.open("https://www.reddit.com/r/uArm/", new=0, autoraise=True))

        communityMenu.addAction(forumAction)
        communityMenu.addAction(redditAction)


        # Create Resources Menu
        resourceMenu = menuBar.addMenu('New Resource')
        visAction  = QtWidgets.QAction(QtGui.QIcon(Paths.event_recognize), "Vision Object", self)
        grpAction  = QtWidgets.QAction(QtGui.QIcon(Paths.event_recognize), "Vision Group", self)
        recAction  = QtWidgets.QAction(QtGui.QIcon(Paths.record_start), "Movement Recording", self)
        fncAction  = QtWidgets.QAction(QtGui.QIcon(Paths.command_run_func), "Function", self)


        visAction.triggered.connect(  lambda: MakeObjectWindow(   None, self.env, parent=self))
        grpAction.triggered.connect(  lambda: MakeGroupWindow(    None, self.env, parent=self))
        recAction.triggered.connect(  lambda: MakeRecordingWindow(None, self.env, parent=self))
        fncAction.triggered.connect(  lambda: MakeFunctionWindow( None, self.env, parent=self))

        resourceMenu.addAction(visAction)
        resourceMenu.addAction(grpAction)
        resourceMenu.addAction(recAction)
        resourceMenu.addAction(fncAction)



        # Add menus to menuBar
        menuBar.addMenu(fileMenu)
        menuBar.addMenu(communityMenu)
        menuBar.addMenu(resourceMenu)


        # Create Toolbar
        toolbar = self.addToolBar("MainToolbar")
        toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

        calibrateBtn = QtWidgets.QAction(QtGui.QIcon(Paths.calibrate), 'Calibrate', self)
        objMngrBtn   = QtWidgets.QAction(QtGui.QIcon(Paths.objectManager), 'Resources', self)

        self.scriptToggleBtn.setToolTip('Run/Pause the command script (Ctrl+R)')
        self.devicesBtn.setToolTip('Open Camera and Robot settings',)
        calibrateBtn.setToolTip('Open Robot and Camera Calibration Center')
        objMngrBtn.setToolTip('Open Resource Manager')

        self.scriptToggleBtn.setShortcut('Ctrl+R')


        self.scriptToggleBtn.triggered.connect(self.toggleScript)
        self.devicesBtn.triggered.connect(self.openDevices)
        calibrateBtn.triggered.connect(self.openCalibrations)
        objMngrBtn.triggered.connect(self.openObjectManager)

        toolbar.addAction(self.scriptToggleBtn)
        toolbar.addAction(self.devicesBtn)
        toolbar.addAction(calibrateBtn)
        toolbar.addAction(objMngrBtn)



        # Add Camera Widget, as a QDockWidget
        def createDockWidget(widget, name):
            dockWidget = QtWidgets.QDockWidget()
            dockWidget.setObjectName(name)  # Without this, self.restoreState() won't work
            dockWidget.setWindowTitle(name)
            dockWidget.setWidget(widget)
            dockWidget.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable |
                                   QtWidgets.QDockWidget.DockWidgetMovable)

            # titleBarWidget = QtWidgets.QWidget()
            # iconLbl = QtWidgets.QLabel()
            # iconLbl.setPixmap(QtGui.QPixmap(icon))
            # titleLbl = QtWidgets.QLabel(name)
            # mainHLayout = QtWidgets.QHBoxLayout()
            # mainHLayout.addWidget(iconLbl)
            # mainHLayout.addWidget(titleLbl)
            # titleBarWidget.setLayout(mainHLayout)
            # dockWidget.setTitleBarWidget(titleBarWidget)
            return dockWidget

        cameraDock = createDockWidget(self.cameraWidget, "Camera")
        consoleDock = createDockWidget(self.consoleWidget, "Console")


        # Add the consoleWidgets to the window, and tabify them
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, cameraDock)
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

        printf("GUI| Setting video to state: ", state)

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
            # if not vStream.connected() or not vStream.cameraID == cameraID:
            #     vStream.setNewCamera(cameraID)

            self.cameraWidget.play()

        if state == "pause":
            self.cameraWidget.pause()


    def toggleScript(self):
        # Run/pause the main script
        if self.interpreter.threadRunning():
            self.endScript()
        else:
            self.startScript()

    def startScript(self):
        if self.interpreter.threadRunning():
                printf("GUI| ERROR: Tried to start interpreter while it was already running.")
                return
        printf("GUI| Interpreter is ready. Loading script and starting task")


        # Load the script with the latest changes in the controlPanel, and get any relevant errors
        self.interpreter.cleanNamespace()   # Clear any changes the user did while it was running
        self.interpreter.setExiting(False)  # Make sure vision and robot are not in exiting mode



        errors = self.interpreter.initializeScript(self.controlPanel.getSaveData())


        # If there were errors during loading, present the user with the option to continue anyways
        if len(errors):
            errorText = ""
            for error, errorObjects in errors.items():
                errorText += "" + str(error) + "\n"
                for errObject in errorObjects:
                    errorText += "     " + str(errObject) + "\n"
                errorText += '\n'


            # Generate a message for the user to explain what parameters are missing
            errorStr = 'Certain Events and Commands are missing the following requirements to work properly: \n\n' + \
                       ''.join(errorText) + \
                       '\nWould you like to continue anyways? Events and commands with errors will not activate.'


            # Warn the user
            reply = QtWidgets.QMessageBox.question(self, 'Warning', errorStr,
                                QtWidgets.QMessageBox.Cancel | QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.Cancel)


            if reply == QtWidgets.QMessageBox.Cancel:
                printf("GUI| Script run canceled by user before starting.")
                vision = self.env.getVision()
                vision.endAllTrackers()  # Clear any tracking that was started during interpreter initialization
                return


        # Prep the robot to start, so it always starts with servos attached and speed at 10
        robot  = self.env.getRobot()
        robot.setActiveServos(all=True)
        robot.setSpeed(10)


        # Stop you from moving stuff around while script is running, and activate the visual cmmnd highlighting
        self.interpreter.startThread(threaded=True)
        self.controlPanel.setScriptModeOn(self.interpreter, self.endScript)

        # Make sure the UI matches the state of the script
        self.scriptToggleBtn.setIcon(QtGui.QIcon(Paths.pause_script))
        self.scriptToggleBtn.setText("Stop")

    def endScript(self):
        # Tell the interpreter to exit the thread, then wait
        if self.interpreter.threadRunning():
            self.interpreter.setExiting(True)
            self.interpreter.mainThread.join(2)  # Give the thread 3 seconds to join


        # Check to make sure the thread closed correctly
        if self.interpreter.threadRunning():
            # Generate a message for the user to explain what parameters are missing
            errorStr = 'The script was unable to end.\n' \
                       'This may mean the script crashed, or it is taking time finishing.\n\n' \
                       'If you are running Python code inside of this script, make sure you check isExiting() during' \
                       ' loops, to exit code quickly when the stop button is pressed.'

            # Warn the user
            reply = QtWidgets.QMessageBox.question(self, 'Error', errorStr, QtWidgets.QMessageBox.Ok)
            return


        # Turn off the gripper, just in case. Do this AFTER interpreter ends, so as to not use Serial twice...
        vision = self.env.getVision()

        robot  = self.env.getRobot()
        robot.setExiting(False)
        vision.setExiting(False)
        robot.setPump(False)

        # Since the robot might still be moving (and this activates servos continuously) wait for it to finish
        robot.stopMoving()
        robot.setActiveServos(all=False)

        # Make sure vision filters are stopped
        vision.endAllTrackers()


        self.scriptToggleBtn.setIcon(QtGui.QIcon(Paths.run_script))
        self.scriptToggleBtn.setText("Start")


    def refreshDevicesIcon(self):
        """
        This checks the status of the robot and camera, and updates the icon of the Devices toolbar button to reflect
        the connection status of the robot and camera.

        This should be run 5 seconds after the devices window closes, or 5 seconds after the program starts, to check
        if the robot thread was able to connect or not.
        """

        camera = self.env.getVStream()
        robot  = self.env.getRobot()

        robotErrors = robot.getErrorsToDisplay()
        if len(robotErrors) > 0:
            reply = QtWidgets.QMessageBox.question(self, 'Communication Errors', "The following errors have occured "
                            "communicating with your robot.\nTry reconnecting under the Devices menu."
                            "\n\nERROR:\n" + "\n".join(robotErrors), QtWidgets.QMessageBox.Ok)
            self.env.updateSettings("robotID", None)

        robCon = robot.connected()
        camCon = camera.connected() and camera.running

        icon = ""

        if     robCon and     camCon: icon = Paths.devices_both
        if     robCon and not camCon: icon = Paths.devices_robot
        if not robCon and     camCon: icon = Paths.devices_camera
        if not robCon and not camCon: icon = Paths.devices_neither

        self.devicesBtn.setIcon(QtGui.QIcon(icon))

    def openDevices(self):
        # This handles the opening and closing of the Settings window.
        printf("GUI| Opening Devices Window")

        if self.interpreter.threadRunning(): self.endScript()

        self.cameraWidget.pause()

        deviceWindow = DeviceWindow(parent=self)
        accepted     = deviceWindow.exec_()

        self.cameraWidget.play()
        if not accepted:
            printf("GUI| Cancel clicked, no settings applied.")
            return

        printf("GUI| Apply clicked, applying settings...")
        if deviceWindow.getRobotSetting() is not None:
            self.env.updateSettings("robotID", deviceWindow.getRobotSetting())

        currentCamera = self.env.getSetting("cameraID")

        if deviceWindow.getCameraSetting() is not None:
            self.env.updateSettings("cameraID", deviceWindow.getCameraSetting())


        # If the camera has changed, update the cameraID
        if currentCamera != self.env.getSetting("cameraID"):
            vStream = self.env.getVStream()
            vStream.setNewCamera(self.env.getSetting('cameraID'))


        # If the robots not connected, attempt to reestablish connection
        robot   = self.env.getRobot()
        if not robot.connected():
            robot.setUArm(self.env.getSetting('robotID'))



        self.cameraWidget.play()

    def openCalibrations(self):
        # This handles the opening and closing of the Calibrations window
        printf("GUI| Opening Calibrations Window")

        if self.interpreter.threadRunning(): self.endScript()
        self.cameraWidget.pause()

        coordSettings = self.env.getSetting("coordCalibrations")
        motionSettings = self.env.getSetting("motionCalibrations")
        calibrationsWindow = CalibrateWindow(coordSettings, motionSettings, self.env, parent=self)
        accepted           = calibrationsWindow.exec_()

        if accepted:
            # Update all the settings
            printf("GUI| Apply clicked, applying calibrations...")

            # Update the settings
            self.env.updateSettings("coordCalibrations", calibrationsWindow.getCoordSettings())
            self.env.updateSettings("motionCalibrations", calibrationsWindow.getMotionSettings())

        else:
            printf("GUI| Cancel clicked, no calibrations applied.")

        self.cameraWidget.play()

    def openObjectManager(self, openResourceWindow=None):
        # This handles the opening and closing of the ObjectManager window
        printf("GUI| Opening ObjectManager Window")

        if self.interpreter.threadRunning(): self.endScript()

        # Make sure video thread is active and playing, but that the actual cameraWidget
        self.setVideo("play")

        self.cameraWidget.pause()
        objMngrWindow = ObjectManagerWindow(self.env, self)
        accepted      = objMngrWindow.exec_()
        objMngrWindow.close()
        objMngrWindow.deleteLater()

        self.setVideo("play")

    def openResourceWindow(self, resourceWindowType):
        """
        This can open a MakeGroupWindow, MakeRecordingWindow, or MakeFunctionWindow, handle its closing and garbage
        collection, and create the object if the user clicks "finished"

        :param menuType: MenuType is the Type of the menu object, such as EditGroupWindow or MakeFunctionWindow
        :return:
        """


    def newTask(self, promptSave):
        if promptSave:
            cancelPressed = self.promptSave()
            if cancelPressed:  # If the user cancelled the close
                return

        self.controlPanel.loadData([])
        self.fileName = None
        self.loadData = deepcopy(self.controlPanel.getSaveData())
        self.setWindowTitle(self.programTitle)

    def saveTask(self, promptSaveLocation):
        printf("GUI| Saving project")

        # If there is no filename, ask for one
        if promptSaveLocation or self.fileName is None:
            Global.ensurePathExists(Paths.saves_dir)
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(parent=self,
                                                                caption="Save Task",
                                                                filter="Task (*.task)",
                                                                directory=Paths.saves_dir)

            if filename == "": return False  #If user hit cancel
            self.fileName = filename
            self.env.updateSettings("lastOpenedFile", self.fileName)


        # Update the save file
        saveData = self.controlPanel.getSaveData()
        json.dump(saveData, open(self.fileName, 'w'), sort_keys=False, indent=3, separators=(',', ': '))

        self.loadData = deepcopy(saveData)  #Update what the latest saved changes are




        self.setWindowTitle(self.programTitle + '       ' + self.fileName)
        printf("GUI| Project Saved Successfully")
        return True

    def loadTask(self,  **kwargs):
        # Load a save file
        self.promptSave()  # Make sure the user isn't losing progress

        # Make sure a script isn't running while you try to load something
        if self.interpreter.threadRunning(): self.endScript()

        printf("GUI| Loading project")

        filename = kwargs.get("filename", None)

        # If there's no filename given, then prompt the user for what to name the task
        if filename is None:  #If no filename was specified, prompt the user for where to save
            filename, _ = QtWidgets.QFileDialog.getOpenFileName(parent=self,
                                                                caption="Load Task",
                                                                filter="Task (*.task)",
                                                                directory=Paths.saves_dir)
            if filename == "": return  #If user hit cancel


        try:
            self.loadData = json.load( open(filename))
        except IOError:
            printf("GUI| ERROR: Task file ", filename, "not found!")
            self.fileName = None
            self.env.updateSettings("lastOpenedFile", None)
            return



        # Load the data- BUT MAKE SURE TO DEEPCOPY otherwise any change in the program will change in self.loadData
        try:

            self.controlPanel.loadData(deepcopy(self.loadData))
            self.fileName = filename
            self.env.updateSettings("lastOpenedFile", filename)
            self.setWindowTitle(self.programTitle + '      ' + self.fileName)
            printf("GUI| Project loaded successfully")
        except Exception as e:
            printf("GUI| ERROR: Could not load task: ", e)
            self.newTask(promptSave=False)
            QtWidgets.QMessageBox.question(self, 'Warning', "The program was unable to load the following script:\n" +
                                    filename + "\n\n The following error occured: " + type(e).__name__ + ": " + str(e),
                                           QtWidgets.QMessageBox.Ok)



    def promptSave(self):
        # Prompts the user if they want to save, but only if they've changed something in the program
        # Returns True if the user presses Cancel or "X", and wants the window to stay open.


        if not self.loadData == self.controlPanel.getSaveData():
            printf("GUI| Prompting user to save changes")
            reply = QtWidgets.QMessageBox.question(self, 'Warning',
                                    "You have unsaved changes. Would you like to save before continuing?",
                                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel,
                                    QtWidgets.QMessageBox.Yes)

            if reply == QtWidgets.QMessageBox.Yes:
                printf("GUI| Saving changes")
                success = self.saveTask(False)
                return not success

            if reply == QtWidgets.QMessageBox.No:
                printf("GUI| Not saving changes")

            if reply == QtWidgets.QMessageBox.Cancel:
                printf("GUI| User canceled- aborting close!")
                return True

    def closeEvent(self, event):
        """
            When window is closed, prompt for save, close the video stream, and close the control panel (thus script)
        """


        # Ask the user they want to save before closing anything
        cancelPressed = self.promptSave()
        if cancelPressed:  # If the user cancelled the close
            event.ignore()
            return


        # Save the window geometry as a string representation of a hex number
        saveGeometry = ''.join([str(char) for char in self.saveGeometry().toHex()])
        self.env.updateSettings("windowGeometry", saveGeometry)


        # Save the dockWidget positions/states as a string representation of a hex number
        saveState    = ''.join([str(char) for char in self.saveState().toHex()])
        self.env.updateSettings("windowState", saveState)


        # Deactivate the robots servos
        robot = self.env.getRobot()
        robot.setActiveServos(all=False)


        # End the script *after* prompting for save and deactivating servos on the robot. Script thread is a Daemon
        self.interpreter.setExiting(True)


        # Close and delete GUI objects, to stop their events from running
        self.refreshTimer.stop()
        self.cameraWidget.close()
        self.controlPanel.close()
        self.centralWidget.close()
        self.centralWidget.deleteLater()


        # Close threads
        self.env.close()

        printf("GUI| Done closing all objects and threads.")



##########    VIEWS    ##########
class DeviceWindow(QtWidgets.QDialog):
    """
    Simple view that lets you select your robot and camera.
    The Apply/Cancel buttons are connected in the MainWindow class, which is why they are 'self' variables
    """

    def __init__(self, parent):
        super(DeviceWindow, self).__init__(parent)
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
        self.cameraToggleBtn = QtWidgets.QPushButton(self._getToggleButtonText(self.parent().env.getVStream()))
        applyBtn      = QtWidgets.QPushButton("Apply")
        cancelBtn     = QtWidgets.QPushButton("Cancel")

        # Connect Buttons
        robotScanBtn.clicked.connect(self.scanForRobotsClicked)
        cameraScanBtn.clicked.connect(self.scanForCamerasClicked)
        self.cameraToggleBtn.clicked.connect(self.toggleCameraClicked)
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

        row5 = QtWidgets.QHBoxLayout()
        row5.addWidget(self.cameraToggleBtn, QtCore.Qt.AlignRight)

        # Place the rows ito the middleVLayout
        middleVLayout = QtWidgets.QVBoxLayout()
        middleVLayout.addLayout(row1)
        middleVLayout.addLayout(row2)
        middleVLayout.addLayout(row3)
        middleVLayout.addLayout(row4)
        middleVLayout.addLayout(row5)
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
        self.setWindowTitle('Devices')
        self.setWindowIcon(QtGui.QIcon(Paths.settings))


    def scanForRobotsClicked(self):
        connectedDevices = getConnectedRobots()  # From Robot.py

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

    @staticmethod
    def _getToggleButtonText(stream):
        if stream.cameraID is None:
            return 'No camera configured'
        state = ['Enable Camera', 'Disable Camera']
        return state[stream.running]

    def toggleCameraClicked(self):
        vStream = self.parent().env.getVStream()

        if vStream.running:
            vStream.endThread()
        else:
            vStream.startThread()

        self.cameraToggleBtn.setText(self._getToggleButtonText(vStream))
        self.parent().refreshDevicesIcon()

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
    # Install a global exception hook to catch pyQt errors that fall through (helps with debugging a ton) #TODO: Remove for builds
    sys.__excepthook = sys.excepthook
    sys._excepthook  = sys.excepthook
    def exception_hook(exctype, value, traceback):
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)
    sys.excepthook   = exception_hook


    # Initialize global variables
    Global.init()


    # Create the Application base
    app = Application(sys.argv)


    # Apply a stylesheet (theme) of choice here
    # app.setStyleSheet(fancyqt.firefox.style)


    # Set Application Font
    font = QtGui.QFont()
    font.setFamily("Verdana")
    font.setPixelSize(12)
    app.setFont(font)


    # Actually start the program
    mainWindow = MainWindow()
    sys.exit(app.exec_())





