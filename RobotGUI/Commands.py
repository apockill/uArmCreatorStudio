from PyQt4 import QtGui, QtCore

########## COMMAND LIST ##########
class CommandList(QtGui.QListWidget):
    def __init__(self):
        super(CommandList, self).__init__()
        #GLOBALS
        self.commands = {}  #Dictionary of commands. Ex: {QListItem: MoveXYZCommand, QListItem: PickupCommand}

        self.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setAcceptDrops(True)
        self.itemDoubleClicked.connect(self.doubleClickEvent)

        self.initUI()


    def initUI(self):
        self.setMaximumWidth(600)
        self.setMinimumWidth(250)

    def updateWidth(self):
        #Update the width of the commandList to the widest element within it
        if self.sizeHintForColumn(0) + 10 < 600:
            self.setMinimumWidth(self.sizeHintForColumn(0) + 10)

    def addCommand(self, type):
        #Called by the Main class when the addCommand button is pressed
        if type is MoveRSHCommand:
            newCommand = MoveRSHCommand()
            self.addNewItem(newCommand)

    def addNewItem(self, command):
        #Get information from user
        command.openView()  #Get information from user
        commandWidget = command.getCommandWidget()
        if commandWidget is None:
            return

        listWidgetItem = QtGui.QListWidgetItem(self)
        print listWidgetItem
        listWidgetItem.setSizeHint(commandWidget.sizeHint())
        self.addItem(listWidgetItem)
        self.setItemWidget(listWidgetItem, commandWidget)

        #Add the new command to the list of commands
        self.commands[listWidgetItem] = command

        #Update the width of the commandList to the widest element within it
        self.updateWidth()

# def dragEnterEvent(self, event):
#
#     super(CommandList, self).dragEnterEvent(event)

# def dragMoveEvent(self, event):
#
#     super(CommandList, self).dragMoveEvent(event)

    def dropEvent(self, event):
        event.setDropAction(QtCore.Qt.MoveAction)
        super(CommandList, self).dropEvent(event)
        lst = [i.text() for i in self.findItems("", QtCore.Qt.MatchContains)]

    def doubleClickEvent(self):
        #Open the command window for the command that was just double clicked

        selectedItem    = self.selectedItems()[0]
        selectedCommand = self.commands[selectedItem]

        selectedCommand.openView()
        updatedWidget = selectedCommand.getCommandWidget()
        self.setItemWidget(selectedItem, updatedWidget)
        self.updateWidth()

class CommandItem(QtGui.QWidget):
    def __init__(self, parent = None):
        super(CommandItem, self).__init__(parent)
        self.commandType        = QtGui.QLabel()
        self.commandDescription = QtGui.QLabel()

        font = QtGui.QFont()
        font.setBold(True)
        self.commandType.setFont(font)

        grid = QtGui.QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(self.commandType, 1, 0)
        grid.addWidget(self.commandDescription, 1, 1)

        # self.textQVBoxLayout.addWidget(self.textUpQLabel)
        # self.textQVBoxLayout.addWidget(self.textDownQLabel)
        # self.allQHBoxLayout.addWidget(self.iconQLabel, 0)
        # self.allQHBoxLayout.addLayout(self.textQVBoxLayout, 1)

        self.setLayout(grid)

    def setTextType(self, text):
        self.commandType.setText(text)

    def setTextDescription(self, text):
        self.commandDescription.setText(text)

class CommandWindow(QtGui.QDialog):
    def __init__(self):
        super(CommandWindow, self).__init__()

        self.parameters = {}  #Will be filled with parameters for the particular command
        self.accepted    = False
        self.mainVLayout = QtGui.QVBoxLayout()

        self.initBaseUI()

    def initBaseUI(self):
        #Create and connect buttons
        applyBtn  = QtGui.QPushButton('Apply', self)
        cancelBtn = QtGui.QPushButton('Cancel', self)
        applyBtn.setMaximumWidth(100)
        cancelBtn.setMaximumWidth(100)
        applyBtn.clicked.connect(self.applyClicked)
        cancelBtn.clicked.connect(self.cancelClicked)

        #Create layout
        grid = QtGui.QGridLayout()

        grid.setSpacing(10)

        grid.addLayout( self.mainVLayout, 0, 1, QtCore.Qt.AlignCenter)
        grid.addWidget( applyBtn, 1, 2, QtCore.Qt.AlignRight)
        grid.addWidget(cancelBtn, 1, 0, QtCore.Qt.AlignLeft)

        self.setLayout(grid)

    def applyClicked(self):
        self.accepted = True
        self.close()

    def cancelClicked(self):
        self.accepted = False
        self.close()

    def openView(self):  #Open window\
        #Run the info window and prevent other windows from being clicked while open:
        self.exec_()

        #See if the user pressed Ok or if he cancelled/exited out
        if self.accepted:
            #Get information that the user input
            newParameters = self.getInfo().copy()

            #  Add the new parameters to the dictionary, and update changed values
            self.parameters.update(newParameters)



            print "CommandWindow.openView(): New parameters: ", self.parameters

        else:
            print "CommandWindow.openView(): User Canceled."





########## COMMANDS ##########

class MoveRSHCommand(CommandWindow):
    def __init__(self):
        #super(MoveRSHCommand, self).__init__()
        CommandWindow.__init__(self)


        self.rotEdit     = QtGui.QLineEdit()
        self.strEdit     = QtGui.QLineEdit()
        self.hgtEdit     = QtGui.QLineEdit()

        self.initUI()

    def initUI(self):
        rot = QtGui.QLabel('Rotation:')
        str = QtGui.QLabel('Stretch:')
        hgt = QtGui.QLabel('Height:')
        self.rotEdit.setText("0")
        self.strEdit.setText("0")
        self.hgtEdit.setText("0")
        # self.rotEdit.setMaximumWidth(50)
        # self.strEdit.setMaximumWidth(50)
        # self.hgtEdit.setMaximumWidth(50)

        row1 = QtGui.QHBoxLayout()
        row2 = QtGui.QHBoxLayout()
        row3 = QtGui.QHBoxLayout()

        row1.addWidget(rot, QtCore.Qt.AlignRight)
        row1.addWidget(self.rotEdit)

        row2.addWidget(str, QtCore.Qt.AlignRight)
        row2.addWidget(self.strEdit)

        row3.addWidget(hgt, QtCore.Qt.AlignRight)
        row3.addWidget(self.hgtEdit)

        self.mainVLayout.addLayout(row1)
        self.mainVLayout.addLayout(row2)
        self.mainVLayout.addLayout(row3)

    def getInfo(self):
        #Build the info inputed into the window into a Json and return it. Used in parent class
        parameters = {"rot": str(self.rotEdit.text()),
                      "str": str(self.strEdit.text()),
                      "hgt": str(self.hgtEdit.text())}
        return parameters

    def getCommandWidget(self):
        #Verify that there are no None statements in the parameters
        if any(self.parameters) is None or self.parameters.__len__() == 0:#any(x is None for x in self.parameters.itervalues()):
            return None
        else:
            self.listWidget = CommandItem()
            self.listWidget.setTextType("Move RSH")
            self.listWidget.setTextDescription("Rotation: " + self.parameters["rot"] +
                                               " Stretch: " + self.parameters["str"] +
                                               " Height: "  + self.parameters["hgt"])
            return self.listWidget

    def runCommand(self):
        pass
