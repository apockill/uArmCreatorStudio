import numpy             as np
import Logic.RobotVision as rv
from time                import time
from PyQt5               import QtCore, QtWidgets, QtGui
from CommonGUI           import centerScreen
from CameraGUI           import CameraWidget, CameraSelector, cvToPixFrame
from Logic               import Paths
from Logic.Global        import printf
from Logic.ObjectManager import TrackableObject, MotionPath
from Logic.RobotVision   import MIN_POINTS_TO_LEARN_OBJECT


class ObjectManagerWindow(QtWidgets.QDialog):


    def __init__(self, environment, parent):
        super(ObjectManagerWindow, self).__init__(parent)
        self.env                = environment
        self.vision             = environment.getVision()
        self.objManager         = environment.getObjectManager()
        self.cameraWidget       = CameraWidget(self.env.getVStream().getFilteredWithID, parent=self)

        # Global UI Variables
        self.selLayout          = QtWidgets.QVBoxLayout()
        self.objTree            = QtWidgets.QTreeWidget()



        # Initialize the UI
        self.initUI()
        self.cameraWidget.play()
        self.refreshObjectList()

    def initUI(self):
        self.objTree.setIndentation(10)
        self.objTree.setHeaderLabels([""])
        self.objTree.header().close()

        # CREATE OBJECTS AND LAYOUTS FOR ROW 1 COLUMN (ALL)
        newObjBtn    = QtWidgets.QPushButton("New Trackable Object")
        newGrpBtn    = QtWidgets.QPushButton("New Trackable Group")
        newRecBtn    = QtWidgets.QPushButton("New Motion Recording")


        newObjBtn.setFixedWidth(150)
        newGrpBtn.setFixedWidth(150)
        newRecBtn.setFixedWidth(150)
        self.objTree.setMinimumWidth(260)

        # Connect everything up
        newObjBtn.clicked.connect(lambda: self.openObjectWizard())
        newGrpBtn.clicked.connect(lambda: self.openGroupMenu())
        newRecBtn.clicked.connect(lambda: self.openRecordingMenu())
        self.objTree.itemSelectionChanged.connect(self.refreshSelected)


        # CREATE OBJECTS AND LAYOUTS FOR COLUMN 1
        listGBox     = QtWidgets.QGroupBox("Loaded Objects")
        listVLayout  = QtWidgets.QVBoxLayout()
        listVLayout.addWidget(self.objTree)
        listGBox.setLayout(listVLayout)


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


    def refreshObjectList(self, selectedItem=None):
        # Clear the objectList, and reload all object names from the environment
        # If selectedItem is a string, it will try to select the item. This is for obj's added through the ObjWizard
        # Clear the current objectList
        self.objTree.clear()
        self.vision.endAllTrackers()


        # Get a list for each section of the QTreeWidget that there will be
        visObjs = self.objManager.getObjectNameList(self.objManager.TRACKABLEOBJ)
        visObjs.sort()

        grpObjs = self.objManager.getObjectNameList(self.objManager.TRACKABLEGROUP)
        grpObjs.sort()

        rcdObjs = self.objManager.getObjectNameList(self.objManager.MOTIONPATH)
        rcdObjs.sort()

        tree = [["Vision Objects", visObjs], ["Vision Groups", grpObjs], ["Motion Recordings", rcdObjs]]


        for section in tree:
            # Create the Title
            title = QtWidgets.QTreeWidgetItem(self.objTree)
            title.setText(0, section[0])
            for name in section[1]:
                newItem = QtWidgets.QTreeWidgetItem(title, [name])

                # Select the item specified in selectedItem arg
                if name == selectedItem:
                    self.objTree.setCurrentItem(newItem)


        self.objTree.expandAll()

    def refreshSelected(self):
        # Modifies self.selectedObjVLayout to show the currently selected object, it's name, description, etc.

        self.clearSelectedLayout()

        # Get the selected object
        selObject = self.getSelected()
        if selObject is None:
            self.clearSelectedLayout()
            return

        obj = self.objManager.getObject(selObject)


        self.vision.endAllTrackers()

        if obj is None:
            self.clearSelectedLayout()
            return


        # Make the SelectedObject window reflect the information about the object (and it's type) that is curr. selected
        if isinstance(obj, self.objManager.TRACKABLEOBJ):
            self.setSelectionTrackable(obj)
            self.vision.addTarget(obj)
            return

        if isinstance(obj, self.objManager.TRACKABLEGROUP):
            self.setSelectionGroup(obj)
            self.vision.addTarget(obj)
            return

        if isinstance(obj, self.objManager.MOTIONPATH):
             self.setSelectionPath(obj)


    def setSelectionTrackable(self, trackableObj):

        views = trackableObj.getViews()
        if len(views) == 0:
            printf("ERROR: Object returned ZERO samples!")
            self.clearSelectedLayout()
            return
        selDescLbl         = QtWidgets.QLabel("")   # Description of selected object
        selImgLbl          = QtWidgets.QLabel("")   # A small picture of the object
        deleteBtn          = QtWidgets.QPushButton("Delete")
        addOrientationBtn  = QtWidgets.QPushButton("Add Orientation")


        # Connect any buttons
        deleteBtn.clicked.connect(self.deleteSelected)
        addOrientationBtn.clicked.connect(lambda: self.openObjectWizard(self.getSelected()))


        # Create a pretty icon for the object, so it's easily recognizable. Use the first sample in the objectt
        icon = cvToPixFrame(trackableObj.getIcon(150, 350))
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
                           "Belongs To Groups:\n" + ''.join(['-'+tag+'\n' for tag in trackableObj.getTags()]) + "\n"
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
        editBtn.clicked.connect(lambda: self.openGroupMenu(groupObj=trackableGrp))


        # Create the appropriate description
        groupMembers = ['-' + obj.name + '\n' for obj in trackableGrp.getMembers()]
        selDescLbl.setText("Name: \n"          + trackableGrp.name+ "\n\n"
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
        editBtn.clicked.connect(lambda: self.openRecordingMenu(pathObj=pathObj))


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


    def clearSelectedLayout(self):
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

        self.refreshObjectList()

    def getSelected(self):
        # Returns the selected object
        selectedObjects = self.objTree.selectedItems()
        if not len(selectedObjects): return None
        selObject = selectedObjects[0].text(0)
        return selObject


    def openObjectWizard(self, trackableObj=None):

        vStream = self.env.getVStream()
        if not vStream.connected():
            message = "A camera must be connected to add new objects"
            QtWidgets.QMessageBox.question(self, 'Error', message, QtWidgets.QMessageBox.Ok)
            return

        printf("Opening Object Wizard!")

        self.cameraWidget.pause()

        # Get the object information from the user using the Object Wizard
        oWizard = ObjectWizard(trackableObj, self.env, self)
        finished = oWizard.exec_()

        # Close objectWizard, make sure that even if "cancel" was pressed, the window still closes
        oWizard.close()
        oWizard.deleteLater()

        if finished:
            oWizard.createNewObject()
            self.refreshObjectList(selectedItem=oWizard.newObject.name)

        self.cameraWidget.play()

    def openGroupMenu(self, groupObj=None):
        """ :type groupObj: Logic.ObjectManager.TrackableGroupObject """

        # Opens a menu that lets people choose what objects to put into a group
        choosableObjects = self.objManager.getObjectNameList(objFilter=self.objManager.TRACKABLEOBJ)
        forbiddenNames   = self.objManager.getForbiddenNames()
        if groupObj is None:
            groupMenu = EditGroupWindow(choosableObjects, forbiddenNames, [], None, self)
        else:
            groupMenu = EditGroupWindow(choosableObjects, forbiddenNames, groupObj.getMembers(), groupObj.name, self)

        accepted = groupMenu.exec_()



        if accepted:
            # Delete the tags of the original version (if there is one) before adding a new one

            grpID = groupMenu.getName()
            self.objManager.deleteObject(grpID)

            # Add the appropriate tags to every object
            for objID in groupMenu.getSelected():
                groupObj = self.objManager.getObject(objID)
                groupObj.addTag(grpID)
                self.objManager.saveObject(groupObj)

            self.objManager.refreshGroups()
            self.refreshObjectList(selectedItem=grpID)
        else:
            printf("User rejected prompt. Ignoring changes!")

        groupMenu.close()
        groupMenu.deleteLater()

    def openRecordingMenu(self, pathObj=None):
        robot          = self.env.getRobot()
        if not robot.connected():
            message = "A robot must be connected to do motion recording."
            QtWidgets.QMessageBox.question(self, 'Error', message, QtWidgets.QMessageBox.Ok)
            return


        forbiddenNames = self.objManager.getForbiddenNames()

        recMenu        = MotionRecordWindow(forbiddenNames, pathObj, robot, self.objManager, self)
        finished       = recMenu.exec_()

        if finished:
            recMenu.createNewObject()
            self.refreshObjectList(selectedItem=recMenu.newObject.name)

        recMenu.close()
        recMenu.deleteLater()



    def closeEvent(self, event):
        # This ensures that the cameraWidget will no longer be open when the window closes
        self.vision.endAllTrackers()
        self.cameraWidget.close()



# Make New Group Menu
class EditGroupWindow(QtWidgets.QDialog):
    """
        This opens up when "New Group" button is clicked or when "add objects to group" is clicked in ObjectManager
    """

    def __init__(self, trackableObjs, forbiddenNames, previouslyChosen, currentName, parent):
        super(EditGroupWindow, self).__init__(parent)
        self.objNames       = trackableObjs  # A list of strings of trackable objects
        self.forbiddenNames = forbiddenNames


        # Initialize UI variables
        self.nameEdit    = QtWidgets.QLineEdit(currentName)
        self.objList     = QtWidgets.QListWidget()
        self.applyBtn    = QtWidgets.QPushButton("Apply", self)
        self.hintLbl     = QtWidgets.QLabel("")


        # If no name was passed, set a default name. If one was passed, disable the nameBox
        if currentName is None:
            self.nameEdit.setText("")
        else:
            self.nameEdit.setDisabled(True)

        self.objList.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)


        # Add trackablObjs to the objList
        prevChosenIDs = [obj.name for obj in previouslyChosen]
        for i, objID in enumerate(trackableObjs):
            self.objList.addItem(objID)
            if objID in prevChosenIDs:
                self.objList.item(i).setSelected(True)

        self.initUI()
        self.isComplete()

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

    def getName(self):
        return self.nameEdit.text()

    def getSelected(self):
        selectedItems = self.objList.selectedItems()
        selectedObjs  = []

        for item in selectedItems:
            selectedObjs.append(item.text())
        return selectedObjs

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
class MotionRecordWindow(QtWidgets.QDialog):
    """
        This opens up when "New Group" button is clicked or when "add objects to group" is clicked in ObjectManager
    """

    def __init__(self, forbiddenNames, currentObj, robot, objManager, parent):
        super(MotionRecordWindow, self).__init__(parent)

        self.robot            = robot
        self.newObject        = currentObj  # This is where the created object will go after being made in objManager
        self.objManager       = objManager

        self.forbiddenNames   = forbiddenNames
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

        # If no name was passed, set a default name. If one was passed, disable the nameBox
        if self.newObject is None:
            self.nameEdit.setText("")
        else:
            self.motionPath = self.newObject.getMotionPath()
            self.nameEdit.setText(self.newObject.name)
            self.nameEdit.setDisabled(True)

            lastPos = self.motionPath[-1][2:]
            pos = robot.getFK(servo0=lastPos[0], servo1=lastPos[1], servo2=lastPos[2])
            robot.setPos(coord=pos, wait=False)
            robot.setServoAngles(servo3=lastPos[3])

        self.initUI()
        self.refreshMotionList()
        self.isComplete()

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
        hint2Lbl  = QtWidgets.QLabel("While recording, press the robots suction cup to activate the pump.\n"
                                     "When you press Apply, Gaussian smoothing will be applied, and areas of no\n"
                                     "movement at the start and end will be trimmed out.")
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


        # Create the rows then fill them
        row1 = QtWidgets.QHBoxLayout()
        row2 = QtWidgets.QHBoxLayout()
        row3 = QtWidgets.QHBoxLayout()
        row4 = QtWidgets.QHBoxLayout()
        row5 = QtWidgets.QHBoxLayout()
        row6 = QtWidgets.QHBoxLayout()
        row7 = QtWidgets.QHBoxLayout()

        self.nameEdit.textChanged.connect(self.isComplete)
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
        self.setWindowTitle('Create a Motion Recording')


    # Table events
    def resizeEvent(self, event):
        super(MotionRecordWindow, self).resizeEvent(event)
        # Modify the resize event to keep the columns evenly distributed
        tableSize = self.motionTbl.width()
        sideHeaderWidth = self.motionTbl.verticalHeader().width()
        tableSize -= sideHeaderWidth
        numberOfColumns = self.motionTbl.columnCount()

        remainingWidth = tableSize % numberOfColumns
        for columnNum in range(numberOfColumns):
            if remainingWidth > 0:
                self.motionTbl.setColumnWidth(columnNum, int(tableSize/numberOfColumns) + 1 )
                remainingWidth -= 1
            else:
                self.motionTbl.setColumnWidth(columnNum, int(tableSize/numberOfColumns) )

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
            self.robot.setGripper(False)
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
                self.robot.setGripper(gripperStatus)
            else:
                gripperStatus = self.motionPath[-1][GRIPPER]
        else:
            gripperStatus = self.motionPath[-1][GRIPPER]

        t         = now - self.startTime + self.baseTime
        angles    = self.robot.getServoAngles()
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
            self.motionPath[i][TIME] = self.motionPath[i][TIME] - startTime
            if self.motionPath[i][TIME] < 0:
                printf("ERROR: Time is negative in motionPath!")

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
        degree = 10
        toSmooth = np.asarray(self.motionPath[:])[:, [TIME, SERVO0, SERVO1, SERVO2, SERVO3]].tolist()
        smooth = rv.smoothListGaussian(toSmooth, degree)

        window    = degree * 2 - 1
        otherData = np.asarray(self.motionPath)[:, [GRIPPER]]

        cutData   = otherData[int(window / 2):-(int(window / 2) + 1), :]
        # print("CutData: ", cutData[:10], "length: ", len(cutData), "cut from/to: ", int(window / 2), (int(window / 2) + 1))

        smooth         = np.asarray(smooth)
        timeAndGripper = np.hstack((smooth[:, [0]], np.asarray(cutData)))
        undrounded     = np.hstack((timeAndGripper, smooth[:, 1:])).tolist()

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
            if motionObj is None:
                printf("ERROR: Could not find object to add sample to!")
                return
        else:
            name = self.nameEdit.text()
            motionObj = MotionPath(name)

        motionObj.setMotionPath(self.motionPath)

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
        self.robot.setGripper(False)
        self.timer.stop()



# Make New Object Wizard
class ObjectWizard(QtWidgets.QWizard):
    def __init__(self, objNameToModify, environment, parent):
        super(ObjectWizard, self).__init__(parent)
        # If objToModifyName is None, then this will not ask the user for the name of the object
        self.objToModifyName = objNameToModify

        # Since there are camera modules in the wizard, make sure that all tracking is off
        vision = environment.getVision()
        vision.endAllTrackers()

        self.objManager = environment.getObjectManager()
        self.vision     = environment.getVision()
        self.newObject  = None  # Is set in self.close()

        if objNameToModify is None:
            self.page1 = OWPage1(self.objManager.getForbiddenNames(), parent=self)
            self.addPage(self.page1)

        self.page2 = OWPage2(environment, parent=self)
        self.page3 = OWPage3(parent=self)
        self.page4 = OWPage4(environment, parent=self)

        self.addPage(self.page2)
        self.addPage(self.page3)
        self.addPage(self.page4)


        self.page2.newObject.connect(lambda: self.page4.setObject(self.page2.object))  # Link page3 to page2's object
        self.setWindowTitle("Object Wizard")
        self.setWindowIcon(QtGui.QIcon(Paths.objectWizard))

        # Center the window after building it
        self.timer    = QtCore.QTimer.singleShot(0, lambda: centerScreen(self))







    def createNewObject(self):
        image       = self.page2.object.view.image.copy()
        rect        = self.page2.object.view.rect
        pickupRect  = self.page4.pickupRect
        height      = float(self.page3.heightTxt.text())

        # Create an actual TrackableObject with this information
        if self.objToModifyName is not None:
            name        = self.objToModifyName
            trackObject = self.objManager.getObject(name)
            if trackObject is None:
                printf("ERROR: Could not find object to add sample to!")
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
        if self.objToModifyName is None: self.page1.close()
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

        # Set the animated gif on the movieLbl
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
            h = "Please place the object you want to recognize in the center of the cameras view.\n\n"  +\
                "Make sure the background is consistent and there is nothing on the screen except the object. The" +\
                "\nwork area should be well lit, but not cause too much glare on the object if it's shiny. The video" +\
                "\nshould be focused, and the object in the orientation that it will be recognized in. \n\n" +\
                "When ready, Click the mouse on the corner of the object, drag it tightly over the object, then" + \
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
        self.heightTxt = QtWidgets.QLineEdit()

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
               "Now that you have selected your object, please drag the mouse over the area of the object that is " +\
               "\nsmooth, flat, and able to be picked up by the robot's suction cup. \n\n" +\
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
        movieLbl.resize(320, 320)

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





def sanitizeName(name, forbiddenNames):
    """
    This function takes a string name, that the user wants to name a new object with

    Returns
        newName:    A modified name, with capitalized first level and certain characters changed
        hintText    Any hint text the user should have, to know why their name doesnt work. If None, name is valid!
    """

        # Check if the user entered a valid name name is valid
    if len(name) == 0:
        return name, "You must input a name to continue"

    # Make sure the first letter is uppercase, and any spaces are converted to underscores
    name = name.replace(name[0], name[0].upper())
    name = name.replace('_', ' ')


    # Record any characters that wre not valid
    validChars   = "0123456789abcdefghijklmnopqrstuvwxyz- "
    invalidChars = []
    for char in name:
        if char.lower() not in validChars:
            invalidChars.append(char)
    invalidChars = list(set(invalidChars))


    # If there were errors, then display a message explaining why
    if len(invalidChars) > 0:
        return name, 'You cannot have the following characters in your object name: ' + ''.join(invalidChars)

    # Make forbiddenNames all be lowercase, for easy comparation
    forbiddenNames = [name.lower() for name in forbiddenNames]

    # Check if the name is the same as any of the forbidden names
    if name.lower().strip() in forbiddenNames:
        return name, 'There is already an object named ' + name.strip() + '! \n' + \
                     ' If you want to replace it, delete the original and try again.'

    # If there were no errors, then turn the "next" button enabled, and make the error message dissapear
    return name, ''