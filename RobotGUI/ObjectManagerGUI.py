from PyQt5                      import QtCore, QtWidgets, QtGui
from RobotGUI                   import Icons
from RobotGUI.CameraGUI         import CameraWidget, CameraSelector
from RobotGUI.Logic.Global      import printf


class ObjectManager(QtWidgets.QDialog):


    def __init__(self, environment, parent):
        super(ObjectManager, self).__init__(parent)
        self.mainWindowParent   = parent  # Since ObjManager creates windows and deletes itself, it passes Main parent
        self.env                = environment
        self.cameraWidget       = CameraWidget(self.env.getVStream().getPixFrame, parent=self)

        self.selectedObjVLayout = QtWidgets.QVBoxLayout()

        self.initUI()
        self.cameraWidget.play()

        # For debugging
        self.openKeypointWizard()

    def initUI(self):

        # CREATE OBJECTS AND LAYOUTS FOR ROW 1 COLUMN (ALL)
        createBtn   = QtWidgets.QPushButton("Create New")
        loadBtn     = QtWidgets.QPushButton("Load Existing")
        createBtn.setFixedWidth(130)
        loadBtn.setFixedWidth(130)
        createBtn.clicked.connect(self.openKeypointWizard)

        # CREATE OBJECTS AND LAYOUTS FOR COLUMN 1
        objectsList = QtWidgets.QListWidget()
        objectsList.setMinimumWidth(260)
        listVLayout = QtWidgets.QVBoxLayout()
        listVLayout.addWidget(objectsList)
        listGBox    = QtWidgets.QGroupBox("Loaded Objects")
        listGBox.setLayout(listVLayout)


        # CREATE OBJECTS AND LAYOUTS FOR COLUMN 2
        selectedGBox = QtWidgets.QGroupBox("Selected Object")
        selectedGBox.setLayout(self.selectedObjVLayout)


        # CREATE OBJECTS AND LAYOUTS FOR COLUMN 3


        # Put everything into 1 row (top) and multiple columns just below the row
        row1 = QtWidgets.QHBoxLayout()
        col1 = QtWidgets.QVBoxLayout()
        col2 = QtWidgets.QVBoxLayout()
        col3 = QtWidgets.QVBoxLayout()

        row1.addWidget(createBtn)
        row1.addWidget(loadBtn)
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
        self.setWindowTitle('Object Manager')
        self.setWindowIcon(QtGui.QIcon(Icons.objectManager))

        self.updateSelectedObjMenu()

    def updateSelectedObjMenu(self):
        # Modifies self.selectedObjVLayout to show the currently selected object

        layout = self.selectedObjVLayout
        # Delete everything currently in the layout
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().deleteLater()

        nameLbl = QtWidgets.QLabel("Name:")
        trackLbl = QtWidgets.QLabel("Detection Methods:")



        layout.addWidget(nameLbl)
        layout.addWidget(trackLbl)
        layout.addStretch(1)

    def openKeypointWizard(self):
        # Close the objectManager and open the KeypointWizard.

        printf("ObjectManager.openKeypointWizard(): Opening Keypoint Wizard!")

        self.close()

        kpWizard = KeypointWizard(self.env, parent=self.mainWindowParent)
        kpWizard.exec_()

    def closeEvent(self, event):
        # This ensures that the cameraWidget will no longer be open when the window closes
        self.cameraWidget.pause()



# KEYPOINT WIZARD
class KeypointWizard(QtWidgets.QWizard):
    def __init__(self, environment, parent):
        super(KeypointWizard, self).__init__(parent)

        self.addPage(KPWPage1(parent=self))
        self.addPage(KPWPage2(environment, parent=self))

        self.setWindowTitle("Keypoint Wizard")
        self.setWindowIcon(QtGui.QIcon(Icons.objectWizard))


class KPWPage1(QtWidgets.QWizardPage):
    def __init__(self, parent):
        super(KPWPage1, self).__init__(parent)

        # Create GUI objects
        self.errorLbl   = QtWidgets.QLabel("")  # Tells the user why the name is invalid
        self.nameTxt    = QtWidgets.QLineEdit()

        self.nameTxt.textChanged.connect(self.completeChanged)

        self.initUI()

    def initUI(self):
        self.nameTxt.setMaximumWidth(260)

        welcomeLbl      = QtWidgets.QLabel("Welcome to the Keypoint Wizard!\n")
        introLbl        = QtWidgets.QLabel("This will walk you through teaching the software how to recognize a new object.")
        step1Lbl        = QtWidgets.QLabel("\n\nStep 1:")
        promptLbl       = QtWidgets.QLabel("Please enter a unique name for this object")


        # Set titles bold
        bold = QtGui.QFont()
        bold.setBold(True)
        welcomeLbl.setFont(bold)
        step1Lbl.setFont(bold)

        # Place the GUI objects vertically
        col1 = QtWidgets.QVBoxLayout()
        col1.addWidget(welcomeLbl)
        col1.addWidget(introLbl)
        col1.addWidget(step1Lbl)
        col1.addWidget(promptLbl)
        col1.addWidget(self.nameTxt)
        col1.addStretch(1)
        col1.addWidget(self.errorLbl)
        mainHLayout = QtWidgets.QHBoxLayout()
        mainHLayout.addLayout(col1)

        self.setLayout(mainHLayout)

    def isComplete(self):
        # Check if the user entered a valid name name is valid
        if len(self.nameTxt.text()) == 0: return False

        # Make sure any spaces are converted to underscores
        self.nameTxt.setText(self.nameTxt.text().replace(' ', '_'))


        # Record any characters that wre not valid
        validChars   = "0123456789abcdefghijklmnopqrstuvwxyz-_"
        invalidChars = []
        name         = self.nameTxt.text()
        for char in name:
            if char.lower() not in validChars:
                invalidChars.append(char)
        invalidChars = list(set(invalidChars))


        # If there were errors, then display a message explaining why
        if len(invalidChars) > 0:
            self.errorLbl.setText('You cannot have the following characters in your object name: ' +
                                  ''.join(invalidChars))
            return False

        # If there were no errors, then turn the "next" button enabled, and make the error message dissapear
        self.errorLbl.setText('')
        return True


class KPWPage2(QtWidgets.QWizardPage):
    def __init__(self, environment, parent):
        super(KPWPage2, self).__init__(parent)

        # Vision is used in self.isSelected() to make sure the object is valid, and to display KP information
        self.vision = environment.getVision()
        vStream     = environment.getVStream()

        self.camera = CameraSelector(vStream.getFrame, vStream.getPixFrame, parent=self)
        self.camera.play()
        self.camera.frameSelected.connect(self.completeChanged)
        self.camera.declinePicBtn.clicked.connect(self.completeChanged)
        self.initUI()

    def initUI(self):
        # Create GUI objects
        step2Lbl  = QtWidgets.QLabel("\n\nStep 2:")
        promptLbl = QtWidgets.QLabel("Please place the object in the center of the screen, in the orientation that the"
                                " object will most commonly be in. \n\nMake sure the lighting is normal and the picture"
                                " is focused. \n\nWhen ready, Click the mouse on the corner of the object, and drag."
                                "\n\n Drag the rectangle until it covers the object tightly, then let go of the mouse.")

        # Set titles bold
        bold = QtGui.QFont()
        bold.setBold(True)
        step2Lbl.setFont(bold)

        # Create a special row for the camera that will force it to remain in the center, regardless of size changes
        camRow = QtWidgets.QHBoxLayout()
        camRow.addStretch(1)
        camRow.addWidget(self.camera)
        camRow.addStretch(1)

        # Place the GUI objects vertically
        col1 = QtWidgets.QVBoxLayout()
        col1.addWidget(step2Lbl)
        col1.addWidget(promptLbl)
        col1.addStretch(1)
        col1.addLayout(camRow)
        col1.addStretch(1)

        mainHLayout = QtWidgets.QHBoxLayout()
        mainHLayout.addLayout(col1)

        self.setLayout(mainHLayout)

    def isComplete(self):
        print("ISCOMPLETE EVENT ACTIVATED!")
        frame = self.camera.getSelectedFrame()
        if frame is None: return False

        return True