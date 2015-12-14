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

    def addCommand(self, type):
        #Called by the Main class when the addCommand button is pressed
        if type == "moveXYZ":
            newCommand = BasicCommand(type)
            self.addNewItem(newCommand)

        self.setMinimumWidth(self.sizeHintForColumn(0) + 10)

    def addNewItem(self, command):
        #Get information from user
        command.openView()  #Get information from user
        commandWidget = command.getCommandWidget()
        if commandWidget == None:  #If the user pressed cancel
            return



        listWidgetItem = QtGui.QListWidgetItem(self)
        listWidgetItem.setSizeHint(commandWidget.sizeHint())
        self.addItem(listWidgetItem)
        self.setItemWidget(listWidgetItem, commandWidget)

        self.commands[listWidgetItem] = command

    def dragEnterEvent(self, event):
        # if event.mimeData().hasUrls():
        #     event.accept()
        # else:
        super(CommandList, self).dragEnterEvent(event)

    def dragMoveEvent(self, event):
        # if event.mimeData().hasUrls():
        #     event.setDropAction(QtCore.Qt.CopyAction)
        #     event.accept()
        # else:
        super(CommandList, self).dragMoveEvent(event)

    def dropEvent(self, event):
        #print 'dropEvent', event
        # if event.mimeData().hasUrls():
        #     event.setDropAction(QtCore.Qt.CopyAction)
        #     event.accept()
        #     links = []
        #     for url in event.mimeData().urls():
        #         links.append(str(url.toLocalFile()))
        #     self.emit(QtCore.SIGNAL("dropped"), links)
        # else:
        event.setDropAction(QtCore.Qt.MoveAction)
        super(CommandList, self).dropEvent(event)
        lst = [i.text() for i in self.findItems("", QtCore.Qt.MatchContains)]

        for i in range(self.count()):
            print self.item(i), self.item(i).text()
            self.commands[self.item(i)].test()
            #QtGui.QListWidgetItem.data(0)


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


########## COMMANDS ##########
"""
Brainstorming types of commands:
    -Move XYZ command (cartesian)
    -Move RSH command (polar)

    -Focus Circle command (Vision)
    -Focus Square command (Vision)
    -Focus Memorized command (Vision)

    -Pickup -- Command (Vision

"""
class MoveXYZCommand():
    def __init__(self):
        self.commandType   = "Move XYZ"
        self.commandWidget = None
        self.rot = None
        self.str = None
        self.hgt = None

    def openView(self):
        self.dialog = MoveXYZView()

        #Prevent any other window from being clicked while this is open:
        self.dialog.exec_()

        #See if the user pressed Ok or if he cancelled/exited out
        if self.dialog.accepted:
            #Get information that the user input
            self.rot, self.str, self.hgt = self.dialog.getInfo()
            print "rot: ", self.rot, "str: ", self.str, "hgt: ", self.hgt
        else:
            print "MoveXYZCommand().openView(): User Canceled."

    def getCommandWidget(self):
        if self.rot is None or self.str is None or self.hgt is None:
            return None
        else:
            self.listWidget = CommandItem()
            self.listWidget.setTextType(self.commandType)
            self.listWidget.setTextDescription("Rotation: " + str(self.rot) + " Stretch: " + str(self.str) + " Height: " + str(self.hgt))
            return self.listWidget



class BasicCommand():
    def __init__(self, commandType):
        #Commandtype is a string, like "moveXYZ" or "pickupObject"

        self.commandWidget     = None
        self.parameters = {"type": commandType}  #Will be filled with parameters
        self.dialog = MoveXYZView()
        # self.rot = None
        # self.str = None
        # self.hgt = None

    def openView(self):
        #Actually execute the dialogview, and also prevent
        #any other window from being clicked while this is open:
        self.dialog.exec_()

        #See if the user pressed Ok or if he cancelled/exited out
        if self.dialog.accepted:
            #Get information that the user input
            newParameters = self.dialog.getInfo()

            # newParameters.update(self.commandParameters.copy())
            # self.commandParameters = newParameters.copy()
            #self.commandParameters.update(newParameters)

            #  Add the new parameters to the dictionary
            self.parameters = dict(newParameters.items() + self.parameters.items())

            print self.parameters
        else:
            print "MoveXYZCommand().openView(): User Canceled."

    def getCommandWidget(self):
        #Verify that there are no None statements in the parameters
        if any(x is None for x in self.parameters.itervalues()):
            return None
        else:
            self.listWidget = CommandItem()
            self.listWidget.setTextType(self.parameters["type"])
            self.listWidget.setTextDescription("Rotation: " + self.parameters["rot"] +
                                               " Stretch: " + self.parameters["str"] +
                                               " Height: " + self.parameters["hgt"])
            print "lol"
            return self.listWidget

    def test(self):
        print self.parameters


class MoveXYZView(QtGui.QDialog):
    def __init__(self):
        super(MoveXYZView, self).__init__()

        self.accepted    = False
        self.mainVLayout = QtGui.QVBoxLayout()

        self.rotEdit     = QtGui.QLineEdit()
        self.strEdit     = QtGui.QLineEdit()
        self.hgtEdit     = QtGui.QLineEdit()


        self.initUI()

    def initUI(self):
        applyBtn = QtGui.QPushButton('Apply', self)
        applyBtn.setMaximumWidth(100)
        cancelBtn = QtGui.QPushButton('Cancel', self)
        cancelBtn.setMaximumWidth(100)


        rot = QtGui.QLabel('Rotation: ')
        str = QtGui.QLabel('Stretch: ')
        hgt = QtGui.QLabel('Height: ')
        self.rotEdit.setText("0")
        self.strEdit.setText("0")
        self.hgtEdit.setText("0")



        grid = QtGui.QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(         rot, 1, 0)
        grid.addWidget(self.rotEdit, 1, 1)

        grid.addWidget(         str, 2, 0)
        grid.addWidget(self.strEdit, 2, 1)

        grid.addWidget(         hgt, 3, 0)
        grid.addWidget(self.hgtEdit, 3, 1)

        grid.addWidget(applyBtn, 4, 1, QtCore.Qt.AlignRight)
        grid.addWidget(cancelBtn, 4, 0, QtCore.Qt.AlignLeft)

        #self.setGeometry(300, 300, 350, 300)
        self.setWindowTitle("XYZ Command")
        self.setLayout(grid)

        applyBtn.clicked.connect(self.applyClicked)
        cancelBtn.clicked.connect(self.cancelClicked)

    def applyClicked(self):
        self.accepted = True
        self.close()

    def cancelClicked(self):
        self.accepted = False
        self.close()

    def getInfo(self):
        parameters = {"rot": str(self.rotEdit.text()), "str": str(self.strEdit.text()), "hgt": str(self.hgtEdit.text())}

        return parameters
