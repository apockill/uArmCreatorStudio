from PyQt4 import QtGui, QtCore
import cPickle as pickle


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

    def dropEvent(self, event):
        event.setDropAction(QtCore.Qt.MoveAction)
        super(CommandList, self).dropEvent(event)
        lst = [i.text() for i in self.findItems('', QtCore.Qt.MatchContains)]

    def doubleClickEvent(self):
        #Open the command window for the command that was just double clicked

        selectedItem    = self.selectedItems()[0]
        selectedCommand = self.commands[selectedItem]

        selectedCommand.openView()
        updatedWidget = selectedCommand.getCommandWidget()
        self.setItemWidget(selectedItem, updatedWidget)
        self.updateWidth()

    def saveList(self, file):
        list = []
        for index in xrange(self.count()):
            item = self.item(index)
            command = self.commands[item]
            list.append(command.parameters)
        pickle.dump( list, open( file, "wb" ))

    def loadList(self, file):
        list = pickle.load( open( file, "rb" ) )
        print list

    def runScript(self, robot):
        for index in xrange(self.count()):
            item = self.item(index)
            command = self.commands[item]
            command.run(robot)


class CommandItem(QtGui.QWidget):
    def __init__(self, parent = None):
        super(CommandItem, self).__init__(parent)
        self.title       = QtGui.QLabel()
        self.description = QtGui.QLabel()
        self.icon        = QtGui.QLabel("No icon found.")

        font = QtGui.QFont()
        font.setBold(True)
        self.title.setFont(font)

        leftLayout  = QtGui.QVBoxLayout()
        rightLayout = QtGui.QVBoxLayout()

        leftLayout.addWidget(self.icon)

        rightLayout.setSpacing(1)
        rightLayout.addWidget(self.title)
        rightLayout.addWidget(self.description)

        mainHLayout = QtGui.QHBoxLayout()
        mainHLayout.addLayout(leftLayout)
        mainHLayout.addLayout(rightLayout)
        # self.textQVBoxLayout.addWidget(self.textUpQLabel)
        # self.textQVBoxLayout.addWidget(self.textDownQLabel)
        # self.allQHBoxLayout.addWidget(self.iconQLabel, 0)
        # self.allQHBoxLayout.addLayout(self.textQVBoxLayout, 1)

        self.setLayout(mainHLayout)

    def setTitle(self, text):
        self.title.setText(text)

    def setDescription(self, text):
        self.description.setText(text)

    def setIcon(self, icon):
        self.icon.setPixmap(QtGui.QPixmap(icon))

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



            print 'CommandWindow.openView(): New parameters: ', self.parameters

        else:
            print 'CommandWindow.openView(): User Canceled.'





########## COMMANDS ##########

class MoveRSHCommand(CommandWindow):
    def __init__(self):
        #super(MoveRSHCommand, self).__init__()
        CommandWindow.__init__(self)

        self.rotEdit     = QtGui.QLineEdit()  #  Rotation textbox
        self.strEdit     = QtGui.QLineEdit()  #  Stretch textbox
        self.hgtEdit     = QtGui.QLineEdit()  #  Height textbox
        self.relCheck    = QtGui.QCheckBox()  #  "relative" CheckBox
        self.initUI()

    def initUI(self):
        #Set up all the labels for the inputs
        rot = QtGui.QLabel('Rotation:')
        str = QtGui.QLabel('Stretch:')
        hgt = QtGui.QLabel('Height:')
        rel = QtGui.QLabel('Relative')
        self.rotEdit.setText('0')
        self.strEdit.setText('0')
        self.hgtEdit.setText('0')
        # self.rotEdit.setMaximumWidth(50)
        # self.strEdit.setMaximumWidth(50)
        # self.hgtEdit.setMaximumWidth(50)

        row1 = QtGui.QHBoxLayout()
        row2 = QtGui.QHBoxLayout()
        row3 = QtGui.QHBoxLayout()
        row4 = QtGui.QHBoxLayout()

        row1.addWidget(rot, QtCore.Qt.AlignRight)
        row1.addWidget(self.rotEdit, QtCore.Qt.AlignJustify)

        row2.addWidget(str, QtCore.Qt.AlignRight)
        row2.addWidget(self.strEdit, QtCore.Qt.AlignJustify)

        row3.addWidget(hgt, QtCore.Qt.AlignRight)
        row3.addWidget(self.hgtEdit, QtCore.Qt.AlignJustify)

        row4.addWidget(rel, QtCore.Qt.AlignRight)
        row4.addWidget(self.relCheck, QtCore.Qt.AlignJustify)

        self.mainVLayout.addLayout(row1)
        self.mainVLayout.addLayout(row2)
        self.mainVLayout.addLayout(row3)
        self.mainVLayout.addLayout(row4)

    def getInfo(self):

        #Build the info inputed into the window into a Json and return it. Used in parent class
        parameters = {'rot': self.sanitizeInt(self.rotEdit.text()),
                      'str': self.sanitizeInt(self.strEdit.text()),
                      'hgt': self.sanitizeInt(self.hgtEdit.text()),
                      'rel': self.relCheck.isChecked()}
        return parameters

    def sanitizeInt(self, input):
        #Sanitize input from the user
            try:
                intInput = int(input)
            except:
                intInput = ""
            return intInput

    def getCommandWidget(self):
        #Verify that there are no None statements in the parameters
        if any(self.parameters) is None or self.parameters.__len__() == 0:#any(x is None for x in self.parameters.itervalues()):
            return None
        else:
            self.listWidget = CommandItem()
            self.listWidget.setIcon('Images/rsh_command.png')
            self.listWidget.setTitle('Move RSH')
            self.listWidget.setDescription('Rotation: ' + str(self.parameters['rot']) +
                                               '   Stretch: ' + str(self.parameters['str']) +
                                               '   Height: '  + str(self.parameters['hgt']) +
                                               '   Relative: ' + str(self.parameters['rel']))
            return self.listWidget

    def run(self, robot):
        robot.moveTo(rotation=self.parameters['rot'],
                     stretch=self.parameters['str'],
                     height=self.parameters['hgt'],
                     relative=self.parameters['rel'],
                     waitForRobot=True)








