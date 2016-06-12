from PyQt5              import QtCore, QtWidgets, QtGui
from RobotGUI           import Icons
from RobotGUI.CameraGUI import CameraWidget

class ObjectManager(QtWidgets.QDialog):

    def __init__(self, environment, parent):
        super(ObjectManager, self).__init__(parent)
        self.env                = environment
        self.cameraWidget       = CameraWidget(self.env.getVStream().getPixFrame)

        self.selectedObjVLayout = QtWidgets.QVBoxLayout()

        self.initUI()
        self.cameraWidget.play()

    def initUI(self):

        # CREATE OBJECTS AND LAYOUTS FOR ROW 1 COLUMN (ALL)
        createBtn   = QtWidgets.QPushButton("Create New")
        loadBtn     = QtWidgets.QPushButton("Load Existing")
        createBtn.setFixedWidth(130)
        loadBtn.setFixedWidth(130)



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





