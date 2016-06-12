import ast  # To check if a statement is python parsible, for evals
from PyQt5                 import QtGui, QtCore, QtWidgets
from RobotGUI              import Icons
from RobotGUI.Logic.Global import printf


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


    def getMovementTab(self):
        tabWidget = QtWidgets.QWidget()
        vBox = QtWidgets.QVBoxLayout()
        vBox.setAlignment(QtCore.Qt.AlignTop)
        tabWidget.setLayout(vBox)
        add  = lambda btnType: vBox.addWidget(self.getButton(btnType))

        add(MoveXYZCommandGUI)
        add(MoveWristCommandGUI)
        add(AttachCommandGUI)
        add(DetachCommandGUI)
        add(GripCommandGUI)
        add(DropCommandGUI)
        add(WaitCommandGUI)


        return tabWidget

    def getLogicTab(self):
        tabWidget = QtWidgets.QWidget()
        vBox = QtWidgets.QVBoxLayout()
        vBox.setAlignment(QtCore.Qt.AlignTop)
        tabWidget.setLayout(vBox)
        add  = lambda btnType: vBox.addWidget(self.getButton(btnType))

        add(SetVariableCommandGUI)
        add(TestVariableCommandGUI)
        add(StartBlockCommandGUI)
        add(EndBlockCommandGUI)


        return tabWidget


    def initUI(self):
        movementTab = self.getMovementTab()
        logicTab    = self.getLogicTab()

        self.addTab(movementTab, "Basic")
        self.addTab(   logicTab, "Logic")
        # moveXYZBtn  = self.getButton(MoveXYZCommandGUI)
        # detachBtn   = self.getButton(DetachCommandGUI)
        # attachBtn   = self.getButton(AttachCommandGUI)
        # waitBtn     = self.getButton(WaitCommandGUI)
        # gripBtn     = self.getButton(GripCommandGUI)
        # dropBtn     = self.getButton(DropCommandGUI)

        # setVarBtn   = self.getButton(SetVariableCommandGUI)
        # testVarBtn  = self.getButton(TestVariableCommandGUI)
        # startBlkBtn = self.getButton(StartBlockCommandGUI)
        # endBlkBtn   = self.getButton(EndBlockCommandGUI)

        # colorBtn    = self.getButton(ColorTrackCommand)

        mainVLayout = QtWidgets.QVBoxLayout()
        # mainVLayout.addWidget(moveXYZBtn)
        # grid = QtWidgets.QGridLayout()
        # grid.addWidget( moveXYZBtn,  0, 0, QtCore.Qt.AlignTop)
        # grid.addWidget(  detachBtn,  1, 0, QtCore.Qt.AlignTop)
        # grid.addWidget(  attachBtn,  2, 0, QtCore.Qt.AlignTop)
        # grid.addWidget(    waitBtn,  3, 0, QtCore.Qt.AlignTop)
        # grid.addWidget(    gripBtn,  4, 0, QtCore.Qt.AlignTop)
        # grid.addWidget(    dropBtn,  5, 0, QtCore.Qt.AlignTop)
        # grid.addWidget(  setVarBtn,  7, 0, QtCore.Qt.AlignTop)
        # grid.addWidget( testVarBtn,  8, 0, QtCore.Qt.AlignTop)
        # grid.addWidget(startBlkBtn,  9, 0, QtCore.Qt.AlignTop)
        # grid.addWidget(  endBlkBtn, 10, 0, QtCore.Qt.AlignTop)
        # grid.addWidget( refreshBtn,  3, 0, QtCore.Qt.AlignTop)
        # grid.addWidget(   colorBtn,  6, 0, QtCore.Qt.AlignTop)
        self.setTabPosition(QtWidgets.QTabWidget.East)
        self.setFixedWidth(85)
        # self.setLayout(mainVLayout)

    def getButton(self, commandType):
        newButton = self.DraggableButton(str(commandType.__name__), self)
        newButton.setIcon(QtGui.QIcon(commandType.icon))
        newButton.setIconSize(QtCore.QSize(32, 32))
        newButton.setToolTip(commandType.tooltip)
        # newButton.doubleClicked.connect(lambda: self.addCmndFunc(commandType))
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

    def __init__(self):
        self.description = ""
        self.parameters = {}  # For commands with no parameters, this should stay empty

    def openWindow(self):  # Open window

        # If this object has no window object, then skip this process and return true (ei, StartBlockCommand)
        if len(self.parameters) == 0:
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

        prompt.mainVLayout = QtWidgets.QVBoxLayout()

        grid = QtWidgets.QGridLayout()
        grid.setSpacing(10)
        grid.addLayout(prompt.mainVLayout, 0, 1, QtCore.Qt.AlignCenter)
        grid.addWidget(applyBtn, 1, 2, QtCore.Qt.AlignRight)
        grid.addWidget(cancelBtn, 1, 0, QtCore.Qt.AlignLeft)

        prompt.setMaximumWidth(450)
        prompt.setLayout(grid)
        prompt.setWindowTitle(self.title)
        prompt.setWindowIcon(QtGui.QIcon(self.icon))
        prompt.setWhatsThis(self.tooltip)  # This makes the "Question Mark" button on the window show the tooltip msg

        # Dress the base window
        prompt = self.dressWindow(prompt)

        # Run the info window and prevent other windows from being clicked while open:
        printf("Command.openView(): Finished executing self...")
        prompt.exec_()

        # Get information that the user input
        if prompt.accepted:
            # Get information that the user input
            self.extractPromptInfo(prompt)
            self.updateDescription()
            printf('CommandWindow.openView(): New parameters: ', self.parameters)

        else:
            printf('CommandWindow.openView(): User Canceled.')

        return prompt.accepted

    def dressWidget(self, newWidget):
        self.updateDescription()

        newWidget.setIcon(self.icon)
        newWidget.setTitle(self.title)
        newWidget.setTip(self.tooltip)
        newWidget.setDescription(self.description)
        return newWidget

    def sanitizeFloat(self, inputTextbox, fallback):
        """
        Sent it a textbox, and it will check the text in the textbox to make sure it is valid.
        If it is, return the float within the textbox. If not, it will set the textbox to the fallback value
        while also setting the textbox back to the fallback value.
        """
        # Sanitize input from the user
        try:
            intInput = float(str(inputTextbox.text()))
        except:
            intInput = fallback
            inputTextbox.setText(str(fallback))
        return intInput

    def sanitizeEval(self, inputTextbox, fallback):
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

    def sanitizeVariable(self, inputTextbox, fallback):
        # Sanitize input from the user
        possibleNumber = str(inputTextbox.text())
        possibleNumber.replace(".", "")  # For isnumeric() to work, there can't be a decimal point

        if possibleNumber.isnumeric():
            return fallback

        return possibleNumber

    # The following commands should be empty, and only are there so that subclasses without them don't cause errors

    def extractPromptInfo(self, prompt):
        # In case there is a command that does not have info, if it is called then this ensures
        # there will be no error. For example, "start block of code" "refresh" or
        # "activate/deactivate gripper" do not have info to give
        pass

    def run(self, shared):
        # For any command that does not have a function such as "start block of code"
        # Then this function will run in it's place.
        pass

    def updateDescription(self):
        # This is called in openView() and will update the decription to match the parameters
        pass



########## COMMANDS ##########
"""
Commands must:
    - Be added to the CommandMenuWidget.initUI() function
    - Be added here
    - Have a logic implimentation
    - If the command has a description, it must have a updateDescription() method
    - If the command has a window, it must have the following methods:
            - dressWindow(prompt)
            - extractPromptInfo(prompt)

Commands must have:
    - Variables
        - tooltip
        - icon
        - logicPair (a string of the class name that is its logic counterpart, for interpreter use only)
        - title   (Except for certain functions, such as StartBlockCommand)
    - Functions
        - init(shared, parameters=None) function
            - Must calls super(NAME, self).__init__(parent)

Special Cases:
    -StartBlockCommand and EndBlockCommand are used directly in ControlPanelGUI.py to indent code blocks correctly

Example of a fully filled out class:

class NameCommandGUI(CommandGUI):
    title     = "Example Title"
    tooltip   = "This tool does X Y and Z"
    icon      = Icons.some_icon
    logicPair = "NameCommand"

    def __init__(self, env, parameters=None):
        super(NameCommandGUI, self).__init__()
        self.parameters = parameters

        if self.parameters is None:
            # Some code to set up default parameters
            pass

    def dressWindow(self, prompt):
        # Do some GUI code setup
        # Put all the objects into horizontal layouts called Rows
        row1 = QtWidgets.QHBoxLayout()
        prompt.mainVLayout.addLayout(row1) # and so on for all of the rows

        return prompt

    def extractPromptInfo(self, prompt):
        newParameters = {} # Get the parameters from the 'prompt' GUI elements. Put numbers through self.sanitizeFloat

        self.parameters.update(newParameters)

        return self.parameters

    def updateDescription(self):
        self.description = ""  # Some string that uses your parameters to describe the object.

"""

class MoveXYZCommandGUI(CommandGUI):
    title     = "Move XYZ"
    tooltip   = "Set the robots position. The robot will move after all events are evaluated"
    icon      = Icons.xyz_command
    logicPair = 'MoveXYZCommand'

    def __init__(self, env, parameters=None):
        super(MoveXYZCommandGUI, self).__init__()

        # Set default parameters that will show up on the window
        self.parameters = parameters

        if self.parameters is None:
            # If no parameters were given, it's a new command. Thus, get the robots current position and fill it in.
            # This helps with workflow so you can create MoveXYZ commands and move the robot around as you work with it
            currentXYZ = env.getRobot().getCurrentCoord()

            self.parameters = {'x': round(currentXYZ['x'], 1),
                               'y': round(currentXYZ['y'], 1),
                               'z': round(currentXYZ['z'], 1),
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
        rotLabel = QtWidgets.QLabel('X:')
        strLabel = QtWidgets.QLabel('Y:')
        hgtLabel = QtWidgets.QLabel('Z:')
        ovrCheck = QtWidgets.QLabel('Override Ongoing Movement:')
        rltCheck = QtWidgets.QLabel('Relative: ')

        # Fill the textboxes with the default parameters
        prompt.rotEdit.setText(str(self.parameters['x']))
        prompt.strEdit.setText(str(self.parameters['y']))
        prompt.hgtEdit.setText(str(self.parameters['z']))
        prompt.ovrCheck.setChecked(self.parameters['override'])
        prompt.rltCheck.setChecked(self.parameters['relative'])

        row1 = QtWidgets.QHBoxLayout()
        row2 = QtWidgets.QHBoxLayout()
        row3 = QtWidgets.QHBoxLayout()
        row4 = QtWidgets.QHBoxLayout()
        row5 = QtWidgets.QHBoxLayout()

        row1.addWidget(rotLabel)
        row1.addStretch(1)
        row1.addWidget(prompt.rotEdit)

        row2.addWidget(strLabel)
        row2.addStretch(1)
        row2.addWidget(prompt.strEdit)

        row3.addWidget(hgtLabel)
        row3.addStretch(1)
        row3.addWidget(prompt.hgtEdit)

        row4.addWidget(ovrCheck)
        row4.addStretch(1)
        row4.addWidget(prompt.ovrCheck)

        row5.addWidget(rltCheck)
        row5.addStretch(1)
        row5.addWidget(prompt.rltCheck)

        prompt.mainVLayout.addLayout(row1)
        prompt.mainVLayout.addLayout(row2)
        prompt.mainVLayout.addLayout(row3)
        prompt.mainVLayout.addLayout(row4)
        prompt.mainVLayout.addLayout(row5)
        return prompt

    def extractPromptInfo(self, prompt):
        # Update the parameters and the description
        newParameters = {'x': self.sanitizeEval(prompt.rotEdit, self.parameters["x"]),
                         'y': self.sanitizeEval(prompt.strEdit, self.parameters["y"]),
                         'z': self.sanitizeEval(prompt.hgtEdit, self.parameters["z"]),
                         'override': prompt.ovrCheck.isChecked(),
                         'relative': prompt.rltCheck.isChecked()}

        self.parameters.update(newParameters)

        return self.parameters

    def updateDescription(self):
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
        super(MoveWristCommandGUI, self).__init__()
        self.parameters = parameters

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

        row1 = QtWidgets.QHBoxLayout()
        row2 = QtWidgets.QHBoxLayout()

        row1.addWidget(wristLabel)
        row1.addStretch(1)
        row1.addWidget(prompt.wristEdit)

        row2.addWidget(rltLabel)
        row2.addStretch(1)
        row2.addWidget(prompt.rltCheck)

        prompt.mainVLayout.addLayout(row1)
        prompt.mainVLayout.addLayout(row2)
        return prompt

    def extractPromptInfo(self, prompt):
        newParameters = {"angle":    self.sanitizeEval(prompt.wristEdit, self.parameters["angle"]),
                         "relative": prompt.rltCheck.isChecked()}

        self.parameters.update(newParameters)

        return self.parameters

    def updateDescription(self):
        self.description = "Set the wrist position to " + self.parameters["angle"] + " degrees"

        if self.parameters['relative']: self.description += '   Relative'


class StartBlockCommandGUI(CommandGUI):
    """
    Start a block of code with this class
    """

    icon      = Icons.startblock_command
    tooltip   = "This is the start of a block of commands that only run if a conditional statement is met."
    logicPair = 'StartBlockCommand'

    def __init__(self, shared, parameters=None):
        super(StartBlockCommandGUI, self).__init__()


class EndBlockCommandGUI(CommandGUI):
    """
    End a block of code with this command
    """

    icon      = Icons.endblock_command
    tooltip   = "This is the end of a block of commands."
    logicPair = 'EndBlockCommand'

    def __init__(self, shared, parameters=None):
        super(EndBlockCommandGUI, self).__init__()


class SetVariableCommandGUI(CommandGUI):
    title     = "Set Variable"
    tooltip   = "This command can create a variable or set an existing variable to a value or an expression."
    icon      = Icons.set_var_command
    logicPair = "SetVariableCommand"

    def __init__(self, env, parameters=None):
        super(SetVariableCommandGUI, self).__init__()
        self.parameters = parameters

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

        row1 = QtWidgets.QHBoxLayout()
        row2 = QtWidgets.QHBoxLayout()

        row1.addWidget(namLabel)
        row1.addStretch(1)
        row1.addWidget(prompt.namEdit)

        row2.addWidget(valLabel)
        row2.addStretch(1)
        row2.addWidget(prompt.valEdit)

        prompt.mainVLayout.addLayout(row1)
        prompt.mainVLayout.addLayout(row2)

        return prompt

    def extractPromptInfo(self, prompt):
        # Get the parameters from the 'prompt' GUI elements. Put numbers through self.sanitizeFloat

        newParameters = {"variable": self.sanitizeVariable(prompt.namEdit, self.parameters["variable"]),
                         "expression": prompt.valEdit.text()}

        self.parameters.update(newParameters)

        return self.parameters

    def updateDescription(self):
        # Some string that uses your parameters to describe the object.
        self.description = "Set " + self.parameters["variable"] + " to " + self.parameters["expression"]


class TestVariableCommandGUI(CommandGUI):
    title     = "Test Variable"
    tooltip   = "This will allow/disallow code to run that is in blocked brackets below it."
    icon      = Icons.test_var_command
    logicPair = 'TestVariableCommand'

    def __init__(self, env, parameters=None):
        super(TestVariableCommandGUI, self).__init__()

        self.parameters = parameters

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

        row1 = QtWidgets.QHBoxLayout()
        row2 = QtWidgets.QHBoxLayout()
        row3 = QtWidgets.QHBoxLayout()
        # row4 = QtWidgets.QHBoxLayout()

        row1.addWidget(varLabel)
        row1.addStretch(1)
        row1.addWidget(prompt.varEdit)

        row2.addWidget(tstLabel)
        row2.addStretch(1)
        row2.addWidget(prompt.tstMenu)

        row3.addWidget(valLabel)
        row3.addStretch(1)
        row3.addWidget(prompt.valEdit)

        # row4.addStretch(1)
        # row4.addWidget(notLabel)
        # row4.addWidget(prompt.notCheck)

        prompt.mainVLayout.addLayout(row1)
        prompt.mainVLayout.addLayout(row2)
        prompt.mainVLayout.addLayout(row3)
        # prompt.mainVLayout.addLayout(row4)

        return prompt

    def extractPromptInfo(self, prompt):
        newParameters = {'variable': self.sanitizeVariable(prompt.varEdit, self.parameters['variable']),
                         'test': prompt.tstMenu.currentIndex(),
                         'expression': str(prompt.valEdit.text())}  # This can't be sanitized, unfortunately :/

        self.parameters.update(newParameters)
        return self.parameters

    def updateDescription(self):
        operations = [' equal to', ' not equal to', ' greater than', ' less than']
        self.description = 'If ' + str(self.parameters['variable']) + ' is' + operations[self.parameters['test']] + \
                           ' ' + self.parameters['expression'] + ' then'


class DetachCommandGUI(CommandGUI):
    title     = "Detach Servos"
    tooltip   = "Disengage the specified servos on the robot"
    icon      = Icons.detach_command
    logicPair = "DetachCommand"

    def __init__(self, env, parameters=None):
        super(DetachCommandGUI, self).__init__()
        self.parameters = parameters

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

        row1 = QtWidgets.QHBoxLayout()
        row2 = QtWidgets.QHBoxLayout()
        row3 = QtWidgets.QHBoxLayout()
        row4 = QtWidgets.QHBoxLayout()

        row1.addWidget(label1)
        row1.addStretch(1)
        row1.addWidget(prompt.srvo1Box)

        row2.addWidget(label2)
        row2.addStretch(1)
        row2.addWidget(prompt.srvo2Box)

        row3.addWidget(label3)
        row3.addStretch(1)
        row3.addWidget(prompt.srvo3Box)

        row4.addWidget(label4)
        row4.addStretch(1)
        row4.addWidget(prompt.srvo4Box)

        prompt.mainVLayout.addLayout(row1)
        prompt.mainVLayout.addLayout(row2)
        prompt.mainVLayout.addLayout(row3)
        prompt.mainVLayout.addLayout(row4)


        return prompt

    def extractPromptInfo(self, prompt):
        newParameters = {'servo1': prompt.srvo1Box.isChecked(),
                         'servo2': prompt.srvo2Box.isChecked(),
                         'servo3': prompt.srvo3Box.isChecked(),
                         'servo4': prompt.srvo4Box.isChecked()}

        self.parameters.update(newParameters)

        return self.parameters

    def updateDescription(self):
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
        super(AttachCommandGUI, self).__init__()
        self.parameters = parameters

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

        row1 = QtWidgets.QHBoxLayout()
        row2 = QtWidgets.QHBoxLayout()
        row3 = QtWidgets.QHBoxLayout()
        row4 = QtWidgets.QHBoxLayout()

        row1.addWidget(label1)
        row1.addStretch(1)
        row1.addWidget(prompt.srvo1Box)

        row2.addWidget(label2)
        row2.addStretch(1)
        row2.addWidget(prompt.srvo2Box)

        row3.addWidget(label3)
        row3.addStretch(1)
        row3.addWidget(prompt.srvo3Box)

        row4.addWidget(label4)
        row4.addStretch(1)
        row4.addWidget(prompt.srvo4Box)

        prompt.mainVLayout.addLayout(row1)
        prompt.mainVLayout.addLayout(row2)
        prompt.mainVLayout.addLayout(row3)
        prompt.mainVLayout.addLayout(row4)
        prompt.mainVLayout.addLayout(row1) # and so on for all of the rows

        return prompt

    def extractPromptInfo(self, prompt):
        newParameters = {'servo1': prompt.srvo1Box.isChecked(),
                         'servo2': prompt.srvo2Box.isChecked(),
                         'servo3': prompt.srvo3Box.isChecked(),
                         'servo4': prompt.srvo4Box.isChecked()}

        self.parameters.update(newParameters)

        return self.parameters

    def updateDescription(self):
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
        super(WaitCommandGUI, self).__init__()
        self.parameters = parameters

        if self.parameters is None:
            self.parameters = {'time': 1.0}
            pass

    def dressWindow(self, prompt):
        prompt.timeEdit = QtWidgets.QLineEdit()

        # Set up all the labels for the inputs
        timeLabel = QtWidgets.QLabel('Number of seconds: ')


        # Fill the textboxes with the default parameters
        prompt.timeEdit.setText(str(self.parameters['time']))

        row1 = QtWidgets.QHBoxLayout()

        row1.addWidget(timeLabel)
        row1.addStretch(1)
        row1.addWidget(prompt.timeEdit)

        prompt.mainVLayout.addLayout(row1)

        return prompt

    def extractPromptInfo(self, prompt):
        newParameters = {'time': self.sanitizeEval(prompt.timeEdit, self.parameters['time'])}

        self.parameters.update(newParameters)

        return self.parameters

    def updateDescription(self):
        self.description = str(self.parameters['time']) + " seconds"


class GripCommandGUI(CommandGUI):
    title     = "Activate Gripper"
    tooltip   = "Activates the robots gripper"
    icon      = Icons.grip_command
    logicPair = "GripCommand"

    def __init__(self, env, parameters=None):
        super(GripCommandGUI, self).__init__()


class DropCommandGUI(CommandGUI):
    title     = "Deactivate Gripper"
    tooltip   = "Deactivates the robots gripper"
    icon      = Icons.drop_command
    logicPair = "DropCommand"

    def __init__(self, env, parameters=None):
        super(DropCommandGUI, self).__init__()






########### NON-UPDATED COMMANDS ########
'''
class RefreshCommand(CommandGUI):
    """
    A command for refreshing the robots position by sending the robot information.
    It activates the robot.refresh() command, which detects if any movement variables have been changed
    and if they have sends that info over to the robot.
    """
    title      = "Refresh Robot"
    tooltip    = "Send any changed position information to the robot. This will stop event processing for a moment."
    icon       = Icons.refresh_command

    def __init__(self, parent, env, **kwargs):
        super(RefreshCommand, self).__init__(parent)

    def run(self, env):
        env.getRobot().refresh()


class ColorTrackCommand(CommandGUI):
    title      = "Move to Color"
    tooltip    = "Tracks objects by looking for a certain color."
    icon       = Icons.colortrack_command

    def __init__(self, parent, env, **kwargs):

        super(ColorTrackCommand, self).__init__(parent)
        self.parameters = kwargs.get("parameters",
                            {'cHue': 0,
                             'tHue': 0,
                             'lSat': 0,
                             'hSat': 0,
                             'lVal': 0,
                             'hVal': 0})




        self.cHueEdit = QtWidgets.QLineEdit()
        self.tHueEdit = QtWidgets.QLineEdit()
        self.lSatEdit = QtWidgets.QLineEdit()
        self.hSatEdit = QtWidgets.QLineEdit()
        self.lValEdit = QtWidgets.QLineEdit()
        self.hValEdit = QtWidgets.QLineEdit()

        self.initUI(env)
        self.setWindowIcon(QtGui.QIcon(self.icon))

    def initUI(self, env):
        #Set up all the labels for the inputs
        hueLabel = QtWidgets.QLabel('Hue/Tolerance: ')
        satLabel = QtWidgets.QLabel('Saturation range: ')
        valLabel = QtWidgets.QLabel('Value range:')



        #Fill the textboxes with the default parameters
        self.cHueEdit.setText(str(self.parameters['cHue']))
        self.tHueEdit.setText(str(self.parameters['tHue']))
        self.lSatEdit.setText(str(self.parameters['lSat']))
        self.hSatEdit.setText(str(self.parameters['hSat']))
        self.lValEdit.setText(str(self.parameters['lVal']))
        self.hValEdit.setText(str(self.parameters['hVal']))

        self.cHueEdit.setFixedWidth(75)
        self.tHueEdit.setFixedWidth(75)
        self.lSatEdit.setFixedWidth(75)
        self.hSatEdit.setFixedWidth(75)
        self.lValEdit.setFixedWidth(75)
        self.hValEdit.setFixedWidth(75)

        #Set up 'scanbutton' that will scan the camera and fill out the parameters for recommended settings
        scanLabel  = QtWidgets.QLabel("Press button to automatically fill out values:")
        scanButton = QtWidgets.QPushButton("Scan Colors")
        scanButton.clicked.connect(lambda: self.scanColors(env))



        row1 = QtWidgets.QHBoxLayout()
        row2 = QtWidgets.QHBoxLayout()
        row3 = QtWidgets.QHBoxLayout()
        row4 = QtWidgets.QHBoxLayout()

        row1.addWidget(    scanLabel, QtCore.Qt.AlignLeft)
        row1.addWidget(   scanButton, QtCore.Qt.AlignRight)

        row2.addWidget(     hueLabel, QtCore.Qt.AlignLeft)
        row2.addWidget(self.cHueEdit, QtCore.Qt.AlignRight)
        row2.addWidget(QtWidgets.QLabel("+-"))
        row2.addWidget(self.tHueEdit, QtCore.Qt.AlignRight)

        row3.addWidget(     satLabel, QtCore.Qt.AlignLeft)
        row3.addWidget(self.lSatEdit, QtCore.Qt.AlignRight)
        row3.addWidget(QtWidgets.QLabel("to"))
        row3.addWidget(self.hSatEdit, QtCore.Qt.AlignRight)

        row4.addWidget(     valLabel, QtCore.Qt.AlignLeft)
        row4.addWidget(self.lValEdit, QtCore.Qt.AlignRight)
        row4.addWidget(QtWidgets.QLabel("to"))
        row4.addWidget(self.hValEdit, QtCore.Qt.AlignRight)



        self.mainVLayout.addLayout(row1)
        self.mainVLayout.addLayout(row2)
        self.mainVLayout.addLayout(row3)
        self.mainVLayout.addLayout(row4)


    def scanColors(self, env):
        printf("ColorTrackCommand.scanColors(): Scanning colors!")

        if env is None:
            printf("ColorTrackCommand.scanColors(): ERROR: Tried to scan colors while env was None! colors!")

            return

        avgColor = env.getVision().bgr2hsv(env.getVision().getColor())
        percentTolerance = .3

        printf("avgColor", avgColor)
        self.cHueEdit.setText(str(round(avgColor[0])))
        self.tHueEdit.setText(str(30))  #Recommended tolerance
        self.lSatEdit.setText(str(round(avgColor[1] - avgColor[1] * percentTolerance, 5)))
        self.hSatEdit.setText(str(round(avgColor[1] + avgColor[1] * percentTolerance, 5)))
        self.lValEdit.setText(str(round(avgColor[2] - avgColor[2] * percentTolerance, 5)))
        self.hValEdit.setText(str(round(avgColor[2] + avgColor[2] * percentTolerance, 5)))

    def getInfo(self):
        #Build the info inputted into the window into a Json and return it. Used in parent class

        newParameters = {'cHue': self.sanitizeFloat(self.cHueEdit, self.parameters['cHue']),
                         'tHue': self.sanitizeFloat(self.tHueEdit, self.parameters['tHue']),
                         'lSat': self.sanitizeFloat(self.lSatEdit, self.parameters['lSat']),
                         'hSat': self.sanitizeFloat(self.hSatEdit, self.parameters['hSat']),
                         'lVal': self.sanitizeFloat(self.lValEdit, self.parameters['lVal']),
                         'hVal': self.sanitizeFloat(self.hValEdit, self.parameters['hVal'])}
        return newParameters

    def updateDescription(self):
        self.description = 'Track objects with a hue of ' + str(self.parameters['cHue'])

    def run(self, env):
        printf("ColorTrackCommand.run(): Tracking colored objects! ")

        if not env.getVision().cameraConnected():
            printf("ColorTrackCommand.run(): ERROR: No camera detected")
            return

        #Build a function that will return the objects position whenever it is called, using the self.parameters
        objPos = lambda: env.getVision().findObjectColor(self.parameters['cHue'],
                                                            self.parameters['tHue'],
                                                            self.parameters['lSat'],
                                                            self.parameters['hSat'],
                                                            self.parameters['lVal'],
                                                            self.parameters['hVal'])
        objCoords = objPos()


        #If no object was found
        if objCoords is None: return

        move = Robot.getDirectionToTarget(objCoords, env.getVision().vStream.dimensions, 10)

        #If the robot is already focused
        if move is None: return

        #Convert the move to one on the base grid
        baseAngle = env.getRobot().getBaseAngle()
        modDirection = Robot.getRelative(move[0], move[1], baseAngle)

        # if modDirection is None: return


        env.getRobot().setPos(x=modDirection[0] / 3, y=modDirection[1] / 3, relative=True)
'''