import copy
from RobotGUI.Events   import *
from RobotGUI.Commands import *
from RobotGUI.Global   import printf, FpsTimer
from threading         import Thread
from PyQt5             import QtCore, QtWidgets



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
        self.__robotObj = robot

        # Used in the motion detection event, ColorTrackCommand, etc
        self.__visionObj = vision

        # Used in the motion detection event to get the motionCalibration settings
        self.__settingsObj = settings

    def getRobot(self):
        return self.__robotObj

    def getVision(self):
        return self.__visionObj

    def getSettings(self):
        return self.__settingsObj


class ControlPanel(QtWidgets.QWidget):
    """
    ControlPanel:

    Purpose: A nice clean widget that has both the EventList and CommandList displayed, and the "AddEvent" and
            "AddCommand" buttons. It is a higher level of abstraction for the purpose of handling the running of the
            robot program, instead of the nitty gritty details of the commandList and eventList.

            It's my attempt at seperating the Logic and GUI sides of things a tiny bit. It was a failed attempt, but I
            think it's still helpful for organization.
    """

    def __init__(self, robot, vision, settings, parent):
        super(ControlPanel, self).__init__(parent)

        # Set up Globals
        self.shared     = Shared(robot, vision, settings)

        self.running    = False  # Whether or not the main thread should be running or not
        self.mainThread = None   # This holds the 'Thread' object of the main thread.
        self.eventList  = EventList(self.shared, self.refresh, parent=self)

        self.commandMenuWidget = CommandMenuWidget(self.eventList.addCommand, parent=self)
        self.commandListStack = QtWidgets.QStackedWidget()

        self.initUI()

    def initUI(self):
        # Set Up Buttons and their text
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

        # Create the button horizontal layout for the 'delete' and 'change' buttons
        btnRowHLayout = QtWidgets.QHBoxLayout()
        btnRowHLayout.addWidget(deleteEventBtn)
        btnRowHLayout.addWidget(changeEventBtn)

        # Create a vertical layout for the buttons (top) and the eventList (bottom)
        eventVLayout = QtWidgets.QVBoxLayout()
        eventVLayout.addWidget(addEventBtn)
        eventVLayout.addLayout(btnRowHLayout)
        eventVLayout.addWidget(self.eventList)

        # Create a layout to hold the 'addCommand' button and the 'commandList'
        commandVLayout = QtWidgets.QVBoxLayout()
        commandVLayout.addWidget(self.commandListStack)
        addCmndVLayout = QtWidgets.QVBoxLayout()

        # Add the addCommand button and a placeholder commandLIst
        addCmndVLayout.addWidget(self.commandMenuWidget)
        addCmndVLayout.addStretch(1)
        # self.commandListStack.addWidget(CommandList(parent=self))

        # Put the eventLIst layout and the commandLayout next to eachother
        mainHLayout = QtWidgets.QHBoxLayout()
        mainHLayout.addLayout(eventVLayout)
        mainHLayout.addLayout(commandVLayout)
        mainHLayout.addLayout(addCmndVLayout)

        self.setLayout(mainHLayout)
        self.show()

    def refresh(self):
        """
        Refresh which commandList is currently being displayed to the one the user has highlighted. It basically just
        goes over certain things and makes sure that everything that should be displaying, is displaying.
        """

        # Get the currently selected event on the eventList
        selectedEvent = self.eventList.getSelectedEvent()

        # Delete all widgets on the commandList stack
        for c in range(0, self.commandListStack.count()):
            widget = self.commandListStack.widget(c)
            self.commandListStack.removeWidget(widget)

        # If user has no event selected, make a clear commandList to view
        if selectedEvent is None:
            printf("ControlPanel.refresh():ERROR: no event selected!")
            # clearList = CommandList(parent=self)
            # self.commandListStack.addWidget(clearList)
            # self.commandListStack.setCurrentWidget(clearList)
            return

        # Add and display the correct widget
        self.commandListStack.addWidget(selectedEvent.commandList)
        self.commandListStack.setCurrentWidget(selectedEvent.commandList)

    def addEvent(self):
        self.eventList.promptUser()

    def deleteEvent(self):
        self.eventList.deleteEvent()

    def replaceEvent(self):
        self.eventList.replaceEvent()


    def closeEvent(self, event):
        # Do things here like closing threads and such
        self.endThread()


    # LOGIC
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
        # This is where the script you create actually gets run. This is run on a seperate thread, self.mainThread

        printf("ControlPanel.programThread(): #################### STARTING PROGRAM THREAD! ######################")
        self.shared.getRobot().setServos(servo1=True, servo2=True, servo3=True, servo4=True)
        self.shared.getRobot().refresh()

        # Deepcopy all of the events, so that every time you run the script it runs with no modified variables
        events = copy.copy(self.eventList.getEventsOrdered())

        # color = QtGui.QColor(150, 255, 150)
        # transparent = QtGui.QColor(QtCore.Qt.transparent)
        # eventItem   = self.eventList.getItemsOrdered()
        # setColor    = lambda item, isColored: item.setBackground((transparent, color)[isColored])

        timer = FpsTimer(fps=10)

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
            self.shared.getRobot().refresh()

        # #Turn each list item transparent once more
        # for item in eventItem:
        #     pass
        #     #setColor(item, False)
        #     #item.setBackground(QtGui.QColor(QtCore.Qt.transparent))


        # Check if there is a DestroyEvent command. If so, run it
        destroyEvent = list(filter(lambda event: type(event) == DestroyEvent, events))
        if len(destroyEvent): self.interpretCommands(destroyEvent[0].commandList)

        self.shared.getRobot().setGripper(False)
        self.shared.getRobot().refresh()

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

        while index < len(commandsOrdered):
            command = commandsOrdered[index]
            ret = command.run(self.shared)

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


    def getSaveData(self):
        return self.eventList.getSaveData()

    def loadData(self, data):
        self.eventList.loadData(data, self.shared)


class EventList(QtWidgets.QListWidget):
    def __init__(self, shared, refreshControlPanel, parent):

        self.shared = shared # used in self.addCommand only

        super(EventList, self).__init__(parent)

        # GLOBALS
        self.refreshControlPanel = refreshControlPanel
        self.events = {}  # A hash map of the current events in the list. The listWidget leads to the event object

        # IMPORTANT This makes sure the ControlPanel refreshes whenever you click on an item in the list,
        # in order to display the correct commandList for the event that was clicked on.
        self.itemSelectionChanged.connect(self.refreshControlPanel)

        # The following is a function that returns a dictionary of the events, in the correct order
        self.getEventsOrdered = lambda: [self.getEvent(self.item(index)) for index in range(self.count())]
        self.getItemsOrdered  = lambda: [self.item(index) for index in range(self.count())]

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
        """
        This gets the "widget" for the currently selected event item, not the Event() object
        """

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
        # Get the Event() object for any events listWidgetItem

        return self.events[self.itemWidget(listWidgetItem)]


    def promptUser(self):
        # Open the eventPromptWindow to ask the user what event they wish to create

        eventPrompt = EventPromptWindow(self)
        if eventPrompt.accepted:
            self.addEvent(eventPrompt.chosenEvent, parameters=eventPrompt.chosenParameters)
        else:
            printf("EventList.promptUser():User rejected the prompt.")


    def addCommand(self, type):
        # When the addCommand button is pressed, add that command to the currently selected

        printf("ControlPanel.addCommand(): Add Command button clicked. Adding command!")

        selectedEvent = self.getSelectedEvent()
        if selectedEvent is None:
            # This occurs when there are no events on the table. Display warning to user in this case.
            printf("ControlPanel.addCommand(): ERROR: Selected event does not have a commandList! Displaying error")
            QtWidgets.QMessageBox.question(self, 'Error', 'You need to select an event or add an event before you can '
                                                          'add commands', QtWidgets.QMessageBox.Ok)
            return

        selectedEvent.commandList.addCommand(type)

    def addEvent(self, eventType, shared, **kwargs):
        """

        :param eventType:
        :param kwargs:
            'parameters' for an event, to fill it in automatically, for loading a file
            'commandListSave' for an event, if you have commandList save to load into it, then it will generate the list
        :return: Nothing
        """

        params = kwargs.get("parameters", None)

        # Check if the event being added already exists in the self.events dictionary
        for item in self.events.items():
            if isinstance(item, eventType) and (item.parameters == params or params is None):
                printf("EventList.addEvent(): Event already exists, disregarding user input.")
                return

        newEvent        = eventType(params)
        commandListSave = kwargs.get("commandListSave", [])
        newCommandList = CommandList(self.shared, parent=self)
        newCommandList.loadData(commandListSave, shared)
        newEvent.commandList =  newCommandList
        # newEvent.commandList = kwargs.get("commandListData", CommandList(self.shared, parent=self))

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
        # Replace one event with another, while keeping the same commandList

        printf("EventList.replaceEvent(): Changing selected event")

        # Get the current item it's corresponding event
        selectedItem = self.getSelectedEventItem()
        if selectedItem is None:
            QtWidgets.QMessageBox.question(self, 'Error', 'You need to select an event to change',
                                           QtWidgets.QMessageBox.Ok)
            return

        # Get the type of event you will be replacing the selected event with
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
        """
        Save looks like
            [
            {"type": eventType, "parameters" {event parameters}, "commandList" [commandList]},
            {"type": eventType, "parameters" {event parameters}, "commandList" [commandList]},
            {"type": eventType, "parameters" {event parameters}, "commandList" [commandList]},
            ]
        :return:
        """

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
            # commandList = CommandList(parent=self)
            # commandList.loadData(eventSave['commandList'], shared)

            self.addEvent(eventSave['type'], shared, commandListSave=eventSave['commandList'], parameters=eventSave["parameters"])

        # Select the first event for viewing
        if self.count() > 0: self.setCurrentRow(0)
        self.refreshControlPanel()


class CommandList(QtWidgets.QListWidget):
    def __init__(self, shared, parent):  # Todo: make commandList have a parent
        super(CommandList, self).__init__()

        self.shared = shared  # Should just be used in addCommand
        
        # GLOBALS
        self.commands = {}  # Dictionary of commands. Ex: {QListItem: MoveXYZCommand, QListItem: PickupCommand}

        # Set up the drag/drop parameters (both for dragging within the commandList, and dragging from outside
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
        # Delete all highlighted commands

        for item in self.selectedItems():
            del self.commands[self.itemWidget(item)]
            self.takeItem(self.row(item))

    def refresh(self):
        # Refreshes the order and indenting of the CommandList

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
        # Get the Command class for the given listWidgetItem
        return self.commands[self.itemWidget(listWidgetItem)]

    def addCommand(self, commandType, parameters=None):
        # If adding a pre-filled command (used when loading a save)

        if parameters is None:
            newCommand = commandType(self, self.shared)
        else:
            newCommand = commandType(self, self.shared, parameters=parameters)

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


    # For deleting items
    def keyPressEvent(self, event):
        # Delete selected items when delete key is pressed
        if event.key() == QtCore.Qt.Key_Delete:
            self.deleteSelected()


    # For clicking and dragging Command Buttons into the list, and moving items within the list
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            super(CommandList, self).dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            super(CommandList, self).dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasText():
            print("Command list receieved drop of", event)
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()

        else:
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
            commandSave = {"type": type(command), "parameters": command.parameters}
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
            self.addCommand(type, parameters=parameters)
        self.refresh()
