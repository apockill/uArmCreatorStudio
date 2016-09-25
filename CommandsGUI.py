"""
This software was designed by Alexander Thiel
Github handle: https://github.com/apockill
Email: Alex.D.Thiel@Gmail.com


The software was designed originaly for use with a robot arm, particularly uArm (Made by uFactory, ufactory.cc)
It is completely open source, so feel free to take it and use it as a base for your own projects.

If you make any cool additions, feel free to share!


License:
    This file is part of uArmCreatorStudio.
    uArmCreatorStudio is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    uArmCreatorStudio is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with uArmCreatorStudio.  If not, see <http://www.gnu.org/licenses/>.
"""
import ast  # To check if a statement is python parsible, for evals
import re   # For variable santization
import Paths
import webbrowser  # For opening the user manual PDF
from os.path      import basename
from PyQt5        import QtGui, QtCore, QtWidgets
from CameraGUI    import CameraSelector
from CommonGUI    import ScriptWidget
from Logic.Global import printf, ensurePathExists
__author__ = "Alexander Thiel"



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
        self.icon        = QtWidgets.QLabel()
        self.deleteBtn   = QtWidgets.QPushButton()


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


        midLayout = QtWidgets.QVBoxLayout()
        midLayout.setSpacing(1)
        midLayout.addWidget(self.title)
        midLayout.addWidget(self.description)


        mainHLayout = QtWidgets.QHBoxLayout()
        mainHLayout.addWidget(self.icon)
        mainHLayout.addLayout(midLayout, QtCore.Qt.AlignLeft)
        mainHLayout.addWidget(self.deleteBtn)
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
        self.initUI()

    def initUI(self):
        self.setStyleSheet("QTabBar::tab{width:23px; height:90;}")

        self.addTab(self.generateBasicTab(),     "Basic")
        self.addTab(self.generateVisionTab(),    "Vision")
        self.addTab(self.generateLogicTab(),     "Logic")
        self.addTab(self.generateFunctionsTab(), "Functions")

        self.setTabPosition(QtWidgets.QTabWidget.East)
        self.setFixedWidth(85)


    # Put Commands into the menu in these functions
    def generateBasicTab(self):
        tabWidget, add = self.generateTabWidget()

        add(MoveXYZCommand)
        add(MoveWristCommand)
        add(MotionRecordingCommand)
        add(SpeedCommand)
        add(AttachCommand)
        add(DetachCommand)
        add(GripCommand)
        add(DropCommand)
        add(WaitCommand)
        add(BuzzerCommand)


        return tabWidget

    def generateVisionTab(self):
        tabWidget, add = self.generateTabWidget()


        add(MoveRelativeToObjectCommand)
        add(MoveWristRelativeToObjectCommand)
        add(PickupObjectCommand)
        add(TestObjectSeenCommand)
        add(TestObjectLocationCommand)
        add(TestObjectAngleCommand)

        return tabWidget

    def generateLogicTab(self):
        tabWidget, add = self.generateTabWidget()

        add(SetVariableCommand)
        add(TestVariableCommand)
        add(LoopCommand)
        add(ElseCommand)
        add(StartBlockCommand)
        add(EndBlockCommand)
        add(EndEventCommand)
        add(EndTaskCommand)


        return tabWidget

    def generateFunctionsTab(self):
        tabWidget, add = self.generateTabWidget()

        add(ScriptCommand)
        add(RunTaskCommand)
        add(RunFunctionCommand)


        return tabWidget


    # Other
    def generateButton(self, commandType):
        """
        Creates a button with the icon of a command, that can be clicked and dragged onto a CommandList
        """

        newButton = self.DraggableButton(str(commandType.__name__), self)


        newButton.setIcon(QtGui.QIcon(commandType.icon))
        newButton.setIconSize(QtCore.QSize(32, 32))
        newButton.setToolTip(commandType.tooltip)
        newButton.setFixedHeight(40)
        newButton.setFixedWidth(40)

        newButton.customContextMenuRequested.connect(lambda: self.addCommandFunc(commandType))
        return newButton

    def generateTabWidget(self):
        """
        Creates a tab widget, and an "add" function that can be used to add widgets to the main layout of the tab.
        This simplifies a lot, I promise.
        :return:
        """
        tabWidget = QtWidgets.QWidget()
        vBox      = QtWidgets.QVBoxLayout()
        vBox.setAlignment(QtCore.Qt.AlignTop)
        tabWidget.setLayout(vBox)

        add  = lambda btnType: vBox.addWidget(self.generateButton(btnType))

        return tabWidget, add


    # Special button that can be dragged and dropped, with information about the Type of command
    class DraggableButton(QtWidgets.QPushButton):
        def __init__(self, dragData, parent):
            super().__init__(parent)
            self.dragData = dragData  # The information that will be transfered upon drag

            self.mouse_down = False  # Has a left-click happened yet?
            self.mouse_posn = QtCore.QPoint()  # If so, this is where...
            self.mouse_time = QtCore.QTime()   # ... and this is when

        def mousePressEvent(self, event):
            if event.button() == QtCore.Qt.LeftButton:
                self.mouse_down = True         # we are left-clicked-upon
                self.mouse_posn = event.pos()  # here and...
                self.mouse_time.start()        # ...now

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
            return


class CommandGUI:
    tooltip = ''
    icon = ''
    title = ''

    defaultTextBoxWidth = 150

    def __init__(self, parameters):
        self.description = ""
        self.parameters = parameters  # For commands with no parameters, this should stay empty

    def openWindow(self):  # Open window

        # If this object has no window object, then skip this process and return true (ei, StartBlockCommand)
        if self.parameters is None: return True

        ##### Create the base window #####
        prompt = QtWidgets.QDialog()


        # Create the apply/cancel buttons, connect them, and format them
        prompt.applyBtn = QtWidgets.QPushButton('Apply')
        cancelBtn       = QtWidgets.QPushButton('Cancel')
        helpBtn         = QtWidgets.QPushButton('User Manual')

        prompt.applyBtn.setMinimumWidth(90)
        cancelBtn.setMinimumWidth(90)
        helpBtn.setMinimumWidth(90)

        prompt.applyBtn.clicked.connect(prompt.accept)
        cancelBtn.clicked.connect(prompt.reject)
        helpBtn.clicked.connect(lambda: webbrowser.open_new(Paths.user_manual))
        prompt.applyBtn.setDefault(True)


        # Create a content box for the command to fill out parameters and GUI elements
        prompt.content    = QtWidgets.QVBoxLayout()
        prompt.content.setContentsMargins(20, 10, 20, 10)
        prompt.content.setAlignment(QtCore.Qt.AlignTop)
        contentGroupBox = QtWidgets.QGroupBox("Parameters")
        contentGroupBox.setLayout(prompt.content)


        # Now that the window is 'dressed', add "Cancel" and "Apply" buttons
        buttonRow = QtWidgets.QHBoxLayout()
        buttonRow.addWidget(cancelBtn)
        buttonRow.addWidget(helpBtn)
        buttonRow.addStretch(1)
        buttonRow.addWidget(prompt.applyBtn)


        # Create the main vertical layout, add everything to it
        prompt.mainVLayout = QtWidgets.QVBoxLayout()
        prompt.mainVLayout.addWidget(contentGroupBox)


        # Set the main layout and general window parameters
        prompt.setMinimumWidth(350)
        prompt.setMinimumHeight(350)
        prompt.setLayout(prompt.mainVLayout)
        prompt.setWindowTitle(self.title)
        prompt.setWindowIcon(QtGui.QIcon(self.icon))
        prompt.setWhatsThis(self.tooltip)  # This makes the "Question Mark" button on the window show the tooltip msg


        # Dress the base window (this is where the child actually puts the content into the widget)
        prompt = self.dressWindow(prompt)  # Calls a child function that should have this function

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
            printf("GUI| New Command Parameters: ", self.parameters)

        else:
            printf("GUI| User Canceled Prompt")

        return accepted

    def dressWidget(self, newWidget):
        self._updateDescription()

        newWidget.setIcon(self.icon)
        newWidget.setTitle(self.title)
        newWidget.setTip(self.tooltip)
        newWidget.setDescription(self.description)
        return newWidget

    def getSaveData(self):
        commandSave = {      'type': self.__class__.__name__,
                       'parameters': self.parameters}
        return commandSave


    # Empty functions so that subclasses without them don't cause errors
    def _updateDescription(self):
        # This is called in openWindow() and will update the decription to match the parameters
        pass


    # Helper functions for general Command children purposes
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
    def _addRow(self, prompt, *args, alignRight=True, resizeBox=True):
        # If any argument is of the following type, then set the width to self.defaultTextBoxWidth
        setWidthOnTypes = [QtWidgets.QLineEdit, QtWidgets.QComboBox, QtWidgets.QPushButton, QtWidgets.QSlider]

        row = QtWidgets.QHBoxLayout()

        # Push objects together, otherwise keep it centered
        if alignRight: row.addStretch(1)

        for widget in args:
            # Set the width if it is a typ
            if type(widget) in setWidthOnTypes and resizeBox:
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
        hintRow.addWidget(prompt.hintLbl)

        # Add it to the prompt
        prompt.content.addLayout(hintRow)

    def _addObjectHint(self, prompt, numResources):
        """
        This is a hint that goes onto any command that asks the user to choose from a vision object. It tells them
        that they can create objects in the Resource Manager
        """
        # If there are no objects, place a nice label to let the user know
        if numResources == 0:
            hintText = "You have not created any trackable objects yet." + \
                       " Try adding new objects in the Resource Manager!"
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
            hintText = "You have not created any Movement Recordings yet. " + \
                       "Try creating new recordings in the Resource Manager!"
            self._addHint(prompt, hintText)

    def _addFunctionHint(self, prompt, numResources):
        if numResources == 0:
            hintText = "You have not created any Functions yet. " + \
                        "Try creating new functions in the Resource Manager!"

            self._addHint(prompt, hintText)


########## COMMANDS ##########
"""
Commands must have:
    - A class, here in CommandsGUI.py
    - A logic implimentation under Commands.py with a run() function
        - The logic implimentation MUST have the same name as the GUI implimentation
    - Be added to the CommandMenuWidget.initUI() function in order for the user to add it to their programs
    - Variables
        - tooltip
        - icon
        - title   (Except for certain functions, such as StartBlockCommand)
    - Functions
        - init(env, parameters=None) function
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



----------------------------------------COMMAND TEMPLATE-------------------------------------------
class NameCommand(CommandGUI):
    title     = "Example Title"
    tooltip   = "This tool does X Y and Z"
    icon      = Paths.some_icon

    def __init__(self, env, parameters=None):
        super(NameCommand, self).__init__(parameters)

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
-----------------------------------------------------------------------------------------------------
"""



#   BASIC CONTROL COMMANDS
class MoveXYZCommand(CommandGUI):
    title     = "Move XYZ"
    tooltip   = "Set the robots position.\n"\
                "If you do not want to set one of the robots axis, simply leave it empty. For example, put y and z \n"\
                "empty and x to 5 will set the robots x position to 5 while keeping the current Y and Z the same."
    icon      = Paths.command_xyz

    def __init__(self, env, parameters=None):
        super(MoveXYZCommand, self).__init__(parameters)
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
            xEdt.setText(str(round(x, 1)))
            yEdt.setText(str(round(y, 1)))
            zEdt.setText(str(round(z, 1)))

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
        rltCheck = QtWidgets.QLabel('Relative ')


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


class MoveWristCommand(CommandGUI):
    title     = "Set Wrist Angle"
    tooltip   = "This command sets the angle of the robots 4th axis, the wrist."
    icon      = Paths.command_move_wrist

    def __init__(self, env, parameters=None):
        super(MoveWristCommand, self).__init__(parameters)
        self.getWristAngle = lambda: env.getRobot().getAngles()[3]

        if self.parameters is None:
            currentWrist = self.getWristAngle()
            self.parameters = {"angle": str(currentWrist),
                               "relative": False}

    def dressWindow(self, prompt):
        def setCurrentAngle(edit):
            angle = self.getWristAngle()
            edit.setText(str(round(angle, 1)))

        # Create what the user will be interacting with
        prompt.wristEdit = QtWidgets.QLineEdit()
        prompt.rltCheck  = QtWidgets.QCheckBox()  # "relative" CheckBox
        currentAngleBtn  = QtWidgets.QPushButton("Get Angle")

        currentAngleBtn.clicked.connect(lambda: setCurrentAngle(prompt.wristEdit))

        # Create the labels for the interactive stuff
        wristLabel       = QtWidgets.QLabel('Angle ')
        rltLabel         = QtWidgets.QLabel('Relative ')

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


class MotionRecordingCommand(CommandGUI):
    title     = "Play Movement Recording"
    tooltip   = "This will play back a 'Movement recording' at a playback speed of your choosing. To create robot\n" + \
                "movement recordings, simply click on 'Resources' on the toolbar and add a new recording."
    icon      = Paths.command_play_path

    def __init__(self, env, parameters=None):
        super(MotionRecordingCommand, self).__init__(parameters)

        objManager = env.getObjectManager()
        self.getObjectList = lambda: objManager.getObjectNameList(typeFilter=objManager.MOTIONPATH)


        if self.parameters is None:
            self.parameters = {"objectID": "",
                               "reversed": False,
                               "speed": "1.0"}

    def dressWindow(self, prompt):

        # Choose a recording
        choiceLbl = QtWidgets.QLabel("Choose a Recording ")
        prompt.recChoices = QtWidgets.QComboBox()
        prompt.recChoices.addItem(self.parameters["objectID"])
        recList = self.getObjectList()
        for objectID in recList: prompt.recChoices.addItem(objectID)
        self._addRow(prompt, choiceLbl, prompt.recChoices)


        # PlaybackSpeed
        speedLbl = QtWidgets.QLabel("Playback Speed ")
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
        self.description = "Play movement recording " + self.parameters["objectID"] \
                           + " Speed x" + str(self.parameters["speed"])
        if self.parameters["reversed"]: self.description += " reversed"


class SpeedCommand(CommandGUI):
    title     = "Set Speed"
    tooltip   = "This tool sets the speed of the robot for any move commands that are done after this. \n" \
                "For example, if you set the speed to 20, then do two Move XYZ commands, the robot will move to \n" \
                "those locations with a speed of 20 cm/s. The default robot speed is 10 cm/s. "
    icon      = Paths.command_speed

    def __init__(self, env, parameters=None):
        super(SpeedCommand, self).__init__(parameters)

        if self.parameters is None:
            # Some code to set up default parameters
            self.parameters = {"speed": str(10)}

    def dressWindow(self, prompt):
        prompt.speedEdit = QtWidgets.QLineEdit()

        # Set up all the labels for the inputs
        speedLabel = QtWidgets.QLabel('Speed (cm/s) ')

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


class DetachCommand(CommandGUI):
    title     = "Detach Servos"
    tooltip   = "Disengage the specified servos on the robot"
    icon      = Paths.command_detach

    def __init__(self, env, parameters=None):
        super(DetachCommand, self).__init__(parameters)

        if self.parameters is None:
            self.parameters = {'servo0': True,
                               'servo1': True,
                               'servo2': True,
                               'servo3': True}


    def dressWindow(self, prompt):
        # Do some GUI code setup
        # Put all the objects into horizontal layouts called Rows
        prompt.srvo1Box = QtWidgets.QCheckBox()  # Rotation textbox
        prompt.srvo2Box = QtWidgets.QCheckBox()  # Stretch textbox
        prompt.srvo3Box = QtWidgets.QCheckBox()  # Height textbox
        prompt.srvo4Box = QtWidgets.QCheckBox()  # "relative" CheckBox

        # Set up all the labels for the inputs
        label1 = QtWidgets.QLabel('Base Servo ')
        label2 = QtWidgets.QLabel('Stretch Servo ')
        label3 = QtWidgets.QLabel('Height Servo ')
        label4 = QtWidgets.QLabel('Wrist Servo ')

        # Fill the textboxes with the default parameters
        prompt.srvo1Box.setChecked(self.parameters['servo0'])
        prompt.srvo2Box.setChecked(self.parameters['servo1'])
        prompt.srvo3Box.setChecked(self.parameters['servo2'])
        prompt.srvo4Box.setChecked(self.parameters['servo3'])
        self._addRow(prompt, label1, prompt.srvo1Box)
        self._addRow(prompt, label2, prompt.srvo2Box)
        self._addRow(prompt, label3, prompt.srvo3Box)
        self._addRow(prompt, label4, prompt.srvo4Box)
        return prompt

    def _extractPromptInfo(self, prompt):
        newParameters = {'servo0': prompt.srvo1Box.isChecked(),
                         'servo1': prompt.srvo2Box.isChecked(),
                         'servo2': prompt.srvo3Box.isChecked(),
                         'servo3': prompt.srvo4Box.isChecked()}

        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        descriptionBuild = "Servos"
        if self.parameters["servo0"]: descriptionBuild += "  Base"
        if self.parameters["servo1"]: descriptionBuild += "  Stretch"
        if self.parameters["servo2"]: descriptionBuild += "  Height"
        if self.parameters["servo3"]: descriptionBuild += "  Wrist"

        self.description = descriptionBuild


class AttachCommand(CommandGUI):
    """
    A command for attaching the servos of the robot
    """

    title     = "Attach Servos"
    tooltip   = "Re-engage servos on the robot. This will 'stiffen' the servos, and they will resist movement."
    icon      = Paths.command_attach

    def __init__(self, env, parameters=None):
        super(AttachCommand, self).__init__(parameters)

        if self.parameters is None:
            self.parameters = {'servo0': True,
                               'servo1': True,
                               'servo2': True,
                               'servo3': True}


    def dressWindow(self, prompt):
        # Do some GUI code setup
        # Put all the objects into horizontal layouts called Rows
        prompt.srvo1Box = QtWidgets.QCheckBox()  #  Rotation textbox
        prompt.srvo2Box = QtWidgets.QCheckBox()  #  Stretch textbox
        prompt.srvo3Box = QtWidgets.QCheckBox()  #  Height textbox
        prompt.srvo4Box = QtWidgets.QCheckBox()  #  "relative" CheckBox

        # Set up all the labels for the inputs
        label1 = QtWidgets.QLabel('Base Servo ')
        label2 = QtWidgets.QLabel('Stretch Servo ')
        label3 = QtWidgets.QLabel('Height Servo ')
        label4 = QtWidgets.QLabel('Wrist Servo ')

        # Fill the textboxes with the default parameters
        prompt.srvo1Box.setChecked(self.parameters['servo0'])
        prompt.srvo2Box.setChecked(self.parameters['servo1'])
        prompt.srvo3Box.setChecked(self.parameters['servo2'])
        prompt.srvo4Box.setChecked(self.parameters['servo3'])

        self._addRow(prompt, label1, prompt.srvo1Box)
        self._addRow(prompt, label2, prompt.srvo2Box)
        self._addRow(prompt, label3, prompt.srvo3Box)
        self._addRow(prompt, label4, prompt.srvo4Box)

        return prompt

    def _extractPromptInfo(self, prompt):
        newParameters = {'servo0': prompt.srvo1Box.isChecked(),
                         'servo1': prompt.srvo2Box.isChecked(),
                         'servo2': prompt.srvo3Box.isChecked(),
                         'servo3': prompt.srvo4Box.isChecked()}

        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        descriptionBuild = "Servos"
        if self.parameters["servo0"]: descriptionBuild += "  Base"
        if self.parameters["servo1"]: descriptionBuild += "  Stretch"
        if self.parameters["servo2"]: descriptionBuild += "  Height"
        if self.parameters["servo3"]: descriptionBuild += "  Wrist"

        self.description = descriptionBuild


class GripCommand(CommandGUI):
    title     = "Activate Gripper"
    tooltip   = "Activates the robots gripper"
    icon      = Paths.command_grip

    def __init__(self, env, parameters=None):
        super(GripCommand, self).__init__(parameters)


class WaitCommand(CommandGUI):
    title     = "Wait"
    tooltip   = "This command will wait for a certain amount of time. Time is measured in seconds."
    icon      = Paths.command_wait

    def __init__(self, env, parameters=None):
        super(WaitCommand, self).__init__(parameters)

        if self.parameters is None:
            self.parameters = {'time': 0.5}
            pass

    def dressWindow(self, prompt):
        prompt.timeEdit = QtWidgets.QLineEdit()

        # Set up all the labels for the inputs
        timeLabel = QtWidgets.QLabel('Number of seconds ')


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


class DropCommand(CommandGUI):
    title     = "Deactivate Gripper"
    tooltip   = "Deactivates the robots gripper"
    icon      = Paths.command_drop

    def __init__(self, env, parameters=None):
        super(DropCommand, self).__init__(parameters)


class BuzzerCommand(CommandGUI):
    title     = "Play Tone"
    tooltip   = "This tool uses the robots buzzer to play a tone at a certain frequency for a certain amount of time"
    icon      = Paths.command_buzzer

    def __init__(self, env, parameters=None):
        super(BuzzerCommand, self).__init__(parameters)

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
        frqLabel = QtWidgets.QLabel('Frequency ')
        tmeLabel = QtWidgets.QLabel('Duration ')
        waitLabel = QtWidgets.QLabel('Wait ')

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







#   Robot + Vision COmmands
class MoveRelativeToObjectCommand(CommandGUI):
    title     = "Move Relative To Object"
    tooltip   = "This tool uses computer vision to recognize an object of your choice, and position the robot directly"\
               "\nrelative to this objects XYZ location. If XYZ = 0,0,0, the robot will move directly onto the object."\
               "\n\nIf you don't want to set one of the robots axis, simply leave it empty. For example, put y and z\n"\
               "empty and x to 5 will set the robots x position to objX + 5 while keeping the current Y and Z the same."
    icon      = Paths.command_move_rel_to

    def __init__(self, env, parameters=None):
        super(MoveRelativeToObjectCommand, self).__init__(parameters)

        objManager = env.getObjectManager()

        # Save a list that gets all loaded objects. This is used only when the window is opened, to populate the objlist
        self.getObjectList  = lambda: objManager.getObjectNameList(typeFilter=objManager.TRACKABLE)

        if self.parameters is None:
            self.parameters = {"objectID": "",
                               "x": 0,
                               "y": 0,
                               "z": 5}

    def dressWindow(self, prompt):
        # Define what happens when the user changes the object selection




        # Set up all the labels for the inputs
        choiceLbl = QtWidgets.QLabel("Choose an object ")
        xLabel    = QtWidgets.QLabel('X ')
        yLabel    = QtWidgets.QLabel('Y ')
        zLabel    = QtWidgets.QLabel('Z ')


        # Populate the comboBox with a list of all trackable objects, and select the self.parameters one if it exists
        prompt.objChoices = QtWidgets.QComboBox()
        prompt.objChoices.addItem(self.parameters["objectID"])
        objectList = self.getObjectList()
        for objectID in objectList: prompt.objChoices.addItem(objectID)


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


        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        objName = (self.parameters["objectID"], "Object")[len(self.parameters["objectID"]) == 0]
        self.title = "Move Relative To " + objName

        self.description = 'XYZ( ' + str(self.parameters['x']) + \
                           ', ' + str(self.parameters['y'])    + \
                           ', ' + str(self.parameters['z'])    + \
                           ') relative to ' + self.parameters["objectID"]


class MoveWristRelativeToObjectCommand(CommandGUI):
    title     = "Set Wrist Relative To Object"
    tooltip   = "This tool will look at the orientation of an object in the cameras view, and align the wrist with \n"\
                "the rotation of the object. The rotation of the object is determined by the orientation that it was\n"\
                "in when the object was memorized. It's recommended to experiment around a bit with this function to\n"\
                " get a feel for how it works!"
    icon      = Paths.command_wrist_rel

    def __init__(self, env, parameters=None):
        super(MoveWristRelativeToObjectCommand, self).__init__(parameters)
        objManager         =  env.getObjectManager()
        self.getObjectList = lambda: objManager.getObjectNameList(typeFilter=objManager.TRACKABLE)

        # If parameters do not exist, then set up the default parameters
        if self.parameters is None:
            # Anything done with env should be done here. Try not to save env as a class variable whenever possible
            self.parameters = {"objectID": "",
                               "angle":   "0",
                               "relToBase": False}

    def dressWindow(self, prompt):


        # Create the "ObjectList" choice box
        objLbl     = QtWidgets.QLabel("Choose an Object")
        prompt.objChoices = QtWidgets.QComboBox()
        prompt.objChoices.addItem(self.parameters["objectID"])  # Add an empty item at the top
        objectList = self.getObjectList()
        for objectID in objectList: prompt.objChoices.addItem(objectID)
        self._addRow(prompt, objLbl, prompt.objChoices)



        # Create the "angle" textbox
        wristLabel       = QtWidgets.QLabel('Angle ')
        prompt.wristEdit = QtWidgets.QLineEdit(self.parameters["angle"])
        self._addRow(prompt, wristLabel, prompt.wristEdit)


        # Create the "relative to 'what'" choices
        bttnGroup = QtWidgets.QButtonGroup()
        prompt.relToAxis = QtWidgets.QRadioButton()
        prompt.relToBase = QtWidgets.QRadioButton()
        bttnGroup.addButton(prompt.relToAxis)
        bttnGroup.addButton(prompt.relToBase)

        prompt.relToAxis.setChecked(not self.parameters["relToBase"])
        prompt.relToBase.setChecked(self.parameters["relToBase"])

        self._addRow(prompt,     QtWidgets.QLabel("Relative to X Axis "), prompt.relToAxis)
        self._addRow(prompt, QtWidgets.QLabel("Relative to Robot Base "), prompt.relToBase)
        self._addObjectHint(prompt, len(objectList))

        return prompt

    def _extractPromptInfo(self, prompt):
        relToBase = prompt.relToBase.isChecked()

        newParameters = {"objectID": str(prompt.objChoices.currentText()),
                         'angle': self._sanitizeEval(prompt.wristEdit, self.parameters["angle"]),
                         'relToBase': relToBase}

        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        objName = (self.parameters["objectID"], "Object")[len(self.parameters["objectID"]) == 0]
        self.title = "Set Wrist Relative To " + objName

        self.description = "Set the wrist " + self.parameters["angle"] + \
                           " degrees relative to " + self.parameters["objectID"]


class PickupObjectCommand(CommandGUI):
    title     = "Pick Up Object"
    tooltip   = "This tool uses computer vision to recognize an object of your choice, and attempt to pick up the " \
                "\nobject. If the object cannot be found or picked up, then False will be returned"
    icon      = Paths.command_pickup

    def __init__(self, env, parameters=None):
        super(PickupObjectCommand, self).__init__(parameters)

        objManager = env.getObjectManager()

        # Save a list that gets all loaded objects. This is used only when the window is opened, to populate the objlist
        self.getObjectList  = lambda: objManager.getObjectNameList(typeFilter=objManager.TRACKABLE)

        if self.parameters is None:
            self.parameters = {"objectID": ""}

    def dressWindow(self, prompt):
        # Define what happens when the user changes the object selection



        # Create a Combobox with the appropriate items
        choiceLbl = QtWidgets.QLabel("Choose an object ")
        prompt.objChoices = QtWidgets.QComboBox()
        prompt.objChoices.addItem(self.parameters["objectID"])  # Add an empty item at the top
        objectList = self.getObjectList()
        for objectID in objectList: prompt.objChoices.addItem(objectID)
        self._addRow(prompt, choiceLbl, prompt.objChoices)


        self._addObjectHint(prompt, len(objectList))

        return prompt

    def _extractPromptInfo(self, prompt):
        # Get the parameters from the 'prompt' GUI elements. Put numbers through self.sanitizeFloat
        newParameters = {"objectID": str(prompt.objChoices.currentText())}

        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        objName = (self.parameters["objectID"], "Object")[len(self.parameters["objectID"]) == 0]
        self.title = "Pick Up " + objName
        self.description = "Find " + self.parameters["objectID"] + " and pick it up"


class TestObjectSeenCommand(CommandGUI):
    title     = "Test If Object Seen"
    tooltip   = "This command will allow code in blocked brackets below it to run IF the specified object has been " \
                "recognized."
    icon      = Paths.command_test_see

    def __init__(self, env, parameters=None):
        super(TestObjectSeenCommand, self).__init__(parameters)

        objManager = env.getObjectManager()
        vision     = env.getVision()
        self.maxAge          = vision.historyLen - 1
        self.getObjectList   = lambda: objManager.getObjectNameList(typeFilter=objManager.TRACKABLE)
        self.ageChoices      = ["latest frame", "last 5 frames", "last 15 frames", "last 30 frames", "last 60 frames"]
        self.accChoices      = ["low", "medium", "high"]

        # If parameters do not exist, then set up the default parameters
        if self.parameters is None:
            # Anything done with env should be done here. Try not to save env as a class variable whenever possible
            self.parameters = {"objectID":    "",
                                    "age":     0,
                             "confidence":     0,  # A number from 0 to 3, which incriments by MIN_MATCH_COUNT points
                                    "not": False}

    def dressWindow(self, prompt):
        # Define what happens when the user changes the object selection
        choiceLbl         = QtWidgets.QLabel("If recognized ")
        accLbl            = QtWidgets.QLabel("Confidence level ")
        prompt.ageLbl     = QtWidgets.QLabel("When ")
        notLbl            = QtWidgets.QLabel("NOT")

        prompt.objChoices = QtWidgets.QComboBox()
        prompt.accChoices = QtWidgets.QComboBox()
        prompt.ageSlider  = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        prompt.notCheck   = QtWidgets.QCheckBox()  # "Not" CheckBox


        # Populate the comboBox with a list of all trackable objects, and select the self.parameters one if it exists
        prompt.objChoices.addItem(self.parameters["objectID"])  # Add the previously selected item at the top
        objectList = self.getObjectList()
        for objectID in objectList: prompt.objChoices.addItem(objectID)


        # Populate the accuracayChoices with a list of different possible accuracies

        for choice in self.accChoices: prompt.accChoices.addItem(choice)
        prompt.accChoices.setCurrentIndex(self.parameters["confidence"])


        # Set up the Age slider
        def updateAgeSliderLabel():
            # Create the text next to the "How Recently" label
            newText = "When: "
            if prompt.ageSlider.value() == 1:
                newText += "Just now"
            else:
                newText += "< " + str(prompt.ageSlider.value()) + " frames"
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
                       "confidence": acc,
                              "not": prompt.notCheck.isChecked()}

        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        objName = (self.parameters["objectID"], "Object")[len(self.parameters["objectID"]) == 0]
        self.title = "Test If " + objName + " Seen"

        confidenceText = ["slightly", "fairly", "highly"]

        self.description = "If"
        if self.parameters["not"]: self.description += " NOT"
        self.description += " " + confidenceText[self.parameters["confidence"]] + " confident object was seen"


class TestObjectLocationCommand(CommandGUI):
    title     = "Test If Object Inside Region"
    tooltip   = "This command will allow code in blocked brackets below it to run IF the specified object has been" \
                "recognized and the objects location in a particular location."
    icon      = Paths.command_test_region

    def __init__(self, env, parameters=None):
        super(TestObjectLocationCommand, self).__init__(parameters)

        objManager         = env.getObjectManager()
        self.vStream       = env.getVStream()
        self.getObjectList = lambda: objManager.getObjectNameList(typeFilter=objManager.TRACKABLE)

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
        choiceLbl = QtWidgets.QLabel("Choose an Object ")
        partLbl   = QtWidgets.QLabel("What part of object must enter the location ")
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
        for objectID in objectList: prompt.objChoices.addItem(objectID)


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
        self.title = "Test If " + objName + " Inside Region"


        self.description = "If " + self.parameters["part"] + " of " + objName + " is"
        if self.parameters["not"]: self.description += " NOT"
        self.description += " seen within a region"


class TestObjectAngleCommand(CommandGUI):
    title     = "Test Angle Of Object"
    tooltip   = "This command will allow code in blocked brackets below it to run IF the object's rotation is\n"\
                "between two angles. The angles are measured from the robots positive X axis, counter clockwise. The\n"\
                "positive X axis is 0 degrees, the positive Y axis is 90 degrees, the negative X axis is 180degrees,\n"\
                "and so on."
    icon      = Paths.command_test_angle

    def __init__(self, env, parameters=None):
        super(TestObjectAngleCommand, self).__init__(parameters)

        objManager         = env.getObjectManager()
        self.getObjectList = lambda: objManager.getObjectNameList(typeFilter=objManager.TRACKABLE)

        # If parameters do not exist, then set up the default parameters
        if self.parameters is None:
            # Anything done with env should be done here. Try not to save env as a class variable whenever possible
            self.parameters = {"objectID":    "",
                                  "start":   "0",
                                    "end": "360",
                                    "not": False}

    def dressWindow(self, prompt):
        # Create a Combobox with the appropriate items
        choiceLbl = QtWidgets.QLabel("Choose an object ")
        prompt.objChoices = QtWidgets.QComboBox()
        prompt.objChoices.addItem(self.parameters["objectID"])  # Add an empty item at the top
        objectList = self.getObjectList()
        for objectID in objectList: prompt.objChoices.addItem(objectID)
        self._addRow(prompt, choiceLbl, prompt.objChoices)


        prompt.valLEdit = QtWidgets.QLineEdit()
        prompt.valUEdit = QtWidgets.QLineEdit()


        # "Lower" Textbox
        valLLbl = QtWidgets.QLabel('Start Angle ')
        prompt.valLEdit.setText(str(self.parameters['start']))
        self._addRow(prompt, valLLbl, prompt.valLEdit)

        # "Upper" Textbox
        valULbl = QtWidgets.QLabel('End Angle ')
        prompt.valUEdit.setText(str(self.parameters['end']))
        self._addRow(prompt, valULbl, prompt.valUEdit)

        # "Not" Checkbox
        notLbl = QtWidgets.QLabel("NOT")
        prompt.notCheck    = QtWidgets.QCheckBox()  # "Not" CheckBox
        prompt.notCheck.setChecked(self.parameters["not"])
        self._addRow(prompt, notLbl, prompt.notCheck)

        self._addObjectHint(prompt, len(self.getObjectList()))
        return prompt

    def _extractPromptInfo(self, prompt):

        newParameters = {"objectID": prompt.objChoices.currentText(),
                         "start":    self._sanitizeEval(prompt.valLEdit, self.parameters["start"]),
                         "end":      self._sanitizeEval(prompt.valUEdit, self.parameters["end"]),
                         "not":      prompt.notCheck.isChecked()}

        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        objName = (self.parameters["objectID"], "Object")[len(self.parameters["objectID"]) == 0]
        self.title = "Test Angle of " + objName


        self.description = "If angle is"

        if self.parameters["not"]: self.description += " NOT"
        self.description += " between (" + self.parameters["start"] + ", " + self.parameters["end"] + ") degrees from the X Axis"






#   LOGIC COMMANDS
class StartBlockCommand(CommandGUI):
    """
    Start a block of code with this class
    """

    icon      = Paths.command_startblock
    tooltip   = "This is the start of a block of commands that only run if a conditional statement is met."

    def __init__(self, env, parameters=None):
        super(StartBlockCommand, self).__init__(parameters)


class EndBlockCommand(CommandGUI):
    """
    End a block of code with this command
    """

    icon      = Paths.command_endblock
    tooltip   = "This is the end of a block of commands."

    def __init__(self, env, parameters=None):
        super(EndBlockCommand, self).__init__(parameters)


class ElseCommand(CommandGUI):
    """
    End a block of code with this command
    """

    icon      = Paths.command_else
    tooltip   = "This will run commands if a test evaluates to False"

    def __init__(self, env, parameters=None):
        super(ElseCommand, self).__init__(parameters)


class SetVariableCommand(CommandGUI):
    title     = "Set Variable"
    tooltip   = "This command can create a variable or set an existing variable to a value or an expression."
    icon      = Paths.command_set_var

    def __init__(self, env, parameters=None):
        super(SetVariableCommand, self).__init__(parameters)

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
        namLabel = QtWidgets.QLabel('Variable Name ')
        valLabel = QtWidgets.QLabel('Expression ')

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


class TestVariableCommand(CommandGUI):
    title     = "Test Value"
    tooltip   = "This will allow/disallow code to run that is in blocked brackets below it IF the test is true."
    icon      = Paths.command_test_var

    def __init__(self, env, parameters=None):
        super(TestVariableCommand, self).__init__(parameters)


        if self.parameters is None:
            self.parameters = {'expressionA': '',
                               'test': 0,
                               'expressionB': ''}

    def dressWindow(self, prompt):
        prompt.valAEdit = QtWidgets.QLineEdit()  # "Variable" edit
        prompt.tstMenu = QtWidgets.QComboBox()
        prompt.valBEdit = QtWidgets.QLineEdit()

        prompt.tstMenu.addItem('Equal To')
        prompt.tstMenu.addItem('Not Equal To')
        prompt.tstMenu.addItem('Greater Than')
        prompt.tstMenu.addItem('Less Than')

        # Set up all the labels for the inputs
        valALabel = QtWidgets.QLabel('Expression ')
        tstLabel  = QtWidgets.QLabel('Test ')
        valBLabel = QtWidgets.QLabel('Expression ')

        # Fill the textboxes with the default parameters
        prompt.valAEdit.setText(str(self.parameters['expressionA']))
        prompt.tstMenu.setCurrentIndex(self.parameters['test'])
        prompt.valBEdit.setText(str(self.parameters['expressionB']))
        # prompt.notCheck.setChecked(self.parameters['not'])

        self._addRow(prompt, valALabel, prompt.valAEdit)
        self._addRow(prompt, tstLabel, prompt.tstMenu)
        self._addRow(prompt, valBLabel, prompt.valBEdit)

        return prompt

    def _extractPromptInfo(self, prompt):
        newParameters = {'expressionA': self._sanitizeEval(prompt.valAEdit, self.parameters['expressionA']),
                         'test': prompt.tstMenu.currentIndex(),
                         'expressionB': self._sanitizeEval(prompt.valBEdit, self.parameters['expressionB'])}  # This can't be sanitized, unfortunately :/

        self.parameters.update(newParameters)
        return self.parameters

    def _updateDescription(self):
        operations = [' equal to', ' not equal to', ' greater than', ' less than']
        self.description = 'If ' + str(self.parameters['expressionA']) + ' is' + operations[self.parameters['test']] + \
                           ' ' + self.parameters['expressionB'] + ' then'


class LoopCommand(CommandGUI):
    title     = "Loop While Test Is True"
    tooltip   = "Repeat this section of commands while a certain test returns true. You can choose what type of test\n"\
                "will be used. "
    icon      = Paths.command_loop

    def __init__(self, env, parameters=None):
        super(LoopCommand, self).__init__(parameters)
        self.env = env
        # If parameters do not exist, then set up the default parameters
        if self.parameters is None:
            # Anything done with env should be done here. Try not to save env as a class variable whenever possible
            self.parameters = {"testType": "",
                               "testParameters": None,
                               "description": "Loops commands while a chosen test is true"}

    def dressWindow(self, prompt):
        def updateTestParameters():
            clearLayout(prompt.fakePrompt.content)
            currTitle = prompt.testChoices.currentText()

            testType = prompt.titleTypeHash[currTitle]

            # print(self.parameters["testType"] == testType, self.parameters["testType"], testType)
            if self.parameters["testType"] == testType.__name__:
                params = self.parameters["testParameters"]
            else:
                params = None

            # Create the object and dress the window with the custom widget that emulates being "prompt"
            prompt.commandObject = testType(self.env, params)
            prompt.commandObject.dressWindow(prompt.fakePrompt)

            # Refresh the window to match the side of the new widget. Do it with a timer so GUI can render the wndow 1st
            QtCore.QTimer.singleShot(10, lambda: prompt.resize(prompt.sizeHint()))


        # Create a Combobox with the appropriate items
        choiceLbl = QtWidgets.QLabel("Choose a Test")
        prompt.testChoices = QtWidgets.QComboBox()

        prompt.titleTypeHash = {}


        # Get the title of the currently selected testType when loading
        for testType in testTypes:
            prompt.titleTypeHash[testType.title] = testType

            if self.parameters["testType"] == testType.__name__:
                prompt.testChoices.addItem(testType.title)


        for testType in testTypes: prompt.testChoices.addItem(testType.title)



        prompt.testChoices.currentIndexChanged.connect(updateTestParameters)
        self._addRow(prompt, choiceLbl, prompt.testChoices, resizeBox=False)
        self._addSpacer(prompt)
        prompt.fakePrompt = QtWidgets.QWidget()
        prompt.fakePrompt.content = QtWidgets.QVBoxLayout()
        prompt.fakePrompt.setLayout(prompt.fakePrompt.content)
        prompt.content.addWidget(prompt.fakePrompt)

        updateTestParameters()
        return prompt

    def _extractPromptInfo(self, prompt):
        prompt.commandObject._extractPromptInfo(prompt.fakePrompt)
        prompt.commandObject._updateDescription()

        chosenType = type(prompt.commandObject)
        chosenParams = prompt.commandObject.parameters
        description  = prompt.commandObject.description

        # Find the matching type for the currently selected title
        newParameters = {"testType": chosenType.__name__,
                         "testParameters": chosenParams,
                         "description": description}  # Get the parameters from the 'prompt' GUI elements. Put numbers through self.sanitizeFloat

        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        self.description = self.parameters["description"]  # Some string that uses your parameters to describe the object.


class EndTaskCommand(CommandGUI):
    title     = "End Task"
    tooltip   = "When the code reaches this point, the program will end."
    icon      = Paths.command_end_script

    def __init__(self, env, parameters=None):
        super(EndTaskCommand, self).__init__(parameters)


class EndEventCommand(CommandGUI):
    title     = "Exit Current Event"
    tooltip   = "When the code reaches this point, the program will not process the rest of this event."
    icon      = Paths.command_exit_event

    def __init__(self, env, parameters=None):
        super(EndEventCommand, self).__init__(parameters)




#   FUNCTION COMMANDS
class ScriptCommand(CommandGUI):
    title     = "Run Python Code"
    tooltip   = "This tool will execute a script made by the user.\nDO NOT RUN PROGRAMS WITH SCRIPTS WRITTEN BY OTHER" \
                "\nUSERS UNLESS YOU HAVE CHECKED THE SCRIPT AND KNOW WHAT YOU ARE DOING!"
    icon      = Paths.command_script

    def __init__(self, env, parameters=None):
        super(ScriptCommand, self).__init__(parameters)

        # If parameters do not exist, then set up the default parameters
        if self.parameters is None:
            # Anything done with env should be done here. Try not to save env as a class variable whenever possible
            self.parameters = {"script":      "",
                               "description": ""}

    def dressWindow(self, prompt):
        # Do some GUI code setup
        # Put all the objects into horizontal layouts called Rows
        prompt.IDE     = ScriptWidget(self.parameters["script"], prompt)
        descriptionLbl = QtWidgets.QLabel("Description ")

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
        self.description = self.parameters["description"]


class RunTaskCommand(CommandGUI):
    title     = "Run Task"
    tooltip   = "This tool will run  another task file and run it inside of this task, until the 'End Task'\n" \
                "command is called within the task, then it will return to the currently running task.\n" \
                "All tasks are preloaded when script is launched, so if a child class runs a parent class, an error\n" \
                "will be returned."

    icon      = Paths.command_run_task

    def __init__(self, env, parameters=None):
        super(RunTaskCommand, self).__init__(parameters)

        # If parameters do not exist, then set up the default parameters
        if self.parameters is None:
            # Anything done with env should be done here. Try not to save env as a class variable whenever possible
            self.parameters = {"filename": "",
                               "shareScope": False}

    def dressWindow(self, prompt):
        def updateFileLbl(prompt):
            chosenFile, _ = QtWidgets.QFileDialog.getOpenFileName(parent=prompt,
                                                                  caption="Load Task",
                                                                  filter="Task (*.task)",
                                                                  directory=Paths.saves_dir)
            if chosenFile == "": return
            prompt.fileLbl.setText(chosenFile)

        ensurePathExists(Paths.saves_dir)

        explanationLbl = QtWidgets.QLabel("\n\nMake sure the task you run has an\n"
                                          "'End Task' command in it, to return to\n"
                                          "this task when its finished")

        # Create the filename label
        prompt.fileLbl = QtWidgets.QLabel(self.parameters["filename"])
        prompt.fileLbl.setWordWrap(True)
        prompt.fileLbl.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        fileBtn = QtWidgets.QPushButton("Select Task")
        fileBtn.clicked.connect(lambda: updateFileLbl(prompt))

        # Create the "Share Variables" checkbox
        shareLbl = QtWidgets.QLabel("Share Current Tasks Variables")
        prompt.shareChk = QtWidgets.QCheckBox()
        prompt.shareChk.setChecked(self.parameters["shareScope"])

        # self._addRow(prompt, fileBtn)
        self._addRow(prompt, prompt.fileLbl, fileBtn)
        self._addRow(prompt, shareLbl, prompt.shareChk)
        self._addRow(prompt, explanationLbl)


        return prompt

    def _extractPromptInfo(self, prompt):
        newParameters = {"filename": str(prompt.fileLbl.text()),
                         "shareScope": prompt.shareChk.isChecked()}

        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        if len(self.parameters["filename"]) == 0:
            self.description = "No Task Selected"
        else:
            self.description = "Run " + basename(self.parameters["filename"])


class RunFunctionCommand(CommandGUI):
    title     = "Run Function"
    tooltip   = "This will run a custom function that the user defines in the Resources menu. If the function has \n" \
                "arguments, the user will be prompted to fill out the arguments"
    icon      = Paths.command_run_func

    def __init__(self, env, parameters=None):
        super(RunFunctionCommand, self).__init__(parameters)
        self.objManager = env.getObjectManager()
        self.getObjectList = lambda: self.objManager.getObjectNameList(typeFilter=self.objManager.FUNCTION)

        # If parameters do not exist, then set up the default parameters
        if self.parameters is None:
            # Anything done with env should be done here. Try not to save env as a class variable whenever possible
            self.parameters = {"objectID": "",
                               "description": "",
                               "arguments": {}}  # A list of {"arg": "expression", "arg2": "expression2}

    def dressWindow(self, prompt):


        def updateArguments():
            # Hide irrelevant arguments
            for arg in prompt.argumentEdits: prompt.argumentEdits[arg].hide()
            for arg in prompt.argumentLbls:  prompt.argumentLbls[arg].hide()

            # Get the current object
            chosenID  = str(prompt.objChoices.currentText())
            chosenObj = self.objManager.getObject(chosenID)

            # If the object does not exist anymore, exit
            if chosenObj is None: return

            # Iterate through the arguments
            arguments = chosenObj.getArguments()
            for arg in arguments:
                # If the argument already has a widget associated with it, show the widget
                if arg in prompt.argumentEdits is not None:
                    prompt.argumentEdits[arg].show()
                    prompt.argumentLbls[arg].show()
                    continue

                # If the argument doesn't have a widget associated with it, create it and store it
                argLbl = QtWidgets.QLabel(arg)
                argEdt = QtWidgets.QLineEdit()
                argEdt.setFixedWidth(self.defaultTextBoxWidth)

                prompt.argumentEdits[arg] = argEdt
                prompt.argumentLbls[arg]  = argLbl
                row = QtWidgets.QHBoxLayout()
                row.addStretch()
                row.addWidget(argLbl)
                row.addWidget(argEdt)
                prompt.argLayout.addLayout(row)



        # Create a Combobox with Functions made in resources
        choiceLbl = QtWidgets.QLabel("Choose a Function ")
        prompt.objChoices = QtWidgets.QComboBox()
        prompt.objChoices.addItem(self.parameters["objectID"])  # Add an empty item at the top
        objectList = self.getObjectList()
        for objectID in objectList: prompt.objChoices.addItem(objectID)
        self._addRow(prompt, choiceLbl, prompt.objChoices)

        prompt.argLayout = QtWidgets.QVBoxLayout()  # This is where the argument queries will be made
        prompt.content.addLayout(prompt.argLayout)
        prompt.objChoices.currentIndexChanged.connect(lambda: updateArguments())


        # These two arrays store the widgets associated with each argument
        prompt.argumentEdits = {}
        prompt.argumentLbls  = {}

        updateArguments()  # This generates the list of arguments

        # Repopulate existing arguments
        for key in prompt.argumentEdits:
            if key in self.parameters["arguments"]:
                prompt.argumentEdits[key].setText(self.parameters["arguments"][key])

        self._addFunctionHint(prompt, len(objectList))
        return prompt

    def _extractPromptInfo(self, prompt):
        chosenID  = str(prompt.objChoices.currentText())
        chosenObj = self.objManager.getObject(chosenID)

        if chosenObj is not None:
            args = chosenObj.getArguments()
            argVals = {}
            for arg in args:
                argVals[arg] = prompt.argumentEdits[arg].text()

            newParameters = {"objectID": chosenID,
                             "description": chosenObj.getDescription(),
                             "arguments": argVals}
        else:
            newParameters = {"objectID": chosenID,
                             "description": "",
                             "arguments": self.parameters["arguments"]}

        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        if len(self.parameters["objectID"]) == 0:
            self.description = "No function selected"
            self.title = "Run Function"
        else:
            self.description = self.parameters["description"]
            self.title = self.parameters["objectID"]



#   EXPERIMENTAL COMMANDS
class VisionMoveXYZCommand(MoveXYZCommand):
    title     = "Vision Assisted Move XYZ"
    tooltip   = "This works like the normal Move XYZ command, but uses vision to verify the robots position and\n"\
                "perform a 'correction' move after an initial move. \n" \
                "This command requires Camera/Robot Calibrations to be done."
    icon      = Paths.command_xyz_vision

    def __init__(self, env, parameters=None):
        super(VisionMoveXYZCommand, self).__init__(env, parameters)

    def dressWindow(self, prompt):
        super(VisionMoveXYZCommand, self).dressWindow(prompt)
        warningLbl = QtWidgets.QLabel("This function is experimental. It may not yield more accurate results.")
        warningLbl.setWordWrap(True)

        self._addRow(prompt, warningLbl)

        return prompt




def clearLayout(layout):
    if layout is not None:
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                clearLayout(child.layout())


# All commands that do "Tests"
testTypes = [TestVariableCommand, TestObjectSeenCommand, TestObjectLocationCommand, TestObjectAngleCommand]



