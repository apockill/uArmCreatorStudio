"""
This software was designed by Alexander Thiel
Github handle: https://github.com/apockill

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
__author__ = "Alexander Thiel"

from PyQt5        import QtGui, QtCore, QtWidgets
from threading    import RLock
from Logic.Global import printf
from Logic        import Paths

import ast  # To check if a statement is python parsible, for evals

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
        https://github.com/apockill/RobotGUIProgramming/blob/master/Logic/Robot.py


    vision
        Using this module, you can easly and without hassle track objects that you have taught the software in the
        Resource manager, find their location real time, search for past "tracks" of the objects, and act based upon
        that information. You can clear tracked objects, add new ones, and generally use powerful premade computer
        vision functions that have been built into this software already.

        For source code on the Vision class, go to:
        https://github.com/apockill/RobotGUIProgramming/blob/master/Logic/Vision.py


    resources
        You can pull any "objects" that you have built using the Resource Manager. This means, for example,
        that you could request a Motion Recording and replay it, or request a Vision object and track it.

        For source code on the Object Manager class, go to:
        https://github.com/apockill/RobotGUIProgramming/blob/master/Logic/ObjectManager.py


    settings
        This is a python dictionary of the GUI settings. This includes things like calibrations for various things.
        Try doing print(settings) to see what it contains.


Examples scripts using robot
    robot.setPos(x=0, y=15, z=15)   # This will set the robots position to XYZ(0, 15, 15)
    robot.setPos(x=0, y=15, z=15)   # Waits for robot to complete move before continuing
    robot.setPos(x=0)               # Will only set the x position, keeps the rest the same
    robot.setGripper(True)          # Turn on the pump. If false, it will deactivate the pump
    robot.setBuzzer(1500, 2)        # Play a tone through the robots buzzer. Parameters: Frequency, duration (seconds)
    robot.setSpeed(10)              # Sets speed for all future moves using robot.setPos. Speed set in cm/s
    robot.connected()               # Returns True if the robot is connected and working, False if not

    robot.getAngles()               # Returns the current angles of the robots servos: [servo0, servo1, servo2, servo3]
    robot.getCoords()               # Returns the current coordinate of the robot in [x, y, z] format
    robot.getTipSensor()            # Returns True or False, if the tip sensor on the robot is being pressed or not
    robot.getMoving()               # Returns True if the robot is currently moving



Example scripts using vision
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
        print("This function can work in any script command in the program!")
        print(someArgument)

    someVariableName = "This string can be used in any Script command in the program"

"""
    minWidth  = 550
    minHeight = 600


    def __init__(self, previousCode, parent):
        super(ScriptWidget, self).__init__(parent)
        self.prompt = parent
        self.prompt.content.setContentsMargins(5, 5, 5, 5)
        self.prompt.setMinimumWidth(self.minWidth)
        self.prompt.setMinimumHeight(self.minHeight)

        # QtWidgets.QTextEdit().toP
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
        self.docText.setFixedWidth(900)
        self.docText.setFixedHeight(self.minHeight)
        # self.docText.set
        # self.docText.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.docBtn.setFixedWidth(150)
        self.docText.setHidden(True)

        bold = QtGui.QFont()
        bold.setBold(True)
        self.hintLbl.setFont(bold)



        self.docBtn.clicked.connect(self.showDocumentation)


        monospace = QtGui.QFont("Monospace")
        monospace.setStyleHint(QtGui.QFont.TypeWriter)
        self.textEdit.setFont(monospace)
        self.textEdit.setMinimumHeight(self.minHeight)
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
        # mainVLayout.addStretch()
        mainVLayout.addLayout(row3)

        self.prompt.setMinimumWidth(600)
        self.prompt.setMinimumHeight(700)
        self.setLayout(mainVLayout)

    def showDocumentation(self):
        hiding = not self.docText.isHidden()

        if hiding:
            self.docBtn.setText("Show Documentation")
            self.docText.hide()
            self.textEdit.show()
            # self.prompt.setMinimumWidth(self.minWidth)
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

    def __init__(self, consoleSettings, parent):
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
        self.refreshTimer.start(1000.0 / 5)  # 1000 / fps

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
                self.write("", ret)


            self.inputEdt.setText("")

    def setExecFunction(self, execFunction):
        # Set the function that will evaluate code
        self.execFunction = execFunction


    def __allowString(self, classString):
        """
        Choose whether or not this string comes from a class that should be printed or not. This is set in the settings.
        """
        with self.printLock:

            if len(classString) == 0:
                return "Output"

            if classString in "Input":
                return "Input"


            # Print anything from the Robot class
            if "Robot" in classString:
                if self.settings["robot"]:
                    return "Robot"
                return ""

            # Print anything from the Vision class
            if "Vision" in classString:
                if self.settings["vision"]:
                    return "Vision"
                return ""

            # Print any serial communication
            if "Device" in classString:
                if self.settings["serial"]:
                    return "Communication"
                return ""

            # Print anything from Interpreter
            if "Interpreter" in classString:
                if self.settings["interpreter"]:
                    return "Interpreter"
                return ""

            # Print anything from Commands.py
            if ("Command" in classString) and not ("GUI" in classString):
                if self.settings["script"]:
                    return "Script"
                return ""

            # Print anything else that hasn't been specified
            if self.settings["gui"]:
                classString = "GUI"
                return classString

            return ""

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

        window.wrapChk   = QtWidgets.QCheckBox()
        window.robotChk  = QtWidgets.QCheckBox()   # Show prints from robot class
        window.visionChk = QtWidgets.QCheckBox()   # Show prints from vision class
        window.comChk    = QtWidgets.QCheckBox()   # Show prints from communication protocol
        window.interpChk = QtWidgets.QCheckBox()   # Show prints from Interpreter (Important!)
        window.scriptChk = QtWidgets.QCheckBox()   # Show prints from GUI Elements
        window.guiChk    = QtWidgets.QCheckBox()

        window.wrapChk  .setChecked(self.settings["wordWrap"])
        window.robotChk .setChecked(self.settings["robot"])
        window.visionChk.setChecked(self.settings["vision"])
        window.comChk   .setChecked(self.settings["serial"])
        window.interpChk.setChecked(self.settings["interpreter"])
        window.scriptChk.setChecked(self.settings["script"])
        window.guiChk   .setChecked(self.settings["gui"])

        window.content.addWidget(descLbl)
        addRow(wrapLbl,   window.wrapChk)
        addRow(robotLbl,  window.robotChk)
        addRow(robotLbl,  window.robotChk)
        addRow(visionLbl, window.visionChk)
        addRow(comLbl,    window.comChk)
        addRow(interpLbl, window.interpChk)
        addRow(scriptLbl, window.scriptChk)
        addRow(guiLbl,    window.guiChk)

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

            for classStr, printStr in self.printBuffer:

                # Check the origin of the print. If its not supported in the settings, exit
                category = self.__allowString(classStr)
                if len(category) == 0: continue


                # Prepare the text to add to console
                printStr = category + " " * (15 - len(category)) + str(printStr)
                if len(printStr) == 0: continue

                # Write to the console log
                self.text.insertPlainText(printStr + "\n")

                # Scroll to the bottom of the console
                c = self.text.textCursor()
                c.movePosition(QtGui.QTextCursor.End)
                self.text.setTextCursor(c)

            self.printBuffer = []


# Center a window on the current screen
def centerScreen(self):
        frameGm = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        centerPoint = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)

        self.move(frameGm.topLeft())









