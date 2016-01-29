from PyQt4 import QtGui, QtCore
import Icons
import Robot
from time import sleep  #Should only be used in the WaitCommand
from Global import printf




class CommandWidget(QtGui.QWidget):
    def __init__(self, parent, onDeleteFunction):
        super(CommandWidget, self).__init__(parent)
        self.title        = QtGui.QLabel()
        self.description  = QtGui.QLabel()
        self.icon         = QtGui.QLabel("No Icon Found")
        self.deleteBtn    = QtGui.QPushButton("")
        self.indent       = 0

        self.initUI()
        self.deleteBtn.clicked.connect(onDeleteFunction)

    def initUI(self):
        # Create the delete button
        self.deleteBtn.setFlat(True)
        self.deleteBtn.setIcon(QtGui.QIcon(Icons.delete))
        self.deleteBtn.setVisible(False)


        font = QtGui.QFont()
        font.setBold(True)
        self.title.setFont(font)

        leftLayout  = QtGui.QVBoxLayout()
        midLayout   = QtGui.QVBoxLayout()
        rightLayout = QtGui.QVBoxLayout()

        leftLayout.addWidget(self.icon)


        midLayout.setSpacing(1)
        midLayout.addWidget(self.title)
        midLayout.addWidget(self.description)

        rightLayout.addWidget(self.deleteBtn)
        rightLayout.setAlignment(QtCore.Qt.AlignRight)

        mainHLayout = QtGui.QHBoxLayout()
        mainHLayout.addLayout(leftLayout)
        mainHLayout.addLayout(midLayout, QtCore.Qt.AlignLeft)
        mainHLayout.addLayout(rightLayout, QtCore.Qt.AlignRight)

        self.setLayout(mainHLayout)


    def setFocused(self, isFocused):
        #Determines whether or not the delete button is visible. Should only be visible when widget is clicked
        if isFocused:
            self.deleteBtn.setVisible(True)
        else:
            self.deleteBtn.setVisible(False)

    def setIndent(self, indent):
        if self.indent == indent: return
        print "set Indent", indent
        self.indent = indent
        if indent >= 0:
            self.layout().setContentsMargins(25 * indent, 0, 0, 0)
        else:
            self.layout().setContentsMargins(0, 0, 0, 0)



    #The following are accessed only by Command.dressWidget()
    def setTitle(self, text):
        self.title.setText(text)

    def setDescription(self, text):
        self.description.setText(text)

    def setIcon(self, icon):
        self.icon.setPixmap(QtGui.QPixmap(icon))

    def setTip(self, text):
        self.setToolTip(text)


class CommandMenuWidget(QtGui.QWidget):
    def __init__(self, addCmndFunc, parent):
        super(CommandMenuWidget, self).__init__(parent)

        #addCmndFunc is a function passed from ControlPanel to be able to hook buttons to that function
        self.addCmndFunc = addCmndFunc
        self.initUI()

    def initUI(self):

        moveXYZBtn  = self.getButton(MoveXYZCommand)
        detachBtn   = self.getButton(DetachCommand)
        attachBtn   = self.getButton(AttachCommand)
        refreshBtn  = self.getButton(RefreshCommand)
        waitBtn     = self.getButton(WaitCommand)
        gripBtn     = self.getButton(GripCommand)
        dropBtn     = self.getButton(DropCommand)
        colorBtn    = self.getButton(ColorTrackCommand)
        testVarBtn  = self.getButton(TestVariable)
        startBlkBtn = self.getButton(StartBlockCommand)
        endBlkBtn   = self.getButton(EndBlockCommand)


        grid = QtGui.QGridLayout()
        grid.addWidget( moveXYZBtn,  0, 0, QtCore.Qt.AlignTop)
        grid.addWidget(  detachBtn,  1, 0, QtCore.Qt.AlignTop)
        grid.addWidget(  attachBtn,  2, 0, QtCore.Qt.AlignTop)
        grid.addWidget( refreshBtn,  3, 0, QtCore.Qt.AlignTop)
        grid.addWidget(    waitBtn,  4, 0, QtCore.Qt.AlignTop)
        grid.addWidget(    dropBtn,  5, 0, QtCore.Qt.AlignTop)
        grid.addWidget(    gripBtn,  6, 0, QtCore.Qt.AlignTop)
        grid.addWidget(   colorBtn,  7, 0, QtCore.Qt.AlignTop)
        grid.addWidget( testVarBtn,  8, 0, QtCore.Qt.AlignTop)
        grid.addWidget(startBlkBtn,  9, 0, QtCore.Qt.AlignTop)
        grid.addWidget(  endBlkBtn, 10, 0, QtCore.Qt.AlignTop)

        self.setLayout(grid)

    def getButton(self, type):
        newButton = QtGui.QPushButton()
        newButton.setIcon(QtGui.QIcon(type.icon))
        newButton.setIconSize(QtCore.QSize(32, 32))
        newButton.setToolTip(type.tooltip)
        newButton.clicked.connect(lambda: self.addCmndFunc(type))
        return newButton


class Command(QtGui.QDialog):
    tooltip = ''
    icon    = ''
    title   = ''

    def __init__(self, parent):
        super(Command, self).__init__(parent)
        self.parent = parent
        self.description = ""
        self.parameters = {}  #For commands with no parameters, this should stay empty
        self.accepted    = False
        self.mainVLayout = QtGui.QVBoxLayout()
        self.initBaseUI()
        self.indent = 0    #Updated in CommandList.refresh()

    def initBaseUI(self):
        #Create and connect buttons
        applyBtn  = QtGui.QPushButton('Apply')
        cancelBtn = QtGui.QPushButton('Cancel')
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

        self.setMaximumWidth(450)
        self.setLayout(grid)
        self.setWindowTitle(self.title)


    def applyClicked(self):
        self.accepted = True
        self.close()

    def cancelClicked(self):
        self.close()


    def openView(self):  #Open window\
        #Run the info window and prevent other windows from being clicked while open:


        if len(self.parameters):  #If this object has a window object, then execute
            #printf("Command.openView(): About to execute self...", self, super(Command, self), self.parent)
            self.exec_()


        else:
            self.accepted = True
            return

        printf("Command.openView(): Finished executing self...")


        #See if the user pressed Ok or if he cancelled/exited out
        if self.accepted:
            #Get information that the user input
            newParameters = self.getInfo().copy()

            #  Add the new parameters to the dictionary, and update changed values
            self.parameters.update(newParameters)

            self.updateDescription()

            printf('CommandWindow.openView(): New parameters: ', self.parameters)

        else:
            printf('CommandWindow.openView(): User Canceled.')

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
        #Sanitize input from the user
        try:
            intInput = float(str(inputTextbox.text()))
        except:
            intInput = fallback
            inputTextbox.setText(str(fallback))
        return intInput


#The following commands should be empty, and only are there so that subclasses without them don't cause errors

    def getInfo(self):
        #In case there is a command that does not have info, if it is called then
        #There will be no error. For example, "start block of code" "refresh" or
        #"activate/deactivate gripper" do not have info to give
        pass

    def run(self, shared):
        #For any command that does not have a function such as "start block of code"
        #Then this function will run in it's place.
        pass

    def updateDescription(self):
        #This is called in openView() and will update the decription to match the parameters
        pass





########## COMMANDS ##########
class MoveXYZCommand(Command):
    title      = "Move XYZ"
    tooltip    = "Set the robots position. The robot will move after all events are evaluated"
    icon       = Icons.xyz_command

    def __init__(self, parent, shared, **kwargs):
        super(MoveXYZCommand, self).__init__(parent)

        #Set default parameters that will show up on the window
        if 'parameters' in kwargs:
            self.parameters = kwargs["parameters"]
        else:
            currentXYZ = shared.getRobot().getCurrentCoord()
            self.parameters = {'x': round(currentXYZ[1], 1),
                               'y': round(currentXYZ[2], 1),
                               'z': round(currentXYZ[3], 1),
                               'rel': False,
                               'ref': True}



        self.rotEdit     = QtGui.QLineEdit()  #  Rotation textbox
        self.strEdit     = QtGui.QLineEdit()  #  Stretch textbox
        self.hgtEdit     = QtGui.QLineEdit()  #  Height textbox
        self.relCheck    = QtGui.QCheckBox()  #  "relative" CheckBox
        self.refCheck    = QtGui.QCheckBox()  #  "refresh" CheckBox

        self.initUI()
        self.setWindowIcon(QtGui.QIcon(self.icon))

    def initUI(self):
        #Set up all the labels for the inputs
        rotLabel = QtGui.QLabel('X:')
        strLabel = QtGui.QLabel('Y:')
        hgtLabel = QtGui.QLabel('Z:')
        relLabel = QtGui.QLabel('Relative')
        refLabel = QtGui.QLabel('Refresh')

        #Fill the textboxes with the default parameters
        self.rotEdit.setText(str(self.parameters['x']))
        self.strEdit.setText(str(self.parameters['y']))
        self.hgtEdit.setText(str(self.parameters['z']))
        self.relCheck.setChecked(self.parameters['rel'])
        self.refCheck.setChecked(self.parameters['ref'])

        row1 = QtGui.QHBoxLayout()
        row2 = QtGui.QHBoxLayout()
        row3 = QtGui.QHBoxLayout()
        row4 = QtGui.QHBoxLayout()
        row5 = QtGui.QHBoxLayout()

        row1.addWidget(rotLabel, QtCore.Qt.AlignRight)
        row1.addWidget(self.rotEdit, QtCore.Qt.AlignJustify)

        row2.addWidget(strLabel, QtCore.Qt.AlignRight)
        row2.addWidget(self.strEdit, QtCore.Qt.AlignJustify)

        row3.addWidget(hgtLabel, QtCore.Qt.AlignRight)
        row3.addWidget(self.hgtEdit, QtCore.Qt.AlignJustify)

        row4.addWidget(relLabel, QtCore.Qt.AlignRight)
        row4.addWidget(self.relCheck, QtCore.Qt.AlignJustify)

        row5.addWidget(refLabel, QtCore.Qt.AlignRight)
        row5.addWidget(self.refCheck, QtCore.Qt.AlignJustify)

        self.mainVLayout.addLayout(row1)
        self.mainVLayout.addLayout(row2)
        self.mainVLayout.addLayout(row3)
        self.mainVLayout.addLayout(row4)
        self.mainVLayout.addLayout(row5)

    def getInfo(self):
        newParameters = {'x': self.sanitizeFloat(self.rotEdit, self.parameters["x"]),
                         'y': self.sanitizeFloat(self.strEdit, self.parameters["y"]),
                         'z': self.sanitizeFloat(self.hgtEdit, self.parameters["z"]),
                         'rel': self.relCheck.isChecked()}

        return newParameters

    def updateDescription(self):
        self.description =     'X: '        + str(round(self.parameters['x'], 1))  +  \
                            '   Y: '        + str(round(self.parameters['y'], 1))  +  \
                            '   Z: '        + str(round(self.parameters['z'], 1))  +  \
                            '   Relative: ' + str(      self.parameters['rel'])

    def run(self, shared):
        printf("MoveXYZCommand.run(): Moving robot to ", self.parameters['x'], self.parameters['y'], self.parameters['z'])
        shared.getRobot().setPos(x=self.parameters['x'],
                                 y=self.parameters['y'],
                                 z=self.parameters['z'],
                                 relative=self.parameters['rel'])

        if self.refCheck.isChecked():  shared.getRobot().refresh()


class DetachCommand(Command):
    """
    A command for detaching the servos of the robot
    """
    title       = "Detach Servos"
    tooltip    = "Disengage servos on the robot"
    icon       = Icons.detach_command

    def __init__(self, parent, shared, **kwargs):
        super(DetachCommand, self).__init__(parent)


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
        self.setWindowIcon(QtGui.QIcon(self.icon))

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
        row1.addStretch(1)
        row1.addWidget(self.srvo1Box, QtCore.Qt.AlignLeft)

        row2.addWidget(label2, QtCore.Qt.AlignRight)
        row2.addStretch(1)
        row2.addWidget(self.srvo2Box, QtCore.Qt.AlignLeft)

        row3.addWidget(label3, QtCore.Qt.AlignRight)
        row3.addStretch(1)
        row3.addWidget(self.srvo3Box, QtCore.Qt.AlignLeft)

        row4.addWidget(label4, QtCore.Qt.AlignRight)
        row4.addStretch(1)
        row4.addWidget(self.srvo4Box, QtCore.Qt.AlignLeft)

        self.mainVLayout.addLayout(row1)
        self.mainVLayout.addLayout(row2)
        self.mainVLayout.addLayout(row3)
        self.mainVLayout.addLayout(row4)

    def getInfo(self):
        newParameters = {'servo1': self.srvo1Box.isChecked(),
                         'servo2': self.srvo2Box.isChecked(),
                         'servo3': self.srvo3Box.isChecked(),
                         'servo4': self.srvo4Box.isChecked()}

        return newParameters

    def updateDescription(self):
        descriptionBuild = "Servos"
        if self.parameters["servo1"]: descriptionBuild += "  Rotation"
        if self.parameters["servo2"]: descriptionBuild += "  Stretch"
        if self.parameters["servo3"]: descriptionBuild += "  Height"
        if self.parameters["servo4"]: descriptionBuild += "  Wrist"

        self.description = descriptionBuild

    def run(self, shared):
        printf("DetachCommand.run(): Detaching servos ", self.parameters['servo1'], \
                                                         self.parameters['servo2'], \
                                                         self.parameters['servo3'], \
                                                         self.parameters['servo4'])
        if self.parameters['servo1']: shared.getRobot().setServos(servo1=False)
        if self.parameters['servo2']: shared.getRobot().setServos(servo2=False)
        if self.parameters['servo3']: shared.getRobot().setServos(servo3=False)
        if self.parameters['servo4']: shared.getRobot().setServos(servo4=False)


class AttachCommand(Command):
    """
    A command for attaching the servos of the robot
    """
    title      = "Attach Servos"
    tooltip    = "Re-engage servos on the robot"
    icon       = Icons.attach_command


    def __init__(self, parent, shared, **kwargs):
        super(AttachCommand, self).__init__(parent)

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
        self.setWindowIcon(QtGui.QIcon(self.icon))

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
        row1.addStretch(1)
        row1.addWidget(self.srvo1Box, QtCore.Qt.AlignLeft)

        row2.addWidget(label2, QtCore.Qt.AlignRight)
        row2.addStretch(1)
        row2.addWidget(self.srvo2Box, QtCore.Qt.AlignLeft)

        row3.addWidget(label3, QtCore.Qt.AlignRight)
        row3.addStretch(1)
        row3.addWidget(self.srvo3Box, QtCore.Qt.AlignLeft)

        row4.addWidget(label4, QtCore.Qt.AlignRight)
        row4.addStretch(1)
        row4.addWidget(self.srvo4Box, QtCore.Qt.AlignLeft)

        self.mainVLayout.addLayout(row1)
        self.mainVLayout.addLayout(row2)
        self.mainVLayout.addLayout(row3)
        self.mainVLayout.addLayout(row4)

    def getInfo(self):
        newParameters = {'servo1': self.srvo1Box.isChecked(),
                         'servo2': self.srvo2Box.isChecked(),
                         'servo3': self.srvo3Box.isChecked(),
                         'servo4': self.srvo4Box.isChecked()}

        return newParameters

    def updateDescription(self):
        descriptionBuild = "Servos"
        if self.parameters["servo1"]: descriptionBuild += "  Rotation"
        if self.parameters["servo2"]: descriptionBuild += "  Stretch"
        if self.parameters["servo3"]: descriptionBuild += "  Height"
        if self.parameters["servo4"]: descriptionBuild += "  Wrist"

        self.description = descriptionBuild

    def run(self, shared):
        printf("AttachCommand.run(): Attaching servos ", self.parameters['servo1'], \
                                                          self.parameters['servo2'], \
                                                          self.parameters['servo3'], \
                                                          self.parameters['servo4'])

        if self.parameters['servo1']: shared.getRobot().setServos(servo1=True)
        if self.parameters['servo2']: shared.getRobot().setServos(servo2=True)
        if self.parameters['servo3']: shared.getRobot().setServos(servo3=True)
        if self.parameters['servo4']: shared.getRobot().setServos(servo4=True)


class WaitCommand(Command):
    title     = "Wait"
    tooltip   = "Halts the program for a preset amount of time"
    icon      = Icons.wait_command

    def __init__(self, parent, shared, **kwargs):
        super(WaitCommand, self).__init__(parent)


        #Set default parameters that will show up on the window
        self.parameters = kwargs.get("parameters", {'time': 1.0})

        self.timeEdit = QtGui.QLineEdit()

        self.initUI()
        self.setWindowIcon(QtGui.QIcon(self.icon))

    def initUI(self):
        #Set up all the labels for the inputs
        timeLabel = QtGui.QLabel('Number of seconds: ')


        #Fill the textboxes with the default parameters
        self.timeEdit.setText(str(self.parameters['time']))

        row1 = QtGui.QHBoxLayout()

        row1.addWidget(timeLabel, QtCore.Qt.AlignRight)
        row1.addWidget(self.timeEdit, QtCore.Qt.AlignJustify)

        self.mainVLayout.addLayout(row1)

    def getInfo(self):
        newParameters = {'time': self.sanitizeFloat(self.timeEdit, self.parameters["time"])}
        return newParameters

    def updateDescription(self):
        self.description = str(round(self.parameters['time'], 1)) + " seconds"

    def run(self, shared):
        printf("WaitCommand.run(): Waiting for", self.parameters["time"], "seconds")
        sleep(self.parameters["time"])


class RefreshCommand(Command):
    """
    A command for refreshing the robots position by sending the robot information.
    It activates the robot.refresh() command, which detects if any movement variables have been changed
    and if they have sends that info over to the robot.
    """
    title      = "Refresh Robot"
    tooltip    = "Send any changed position information to the robot. This will stop event processing for a moment."
    icon       = Icons.refresh_command

    def __init__(self, parent, shared, **kwargs):
        super(RefreshCommand, self).__init__(parent)

    def run(self, shared):
        shared.getRobot().refresh()


class GripCommand(Command):
    title       = "Activate Gripper"
    tooltip    = "Activate the robots gripper"
    icon       = Icons.grip_command

    def __init__(self, parent, shared, **kwargs):
        super(GripCommand, self).__init__(parent)

    def run(self, shared):
        shared.getRobot().setGripper(True)


class DropCommand(Command):
    title      = "Deactivate Gripper"
    tooltip    = "Deactivate the robots gripper"
    icon       = Icons.drop_command

    def __init__(self, parent, shared,  **kwargs):
        super(DropCommand, self).__init__(parent)


    def run(self, shared):
        shared.getRobot().setGripper(False)


class ColorTrackCommand(Command):
    title      = "Move to Color"
    tooltip    = "Tracks objects by looking for a certain color."
    icon       = Icons.colortrack_command

    def __init__(self, parent, shared, **kwargs):

        super(ColorTrackCommand, self).__init__(parent)
        self.parameters = kwargs.get("parameters",
                            {'cHue': 0,
                             'tHue': 0,
                             'lSat': 0,
                             'hSat': 0,
                             'lVal': 0,
                             'hVal': 0})




        self.cHueEdit = QtGui.QLineEdit()
        self.tHueEdit = QtGui.QLineEdit()
        self.lSatEdit = QtGui.QLineEdit()
        self.hSatEdit = QtGui.QLineEdit()
        self.lValEdit = QtGui.QLineEdit()
        self.hValEdit = QtGui.QLineEdit()

        self.initUI(shared)
        self.setWindowIcon(QtGui.QIcon(self.icon))

    def initUI(self, shared):
        #Set up all the labels for the inputs
        hueLabel = QtGui.QLabel('Hue/Tolerance: ')
        satLabel = QtGui.QLabel('Saturation range: ')
        valLabel = QtGui.QLabel('Value range:')



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
        scanLabel  = QtGui.QLabel("Press button to automatically fill out values:")
        scanButton = QtGui.QPushButton("Scan Colors")
        scanButton.clicked.connect(lambda: self.scanColors(shared))



        row1 = QtGui.QHBoxLayout()
        row2 = QtGui.QHBoxLayout()
        row3 = QtGui.QHBoxLayout()
        row4 = QtGui.QHBoxLayout()

        row1.addWidget(    scanLabel, QtCore.Qt.AlignLeft)
        row1.addWidget(   scanButton, QtCore.Qt.AlignRight)

        row2.addWidget(     hueLabel, QtCore.Qt.AlignLeft)
        row2.addWidget(self.cHueEdit, QtCore.Qt.AlignRight)
        row2.addWidget(QtGui.QLabel("+-"))
        row2.addWidget(self.tHueEdit, QtCore.Qt.AlignRight)

        row3.addWidget(     satLabel, QtCore.Qt.AlignLeft)
        row3.addWidget(self.lSatEdit, QtCore.Qt.AlignRight)
        row3.addWidget(QtGui.QLabel("to"))
        row3.addWidget(self.hSatEdit, QtCore.Qt.AlignRight)

        row4.addWidget(     valLabel, QtCore.Qt.AlignLeft)
        row4.addWidget(self.lValEdit, QtCore.Qt.AlignRight)
        row4.addWidget(QtGui.QLabel("to"))
        row4.addWidget(self.hValEdit, QtCore.Qt.AlignRight)



        self.mainVLayout.addLayout(row1)
        self.mainVLayout.addLayout(row2)
        self.mainVLayout.addLayout(row3)
        self.mainVLayout.addLayout(row4)


    def scanColors(self, shared):
        printf("ColorTrackCommand.scanColors(): Scanning colors!")

        if shared is None:
            printf("ColorTrackCommand.scanColors(): ERROR: Tried to scan colors while shared was None! colors!")

            return

        avgColor = shared.getVision().bgr2hsv(shared.getVision().getColor())
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

    def run(self, shared):
        printf("ColorTrackCommand.run(): Tracking colored objects! ")

        if not shared.getVision().cameraConnected():
            printf("ColorTrackCommand.run(): ERROR: No camera detected")
            return

        #Build a function that will return the objects position whenever it is called, using the self.parameters
        objPos = lambda: shared.getVision().findObjectColor(self.parameters['cHue'],
                                                            self.parameters['tHue'],
                                                            self.parameters['lSat'],
                                                            self.parameters['hSat'],
                                                            self.parameters['lVal'],
                                                            self.parameters['hVal'])
        objCoords = objPos()


        #If no object was found
        if objCoords is None: return

        move = Robot.getDirectionToTarget(objCoords, shared.getVision().vStream.dimensions, 10)

        #If the robot is already focused
        if move is None: return

        #Convert the move to one on the base grid
        baseAngle = shared.getRobot().getBaseAngle()
        modDirection = Robot.getRelative(move[0], move[1], baseAngle)

        # if modDirection is None: return


        shared.getRobot().setPos(x=modDirection[0] / 3, y=modDirection[1] / 3, relative=True)



class TestVariable(Command):
    title      = "Test Variable"
    tooltip    = "This will allow/disallow code to run that is in blocked brackets below it."
    icon       = Icons.test_var_command

    def __init__(self, parent, shared, **kwargs):
        super(TestVariable, self).__init__(parent)


        self.parameters = kwargs.get("parameters",
                                     {'variable': '',
                                      'not': False})  #Flip the result

        self.varEdit   = QtGui.QLineEdit(self)   #  "Variable" edit
        self.tstMenu   = QtGui.QComboBox()       #  "test" menu
        self.notCheck  = QtGui.QCheckBox(self)   #  "Not" CheckBox

        self.initUI()
        self.setWindowIcon(QtGui.QIcon(self.icon))

    def initUI(self):
        self.varEdit.setFixedWidth(100)
        self.tstMenu.setFixedWidth(100)

        self.tstMenu.addItem('Equal To')
        self.tstMenu.addItem('Greater Than')
        self.tstMenu.addItem('Less Then')


        #Set up all the labels for the inputs
        varLabel = QtGui.QLabel('Variable: ')
        tstLabel = QtGui.QLabel('Test: ')
        notLabel = QtGui.QLabel('Not')

        #Fill the textboxes with the default parameters
        self.varEdit.setText(str(self.parameters['variable']))
        self.tstMenu.setCurrentIndex(2)
        self.notCheck.setChecked(self.parameters['not'])

        row1 = QtGui.QHBoxLayout()
        row2 = QtGui.QHBoxLayout()
        row3 = QtGui.QHBoxLayout()

        row1.addWidget(     varLabel, QtCore.Qt.AlignRight)
        row1.addWidget( self.varEdit, QtCore.Qt.AlignLeft)

        row2.addWidget(tstLabel, QtCore.Qt.AlignRight)
        row2.addWidget(self.tstMenu, QtCore.Qt.AlignLeft)

        row3.addStretch(1)
        row3.addWidget(     notLabel)
        row3.addWidget(self.notCheck)

        self.mainVLayout.addLayout(row1)
        self.mainVLayout.addLayout(row2)
        self.mainVLayout.addLayout(row3)


    def getInfo(self):
        newParameters = {'variable': str(self.varEdit.text()),
                              'not': self.notCheck.isChecked()}
        return newParameters

    def updateDescription(self):
        self.description =  'checked: ' + str(self.notCheck.isChecked())

    def run(self, shared):
        return self.notCheck.isChecked()


class StartBlockCommand(Command):
    """
    Start a block of code with this class
    """

    icon       = Icons.startblock_command
    tooltip    = "This is the start of a block of commands that only run if a conditional statement is met."

    def __init__(self, parent, shared, **kwargs):
        super(StartBlockCommand, self).__init__(parent)


class EndBlockCommand(Command):
    """
    End a block of code with this command
    """

    icon       = Icons.endblock_command
    tooltip    = "This is the end of a block of commands."

    def __init__(self, parent, shared, **kwargs):
        super(EndBlockCommand, self).__init__(parent)


















