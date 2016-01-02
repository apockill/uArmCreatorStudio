from PyQt4     import QtGui, QtCore
from threading import Thread
import copy
import time
import Icons
import Global




class ControlPanel(QtGui.QWidget):
    """
    ControlPanel:

    Purpose: A nice clean widget that has both the EventList and CommandList displayed, and the "AddEvent" and
            "AddCommand" buttons. It is a higher level of abstraction for the purpose of handling the running of the
            robot program, instead of the nitty gritty details of the commandList and eventList
    """
    def __init__(self):
        super(ControlPanel, self).__init__()

        #Set up Globals
        self.eventList         = EventList(self.refresh)
        self.running           = False                    #Whether or not the main thread should be running or not
        self.mainThread        = None                     #This holds the 'Thread' object of the main thread.
        self.addEventBtn       = QtGui.QPushButton()
        self.addCommandBtn     = QtGui.QPushButton()
        self.commandListStack  = QtGui.QStackedWidget()   #Until something is selected first, there will be no commandListStack

        self.initUI()

        #Connect Events
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
        #Refresh which commandList is currently being displayed to the one the user has highlighted
        print "ControlPanel.refresh(): Refreshing widget!"
        #Get the currently selected event on the eventList
        selectedEvent = self.eventList.getSelectedEvent()


        #Delete all widgets on the commandList stack
        for c in range(0, self.commandListStack.count()):
            widget = self.commandListStack.widget(c)
            self.commandListStack.removeWidget(widget)

        #If user has no event selected, make a clear commandList to view
        if selectedEvent is None:
            print "ControlPanel.refresh(): ERROR: no event selected!"
            clearList = CommandList()
            self.commandListStack.addWidget(clearList)
            self.commandListStack.setCurrentWidget(clearList)
            return

        #Add and display the correct widget
        self.commandListStack.addWidget(selectedEvent.commandList)
        self.commandListStack.setCurrentWidget(selectedEvent.commandList)



    def startThread(self):
        #Start the program thread
        if self.mainThread is None:
            self.running = True
            self.mainThread = Thread(target=self.programThread)
            self.mainThread.start()
        else:
            print "ControlPanel.startThread():\t ERROR: Tried to run programthread, but there was one already running!"

    def endThread(self):
        #Close the program thread and wrap up loose ends
        print "ControlPanel.endThread():\t Closing program thread."
        self.running = False

        if self.mainThread is not None:
            self.mainThread.join(1000)
            self.mainThread = None

    def programThread(self):
        #This is where the script will be run

        print "ControlPanel.programThread(): #################### STARTING PROGRAM THREAD! ######################"
        millis         = lambda: int(round(time.time() * 1000))
        readyForNext   = lambda lastMillis: millis() - lastMillis >= (1 / float(stepsPerSecond)) * 1000
        stepsPerSecond = 1
        lastMillis     = millis()

        #Deepcopy all of the events, so that every time you run the script it runs with no modified variables
        events = copy.deepcopy(self.eventList.getEventsOrdered())


        while self.running:

            #Wait till it's time for a new step
            if not readyForNext(lastMillis): continue
            lastMillis = millis()

            print "\n\nControlPanel.programThread():   ########## PERFORMING    ALL    EVENTS ##########"
            #Check all events and tell them to run their commands when appropriate
            for event in events:

                if event.isActive():
                    event.runCommands()
                    print "\n"

            #Only "Render" the robots movement once per step
            Global.robot.refresh()

        #Re-lock the servos on the robot
        Global.robot.setPos(**Global.robot.home)
        Global.robot.setServos(servo1=True, servo2=True, servo3=True, servo4=True)
        Global.robot.refresh()



    def addCommand(self):
        #When the addCommand button is pressed
        print "ControlPanel.addCommand():\t Add Command button clicked. Adding command!"

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
        return self.eventList.getSaveData()

    def loadData(self, data):
        self.eventList.loadData(data)
        #self.refresh()


    def closeEvent(self, event):
        #Do things here like closing threads and such
        self.endThread()




########## EVENT LIST ##########
class EventList(QtGui.QListWidget):
    def __init__(self, refresh):
        super(EventList, self).__init__()
        #GLOBALS
        self.refreshControlPanel = refresh
        self.events = {}  #A hash map of the current events in the list. The listWidget leads to the event object

        #IMPORTANT This makes sure the ControlPanel refreshes whenever you click on an item in the list,
        #in order to display the correct commandList for the event that was clicked on.
        self.itemSelectionChanged.connect(self.refreshControlPanel)

        #The following is a function that returns a dictionary of the events, in the correct order
        self.getEventsOrdered = lambda: [self.events[self.item(index)] for index in xrange(self.count())]

        self.initUI()

    def initUI(self):
        self.setFixedWidth(200)



    def getSelectedEvent(self):
        """
        This method returns the Event() class for the currently clicked-on event.
        This is used for displaying the correct commandList, or adding a command
        to the correct event.
        """
        selected = self.selectedItems()

        #Make sure there is only one item selected
        if len(selected) == 0 or len(selected) > 1:
            print "EventList.getSelected(): ERROR: ", len(selected), "events selected"
            return None
        selected = selected[0]

        #Get the corresponding event
        return self.events[selected]

    def promptUser(self):
        #Open the eventPromptWindow to ask the user what event they wish to create
        eventPrompt = EventPromptWindow()
        if eventPrompt.accepted:
            self.addEvent(eventPrompt.chosenEvent, parameters=eventPrompt.chosenParameters)
        else:
            print "EventList.promptUser(): User rejected the prompt."

    def addEvent(self, eventType, **kwargs):
        params = kwargs.get("parameters", None)


        #Check if the event being added already exists in the self.events dictionary
        for x in self.events.itervalues():
            if isinstance(x, eventType) and (x.parameters == params or params is None):

                print "EventList.addEvent():\t Event already exists, disregarding user input."
                return

        # if any((isinstance(x, eventType) and x.parameters == params) for x in self.events.itervalues()):
        #     print "EventList.addEvent():\t Event already exists, disregarding user input."
        #     return


        #Check if the event has specific parameters (Such as a KeyPressEvent that specifies A must be the key pressed)
        if params is None or params == {}:
            newEvent = eventType()
        else:
            print "adding params", params
            newEvent = eventType(params)


        newEvent.commandList = kwargs.get("commandList", CommandList())

        #Create the widget and list item to visualize the event
        eventWidget = newEvent.getWidget()
        listWidgetItem = QtGui.QListWidgetItem(self)
        listWidgetItem.setSizeHint(eventWidget.sizeHint())   #Widget will not appear without this line
        self.addItem(listWidgetItem)

        #Add the widget to the list item
        self.setItemWidget(listWidgetItem, eventWidget)

        self.events[listWidgetItem] = newEvent


        self.setCurrentRow(self.count() - 1)  #Select the newly added event
        self.refreshControlPanel()            #Call for a refresh of the ControlPanel so it shows the commandList


    def getSaveData(self):
        eventList = []
        eventsOrdered = self.getEventsOrdered()

        for event in eventsOrdered:
            eventSave = {}
            eventSave["type"] = type(event)
            eventSave["parameters"] = event.parameters
            eventSave["commandList"] = event.commandList.getSaveData()

            eventList.append(eventSave)

        return eventList

    def loadData(self, data):
        self.events = {}
        self.clear()  #clear eventList

        #Fill event list with new data
        for index, eventSave in enumerate(data):
            commandList = CommandList()
            commandList.loadData(eventSave['commandList'])

            self.addEvent(eventSave['type'], commandList=commandList, parameters=eventSave["parameters"])

        #Select the first event for viewing
        if self.count() > 0: self.setCurrentRow(0)


class EventWidget(QtGui.QWidget):
    """
    This is the widget that appears on the EventList.
    It's supposed to be prettier than the normal list items.
    """
    def __init__(self, parent = None):
        super(EventWidget, self).__init__(parent)
        self.title       = QtGui.QLabel()
        self.icon        = QtGui.QLabel("No icon found.")
        self.initUI()

    def initUI(self):
        font = QtGui.QFont()
        font.setBold(True)
        self.title.setFont(font)

        mainHLayout = QtGui.QHBoxLayout()
        mainHLayout.addWidget(self.icon)
        mainHLayout.addWidget(self.title, QtCore.Qt.AlignLeft)

        self.setLayout(mainHLayout)

    def setTitle(self, text):
        self.title.setText(text)

    def setIcon(self, icon):
        self.icon.setPixmap(QtGui.QPixmap(icon))


class EventPromptWindow(QtGui.QDialog):
    def __init__(self):
        super(EventPromptWindow, self).__init__()
        self.accepted         = False
        self.chosenEvent      = None  #What event the user chose to add (changed in btnClicked() function)
        self.chosenParameters = None
        self.initUI()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.exec_()  #Open self, and prevent anyone clicking on other windows


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
        self.setFixedSize(self.sizeHint())  #Make the window a fixed size
        self.setWindowTitle('Add an Event')


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
                    'N', 'O', 'P', 'Q','R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
        for letter in alphabet:
            #About the lambda letter=letter:. I don't know why it fixes the problem, but it does. Here's a better
            #Explanation: http://stackoverflow.com/questions/4578861/connecting-slots-and-signals-in-pyqt4-in-a-loop
            self.lettersSubMnu.addAction(letter, lambda letter=letter: self.btnClicked(KeypressEvent, parameters={"checkKey": letter}))

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


    def btnClicked(self, eventType, **kwargs):
        print "EventWindow.buttonSelected():\t Event Type ", eventType, "selected"
        self.chosenEvent      = eventType
        self.chosenParameters = kwargs.get("parameters", None)
        self.accepted = True
        self.close()

    def cancelClicked(self, event):
        self.close()




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


        #The following is a function that returns a dictionary of the commands, in the correct order
        self.getCommandsOrdered = lambda: [self.commands[self.item(index)] for index in xrange(self.count())]

        self.initUI()

    def initUI(self):
        self.setMinimumWidth(250)

    def updateWidth(self):
        #Update the width of the commandList to the widest element within it
        #This occurs whenever items are changed, or added, to the commandList
        if self.sizeHintForColumn(0) + 10 < 600:
            self.setMinimumWidth(self.sizeHintForColumn(0) + 10)


    def addCommand(self, commandType, **kwargs):
        #If adding a pre-filled command (used when loading a save)
        parameters = kwargs.get("parameters", None)
        if parameters is None:
            newCommand = commandType(self)
        else:
            newCommand = commandType(self, parameters=parameters)


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
        print "CommandList.doubleClickEvent(): Opening double clicked command"
        selectedItems   = self.selectedItems()
        selectedItem    = selectedItems[0]

        self.commands[selectedItem].openView()
        #selectedCommand.openView()
        print "view opened"
        self.commands[selectedItem].getInfo()
        updatedWidget   =  self.commands[selectedItem].getWidget()

        self.setItemWidget( selectedItem, updatedWidget)
        self.updateWidth()


    def getSaveData(self):
        commandList = []
        commandsOrdered = self.getCommandsOrdered()

        for command in commandsOrdered:
            commandSave = {}
            commandSave["type"] = type(command)
            commandSave["parameters"] = command.parameters
            commandList.append(commandSave)

        return commandList

    def loadData(self, data):
        #Clear all data on the current list
        self.commands = {}
        self.clear()

        #Fill the list with new data
        for index, commandInfo in enumerate(data):
            type = commandInfo["type"]
            parameters = commandInfo["parameters"]
            self.addCommand(type, parameters=parameters)

    # def loadData(self, data):
    #     self.events = {}
    #     self.clear()  #clear eventList
    #
    #     #Fill event list with new data
    #     for index, eventSave in enumerate(data):
    #         commandList = CommandList()
    #         commandList.loadData(eventSave['commandList'])
    #
    #         self.addEvent(eventSave['type'], commandList=commandList, parameters=eventSave["parameters"])


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


class CommandPromptWindow(QtGui.QDialog):
    def __init__(self):
        super(CommandPromptWindow, self).__init__()
        self.accepted         = False
        self.chosenCommand    = None  #What event the user chose to add (changed in btnClicked() function)
        self.initUI()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.exec_()  #Open self, and prevent anyone clicking on other windows


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
        self.setFixedSize(self.sizeHint())  #Make the window a fixed size
        self.setWindowTitle('Add an Event')


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
                    'N', 'O', 'P', 'Q','R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
        for letter in alphabet:
            #About the lambda letter=letter:. I don't know why it fixes the problem, but it does. Here's a better
            #Explanation: http://stackoverflow.com/questions/4578861/connecting-slots-and-signals-in-pyqt4-in-a-loop
            self.lettersSubMnu.addAction(letter, lambda letter=letter: self.btnClicked(KeypressEvent, parameters={"checkKey": letter}))

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


    def btnClicked(self, eventType, **kwargs):
        print "EventWindow.buttonSelected():\t Event Type ", eventType, "selected"
        self.chosenEvent      = eventType
        self.chosenParameters = kwargs.get("parameters", None)
        self.accepted = True
        self.close()

    def cancelClicked(self, event):
        self.close()




########## EVENTS ##########
class Event(object):
    def __init__(self):
        """
        self.parameters is used for events like KeyPressEvent where one class can handle multiple types of events
        such as A KeyPress or ZKeypress. THe self.parameters makes sure that you can differentiate between events
        when adding new ones, so you can make sure there aren't two 'A Keypress' events.
        """

        self.commandList = None
        self.parameters = {}

    def runCommands(self):
        commandsOrdered = self.commandList.getCommandsOrdered()
        print commandsOrdered
        for command in commandsOrdered:
            command.run()


class InitEvent(Event):
    def __init__(self):
        super(InitEvent, self).__init__()
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
            return True

    def runCommands(self):
        #Intercept the parent class events so that you can set self.hasBeenRun to true
        Event.runCommands(self)
        self.hasBeenRun = True


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


class KeypressEvent(Event):
    def __init__(self, parameters):
        Event.__init__(self)

        self.parameters = parameters
        print "event started with a checkey of ", parameters

    def getWidget(self):
        listWidget = EventWidget()
        listWidget.setIcon(Icons.keyboard_event)
        listWidget.setTitle('Keypress ' + self.parameters["checkKey"])

        return listWidget

    def isActive(self):
        if ord(self.parameters["checkKey"]) in Global.keysPressed:
            return True
        else:
            return False
        # if len(Global.keysPressed) > 0:
        #     return True
        # else:
        #     return False








########## COMMANDS ##########
class Command(QtGui.QDialog):
    def __init__(self, parent):

        super(Command, self).__init__(parent)

        #self.parameters = {}  #Will be filled with parameters for the particular command
        self.accepted    = False
        self.mainVLayout = QtGui.QVBoxLayout()
       # self.parameters = {"type": type(self)}
        self.initBaseUI()
        #self.setAttribute( QtCore.Qt.WA_DeleteOnClose)

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

        try:
            print "Command.openView():\t About to execute self..."
            #self.show()
            self.exec_()
            print "Command.openView():\t Finished executing self..."
        except:
            print "Command.openView():\t ERROR ERROR ERROR while opening view of command window. Fix!"

        #See if the user pressed Ok or if he cancelled/exited out
        if self.accepted:
            #Get information that the user input
            newParameters = self.getInfo().copy()

            #  Add the new parameters to the dictionary, and update changed values
            self.parameters.update(newParameters)



            print 'CommandWindow.openView(): New parameters: ', self.parameters

        else:
            print "c was not accepted"
            print 'CommandWindow.openView(): User Canceled.'


class MoveXYZCommand(Command):
    def __init__(self, parent, **kwargs):
        self.title       = "Move XYZ"

        super(MoveXYZCommand, self).__init__(parent)

        #Set default parameters that will show up on the window
        currentXYZ = Global.robot.currentCoord()

        self.parameters = kwargs.get("parameters",
                            {'x': round(currentXYZ[1], 1),
                             'y': round(currentXYZ[2], 1),
                             'z': round(currentXYZ[3], 1),
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
            listWidget.setDescription('X: '                + str(int(self.parameters['x'])) +
                                           '   Y: '        + str(int(self.parameters['y'])) +
                                           '   Z: '        + str(int(self.parameters['z'])) +
                                           '   Relative: ' + str(    self.parameters['rel']))
            return listWidget

    def run(self):
        print "MoveXYZCommand.run(): Moving robot to ", self.parameters['x'], self.parameters['y'], self.parameters['z']
        Global.robot.setPos(x=self.parameters['x'],
                            y=self.parameters['y'],
                            z=self.parameters['z'],
                            relative=self.parameters['rel'])


class DetachCommand(Command):
    """
    A command for detaching the servos of the robot
    """
    def __init__(self, parent, **kwargs):
        self.title       = "Detach Servos"
        super(DetachCommand, self).__init__(parent)
        #Command.__init__(self)

        #Set default parameters that will show up on the window
        self.parameters = kwargs.get("parameters",
                                     {'servo1': False,
                                      'servo2': False,
                                      'servo3': False,
                                      'servo4': False})

        self.srvo1Box = QtGui.QCheckBox()  #  Rotation textbox
        self.srvo2Box = QtGui.QCheckBox()  #  Stretch textbox
        self.srvo3Box = QtGui.QCheckBox()  #  Height textbox
        self.srvo4Box = QtGui.QCheckBox()  #  "relative" CheckBox
        self.initUI()

    def initUI(self):
        #Set up all the labels for the inputs
        label1 = QtGui.QLabel('Rotation Servo:')
        label2 = QtGui.QLabel('Stretch Servo:')
        label3 = QtGui.QLabel('Height Servo:')
        label4 = QtGui.QLabel('Wrist Servo:')

        #Fill the textboxes with the default parameters
        self.srvo1Box.setChecked(self.parameters['servo1'])
        self.srvo2Box.setChecked(self.parameters['servo2'])
        self.srvo3Box.setChecked(self.parameters['servo3'])
        self.srvo4Box.setChecked(self.parameters['servo4'])

        row1 = QtGui.QHBoxLayout()
        row2 = QtGui.QHBoxLayout()
        row3 = QtGui.QHBoxLayout()
        row4 = QtGui.QHBoxLayout()

        row1.addWidget(label1, QtCore.Qt.AlignRight)
        row1.addWidget(self.srvo1Box, QtCore.Qt.AlignLeft)

        row2.addWidget(label2, QtCore.Qt.AlignRight)
        row2.addWidget(self.srvo2Box, QtCore.Qt.AlignLeft)

        row3.addWidget(label3, QtCore.Qt.AlignRight)
        row3.addWidget(self.srvo3Box, QtCore.Qt.AlignLeft)

        row4.addWidget(label4, QtCore.Qt.AlignRight)
        row4.addWidget(self.srvo4Box, QtCore.Qt.AlignLeft)

        self.mainVLayout.addLayout(row1)
        self.mainVLayout.addLayout(row2)
        self.mainVLayout.addLayout(row3)
        self.mainVLayout.addLayout(row4)

    def getInfo(self):
        #Build the info inputed into the window into a Json and return it. Used in parent class

        newParameters = {'servo1': self.srvo1Box.isChecked(),
                         'servo2': self.srvo2Box.isChecked(),
                         'servo3': self.srvo3Box.isChecked(),
                         'servo4': self.srvo4Box.isChecked()}

        return newParameters

    def getWidget(self):
        #Verify that there are no None statements in the parameters
        if any(self.parameters) is None or self.parameters.__len__() == 0:#any(x is None for x in self.parameters.itervalues()):
            return None
        else:
            listWidget = CommandWidget()
            listWidget.setIcon(Icons.detach_command)
            listWidget.setTitle(self.title)

            descriptionBuild = "Servos"
            if self.parameters["servo1"]: descriptionBuild += "  Rotation"
            if self.parameters["servo2"]: descriptionBuild += "  Stretch"
            if self.parameters["servo3"]: descriptionBuild += "  Height"
            if self.parameters["servo4"]: descriptionBuild += "  Wrist"

            listWidget.setDescription(descriptionBuild)

            return listWidget

    def run(self):
        print "DetachCommand.run(): Detaching servos ", self.parameters['servo1'], \
                                                        self.parameters['servo2'], \
                                                        self.parameters['servo3'], \
                                                        self.parameters['servo4']
        if self.parameters['servo1']: Global.robot.setServos(servo1=False)
        if self.parameters['servo2']: Global.robot.setServos(servo2=False)
        if self.parameters['servo3']: Global.robot.setServos(servo3=False)
        if self.parameters['servo4']: Global.robot.setServos(servo4=False)
