from PyQt4 import QtGui, QtCore
from threading import Thread
from time import sleep
import Icons
import cPickle as pickle



class ControlPanel(QtGui.QWidget):
    def __init__(self):
        super(ControlPanel, self).__init__()
        self.eventList     = EventList(self.refresh)

        self.addEventBtn   = QtGui.QPushButton()
        self.addCommandBtn = QtGui.QPushButton()

        self.commandListStack  = QtGui.QStackedWidget()   #Until something is selected first, there will be no commandListStack

        self.initUI()

        self.addEventBtn.clicked.connect(self.addEvent)
        self.addCommandBtn.clicked.connect(self.addCommand)

    def initUI(self):
        self.addCommandBtn.setText("Add Command")
        self.addEventBtn.setText("Add Event")

        eventVLayout   = QtGui.QVBoxLayout()
        eventVLayout.addWidget(self.addEventBtn)
        eventVLayout.addWidget(self.eventList)



        commandVLayout = QtGui.QVBoxLayout()
        commandVLayout.addWidget(self.addCommandBtn)
        commandVLayout.addWidget(self.commandListStack)
        self.commandListStack.addWidget(CommandList())  #Add a placeholder commandList

        mainHLayout   = QtGui.QHBoxLayout()
        mainHLayout.addLayout(eventVLayout)
        mainHLayout.addLayout(commandVLayout)

        self.setLayout(mainHLayout)
        self.show()

    def refresh(self):
        print "ControlPanel.refresh(): Refreshing widget!"

        selectedEvent = self.eventList.getSelectedEvent()
        if selectedEvent is None:
            print "ControlPanel.refresh(): ERROR: no event selected!"
            return

        # for c in range(0, self.commandListStack.count()):
        #     print self.commandListStack.widget(c).commands

        #Add command widget if it does not exist, or ignore it if it already does
        self.commandListStack.addWidget(selectedEvent.commandList)

        #Display the currently selected event
        self.commandListStack.setCurrentWidget(selectedEvent.commandList)


    def addCommand(self):
        selectedEvent = self.eventList.getSelectedEvent()
        if selectedEvent is None:
            #This occurs when there are no events on the table. Display warning to user in this case.
            print "ControlPanel.addCommand():\t ERROR: Selected event does not have a commandList! Displaying error"
            QtGui.QMessageBox.question(self, 'Error', 'You need to select an event or add '
                                       'an event before you can add commands', QtGui.QMessageBox.Ok)
            return

        selectedEvent.commandList.addCommand(MoveXYZCommand)

    def addEvent(self):
        self.eventList.promptUser()


    def getSaveData(self):
        pass

    def loadData(self, data):
        pass


    def closeEvent(self, event):
        self.eventList.endThread()


########## EVENT LIST ##########
class EventList(QtGui.QListWidget):
    def __init__(self, refresh):
        super(EventList, self).__init__()
        #GLOBALS
        self.refresh = refresh
        self.exitApp = False
        self.mainThread = None
        self.events = {}  #A hash map of the current events in the list. The listWidget leads to the event object

        self.itemSelectionChanged.connect(self.refresh)

        self.initUI()

    def initUI(self):
        self.setFixedWidth(200)
        # self.setMaximumWidth(600)
        # self.setMinimumWidth(250)


    def getSelectedEvent(self):
        selected = self.selectedItems()

        #Error check
        if len(selected) == 0 or len(selected) > 1:
            print "EventList.getSelected(): ERROR: ", len(selected), "events selected"
            return None
        selected = selected[0]

        #Get the corresponding event
        return self.events[selected]

    def promptUser(self):
        eventPrompt = EventWindow()
        if eventPrompt.accepted:
            self.addEvent(eventPrompt.chosenEvent)
        else:
            print "EventList.promptUser(): User rejected the prompt."

    def addEvent(self, eventType):
        #Check if the event being added already exists in the self.events dictionary
        if any((isinstance(x, eventType)) for x in self.events.itervalues()):
            print "EventList.addEvent():\t Event already exists, disregarding user input."
            return


        #Create the widget and list item to visualize the event
        newEvent = eventType()
        newEvent.commandList = CommandList()

        eventWidget = newEvent.getWidget()
        listWidgetItem = QtGui.QListWidgetItem(self)
        listWidgetItem.setSizeHint(eventWidget.sizeHint())   #Widget will not appear without this line
        self.addItem(listWidgetItem)

        #Add the widget to the list item
        self.setItemWidget(listWidgetItem, eventWidget)

        self.events[listWidgetItem] = newEvent


        self.setCurrentRow(self.count() - 1)  #Select the newly added event
        self.refresh()                        #Call for a refresh of the ControlPanel so it shows the commandList


    def startThread(self, mainWindow, robot):
        if self.mainThread is None:
            self.mainThread = Thread(target=lambda: self.programThread(mainWindow, robot))
            self.mainThread.start()
        else:
            print "EventList.startThread(): ERROR: Tried to create mainThread, but mainThread already existed."

    def endThread(self):
        self.exitApp = True

        if self.mainThread is not None:
            self.mainThread.join(1000)
            self.mainThread = None


    def programThread(self, mainWindow, robot):
        while not self.exitApp:
            print "running thread still"
            sleep(1)

    def updateCommands(self):
        pass

class EventWidget(QtGui.QWidget):
    def __init__(self, parent = None):
        super(EventWidget, self).__init__(parent)
        self.title       = QtGui.QLabel()
        self.icon        = QtGui.QLabel("No icon found.")
        self.initUI()

    def initUI(self):
        # self.setGeometry(10, 10, 10, 10)
        # self.icon.setGeometry(10,10, 10, 10)
        #self.icon.setFixedWidth(15)


        font = QtGui.QFont()
        font.setBold(True)
        self.title.setFont(font)

        # leftLayout  = QtGui.QVBoxLayout()
        # rightLayout = QtGui.QVBoxLayout()

        mainHLayout = QtGui.QHBoxLayout()
        mainHLayout.addWidget(self.icon)
        mainHLayout.addWidget(self.title, QtCore.Qt.AlignLeft)

        # self.textQVBoxLayout.addWidget(self.textUpQLabel)
        # self.textQVBoxLayout.addWidget(self.textDownQLabel)
        # self.allQHBoxLayout.addWidget(self.iconQLabel, 0)
        # self.allQHBoxLayout.addLayout(self.textQVBoxLayout, 1)
        #self.setFixedHeight(25)
        self.setLayout(mainHLayout)

    def setTitle(self, text):
        self.title.setText(text)

    def setIcon(self, icon):
        self.icon.setPixmap(QtGui.QPixmap(icon))

class EventWindow(QtGui.QDialog):
    def __init__(self):
        super(EventWindow, self).__init__()
        self.accepted    = False
        self.chosenEvent = None  #What event the user chose to add (changed in btnClicked() function)
        self.initUI()

    def initUI(self):
        self.initButtons()
        self.initButtonMenus()

        #Create grid layout
        grid = QtGui.QGridLayout()

        grid.addWidget(      self.initBtn, 0, 0, QtCore.Qt.AlignLeft)
        grid.addWidget( self.keyboardBtn, 0, 1, QtCore.Qt.AlignLeft)
        grid.addWidget(      self.stepBtn, 1, 0, QtCore.Qt.AlignLeft)
        grid.addWidget( self.intersectBtn, 1, 1, QtCore.Qt.AlignLeft)


        #Set up Cancel button in it's own layout:
        cancelLayout = QtGui.QHBoxLayout()
        cancelLayout.addWidget(self.cancelBtn)


        #Create main layout
        mainVLayout = QtGui.QVBoxLayout()
        mainVLayout.addLayout(grid)
        mainVLayout.addLayout(cancelLayout, QtCore.Qt.AlignHCenter)


        #Finalize everything
        self.setLayout(mainVLayout)
        #self.setFixedWidth(250)
        #self.setFixedHeight(350)
        self.setWindowTitle('Add an Event')
        #self.show()
        self.exec_()  #Open self, and prevent anyone clicking on other windows

    def initButtons(self):
        buttonWidth = 115

        #Create widgets
        self.initBtn      = QtGui.QPushButton('Initialization')
        self.keyboardBtn  = QtGui.QPushButton('Keyboard')
        self.stepBtn      = QtGui.QPushButton('Step')
        self.intersectBtn = QtGui.QPushButton('Intersect')
        self.cancelBtn    = QtGui.QPushButton('Cancel')

        self.initBtn      .setStyleSheet("Text-align:left")
        self.keyboardBtn  .setStyleSheet("Text-align:left")
        self.stepBtn      .setStyleSheet("Text-align:left")
        self.intersectBtn .setStyleSheet("Text-align:left")
        self.initBtn      .setStyleSheet("Text-align:left")

        self.initBtn      .setFixedWidth(buttonWidth)
        self.keyboardBtn  .setFixedWidth(buttonWidth)
        self.stepBtn      .setFixedWidth(buttonWidth)
        self.intersectBtn .setFixedWidth(buttonWidth)
        self.cancelBtn    .setFixedWidth(buttonWidth * 1.5)
        self.cancelBtn    .setFixedHeight(25)

        self.initBtn      .setIcon(QtGui.QIcon(Icons.creation_event))
        self.keyboardBtn  .setIcon(QtGui.QIcon(Icons.keyboard_event))
        self.stepBtn      .setIcon(QtGui.QIcon(Icons.step_event))
        self.intersectBtn .setIcon(QtGui.QIcon(Icons.intersect_event))
        self.cancelBtn    .setIcon(QtGui.QIcon(Icons.cancel))

        #CONNECT BUTTONS THAT DON'T HAVE MENUS
        self.initBtn      .clicked.connect(lambda: self.btnClicked(InitEvent))
        self.stepBtn      .clicked.connect(lambda: self.btnClicked(StepEvent))
        self.cancelBtn    .clicked.connect(self.cancelClicked)

    def initButtonMenus(self):
        """
        initBtn         NO menu
        keyboardBtn     Has menu
        stepBtn         Has menu
        intersectBtn    Has menu
        cancelBtn       NO menu
        :return:
        """
        #Set up Menus for buttons that have menus:

        #KEYBOARD MENU
        keyboardMnu = QtGui.QMenu()
        keyboardMnu.addAction(   '<Up>', lambda: self.btnClicked('Up Clicked'))
        keyboardMnu.addAction( '<Down>', lambda: self.btnClicked('Down Clicked'))
        keyboardMnu.addAction( '<Left>', lambda: self.btnClicked('Left Clicked'))
        keyboardMnu.addAction('<Right>', lambda: self.btnClicked('Right Clicked'))

            #Create Letters Sub Menu
        self.lettersSubMnu = QtGui.QMenu("Letters")  #Has to be self or else doesn't work. Don't know why...
        alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I','J', 'K', 'L', 'M',
                    'N', 'O', 'P', 'Q','R', 'S', 'T', 'U', 'V', 'X', 'Y', 'Z']
        for letter in alphabet:
            #About the lambda letter=letter:. I don't know why it fixes the problem, but it does. Here's a better
            #Explanation: http://stackoverflow.com/questions/4578861/connecting-slots-and-signals-in-pyqt4-in-a-loop
            self.lettersSubMnu.addAction(letter, lambda letter=letter: self.btnClicked(letter))

            #Create Digits Sub Menu
        self.digitsSubMnu = QtGui.QMenu("Digits")  #Has to be self or else doesn't work. Don't know why...
        digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        for index, digit in enumerate(digits):
            self.digitsSubMnu.addAction(digit, lambda digit=digit: self.btnClicked(digit))

            #Add Sub Menus
        keyboardMnu.addMenu(self.lettersSubMnu)
        keyboardMnu.addMenu(self.digitsSubMnu)
        self.keyboardBtn.setMenu(keyboardMnu)


        #INTERSECT MENU
        intersectMnu = QtGui.QMenu()
        intersectMnu.addAction('Intersect +X Boundary', lambda: self.btnClicked("+X"))
        intersectMnu.addAction('Intersect -X Boundary', lambda: self.btnClicked("-X"))
        intersectMnu.addAction('Intersect  X Boundary', lambda: self.btnClicked("X"))
        intersectMnu.addAction('Intersect +Y Boundary', lambda: self.btnClicked("+Y"))
        intersectMnu.addAction('Intersect -Y Boundary', lambda: self.btnClicked("-Y"))
        intersectMnu.addAction('Intersect  Y Boundary', lambda: self.btnClicked("Y"))
        self.intersectBtn.setMenu(intersectMnu)

    def btnClicked(self, eventType):
        print "EventWindow.buttonSelected():\t Event Type ", eventType, "selected"
        self.chosenEvent = eventType
        self.accepted = True
        self.close()

    def cancelClicked(self, event):
        self.close()

    def setTitle(self, text):
        self.title.setText(text)

    def setDescription(self, text):
        self.description.setText(text)

    def setIcon(self, icon):
        self.icon.setPixmap(QtGui.QPixmap(icon))




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
        #self.setMaximumWidth(600)
        self.setMinimumWidth(250)

    def updateWidth(self):
        #Update the width of the commandList to the widest element within it
        if self.sizeHintForColumn(0) + 10 < 600:
            self.setMinimumWidth(self.sizeHintForColumn(0) + 10)


    def addCommand(self, type, **kwargs):
        #If adding a pre-filled command (used when loading a save)
        parameters = kwargs.get("parameters", None)
        if parameters is None:
            newCommand = type()
        else:
            newCommand = type(parameters=parameters)


        #Fill command with information either by opening window or loading it in
        if parameters is None:
            newCommand.openView()  #Get information from user
            if not newCommand.accepted:
                print "CommandList.addCommand(): User rejected prompt"
                return
        else:
            newCommand.parameters = parameters



        #Create the list widget to visualize the widget
        commandWidget = newCommand.getWidget()

        listWidgetItem = QtGui.QListWidgetItem(self)
        listWidgetItem.setSizeHint(commandWidget.sizeHint())  #Widget will not appear without this line
        self.addItem(listWidgetItem)

        #Add list widget to commandList
        self.setItemWidget(listWidgetItem, commandWidget)

        #Add the new command to the list of commands, linking it with its corresponding listWidgetItem
        self.commands[listWidgetItem] = newCommand

        #Update the width of the commandList to the widest element within it
        self.updateWidth()


    def keyPressEvent(self, event):
        #modifiers = QtGui.QApplication.keyboardModifiers()

        #Delete selected items when delete key is pressed
        if event.key() == QtCore.Qt.Key_Delete:
            for item in self.selectedItems():
                del self.commands[item]
                self.takeItem(self.row(item))

    def dropEvent(self, event):
        event.setDropAction(QtCore.Qt.MoveAction)
        super(CommandList, self).dropEvent(event)
        lst = [i.text() for i in self.findItems('', QtCore.Qt.MatchContains)]

    def doubleClickEvent(self):
        #Open the command window for the command that was just double clicked

        selectedItem    = self.selectedItems()[0]
        selectedCommand = self.commands[selectedItem]

        selectedCommand.openView()
        updatedWidget = selectedCommand.getWidget()
        self.setItemWidget(selectedItem, updatedWidget)
        self.updateWidth()


    def getSaveData(self):
        commandList = []
        for index in xrange(self.count()):
            item = self.item(index)
            command = self.commands[item]
            commandList.append(command.parameters)
        return commandList

    def loadData(self, data):
        #Clear all data on the current list
        self.commands = {}
        self.clear()

        #Fill the list with new data
        for index, parameters in enumerate(data):
            self.addCommand(parameters["type"], parameters=parameters)

class CommandWidget(QtGui.QWidget):
    def __init__(self, parent = None):
        super(CommandWidget, self).__init__(parent)
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
        mainHLayout.addLayout(rightLayout, QtCore.Qt.AlignLeft)
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




########## EVENTS ##########
class Event():
    def __init__(self):
        self.commandList = None

class InitEvent(Event):
    def __init__(self):
        Event.__init__(self)
        self.hasBeenRun = False

    def getWidget(self):
        listWidget = EventWidget()
        listWidget.setIcon(Icons.creation_event)
        listWidget.setTitle('Initialization')

        return listWidget

    def isActive(self):
        #Returns true or false if this event should be activated

        if self.hasBeenRun:
            return False
        else:
            self.hasBeenRun = True
            return True

class StepEvent(Event):
    def __init__(self):
        Event.__init__(self)

    def getWidget(self):
        listWidget = EventWidget()
        listWidget.setIcon(Icons.step_event)
        listWidget.setTitle('Step')

        return listWidget

    def isActive(self):
        #Since this is a "step" event, it will run each time the events are checked
        return True


########## COMMANDS ##########
class Command(QtGui.QDialog):
    def __init__(self):
        super(Command, self).__init__()
        #self.parameters = {}  #Will be filled with parameters for the particular command
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
        self.setWindowTitle(self.title)

    def applyClicked(self):
        self.accepted = True
        self.close()

    def cancelClicked(self):
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

class MoveXYZCommand(Command):
    def __init__(self, **kwargs):
        self.title       = "Move XYZ"

        Command.__init__(self)

        #Set default parameters that will show up on the window
        self.parameters = kwargs.get("parameters",
                           {'type': type(self),
                            'x': 0,
                            'y': 0,
                            'z': 0,
                            'rel': False})

        self.rotEdit     = QtGui.QLineEdit()  #  Rotation textbox
        self.strEdit     = QtGui.QLineEdit()  #  Stretch textbox
        self.hgtEdit     = QtGui.QLineEdit()  #  Height textbox
        self.relCheck    = QtGui.QCheckBox()  #  "relative" CheckBox
        self.initUI()

    def initUI(self):
        #Set up all the labels for the inputs
        rotLabel = QtGui.QLabel('X:')
        strLabel = QtGui.QLabel('Y:')
        hgtLabel = QtGui.QLabel('Z:')
        relLabel = QtGui.QLabel('Relative')

        #Fill the textboxes with the default parameters
        self.rotEdit.setText(str(self.parameters['x']))
        self.strEdit.setText(str(self.parameters['y']))
        self.hgtEdit.setText(str(self.parameters['z']))
        self.relCheck.setChecked(self.parameters['rel'])


        row1 = QtGui.QHBoxLayout()
        row2 = QtGui.QHBoxLayout()
        row3 = QtGui.QHBoxLayout()
        row4 = QtGui.QHBoxLayout()

        row1.addWidget(rotLabel, QtCore.Qt.AlignRight)
        row1.addWidget(self.rotEdit, QtCore.Qt.AlignJustify)

        row2.addWidget(strLabel, QtCore.Qt.AlignRight)
        row2.addWidget(self.strEdit, QtCore.Qt.AlignJustify)

        row3.addWidget(hgtLabel, QtCore.Qt.AlignRight)
        row3.addWidget(self.hgtEdit, QtCore.Qt.AlignJustify)

        row4.addWidget(relLabel, QtCore.Qt.AlignRight)
        row4.addWidget(self.relCheck, QtCore.Qt.AlignJustify)

        self.mainVLayout.addLayout(row1)
        self.mainVLayout.addLayout(row2)
        self.mainVLayout.addLayout(row3)
        self.mainVLayout.addLayout(row4)

    def getInfo(self):
        #Build the info inputed into the window into a Json and return it. Used in parent class

        newParameters = {'x': self.sanitizeFloat(self.rotEdit.text(), self.parameters["x"]),
                         'y': self.sanitizeFloat(self.strEdit.text(), self.parameters["y"]),
                         'z': self.sanitizeFloat(self.hgtEdit.text(), self.parameters["z"]),
                         'rel': self.relCheck.isChecked()}

        return newParameters

    def sanitizeFloat(self, input, fallback):
        #Sanitize input from the user
            try:
                intInput = float(input)
            except:
                intInput = fallback
            return intInput

    def getWidget(self):
        #Verify that there are no None statements in the parameters
        if any(self.parameters) is None or self.parameters.__len__() == 0:#any(x is None for x in self.parameters.itervalues()):
            return None
        else:
            listWidget = CommandWidget()
            listWidget.setIcon(Icons.xyz_command)
            listWidget.setTitle(self.title)
            listWidget.setDescription('X: '    + str(self.parameters['x']) +
                                           '   Y: ' + str(self.parameters['y']) +
                                           '   Z: ' + str(self.parameters['z']) +
                                           '   Relative: ' + str(self.parameters['rel']))
            return listWidget

    def run(self, robot):
        robot.setPos(x=self.parameters['x'],
                     y=self.parameters['y'],
                     z=self.parameters['z'],
                     relative=self.parameters['rel'],
                     waitForRobot=True)
        robot.sendPos()








