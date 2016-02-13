import copy
from RobotGUI.Events   import *
from RobotGUI.Commands import *
from RobotGUI.Global   import printf, FpsTimer
from threading         import Thread
from PyQt5             import QtGui, QtCore, QtWidgets



class Shared:
    """
    This is my slightly safer attempt at avoiding global variables.
    This class will share variables between commands, such as the robot, the vision class, and
    various calibration settings.

    I mean, anything is better than globals right?

    Also, having the getRobot, getVision, and getSettings will allow someday for threaded events,
    if I ever choose to do such a thing.
    """

    def __init__(self, robot, vision, settings):
        # Used in any movement related task
        self.robotObj = robot

        # Used in the motion detection event, ColorTrackCommand, etc
        self.visionObj = vision

        # Used in the motion detection event to get the motionCalibration settings
        self.settingsObj = settings

    def getRobot(self):
        return self.robotObj

    def getVision(self):
        return self.visionObj

    def getSettings(self):
        return self.settingsObj


class ControlPanel(QtWidgets.QWidget):
    """
    ControlPanel:

    Purpose: A nice clean widget that has both the EventList and CommandList displayed, and the "AddEvent" and
            "AddCommand" buttons. It is a higher level of abstraction for the purpose of handling the running of the
            robot program, instead of the nitty gritty details of the commandList and eventList
    """

    def __init__(self, robot, vision, settings, parent):
        super(ControlPanel, self).__init__(parent)

        # Set up Globals
        self.shared = Shared(robot, vision, settings)
        self.robot = robot  # Used in programThread() to 'refresh' the robot
        self.eventList = EventList(self.refresh, parent=self)
        self.running = False  # Whether or not the main thread should be running or not
        self.mainThread = None  # This holds the 'Thread' object of the main thread.
        self.addCommandWidget = CommandMenuWidget(self.addCommand, parent=self)
        self.commandListStack = QtWidgets.QStackedWidget()

        self.initUI()

    def initUI(self):
        # Set Up Buttons
        addEventBtn = QtWidgets.QPushButton()
        deleteEventBtn = QtWidgets.QPushButton()
        changeEventBtn = QtWidgets.QPushButton()

        addEventBtn.setText("Add Event")
        deleteEventBtn.setText("Delete")
        changeEventBtn.setText("Change")

        # Connect Button Events
        addEventBtn.clicked.connect(self.addEvent)
        deleteEventBtn.clicked.connect(self.deleteEvent)
        changeEventBtn.clicked.connect(self.replaceEvent)

        eventVLayout = QtWidgets.QVBoxLayout()
        eventVLayout.addWidget(addEventBtn)
        btnRowHLayout = QtWidgets.QHBoxLayout()
        btnRowHLayout.addWidget(deleteEventBtn)
        btnRowHLayout.addWidget(changeEventBtn)
        eventVLayout.addLayout(btnRowHLayout)
        eventVLayout.addWidget(self.eventList)

        commandVLayout = QtWidgets.QVBoxLayout()
        commandVLayout.addWidget(self.commandListStack)

        addCmndVLayout = QtWidgets.QVBoxLayout()
        addCmndVLayout.addWidget(self.addCommandWidget)
        addCmndVLayout.addStretch(1)

        self.commandListStack.addWidget(CommandList(parent=self))  # Add a placeholder commandList

        mainHLayout = QtWidgets.QHBoxLayout()
        mainHLayout.addLayout(eventVLayout)
        mainHLayout.addLayout(commandVLayout)
        mainHLayout.addLayout(addCmndVLayout)

        self.setLayout(mainHLayout)
        self.show()

    def refresh(self):
        # Refresh which commandList is currently being displayed to the one the user has highlighted

        # Get the currently selected event on the eventList
        selectedEvent = self.eventList.getSelectedEvent()

        # Delete all widgets on the commandList stack
        for c in range(0, self.commandListStack.count()):
            widget = self.commandListStack.widget(c)
            self.commandListStack.removeWidget(widget)

        # If user has no event selected, make a clear commandList to view
        if selectedEvent is None:
            printf("ControlPanel.refresh():ERROR: no event selected!")
            clearList = CommandList(parent=self)
            self.commandListStack.addWidget(clearList)
            self.commandListStack.setCurrentWidget(clearList)
            return

        # Add and display the correct widget
        print("SelectedEvent: ", selectedEvent)
        print("cmmndlist: ", selectedEvent.commandList)
        self.commandListStack.addWidget(selectedEvent.commandList)
        self.commandListStack.setCurrentWidget(selectedEvent.commandList)

    def startThread(self):
        # Start the program thread
        if self.mainThread is None:
            self.running = True

            self.mainThread = Thread(target=self.programThread)

            self.mainThread.start()
        else:
            printf("ControlPanel.startThread(): ERROR: Tried to run programthread, but there was one already running!")

    def endThread(self):
        # Close the program thread and wrap up loose ends
        printf("ControlPanel.endThread(): Closing program thread.")
        self.running = False

        if self.mainThread is not None:
            self.mainThread.join(3000)
            if self.mainThread.is_alive():
                printf("ControlPanel.endThread(): ERROR: Thread was told to close but did not")
            else:
                self.mainThread = None

    def programThread(self):
        # while self.running: pass
        # This is where the script will be run
        printf("ControlPanel.programThread(): #################### STARTING PROGRAM THREAD! ######################")

        # Deepcopy all of the events, so that every time you run the script it runs with no modified variables
        events = copy.copy(self.eventList.getEventsOrdered())

        # color = QtGui.QColor(150, 255, 150)
        # transparent = QtGui.QColor(QtCore.Qt.transparent)
        # eventItem   = self.eventList.getItemsOrdered()
        # setColor    = lambda item, isColored: item.setBackground((transparent, color)[isColored])

        timer = FpsTimer(fps=1)
        # Reset all events to default state
        for event in events: event.reset()

        while self.running:
            timer.wait()
            if not timer.ready(): continue

            # Check each event to see if it is active
            for index, event in enumerate(events):

                if event.isActive(self.shared):
                    # setColor(eventItem[index], True)
                    # eventItem[index].setBackground(QtGui.QColor(150, 255, 150))  #Highlight event that running

                    # Run all commands in the active event
                    self.interpretCommands(event.commandList)

                else:
                    pass
                    # setColor(eventItem[index], False)
                    # eventItem[index].setBackground(QtGui.QColor(QtCore.Qt.transparent))

            # Only "Render" the robots movement once per step
            self.robot.refresh()

        # #Turn each list item transparent once more
        # for item in eventItem:
        #     pass
        #     #setColor(item, False)
        #     #item.setBackground(QtGui.QColor(QtCore.Qt.transparent))


        # Check if there is a DestroyEvent command. If so, run it
        destroyEvent = list(filter(lambda event: type(event) == DestroyEvent, events))
        if len(destroyEvent): self.interpretCommands(destroyEvent[0].commandList)

        self.robot.setGripper(False)
        self.robot.refresh()

    def interpretCommands(self, commandList):
        """
        This is only used in programThread(). It parses through and runs all commands in a commandList,
        correctly accounting for all the indenting and such. The idea is that you can pass a commandList
        from an event to this function, and all the commands will be evaluated and run.

        Most commands (almost all) will not return anything. However, any commands that evaluate to
        True or False will, in fact, return True or False. This determines whether or not code in blocks
        will run.
        :param commandList: This is the commandList that will be 'interpreted'
        """

        commandsOrdered = commandList.getCommandsOrdered()
        index = 0
        # indent = 0

        while index < len(commandsOrdered):
            command = commandsOrdered[index]
            ret = command.run(self.shared)

            # If the command is an evaluation command, test it
            print("Index: ", index, "\tindent: ", command.indent, "\tret", ret, "cmnd: ", type(command), "next: ")

            # if ret is None: continue

            if ret is not None and not ret:
                skipToIndent = command.indent
                # print("skipping to next indent of", skipToIndent, "starting at", index)

                for i in range(index + 1, len(commandsOrdered)):
                    if commandsOrdered[i].indent == skipToIndent:
                        index = i - 1
                        break
                    # If there are no commands
                    if i == len(commandsOrdered) - 1:
                        index = i
                        break

            index += 1

    def addCommand(self, type):
        # When the addCommand button is pressed
        printf("ControlPanel.addCommand(): Add Command button clicked. Adding command!")

        selectedEvent = self.eventList.getSelectedEvent()
        if selectedEvent is None:
            # This occurs when there are no events on the table. Display warning to user in this case.
            printf("ControlPanel.addCommand(): ERROR: Selected event does not have a commandList! Displaying error")
            QtWidgets.QMessageBox.question(self, 'Error', 'You need to select an event or add '
                                                          'an event before you can add commands',
                                           QtWidgets.QMessageBox.Ok)
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
        # Do things here like closing threads and such
        self.endThread()


class EventList(QtWidgets.QListWidget):
    def __init__(self, refresh, parent):

        super(EventList, self).__init__()
        # GLOBALS
        self.refreshControlPanel = refresh
        self.events = {}  # A hash map of the current events in the list. The listWidget leads to the event object

        # IMPORTANT This makes sure the ControlPanel refreshes whenever you click on an item in the list,
        # in order to display the correct commandList for the event that was clicked on.
        self.itemSelectionChanged.connect(self.refreshControlPanel)

        # The following is a function that returns a dictionary of the events, in the correct order
        self.getEventsOrdered = lambda: [self.getEvent(self.item(index)) for index in range(self.count())]
        # self.getItemsOrdered  = lambda: [self.item(index) for index in range(self.count())]
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
        return self.getEvent(selectedItem)

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

    def getEvent(self, listWidgetItem):
        return self.events[self.itemWidget(listWidgetItem)]

    def promptUser(self):
        # Open the eventPromptWindow to ask the user what event they wish to create
        eventPrompt = EventPromptWindow(self)
        if eventPrompt.accepted:
            self.addEvent(eventPrompt.chosenEvent, parameters=eventPrompt.chosenParameters)
        else:
            printf("EventList.promptUser():User rejected the prompt.")

    def addEvent(self, eventType, **kwargs):
        params = kwargs.get("parameters", None)

        # Check if the event being added already exists in the self.events dictionary
        for x in self.events.items():
            if isinstance(x, eventType) and (x.parameters == params or params is None):
                printf("EventList.addEvent(): Event already exists, disregarding user input.")
                return

        newEvent = eventType(params)

        newEvent.commandList = kwargs.get("commandList", CommandList(parent=self))

        # Create the widget item to visualize the event
        blankWidget = EventWidget(self)
        eventWidget = newEvent.dressWidget(blankWidget)

        # Create the list item to put the widget item inside of
        listWidgetItem = QtWidgets.QListWidgetItem(self)
        listWidgetItem.setSizeHint(eventWidget.sizeHint())  # Widget will not appear without this line
        self.addItem(listWidgetItem)

        # Add the widget to the list item
        self.setItemWidget(listWidgetItem, eventWidget)

        self.events[eventWidget] = newEvent

        self.setCurrentRow(self.count() - 1)  # Select the newly added event
        self.refreshControlPanel()  # Call for a refresh of the ControlPanel so it shows the commandList

    def deleteEvent(self):
        printf("EventList.deleteEvent(): Removing selected event")
        # Get the current item it's corresponding event
        selectedItem = self.getSelectedEventItem()
        if selectedItem is None:
            QtWidgets.QMessageBox.question(self, 'Error', 'You need to select an event to delete',
                                           QtWidgets.QMessageBox.Ok)
            return

        # If there are commands inside the event, ask the user if they are sure they want to delete it
        if len(self.getSelectedEvent().commandList.commands) > 0:
            reply = QtWidgets.QMessageBox.question(self, 'Message',
                                                   "Are you sure you want to delete this event and all its commands?",
                                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                   QtWidgets.QMessageBox.No)

            if reply == QtWidgets.QMessageBox.No:
                printf("EventList.addCommand(): User rejected deleting the event")
                return

        # Delete the event item and it's corresponding event
        del self.events[self.itemWidget(selectedItem)]
        self.takeItem(self.currentRow())

    def replaceEvent(self):
        printf("EventList.replaceEvent(): Changing selected event")

        # Get the current item it's corresponding event
        selectedItem = self.getSelectedEventItem()
        if selectedItem is None:
            QtWidgets.QMessageBox.question(self, 'Error', 'You need to select an event to change',
                                           QtWidgets.QMessageBox.Ok)
            return

        # Get the replacement event from the user
        eventPrompt = EventPromptWindow(parent=self)
        if not eventPrompt.accepted:
            printf("EventList.replaceEvent():User rejected the prompt.")
            return
        eventType = eventPrompt.chosenEvent
        params = eventPrompt.chosenParameters

        # Make sure this event does not already exist
        for e in self.events.values():
            if isinstance(e, eventType) and (e.parameters == params or params is None):
                printf("EventList.addEvent(): Event already exists, disregarding user input.")
                return

        # Actually change the event to the new type
        newEvent = eventType(params)
        newEvent.commandList = self.getEvent(selectedItem).commandList  # self.events[selectedItem].commandList

        # Transfer the item widget and update the looks
        oldWidget = self.itemWidget(selectedItem)
        newEvent.dressWidget(oldWidget)

        # Update the self.events dictionary with the new event
        self.events[self.itemWidget(selectedItem)] = newEvent

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
        self.clear()  # clear eventList

        # Fill event list with new data
        for index, eventSave in enumerate(data):
            commandList = CommandList(parent=self)
            commandList.loadData(eventSave['commandList'], shared)
            self.addEvent(eventSave['type'], commandList=commandList, parameters=eventSave["parameters"])

        # Select the first event for viewing
        if self.count() > 0: self.setCurrentRow(0)


class CommandList(QtWidgets.QListWidget):
    def __init__(self, parent):  # Todo: make commandList have a parent
        super(CommandList, self).__init__()
        # GLOBALS
        self.commands = {}  # Dictionary of commands. Ex: {QListItem: MoveXYZCommand, QListItem: PickupCommand}
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setAcceptDrops(True)

        self.itemDoubleClicked.connect(self.doubleClickEvent)  # For opening the widget's window
        self.itemClicked.connect(self.clickEvent)

        # The following defines a function that returns a dictionary of the commands, in the correct order
        self.getCommandsOrdered = lambda: [self.getCommand(self.item(index)) for index in range(self.count())]

        self.initUI()

    def initUI(self):
        self.setMinimumWidth(250)

    def deleteSelected(self):
        for item in self.selectedItems():
            del self.commands[self.itemWidget(item)]
            self.takeItem(self.row(item))

    def refresh(self):
        # commandsOrdered = self.getCommandsOrdered()
        zeroAndAbove = lambda i: (i < 0) * 0 + (i >= 0) * i
        indent = 0

        for index in range(self.count()):
            command = self.getCommand(self.item(index))
            commandWidget = self.itemWidget(self.item(index))

            if type(command) is StartBlockCommand:
                indent += 1

            commandWidget.setIndent(zeroAndAbove(indent))
            command.indent = zeroAndAbove(indent)

            if type(command) is EndBlockCommand:
                indent -= 1

        # Update the width of the commandList to the widest element within it
        # This occurs whenever items are changed, or added, to the commandList
        if self.sizeHintForColumn(0) + 10 < 1300:
            self.setMinimumWidth(self.sizeHintForColumn(0) + 10)

    def getCommand(self, listWidgetItem):
        return self.commands[self.itemWidget(listWidgetItem)]

    def addCommand(self, commandType, shared, parameters=None):
        # If adding a pre-filled command (used when loading a save)

        if parameters is None:
            newCommand = commandType(self, shared)
        else:
            newCommand = commandType(self, shared, parameters=parameters)

        # Fill command with information either by opening window or loading it in
        if parameters is None:  # If none, then this is being added by the user and not the system loading a file
            newCommand.openView()  # Get information from user
            if not newCommand.accepted:
                printf("CommandList.addCommand(): User rejected prompt")
                return
        else:
            newCommand.parameters = parameters

        # Create the widget to be placed inside the listWidgetItem
        newWidget = CommandWidget(self, self.deleteSelected)
        newWidget = newCommand.dressWidget(newWidget)  # Dress up the widget

        # Create the list widget item
        listWidgetItem = QtWidgets.QListWidgetItem(self)
        listWidgetItem.setSizeHint(newWidget.sizeHint())  # Widget will not appear without this line
        self.addItem(listWidgetItem)

        # Add list widget to commandList
        self.setItemWidget(listWidgetItem, newWidget)

        # Add the new command to the list of commands, linking it with its corresponding listWidgetItem
        self.commands[newWidget] = newCommand

        # Update the width of the commandList to the widest element within it
        self.refresh()

    def keyPressEvent(self, event):
        # Delete selected items when delete key is pressed
        if event.key() == QtCore.Qt.Key_Delete:
            self.deleteSelected()

    def dropEvent(self, event):
        self.refresh()
        event.setDropAction(QtCore.Qt.MoveAction)

        super(CommandList, self).dropEvent(event)
        self.refresh()
        # lst = [i.text() for i in self.findItems('', QtCore.Qt.MatchContains)]

    def doubleClickEvent(self, clickedItem):
        # Open the command window for the command that was just double clicked
        printf("CommandList.doubleClickEvent(): Opening double clicked command")

        command = self.getCommand(clickedItem)
        command.openView()

        # Update the widget to match the new parameters
        command.getInfo()

        # Update the current itemWidget to match the new parameters
        currentWidget = self.itemWidget(clickedItem)  # Get the current itemWidget
        command.dressWidget(currentWidget)

        self.refresh()

    def clickEvent(self, clickedItem):
        for i in range(self.count()):
            item = self.item(i)
            self.itemWidget(item).setFocused(False)

        self.itemWidget(clickedItem).setFocused(True)
        self.refresh()

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
        # Clear all data on the current list
        self.commands = {}
        self.clear()

        # Fill the list with new data
        for index, commandInfo in enumerate(data):
            type = commandInfo["type"]
            parameters = commandInfo["parameters"]
            self.addCommand(type, shared, parameters=parameters)
        self.refresh()
