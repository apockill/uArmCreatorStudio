import ast  # To check if a statement is python parsible, for evals
import re   # For variable santization
from CameraGUI    import CameraSelector
from PyQt5        import QtGui, QtCore, QtWidgets
from Logic        import Paths
from Logic.Global import printf
from CommonGUI    import ScriptWidget


# This should only be used once, in CommandList.addCommand
class CommandWidget(QtWidgets.QWidget):
    def __init__(self, parent, onDeleteFunction):
        super(CommandWidget, self).__init__(parent)

        # Set up Globals
        self.indent = 0
        self.margins = None  # Is set after initUI creates it's first layout
        # Set up UI Globals
        self.title       = QtWidgets.QLabel()
        self.description = QtWidgets.QLabel()
        self.icon        = QtWidgets.QLabel("No Icon XFound")
        self.deleteBtn   = QtWidgets.QPushButton("")


        self.initUI()
        self.margins = self.layout().getContentsMargins()  # Has to be after initUI()
        self.setIndent(0)

        # Connect the delete button with a function in the CommandList widget that will delete selected commands
        self.deleteBtn.clicked.connect(onDeleteFunction)

    def initUI(self):
        # Create the delete button
        self.deleteBtn.setFlat(True)
        self.deleteBtn.setIcon(QtGui.QIcon(Paths.delete))
        self.deleteBtn.setVisible(False)

        bold = QtGui.QFont()
        bold.setBold(True)
        self.title.setFont(bold)

        leftLayout = QtWidgets.QVBoxLayout()
        midLayout = QtWidgets.QVBoxLayout()
        rightLayout = QtWidgets.QVBoxLayout()

        leftLayout.addWidget(self.icon)

        midLayout.setSpacing(1)
        midLayout.addWidget(self.title)
        midLayout.addWidget(self.description)

        rightLayout.addWidget(self.deleteBtn)
        rightLayout.setAlignment(QtCore.Qt.AlignRight)

        mainHLayout = QtWidgets.QHBoxLayout()
        mainHLayout.addLayout(leftLayout)
        mainHLayout.addLayout(midLayout, QtCore.Qt.AlignLeft)
        mainHLayout.addLayout(rightLayout, QtCore.Qt.AlignRight)

        self.setLayout(mainHLayout)

    def setFocused(self, isFocused):
        # Determines whether or not the delete button is visible. Should only be visible when widget is clicked
        if isFocused:
            self.deleteBtn.setVisible(True)
        else:
            self.deleteBtn.setVisible(False)

    def setIndent(self, indent):
        if self.indent == indent: return  # If no indent change has been detected, ignore.

        self.indent = indent
        if indent >= 0:
            # Indent the margin on the left, to push the block of code and simulate an 'indent'
            self.layout().setContentsMargins(self.margins[0] + 25 * indent,
                                             self.margins[1],
                                             self.margins[2],
                                             self.margins[3])
        else:
            # Reset the margins to the default setting
            self.layout().setContentsMargins(self.margins[0],
                                             self.margins[1],
                                             self.margins[2],
                                             self.margins[3])

    # The following are accessed only by Command.dressWidget()
    def setTitle(self, text):
        self.title.setText(text)

    def setDescription(self, text):
        self.description.setText(text)

    def setIcon(self, icon):
        self.icon.setPixmap(QtGui.QPixmap(icon))

    def setTip(self, text):
        self.setToolTip(text)


class CommandMenuWidget(QtWidgets.QTabWidget):
    def __init__(self, parent):
        super(CommandMenuWidget, self).__init__(parent)

        # addCmndFunc is a function passed from ControlPanel to be able to hook buttons to that function
        self.initUI()

    def initUI(self):

        self.addTab( self.generateBasicTab(), "Basic")
        self.addTab(self.generateVisionTab(), "Vision")
        self.addTab( self.generateLogicTab(), "Logic")

        self.setTabPosition(QtWidgets.QTabWidget.East)
        self.setFixedWidth(85)



    def generateBasicTab(self):
        tabWidget = QtWidgets.QWidget()
        vBox = QtWidgets.QVBoxLayout()
        vBox.setAlignment(QtCore.Qt.AlignTop)
        tabWidget.setLayout(vBox)
        add  = lambda btnType: vBox.addWidget(self.getButton(btnType))

        add(MoveXYZCommandGUI)
        add(MoveWristCommandGUI)
        add(MotionRecordingCommandGUI)
        add(SpeedCommandGUI)
        add(AttachCommandGUI)
        add(DetachCommandGUI)
        add(GripCommandGUI)
        add(DropCommandGUI)
        add(WaitCommandGUI)
        add(BuzzerCommandGUI)


        return tabWidget

    def generateVisionTab(self):
        tabWidget = QtWidgets.QWidget()
        vBox = QtWidgets.QVBoxLayout()
        vBox.setAlignment(QtCore.Qt.AlignTop)
        tabWidget.setLayout(vBox)
        add  = lambda btnType: vBox.addWidget(self.getButton(btnType))
        add(VisionMoveXYZCommandGUI)
        add(MoveRelativeToObjectCommandGUI)
        add(MoveWristRelativeToObjectCommandGUI)
        add(PickupObjectCommandGUI)
        add(TestObjectSeenCommandGUI)
        add(TestObjectLocationCommandGUI)

        return tabWidget

    def generateLogicTab(self):
        tabWidget = QtWidgets.QWidget()
        vBox = QtWidgets.QVBoxLayout()
        vBox.setAlignment(QtCore.Qt.AlignTop)
        tabWidget.setLayout(vBox)
        add  = lambda btnType: vBox.addWidget(self.getButton(btnType))

        add(ScriptCommandGUI)
        add(SetVariableCommandGUI)
        add(TestVariableCommandGUI)
        add(ElseCommandGUI)
        add(StartBlockCommandGUI)
        add(EndBlockCommandGUI)
        add(EndEventCommandGUI)
        add(EndProgramCommandGUI)



        return tabWidget


    def getButton(self, commandType):
        newButton = self.DraggableButton(str(commandType.__name__), self)
        newButton.setIcon(QtGui.QIcon(commandType.icon))
        newButton.setIconSize(QtCore.QSize(32, 32))
        newButton.setToolTip(commandType.tooltip)

        newButton.customContextMenuRequested.connect(lambda: self.addCommandFunc(commandType))
        return newButton

    class DraggableButton(QtWidgets.QPushButton):
        def __init__(self, dragData, parent):
            super().__init__(parent)
            self.dragData = dragData  # The information that will be transfered upon drag

            self.mouse_down = False  # Has a left-click happened yet?
            self.mouse_posn = QtCore.QPoint()  # If so, this is where...
            self.mouse_time = QtCore.QTime()  # ... and this is when

        def mousePressEvent(self, event):
            if event.button() == QtCore.Qt.LeftButton:
                self.mouse_down = True  # we are left-clicked-upon
                self.mouse_posn = event.pos()  # here and...
                self.mouse_time.start()  # ...now

            event.ignore()
            super().mousePressEvent(event)  # pass it on up

        def mouseMoveEvent(self, event):
            if self.mouse_down:
                # Mouse left-clicked and is now moving. Is this the start of a
                # drag? Note time since the click and approximate distance moved
                # since the click and test against the app's standard.

                t = self.mouse_time.elapsed()
                d = (event.pos() - self.mouse_posn).manhattanLength()

                if t >= QtWidgets.QApplication.startDragTime() or d >= QtWidgets.QApplication.startDragDistance():

                    # Yes, a proper drag is indicated. Commence dragging.
                    self.dragEvent(QtCore.Qt.CopyAction | QtCore.Qt.MoveAction)
                    event.accept()
                    return

            # Move does not (yet) constitute a drag, ignore it.
            event.ignore()
            super().mouseMoveEvent(event)

        def dragEvent(self, actions):
            # Taken straight from Qt documentation

            # Create the QDrag object
            dragster = QtGui.QDrag(self)

            # Make a scaled pixmap of our widget to put under the cursor.
            thumb = self.grab()  # .scaledToHeight(32)
            dragster.setPixmap(thumb)
            dragster.setHotSpot(QtCore.QPoint(thumb.width() / 2, thumb.height() / 2))

            # Create some data to be dragged and load it in the dragster.
            md = QtCore.QMimeData()
            md.setText(self.dragData)
            dragster.setMimeData(md)

            # Initiate the drag, which really is a form of modal dialog.
            # Result is supposed to be the action performed at the drop.
            act = dragster.exec_(actions)
            defact = dragster.defaultAction()

            # Display the results of the drag.
            targ = dragster.target()  # s.b. the widget that received the drop
            src = dragster.source()  # s.b. this very widget

            return


class CommandGUI:
    tooltip = ''
    icon = ''
    title = ''

    defaultTextBoxWidth = 130

    def __init__(self, parameters):
        self.description = ""
        self.parameters = parameters  # For commands with no parameters, this should stay empty

    def openWindow(self):  # Open window

        # If this object has no window object, then skip this process and return true (ei, StartBlockCommand)
        if self.parameters is None:
            # printf("About to execute self...", self, super(Command, self), self.parent)
            return True

        ##### Create the base window #####
        prompt = QtWidgets.QDialog()


        # Create the apply/cancel buttons, connect them, and format them
        prompt.applyBtn = QtWidgets.QPushButton('Apply')
        cancelBtn       = QtWidgets.QPushButton('Cancel')
        prompt.applyBtn.setMaximumWidth(100)
        cancelBtn.setMaximumWidth(100)
        prompt.applyBtn.clicked.connect(prompt.accept)
        cancelBtn.clicked.connect(prompt.reject)
        prompt.applyBtn.setDefault(True)


        # Create a content box for the command to fill out parameters and GUI elements
        prompt.content    = QtWidgets.QVBoxLayout()
        prompt.content.setContentsMargins(20, 10, 20, 10)
        contentGroupBox = QtWidgets.QGroupBox("Parameters")
        contentGroupBox.setLayout(prompt.content)


        # Now that the window is 'dressed', add "Cancel" and "Apply" buttons
        buttonRow = QtWidgets.QHBoxLayout()
        buttonRow.addWidget(cancelBtn)
        buttonRow.addStretch(1)
        buttonRow.addWidget(prompt.applyBtn)


        # Create the main vertical layout, add everything to it
        prompt.mainVLayout = QtWidgets.QVBoxLayout()
        prompt.mainVLayout.addWidget(contentGroupBox)
        prompt.mainVLayout.addStretch(1)


        # Set the main layout and general window parameters
        prompt.setMinimumWidth(350)
        prompt.setMinimumHeight(350)
        prompt.setLayout(prompt.mainVLayout)
        prompt.setWindowTitle(self.title)
        prompt.setWindowIcon(QtGui.QIcon(self.icon))
        prompt.setWhatsThis(self.tooltip)  # This makes the "Question Mark" button on the window show the tooltip msg


        # Dress the base window (this is where the child actually puts the content into the widget)
        prompt = self.dressWindow(prompt)

        prompt.mainVLayout.addLayout(buttonRow)  # Add button after, so hints appear above buttons

        # Run the info window and prevent other windows from being clicked while open:
        accepted = prompt.exec_()

        # Make sure QT properly handles the memory after this function ends
        prompt.close()
        prompt.deleteLater()


        # Get information that the user input
        if accepted:
            # Get information that the user input
            self._extractPromptInfo(prompt)

            # Update self.description for the widget to be dressed with after, by CommandList
            self._updateDescription()
            printf("New parameters: ", self.parameters)

        else:
            printf("User Canceled.")




        return accepted

    def dressWidget(self, newWidget):
        self._updateDescription()

        newWidget.setIcon(self.icon)
        newWidget.setTitle(self.title)
        newWidget.setTip(self.tooltip)
        newWidget.setDescription(self.description)
        return newWidget


    # The following functions should be empty, and only are there so that subclasses without them don't cause errors
    def _updateDescription(self):
        # This is called in openView() and will update the decription to match the parameters
        pass


    # The following are helper functions for general CommandGUI children purposes
    def _sanitizeEval(self, inputTextbox, fallback):
        """
        Checks if the eval statement is python-parsible. If it is not, it will return the "fallback" value.
        """
        # Makes sure that the statement is parseable by python

        inputCode = inputTextbox.text()
        inputCode = inputCode.replace('^', '**')

        try:
            ast.parse(inputCode)
        except SyntaxError:
            return fallback
        return inputCode

    def _sanitizeVariable(self, inputTextbox, fallback):
        # Sanitize input from the user
        possibleVariable = str(inputTextbox.text())

        # Remove invalid characters
        possibleVariable = re.sub('[^0-9a-zA-Z_]', '', possibleVariable)

        # Remove leading characters until we find a letter or underscore
        possibleVariable = re.sub('^[^a-zA-Z_]+', '', possibleVariable)


        # If the variable has been changed, then it was not valid, so return the "fallback" instead.
        if not possibleVariable == inputTextbox.text():
            return fallback

        return possibleVariable


    # The following are helper functions for modifying the prompt window in a consistent way
    def _addRow(self, prompt, *args, alignRight=True):
        # If any argument is of the following type, then set the width to self.defaultTextBoxWidth
        setWidthOnTypes = [QtWidgets.QLineEdit, QtWidgets.QComboBox, QtWidgets.QPushButton]

        row = QtWidgets.QHBoxLayout()

        # Push objects together, otherwise keep it centered
        if alignRight: row.addStretch(1)

        for widget in args:
            # Set the width if it is a typ
            if type(widget) in setWidthOnTypes:   # any([isinstance(widget, wType) for wType in  setWidthOnTypes]):
                widget.setFixedWidth(self.defaultTextBoxWidth)

            # Creates and adds a row to prompt.content, with proper formatting
            row.addWidget(widget)

        prompt.content.addLayout(row)

    def _addSpacer(self, prompt):
        """
        Add a certain amount of pixels of spacing between two rows in the prompt window
        """

        height = 20
        column = QtWidgets.QVBoxLayout()
        column.addSpacing(height)
        prompt.content.addLayout(column)

    def _addHint(self, prompt, hintText):
        """
        Add some text (usually at the bottom of the prompt) that tells the user something to help them out
        HintText is bolded by default, and always appears in the same spot.
        """

        prompt.hintLbl = QtWidgets.QLabel(hintText)
        prompt.hintLbl.setWordWrap(True)

        # Make the hint bold
        bold = QtGui.QFont()
        bold.setBold(True)
        prompt.hintLbl.setFont(bold)

        # Create a row for the hint
        hintRow = QtWidgets.QHBoxLayout()
        # hintRow.addStretch(1)
        hintRow.addWidget(prompt.hintLbl)

        # Add it to the prompt
        prompt.mainVLayout.addLayout(hintRow)

    def _addObjectHint(self, prompt, numResources):
        """
        This is a hint that goes onto any command that asks the user to choose from a vision object. It tells them
        that they can create objects in the Resource Manager
        """
        # If there are no objects, place a nice label to let the user know
        if numResources == 0:
            hintText = "You have not created any trackable objects yet." + \
                       "\nTry adding new objects in the Resource Manager!"
            self._addHint(prompt, hintText)
        elif numResources == 1:
            hintText = "It looks like you've only created one object." + \
                       " Feel free to add new objects in the Resource Manager!"
            self._addHint(prompt, hintText)

    def _addRecordingHint(self, prompt, numResources):
        """
        This is a hint that goes onto any command that uses motion recordings, to warn the user if they have not
        created any motion recordings
        """

        if numResources == 0:
            hintText = "You have not created any Motion Recordings yet. " + \
                       "Try creating new recordings in the Resource Manager!"
            self._addHint(prompt, hintText)




########## COMMANDS ##########
"""
Commands must have:
    - A class, here in CommandsGUI.py
    - A logic implimentation under Commands.py with a run() function
    - Be added to the CommandMenuWidget.initUI() function in order for the user to add it to their programs
    - Variables
        - tooltip
        - icon
        - logicPair (a string of the class name of its logic counterpart in commands.py, for interpreter use only)
        - title   (Except for certain functions, such as StartBlockCommand)
    - Functions
        - init(shared, parameters=None) function
            - Must calls super(NAME, self).__init__(parent)
        - If the command has a description, it must have a updateDescription() method
        - If the command has a window, it must have the following methods:
            - dressWindow(prompt)
            - extractPromptInfo(prompt)

Special Cases:
    -StartBlockCommand and EndBlockCommand are used directly in ControlPanelGUI.py to indent code blocks correctly
    -ElseCommand is used directly in the Interpreter for processing code
    -Test commands should be entered in ControlPanelGUI.CommandList.dropEvent() so that when it is dropped, a
        StartBlockCommand and EndBlockCommand is placed after it, for the users convenience

Example of a fully filled out class:

class NameCommandGUI(CommandGUI):
    title     = "Example Title"
    tooltip   = "This tool does X Y and Z"
    icon      = Paths.some_icon
    logicPair = "NameCommand"

    def __init__(self, env, parameters=None):
        super(NameCommandGUI, self).__init__(parameters)

        # If parameters do not exist, then set up the default parameters
        if self.parameters is None:
            # Anything done with env should be done here. Try not to save env as a class variable whenever possible
            self.parameters = {}

    def dressWindow(self, prompt):
        # Do some GUI code setup
        # Put all the objects into horizontal layouts called Rows

        self._addRow(prompt, some GUI label, some GUI object)  # Add rows using self._addRow to keep consistency

        return prompt

    def _extractPromptInfo(self, prompt):
        newParameters = {} # Get the parameters from the 'prompt' GUI elements. Put numbers through self.sanitizeFloat

        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        self.description = ""  # Some string that uses your parameters to describe the object.

"""

#   BASIC CONTROL COMMANDS
class MoveXYZCommandGUI(CommandGUI):
    title     = "Move XYZ"
    tooltip   = "Set the robots position.\nThe robot will move after all events are evaluated.\n\n"\
                "If you don't want to set one of the robots axis, simply leave it empty. For example, put y and z \n"\
                "empty and x to 5 will set the robots x position to 5 while keeping the current Y and Z the same."
    icon      = Paths.command_xyz
    logicPair = 'MoveXYZCommand'

    def __init__(self, env, parameters=None):
        super(MoveXYZCommandGUI, self).__init__(parameters)
        self.getCoordinates = env.getRobot().getCoords

        if self.parameters is None:
            # If no parameters were given, it's a new command. Thus, get the robots current position and fill it in.
            # This helps with workflow so you can create MoveXYZ commands and move the robot around as you work with it
            currentXYZ = self.getCoordinates()

            self.parameters = {'x': round(currentXYZ[0], 1),
                               'y': round(currentXYZ[1], 1),
                               'z': round(currentXYZ[2], 1),
                               'relative': False}

    def dressWindow(self, prompt):
        # Prompt is a QDialog type, this is simply a function to dress it up with the appropriate interface
        # Then it's returned, and the Command.openView() function will open the window and perform appropriate actions
        def setCoordinates(xEdt, yEdt, zEdt):
            x, y, z = self.getCoordinates()
            xEdt.setText(str(x))
            yEdt.setText(str(y))
            zEdt.setText(str(z))

        # Input: the base window with the cancel and apply buttons, and the layouts set up and connected
        getCurrBtn      = QtWidgets.QPushButton("Get Position")
        prompt.xEdit    = QtWidgets.QLineEdit()  # Rotation textbox
        prompt.yEdit    = QtWidgets.QLineEdit()  # Stretch textbox
        prompt.zEdit    = QtWidgets.QLineEdit()  # Height textbox
        prompt.ovrCheck = QtWidgets.QCheckBox()  # "override" CheckBox
        prompt.rltCheck = QtWidgets.QCheckBox()  # "relative" CheckBox

        getCurrBtn.clicked.connect(lambda: setCoordinates(prompt.xEdit, prompt.yEdit, prompt.zEdit))

        # Set up all the labels for the inputs
        xLabel = QtWidgets.QLabel('X ')
        yLabel = QtWidgets.QLabel('Y ')
        zLabel = QtWidgets.QLabel('Z ')
        rltCheck = QtWidgets.QLabel('Relative: ')


        # Fill the textboxes with the default parameters
        prompt.xEdit.setText(str(self.parameters['x']))
        prompt.yEdit.setText(str(self.parameters['y']))
        prompt.zEdit.setText(str(self.parameters['z']))
        prompt.rltCheck.setChecked(self.parameters['relative'])

        self._addRow(prompt, getCurrBtn)
        self._addRow(prompt, xLabel, prompt.xEdit)
        self._addRow(prompt, yLabel, prompt.yEdit)
        self._addRow(prompt, zLabel, prompt.zEdit)
        self._addRow(prompt, rltCheck, prompt.rltCheck)

        return prompt

    def _extractPromptInfo(self, prompt):
        # Update the parameters and the description
        newParameters = {'x': self._sanitizeEval(prompt.xEdit, self.parameters["x"]),
                         'y': self._sanitizeEval(prompt.yEdit, self.parameters["y"]),
                         'z': self._sanitizeEval(prompt.zEdit, self.parameters["z"]),
                         'relative': prompt.rltCheck.isChecked()}

        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        # Update the description, for the dressWidget() and the openView() prompt
        self.description = 'XYZ( ' + str(self.parameters['x']) + \
                           ', ' + str(self.parameters['y'])    + \
                           ', ' + str(self.parameters['z'])    + ')'

        if self.parameters['relative']: self.description += '   Relative'


class MoveWristCommandGUI(CommandGUI):
    title     = "Set Wrist Angle"
    tooltip   = "This command sets the angle of the robots 4th axis, the wrist."
    icon      = Paths.command_move_wrist
    logicPair = "MoveWristCommand"

    def __init__(self, env, parameters=None):
        super(MoveWristCommandGUI, self).__init__(parameters)
        self.getWristAngle = lambda: env.getRobot().getAngles()[3]

        if self.parameters is None:
            currentWrist = self.getWristAngle()
            self.parameters = {"angle": str(currentWrist),
                               "relative": False}


    def dressWindow(self, prompt):
        def setCurrentAngle(edit):
            angle = self.getWristAngle()
            edit.setText(str(angle))

        # Create what the user will be interacting with
        prompt.wristEdit = QtWidgets.QLineEdit()
        prompt.rltCheck  = QtWidgets.QCheckBox()  # "relative" CheckBox
        currentAngleBtn  = QtWidgets.QPushButton("Get Angle")

        currentAngleBtn.clicked.connect(lambda: setCurrentAngle(prompt.wristEdit))

        # Create the labels for the interactive stuff
        wristLabel       = QtWidgets.QLabel('Wrist Angle:')
        rltLabel         = QtWidgets.QLabel('Relative:')

        # Set up everything so it matches the current parameters
        prompt.wristEdit.setText(  self.parameters["angle"])
        prompt.rltCheck.setChecked(self.parameters["relative"])

        self._addRow(prompt, currentAngleBtn)
        self._addRow(prompt, wristLabel, prompt.wristEdit)
        self._addRow(prompt, rltLabel, prompt.rltCheck)
        return prompt

    def _extractPromptInfo(self, prompt):
        newParameters = {"angle":    self._sanitizeEval(prompt.wristEdit, self.parameters["angle"]),
                         "relative": prompt.rltCheck.isChecked()}

        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        self.description = "Set the wrist position to " + self.parameters["angle"] + " degrees"

        if self.parameters['relative']: self.description += '   Relative'


class MotionRecordingCommandGUI(CommandGUI):
    title     = "Play Motion Recording"
    tooltip   = "This will play back a 'motion recording' at a playback speed of your choosing. To create robot\n" + \
                "motion recordings, simply click on 'Resources' on the toolbar and add a new recording."
    icon      = Paths.command_play_path
    logicPair = "MotionRecordingCommand"

    def __init__(self, env, parameters=None):
        super(MotionRecordingCommandGUI, self).__init__(parameters)

        objManager = env.getObjectManager()
        self.getObjectList = lambda: objManager.getObjectNameList(objFilter=objManager.MOTIONPATH)


        if self.parameters is None:
            self.parameters = {"objectID": "",
                               "reversed": False,
                               "speed": "1.0"}

    def dressWindow(self, prompt):

        # Choose a recording
        choiceLbl = QtWidgets.QLabel("Choose a Recording: ")
        prompt.recChoices = QtWidgets.QComboBox()
        prompt.recChoices.addItem(self.parameters["objectID"])
        recList = self.getObjectList()
        for index, objectID in enumerate(recList): prompt.recChoices.addItem(objectID)
        self._addRow(prompt, choiceLbl, prompt.recChoices)


        # PlaybackSpeed
        speedLbl = QtWidgets.QLabel("Playback Speed: ")
        prompt.speedEdit = QtWidgets.QLineEdit()
        prompt.speedEdit.setText(self.parameters["speed"])
        self._addRow(prompt, speedLbl, prompt.speedEdit)


        # Reversed?
        reversedLbl = QtWidgets.QLabel("Play in reverse?")
        prompt.reverseCheck = QtWidgets.QCheckBox()
        prompt.reverseCheck.setChecked(self.parameters["reversed"])
        self._addRow(prompt, reversedLbl, prompt.reverseCheck)

        self._addRecordingHint(prompt, len(recList))
        return prompt

    def _extractPromptInfo(self, prompt):
        newParameters = {"objectID": str(prompt.recChoices.currentText()),
                         "reversed": prompt.reverseCheck.isChecked(),
                         "speed": self._sanitizeEval(prompt.speedEdit, self.parameters["speed"])}

        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        self.description = "Play motion recording " + self.parameters["objectID"] + " x" + str(self.parameters["speed"])
        if self.parameters["reversed"]: self.description += " reversed"


class SpeedCommandGUI(CommandGUI):
    title     = "Set Speed"
    tooltip   = "This tool sets the speed of the robot for any move commands that are done after this. "
    icon      = Paths.command_speed
    logicPair = "SpeedCommand"

    def __init__(self, env, parameters=None):
        super(SpeedCommandGUI, self).__init__(parameters)

        if self.parameters is None:
            # Some code to set up default parameters
            # robot = env.getRobot()
            self.parameters = {"speed": str(10)}

    def dressWindow(self, prompt):
        prompt.speedEdit = QtWidgets.QLineEdit()

        # Set up all the labels for the inputs
        speedLabel = QtWidgets.QLabel('Speed (cm/s): ')

        # Fill the textboxes with the default parameters
        prompt.speedEdit.setText(str(self.parameters['speed']))

        self._addRow(prompt, speedLabel, prompt.speedEdit)


        return prompt

    def _extractPromptInfo(self, prompt):
        newParameters = {'speed': self._sanitizeEval(prompt.speedEdit, self.parameters['speed'])}

        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        self.description = 'Set robot speed to ' + str(self.parameters['speed']) + " cm/s"


class DetachCommandGUI(CommandGUI):
    title     = "Detach Servos"
    tooltip   = "Disengage the specified servos on the robot"
    icon      = Paths.command_detach
    logicPair = "DetachCommand"

    def __init__(self, env, parameters=None):
        super(DetachCommandGUI, self).__init__(parameters)

        if self.parameters is None:
            self.parameters = {'servo1': True,
                               'servo2': True,
                               'servo3': True,
                               'servo4': True}


    def dressWindow(self, prompt):
        # Do some GUI code setup
        # Put all the objects into horizontal layouts called Rows
        prompt.srvo1Box = QtWidgets.QCheckBox()  # Rotation textbox
        prompt.srvo2Box = QtWidgets.QCheckBox()  # Stretch textbox
        prompt.srvo3Box = QtWidgets.QCheckBox()  # Height textbox
        prompt.srvo4Box = QtWidgets.QCheckBox()  # "relative" CheckBox

        # Set up all the labels for the inputs
        label1 = QtWidgets.QLabel('Base Servo:')
        label2 = QtWidgets.QLabel('Stretch Servo:')
        label3 = QtWidgets.QLabel('Height Servo:')
        label4 = QtWidgets.QLabel('Wrist Servo:')

        # Fill the textboxes with the default parameters
        prompt.srvo1Box.setChecked(self.parameters['servo1'])
        prompt.srvo2Box.setChecked(self.parameters['servo2'])
        prompt.srvo3Box.setChecked(self.parameters['servo3'])
        prompt.srvo4Box.setChecked(self.parameters['servo4'])
        self._addRow(prompt, label1, prompt.srvo1Box)
        self._addRow(prompt, label2, prompt.srvo2Box)
        self._addRow(prompt, label3, prompt.srvo3Box)
        self._addRow(prompt, label4, prompt.srvo4Box)
        return prompt

    def _extractPromptInfo(self, prompt):
        newParameters = {'servo1': prompt.srvo1Box.isChecked(),
                         'servo2': prompt.srvo2Box.isChecked(),
                         'servo3': prompt.srvo3Box.isChecked(),
                         'servo4': prompt.srvo4Box.isChecked()}

        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        descriptionBuild = "Servos"
        if self.parameters["servo1"]: descriptionBuild += "  Base"
        if self.parameters["servo2"]: descriptionBuild += "  Stretch"
        if self.parameters["servo3"]: descriptionBuild += "  Height"
        if self.parameters["servo4"]: descriptionBuild += "  Wrist"

        self.description = descriptionBuild


class AttachCommandGUI(CommandGUI):
    """
    A command for attaching the servos of the robot
    """

    title     = "Attach Servos"
    tooltip   = "Re-engage servos on the robot"
    icon      = Paths.command_attach
    logicPair = "AttachCommand"

    def __init__(self, env, parameters=None):
        super(AttachCommandGUI, self).__init__(parameters)

        if self.parameters is None:
            self.parameters = {'servo1': True,
                               'servo2': True,
                               'servo3': True,
                               'servo4': True}


    def dressWindow(self, prompt):
        # Do some GUI code setup
        # Put all the objects into horizontal layouts called Rows
        prompt.srvo1Box = QtWidgets.QCheckBox()  #  Rotation textbox
        prompt.srvo2Box = QtWidgets.QCheckBox()  #  Stretch textbox
        prompt.srvo3Box = QtWidgets.QCheckBox()  #  Height textbox
        prompt.srvo4Box = QtWidgets.QCheckBox()  #  "relative" CheckBox

        # Set up all the labels for the inputs
        label1 = QtWidgets.QLabel('Base Servo:')
        label2 = QtWidgets.QLabel('Stretch Servo:')
        label3 = QtWidgets.QLabel('Height Servo:')
        label4 = QtWidgets.QLabel('Wrist Servo:')

        # Fill the textboxes with the default parameters
        prompt.srvo1Box.setChecked(self.parameters['servo1'])
        prompt.srvo2Box.setChecked(self.parameters['servo2'])
        prompt.srvo3Box.setChecked(self.parameters['servo3'])
        prompt.srvo4Box.setChecked(self.parameters['servo4'])

        self._addRow(prompt, label1, prompt.srvo1Box)
        self._addRow(prompt, label2, prompt.srvo2Box)
        self._addRow(prompt, label3, prompt.srvo3Box)
        self._addRow(prompt, label4, prompt.srvo4Box)

        return prompt

    def _extractPromptInfo(self, prompt):
        newParameters = {'servo1': prompt.srvo1Box.isChecked(),
                         'servo2': prompt.srvo2Box.isChecked(),
                         'servo3': prompt.srvo3Box.isChecked(),
                         'servo4': prompt.srvo4Box.isChecked()}

        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        descriptionBuild = "Servos"
        if self.parameters["servo1"]: descriptionBuild += "  Base"
        if self.parameters["servo2"]: descriptionBuild += "  Stretch"
        if self.parameters["servo3"]: descriptionBuild += "  Height"
        if self.parameters["servo4"]: descriptionBuild += "  Wrist"

        self.description = descriptionBuild


class WaitCommandGUI(CommandGUI):
    title     = "Wait"
    tooltip   = "Halts the program for a preset amount of time"
    icon      = Paths.command_wait
    logicPair = "WaitCommand"

    def __init__(self, env, parameters=None):
        super(WaitCommandGUI, self).__init__(parameters)

        if self.parameters is None:
            self.parameters = {'time': 0.5}
            pass

    def dressWindow(self, prompt):
        prompt.timeEdit = QtWidgets.QLineEdit()

        # Set up all the labels for the inputs
        timeLabel = QtWidgets.QLabel('Number of seconds: ')


        # Fill the textboxes with the default parameters
        prompt.timeEdit.setText(str(self.parameters['time']))

        self._addRow(prompt, timeLabel, prompt.timeEdit)

        return prompt

    def _extractPromptInfo(self, prompt):
        newParameters = {'time': self._sanitizeEval(prompt.timeEdit, self.parameters['time'])}

        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        self.description = str(self.parameters['time']) + " seconds"


class GripCommandGUI(CommandGUI):
    title     = "Activate Gripper"
    tooltip   = "Activates the robots gripper"
    icon      = Paths.command_grip
    logicPair = "GripCommand"

    def __init__(self, env, parameters=None):
        super(GripCommandGUI, self).__init__(parameters)


class DropCommandGUI(CommandGUI):
    title     = "Deactivate Gripper"
    tooltip   = "Deactivates the robots gripper"
    icon      = Paths.command_drop
    logicPair = "DropCommand"

    def __init__(self, env, parameters=None):
        super(DropCommandGUI, self).__init__(parameters)


class BuzzerCommandGUI(CommandGUI):
    title     = "Play Tone"
    tooltip   = "This tool uses the robots buzzer to play a tone at a certain frequency for a certain amount of time"
    icon      = Paths.command_buzzer
    logicPair = "BuzzerCommand"

    def __init__(self, env, parameters=None):
        super(BuzzerCommandGUI, self).__init__(parameters)

        if self.parameters is None:
            # Some code to set up default parameters
            self.parameters = {"frequency": str(1500),
                               "time": str(.5),
                               "waitForBuzzer": True}

    def dressWindow(self, prompt):
        # Put all the objects into horizontal layouts called Rows
        prompt.frqEdit   = QtWidgets.QLineEdit()  # "Name" edit
        prompt.tmeEdit   = QtWidgets.QLineEdit()  # "value" edit
        prompt.waitCheck = QtWidgets.QCheckBox()  # "override" CheckBox

        # Set up all the labels for the inputs
        frqLabel = QtWidgets.QLabel('Frequency: ')
        tmeLabel = QtWidgets.QLabel('Duration: ')
        waitLabel = QtWidgets.QLabel('Wait: ')

        # Fill the textboxes with the default parameters
        prompt.frqEdit.setText(str(self.parameters['frequency']))
        prompt.tmeEdit.setText(str(self.parameters['time']))
        prompt.waitCheck.setChecked(self.parameters['waitForBuzzer'])


        self._addRow(prompt, frqLabel, prompt.frqEdit)
        self._addRow(prompt, tmeLabel, prompt.tmeEdit)
        self._addRow(prompt, waitLabel, prompt.waitCheck)

        return prompt

    def _extractPromptInfo(self, prompt):
        # Get the parameters from the 'prompt' GUI elements. Put numbers through self.sanitizeFloat
        newParameters = {"frequency":     self._sanitizeEval(prompt.frqEdit, self.parameters["frequency"]),
                         "time":          self._sanitizeEval(prompt.tmeEdit, self.parameters["time"]),
                         "waitForBuzzer": prompt.waitCheck.isChecked()}

        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        # Some string that uses your parameters to describe the object.
        self.description = "Play a tone of " + self.parameters["frequency"] + "HZ for  " +\
                           self.parameters["time"] + " seconds"


class EndProgramCommandGUI(CommandGUI):
    title     = "End Program"
    tooltip   = "When the code reaches this point, the program will end."
    icon      = Paths.command_end_script
    logicPair = "EndProgramCommand"

    def __init__(self, env, parameters=None):
        super(EndProgramCommandGUI, self).__init__(parameters)


class EndEventCommandGUI(CommandGUI):
    title     = "Exit Current Event"
    tooltip   = "When the code reaches this point, the program will not process the rest of this event."
    icon      = Paths.command_exit_event
    logicPair = "EndEventCommand"

    def __init__(self, env, parameters=None):
        super(EndEventCommandGUI, self).__init__(parameters)





#   Robot + Vision COmmands
class MoveRelativeToObjectCommandGUI(CommandGUI):
    title     = "Move Relative To Object"
    tooltip   = "This tool uses computer vision to recognize an object of your choice, and position the robot directly"\
               "\nrelative to this objects XYZ location. If XYZ = 0,0,0, the robot will move directly onto the object."\
               "\n\nIf you don't want to set one of the robots axis, simply leave it empty. For example, put y and z \n"\
               "empty and x to 5 will set the robots x position to objX + 5 while keeping the current Y and Z the same."
    icon      = Paths.command_move_rel_to
    logicPair = "MoveRelativeToObjectCommand"

    def __init__(self, env, parameters=None):
        super(MoveRelativeToObjectCommandGUI, self).__init__(parameters)

        objManager = env.getObjectManager()

        # Save a list that gets all loaded objects. This is used only when the window is opened, to populate the objlist
        self.getObjectList  = lambda: objManager.getObjectNameList(objFilter=objManager.PICKUP)

        if self.parameters is None:
            self.parameters = {"objectID": "",
                               "x": 0,
                               "y": 0,
                               "z": 5}

    def dressWindow(self, prompt):
        # Define what happens when the user changes the object selection




        # Set up all the labels for the inputs
        choiceLbl = QtWidgets.QLabel("Choose an object: ")
        xLabel    = QtWidgets.QLabel('X ')
        yLabel    = QtWidgets.QLabel('Y ')
        zLabel    = QtWidgets.QLabel('Z ')


        # Populate the comboBox with a list of all trackable objects, and select the self.parameters one if it exists
        prompt.objChoices = QtWidgets.QComboBox()
        prompt.objChoices.addItem(self.parameters["objectID"])
        objectList = self.getObjectList()
        for index, objectID in enumerate(objectList): prompt.objChoices.addItem(objectID)


        prompt.xEdit = QtWidgets.QLineEdit()
        prompt.yEdit = QtWidgets.QLineEdit()
        prompt.zEdit = QtWidgets.QLineEdit()



        # Fill the textboxes with the default parameters
        prompt.xEdit.setText(str(self.parameters['x']))
        prompt.yEdit.setText(str(self.parameters['y']))
        prompt.zEdit.setText(str(self.parameters['z']))


        self._addRow(prompt, choiceLbl, prompt.objChoices)
        self._addRow(prompt, xLabel, prompt.xEdit)
        self._addRow(prompt, yLabel, prompt.yEdit)
        self._addRow(prompt, zLabel, prompt.zEdit)



        self._addObjectHint(prompt, len(objectList))

        return prompt

    def _extractPromptInfo(self, prompt):
        # Get the parameters from the 'prompt' GUI elements. Put numbers through self.sanitizeFloat
        newParameters = {"objectID": str(prompt.objChoices.currentText()),
                         'x': self._sanitizeEval(prompt.xEdit, self.parameters["x"]),
                         'y': self._sanitizeEval(prompt.yEdit, self.parameters["y"]),
                         'z': self._sanitizeEval(prompt.zEdit, self.parameters["z"])}

        print(newParameters)
        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        self.description = 'XYZ( ' + str(self.parameters['x']) + \
                           ', ' + str(self.parameters['y'])    + \
                           ', ' + str(self.parameters['z'])    + \
                           ') relative to ' + self.parameters["objectID"]


class MoveWristRelativeToObjectCommandGUI(CommandGUI):
    title     = "Set Wrist Relative To Object"
    tooltip   = "This tool sets the wrist angle of the robot to the angle of an object in the cameras view, plus \n" \
                "some relative degree of your choice. The rotation of the object is determined by the orientation\n" \
                "that it's in when you create the object. "
    tooltip   = "This tool will look at the orientation of an object in the cameras view, and align the wrist with \n"\
                "the rotation of the object. The rotation of the object is determined by the orientation that it was\n"\
                "in when the object was memorized. It's recommended to experiment around a bit with this function to\n"\
                " get a feel for how it works!"

    icon      = Paths.command_wrist_rel
    logicPair = "MoveWristRelativeToObjectCommand"

    def __init__(self, env, parameters=None):
        super(MoveWristRelativeToObjectCommandGUI, self).__init__(parameters)
        objManager         =  env.getObjectManager()
        self.getObjectList = lambda: objManager.getObjectNameList(objFilter=objManager.TRACKABLE)

        # If parameters do not exist, then set up the default parameters
        if self.parameters is None:
            # Anything done with env should be done here. Try not to save env as a class variable whenever possible
            self.parameters = {"objectID": "",
                               "angle": "0"}

    def dressWindow(self, prompt):


        # Create the "ObjectList" choice box
        objLbl     = QtWidgets.QLabel("Choose an Object")
        prompt.objChoices = QtWidgets.QComboBox()
        prompt.objChoices.addItem(self.parameters["objectID"])  # Add an empty item at the top
        objectList = self.getObjectList()
        for index, objectID in enumerate(objectList): prompt.objChoices.addItem(objectID)
        self._addRow(prompt, objLbl, prompt.objChoices)
        self._addObjectHint(prompt, len(objectList))


        # Create the "angle" textbox
        wristLabel       = QtWidgets.QLabel('Angle:')
        prompt.wristEdit = QtWidgets.QLineEdit(self.parameters["angle"])
        self._addRow(prompt, wristLabel, prompt.wristEdit)

        return prompt

    def _extractPromptInfo(self, prompt):
        newParameters = {"objectID": str(prompt.objChoices.currentText()),
                         'angle': self._sanitizeEval(prompt.wristEdit, self.parameters["angle"])}

        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        self.title = "Set Wrist Relative To " + self.parameters["objectID"]
        self.description = "Set the wrist " + self.parameters["angle"] + \
                           " degrees relative to " + self.parameters["objectID"]


class PickupObjectCommandGUI(CommandGUI):
    title     = "Pick Up An Object"
    tooltip   = "This tool uses computer vision to recognize an object of your choice, and attempt to pick up the " \
                "\nobject. If the object cannot be found or picked up, then False will be returned"

    icon      = Paths.command_pickup
    logicPair = "PickupObjectCommand"

    def __init__(self, env, parameters=None):
        super(PickupObjectCommandGUI, self).__init__(parameters)

        objManager = env.getObjectManager()

        # Save a list that gets all loaded objects. This is used only when the window is opened, to populate the objlist
        self.getObjectList  = lambda: objManager.getObjectNameList(objFilter=objManager.PICKUP)

        if self.parameters is None:
            self.parameters = {"objectID": ""}

    def dressWindow(self, prompt):
        # Define what happens when the user changes the object selection
        choiceLbl = QtWidgets.QLabel("Choose an object: ")

        # Create a QComboBox



        # Populate the comboBox with a list of all trackable objects, and select the self.parameters one if it exists
        prompt.objChoices = QtWidgets.QComboBox()
        prompt.objChoices.addItem(self.parameters["objectID"])  # Add an empty item at the top
        objectList = self.getObjectList()
        for index, objectID in enumerate(objectList): prompt.objChoices.addItem(objectID)


        self._addRow(prompt, choiceLbl, prompt.objChoices)
        self._addObjectHint(prompt, len(objectList))

        return prompt

    def _extractPromptInfo(self, prompt):
        # Get the parameters from the 'prompt' GUI elements. Put numbers through self.sanitizeFloat
        newParameters = {"objectID": str(prompt.objChoices.currentText())}

        print(newParameters)
        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        self.description = "Find " + self.parameters["objectID"] + " and move the robot over it"


class TestObjectSeenCommandGUI(CommandGUI):
    title     = "Test If Object Seen"
    tooltip   = "This command will allow code in blocked brackets below it to run IF the specified object has been " \
                "recognized."
    icon      = Paths.command_see_obj
    logicPair = "TestObjectSeenCommand"

    def __init__(self, env, parameters=None):
        super(TestObjectSeenCommandGUI, self).__init__(parameters)

        objManager = env.getObjectManager()
        vision     = env.getVision()
        self.maxAge          = vision.historyLen - 1
        self.getObjectList   = lambda: objManager.getObjectNameList(objFilter=objManager.TRACKABLE)
        self.ageChoices      = ["latest frame", "last 5 frames", "last 15 frames", "last 30 frames", "last 60 frames"]
        self.accChoices      = ["low", "medium", "high"]

        # If parameters do not exist, then set up the default parameters
        if self.parameters is None:
            # Anything done with env should be done here. Try not to save env as a class variable whenever possible
            self.parameters = {"objectID":    "",
                                    "age":     0,
                                "ptCount":     0,  # A number from 0 to 3, which incriments by MIN_MATCH_COUNT points
                                    "not": False}

    def dressWindow(self, prompt):
        # Define what happens when the user changes the object selection
        choiceLbl         = QtWidgets.QLabel("If recognized: ")
        accLbl            = QtWidgets.QLabel("Confidence level: ")
        prompt.ageLbl     = QtWidgets.QLabel("How recently :")
        notLbl            = QtWidgets.QLabel("NOT")

        prompt.objChoices = QtWidgets.QComboBox()
        prompt.accChoices = QtWidgets.QComboBox()
        prompt.ageSlider  = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        prompt.notCheck   = QtWidgets.QCheckBox()  # "Not" CheckBox


        # Populate the comboBox with a list of all trackable objects, and select the self.parameters one if it exists
        prompt.objChoices.addItem(self.parameters["objectID"])  # Add the previously selected item at the top
        objectList = self.getObjectList()
        for index, objectID in enumerate(objectList): prompt.objChoices.addItem(objectID)


        # Populate the accuracayChoices with a list of different possible accuracies

        for choice in self.accChoices: prompt.accChoices.addItem(choice)
        prompt.accChoices.setCurrentIndex(self.parameters["ptCount"])


        # Set up the Age slider
        def updateAgeSliderLabel():
            # Create the text next to the "How Recently" label
            newText = "How Recently: "
            if prompt.ageSlider.value() == 1:
                newText += "Just now"
            else:
                newText += "< " + str(prompt.ageSlider.value()) + " frames ago"
            prompt.ageLbl.setText(newText)
        prompt.ageSlider.valueChanged.connect(updateAgeSliderLabel)
        prompt.ageSlider.setMinimum(1)
        prompt.ageSlider.setMaximum(self.maxAge)
        prompt.ageSlider.setValue(self.parameters["age"])
        updateAgeSliderLabel()

        # Set up the "NOT" Check
        prompt.notCheck.setChecked(self.parameters["not"])
        self._addRow(prompt,     choiceLbl, prompt.objChoices)
        self._addRow(prompt,        accLbl, prompt.accChoices)
        self._addRow(prompt, prompt.ageLbl, prompt.ageSlider)
        self._addRow(prompt,        notLbl,   prompt.notCheck)

        self._addObjectHint(prompt, len(objectList))

        return prompt

    def _extractPromptInfo(self, prompt):
        age = int(prompt.ageSlider.value())
        acc = self.accChoices.index(prompt.accChoices.currentText())
        newParameters = {"objectID": str(prompt.objChoices.currentText()),
                              "age": age,
                              "ptCount": acc,
                              "not": prompt.notCheck.isChecked()}

        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        objName = (self.parameters["objectID"], "Object")[len(self.parameters["objectID"]) == 0]
        self.title = "Test If " + objName + " Seen"

        confidenceText = ["slightly", "fairly", "highly"]

        self.description = "If"
        if self.parameters["not"]: self.description += " NOT"
        self.description += " " + confidenceText[self.parameters["ptCount"]] + " confident object was seen"


class TestObjectLocationCommandGUI(CommandGUI):
    title     = "Test Location Of Object"
    tooltip   = "This command will allow code in blocked brackets below it to run IF the specified object has been" \
                "recognized and the objects location in a particular location."
    icon      = Paths.command_see_loc
    logicPair = "TestObjectLocationCommand"


    def __init__(self, env, parameters=None):
        super(TestObjectLocationCommandGUI, self).__init__(parameters)

        objManager         = env.getObjectManager()
        self.vStream       = env.getVStream()
        self.getObjectList = lambda: objManager.getObjectNameList(objFilter=objManager.TRACKABLE)

        # If parameters do not exist, then set up the default parameters
        if self.parameters is None:
            # Anything done with env should be done here. Try not to save env as a class variable whenever possible
            self.parameters = {"objectID":                "",
                               "location":  [[0, 0], [0, 0]],
                                   "part":          "center",  # Indexes correspond to self.partChoices
                                    "not":             False}

        self.partChoices = ["center", "all", "any"]

    def dressWindow(self, prompt):
        # Define what happens when the user changes the object selection
        choiceLbl = QtWidgets.QLabel("Choose an Object: ")
        partLbl   = QtWidgets.QLabel("What part of object must enter the location: ")
        selectLbl = QtWidgets.QLabel("Click and drag the area of the screen that the object will be in")
        notLbl    = QtWidgets.QLabel("NOT")


        # Create the "input" objects
        prompt.objChoices  = QtWidgets.QComboBox()
        prompt.partChoices = QtWidgets.QComboBox()
        prompt.camWidget   = CameraSelector(self.vStream, prompt, hideRectangle=False)
        prompt.notCheck    = QtWidgets.QCheckBox()  # "Not" CheckBox


        # Populate the ObjectList with trackable objects
        prompt.objChoices.addItem(self.parameters["objectID"])  # Add the previously selected item at the top
        objectList = self.getObjectList()
        for index, objectID in enumerate(objectList): prompt.objChoices.addItem(objectID)


        # Populate the "parts choices" with trackable objects
        prompt.partChoices.addItem(self.parameters["part"])
        for choice in self.partChoices: prompt.partChoices.addItem(choice)


        # Set up the CameraWidget
        prompt.camWidget.play()
        prompt.camWidget.setRectangle(self.parameters["location"])


        # Set up the "NOT" Check
        prompt.notCheck.setChecked(self.parameters["not"])



        self._addRow(prompt, choiceLbl, prompt.objChoices)
        self._addRow(prompt, partLbl, prompt.partChoices)
        self._addRow(prompt, selectLbl, alignRight=False)
        self._addRow(prompt, prompt.camWidget)
        self._addRow(prompt, notLbl, prompt.notCheck)
        self._addObjectHint(prompt, len(objectList))
        prompt.resize(prompt.sizeHint())

        return prompt

    def _extractPromptInfo(self, prompt):
        # Get a new location and sanitize the value
        newLoc = prompt.camWidget.getSelectedRect()
        if newLoc is not None:
            newLoc = [[newLoc[0], newLoc[1]], [newLoc[2], newLoc[3]]]  # Format the new location to this commands format
        else:
            newLoc = self.parameters["location"]

        # Get the "partChoice"
        choice = prompt.partChoices.currentText()


        # Save the new parameters
        newParameters = {"objectID": str(prompt.objChoices.currentText()),
                              "not": prompt.notCheck.isChecked(),
                             "part": choice,
                         "location": newLoc}

        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        objName = (self.parameters["objectID"], "Object")[len(self.parameters["objectID"]) == 0]
        self.title = "Test the Location of " + objName


        self.description = "If " + self.parameters["part"] + " of " + objName + " is"
        if self.parameters["not"]: self.description += " NOT"
        self.description += " seen within a location"


class VisionMoveXYZCommandGUI(MoveXYZCommandGUI):
    title     = "Vision Assisted Move XYZ"
    tooltip   = "This works like the normal Move XYZ command, but uses vision to verify the robots position and\n"\
                "perform a 'correction' move after an initial move. \n" \
                "This command requires Camera/Robot Calibrations to be done."
    icon      = Paths.command_xyz_vision
    logicPair = "VisionMoveXYZCommand"

    def __init__(self, env, parameters=None):
        super(VisionMoveXYZCommandGUI, self).__init__(env, parameters)

    def dressWindow(self, prompt):
        super(VisionMoveXYZCommandGUI, self).dressWindow(prompt)
        warningLbl = QtWidgets.QLabel("This function is experimental. It may not yield more accurate results.")
        warningLbl.setWordWrap(True)

        print("Prompt: ", prompt)
        self._addRow(prompt, warningLbl)

        return prompt




#   LOGIC COMMANDS
class StartBlockCommandGUI(CommandGUI):
    """
    Start a block of code with this class
    """

    icon      = Paths.command_startblock
    tooltip   = "This is the start of a block of commands that only run if a conditional statement is met."
    logicPair = 'StartBlockCommand'

    def __init__(self, shared, parameters=None):
        super(StartBlockCommandGUI, self).__init__(parameters)


class EndBlockCommandGUI(CommandGUI):
    """
    End a block of code with this command
    """

    icon      = Paths.command_endblock
    tooltip   = "This is the end of a block of commands."
    logicPair = 'EndBlockCommand'

    def __init__(self, shared, parameters=None):
        super(EndBlockCommandGUI, self).__init__(parameters)


class ElseCommandGUI(CommandGUI):
    """
    End a block of code with this command
    """

    icon      = Paths.command_else
    tooltip   = "This will run commands if a test evaluates to False"
    logicPair = 'ElseCommand'

    def __init__(self, shared, parameters=None):
        super(ElseCommandGUI, self).__init__(parameters)


class SetVariableCommandGUI(CommandGUI):
    title     = "Set Variable"
    tooltip   = "This command can create a variable or set an existing variable to a value or an expression."
    icon      = Paths.command_set_var
    logicPair = "SetVariableCommand"

    def __init__(self, env, parameters=None):
        super(SetVariableCommandGUI, self).__init__(parameters)

        if self.parameters is None:
            # Some code to set up default parameters
            self.parameters = {"variable": "",
                               "expression": ""}

    def dressWindow(self, prompt):
        # Do some GUI code setup
        # Put all the objects into horizontal layouts called Rows
        prompt.namEdit = QtWidgets.QLineEdit()  # "Name" edit
        prompt.valEdit = QtWidgets.QLineEdit()  # "value" edit


        # Set up all the labels for the inputs
        namLabel = QtWidgets.QLabel('Variable Name: ')
        valLabel = QtWidgets.QLabel('Value or Expression: ')

        # Fill the textboxes with the default parameters
        prompt.namEdit.setText(str(self.parameters['variable']))
        prompt.valEdit.setText(str(self.parameters['expression']))

        self._addRow(prompt, namLabel, prompt.namEdit)
        self._addRow(prompt, valLabel, prompt.valEdit)

        return prompt

    def _extractPromptInfo(self, prompt):
        # Get the parameters from the 'prompt' GUI elements. Put numbers through self.sanitizeFloat

        newParameters = {"variable": self._sanitizeVariable(prompt.namEdit, self.parameters["variable"]),
                         "expression": prompt.valEdit.text()}

        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        # Some string that uses your parameters to describe the object.
        self.description = "Set " + self.parameters["variable"] + " to " + self.parameters["expression"]


class TestVariableCommandGUI(CommandGUI):
    title     = "Test Variable"
    tooltip   = "This will allow/disallow code to run that is in blocked brackets below it."
    icon      = Paths.command_test_var
    logicPair = 'TestVariableCommand'

    def __init__(self, env, parameters=None):
        super(TestVariableCommandGUI, self).__init__(parameters)


        if self.parameters is None:
            self.parameters = {'variable': '',
                               'test': 0,
                               'expression': ''}

    def dressWindow(self, prompt):
        prompt.varEdit = QtWidgets.QLineEdit()  # "Variable" edit
        prompt.tstMenu = QtWidgets.QComboBox()
        prompt.valEdit = QtWidgets.QLineEdit()

        prompt.tstMenu.addItem('Equal To')
        prompt.tstMenu.addItem('Not Equal To')
        prompt.tstMenu.addItem('Greater Than')
        prompt.tstMenu.addItem('Less Then')

        # Set up all the labels for the inputs
        varLabel = QtWidgets.QLabel('Variable: ')
        tstLabel = QtWidgets.QLabel('Test: ')
        valLabel = QtWidgets.QLabel('Value: ')

        # Fill the textboxes with the default parameters
        prompt.varEdit.setText(str(self.parameters['variable']))
        prompt.tstMenu.setCurrentIndex(self.parameters['test'])
        prompt.valEdit.setText(str(self.parameters['expression']))
        # prompt.notCheck.setChecked(self.parameters['not'])

        self._addRow(prompt, varLabel, prompt.varEdit)
        self._addRow(prompt, tstLabel, prompt.tstMenu)
        self._addRow(prompt, valLabel, prompt.valEdit)

        return prompt

    def _extractPromptInfo(self, prompt):
        newParameters = {'variable': self._sanitizeVariable(prompt.varEdit, self.parameters['variable']),
                         'test': prompt.tstMenu.currentIndex(),
                         'expression': str(prompt.valEdit.text())}  # This can't be sanitized, unfortunately :/

        self.parameters.update(newParameters)
        return self.parameters

    def _updateDescription(self):
        operations = [' equal to', ' not equal to', ' greater than', ' less than']
        self.description = 'If ' + str(self.parameters['variable']) + ' is' + operations[self.parameters['test']] + \
                           ' ' + self.parameters['expression'] + ' then'


class ScriptCommandGUI(CommandGUI):
    title     = "Run Python Code"
    tooltip   = "This tool will execute a script made by the user.\nDO NOT RUN PROGRAMS WITH SCRIPTS WRITTEN BY OTHER"+\
                "\nUSERS UNLESS YOU HAVE CHECKED THE SCRIPT AND KNOW WHAT YOU ARE DOING!"
    icon      = Paths.command_script
    logicPair = "ScriptCommand"

    def __init__(self, env, parameters=None):
        super(ScriptCommandGUI, self).__init__(parameters)

        # If parameters do not exist, then set up the default parameters
        if self.parameters is None:
            # Anything done with env should be done here. Try not to save env as a class variable whenever possible
            self.parameters = {"script":      "",
                               "description": ""}

    def dressWindow(self, prompt):
        # Do some GUI code setup
        # Put all the objects into horizontal layouts called Rows
        prompt.IDE     = ScriptWidget(self.parameters["script"], prompt)
        descriptionLbl = QtWidgets.QLabel("Description: ")

        prompt.descriptionEdt = QtWidgets.QLineEdit(self.parameters["description"])

        self._addRow(prompt, descriptionLbl, prompt.descriptionEdt)
        prompt.content.addWidget(prompt.IDE)  # and so on for all of the rows

        return prompt

    def _extractPromptInfo(self, prompt):
        newParameters = {"script": str(prompt.IDE.getCode()),
                         "description": prompt.descriptionEdt.text()}

        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        self.description = self.parameters["description"]  # Some string that uses your parameters to describe the object.



class RunTaskCommandGUI(CommandGUI):
    title     = "Run Another Task File"
    tooltip   = "This tool will run  another task file and run it inside of this task, until the 'End Program'\n" +\
                "command is called within the task, then it will return to the currently running task.\n" + \
                "All tasks are preloaded when script is launched, so if a child class runs a parent class, an error\n"+\
                "will be returned."

    icon      = Paths.command_run_task
    logicPair = "RunTaskCommand"

    def __init__(self, env, parameters=None):
        super(RunTaskCommandGUI, self).__init__(parameters)

        # If parameters do not exist, then set up the default parameters
        if self.parameters is None:
            # Anything done with env should be done here. Try not to save env as a class variable whenever possible
            self.parameters = {"filename": ""}

    def dressWindow(self, prompt):
        # Do some GUI code setup
        # Put all the objects into horizontal layouts called Rows


        return prompt

    def _extractPromptInfo(self, prompt):
        newParameters = {}

        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        self.description = ""
