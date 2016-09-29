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
import Paths
from threading    import RLock
from PyQt5        import QtGui, QtCore, QtWidgets
__author__ = "Alexander Thiel"




class LineTextWidget(QtWidgets.QFrame):
    """
    This puts line numbers on a QTextEdit widget
    """
    class NumberBar(QtWidgets.QWidget):

        def __init__(self, *args):
            QtWidgets.QWidget.__init__(self, *args)
            self.edit = None
            # This is used to update the width of the control.
            # It is the highest line that is currently visibile.
            self.highest_line = 0

        def setTextEdit(self, edit):
            self.edit = edit

        def update(self, *args):
            """
            Updates the number bar to display the current set of numbers.
            Also, adjusts the width of the number bar if necessary.
            """

            # The + 4 is used to compensate for the current line being bold.
            width = self.fontMetrics().width(str(self.highest_line)) + 4
            if self.width() != width:
                self.setFixedWidth(width)
            QtWidgets.QWidget.update(self, *args)

        def paintEvent(self, event):

            contents_y = self.edit.verticalScrollBar().value()
            page_bottom = contents_y + self.edit.viewport().height()
            font_metrics = self.fontMetrics()
            current_block = self.edit.document().findBlock(self.edit.textCursor().position())

            painter = QtGui.QPainter(self)

            line_count = 0
            # Iterate over all text blocks in the document.
            block = self.edit.document().begin()
            while block.isValid():
                line_count += 1

                # The top left position of the block in the document
                position = self.edit.document().documentLayout().blockBoundingRect(block).topLeft()

                # Check if the position of the block is out side of the visible
                # area.
                if position.y() > page_bottom:
                    break

                # We want the line number for the selected line to be bold.
                bold = False
                if block == current_block:
                    bold = True
                    font = painter.font()
                    font.setBold(True)
                    painter.setFont(font)

                # Draw the line number right justified at the y position of the
                # line. 3 is a magic padding number. drawText(x, y, text).
                painter.drawText(self.width() - font_metrics.width(str(line_count)) - 3,
                                 round(position.y()) - contents_y + font_metrics.ascent(),
                                 str(line_count))

                # Remove the bold style if it was set previously.
                if bold:
                    font = painter.font()
                    font.setBold(False)
                    painter.setFont(font)

                block = block.next()

            self.highest_line = line_count
            painter.end()

            QtWidgets.QWidget.paintEvent(self, event)

    def __init__(self, *args):
        QtWidgets.QFrame.__init__(self, *args)

        self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Sunken)

        self.edit = QtWidgets.QTextEdit()
        self.edit.setFrameStyle(QtWidgets.QFrame.NoFrame)
        self.edit.setAcceptRichText(False)
        self.edit.setTabStopWidth(28)

        self.number_bar = self.NumberBar()
        self.number_bar.setTextEdit(self.edit)

        hbox = QtWidgets.QHBoxLayout(self)
        hbox.setSpacing(0)
        # hbox.setMargin(0)
        hbox.addWidget(self.number_bar)
        hbox.addWidget(self.edit)

        self.edit.installEventFilter(self)
        self.edit.viewport().installEventFilter(self)

    # noinspection PyArgumentList
    def eventFilter(self, obj, event):
        # Update the line numbers for all events on the text edit and the viewport.
        # This is easier than connecting all necessary singals.
        if obj in (self.edit, self.edit.viewport()):
            self.number_bar.update()
            return False
        return QtWidgets.QFrame.eventFilter(obj, event)

    def setText(self, plainText):
        self.edit.setPlainText(plainText)

    def getTextEdit(self):
        return self.edit

    def getText(self):
        return self.edit.toPlainText()



class ScriptWidget(QtWidgets.QWidget):
    """This class is for making a text editor that will help you write python code"""

    documentation = "" \
"""
    Using this scripting module, the possibilities are endless. You can directly inject python code into your program
without a hassle. You can use any of the libraries and modules that are built into this software, real time, and
without any extra modification.

    There are certain classes that are loaded into the script as python builtins, so you don't need to pass them to
functions or worry about scope, or even worry about setting them global. They are:


Builtin Variables:
    robot
        You have full access to controlling the robot, using the Robot.py library that was built as a wrapper for
        a communication protocol.

        For source code on the Robot class, go to:
        https://github.com/apockill/uArmCreatorStudio/blob/master/Logic/Robot.py


    vision
        Using this module, you can easly and without hassle track objects that you have taught the software in the
        Resource manager, find their location real time, search for past "tracks" of the objects, and act based upon
        that information. You can clear tracked objects, add new ones, and generally use powerful premade computer
        vision functions that have been built into this software already.

        For source code on the Vision class, go to:
        https://github.com/apockill/uArmCreatorStudio/blob/master/Logic/Vision.py

    resources
        You can pull any "objects" that you have built using the Resource Manager. This means, for example,
        that you could request a Movement Recording and replay it, or request a Vision object and track it.

        For source code on the Object Manager class, go to:
        https://github.com/apockill/uArmCreatorStudio/blob/master/Logic/ObjectManager.py

    settings
        This is a python dictionary of the GUI settings. This includes things like calibrations for various things.
        Try doing print(settings) to see what it contains.


    scriptStopping()
        This is a function that returns True if the user has pressed the "stop" button on the top left. You can use
        this to check if your script should end, if you're doing long loops.

        For source code on the Interpreter environment that runs your script, go to:
        https://github.com/apockill/uArmCreatorStudio/blob/master/Logic/Interpreter.py

    sleep
        The usual python sleep variable has been replaced by one that will automatically stop sleeping when the user
        presses the "stop script" button on the GUI. So don't worry about writing blocking code, that's been handled!

Examples scripts using 'robot'
    robot.setPos(x=0, y=15, z=15)  # This will set the robots position to XYZ(0, 15, 15)
    robot.setPos(x=0, wait=False)  # Allows your code to continue while the robot moves.
    robot.setPos(x=0)              # Will only set the x position, keeps the rest the same
    robot.setGripper(True)         # Turn on the pump. If false, it will deactivate the pump
    robot.setBuzzer(1500, 2)       # Play a tone through the robots buzzer. Parameters: Frequency, duration (seconds)
    robot.setSpeed(10)             # Sets speed for all future moves using robot.setPos. Speed set in cm/s
    robot.connected()              # Returns True if the robot is connected and working, False if not

    robot.getAngles()              # Returns the current angles of the robots servos: [servo0, servo1, servo2, servo3]
    robot.getCoords()              # Returns the current coordinate of the robot in [x, y, z] format
    robot.getTipSensor()           # Returns True or False, if the tip sensor on the robot is being pressed or not
    robot.getMoving()              # Returns True if the robot is currently moving



Example scripts using 'vision'
    # The first step of using vision is getting a trackable object. Make an object in Resources then access it by name.
    trackableObject = resources.getObject("Ace of Spades")


    # The next step is to make sure vision is tracking the object. Usually this should be done in Initialization event.
    # Objects only stop being tracked when the script ends. Do this only once.
    vision.addPlaneTarget(trackableObject)


    # Wait two seconds to make sure that vision has time to search for the new object
    sleep(2)


    # Alternatively you can use the following, which will wait for 30 frames to pass before continuing
    vision.waitForNewFrames(30)


    # If the object is already being tracked and has been for a while, you can try using vision to search for it
    # This function returns how many frames ago the object was recognized, and a "tracked" object with some information
    frameID, trackedObject = vision.getObjectLatestRecognition(trackableObject)


    # If no object is found, the "trackedObject" will be None. Check if its None before continuing
    if trackedObject is None:
        # Handle the error here
        print("Object ", trackableObject.name, " was not recognized!")
        return

    # If the object was, in fact, found, then you can pull all sorts of information from it
    print(trackedObject.center)     # Prints a list [x, y, z] of the objects position in the cameras coordinate system
    print(trackedObject.rotation)   # Prints a list [xRotation, yRotation, zRotation] of rotation along each axis
    print(trackedObject.ptCount)    # Prints how many points the object was recognized with. More points = more accuracy


    # Here is another function for looking for tracked objects
    # This will search through the last 30 frames for trackableObject, and try to find a recognition with > 50 keypoints
    trackedObject = vision.searchTrackedHistory(trackable=trackableObject, maxAge=30, minPoints=50)



Any variable created in the scope of the script command can be used in any other script command, or block command
    def someFunctionName(someArgument):
        # Any python function here
        print("This function can work in any script command in the task!")
        print(someArgument)

    someVariableName = "This string can be used in any Script command in the program"



You might notice that scripts with big loops or 'while True' statements will take a long time to end when the "stop"
button is pressed on the GUI. Sometimes, they might freeze the program. The reason for this is because your code
is running inside of a seperate thread/process, and when you end the task the thread has to end as well.

Any drag-and-drop command will end quickly, because they have been designed to do so. However, you will have to do this
yourself if you have a long lasting script that you want to be able to quit at any time. In order to do so, you can use
the function "scriptStopping()"

scriptStopping() returns True if the user has attempted to end the task, and False if the task has not been ended

    The typical use case is:

    while [Some Condition]:
        if scriptStopping(): break  # Break out of the loop if the program has ended. Place this wherever needed
        # ... code ...
        # ... code ...
        # ... code ...

    or, if it's in a big loop

    for i in range(0, 100000):
        if scriptStopping(): break
        # ... code ...
        # ... code ...
        # ... code ...

"""


    def __init__(self, previousCode, parent):
        super(ScriptWidget, self).__init__(parent)
        self.prompt = parent
        self.prompt.content.setContentsMargins(5, 5, 5, 5)

        self.docText   = QtWidgets.QTextEdit()
        self.docBtn    = QtWidgets.QPushButton("Show Documentation")
        self.textEdit  = LineTextWidget()
        self.textEdit.setText(previousCode)

        self.hintLbl           = QtWidgets.QLabel("")  # Will give you warnings and whatnot
        self.initUI()


    def initUI(self):
        self.docText.setReadOnly(True)
        self.docText.setAcceptRichText(True)
        self.docText.setText(self.documentation)
        self.docText.setMinimumWidth(900)
        self.docText.setMinimumHeight(600)
        self.docBtn.setFixedWidth(150)
        self.docText.setHidden(True)

        bold = QtGui.QFont()
        bold.setBold(True)
        self.hintLbl.setFont(bold)



        self.docBtn.clicked.connect(self.showDocumentation)


        monospace = QtGui.QFont("Monospace")
        monospace.setStyleHint(QtGui.QFont.TypeWriter)
        self.textEdit.setFont(monospace)
        self.textEdit.setMinimumHeight(550)
        self.textEdit.setMinimumWidth(500)
        self.textEdit.getTextEdit().textChanged.connect(self.verifyCode)
        self.docText.setFont(monospace)

        row1 = QtWidgets.QHBoxLayout()
        row2 = QtWidgets.QHBoxLayout()
        row3 = QtWidgets.QHBoxLayout()


        row1.addWidget(self.docBtn)
        row1.addStretch(1)

        row2.addWidget(self.textEdit)
        row2.addWidget(self.docText)
        row3.addWidget(self.hintLbl)


        mainVLayout = QtWidgets.QVBoxLayout()
        mainVLayout.addLayout(row1)
        mainVLayout.addLayout(row2)
        mainVLayout.addLayout(row3)


        self.setLayout(mainVLayout)


    def showDocumentation(self):
        hiding = not self.docText.isHidden()

        if hiding:
            self.docBtn.setText("Show Documentation")
            self.docText.hide()
            self.textEdit.show()
            self.prompt.resize(self.prompt.sizeHint())
        else:
            self.docBtn.setText("Show Code")
            self.textEdit.hide()
            self.docText.show()

            self.prompt.resize(self.prompt.sizeHint())

    def getCode(self):
        return self.textEdit.getText()

    def verifyCode(self):
        # Checks if the users code is valid, and updates self.applyBtn
        code  = self.textEdit.getText()

        error = ""

        try:
            ast.parse(code)
        except SyntaxError as e:
            error = str(e)

        self.prompt.applyBtn.setDisabled(len(error))
        self.hintLbl.setText(error)



class Console(QtWidgets.QWidget):
    """
        This is used to display console output, and allow the user to choose which classes print output, and allow
        users to "exec" code
    """
    # Have clear button, settings (for which classes to display responses from), exec stuff,
    settingsChanged = QtCore.pyqtSignal()

    def __init__(self, consoleSettings, parent, fps=4.0):
        super(Console, self).__init__(parent)
        # Since prints might come from different threads, lock before adding stuff to self.text
        self.printLock    = RLock()
        self.execFunction = None
        self.printBuffer  = []  # A buffer of strings to print
        self.settings     = consoleSettings



        # Initialize UI Globals
        self.inputEdt     = QtWidgets.QLineEdit()
        self.text         = QtWidgets.QPlainTextEdit()

        # Set up the refresh timer
        self.refreshTimer = QtCore.QTimer()
        self.refreshTimer.timeout.connect(self.__refreshBuffer)
        self.refreshTimer.start(1000.0 / fps)  # How often the console refreshes

        self.initUI()

    def initUI(self):
        settingsBtn = QtWidgets.QPushButton()  # A button to add filters to the printing

        self.inputEdt.returnPressed.connect(self.input)
        settingsBtn.clicked.connect(self.__openSettings)
        settingsBtn.setIcon(QtGui.QIcon(Paths.settings))

        monospace = QtGui.QFont("Monospace")
        monospace.setStyleHint(QtGui.QFont.TypeWriter)
        self.text.setFont(monospace)
        self.text.setReadOnly(True)

        if not self.settings["wordWrap"]:
            self.text.setWordWrapMode(QtGui.QTextOption.NoWrap)


        codeLayout = QtWidgets.QHBoxLayout()
        codeLayout.addWidget(QtWidgets.QLabel("Run Code: "))
        codeLayout.addWidget(self.inputEdt)
        codeLayout.addWidget(settingsBtn)

        mainVLayout = QtWidgets.QVBoxLayout()
        mainVLayout.addWidget(self.text)
        mainVLayout.addLayout(codeLayout)
        self.setLayout(mainVLayout)


    def write(self, classString, printStr):
        # Add something to the printBuffer, for it to be printed later, in the refreshBuffer function
        with self.printLock:
            self.printBuffer.append((classString, printStr))

    def input(self):
        with self.printLock:

            if self.execFunction is None:
                self.inputEdt.setText("")
                return

            command =  self.inputEdt.text()

            self.write("Input", command)

            ret, success = self.execFunction(command)

            if ret is not None:
                self.write("Output", ret)


            self.inputEdt.setText("")

    def setExecFunction(self, execFunction):
        # Set the function that will evaluate code
        self.execFunction = execFunction


    def __allowString(self, moduleString):
        """
        Choose whether or not this string comes from a class that should be printed or not. This is set in the settings.
        """
        with self.printLock:

            if "Output" == moduleString:
                return "Output"

            if "Input" == moduleString:
                return "Input"

            # Print anything from a GUI module
            if "GUI" == moduleString:
                if self.settings["gui"]: return "GUI"
                return None

            # Print anything from the Robot module
            if "Robot" == moduleString:
                if self.settings["robot"]: return "Robot"
                return None

            # Print anything from the Vision module
            if "Vision" == moduleString or "Video" == moduleString:
                if self.settings["vision"]: return "Vision"
                return None

            # Print anything from the communication module
            if "Communication" == moduleString:
                if self.settings["serial"]: return "Communication"
                return None

            # Print anything from the Interpreter module
            if "Environment"   in moduleString or \
               "ObjectManager" in moduleString or \
               "Resources"     in moduleString or \
               "Interpreter"   in moduleString:

                if self.settings["interpreter"]: return "Interpreter"
                return None

            # Print anything from Commands
            if "Commands" == moduleString or "Events" == moduleString or "RobotVision" == moduleString:
                if self.settings["script"]: return "Script"
                return None

            # If the user wants everything to be printed, just in case, then send "Other" as the category
            if self.settings["other"]:
                return moduleString

            return None

    def __openSettings(self):
        window = QtWidgets.QDialog()

        def addRow(left, right):
            right.setFixedWidth(100)
            row = QtWidgets.QHBoxLayout()
            row.addStretch(1)
            row.addWidget(left)
            row.addWidget(right)
            window.content.addLayout(row)

        # Create the apply/cancel buttons, connect them, and format them
        window.okBtn = QtWidgets.QPushButton('Ok')
        window.okBtn.setMaximumWidth(100)
        window.okBtn.clicked.connect(window.accept)


        # Create a content box for the command to fill out parameters and GUI elements
        window.content    = QtWidgets.QVBoxLayout()
        window.content.setContentsMargins(20, 10, 20, 10)


        # Now that the window is 'dressed', add "Cancel" and "Apply" buttons
        buttonRow = QtWidgets.QHBoxLayout()
        buttonRow.addStretch(1)
        buttonRow.addWidget(window.okBtn)


        # Create the main vertical layout, add everything to it
        window.mainVLayout = QtWidgets.QVBoxLayout()
        window.mainVLayout.addLayout(window.content)
        window.mainVLayout.addStretch(1)


        # Set the main layout and general window parameters
        window.setLayout(window.mainVLayout)
        window.setWindowTitle("Console Settings")
        window.setWindowIcon(QtGui.QIcon(Paths.settings))
        window.setWhatsThis("Here you can change settings about what you see in the console")


        # Dress the base window (this is where the child actually puts the content into the widget)
        descLbl   = QtWidgets.QLabel("Customize what you see printed on the Console")

        wrapLbl   = QtWidgets.QLabel("Wrap Lines ")
        robotLbl  = QtWidgets.QLabel("Robot Logs ")
        visionLbl = QtWidgets.QLabel("Vision Logs ")
        comLbl    = QtWidgets.QLabel("Communication Logs ")
        interpLbl = QtWidgets.QLabel("Interpreter Logs ")
        scriptLbl = QtWidgets.QLabel("Script Logs ")
        guiLbl    = QtWidgets.QLabel("GUI Logs ")
        othLbl    = QtWidgets.QLabel("Other Logs ")

        window.wrapChk   = QtWidgets.QCheckBox()
        window.robotChk  = QtWidgets.QCheckBox()   # Show prints from robot class
        window.visionChk = QtWidgets.QCheckBox()   # Show prints from vision class
        window.comChk    = QtWidgets.QCheckBox()   # Show prints from communication protocol
        window.interpChk = QtWidgets.QCheckBox()   # Show prints from Interpreter (Important!)
        window.scriptChk = QtWidgets.QCheckBox()   # Show prints from Command and Event Elements
        window.guiChk    = QtWidgets.QCheckBox()   # Show prints from GUI Elements
        window.othChk    = QtWidgets.QCheckBox()   # Show prints from anything else

        window.wrapChk  .setChecked(self.settings["wordWrap"])
        window.robotChk .setChecked(self.settings["robot"])
        window.visionChk.setChecked(self.settings["vision"])
        window.comChk   .setChecked(self.settings["serial"])
        window.interpChk.setChecked(self.settings["interpreter"])
        window.scriptChk.setChecked(self.settings["script"])
        window.guiChk   .setChecked(self.settings["gui"])
        window.othChk   .setChecked(self.settings["other"])

        window.content.addWidget(descLbl)
        addRow(wrapLbl,   window.wrapChk)
        addRow(robotLbl,  window.robotChk)
        addRow(robotLbl,  window.robotChk)
        addRow(visionLbl, window.visionChk)
        addRow(comLbl,    window.comChk)
        addRow(interpLbl, window.interpChk)
        addRow(scriptLbl, window.scriptChk)
        addRow(guiLbl,    window.guiChk)
        addRow(othLbl,    window.othChk)

        window.mainVLayout.addLayout(buttonRow)  # Add button after, so hints appear above buttons

        # Run the info window and prevent other windows from being clicked while open:
        accepted = window.exec_()

        if accepted:
            self.settings["wordWrap"]    = window.wrapChk.isChecked()
            self.settings["robot"]       = window.robotChk.isChecked()
            self.settings["vision"]      = window.visionChk.isChecked()
            self.settings["serial"]      = window.comChk.isChecked()
            self.settings["interpreter"] = window.interpChk.isChecked()
            self.settings["script"]      = window.scriptChk.isChecked()
            self.settings["gui"]         = window.guiChk.isChecked()
            self.settings["other"]       = window.othChk.isChecked()

            # Update the wordWrap settings
            if self.settings["wordWrap"]:
                self.text.setWordWrapMode(QtGui.QTextOption.WordWrap)
            else:
                self.text.setWordWrapMode(QtGui.QTextOption.NoWrap)

            self.settingsChanged.emit()

        # Make sure QT properly handles the memory after this function ends
        window.close()
        window.deleteLater()

    def __refreshBuffer(self):
        """
        This is where all the strings in the buffer written to the console
        :return:
        """


        if len(self.printBuffer) == 0: return

        with self.printLock:
            tempBuffer = self.printBuffer
            self.printBuffer = []

        # This is the text that will be inserted onto the console window
        textToInsert = ""

        # Build the textToInsert string by
        for classStr, printStr in tempBuffer:

            printStr = str(printStr)
            if len(printStr) == 0: continue

            # Check the origin of the print. If its not supported in the settings, exit
            category = self.__allowString(classStr)

            # Check if the user has this category turned on in settings. If there's an error, print anyways.
            if category is None and "ERROR" not in printStr: continue

            if category is None: category = classStr



            # Prepare the text to add to console
            printStr = category + " " * (15 - len(category)) + printStr

            # This will indent any newlines to the level of the print text, so its not mixed with the category text
            printStr = printStr.replace("\n", "\n" + " " * 15)

            # Write to the console log
            textToInsert += printStr + "\n"


        # Insert the text and scroll to the bottom of the console
        if len(textToInsert):

            self.text.insertPlainText(textToInsert)
            c = self.text.textCursor()
            c.movePosition(QtGui.QTextCursor.End)
            self.text.setTextCursor(c)


# For overlaying things on top of a wdiget
class OverlayCenter(QtWidgets.QLayout):
    """Layout for managing overlays."""

    def __init__(self, parent):
        super().__init__(parent)

        # Properties
        self.setContentsMargins(0, 0, 0, 0)

        self.items = []
    # end Constructor

    def addLayout(self, layout):
        """Add a new layout to overlay on top of the other layouts and widgets."""
        self.addChildLayout(layout)
        self.addItem(layout)
    # end addLayout

    def __del__(self):
        """Destructor for garbage collection."""
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)
    # end Destructor

    def addItem(self, item):
        """Add an item (widget/layout) to the list."""
        self.items.append(item)
    # end addItem

    def count(self):
        """Return the number of items."""
        return len(self.items)
    # end Count

    def itemAt(self, index):
        """Return the item at the given index."""
        if index >= 0 and index < len(self.items):
            return self.items[index]

        return None
    # end itemAt

    def takeAt(self, index):
        """Remove and return the item at the given index."""
        if index >= 0 and index < len(self.items):
            return self.items.pop(index)

        return None
    # end takeAt

    def setGeometry(self, rect):
        """Set the main geometry and the item geometry."""
        super().setGeometry(rect)

        for item in self.items:
            item.setGeometry(rect)
    # end setGeometry

class Overlay(QtWidgets.QBoxLayout):
    """Overlay widgets on a parent widget."""

    def __init__(self, location="left", parent=None):
        super().__init__(QtWidgets.QBoxLayout.TopToBottom, parent)

        if location == "left":
            self.setDirection(QtWidgets.QBoxLayout.TopToBottom)
            self.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        elif location == "right":
            self.setDirection(QtWidgets.QBoxLayout.TopToBottom)
            self.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        elif location == "top":
            self.setDirection(QtWidgets.QBoxLayout.LeftToRight)
            self.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
        elif location == "bottom":
            self.setDirection(QtWidgets.QBoxLayout.LeftToRight)
            self.setAlignment(QtCore.Qt.AlignBottom | QtCore.Qt.AlignHCenter)
        elif location == "center":
            self.setDirection(QtWidgets.QBoxLayout.LeftToRight)
            self.setAlignment(QtCore.Qt.AlignCenter)

        # self.css = "QWidget {background-color: black; color: black}"


# Center a window on the current screen
def centerScreen(self):
        frameGm = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        centerPoint = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)

        self.move(frameGm.topLeft())






