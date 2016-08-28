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
import re
import Paths
import Logic.RobotVision as rv
import numpy             as np
from time                import time
from PyQt5               import QtCore, QtWidgets, QtGui
from CameraGUI           import CameraWidget, CameraSelector, cvToPixFrame
from CommandsGUI         import CommandMenuWidget
from CommonGUI           import centerScreen
from ControlPanelGUI     import CommandList
from Logic.Global        import printf
from Logic.Resources     import TrackableObject, MotionPath, Function
from Logic.RobotVision   import MIN_POINTS_TO_LEARN_OBJECT
__author__ = "Alexander Thiel"



class ObjectManagerWindow(QtWidgets.QDialog):


    def __init__(self, environment, parent):
        super(ObjectManagerWindow, self).__init__(parent)
        self.env                = environment
        self.vision             = environment.getVision()
        self.objManager         = environment.getObjectManager()
        self.cameraWidget       = CameraWidget(self.env.getVStream(), parent=self)

        # Global UI Variables
        self.selLayout          = QtWidgets.QVBoxLayout()
        self.objTree            = QtWidgets.QTreeWidget()



        # Initialize the UI
        self.initUI()
        self.cameraWidget.play()
        self.refreshTreeWidget()

    def initUI(self):
        self.objTree.setIndentation(10)
        self.objTree.setHeaderLabels([""])
        self.objTree.header().close()



        # CREATE OBJECTS AND LAYOUTS FOR ROW 1 COLUMN (ALL)
        newObjBtn    = QtWidgets.QPushButton("New Vision Object")
        newGrpBtn    = QtWidgets.QPushButton("New Vision Group")
        newRecBtn    = QtWidgets.QPushButton("New Move Recording")
        newFncBtn    = QtWidgets.QPushButton("New Function")

        # Set the icons for the buttons
        newObjBtn.setIcon(QtGui.QIcon(Paths.event_recognize))
        newGrpBtn.setIcon(QtGui.QIcon(Paths.event_recognize))
        newRecBtn.setIcon(QtGui.QIcon(Paths.record_start))
        newFncBtn.setIcon(QtGui.QIcon(Paths.command_run_func))

        newObjBtn.setFixedWidth(175)
        newGrpBtn.setFixedWidth(175)
        newRecBtn.setFixedWidth(175)
        newFncBtn.setFixedWidth(175)

        newObjBtn.setFixedHeight(35)
        newGrpBtn.setFixedHeight(35)
        newRecBtn.setFixedHeight(35)
        newFncBtn.setFixedHeight(35)



        # Connect everything up
        newObjBtn.clicked.connect(lambda: self.openResourceMenu(MakeObjectWindow))
        newGrpBtn.clicked.connect(lambda: self.openResourceMenu(MakeGroupWindow))
        newRecBtn.clicked.connect(lambda: self.openResourceMenu(MakeRecordingWindow))
        newFncBtn.clicked.connect(lambda: self.openResourceMenu(MakeFunctionWindow))

        self.objTree.itemSelectionChanged.connect(self.refreshSelected)


        # CREATE OBJECTS AND LAYOUTS FOR COLUMN 1
        listGBox     = QtWidgets.QGroupBox("Loaded Objects")
        listVLayout  = QtWidgets.QVBoxLayout()
        listVLayout.addWidget(self.objTree)
        listGBox.setLayout(listVLayout)
        listGBox.setFixedWidth(325)

        # CREATE OBJECTS AND LAYOUTS FOR COLUMN 2
        selectedGBox   = QtWidgets.QGroupBox("Selected Resource")
        selectedGBox.setLayout(self.selLayout)


        # Put everything into 1 row (top) and multiple columns just below the row
        row1 = QtWidgets.QHBoxLayout()
        col1 = QtWidgets.QVBoxLayout()
        col2 = QtWidgets.QVBoxLayout()
        col3 = QtWidgets.QVBoxLayout()

        row1.addWidget(newObjBtn)
        row1.addWidget(newGrpBtn)
        row1.addWidget(newRecBtn)
        row1.addWidget(newFncBtn)
        row1.addStretch(1)

        col1.addWidget(listGBox)
        col2.addWidget(selectedGBox)
        col3.addWidget(self.cameraWidget)


        # Place the row into the main vertical layout
        mainVLayout = QtWidgets.QVBoxLayout()
        mainVLayout.addLayout(row1)
        mainHLayout = QtWidgets.QHBoxLayout()
        mainVLayout.addLayout(mainHLayout)


        # Place the columns into the main horizontal layout
        mainHLayout.addLayout(col1)
        mainHLayout.addLayout(col2)
        mainHLayout.addLayout(col3)


        # Set the layout and customize the window
        self.setLayout(mainVLayout)
        self.setWindowTitle('Resource Manager')
        self.setWindowIcon(QtGui.QIcon(Paths.objectManager))
        self.setMinimumHeight(700)


    def refreshTreeWidget(self, selectedItem=None):
        """
        Clear the objectList, and reload all object names from the environment

        :param selectedItem:         If selectedItem is a string name of an object, it will try to select the item in the TreeWidget
        Clear the current objectList
        """


        self.objTree.clear()
        self.vision.endAllTrackers()


        # Get a list for each section of the QTreeWidget that there will be
        visObjs = self.objManager.getObjectNameList(self.objManager.TRACKABLEOBJ)
        visObjs.sort()

        grpObjs = self.objManager.getObjectNameList(self.objManager.TRACKABLEGROUP)
        grpObjs.sort()

        rcdObjs = self.objManager.getObjectNameList(self.objManager.MOTIONPATH)
        rcdObjs.sort()

        fncObjs = self.objManager.getObjectNameList(self.objManager.FUNCTION)
        fncObjs.sort()

        tree = [[     "Vision Objects", visObjs],
                [      "Vision Groups", grpObjs],
                ["Movement Recordings", rcdObjs],
                [          "Functions", fncObjs]]


        for section in tree:
            # Create the Title
            title = QtWidgets.QTreeWidgetItem(self.objTree)
            title.setText(0, section[0])
            for name in section[1]:
                newItem = QtWidgets.QTreeWidgetItem(title, [name])

                # Select the item specified in selectedItem arg
                if name == selectedItem:
                    self.objTree.setCurrentItem(newItem)

        self.refreshSelected()
        self.objTree.expandAll()

    def refreshSelected(self):
        # Modifies self.selectedObjVLayout to show the currently selected object, it's name, description, etc.

        self.clearSelectedLayout()

        # Get the selected object
        selObject = self.getSelected()
        if selObject is None: return

        obj = self.objManager.getObject(selObject)


        self.vision.endAllTrackers()

        if obj is None: return


        # Disconnect "doubleClick" event from doing anything
        try: self.objTree.itemDoubleClicked.disconnect()
        except Exception: pass


        # Make the SelectedObject window reflect the information about the object (and it's type) that is curr. selected
        if isinstance(obj, self.objManager.TRACKABLEOBJ):
            self.objTree.itemDoubleClicked.connect(lambda: self.openResourceMenu(MakeObjectWindow, editResource=obj))
            self.setSelectionTrackable(obj)
            self.vision.addTarget(obj)
            return

        if isinstance(obj, self.objManager.TRACKABLEGROUP):
            self.objTree.itemDoubleClicked.connect(lambda: self.openResourceMenu(MakeGroupWindow, editResource=obj))
            self.setSelectionGroup(obj)
            self.vision.addTarget(obj)
            return

        if isinstance(obj, self.objManager.MOTIONPATH):
            self.objTree.itemDoubleClicked.connect(lambda: self.openResourceMenu(MakeRecordingWindow, editResource=obj))
            self.setSelectionPath(obj)

        if isinstance(obj, self.objManager.FUNCTION):
            self.objTree.itemDoubleClicked.connect(lambda: self.openResourceMenu(MakeFunctionWindow, editResource=obj))
            self.setSelectionFunction(obj)


    def setSelectionTrackable(self, trackableObj):

        views = trackableObj.getViews()


        selDescLbl         = QtWidgets.QLabel("")   # Description of selected object
        selImgLbl          = QtWidgets.QLabel("")   # A small picture of the object
        deleteBtn          = QtWidgets.QPushButton("Delete")
        addOrientationBtn  = QtWidgets.QPushButton("Add Orientation")


        # Connect any buttons
        deleteBtn.clicked.connect(self.deleteSelected)
        addOrientationBtn.clicked.connect(lambda: self.openResourceMenu(MakeObjectWindow, editResource=trackableObj))


        # Create a pretty icon for the object, so it's easily recognizable. Use the first sample in the objectt
        icon = cvToPixFrame(trackableObj.getIcon(150, 300))
        selImgLbl.setPixmap(icon)


        # Get the "Average" number of keypoints for this object
        totalPoints = 0
        for view in views:
            target = self.vision.planeTracker.createTarget(view)
            totalPoints += len(target.descrs)
        avgPoints = int(totalPoints / len(views))


        # Create and set the description for this object
        selDescLbl.setText("Name: \n"             + trackableObj.name + "\n\n"
                           "Detail Points: \n"    + str(avgPoints)    + "\n\n"
                           "Orientations: \n"     + str(len(views))   + "\n\n"
                           "Belongs To Groups:\n" + ''.join(['-' + tag + '\n' for tag in trackableObj.getTags()]) + "\n"
                           "Image:")

        self.selLayout.addWidget(selDescLbl)
        self.selLayout.addWidget(selImgLbl)
        self.selLayout.addWidget(addOrientationBtn)
        self.selLayout.addWidget(deleteBtn)
        self.selLayout.addStretch(1)

    def setSelectionGroup(self, trackableGrp):
        selDescLbl = QtWidgets.QLabel("")   # Description of selected object
        deleteBtn  = QtWidgets.QPushButton("Delete")
        editBtn    = QtWidgets.QPushButton("Edit Group")

        # Connect any buttons
        deleteBtn.clicked.connect(self.deleteSelected)
        editBtn.clicked.connect(lambda: self.openResourceMenu(MakeGroupWindow, editResource=trackableGrp))


        # Create the appropriate description
        groupMembers = ['-' + obj.name + '\n' for obj in trackableGrp.getMembers()]
        selDescLbl.setText("Name: \n"          + trackableGrp.name     + "\n\n"
                           "Group Members: \n" + ''.join(groupMembers) + "\n")


        self.selLayout.addWidget(selDescLbl)
        self.selLayout.addWidget(editBtn)
        self.selLayout.addWidget(deleteBtn)
        self.selLayout.addStretch(1)

    def setSelectionPath(self, pathObj):

        selDescLbl = QtWidgets.QLabel("")   # Description of selected object
        deleteBtn  = QtWidgets.QPushButton("Delete")
        editBtn    = QtWidgets.QPushButton("Edit Recording")

        # Connect any buttons
        deleteBtn.clicked.connect(self.deleteSelected)
        editBtn.clicked.connect(lambda: self.openResourceMenu(MakeRecordingWindow, editResource=pathObj))


        # Create the appropriate description
        motionPath = pathObj.getMotionPath()
        totalTime  = round(motionPath[-1][0], 1)
        if len(motionPath) == 0: return  # That would be weird, but you never know...
        selDescLbl.setText("Name: \n"        + pathObj.name + "\n\n"
                           "Move Count: \n"  + str(len(motionPath)) + "\n\n"
                           "Length: \n"      + str(totalTime) + " seconds\n\n"
                           "Moves/Second:\n"  + str(round(len(motionPath) / totalTime, 1)))


        self.selLayout.addWidget(selDescLbl)
        self.selLayout.addWidget(editBtn)
        self.selLayout.addWidget(deleteBtn)
        self.selLayout.addStretch(1)

    def setSelectionFunction(self, funcObj):

        selDescLbl = QtWidgets.QLabel("")   # Description of selected object
        deleteBtn  = QtWidgets.QPushButton("Delete")
        editBtn    = QtWidgets.QPushButton("Edit Function")

        selDescLbl.setWordWrap(True)

        # Connect any buttons
        deleteBtn.clicked.connect(self.deleteSelected)
        editBtn.clicked.connect(lambda: self.openResourceMenu(MakeFunctionWindow, editResource=funcObj))


        # Create the appropriate description
        commandList = funcObj.getCommandList()
        description = funcObj.getDescription()
        arguments   = funcObj.getArguments()

        selDescLbl.setText("Name: \n"                + funcObj.name + "\n\n"
                           "Description: \n"         + description + "\n\n"
                           "Length: \n"  + str(len(commandList)) + " Commands\n\n"
                           "Arguments:\n" + ''.join(['-' + arg + '\n' for arg in arguments]) + "\n")



        self.selLayout.addWidget(selDescLbl)
        self.selLayout.addWidget(editBtn)
        self.selLayout.addWidget(deleteBtn)
        self.selLayout.addStretch(1)



    def clearSelectedLayout(self):
        """
        Delete/garbage collect every widget in the layout
        :return:
        """
        for cnt in reversed(range(self.selLayout.count())):
            # takeAt does both the jobs of itemAt and removeWidget
            # namely it removes an item and returns it
            widget = self.selLayout.takeAt(cnt).widget()

            if widget is not None:
                # widget will be None if the item is a layout
                widget.deleteLater()

    def deleteSelected(self):
        # Get the selected object
        selObject = self.getSelected()
        if selObject is None: return

        # Warn the user of the consequences of continuing
        reply = QtWidgets.QMessageBox.question(self, 'Warning',
                                       "Deleting this object will delete it permanently.\n"
                                       "Do you want to continue?",
                                       QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            self.objManager.deleteObject(selObject)

        self.refreshTreeWidget()

    def getSelected(self):
        """Returns the selected resource, as a string of the resources name"""

        selectedObjects = self.objTree.selectedItems()
        if not len(selectedObjects): return None
        selObject = selectedObjects[0].text(0)
        return selObject


    def openResourceMenu(self, resourceMenuType, editResource=None):
        """
        This will open a resource menu window. Before this happens, it pauses the cameraWidget on the ObjectMenu,
        and after the resource menu is closed, it will select the newly created item (if one was created).

        :param resoureceMenuType: MakeGroupWindow, MakeRecordingWindow, MakeFunctionWindow, MakeObjectWindow, etc.
        :param editResource: If there is an object (say, a vision object or recording object) that you want to open the
                            editing window for, then pass it in through here.
        """

        self.cameraWidget.pause()

        # Open the window (the code will only continue once the window has closed)
        menuWindow = resourceMenuType(editResource, self.env, parent=self)

        # If the menuWindow created a new object, then select
        if menuWindow.newObject is not None:
            self.refreshTreeWidget(selectedItem=menuWindow.newObject.name)

        self.cameraWidget.play()

    def closeEvent(self, event):
        # This ensures that the cameraWidget will no longer be open when the window closes
        self.vision.endAllTrackers()
        self.cameraWidget.close()


# Make New Group Menu
class MakeGroupWindow(QtWidgets.QDialog):
    """
        This opens up when "New Group" button is clicked or when "add objects to group" is clicked in ObjectManager
    """

    def __init__(self, currentObj, env, parent):
        super(MakeGroupWindow, self).__init__(parent)

        self.newObject      = currentObj
        self.objManager     = env.getObjectManager()
        self.forbiddenNames = self.objManager.getForbiddenNames()


        # Initialize UI variables

        self.nameEdit   = QtWidgets.QLineEdit()
        self.objList    = QtWidgets.QListWidget()
        self.applyBtn   = QtWidgets.QPushButton("Apply", self)
        self.hintLbl    = QtWidgets.QLabel("")

        # Add trackablObjs to the objList
        objNames      = self.objManager.getObjectNameList(typeFilter=self.objManager.TRACKABLEOBJ)
        for i, objID in enumerate(objNames):
            self.objList.addItem(objID)

        self.objList.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)

        # If this is in 'editing' mode, restore the last state
        if self.newObject is not None:
            self.nameEdit.setText(self.newObject.name)
            self.nameEdit.setDisabled(True)

            # Select any objets that are in the group
            prevChosenIDs = [obj.name for obj in self.newObject.getMembers()]
            for i, objID in enumerate(objNames):
                if objID in prevChosenIDs:
                    self.objList.item(i).setSelected(True)


        # Initialize UI Elements
        self.initUI()
        self.isComplete()


        # Execute window and garbage collect afterwards
        finished = self.exec_()
        self.close()
        self.deleteLater()

        # If the window was valid, then create the object
        if finished:
            self.createNewObject()

    def initUI(self):




        nameLbl   = QtWidgets.QLabel("Group Name: ")
        cancelBtn = QtWidgets.QPushButton("Cancel", self)

        # Set up slots to check if the "Apply" button should be enabled or disabled
        self.objList.itemSelectionChanged.connect(self.isComplete)

        self.applyBtn.clicked.connect(self.accept)
        cancelBtn.clicked.connect(self.reject)


        bold = QtGui.QFont()
        bold.setBold(True)
        self.hintLbl.setFont(bold)
        self.hintLbl.setWordWrap(True)

        row1 = QtWidgets.QHBoxLayout()
        row2 = QtWidgets.QHBoxLayout()
        row3 = QtWidgets.QHBoxLayout()
        row4 = QtWidgets.QHBoxLayout()

        self.nameEdit.textChanged.connect(self.isComplete)
        row1.addWidget(nameLbl)
        row1.addWidget(self.nameEdit)

        row2.addWidget(self.objList)

        row3.addWidget(self.hintLbl)

        row4.addWidget(cancelBtn)
        row4.addStretch(1)
        row4.addWidget(self.applyBtn)

        mainVLayout = QtWidgets.QVBoxLayout()
        mainVLayout.addLayout(row1)
        mainVLayout.addLayout(row2)
        mainVLayout.addLayout(row3)
        mainVLayout.addLayout(row4)

        self.setLayout(mainVLayout)
        self.setMinimumHeight(400)
        self.setWindowTitle('Add Objects to Group')

    def createNewObject(self):
        name = self.nameEdit.text()

        self.objManager.deleteObject(name)

        # Get the name of every selected object
        selectedItems = self.objList.selectedItems()
        selectedObjs  = []

        for item in selectedItems:
            selectedObjs.append(item.text())


        # Add the appropriate tags to every object
        for objID in selectedObjs:
            trackableInGroup = self.objManager.getObject(objID)
            trackableInGroup.addTag(name)
            self.objManager.saveObject(trackableInGroup)

        self.objManager.refreshGroups()
        self.newObject = self.objManager.getObject(name)

    def isComplete(self):
        newHintText = ""
        if self.nameEdit.isEnabled():
            newName, newHintText = sanitizeName(self.nameEdit.text(), self.forbiddenNames)
            self.nameEdit.setText(newName)

        if len(self.objList.selectedItems()) == 0:
            newHintText = "You must select at least one object"

        self.hintLbl.setText(newHintText)


        # Set the apply button enabled if everything is filled out correctly
        setEnabled = len(newHintText) == 0 and len(self.objList.selectedItems())
        self.applyBtn.setEnabled(setEnabled)



# Make New Motion Recording Menu
class MakeRecordingWindow(QtWidgets.QDialog):
    """
        This opens up when "New Group" button is clicked or when "add objects to group" is clicked in ObjectManager
    """

    def __init__(self, currentObj, env, parent):
        super(MakeRecordingWindow, self).__init__(parent)

        self.newObject        = currentObj  # This is where the created object will go after being made in objManager
        self.robot            = env.getRobot()
        self.objManager       = env.getObjectManager()


        self.forbiddenNames   = self.objManager.getForbiddenNames()
        self.recording        = False   # State of recording
        self.baseTime         = None    # When continuing a recording, this is the time of the last recording ending
        self.startTime        = None    # Keeps track of *when* the recording started
        self.lastTime         = None    # Used to keep track of time between recorded points
        self.motionPath       = []      # Format:  [(time, gripperStatus, angleA, angleB, angleC, angleD), (...)]


        # Initialize UI variables
        self.timer       = QtCore.QTimer()
        self.nameEdit    = QtWidgets.QLineEdit()
        self.motionTbl   = QtWidgets.QTableWidget()
        self.recordBtn   = QtWidgets.QPushButton("Record")
        self.applyBtn    = QtWidgets.QPushButton("Apply", self)
        self.hintLbl     = QtWidgets.QLabel("")


        # If this is in 'editing' mode, restore the last state
        if self.newObject is not None:
            self.motionPath = self.newObject.getMotionPath()
            self.nameEdit.setText(self.newObject.name)
            self.nameEdit.setDisabled(True)

            # Move to the last position of the current recording
            lastPos = self.motionPath[-1][2:]
            pos = self.robot.getFK(servo0=lastPos[0], servo1=lastPos[1], servo2=lastPos[2])
            self.robot.setPos(coord=pos, wait=False)
            self.robot.setServoAngles(servo3=lastPos[3])

        # Initialize UI Elements
        self.initUI()
        self.refreshMotionList()
        self.isComplete()


        # Check if the robot is connected before running
        robot          = env.getRobot()
        if not robot.connected():
            message = "A robot must be connected to do movement recording."
            QtWidgets.QMessageBox.question(self, 'Error', message, QtWidgets.QMessageBox.Ok)
            return
        # Execute window and garbage collect afterwards
        finished = self.exec_()
        self.close()
        self.deleteLater()
        # If the window was valid, then create the object
        if finished:
            self.createNewObject()

    def initUI(self):
        self.recordBtn.setMinimumWidth(150)
        self.recordBtn.setIcon(QtGui.QIcon(Paths.record_start))


        monospace = QtGui.QFont("Monospace")
        monospace.setStyleHint(QtGui.QFont.TypeWriter)
        self.motionTbl.setFont(monospace)
        self.motionTbl.setColumnCount(3)
        self.motionTbl.setHorizontalHeaderLabels(("Time", "Servo Angles", "Gripper Action"))
        self.motionTbl.verticalHeader().hide()



        # Create non global UI variables
        nameLbl   = QtWidgets.QLabel("Recording Name: ")
        pathLbl   = QtWidgets.QLabel("Recorded Path")
        hint2Lbl  = QtWidgets.QLabel("Press 'Record' to start recording robot movements.\n"
                                     "While recording, press the robots suction cup to activate the pump.\n"
                                     "When you press Apply, areas of no movement at the start and end\n"
                                     "will be trimmed out.")

        cancelBtn = QtWidgets.QPushButton("Cancel", self)


        # Connect everything
        self.timer.timeout.connect(self.recordAction)
        self.recordBtn.clicked.connect(self.toggleRecording)
        self.applyBtn.clicked.connect(self.accept)
        cancelBtn.clicked.connect(self.reject)


        # Bolden the hintLbl
        bold = QtGui.QFont()
        bold.setBold(True)
        self.hintLbl.setFont(bold)
        self.hintLbl.setWordWrap(True)

        self.nameEdit.textChanged.connect(self.isComplete)

        # Create the rows then fill them
        row1 = QtWidgets.QHBoxLayout()
        row2 = QtWidgets.QHBoxLayout()
        row3 = QtWidgets.QHBoxLayout()
        row4 = QtWidgets.QHBoxLayout()
        row5 = QtWidgets.QHBoxLayout()
        row6 = QtWidgets.QHBoxLayout()
        row7 = QtWidgets.QHBoxLayout()



        row1.addWidget(nameLbl)
        row1.addWidget(self.nameEdit)

        row2.addWidget(self.recordBtn)

        row3.addWidget(pathLbl)

        row4.addWidget(self.motionTbl)
        row5.addWidget(hint2Lbl)
        row6.addWidget(self.hintLbl)

        row7.addWidget(cancelBtn)
        row7.addStretch(1)
        row7.addWidget(self.applyBtn)


        # Add everything to the main layout then touch it up a bit
        mainVLayout = QtWidgets.QVBoxLayout()
        mainVLayout.addLayout(row1)
        mainVLayout.addLayout(row2)
        mainVLayout.addLayout(row3)
        mainVLayout.addLayout(row4)
        mainVLayout.addLayout(row5)
        mainVLayout.addLayout(row6)
        mainVLayout.addLayout(row7)

        self.setLayout(mainVLayout)
        self.setMinimumHeight(550)
        self.setMinimumWidth(500)
        self.setWindowTitle('Create a Movement Recording')

    # Table events
    def resizeEvent(self, event):
        super(MakeRecordingWindow, self).resizeEvent(event)
        # Modify the resize event to keep the columns evenly distributed
        tableSize = self.motionTbl.width()
        sideHeaderWidth = self.motionTbl.verticalHeader().width()
        tableSize -= sideHeaderWidth
        numberOfColumns = self.motionTbl.columnCount()

        remainingWidth = tableSize % numberOfColumns
        for columnNum in range(numberOfColumns):
            if remainingWidth > 0:
                self.motionTbl.setColumnWidth(columnNum, int(tableSize / numberOfColumns) + 1)
                remainingWidth -= 1
            else:
                self.motionTbl.setColumnWidth(columnNum, int(tableSize / numberOfColumns))

    def addActionToTable(self, action, loading=False):
        # Add a single motionpath point to the self.motionTbl
        row = self.motionTbl.rowCount()

        time    = str(round(action[0], 2))
        gripper = str((False, True)[action[1]])
        servos  = str(round(action[2], 1)) + ", " + \
                  str(round(action[3], 1)) + ", " + \
                  str(round(action[4], 1)) + ", " + \
                  str(round(action[5], 1))

        self.motionTbl.insertRow(row)
        self.motionTbl.setItem(row, 0, QtWidgets.QTableWidgetItem(time))
        self.motionTbl.setItem(row, 1, QtWidgets.QTableWidgetItem(servos))
        self.motionTbl.setItem(row, 2, QtWidgets.QTableWidgetItem(gripper))

        # To prevent noticible lag when loading the window, don't skip rows when loading the table
        if not loading:
            self.motionTbl.scrollToItem(self.motionTbl.item(row, 0))

    def refreshMotionList(self):
        # # Clear previous data and remove previous rows
        # self.motionTbl.clear()
        while self.motionTbl.rowCount() > 0: self.motionTbl.removeRow(0)
        for r, action, in enumerate(self.motionPath):
            self.addActionToTable(action, loading=True)


    # Recording events
    def toggleRecording(self):
        self.lastTime = time()
        if self.recording:
            self.robot.setPump(False)
            self.recordBtn.setText("Record")
            if len(self.motionPath):
                self.recordBtn.setText("Continue Recording")
            self.timer.stop()
            self.recordBtn.setIcon(QtGui.QIcon(Paths.record_start))


        else:
            self.baseTime = 0
            if len(self.motionPath):
                self.baseTime = self.motionPath[-1][0]
            self.startTime = time()
            self.lastTime  = self.startTime

            self.timer.start()

            self.recordBtn.setText("Stop Recording")
            self.recordBtn.setIcon(QtGui.QIcon(Paths.record_end))
            self.robot.setActiveServos(all=False)

        self.recording = not self.recording
        self.isComplete()

    def recordAction(self):
        # This is where a point is recorded from the robot


        GRIPPER = 1

        now = time()
        if now - self.lastTime < 0.01: return  # If 10 ms havent passed, ignore
        print("Current FPS: ", 1.0 / (now - self.lastTime))

        self.lastTime = now

        # Every 10 times check the gripper status

        if len(self.motionPath) == 0:
            gripperStatus = 0
        elif len(self.motionPath) % 15 == 0:
            # If the robots tip is pressed, toggle the pump
            if self.robot.getTipSensor():
                gripperStatus = int(not self.motionPath[-1][GRIPPER])
                self.robot.setPump(gripperStatus)
            else:
                gripperStatus = self.motionPath[-1][GRIPPER]
        else:
            gripperStatus = self.motionPath[-1][GRIPPER]

        t         = now - self.startTime + self.baseTime
        angles    = self.robot.getAngles()
        tip       = gripperStatus
        newAction = [round(t, 3), int(tip), angles[0], angles[1], angles[2], angles[3]]


        self.motionPath.append(newAction)
        self.addActionToTable(newAction)

    def trimPath(self):
        """
        Gets rid of motionless parts of the motion path at the beginning and end, where the user is presumably pressing
        "record" or pressing "stop recording"
        """
        if len(self.motionPath) <= 20: return
        TIME    = 0
        GRIPPER = 1
        SERVO0  = 2
        SERVO1  = 3
        SERVO2  = 4
        SERVO3  = 5
        minDist = 1   # In degrees



        startPoint = self.motionPath[0]
        trimStart  = 0
        for i, p in enumerate(self.motionPath):
            trimStart = i
            # print("Start: ", startPoint, "curr: ", p)
            if abs(p[SERVO0] - startPoint[SERVO0]) > minDist: break
            if abs(p[SERVO1] - startPoint[SERVO1]) > minDist: break
            if abs(p[SERVO2] - startPoint[SERVO2]) > minDist: break
            if abs(p[SERVO3] - startPoint[SERVO3]) > minDist: break

        if trimStart < len(self.motionPath) - 1:
            self.motionPath = self.motionPath[trimStart:]

        if len(self.motionPath) <= 20: return


        endPoint   = self.motionPath[-1]
        trimEnd    = 0
        self.motionPath.reverse()
        for i, p in enumerate(self.motionPath):
            trimEnd = i
            # print("Start: ", endPoint, "curr: ", p)
            if abs(p[SERVO0] - endPoint[SERVO0]) > minDist: break
            if abs(p[SERVO1] - endPoint[SERVO1]) > minDist: break
            if abs(p[SERVO2] - endPoint[SERVO2]) > minDist: break
            if abs(p[SERVO3] - endPoint[SERVO3]) > minDist: break

        # Correct the order
        self.motionPath.reverse()
        if trimStart < len(self.motionPath) - 1:
            self.motionPath = self.motionPath[:-trimEnd]


        # Subtract the time from the start to every cell in the array now
        startTime = self.motionPath[0][TIME] - .1
        for i in range(len(self.motionPath)):
            self.motionPath[i][TIME] -= startTime
            if self.motionPath[i][TIME] < 0:
                printf("GUI| ERROR: Time is negative in motionPath!")

        startPoint[TIME] = 0
        endPoint[TIME]   = self.motionPath[-1][TIME] + .1
        self.motionPath = [startPoint] + self.motionPath + [endPoint]

    def optimizeMotionPath(self):
        if len(self.motionPath) <= 20: return


        TIME    = 0
        GRIPPER = 1
        SERVO0  = 2
        SERVO1  = 3
        SERVO2  = 4
        SERVO3  = 5

        # Run the motion path through a gausian smoother
        # Smooth the Time values, and all the servo values
        degree   = 8
        toSmooth = np.asarray(self.motionPath[:])[:, [TIME, SERVO0, SERVO1, SERVO2, SERVO3]].tolist()
        smooth   = rv.smoothListGaussian(toSmooth, degree)

        window    = degree * 2 - 1
        otherData = np.asarray(self.motionPath)[:, [GRIPPER]]

        cutData   = otherData[int(window / 2):-(int(window / 2) + 1), :]

        smooth          = np.asarray(smooth)
        timeAndGripper  = np.hstack((smooth[:, [0]], np.asarray(cutData)))
        unrounded       = np.hstack((timeAndGripper, smooth[:, 1:])).tolist()
        self.motionPath = unrounded

        self.roundMotionPath()

    def roundMotionPath(self):
        # Makes sure saves don't take a lot of space, by rounding any float errors
        self.motionPath = list(map(lambda a: [float(round(a[0], 2)),
                                    int(a[1]),
                                    float(round(a[2], 1)),
                                    float(round(a[3], 1)),
                                    float(round(a[4], 1)),
                                    float(round(a[5], 1))], self.motionPath))

    def createNewObject(self):
        if self.newObject is None:
            self.optimizeMotionPath()
            self.trimPath()

        self.roundMotionPath()
        # Create an actual TrackableObject with this information
        if self.newObject is not None:
            name        = self.newObject.name
            motionObj   = self.objManager.getObject(name)
        else:
            name = self.nameEdit.text()
            motionObj = MotionPath(name)

        motionObj.setup(motionPath = self.motionPath)

        self.objManager.saveObject(motionObj)
        self.newObject = motionObj

    def isComplete(self):
        newHintText = ""
        if self.nameEdit.isEnabled():
            newName, newHintText = sanitizeName(self.nameEdit.text(), self.forbiddenNames)
            self.nameEdit.setText(newName)

        self.hintLbl.setText(newHintText)

        if len(self.motionPath) <= 20:
            self.hintLbl.setText("Recording must be longer than 20 points of data")

        # Set the apply button enabled if everything is filled out correctly
        setEnabled = len(newHintText) == 0 and len(self.motionPath) > 20 and not self.recording
        self.applyBtn.setEnabled(setEnabled)

    def close(self):
        self.robot.setPump(False)
        self.timer.stop()



# Make a Custom Function
class MakeFunctionWindow(QtWidgets.QDialog):
    class ArgumentsList(QtWidgets.QWidget):
        """
        This is a list where the user can add/delete elements, its meant for setting the arguments of the function
        """
        def __init__(self, parent):
            super().__init__(parent)
            self.argList = QtWidgets.QListWidget()
            self.argList.setMaximumHeight(55)
            addBtn  = QtWidgets.QPushButton()
            delBtn  = QtWidgets.QPushButton()
            addBtn.setIcon(QtGui.QIcon(Paths.create))
            delBtn.setIcon(QtGui.QIcon(Paths.delete))

            addBtn.clicked.connect(self.addArgument)
            delBtn.clicked.connect(self.deleteArgument)

            col1 = QtWidgets.QVBoxLayout()
            col2 = QtWidgets.QVBoxLayout()

            col1.addWidget(self.argList)
            col2.addWidget(addBtn)
            col2.addWidget(delBtn)
            col2.addStretch()

            mainHLayout = QtWidgets.QHBoxLayout()
            # mainHLayout.addStretch()
            mainHLayout.addLayout(col1)
            mainHLayout.addLayout(col2)
            # mainHLayout.addStretch()
            self.setLayout(mainHLayout)
            self.layout().setContentsMargins(0, 0, 0, 0)

        def addArgument(self):
            var, accepted = QtWidgets.QInputDialog.getText(self, 'Add Argument', 'Variable Name: ')

            # If the user canceled, don't do anything
            if not accepted: return


            # Make sure the variable is a valid python variable
            possibleVariable = str(var)
            possibleVariable = re.sub('[^0-9a-zA-Z_]', '', possibleVariable)
            possibleVariable = re.sub('^[^a-zA-Z_]+', '', possibleVariable)

            # If the variable is invalid, then warn and re-prompt the user
            if not possibleVariable == var:
                QtWidgets.QMessageBox.question(self, 'Invalid Variable Name',
                                               'The argument must be a valid python variable. This means no numbers '
                                               'in the beginning, no spaces, and only numbers and letters',
                                               QtWidgets.QMessageBox.Ok)
                self.addArgument()
                return

            self.argList.addItem(var)

        def deleteArgument(self):

            # If something is selected, delete that
            selected = self.argList.selectedIndexes()
            if len(selected) > 0:
                self.argList.takeItem(selected[0].row())

            elif self.argList.count() > 0:
                # If nothing is selected, then just delete whatever is at the end of the list
                self.argList.takeItem(self.argList.count() - 1)

        def getArguments(self):
            """
            Returns a list of argument names
            """
            args = []
            for index in range(self.argList.count()):
                args.append(self.argList.item(index).text())
            return args

        def setArguments(self, arguments):
            # Delete any existing arguments
            while self.argList.count():
                self.argList.takeItem(0)

            # Add new arguments
            for arg in arguments:
                self.argList.addItem(arg)

    def __init__(self, currentObj, environment, parent):
        super(MakeFunctionWindow, self).__init__(parent)

        self.newObject      = currentObj
        self.objManager     = environment.getObjectManager()
        self.forbiddenNames = self.objManager.getForbiddenNames()


        # Initialize UI variables
        self.commandList = CommandList(environment, parent=self)
        self.commandMenu = CommandMenuWidget(parent=self)
        self.argList     = self.ArgumentsList(parent=self)
        self.nameEdit    = QtWidgets.QLineEdit()
        self.descEdit    = QtWidgets.QLineEdit()
        self.applyBtn    = QtWidgets.QPushButton("Apply", self)
        self.hintLbl     = QtWidgets.QLabel()


        # If this is in 'editing' mode, restore the last state
        if self.newObject is not None:
            self.nameEdit.setText(self.newObject.name)
            self.nameEdit.setDisabled(True)
            self.descEdit.setText(self.newObject.getDescription())
            self.commandList.loadData(self.newObject.getCommandList())
            self.argList.setArguments(self.newObject.getArguments())

        # Initialize UI Objects
        self.initUI()
        self.isComplete()


        # Execute Window and garbage collect it after
        finished = self.exec_()
        self.close()
        self.deleteLater()

        # If the window was valid, then create the object
        if finished:
            self.createNewObject()

    def initUI(self):
        self.nameEdit.textChanged.connect(self.isComplete)

        # Create non global UI variables
        nameLbl   = QtWidgets.QLabel("Function Name ")
        descLbl   = QtWidgets.QLabel("Function Description ")
        argLbl    = QtWidgets.QLabel("Arguments (optional)")
        hint2Lbl  = QtWidgets.QLabel("Drag commands into the list to create a function")
        cancelBtn = QtWidgets.QPushButton("Cancel", self)


        # Connect everything
        self.applyBtn.clicked.connect(self.accept)
        cancelBtn.clicked.connect(self.reject)


        # Bolden the hintLbl
        bold = QtGui.QFont()
        bold.setBold(True)
        self.hintLbl.setFont(bold)
        self.hintLbl.setWordWrap(True)

        self.nameEdit.setFixedWidth(300)
        self.descEdit.setFixedWidth(300)

        # Create the rows then fill them
        row1 = QtWidgets.QHBoxLayout()
        row2 = QtWidgets.QHBoxLayout()
        row3 = QtWidgets.QHBoxLayout()
        row4 = QtWidgets.QHBoxLayout()
        row5 = QtWidgets.QHBoxLayout()
        row6 = QtWidgets.QHBoxLayout()
        row7 = QtWidgets.QHBoxLayout()
        row8 = QtWidgets.QHBoxLayout()

        row1.addStretch(1)
        row1.addWidget(nameLbl)
        row1.addWidget(self.nameEdit)

        row2.addStretch(1)
        row2.addWidget(descLbl)
        row2.addWidget(self.descEdit)

        row3.addStretch()
        row3.addWidget(argLbl)
        row3.addStretch()

        row4.addWidget(self.argList)

        row5.addWidget(self.commandList)
        row5.addWidget(self.commandMenu)

        row6.addWidget(hint2Lbl)

        row7.addWidget(self.hintLbl)

        row8.addWidget(cancelBtn)
        row8.addStretch(1)
        row8.addWidget(self.applyBtn)


        # Add everything to the main layout then touch it up a bit
        mainVLayout = QtWidgets.QVBoxLayout()
        mainVLayout.addLayout(row1)
        mainVLayout.addLayout(row2)
        mainVLayout.addLayout(row3)
        mainVLayout.addLayout(row4)
        mainVLayout.addLayout(row5)
        mainVLayout.addLayout(row6)
        mainVLayout.addLayout(row7)
        mainVLayout.addLayout(row8)

        self.setLayout(mainVLayout)
        self.setMinimumHeight(550)
        self.setMinimumWidth(500)
        self.setWindowTitle('Create a Function')

    def createNewObject(self):
        # Create an actual TrackableObject with this information
        if self.newObject is not None:
            name        = self.newObject.name
            functionObj = self.objManager.getObject(name)
        else:
            name = self.nameEdit.text()
            functionObj = Function(name)
        functionObj.setup(commandList  = self.commandList.getSaveData(),
                          argumentList = self.argList.getArguments(),
                          description  = self.descEdit.text())
        self.objManager.saveObject(functionObj)

        self.newObject = functionObj

    def isComplete(self):
        newHintText = ""
        if self.nameEdit.isEnabled():
            newName, newHintText = sanitizeName(self.nameEdit.text(), self.forbiddenNames)
            self.nameEdit.setText(newName)

        self.hintLbl.setText(newHintText)

        # if len(self.motionPath) <= 20:
        #     self.hintLbl.setText("Recording must be longer than 20 points of data")

        # Set the apply button enabled if everything is filled out correctly
        setEnabled = len(newHintText) == 0
        self.applyBtn.setEnabled(setEnabled)



# Make New Object Wizard
class MakeObjectWindow(QtWidgets.QWizard):
    def __init__(self, currentObj, env, parent):
        print("GOT CURRENT OBJECT ", currentObj)
        super(MakeObjectWindow, self).__init__(parent)
        # If objToModifyName is None, then this will not ask the user for the name of the object
        self.newObject = currentObj

        # Since there are camera modules in the wizard, make sure that all tracking is off
        vision = env.getVision()
        vision.endAllTrackers()

        self.objManager = env.getObjectManager()
        self.vision     = env.getVision()

        if self.newObject is None:
            self.page1 = OWPage1(self.objManager.getForbiddenNames(), parent=self)
            self.addPage(self.page1)

        self.page2 = OWPage2(env, parent=self)
        self.page3 = OWPage3(parent=self)
        self.page4 = OWPage4(env, parent=self)

        self.addPage(self.page2)
        self.addPage(self.page3)
        self.addPage(self.page4)


        self.page2.newObject.connect(lambda: self.page4.setObject(self.page2.object))  # Link page3 to page2's object
        self.setWindowTitle("Object Wizard")
        self.setWindowIcon(QtGui.QIcon(Paths.objectWizard))

        # Center the window after building it
        self.timer    = QtCore.QTimer.singleShot(0, lambda: centerScreen(self))


        # Check if the camera is connected before running
        vStream = env.getVStream()
        if not vStream.connected():
            message = "A camera must be connected to add new objects"
            QtWidgets.QMessageBox.question(self, 'Error', message, QtWidgets.QMessageBox.Ok)
            return
        # Execute Window and garbage collect it after
        finished = self.exec_()
        self.close()
        self.deleteLater()
        # If the window was valid, then create the object
        if finished:
            self.createNewObject()

    def createNewObject(self):
        image       = self.page2.object.view.image.copy()
        rect        = self.page2.object.view.rect
        pickupRect  = self.page4.pickupRect
        height      = float(self.page3.heightTxt.text())

        # Create an actual TrackableObject with this information
        if self.newObject is not None:
            name        = self.newObject.name
            trackObject = self.objManager.getObject(name)
            if trackObject is None:
                printf("GUI| ERROR: Could not find object to add sample to!")
                return
        else:
            name = self.page1.nameEdit.text()
            trackObject = TrackableObject(name)

        trackObject.addNewView(image      = image,
                               rect       = rect,
                               pickupRect = pickupRect,
                               height     = height)

        self.objManager.saveObject(trackObject)
        self.newObject = trackObject

    def closeEvent(self, event):

        # Close any pages that have active widgets, such as the cameraWidget. This will trigger each page's close func.
        if self.newObject is None: self.page1.close()
        self.page2.close()
        self.page3.close()
        self.page4.close()

class OWPage1(QtWidgets.QWizardPage):
    """
    Get the name of the object
    """

    def __init__(self, forbiddenNames, parent):
        super(OWPage1, self).__init__(parent)

        # Create GUI objects
        self.forbiddenNames = forbiddenNames
        self.hintLbl       = QtWidgets.QLabel("")  # Tells the user why the name is invalid
        self.nameEdit        = QtWidgets.QLineEdit()

        self.nameEdit.textChanged.connect(self.completeChanged)

        self.initUI()

    def initUI(self):
        self.nameEdit.setMaximumWidth(260)

        welcomeLbl = QtWidgets.QLabel("Welcome to the Object Wizard!\n")
        introLbl   = QtWidgets.QLabel("This will walk you through teaching the software how to recognize a new object.")
        step1Lbl   = QtWidgets.QLabel("\n\nStep 1: Naming")
        promptLbl  = QtWidgets.QLabel("Please enter a unique name for this object.")


        # Set titles bold
        bold = QtGui.QFont()
        bold.setBold(True)
        step1Lbl.setFont(bold)
        self.hintLbl.setFont(bold)


        # Make the title larger
        bold.setPointSize(15)
        welcomeLbl.setFont(bold)


        # Place the GUI objects vertically
        col1 = QtWidgets.QVBoxLayout()
        col1.addWidget(welcomeLbl)
        col1.addWidget(introLbl)
        col1.addWidget(step1Lbl)
        col1.addWidget(promptLbl)
        col1.addWidget(self.nameEdit)
        col1.addStretch(1)
        col1.addWidget(self.hintLbl)
        mainHLayout = QtWidgets.QHBoxLayout()
        mainHLayout.addLayout(col1)

        self.setMinimumHeight(750)
        self.setMinimumWidth(900)
        self.setLayout(mainHLayout)

    def isComplete(self):
        newName, newHintText = sanitizeName(self.nameEdit.text(), self.forbiddenNames)
        self.nameEdit.setText(newName)
        self.hintLbl.setText(newHintText)

        return len(newHintText) == 0

class OWPage2(QtWidgets.QWizardPage):
    """
    Have the user select the object
    """

    newObject = QtCore.pyqtSignal()  # This emits when a valid object is selected, so that OWPage3 can update

    def __init__(self, environment, parent):
        super(OWPage2, self).__init__(parent)

        # Detach the robots servos so that the user can move the robot out of the way
        robot = environment.getRobot()
        robot.setActiveServos(all=False)

        # The final object is stored here:
        self.object       = None

        # The instructions are set in self.setStep(step) function, and are changed as needed
        self.stepLbl      = QtWidgets.QLabel("")
        self.howToLbl     = QtWidgets.QLabel("")
        self.hintLbl      = QtWidgets.QLabel("")  # This will tell the user if the object is good or bad

        # Create the camera widget and set it up
        self.vision       = environment.getVision()
        self.cameraWidget = CameraSelector(environment.getVStream(), parent=self)
        self.cameraWidget.play()
        # self.cameraWidget.declinePicBtn.clicked.connect(self.tryAgain)
        self.cameraWidget.objSelected.connect(self.objectSelected)


        self.initUI()
        self.setStep(1)


    def initUI(self):
        # Set titles bold
        bold = QtGui.QFont()
        bold.setBold(True)
        self.stepLbl.setFont(bold)
        self.hintLbl.setFont(bold)
        self.hintLbl.setWordWrap(True)

        # Create a tutorial gif that will be next to the video
        movieLbl   = QtWidgets.QLabel("")
        movie = QtGui.QMovie(Paths.help_sel_obj)
        movieLbl.setMovie(movie)
        movie.start()

        # Create a special row for the camera that will force it to remain in the center, regardless of size changes

        camRow = QtWidgets.QHBoxLayout()
        camRow.addWidget(self.cameraWidget)
        camRow.addWidget(movieLbl)
        camRow.addStretch(1)

        # Place the GUI objects vertically
        col1 = QtWidgets.QVBoxLayout()
        col1.addWidget(self.stepLbl)
        col1.addWidget(self.howToLbl)
        col1.addWidget(self.hintLbl)
        col1.addLayout(camRow)

        mainHLayout = QtWidgets.QHBoxLayout()
        mainHLayout.addLayout(col1)


        self.setLayout(mainHLayout)

    def setStep(self, step):
        if step == 1:
            s = "\n\nStep 2: Select the Object"
            h = "Please place the object you want to recognize ON THE TABLES SURFACE, in the middle of the screen.\n\n"\
                "Make sure the background is consistent and there is nothing on the screen except the object. The"\
                "\nwork area should be well lit, but not cause too much glare on the object if it's shiny. The video"\
                "\nshould be focused, and the object in the orientation that it will be recognized in. \n\n"\
                "When ready, Click the mouse on the corner of the object, drag it tightly over the object, then"\
                "\nrelease the mouse button."


        if step == 2:
            s = "\n\nStep 3: Verify"
            h = "-test text-"
        self.stepLbl.setText(s)
        self.howToLbl.setText(h)


    def objectSelected(self):
        """
            Runs when the user has selected an object on the CameraSelector widget.
            It will verify if the object is trackable (has enough points), if so, it will set the vision to tracking
            mode, generate a "trackable" object, and set the camera to play.

            Then, it will display information about the object next to the camera, so that the user can decide if
            they want to keep this selected object or try again.

            If there are not enough keypoints, the program will warn the user that this is a bad idea. If there are
            zero keypoints, it won't allow the user to track it, and will automatically revert the camera to
            selection mode.
        """
        # Reset all variables before setting a new object
        self.object = None
        self.completeChanged.emit()
        self.hintLbl.setText("")
        self.setStep(1)
        self.vision.endAllTrackers()


        rect  = self.cameraWidget.getSelectedRect()
        frame = self.cameraWidget.getSelectedFrame()

        # Get the "target" object from the image and rectangle
        trackable = TrackableObject("")
        trackable.addNewView(frame, rect, None, None)
        target    = self.vision.planeTracker.createTarget(trackable.getViews()[0])

        # Analyze it, and make sure it's a valid target. If not, return the camera to selection mode.
        if len(target.descrs) == 0 or len(target.keypoints) == 0:
            self.hintLbl.setText("Your selected object needs more detail to be tracked")
            self.cameraWidget.takeAnother()
            return

        # Turn on the camera, and start tracking
        self.object = target
        self.completeChanged.emit()
        self.cameraWidget.play()
        self.vision.endAllTrackers()  # Reset the trackers
        self.vision.addTarget(trackable)
        self.newObject.emit()



        # Do all the necessary things: Change the instructions, the step
        self.setStep(2)
        numPoints = str(len(self.object.descrs))
        des = "Good job, you have selected an object. Try moving the object around to see how accurate the" + \
            "\ntracking is. If it's not good enough, click 'Try Again'' on the bottom right of the camera to"       + \
            "\nreselect the object.\n\n" + \
            "Your selected object has " + numPoints + " points to describe it. " + \
            "The more detail on the object, the more points"   + \
            "\nwill be found, and the better the tracking will be. If you are having trouble tracking, try adding" + \
            "\ndetail to the object by drawing on it or putting a sticker on it. \n"
        self.howToLbl.setText(des)


        # If the object was not very good, warn the user. Otherwise, state the # of points on the object
        if len(target.descrs) < MIN_POINTS_TO_LEARN_OBJECT:
            self.hintLbl.setText("Your selected object has only " + numPoints + " points to describe it. It is not very"
                                 " detailed, or is too small. Try adding more detail by drawing on it, or adding a "
                                 "sticker to it. Tracking may not be very accurate.")
        else:
            self.hintLbl.setText("Tracking " + str(len(self.object.descrs)) + " Points")


    def isComplete(self):
        return self.object is not None

    def close(self):
        self.cameraWidget.close()
        self.vision.endAllTrackers()

class OWPage3(QtWidgets.QWizardPage):
    """
    Get the height of the object, in centimeters
    """

    def __init__(self, parent):
        super(OWPage3, self).__init__(parent)

        # Create GUI objects
        self.errorLbl  = QtWidgets.QLabel("")  # Tells the user why the height is invalid
        self.heightTxt = QtWidgets.QLineEdit("0")

        self.heightTxt.textChanged.connect(self.completeChanged)

        self.initUI()

    def initUI(self):
        self.heightTxt.setMaximumWidth(260)

        step1Lbl   = QtWidgets.QLabel("\n\nStep 4: Measure Height")
        promptLbl  = QtWidgets.QLabel("Please enter the height of the object in centimeters. "
                                      "\nIf the object is very thin, like paper, enter 0."
                                      "\nIf the object is not flat on the top, measure the height to the part of the "
                                      "object that the robot will be grasping.")

        centLbl    = QtWidgets.QLabel(" centimeters")

        # Set titles bold
        bold = QtGui.QFont()
        bold.setBold(True)
        step1Lbl.setFont(bold)
        self.errorLbl.setFont(bold)

        heightRow = QtWidgets.QHBoxLayout()
        heightRow.addWidget(self.heightTxt)
        heightRow.addWidget(centLbl)

        # Place the GUI objects vertically
        col1 = QtWidgets.QVBoxLayout()
        col1.addWidget(step1Lbl)
        col1.addWidget(promptLbl)
        col1.addLayout(heightRow)
        col1.addStretch(1)
        col1.addWidget(self.errorLbl)

        mainHLayout = QtWidgets.QHBoxLayout()
        mainHLayout.addLayout(col1)

        self.setMinimumHeight(750)
        self.setMinimumWidth(700)
        self.setLayout(mainHLayout)

    def isComplete(self):
        # Check if the user entered a valid height

        if len(self.heightTxt.text()) == 0:
            self.errorLbl.setText('')
            return False

        # Make sure the value is a number
        try:
            float(self.heightTxt.text())
        except ValueError:
            self.errorLbl.setText('You must input a real number.')
            return False

        if float(self.heightTxt.text()) < 0:
            self.errorLbl.setText('Height must be a number greater than or equal to 0.')
            return False

        self.errorLbl.setText('')
        return True

class OWPage4(QtWidgets.QWizardPage):
    """
    If anything is changed here, check the CoordWizard in CalibrationsGUI.py to make sure that it still works, since
    this class is used there.

    This page prompts the user to select the area of the object that can be picked up by the robot.

    Works with KPWPage2: Use setObject to set the picture. Every time a new object is set, it resets the widget somewhat
    and requets another picture. The isComplete() function returns true only when there is a selected rectangle.

    Only a rectangle is returned, to be used with PlaneTracker's pickupRect variable
    """
    """
    Get the pickup area of the object
    """

    def __init__(self, environment, parent):
        super(OWPage4, self).__init__(parent)


        # The final "rect" of the pickup area of the object is stored here: (x1,y1,x2,y2)
        self.pickupRect   = None

        self.yourDoneLbl  = QtWidgets.QLabel("")  # Displays a message to the user telling them they're all done!


        # Create the camera widget and set it up. The camera's image is set in self.setObject()
        self.vision       = environment.getVision()
        self.cameraWidget = CameraSelector(environment.getVStream(), parent=self, hideRectangle=False)
        self.cameraWidget.pause()
        # self.cameraWidget.declinePicBtn.clicked.connect(self.tryAgain)
        self.cameraWidget.objSelected.connect(self.rectSelected)

        self.initUI()

    def initUI(self):
        # Create the instructions
        desc = "You're almost done!\n\n" +\
               "Now that you have selected your object, please drag the mouse over THE ENTIRE AREA OF THE OBJECT \n" +\
               "\nthat is smooth, flat, and able to be picked up by the robot's suction cup. \n\n" \
               "\nThis information will be used in any commands that require the robot to pick up the object. If you" +\
               "\ndo not intend to use those functions, then just select an area around the center of the object.\n\n"

        stepLbl = QtWidgets.QLabel("Step 5: Select the Pickup Area")
        howToLbl = QtWidgets.QLabel(desc)


        # Set titles bold
        bold = QtGui.QFont()
        bold.setBold(True)
        stepLbl.setFont(bold)
        self.yourDoneLbl.setFont(bold)


        # Create a tutorial gif that will be next to the video
        movieLbl   = QtWidgets.QLabel("Could not find example gif")

        # Set the animated gif on the movieLbl
        movie = QtGui.QMovie(Paths.help_sel_pickuprect)
        movieLbl.setMovie(movie)
        movie.start()


        # Create a special row for the camera that will force it to remain in the center, regardless of size changes
        camRow = QtWidgets.QHBoxLayout()
        camRow.addStretch(1)
        camRow.addWidget(self.cameraWidget)
        camRow.addWidget(movieLbl)
        camRow.addStretch(1)


        # Place the GUI objects vertically
        col1 = QtWidgets.QVBoxLayout()
        col1.addWidget(stepLbl)
        col1.addWidget(howToLbl)
        col1.addWidget(self.yourDoneLbl)
        col1.addStretch(1)
        col1.addLayout(camRow)
        col1.addStretch(1)

        mainHLayout = QtWidgets.QHBoxLayout()
        mainHLayout.addLayout(col1)

        self.setLayout(mainHLayout)


    def setObject(self, target):
        # Crop the image of just the object and display it on the Camera widget
        r       = target.view.rect
        cropped = target.view.image[r[1]:r[3], r[0]:r[2]]

        self.cameraWidget.setFrame(cropped)

        self.yourDoneLbl.setText("")
        self.pickupRect = None
        self.cameraWidget.takeAnother()
        self.completeChanged.emit()


    def rectSelected(self):
        # Runs when the user has selected an area on self.cameraWidget
        rect = self.cameraWidget.getSelectedRect()
        self.pickupRect = rect
        self.yourDoneLbl.setText("Congratulations, you've created a new object! "
                                 "\nThis will now be saved in a seperate file, and can be used in any project.")
        self.completeChanged.emit()


    def isComplete(self):
        return self.pickupRect is not None

    def close(self):
        self.cameraWidget.close()




# Utility function for determining if a name is a valid name for a resource
def sanitizeName(name, forbiddenNames):
    """
    This function takes a string name, that the user wants to name a new object with

    Returns
        newName:    A modified name, with capitalized first level and certain characters changed
        hintText    Any hint text the user should have, to know why their name doesnt work. If None, name is valid!
    """
    # DO NAME MODIFICATIONS BEFORE CHECKING VALIDITIY
    # If the first character is a space, remove it
    if len(name) > 0 and name[0] == " ":
        name = name[1:]

    if len(name) > 0:
        # Make sure the first letter of each word is capitalized, and any spaces are converted to underscores
        name = name[0].upper() + name[1:]
        name = name.replace('_', ' ')


    # START CHECKING FOR VALIDITIY
    if len(name) == 0:
        return name, "You must input a name to continue"



    # Record any characters that wre not valid
    validChars   = "0123456789abcdefghijklmnopqrstuvwxyz- "
    invalidChars = []
    for char in name:
        if char.lower() not in validChars:
            invalidChars.append(char)
    invalidChars = list(set(invalidChars))


    # If there were errors, then display a message explaining why
    if len(invalidChars) > 0:
        return name, 'You cannot have the following characters in the resource name: ' + ''.join(invalidChars)

    # Make forbiddenNames all be lowercase, for easy comparation
    forbiddenNames = [name.lower() for name in forbiddenNames]

    # Check if the name is the same as any of the forbidden names
    if name.lower().strip() in forbiddenNames:
        return name, 'There is already a resource named ' + name.strip() + '! \n' + \
                     ' If you want to replace it, delete the original and try again.'

    if len(name) > 30:
        return name, 'That name is too long.'

    if name[-1] == " ":
        return name, 'Names cannot end with a space.'
    # If there were no errors, then turn the "next" button enabled, and make the error message dissapear
    return name, ''




