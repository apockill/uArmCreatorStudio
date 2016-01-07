#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import webbrowser           #Used soley to open the uFactory forum
import pickle
import Robot
import Video
import ControlPanel
import Icons
import Global
from PyQt4 import QtGui, QtCore





########## VIEWS ##########
class CalibrateView(QtGui.QWidget):
    """
    This is the dashboard where the user can calibrate different aspects of their robot.
    Things like motion calibration for the camera, color calibration, focus calibration, and maybe even eventually
    visual servo-ing calibrations
    """

    def __init__(self, vision, robot, parent=None):
        super(CalibrateView, self).__init__(parent)

        self.newSettings    = {"motionCalibrations": {"stationaryMovement": None, "activeMovement": None}}

        #These buttons are connected in Main.MainWindow.__init__()
        self.cancelBtn = QtGui.QPushButton("Cancel")
        self.applyBtn  = QtGui.QPushButton("Apply")
        self.vision = vision
        self.robot = robot
        #May be changed in updateLabels()
        self.motionLbl = QtGui.QLabel("No information for this calibration")

        self.initUI()


    def initUI(self):

        motionBtn = QtGui.QPushButton("Calibrate Motion")


        maxWidth  = 100
        motionBtn.setFixedWidth(maxWidth)
        self.cancelBtn.setFixedWidth(maxWidth)
        self.applyBtn.setFixedWidth(maxWidth)



        row1 = QtGui.QHBoxLayout()

        row1.addWidget(     motionBtn, QtCore.Qt.AlignLeft)
        row1.addWidget(self.motionLbl, QtCore.Qt.AlignRight)

        middleVLayout = QtGui.QVBoxLayout()
        middleVLayout.addLayout(row1)
        middleVLayout.addStretch(1)

        #Set up Cancel and Apply buttons
        leftVLayout = QtGui.QVBoxLayout()
        leftVLayout.addStretch(1)
        leftVLayout.addWidget(self.cancelBtn, QtCore.Qt.AlignRight)
        rightVLayout = QtGui.QVBoxLayout()
        rightVLayout.addStretch(1)
        rightVLayout.addWidget(self.applyBtn, QtCore.Qt.AlignLeft)

        mainHLayout = QtGui.QHBoxLayout()
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
        #Make sure VideoStream is collecting new frames
        self.vision.vStream.setPaused(False)


        #Get movement while nothing is happening
        totalMotion = 0.0
        samples     = 50
        for i in xrange(0, samples):
            self.vision.vStream.waitForNewFrame()
            totalMotion += self.vision.getMotion()
        noMovement = totalMotion / samples


        #Get movement while robot is moving
        totalMotion = 0.0
        samples     = 5
        self.robot.setPos( x=-15, y=-15, z=20)   #Start position
        self.robot.refresh()
        for i in xrange(0, samples):
            #Shake the robot while getting new frames
            self.vision.vStream.waitForNewFrame()
            self.robot.setPos(x=30, y=0, z=0, relative=True)   #end position
            self.robot.refresh(instant=True)
            self.vision.vStream.waitForNewFrame()
            totalMotion += self.vision.getMotion()

            self.vision.vStream.waitForNewFrame()
            self.robot.setPos(x=-30, y=0, z=0, relative=True)   #end position
            self.robot.refresh(instant=True)
            totalMotion += self.vision.getMotion()
        highMovement = totalMotion / (samples * 2)  #Since two samples are gotten from each loop


        self.newSettings["motionCalibrations"]["stationaryMovement"] = round(  noMovement, 1)
        self.newSettings["motionCalibrations"]["activeMovement"]     = round(highMovement, 1)

        #Return the vStream to paused
        self.vision.vStream.setPaused(True)
        self.updateLabels()
        print "CalibrateView.calibrateMotion():\t Function complete! New motion settings: ", self.newSettings

    def getSettings(self):
        return self.newSettings


class SettingsView(QtGui.QWidget):
    """
    Simple view that lets you select your robot and camera.
    The Apply/Cancel buttons are connected in the MainWindow class, which is why they are 'self' variables
    """
    def __init__(self, parent=None):
        super(SettingsView, self).__init__(parent)
        self.settings  = {"robotID": None, "cameraID": None}

        #Init UI Globals
        self.cameraButtonGroup = None
        self.robotButtonGroup  = None
        self.robVBox   = QtGui.QVBoxLayout()
        self.camVBox   = QtGui.QVBoxLayout()
        self.applyBtn  = QtGui.QPushButton("Apply")  #Gets connected from the MainWindow method
        self.cancelBtn = QtGui.QPushButton("Cancel")

        self.initUI()

    def initUI(self):
        #Create Text
        selectRobotTxt  = QtGui.QLabel('Please select the robot you will be using:')
        selectCameraTxt = QtGui.QLabel('Please select the camera you will be using:')

        #CREATE BUTTONS
        robotScanBtn  = QtGui.QPushButton("Scan for Robots")
        cameraScanBtn = QtGui.QPushButton("Scan for Cameras")
            #Set max widths of buttons
        maxWidth = 100
        robotScanBtn.setFixedWidth(maxWidth)
        cameraScanBtn.setFixedWidth(maxWidth)
        self.applyBtn.setFixedWidth(maxWidth)
        self.cancelBtn.setFixedWidth(maxWidth)

        row1 = QtGui.QHBoxLayout()
        row1.addWidget(selectRobotTxt, QtCore.Qt.AlignLeft)
        row1.addWidget(robotScanBtn, QtCore.Qt.AlignRight)

        row2 = QtGui.QHBoxLayout()
        row2.addLayout(self.robVBox, QtCore.Qt.AlignLeft)


        row3 = QtGui.QHBoxLayout()
        row3.addWidget(selectCameraTxt, QtCore.Qt.AlignLeft)
        row3.addWidget(cameraScanBtn, QtCore.Qt.AlignRight)

        row4 = QtGui.QHBoxLayout()
        row4.addLayout(self.camVBox)

        middleVLayout = QtGui.QVBoxLayout()
        middleVLayout.addLayout(row1)
        middleVLayout.addLayout(row2)
        middleVLayout.addLayout(row3)
        middleVLayout.addLayout(row4)
        middleVLayout.addStretch(1)

        #Set up Cancel and Apply buttons
        leftVLayout = QtGui.QVBoxLayout()
        leftVLayout.addStretch(1)
        leftVLayout.addWidget(self.cancelBtn, QtCore.Qt.AlignRight)
        rightVLayout = QtGui.QVBoxLayout()
        rightVLayout.addStretch(1)
        rightVLayout.addWidget(self.applyBtn, QtCore.Qt.AlignLeft)

        #Build the final layout
        mainHLayout = QtGui.QHBoxLayout()
        mainHLayout.addStretch(1)
        mainHLayout.addLayout(leftVLayout)
        mainHLayout.addLayout(middleVLayout)
        mainHLayout.addLayout(rightVLayout)
        mainHLayout.addStretch(1)

        self.setLayout(mainHLayout)

        #Connect Buttons
        robotScanBtn.clicked.connect(self.scanForRobotsClicked)
        cameraScanBtn.clicked.connect(self.scanForCamerasClicked)

    def scanForRobotsClicked(self):
        connectedDevices = Robot.getConnectedRobots()
        print "SettingsView.scanForRobots():\t Connected Devices: ", connectedDevices
        self.robotButtonGroup = QtGui.QButtonGroup()

        #Update the list of found devices
        self.clearLayout(self.robVBox)  #  Clear robot list
        for i, port in enumerate(connectedDevices):
            newButton = QtGui.QRadioButton(port[0])
            self.robVBox.addWidget(newButton)                        # Add the button to the button layout
            self.robotButtonGroup.addButton(newButton, i)            # Add the button to a group, with an ID of i
            newButton.clicked.connect(self.robButtonClicked) # Connect each radio button to a method


        if len(connectedDevices) == 0:
            notFoundTxt = QtGui.QLabel('No devices were found.')
            self.robVBox.addWidget(notFoundTxt)

    def scanForCamerasClicked(self):

        #  Get all of the cameras connected to the computer and list them
        connectedCameras = Video.getConnectedCameras()

        self.cameraButtonGroup = QtGui.QButtonGroup()

        #Update the list of found cameras
        self.clearLayout(self.camVBox)  #  Clear camera list
        for i in xrange(len(connectedCameras)):
            newButton = QtGui.QRadioButton("Camera " + str(i))
            self.camVBox.addWidget(newButton)                  # Add the button to the button layout
            self.cameraButtonGroup.addButton(newButton, i)     # Add the button to a group, with an ID of i
            newButton.clicked.connect(self.camButtonClicked)   # Connect each radio button to a method



        if len(connectedCameras) == 0:
            notFoundTxt = QtGui.QLabel('No cameras were found.')
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


class DashboardView(QtGui.QWidget):
    def __init__(self, controlPanel, cameraWidget, parent=None):
        super(DashboardView, self).__init__(parent)

        #UI Globals setup
        self.controlPanel   = controlPanel
        self.cameraWidget   = cameraWidget

        self.initUI()

    def initUI(self):

        #Create main layout
        mainHLayout = QtGui.QHBoxLayout()
        mainVLayout = QtGui.QVBoxLayout()
        mainVLayout.addLayout(mainHLayout)

        mainHLayout.addWidget(self.controlPanel)
        #mainHLayout.addStretch(1)                   #Put a space between control list and camera view
        mainHLayout.addWidget(self.cameraWidget)    #Create Camera view (RIGHT)

        #mainHLayout.addLayout(listVLayout)
        self.setLayout(mainVLayout)




########## MAIN WINDOW ##########
class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.settings  = {"robotID": None, "cameraID": None, "lastOpenedFile": None,
                          "motionCalibrations": None}

        #Init self variables
        self.fileName    = None
        self.loadData    = None   #Set when file is loaded. Used to check if the user has changed anything and prompt save
        self.keysPressed = None
        self.vStream     = Video.VideoStream(None)
        self.vision      = Video.Vision(self.vStream)
        self.robot       = Robot.Robot(None)



        #Set Global UI Variables
        self.centralWidget   = QtGui.QStackedWidget()
        self.controlPanel    = ControlPanel.ControlPanel(self.robot, self.vision, self.settings, parent=self)
        self.cameraWidget    = Video.CameraWidget(self.vStream.getPixFrame)

        self.dashboardView   = DashboardView(self.controlPanel, self.cameraWidget, parent=self)
        self.settingsView    = SettingsView(parent=self)  #'self' so that StackedWidget can be used
        self.calibrateView   = CalibrateView(self.vision, self.robot, parent=self)

        self.scriptToggleBtn = QtGui.QAction(QtGui.QIcon(Icons.run_script), 'Run/Pause the command script (Ctrl+R)', self)
        self.videoToggleBtn  = QtGui.QAction(QtGui.QIcon(Icons.play_video), 'Play/Pause the video stream (Ctrl+P)', self)


        #Connect Cancel/Apply Buttons from various views
        self.settingsView.applyBtn.clicked.connect( lambda: self.closeSettingsView("Apply"))
        self.settingsView.cancelBtn.clicked.connect(lambda: self.closeSettingsView("Cancel"))
        self.calibrateView.applyBtn.clicked.connect( lambda: self.closeCalibrateView("Apply"))
        self.calibrateView.cancelBtn.clicked.connect(lambda: self.closeCalibrateView("Cancel"))


        #Now that objects have been created, load the settings
        configExists = self.loadSettings()

        self.initUI()

        #If any file is specified in "lastOpenedFile" then load it.
        if self.settings["lastOpenedFile"] is not None:
            self.loadTask(filename=self.settings["lastOpenedFile"])
        else:
            self.newTask()

        if not configExists:
            self.setView(self.settingsView)

    def initUI(self):
        #Create Menu
        menuBar      = self.menuBar()
        fileMenu     = menuBar.addMenu('File')

        newAction    = QtGui.QAction( QtGui.QIcon(Icons.new_file), "New Task", self)
        saveAction   = QtGui.QAction(QtGui.QIcon(Icons.save_file), "Save Task", self)
        saveAsAction = QtGui.QAction(QtGui.QIcon(Icons.save_file), "Save Task As", self)
        loadAction   = QtGui.QAction(QtGui.QIcon(Icons.load_file), "Load Task", self)
        forumAction  = QtGui.QAction("Visit the forum!", self)

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



        #Create toolbar
        toolbar = self.addToolBar("MainToolbar")

        settingsBtn  = QtGui.QAction( QtGui.QIcon(Icons.settings),  'Open Camera and Robot settings (Ctrl+T)', self)
        calibrateBtn = QtGui.QAction(QtGui.QIcon(Icons.calibrate), 'Open Robot and Camera Calibration Center', self)

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


        #Create the main layout
        self.setCentralWidget(self.centralWidget)
        self.centralWidget.addWidget(self.dashboardView)
        self.centralWidget.addWidget(self.settingsView)
        self.centralWidget.addWidget(self.calibrateView)

        #Final touches
        self.setWindowTitle('uArm Creator Dashboard')
        self.setWindowIcon(QtGui.QIcon(Icons.taskbar))
        self.show()



    def setSettings(self, newSettings):
        #Apply settings
        isNew = lambda key: key in newSettings and newSettings[key] is not None and not self.settings[key] == newSettings[key]

        if isNew("cameraID"):  #
            print "Main.closeSettingsView()\t Changing cameraID from ", \
                  self.settings["cameraID"], "to", newSettings["cameraID"]
            self.settings["cameraID"] = newSettings["cameraID"]
            success = self.vStream.setNewCamera(self.settings["cameraID"])
            if success:
                self.setVideo("play")
            else:
                self.setVideo("pause")


        if isNew("robotID"):
            print "Main.closeSettingsView()\t Changing robotID from ", \
                  self.settings["robotID"], "to", newSettings["robotID"]
            self.settings["robotID"] = newSettings["robotID"]
            self.robot.setUArm(self.settings["robotID"])


        if isNew("lastOpenedFile"):
            print "Main.setSettings():\t Loading file ", str(newSettings["lastOpenedFile"])
            self.settings["lastOpenedFile"] = newSettings["lastOpenedFile"]
            self.loadTask(filename=self.settings["lastOpenedFile"])


        if isNew("motionCalibrations"):
            self.settings["motionCalibrations"] = newSettings["motionCalibrations"]
            self.calibrateView.newSettings["motionCalibrations"] = self.settings["motionCalibrations"]
            self.calibrateView.updateLabels()


        #Save settings to a config file
        self.saveSettings()

    def setVideo(self, state):
        #State can be play, pause, or simply "toggle"
        print "MainWindow.setVideo():\t Setting video to state: ", state

        if self.settings["cameraID"] is None: return  #Don't change anything if no camera ID has been added yet


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
        #Run/pause the main script

        print "MainWindow.setScript(): Setting script to ", state

        if self.robot.uArm is None:
            print "MainWindow.setScript(): ERROR: Tried to start script with no uArm connected!"
            return

        if state == "play":  #self.controlPanel.running:
            self.controlPanel.startThread()
            self.scriptToggleBtn.setIcon(QtGui.QIcon(Icons.pause_script))

        if state == "pause":
            self.controlPanel.endThread()
            self.scriptToggleBtn.setIcon(QtGui.QIcon(Icons.run_script))
           # self.controlPanel.running or setState == "play":

        if state == "toggle":
            if self.controlPanel.running:
                self.setScript("pause")
            else:
                self.setScript("play")



    def setView(self, viewWidget):
        #Change between the main view, settings, and calibrations view.
        print "MainWindow.openSettingsView(): Opening Settings!"
        self.setScript("pause")
        self.setVideo("pause")
        self.centralWidget.setCurrentWidget(viewWidget)

    def closeSettingsView(self, buttonClicked):
        newSettings = self.settingsView.getSettings()

        if buttonClicked == "Apply":
            print 'Main.closeSettingsView():\t "Apply" clicked, applying settings...'
            self.setSettings(newSettings)

        if buttonClicked == "Cancel":
            print 'Main.closeSettingsView():\t "Cancel" clicked, no settings applied.'

        #Go back to dashboard
        self.centralWidget.setCurrentWidget(self.dashboardView)

    def closeCalibrateView(self, buttonClicked):
        self.centralWidget.setCurrentWidget(self.dashboardView)

        newSettings = self.calibrateView.getSettings()
        print "new settings: ", newSettings
        if buttonClicked == "Apply":
            print 'Main.closeCalibrateView():\t "Apply" clicked, applying settings...'
            self.setSettings(newSettings)

        if buttonClicked == "Cancel":
            print 'Main.closeCalibrateView():\t "Cancel" clicked, no calibrations applied...'

        #Go back to dashboard
        self.centralWidget.setCurrentWidget(self.dashboardView)



    def promptSave(self):
        #Prompts the user if they want to save, but only if they've changed something in the program
        if not self.loadData is None and not self.loadData == self.controlPanel.getSaveData():
            print "MainWindow.promptSave():\t Prompting user to save changes"
            reply = QtGui.QMessageBox.question(self, 'Warning',
                                           "You have unsaved changes. Would you like to save before continuing?",
                                           QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.Yes)
            if reply == QtGui.QMessageBox.Yes:
                print "MainWindow.promptSave():\tSaving changes"

                self.saveTask(False)

    def newTask(self):
        self.promptSave()
        self.dashboardView.controlPanel.loadData([])
        self.fileName = None
        self.loadData = self.controlPanel.getSaveData()



    def saveTask(self, promptSave):
        print "MainWindow.save():\t Saving project"

        #If there is no filename, ask for one
        if promptSave or self.fileName is None:
            filename = QtGui.QFileDialog.getSaveFileName(self, "Save Task", "MyTask", "*.task")
            if filename == "": return  #If user hit cancel
            self.fileName = filename

        #Update the save file
        saveData = self.controlPanel.getSaveData()
        print "MainWindow.save():\t Saving: ", saveData
        pickle.dump(saveData, open(self.fileName, "wb"))

        self.setWindowTitle('uArm Creator Dashboard       ' + self.fileName)
        self.saveSettings()

    def loadTask(self,  **kwargs):
        filename = kwargs.get("filename", None)

        if filename is None:  #If no filename was specified, prompt the user for where to save
            filename = QtGui.QFileDialog.getOpenFileName(self, "Load Task", "", "*.task")
            if filename == "": return  #If user hit cancel

        try:
            self.loadData = pickle.load( open( filename, "rb"))
        except IOError:
            print "MainWindow.loadTask():\t ERROR: Task file ", filename, "not found!"
            self.settings["lastOpenedFile"] = None
            return
        print "MainWindow.save():\t Loading Project."
        self.fileName = filename
        self.dashboardView.controlPanel.loadData(self.loadData)
        self.setWindowTitle('uArm Creator Dashboard      ' + self.fileName)

        self.saveSettings()


    def saveSettings(self):
        self.settings["lastOpenedFile"] = self.fileName
        pickle.dump(self.settings, open("Settings.p", "wb"))

    def loadSettings(self):
        try:
            newSettings = pickle.load(open( "Settings.p", "rb"))
            print "MainWindow.loadSettings():\t Loading settings: ", newSettings, "..."
            self.setSettings(newSettings)
            return True
        except IOError:
            print "MainWindow.loadSettings():\t No settings file detected. Using default values."
            return False

    def closeEvent(self, event):
        self.promptSave()

        self.vStream.endThread()
        self.controlPanel.close()


class Application(QtGui.QApplication):
    """
        I modified the QtGui.QApplication class slightly in order to intercept keypress events
        and write them in the Global.keysPressed list
    """
    def __init__(self, args):
        super(Application, self).__init__(args)


    def notify(self, receiver, event):
        #Intercept any events before they reach their object
        if event.type() == QtCore.QEvent.Close:
            print "Application.notify():\t Closing window! Event: ", event

        #if event.type() == QtCore.QEvent.WindowActivate:
            #print "Application.notify():\t Opening window! Event: ", event

        #Add any keys that are pressed to keysPressed
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() not in Global.keysPressed:
                Global.keysPressed.append(event.key())

        #Remove any keys that are released from self.keysPressed
        if event.type() == QtCore.QEvent.KeyRelease:
            if event.key() in Global.keysPressed:
                Global.keysPressed = filter(lambda x: x != event.key(), Global.keysPressed)


        #Call Base Class Method to Continue Normal Event Processing
        return super(Application, self).notify(receiver, event)




if __name__ == '__main__':

    Global.init()
    try:
        app = Application(sys.argv)
        mainWindow = MainWindow()
        print "__main__():\t mainWindow class successfully initiated!"
        mainWindow.show()
        print "__main__():\t mainWindow successfully shown()"
        app.exec_()
        print "__main__():\t Program successfully executed."
    except:
        print "__main__(): ERROR: omething big went wrong!"

