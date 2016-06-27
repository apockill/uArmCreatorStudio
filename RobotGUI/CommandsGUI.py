import ast  # To check if a statement is python parsible, for evals
from PyQt5                        import QtGui, QtCore, QtWidgets
from RobotGUI                     import Icons
from RobotGUI.Logic.Global        import printf
from RobotGUI.Logic.ObjectManager import TrackableObject


# This should only be used once, in CommandList.addCommand
class CommandWidget(QtWidgets.QWidget):
    def __init__(self, parent, onDeleteFunction):
        super(CommandWidget, self).__init__(parent)

        # Set up Globals
        self.indent = 0
        self.margins = None  # Is set after initUI creates it's first layout
        # Set up UI Globals
        self.title = QtWidgets.QLabel()
        self.description = QtWidgets.QLabel()
        self.icon = QtWidgets.QLabel("No Icon Found")
        self.deleteBtn = QtWidgets.QPushButton("")

        self.initUI()
        self.margins = self.layout().getContentsMargins()  # Has to be after initUI()
        self.setIndent(0)
        # Connect the delete button with a function in the CommandList widget that will delete selected commands
        self.deleteBtn.clicked.connect(onDeleteFunction)

    def initUI(self):
        # Create the delete button
        self.deleteBtn.setFlat(True)
        self.deleteBtn.setIcon(QtGui.QIcon(Icons.delete))
        self.deleteBtn.setVisible(False)

        font = QtGui.QFont()
        font.setBold(True)
        self.title.setFont(font)

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
        self.addTab(self.generatePickupTab(), "Vision")
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
        add(SpeedCommandGUI)
        add(AttachCommandGUI)
        add(DetachCommandGUI)
        add(GripCommandGUI)
        add(DropCommandGUI)
        add(WaitCommandGUI)
        add(BuzzerCommandGUI)


        return tabWidget

    def generateLogicTab(self):
        tabWidget = QtWidgets.QWidget()
        vBox = QtWidgets.QVBoxLayout()
        vBox.setAlignment(QtCore.Qt.AlignTop)
        tabWidget.setLayout(vBox)
        add  = lambda btnType: vBox.addWidget(self.getButton(btnType))

        add(SetVariableCommandGUI)
        add(TestVariableCommandGUI)
        add(ElseCommandGUI)
        add(StartBlockCommandGUI)
        add(EndBlockCommandGUI)
        add(EndEventCommandGUI)
        add(EndProgramCommandGUI)


        return tabWidget

    def generatePickupTab(self):
        tabWidget = QtWidgets.QWidget()
        vBox = QtWidgets.QVBoxLayout()
        vBox.setAlignment(QtCore.Qt.AlignTop)
        tabWidget.setLayout(vBox)
        add  = lambda btnType: vBox.addWidget(self.getButton(btnType))

        add(FocusOnObjectCommandGUI)

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
            # printf("Command.openView(): About to execute self...", self, super(Command, self), self.parent)
            return True

        ##### Create the base window #####

        def applyClicked(prompt):
            prompt.accepted = True
            prompt.close()

        def cancelClicked(prompt):
            prompt.accepted = False
            prompt.close()

        prompt = QtWidgets.QDialog()

        applyBtn = QtWidgets.QPushButton('Apply')
        cancelBtn = QtWidgets.QPushButton('Cancel')

        applyBtn.setMaximumWidth(100)
        cancelBtn.setMaximumWidth(100)

        applyBtn.clicked.connect(lambda: applyClicked(prompt))
        cancelBtn.clicked.connect(lambda: cancelClicked(prompt))


        # Create a content box for the command to fill out parameters and GUI elements
        prompt.content    = QtWidgets.QVBoxLayout()
        prompt.content.setContentsMargins(20, 10, 20, 10)
        contentGroupBox = QtWidgets.QGroupBox("Parameters")
        contentGroupBox.setLayout(prompt.content)

        # Create the main vertical layout, add the contentBox to it
        prompt.mainVLayout = QtWidgets.QVBoxLayout()
        prompt.mainVLayout.addWidget(contentGroupBox)
        prompt.mainVLayout.addStretch(1)

        # Dress the base window (this is where the child actually puts the content into the widget)
        prompt = self.dressWindow(prompt)


        # Now that the window is 'dressed', add "Cancel" and "Apply" buttons
        buttonRow         = QtWidgets.QHBoxLayout()
        buttonRow.addWidget(cancelBtn)
        buttonRow.addStretch(1)
        buttonRow.addWidget(applyBtn)
        prompt.mainVLayout.addLayout(buttonRow)

        # Set the main layout and general window parameters
        prompt.setFixedWidth(350)
        prompt.setMinimumHeight(350)
        prompt.setLayout(prompt.mainVLayout)
        prompt.setWindowTitle(self.title)
        prompt.setWindowIcon(QtGui.QIcon(self.icon))
        prompt.setWhatsThis(self.tooltip)  # This makes the "Question Mark" button on the window show the tooltip msg





        # Run the info window and prevent other windows from being clicked while open:
        printf("Command.openView(): Finished executing self...")
        prompt.exec_()


        # Get information that the user input
        if prompt.accepted:
            # Get information that the user input
            self._extractPromptInfo(prompt)

            # Update self.description for the widget to be dressed with after, by CommandList
            self._updateDescription()
            printf('CommandWindow.openView(): New parameters: ', self.parameters)

        else:
            printf('CommandWindow.openView(): User Canceled.')


        # Make sure QT properly handles the memory
        # prompt.close()
        # prompt.deleteLater()

        return prompt.accepted

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
        possibleNumber = str(inputTextbox.text())
        possibleNumber.replace(".", "")  # For isnumeric() to work, there can't be a decimal point

        if possibleNumber.isnumeric():
            return fallback

        return possibleNumber


    # The following are helper functions for modifying the prompt window in a consistent way
    def _addRow(self, prompt, leftWidget, rightItem):
        # Creates and adds a row to prompt.content, with proper formatting
        row = QtWidgets.QHBoxLayout()
        row.addStretch(1)
        row.addWidget(leftWidget)
        row.addWidget(rightItem)
        prompt.content.addLayout(row)

    def _addHint(self, prompt, hintText):
        # Add some text (usually at the bottom of the prompt) that tells the user something to help them out
        hintLbl = QtWidgets.QLabel(hintText)
        hintLbl.setWordWrap(True)
        # Make the hint bold
        bold = QtGui.QFont()
        bold.setBold(True)
        hintLbl.setFont(bold)

        # Create a row for the hint
        hintRow = QtWidgets.QHBoxLayout()
        hintRow.addStretch(1)
        hintRow.addWidget(hintLbl)

        # Add it to the prompt
        prompt.mainVLayout.addLayout(hintRow)




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

Example of a fully filled out class:

class NameCommandGUI(CommandGUI):
    title     = "Example Title"
    tooltip   = "This tool does X Y and Z"
    icon      = Icons.some_icon
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
        row1 = QtWidgets.QHBoxLayout()
        prompt.content.addLayout(row1) # and so on for all of the rows

        return prompt

    def extractPromptInfo(self, prompt):
        newParameters = {} # Get the parameters from the 'prompt' GUI elements. Put numbers through self.sanitizeFloat

        self.parameters.update(newParameters)

        return self.parameters

    def updateDescription(self):
        self.description = ""  # Some string that uses your parameters to describe the object.

"""

#   BASIC CONTROL COMMANDS
class MoveXYZCommandGUI(CommandGUI):
    title     = "Move XYZ"
    tooltip   = "Set the robots position. The robot will move after all events are evaluated"
    icon      = Icons.xyz_command
    logicPair = 'MoveXYZCommand'

    def __init__(self, env, parameters=None):
        super(MoveXYZCommandGUI, self).__init__(parameters)

        if self.parameters is None:
            # If no parameters were given, it's a new command. Thus, get the robots current position and fill it in.
            # This helps with workflow so you can create MoveXYZ commands and move the robot around as you work with it
            currentXYZ = env.getRobot().getCurrentCoord()

            self.parameters = {'x': round(currentXYZ[0], 1),
                               'y': round(currentXYZ[1], 1),
                               'z': round(currentXYZ[2], 1),
                               'relative': False,
                               'override': False}

    def dressWindow(self, prompt):
        # Prompt is a QDialog type, this is simply a function to dress it up with the appropriate interface
        # Then it's returned, and the Command.openView() function will open the window and perform appropriate actions

        # Input: the base window with the cancel and apply buttons, and the layouts set up and connected
        prompt.rotEdit = QtWidgets.QLineEdit()  # Rotation textbox
        prompt.strEdit = QtWidgets.QLineEdit()  # Stretch textbox
        prompt.hgtEdit = QtWidgets.QLineEdit()  # Height textbox
        prompt.ovrCheck = QtWidgets.QCheckBox()  # "override" CheckBox
        prompt.rltCheck = QtWidgets.QCheckBox()  # "relative" CheckBox

        # Set up all the labels for the inputs
        rotLabel = QtWidgets.QLabel('X ')
        strLabel = QtWidgets.QLabel('Y ')
        hgtLabel = QtWidgets.QLabel('Z ')
        ovrCheck = QtWidgets.QLabel('Override Ongoing Movement: ')
        rltCheck = QtWidgets.QLabel('Relative: ')

        # Fill the textboxes with the default parameters
        prompt.rotEdit.setText(str(self.parameters['x']))
        prompt.strEdit.setText(str(self.parameters['y']))
        prompt.hgtEdit.setText(str(self.parameters['z']))
        prompt.ovrCheck.setChecked(self.parameters['override'])
        prompt.rltCheck.setChecked(self.parameters['relative'])


        self._addRow(prompt, rotLabel, prompt.rotEdit)
        self._addRow(prompt, strLabel, prompt.strEdit)
        self._addRow(prompt, hgtLabel, prompt.hgtEdit)
        self._addRow(prompt, ovrCheck, prompt.ovrCheck)
        self._addRow(prompt, rltCheck, prompt.rltCheck)

        return prompt

    def _extractPromptInfo(self, prompt):
        # Update the parameters and the description
        newParameters = {'x': self._sanitizeEval(prompt.rotEdit, self.parameters["x"]),
                         'y': self._sanitizeEval(prompt.strEdit, self.parameters["y"]),
                         'z': self._sanitizeEval(prompt.hgtEdit, self.parameters["z"]),
                         'override': prompt.ovrCheck.isChecked(),
                         'relative': prompt.rltCheck.isChecked()}

        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        # Update the description, for the dressWidget() and the openView() prompt
        self.description =    'X: ' + str(self.parameters['x']) + \
                           '   Y: ' + str(self.parameters['y']) + \
                           '   Z: ' + str(self.parameters['z'])

        if self.parameters['override']: self.description += '   Override'
        if self.parameters['relative']: self.description += '   Relative'


class MoveWristCommandGUI(CommandGUI):
    title     = "Set Wrist Angle"
    tooltip   = "This command sets the angle of the robots 4th axis, the wrist."
    icon      = Icons.move_wrist_command
    logicPair = "MoveWristCommand"

    def __init__(self, env, parameters=None):
        super(MoveWristCommandGUI, self).__init__(parameters)


        if self.parameters is None:
            currentWrist = env.getRobot().getServoAngle(4)
            self.parameters = {"angle": str(currentWrist),
                               "relative": False}


    def dressWindow(self, prompt):


        # Create what the user will be interacting with
        prompt.wristEdit = QtWidgets.QLineEdit()
        prompt.rltCheck  = QtWidgets.QCheckBox()  # "relative" CheckBox

        # Create the labels for the interactive stuff
        wristLabel       = QtWidgets.QLabel('Wrist Angle:')
        rltLabel         = QtWidgets.QLabel('Relative:')

        # Set up everything so it matches the current parameters
        prompt.wristEdit.setText(  self.parameters["angle"])
        prompt.rltCheck.setChecked(self.parameters["relative"])

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


class SpeedCommandGUI(CommandGUI):
    title     = "Set Speed"
    tooltip   = "This tool sets the speed of the robot for any move commands that are done after this. "
    icon      = Icons.speed_command
    logicPair = "SpeedCommand"

    def __init__(self, env, parameters=None):
        super(SpeedCommandGUI, self).__init__(parameters)

        if self.parameters is None:
            # Some code to set up default parameters
            robot = env.getRobot()
            self.parameters = {"speed": str(robot.speed)}

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
    icon      = Icons.detach_command
    logicPair = "DetachCommand"

    def __init__(self, env, parameters=None):
        super(DetachCommandGUI, self).__init__(parameters)

        if self.parameters is None:
            self.parameters = {'servo1': False,
                               'servo2': False,
                               'servo3': False,
                               'servo4': False}


    def dressWindow(self, prompt):
        # Do some GUI code setup
        # Put all the objects into horizontal layouts called Rows
        prompt.srvo1Box = QtWidgets.QCheckBox()  # Rotation textbox
        prompt.srvo2Box = QtWidgets.QCheckBox()  # Stretch textbox
        prompt.srvo3Box = QtWidgets.QCheckBox()  # Height textbox
        prompt.srvo4Box = QtWidgets.QCheckBox()  # "relative" CheckBox

        # Set up all the labels for the inputs
        label1 = QtWidgets.QLabel('Rotation Servo:')
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
        if self.parameters["servo1"]: descriptionBuild += "  Rotation"
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
    icon      = Icons.attach_command
    logicPair = "AttachCommand"

    def __init__(self, env, parameters=None):
        super(AttachCommandGUI, self).__init__(parameters)

        if self.parameters is None:
            self.parameters = {'servo1': False,
                               'servo2': False,
                               'servo3': False,
                               'servo4': False}


    def dressWindow(self, prompt):
        # Do some GUI code setup
        # Put all the objects into horizontal layouts called Rows
        prompt.srvo1Box = QtWidgets.QCheckBox()  #  Rotation textbox
        prompt.srvo2Box = QtWidgets.QCheckBox()  #  Stretch textbox
        prompt.srvo3Box = QtWidgets.QCheckBox()  #  Height textbox
        prompt.srvo4Box = QtWidgets.QCheckBox()  #  "relative" CheckBox

        # Set up all the labels for the inputs
        label1 = QtWidgets.QLabel('Rotation Servo:')
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
        if self.parameters["servo1"]: descriptionBuild += "  Rotation"
        if self.parameters["servo2"]: descriptionBuild += "  Stretch"
        if self.parameters["servo3"]: descriptionBuild += "  Height"
        if self.parameters["servo4"]: descriptionBuild += "  Wrist"

        self.description = descriptionBuild


class WaitCommandGUI(CommandGUI):
    title     = "Wait"
    tooltip   = "Halts the program for a preset amount of time"
    icon      = Icons.wait_command
    logicPair = "WaitCommand"

    def __init__(self, env, parameters=None):
        super(WaitCommandGUI, self).__init__(parameters)

        if self.parameters is None:
            self.parameters = {'time': 1.0}
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
    icon      = Icons.grip_command
    logicPair = "GripCommand"

    def __init__(self, env, parameters=None):
        super(GripCommandGUI, self).__init__(parameters)


class DropCommandGUI(CommandGUI):
    title     = "Deactivate Gripper"
    tooltip   = "Deactivates the robots gripper"
    icon      = Icons.drop_command
    logicPair = "DropCommand"

    def __init__(self, env, parameters=None):
        super(DropCommandGUI, self).__init__(parameters)


class BuzzerCommandGUI(CommandGUI):
    title     = "Play Tone"
    tooltip   = "This tool uses the robots buzzer to play a tone at a certain frequency for a certain amount of time"
    icon      = Icons.buzzer_command
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


        prompt.frqEdit.setFixedWidth(self.defaultTextBoxWidth)
        prompt.tmeEdit.setFixedWidth(self.defaultTextBoxWidth)

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
    title     = "Ends Program"
    tooltip   = "When the code reaches this point, the program will end."
    icon      = Icons.pause_script
    logicPair = "EndProgramCommand"

    def __init__(self, env, parameters=None):
        super(EndProgramCommandGUI, self).__init__(parameters)


class EndEventCommandGUI(CommandGUI):
    title     = "Exit Current Event"
    tooltip   = "When the code reaches this point, the program will not process the rest of this event."
    icon      = Icons.exit_event_command
    logicPair = "EndEventCommand"

    def __init__(self, env, parameters=None):
        super(EndEventCommandGUI, self).__init__(parameters)





#   Robot + Vision COmmands
class FocusOnObjectCommandGUI(CommandGUI):
    title     = "Move Robot Over Object"
    tooltip   = "This tool uses computer vision to recognize an object of your choice, and position the robot directly"\
                " over the object of choice, if it is visible. If it cannot be found, False will be returned."
    icon      = Icons.move_over_command
    logicPair = "FocusOnObjectCommand"

    def __init__(self, env, parameters=None):
        super(FocusOnObjectCommandGUI, self).__init__(parameters)

        objectManager = env.getObjectManager()

        # Save a list that gets all loaded objects. This is used only when the window is opened, to populate the objlist
        self.getObjectList  = objectManager.getObjectIDList

        if self.parameters is None:
            self.parameters = {"objectID": ""}

    def dressWindow(self, prompt):
        # Define what happens when the user changes the object selection

        choiceLbl = QtWidgets.QLabel("Choose an object: ")

        # Create a QComboBox
        prompt.objChoices = QtWidgets.QComboBox()
        prompt.objChoices.setMinimumWidth(150)


        # Add an empty item at the top if no object has ever been selected
        prompt.objChoices.addItem(self.parameters["objectID"])


        # Populate the comboBox with a list of all trackable objects, and select the self.parameters one if it exists
        objectList = self.getObjectList(objectType=TrackableObject)
        for index, objectID in enumerate(objectList):
            prompt.objChoices.addItem(objectID)


        self._addRow(prompt, choiceLbl, prompt.objChoices)

        # If there are no objects, place a nice label to let the user know
        if len(objectList) == 0:
            hintText = "You have not created any trackable objects yet." + \
                       "\nTry adding new objects in the Object Manager!"
            self._addHint(prompt, hintText)
        elif len(objectList) == 1:
            hintText = "It looks like you've only created one object." + \
                       " Feel free to add new objects in the Object Manager!"
            self._addHint(prompt, hintText)

        return prompt

    def _extractPromptInfo(self, prompt):
        # Get the parameters from the 'prompt' GUI elements. Put numbers through self.sanitizeFloat
        newParameters = {"objectID": prompt.objChoices.currentText()}

        print(newParameters)
        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        self.description = "Find " + self.parameters["objectID"] + " and move the robot over it"


class PickupObjectCommandGUI(CommandGUI):
    title     = "Pick Up an Object"
    tooltip   = "This tool uses computer vision to recognize an object of your choice, and attempt to pick up the " \
                "object. If the object cannot be found or picked up, then False will be returned"

    icon      = Icons.pickup_command
    logicPair = "PickupObjectCommand"

    def __init__(self, env, parameters=None):
        super(PickupObjectCommandGUI, self).__init__(parameters)

        objectManager = env.getObjectManager()

        # Save a list that gets all loaded objects. This is used only when the window is opened, to populate the objlist
        self.getObjectList  = objectManager.getObjectIDList

        if self.parameters is None:
            self.parameters = {"objectID": ""}

    def dressWindow(self, prompt):
        # Define what happens when the user changes the object selection

        choiceLbl = QtWidgets.QLabel("Choose an object: ")

        # Create a QComboBox
        prompt.objChoices = QtWidgets.QComboBox()
        prompt.objChoices.setMinimumWidth(150)


        # Add an empty item at the top if no object has ever been selected
        prompt.objChoices.addItem(self.parameters["objectID"])


        # Populate the comboBox with a list of all trackable objects, and select the self.parameters one if it exists
        objectList = self.getObjectList(objectType=TrackableObject)
        for index, objectID in enumerate(objectList):
            prompt.objChoices.addItem(objectID)


        self._addRow(prompt, choiceLbl, prompt.objChoices)


        # If there are no objects, place a nice label to let the user know
        if len(objectList) == 0:
            hintText = "You have not created any trackable objects yet." + \
                       "\nTry adding new objects in the Object Manager!"
            self._addHint(prompt, hintText)
        elif len(objectList) == 1:
            hintText = "It looks like you've only created one object(s)." + \
                       " Feel free to add new objects in the Object Manager!"
            self._addHint(prompt, hintText)

        return prompt

    def _extractPromptInfo(self, prompt):
        # Get the parameters from the 'prompt' GUI elements. Put numbers through self.sanitizeFloat
        newParameters = {"objectID": prompt.objChoices.currentText()}

        print(newParameters)
        self.parameters.update(newParameters)

        return self.parameters

    def _updateDescription(self):
        self.description = "Find " + self.parameters["objectID"] + " and move the robot over it"



#   LOGIC COMMANDS
class StartBlockCommandGUI(CommandGUI):
    """
    Start a block of code with this class
    """

    icon      = Icons.startblock_command
    tooltip   = "This is the start of a block of commands that only run if a conditional statement is met."
    logicPair = 'StartBlockCommand'

    def __init__(self, shared, parameters=None):
        super(StartBlockCommandGUI, self).__init__(parameters)


class EndBlockCommandGUI(CommandGUI):
    """
    End a block of code with this command
    """

    icon      = Icons.endblock_command
    tooltip   = "This is the end of a block of commands."
    logicPair = 'EndBlockCommand'

    def __init__(self, shared, parameters=None):
        super(EndBlockCommandGUI, self).__init__(parameters)


class ElseCommandGUI(CommandGUI):
    """
    End a block of code with this command
    """

    icon      = Icons.else_command
    tooltip   = "This will run commands if a test evaluates to False"
    logicPair = 'ElseCommand'

    def __init__(self, shared, parameters=None):
        super(ElseCommandGUI, self).__init__(parameters)


class SetVariableCommandGUI(CommandGUI):
    title     = "Set Variable"
    tooltip   = "This command can create a variable or set an existing variable to a value or an expression."
    icon      = Icons.set_var_command
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

        prompt.namEdit.setFixedWidth(self.defaultTextBoxWidth)
        prompt.valEdit.setFixedWidth(self.defaultTextBoxWidth)

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
    icon      = Icons.test_var_command
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
        # prompt.notCheck = QtWidgets.QCheckBox()  # "Not" CheckBox

        prompt.varEdit.setFixedWidth(self.defaultTextBoxWidth)
        prompt.tstMenu.setFixedWidth(self.defaultTextBoxWidth)
        prompt.valEdit.setFixedWidth(self.defaultTextBoxWidth)

        prompt.tstMenu.addItem('Equal To')
        prompt.tstMenu.addItem('Not Equal To')
        prompt.tstMenu.addItem('Greater Than')
        prompt.tstMenu.addItem('Less Then')

        # Set up all the labels for the inputs
        varLabel = QtWidgets.QLabel('Variable: ')
        tstLabel = QtWidgets.QLabel('Test: ')
        valLabel = QtWidgets.QLabel('Value: ')
        # notLabel = QtWidgets.QLabel('Not')

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




########### NON-UPDATED COMMANDS ########
