#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import pickle
import Robot
import Video
import ControlPanel
import Icons
import Global
from PyQt4 import QtGui, QtCore





########## VIEWS ##########
class ScanView(QtGui.QWidget):

    def __init__(self):
        super(ScanView, self).__init__()
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
        robotScanBtn.setMaximumWidth(maxWidth)
        cameraScanBtn.setMaximumWidth(maxWidth)
        self.applyBtn.setMaximumWidth(maxWidth)
        self.cancelBtn.setMaximumWidth(maxWidth)


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

        grid.addWidget(self.cancelBtn,  4, 0, QtCore.Qt.AlignBottom)
        grid.addWidget(self.applyBtn,   4, 1, QtCore.Qt.AlignBottom)

        self.setLayout(grid)

        #Connect Buttons
        robotScanBtn.clicked.connect(self.scanForRobotsClicked)
        cameraScanBtn.clicked.connect(self.scanForCamerasClicked)

    def scanForRobotsClicked(self):
        connectedDevices = Robot.getConnectedRobots()
        print connectedDevices
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
    def __init__(self, getFrameFunction):
        super(DashboardView, self).__init__()

        #UI Globals setup
        self.controlPanel   = ControlPanel.ControlPanel()
        self.cameraWidget   = Video.CameraWidget(getFrameFunction)

        self.initUI()

    def initUI(self):

        self.cameraWidget.setMinimumWidth(640)
        self.cameraWidget.setMinimumHeight(480)
        #Create main layout
        mainHLayout = QtGui.QHBoxLayout()
        mainVLayout = QtGui.QVBoxLayout()
        mainVLayout.addLayout(mainHLayout)

        mainHLayout.addWidget(self.controlPanel)
        mainHLayout.addStretch(1)                   #Put a space between control list and camera view
        mainHLayout.addWidget(self.cameraWidget)    #Create Camera view (RIGHT)

        #mainHLayout.addLayout(listVLayout)
        self.setLayout(mainVLayout)




########## MAIN WINDOW ##########
class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        #Set Global variables
        Global.init()
        self.fileName  = None
        self.loadData  = None   #Set when file is loaded. Used to check if the user has changed anything and prompt save
        self.settings  = {"robotID": None, "cameraID": None, "lastOpenedFile": None}
        self.vStream = Video.VideoStream(None)
        Global.robot   = Robot.Robot(None)



        #Set Global UI Variables
        self.centralWidget   = QtGui.QStackedWidget()
        self.dashboardView   = DashboardView(self.vStream.getPixFrame)
        self.controlPanel    = self.dashboardView.controlPanel
        self.settingsView    = ScanView()
        self.scriptToggleBtn = QtGui.QAction(QtGui.QIcon(Icons.run_script),   'Run/Pause the command script (Ctrl+R)', self)
        self.videoToggleBtn  = QtGui.QAction(QtGui.QIcon(Icons.play_video),    'Play/Pause the video stream (Ctrl+P)', self)
        self.settingsBtn     = QtGui.QAction(QtGui.QIcon(Icons.settings), 'Open Camera and Robot settings (Ctrl+T)', self)

        #Now that objects are specified, load all settings
        self.loadSettings()

        self.initUI()

        #self.setVideo("play")  #Play video
        if self.settings["lastOpenedFile"] is not None: self.loadTask(filename=self.settings["lastOpenedFile"])

    def initUI(self):
        #Create Menu
        menuBar      = self.menuBar()
        fileMenu     = menuBar.addMenu('File')

        newAction    = QtGui.QAction( QtGui.QIcon(Icons.new_file), "New Task", self)
        saveAction   = QtGui.QAction(QtGui.QIcon(Icons.save_file), "Save Task", self)
        saveAsAction = QtGui.QAction(QtGui.QIcon(Icons.save_file), "Save Task As", self)
        loadAction   = QtGui.QAction(QtGui.QIcon(Icons.load_file), "Load Task", self)

        newAction.triggered.connect(self.newTask)
        saveAction.triggered.connect(self.saveTask)
        saveAsAction.triggered.connect(lambda: self.saveTask(True))
        loadAction.triggered.connect(self.loadTask)

        fileMenu.addAction(newAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(saveAsAction)
        fileMenu.addAction(loadAction)
        menuBar.addMenu(fileMenu)



        #Create toolbar
        toolbar = self.addToolBar("MainToolbar")
        self.scriptToggleBtn.setShortcut('Ctrl+R')
        self.videoToggleBtn.setShortcut('Ctrl+P')
        self.settingsBtn.setShortcut('Ctrl+S')

        self.scriptToggleBtn.triggered.connect(self.scriptToggle)
        self.videoToggleBtn.triggered.connect(lambda: self.setVideo("toggle"))
        self.settingsBtn.triggered.connect(self.openSettingsView)

        toolbar.addAction(self.scriptToggleBtn)
        toolbar.addAction(self.videoToggleBtn)
        toolbar.addAction(self.settingsBtn)



        #Create the main layout
        self.setCentralWidget(self.centralWidget)
        self.centralWidget.addWidget(self.dashboardView)
        self.centralWidget.addWidget(self.settingsView)



        #Connect Buttons
        self.settingsView.applyBtn.clicked.connect( lambda: self.closeSettingsView("Apply"))
        self.settingsView.cancelBtn.clicked.connect(lambda: self.closeSettingsView("Cancel"))



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
            Global.robot.setUArm(self.settings["robotID"])



        if isNew("lastOpenedFile"):
            print "Main.setSettings()\t Loading file ", str(newSettings["lastOpenedFile"])
            self.settings["lastOpenedFile"] = newSettings["lastOpenedFile"]
            self.loadTask(filename=self.settings["lastOpenedFile"])

        self.saveSettings()  #Save settings to a config file

    def setVideo(self, state):
        #State can be play, pause, or simply "toggle"
        print "MainWindow.setVideo():\t Setting video to state: ", state

        if self.settings["cameraID"] is None: return  #Don't change anything if no camera ID has been added yet


        if state == "play":
            print "Playing!"
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

    def scriptToggle(self):
        #Run/pause the main script
        print "MainWindow.scriptToggle(): Toggling script!"
        if self.controlPanel.running:
            self.controlPanel.endThread()
            self.scriptToggleBtn.setIcon(QtGui.QIcon(Icons.run_script))
        else:
            self.controlPanel.startThread()
            self.scriptToggleBtn.setIcon(QtGui.QIcon(Icons.pause_script))



    def openSettingsView(self):
        #Pause video so that camera scanning doesn't cause a crash
        self.setVideo("pause")
        self.centralWidget.setCurrentWidget(self.settingsView)

    def closeSettingsView(self, buttonClicked):
        print "lol"
        print "MainWindow.closeSettingsView():\t Closing settings from button: ", buttonClicked
        newSettings = self.settingsView.getSettings()

        if buttonClicked == "Apply":
            print 'Main.closeSettingsView():\t "Apply" clicked, applying settings...'
            self.setSettings(newSettings)

        if buttonClicked == "Cancel":
            #Don't apply settings
            print 'Main.closeSettingsView():\t "Cancel" clicked, no settings applied.'

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

        self.loadData = pickle.load( open( filename, "rb"))
        print "MainWindow.save():\t Loading Project. SaveData: ", self.loadData
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
            #return newSettings
        except IOError:
            print "MainWindow.loadSettings():\t ERROR: No settings file detected. Using default values."
            #return {"robotID": None, "cameraID": None, "lastOpenedFile": None}


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

        #Add any keys that are pressed to Global.keysPressed
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() not in Global.keysPressed:
                Global.keysPressed.append(event.key())

        #Remove any keys that are released from Global.keysPressed
        if event.type() == QtCore.QEvent.KeyRelease:
            if event.key() in Global.keysPressed:
                Global.keysPressed = filter(lambda x: x != event.key(), Global.keysPressed)

        #Call Base Class Method to Continue Normal Event Processing
        return super(Application, self).notify(receiver, event)




if __name__ == '__main__':

    app = Application(sys.argv)
    mainWindow = MainWindow()
    print "__main__():\t mainWindow class successfully initiated!"
    mainWindow.show()
    print "__main__():\t mainWindow successfully shown()"
    app.exec_()
    print "__main__():\t Program successfully executed."

