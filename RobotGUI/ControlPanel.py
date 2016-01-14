from threading import Thread
from Events import *
from Commands import *
from time import time
from PyQt4 import QtGui, QtCore
from Global import printf
import copy


class Shared():
    """
    This is my slightly safer attempt at avoiding global variables.
    This class will share variables between commands, such as the robot, the vision class, and
    various calibration settings.

    I mean, anything is better than globals right?
    """

    def __init__(self, robot, vision, settings):

        #Used in any movement related task
        self.robot       = robot


        #Used in the motion detection event, ColorTrackCommand, etc
        self.vision      = vision


        #Used in the motion detection event to get the motionCalibration settings
        self.settings    = settings





class ControlPanel(QtGui.QWidget):
    """
    ControlPanel:

    Purpose: A nice clean widget that has both the EventList and CommandList displayed, and the "AddEvent" and
            "AddCommand" buttons. It is a higher level of abstraction for the purpose of handling the running of the
            robot program, instead of the nitty gritty details of the commandList and eventList
    """
    def __init__(self, robot, vision, settings, parent):
        super(ControlPanel, self).__init__(parent)

        #Set up Globals
        self.shared            = Shared(robot, vision, settings)
        self.robot             = robot                    #Used in programThread() to 'refresh' the robot
        self.eventList         = EventList(self.refresh, parent=self)
        self.running           = False                    #Whether or not the main thread should be running or not
        self.mainThread        = None                     #This holds the 'Thread' object of the main thread.
        self.addCommandWidget  = CommandMenuWidget(self.addCommand, parent=self)
        self.commandListStack  = QtGui.QStackedWidget()

        self.initUI()



    def initUI(self):
        #Set Up Buttons
        addEventBtn       = QtGui.QPushButton()
        deleteEventBtn    = QtGui.QPushButton()
        changeEventBtn    = QtGui.QPushButton()

        addEventBtn.setText("Add Event")
        deleteEventBtn.setText("Delete")
        changeEventBtn.setText("Change")

        #Connect Button Events
        addEventBtn.clicked.connect(self.addEvent)
        deleteEventBtn.clicked.connect(self.deleteEvent)
        changeEventBtn.clicked.connect(self.replaceEvent)


        eventVLayout   = QtGui.QVBoxLayout()
        eventVLayout.addWidget(addEventBtn)
        btnRowHLayout  = QtGui.QHBoxLayout()
        btnRowHLayout.addWidget(deleteEventBtn)
        btnRowHLayout.addWidget(changeEventBtn)
        eventVLayout.addLayout(btnRowHLayout)
        eventVLayout.addWidget(self.eventList)

        commandVLayout = QtGui.QVBoxLayout()
        commandVLayout.addWidget(self.commandListStack)

        addCmndVLayout = QtGui.QVBoxLayout()
        addCmndVLayout.addWidget(self.addCommandWidget)
        addCmndVLayout.addStretch(1)


        self.commandListStack.addWidget(CommandList(parent=self))  #Add a placeholder commandList

        mainHLayout   = QtGui.QHBoxLayout()
        mainHLayout.addLayout(eventVLayout)
        mainHLayout.addLayout(commandVLayout)
        mainHLayout.addLayout(addCmndVLayout)

        self.setLayout(mainHLayout)
        self.show()

    def refresh(self):
        #Refresh which commandList is currently being displayed to the one the user has highlighted

        #Get the currently selected event on the eventList
        selectedEvent = self.eventList.getSelectedEvent()


        #Delete all widgets on the commandList stack
        for c in range(0, self.commandListStack.count()):
            widget = self.commandListStack.widget(c)
            self.commandListStack.removeWidget(widget)

        #If user has no event selected, make a clear commandList to view
        if selectedEvent is None:
            printf("ControlPanel.refresh():ERROR: no event selected!")
            clearList = CommandList(parent=self)
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
            printf("ControlPanel.startThread(): ERROR: Tried to run programthread, but there was one already running!")

    def endThread(self):
        #Close the program thread and wrap up loose ends
        printf("ControlPanel.endThread(): Closing program thread.")
        self.running = False

        if self.mainThread is not None:
            self.mainThread.join(3000)
            self.mainThread = None

    def programThread(self):
        #This is where the script will be run

        printf("ControlPanel.programThread():#################### STARTING PROGRAM THREAD! ######################")
        millis         = lambda: int(round(time() * 1000))
        readyForNext   = lambda lastMillis: millis() - lastMillis >= (1 / float(stepsPerSecond)) * 1000
        stepsPerSecond = 10
        lastMillis     = millis()

        #Deepcopy all of the events, so that every time you run the script it runs with no modified variables
        events = copy.deepcopy(self.eventList.getEventsOrdered())
        eventItem  = self.eventList.getItemsOrdered()

        while self.running:



            #Wait till it's time for a new step
            if not readyForNext(lastMillis): continue
            lastMillis = millis()

            #printf("\n\nControlPanel.programThread():  ########## PERFORMING    ALL    EVENTS ##########"
            #Check all events and tell them to run their commands when appropriate
            for index, event in enumerate(events):

                if event.isActive(self.shared):
                    eventItem[index].setBackgroundColor(QtGui.QColor(150, 255, 150))  #Highlight event thats going to run
                    event.runCommands(self.shared)
                    #printf("\n"
                else:
                    eventItem[index].setBackgroundColor(QtGui.QColor(QtCore.Qt.transparent))

            #Only "Render" the robots movement once per step
            self.robot.refresh()




        #Turn each list item transparent once more
        for item in eventItem:
            item.setBackgroundColor(QtGui.QColor(QtCore.Qt.transparent))


        #Check if there is a DestroyEvent command. If so, run it
        destroyEvent = filter(lambda event: type(event) == DestroyEvent, events)
        if len(destroyEvent): destroyEvent[0].runCommands(self.shared)
        self.robot.setGripper(False)
        self.robot.refresh()
        #Global.robot.setServos(servo1=True, servo2=True, servo3=True, servo4=True)  #Re-lock all servos on the robot




    def addCommand(self, type):
        #When the addCommand button is pressed
        printf("ControlPanel.addCommand(): Add Command button clicked. Adding command!")

        selectedEvent = self.eventList.getSelectedEvent()
        if selectedEvent is None:
            #This occurs when there are no events on the table. Display warning to user in this case.
            printf("ControlPanel.addCommand(): ERROR: Selected event does not have a commandList! Displaying error")
            QtGui.QMessageBox.question(self, 'Error', 'You need to select an event or add '
                                       'an event before you can add commands', QtGui.QMessageBox.Ok)
            return

        selectedEvent.commandList.addCommand(type, shared=self.shared)

    def addEvent(self):
        self.eventList.promptUser()

    def deleteEvent(self):
        self.eventList.deleteEvent()

    def replaceEvent(self):
        self.eventList.replaceEvent()


    def getSaveData(self):
        return self.eventList.getSaveData()

    def loadData(self, data):
        self.eventList.loadData(data, self.shared)


    def closeEvent(self, event):
        #Do things here like closing threads and such
        self.endThread()


class EventList(QtGui.QListWidget):
    def __init__(self, refresh, parent):

        super(EventList, self).__init__()
        #GLOBALS
        self.refreshControlPanel = refresh
        self.events = {}  #A hash map of the current events in the list. The listWidget leads to the event object

        #IMPORTANT This makes sure the ControlPanel refreshes whenever you click on an item in the list,
        #in order to display the correct commandList for the event that was clicked on.
        self.itemSelectionChanged.connect(self.refreshControlPanel)

        #The following is a function that returns a dictionary of the events, in the correct order
        self.getEventsOrdered = lambda: [self.events[self.item(index)] for index in xrange(self.count())]
        self.getItemsOrdered  = lambda: [self.item(index) for index in xrange(self.count())]
        self.initUI()

    def initUI(self):
        self.setFixedWidth(200)


    def getSelectedEvent(self):
        """
        This method returns the Event() class for the currently clicked-on event.
        This is used for displaying the correct commandList, or adding a command
        to the correct event.
        """
        selectedItem = self.getSelectedEventItem()
        if selectedItem is None:
            printf("EventList.getSelected(): ERROR: 0 events selected")
            return None
        return self.events[selectedItem]

    def getSelectedEventItem(self):
        selectedItems = self.selectedItems()
        if len(selectedItems) == 0 or len(selectedItems) > 1:
            printf("EventList.getSelectedEventItem(): ERROR: ", len(selectedItems), " events selected")
            return None


        if selectedItems is None:
            printf("EventList.getSelectedEventItem(): BIG ERROR: selectedEvent was none!")
            raise Exception

        selectedItem = selectedItems[0]
        return selectedItem


    def promptUser(self):
        #Open the eventPromptWindow to ask the user what event they wish to create
        eventPrompt = EventPromptWindow(self)
        if eventPrompt.accepted:
            self.addEvent(eventPrompt.chosenEvent, parameters=eventPrompt.chosenParameters)
        else:
            printf("EventList.promptUser():User rejected the prompt.")


    def addEvent(self, eventType, **kwargs):
        params = kwargs.get("parameters", None)


        #Check if the event being added already exists in the self.events dictionary
        for x in self.events.itervalues():
            if isinstance(x, eventType) and (x.parameters == params or params is None):
                printf("EventList.addEvent(): Event already exists, disregarding user input.")
                return

        #Check if the event has specific parameters (Such as a KeyPressEvent that specifies A must be the key pressed)
        # if params is None or params == {}:
        #     newEvent = eventType()
        # else:
        newEvent = eventType(params)


        newEvent.commandList = kwargs.get("commandList", CommandList(parent=self))
        #Create the widget and list item to visualize the event
        blankWidget    = EventWidget(self)
        eventWidget    = newEvent.getWidget(blankWidget)
        listWidgetItem = QtGui.QListWidgetItem(self)
        listWidgetItem.setSizeHint(eventWidget.sizeHint())   #Widget will not appear without this line
        self.addItem(listWidgetItem)

        #Add the widget to the list item
        self.setItemWidget(listWidgetItem, eventWidget)

        self.events[listWidgetItem] = newEvent


        self.setCurrentRow(self.count() - 1)  #Select the newly added event
        self.refreshControlPanel()            #Call for a refresh of the ControlPanel so it shows the commandList

    def deleteEvent(self):
        printf("EventList.deleteEvent(): Removing selected event")
        #Get the current item it's corresponding event
        selectedItem = self.getSelectedEventItem()
        if selectedItem is None:
            QtGui.QMessageBox.question(self, 'Error', 'You need to select an event to delete', QtGui.QMessageBox.Ok)
            return



        #If there are commands inside the event, ask the user if they are sure they want to delete it
        #if len(self.getSelectedEvent.commands) > 0:
        if len(self.getSelectedEvent().commandList.commands) > 0:
            reply = QtGui.QMessageBox.question(self, 'Message',
                                               "Are you sure you want to delete this event and all its commands?",
                                               QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)

            if reply == QtGui.QMessageBox.No:
                printf("EventList.addCommand(): User rejected deleting the event")
                return


        #Delete the event item and it's corresponding event
        del self.events[selectedItem]
        self.takeItem(self.currentRow())

    def replaceEvent(self):
        printf("EventList.replaceEvent(): Changing selected event")

        #Get the current item it's corresponding event
        selectedItem = self.getSelectedEventItem()
        if selectedItem is None:
            QtGui.QMessageBox.question(self, 'Error', 'You need to select an event to change', QtGui.QMessageBox.Ok)
            return

        #Get the replacement event from the user
        eventPrompt = EventPromptWindow(parent=self)
        if not eventPrompt.accepted:
            printf("EventList.replaceEvent():User rejected the prompt.")
            return
        eventType = eventPrompt.chosenEvent
        params    = eventPrompt.chosenParameters

        #Make sure this event does not already exist
        for x in self.events.itervalues():
            if isinstance(x, eventType) and (x.parameters == params or params is None):
                printf("EventList.addEvent(): Event already exists, disregarding user input.")
                return

        #Actually change the event to the new type
        newEvent = eventType(params)
        newEvent.commandList = self.events[selectedItem].commandList



        #Change the item widget to match
        blankWidget    = EventWidget(self)
        eventWidget    = newEvent.getWidget(blankWidget)
        self.setItemWidget(selectedItem, eventWidget)

        #Update the self.events dictionary with the new event
        self.events[selectedItem] = newEvent



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


    def loadData(self, data, shared):
        self.events = {}
        self.clear()  #clear eventList

        #Fill event list with new data
        for index, eventSave in enumerate(data):
            commandList = CommandList(parent=self)
            commandList.loadData(eventSave['commandList'], shared)
            self.addEvent(eventSave['type'], commandList=commandList, parameters=eventSave["parameters"])


        #Select the first event for viewing
        if self.count() > 0: self.setCurrentRow(0)


class CommandList(QtGui.QListWidget):
    def __init__(self, parent):
        super(CommandList, self).__init__()
        #GLOBALS
        self.commands       = {}      #Dictionary of commands. Ex: {QListItem: MoveXYZCommand, QListItem: PickupCommand}
        self.commandWidgets = {}
        self.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setAcceptDrops(True)
        self.itemDoubleClicked.connect(self.doubleClickEvent)
        self.itemClicked.connect(self.clickEvent)
        self.itemSelectionChanged.connect(self.selectionChangedEvent)
        self.selectedCommand = None


        #The following is a function that returns a dictionary of the commands, in the correct order
        self.getCommandsOrdered = lambda: [self.commands[self.item(index)] for index in xrange(self.count())]

        self.initUI()

    def initUI(self):
        self.setMinimumWidth(250)

    def clickEvent(self, listWidgetItem):
        # Notify the clicked item that it is in focus
        self.commandWidgets[listWidgetItem].focusIn()
        self.selectedCommand =  self.commandWidgets[listWidgetItem]

    def selectionChangedEvent(self):
        # Notify the last focused item that it is no longer in focus
        if self.selectedCommand != None:
            self.selectedCommand.focusOut()
            self.selectedCommand = None

    def updateWidth(self):
        #Update the width of the commandList to the widest element within it
        #This occurs whenever items are changed, or added, to the commandList
        if self.sizeHintForColumn(0) + 10 < 1300:
            self.setMinimumWidth(self.sizeHintForColumn(0) + 10)


    def addCommand(self, commandType, shared, **kwargs):
        #If adding a pre-filled command (used when loading a save)
        parameters = kwargs.get("parameters", None)

        if parameters is None:
            newCommand = commandType(self, shared)
        else:
            newCommand = commandType(self, shared, parameters=parameters)


        #Fill command with information either by opening window or loading it in
        if parameters is None:  #If none, then this is being added by the user and not the system loading a file
            newCommand.openView()  #Get information from user
            if not newCommand.accepted:
                printf("CommandList.addCommand(): User rejected prompt")
                return
        else:
            newCommand.parameters = parameters



        #Create the list widget to visualize the widget
        commandWidget = newCommand.getWidget(self.deleteCommandEvent)
        listWidgetItem = QtGui.QListWidgetItem(self)
        listWidgetItem.setSizeHint(commandWidget.sizeHint())  #Widget will not appear without this line
        self.addItem(listWidgetItem)

        #Add list widget to commandList
        self.setItemWidget(listWidgetItem, commandWidget)

        #Add the new command to the list of commands, linking it with its corresponding listWidgetItem
        self.commands[listWidgetItem] = newCommand
        self.commandWidgets[listWidgetItem] = commandWidget

        #Update the width of the commandList to the widest element within it
        self.updateWidth()

    def deleteCommandEvent(self, widget):
        for key, val in self.commandWidgets.iteritems():
            if val == widget:
                self.commandWidgets[key].deleteLater()
                del self.commands[key]
                del self.commandWidgets[key]
                self.takeItem(self.row(key))
                break

    def keyPressEvent(self, event):
        #Delete selected items when delete key is pressed
        if event.key() == QtCore.Qt.Key_Delete:
            for item in self.selectedItems():
                self.commandWidgets[item].deleteLater()
                del self.commands[item]
                del self.commandWidgets[item]
                self.takeItem(self.row(item))

    def dropEvent(self, event):
        event.setDropAction(QtCore.Qt.MoveAction)
        super(CommandList, self).dropEvent(event)
        lst = [i.text() for i in self.findItems('', QtCore.Qt.MatchContains)]

    def doubleClickEvent(self):
        #Open the command window for the command that was just double clicked
        printf("CommandList.doubleClickEvent(): Opening double clicked command")
        selectedItems   = self.selectedItems()
        selectedItem    = selectedItems[0]

        self.commands[selectedItem].openView()
        self.commands[selectedItem].getInfo()
        updatedWidget   =  self.commands[selectedItem].getWidget(self.deleteCommandEvent)

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

    def loadData(self, data, shared):
        #Clear all data on the current list
        self.commands = {}
        self.clear()

        #Fill the list with new data
        for index, commandInfo in enumerate(data):
            type = commandInfo["type"]
            parameters = commandInfo["parameters"]
            self.addCommand(type, shared, parameters=parameters)
