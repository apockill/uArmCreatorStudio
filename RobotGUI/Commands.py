from PyQt4 import QtGui, QtCore
import Icons
import Robot            #Used for any peripheral functions in the library
from time import sleep  #Should only be used in the WaitCommand




class CommandWidget(QtGui.QWidget):
    def __init__(self, parent, onDeleteFunction):
        super(CommandWidget, self).__init__(parent)
        self.title       = QtGui.QLabel()
        self.description = QtGui.QLabel()
        self.icon        = QtGui.QLabel("No icon found.")

        # Create the delete button
        self.delete      = QtGui.QPushButton("")
        self.delete.setFlat(True)
        self.delete.setIcon(QtGui.QIcon(Icons.delete))
        self.delete.setVisible(False)
        self.delete.clicked.connect(lambda: onDeleteFunction(self))

        font = QtGui.QFont()
        font.setBold(True)
        self.title.setFont(font)

        leftLayout  = QtGui.QVBoxLayout()
        midLayout = QtGui.QVBoxLayout()
        rightLayout = QtGui.QVBoxLayout()

        leftLayout.addWidget(self.icon)

        midLayout.setSpacing(1)
        midLayout.addWidget(self.title)
        midLayout.addWidget(self.description)

        rightLayout.addWidget(self.delete)
        rightLayout.setAlignment(QtCore.Qt.AlignRight)

        mainHLayout = QtGui.QHBoxLayout()
        mainHLayout.addLayout(leftLayout)
        mainHLayout.addLayout(midLayout, QtCore.Qt.AlignLeft)
        mainHLayout.addLayout(rightLayout, QtCore.Qt.AlignRight)
        # self.textQVBoxLayout.addWidget(self.textUpQLabel)
        # self.textQVBoxLayout.addWidget(self.textDownQLabel)
        # self.allQHBoxLayout.addWidget(self.iconQLabel, 0)
        # self.allQHBoxLayout.addLayout(self.textQVBoxLayout, 1)

        self.setLayout(mainHLayout)

    def focusIn(self):
        self.delete.setVisible(True)

    def focusOut(self):
        self.delete.setVisible(False)

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

        moveXYZButton = self.getButton(MoveXYZCommand)
        detachButton  = self.getButton(DetachCommand)
        attachButton  = self.getButton(AttachCommand)
        refreshButton = self.getButton(RefreshCommand)
        waitButton    = self.getButton(WaitCommand)
        gripButton    = self.getButton(GripCommand)
        dropButton    = self.getButton(DropCommand)
        colorButton   = self.getButton(ColorTrackCommand)

        grid = QtGui.QGridLayout()
        grid.addWidget( moveXYZButton, 0, 0, QtCore.Qt.AlignTop)
        grid.addWidget(  detachButton, 1, 0, QtCore.Qt.AlignTop)
        grid.addWidget(  attachButton, 2, 0, QtCore.Qt.AlignTop)
        grid.addWidget( refreshButton, 3, 0, QtCore.Qt.AlignTop)
        grid.addWidget(    waitButton, 4, 0, QtCore.Qt.AlignTop)
        grid.addWidget(    gripButton, 5, 0, QtCore.Qt.AlignTop)
        grid.addWidget(    dropButton, 6, 0, QtCore.Qt.AlignTop)
        grid.addWidget(   colorButton, 7, 0, QtCore.Qt.AlignTop)
        self.setLayout(grid)

    def getButton(self, type):
        newButton = QtGui.QPushButton()
        newButton.setIcon(QtGui.QIcon(type.icon))
        newButton.setIconSize(QtCore.QSize(32, 32))
        newButton.setToolTip(type.tooltip)
        newButton.clicked.connect(lambda: self.addCmndFunc(type))
        return newButton


class Command(QtGui.QDialog):
    def __init__(self, parent):

        super(Command, self).__init__(parent)

        #self.parameters = {}  #Will be filled with parameters for the particular command
        self.accepted    = False
        self.mainVLayout = QtGui.QVBoxLayout()
        self.initBaseUI()

    def initBaseUI(self):
        #Create and connect buttons
        applyBtn  = QtGui.QPushButton('Apply', self)
        cancelBtn = QtGui.QPushButton('Cancel', self)
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
            print "Command.openView():\t About to execute self..."
            self.exec_()
        else:
            self.accepted = True
            return
        #self.show()
        print "Command.openView():\t Finished executing self..."

        #print "Command.openView():\t ERROR ERROR ERROR while opening view of command window. Fix!"

        #See if the user pressed Ok or if he cancelled/exited out
        if self.accepted:
            #Get information that the user input
            newParameters = self.getInfo().copy()

            #  Add the new parameters to the dictionary, and update changed values
            self.parameters.update(newParameters)



            print 'CommandWindow.openView():\t New parameters: ', self.parameters

        else:
            print 'CommandWindow.openView():\t User Canceled.'

    def sanitizeFloat(self, inputTextbox, fallback):
        """
        Sent it a textbox, and it will check the text in the textbox to make sure it is valid.
        If it is, return the float within the textbox. If not, it will set the textbox to the fallback value
        while also setting the textbox back to the fallback value.
        """
        #Sanitize input from the user
        try:
            intInput = float(str(inputTextbox.text()))
            print "before: ", inputTextbox.text(), "after: ", intInput
        except:
            intInput = fallback
            inputTextbox.setText(str(fallback))
        return intInput



########## COMMANDS ##########
class MoveXYZCommand(Command):
    tooltip    = "Set the robots position. The robot will move after all events are evaluated"
    icon       = Icons.xyz_command

    def __init__(self, parent, shared, **kwargs):
        self.title       = "Move XYZ"
        super(MoveXYZCommand, self).__init__(parent)

        #Set default parameters that will show up on the window
        self.parameters = kwargs.get("parameters",
                            {'x': 0,
                             'y': 0,
                             'z': 0,
                             'rel': False,  #Relative move?
                             'ref': True})  #Refresh after move?


        shared = kwargs.get("shared", None)
        if shared is not None:
            currentXYZ = shared.robot.currentCoord()
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
        #Build the info inputed into the window into a Json and return it. Used in parent class

        newParameters = {'x': self.sanitizeFloat(self.rotEdit, self.parameters["x"]),
                         'y': self.sanitizeFloat(self.strEdit, self.parameters["y"]),
                         'z': self.sanitizeFloat(self.hgtEdit, self.parameters["z"]),
                         'rel': self.relCheck.isChecked(),
                         'ref': self.refCheck.isChecked()}

        return newParameters

    def getWidget(self, onDeleteFunction):
        #Verify that there are no None statements in the parameters
        if any(self.parameters) is None or self.parameters.__len__() == 0:#any(x is None for x in self.parameters.itervalues()):
            return None
        else:

            listWidget = CommandWidget(parent=self, onDeleteFunction=onDeleteFunction)
            listWidget.setIcon(self.icon)
            listWidget.setTitle(self.title)
            listWidget.setTip(self.tooltip)
            listWidget.setDescription('X: '                + str(round(self.parameters['x'], 1))  +
                                           '   Y: '        + str(round(self.parameters['y'], 1))  +
                                           '   Z: '        + str(round(self.parameters['z'], 1))  +
                                           '   Relative: ' + str(    self.parameters['rel']) +
                                           '   Refresh: '  + str(    self.parameters['ref']))
            return listWidget

    def run(self, shared):
        print "MoveXYZCommand.run():\t Moving robot to ", self.parameters['x'], self.parameters['y'], self.parameters['z']
        shared.robot.setPos(x=self.parameters['x'],
                            y=self.parameters['y'],
                            z=self.parameters['z'],
                            relative=self.parameters['rel'])
        if self.parameters['ref']: shared.robot.refresh()


class DetachCommand(Command):
    """
    A command for detaching the servos of the robot
    """
    icon       = Icons.detach_command
    tooltip    = "Disengage servos on the robot"
    def __init__(self, parent, shared,  **kwargs):
        self.title       = "Detach Servos"
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
        #Build the info inputed into the window into a Json and return it. Used in parent class

        newParameters = {'servo1': self.srvo1Box.isChecked(),
                         'servo2': self.srvo2Box.isChecked(),
                         'servo3': self.srvo3Box.isChecked(),
                         'servo4': self.srvo4Box.isChecked()}

        return newParameters

    def getWidget(self, onDeleteFunction):
        #Verify that there are no None statements in the parameters
        if any(self.parameters) is None or self.parameters.__len__() == 0:#any(x is None for x in self.parameters.itervalues()):
            return None
        else:
            listWidget = CommandWidget(parent=self, onDeleteFunction=onDeleteFunction)
            listWidget.setIcon(self.icon)
            listWidget.setTitle(self.title)
            listWidget.setTip(self.tooltip)

            descriptionBuild = "Servos"
            if self.parameters["servo1"]: descriptionBuild += "  Rotation"
            if self.parameters["servo2"]: descriptionBuild += "  Stretch"
            if self.parameters["servo3"]: descriptionBuild += "  Height"
            if self.parameters["servo4"]: descriptionBuild += "  Wrist"

            listWidget.setDescription(descriptionBuild)

            return listWidget

    def run(self, shared):
        print "DetachCommand.run():\t Detaching servos ", self.parameters['servo1'], \
                                                        self.parameters['servo2'], \
                                                        self.parameters['servo3'], \
                                                        self.parameters['servo4']
        if self.parameters['servo1']: shared.robot.setServos(servo1=False)
        if self.parameters['servo2']: shared.robot.setServos(servo2=False)
        if self.parameters['servo3']: shared.robot.setServos(servo3=False)
        if self.parameters['servo4']: shared.robot.setServos(servo4=False)


class AttachCommand(Command):
    """
    A command for detaching the servos of the robot
    """
    icon       = Icons.attach_command
    tooltip    = "Re-engage servos on the robot"

    def __init__(self, parent, shared, **kwargs):
        self.title       = "Attach Servos"
        super(AttachCommand, self).__init__(parent)


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
        #Build the info inputed into the window into a Json and return it. Used in parent class

        newParameters = {'servo1': self.srvo1Box.isChecked(),
                         'servo2': self.srvo2Box.isChecked(),
                         'servo3': self.srvo3Box.isChecked(),
                         'servo4': self.srvo4Box.isChecked()}

        return newParameters

    def getWidget(self, onDeleteFunction):
        #Verify that there are no None statements in the parameters
        if any(self.parameters) is None or self.parameters.__len__() == 0:#any(x is None for x in self.parameters.itervalues()):
            return None
        else:
            listWidget = CommandWidget(parent=self, onDeleteFunction=onDeleteFunction)
            listWidget.setIcon(self.icon)
            listWidget.setTitle(self.title)
            listWidget.setTip(self.tooltip)

            descriptionBuild = "Servos"
            if self.parameters["servo1"]: descriptionBuild += "  Rotation"
            if self.parameters["servo2"]: descriptionBuild += "  Stretch"
            if self.parameters["servo3"]: descriptionBuild += "  Height"
            if self.parameters["servo4"]: descriptionBuild += "  Wrist"

            listWidget.setDescription(descriptionBuild)

            return listWidget

    def run(self, shared):
        print "AttachCommand.run():\t Attaching servos ", self.parameters['servo1'], \
                                                          self.parameters['servo2'], \
                                                          self.parameters['servo3'], \
                                                          self.parameters['servo4']
        #pos = Global.robot.currentCoord()
        #Global.robot.setPos(x=pos[1], y=pos[2], z=pos[3])  #This makes the robot attach at the current position it's at
        if self.parameters['servo1']: shared.robot.setServos(servo1=True)
        if self.parameters['servo2']: shared.robot.setServos(servo2=True)
        if self.parameters['servo3']: shared.robot.setServos(servo3=True)
        if self.parameters['servo4']: shared.robot.setServos(servo4=True)


class WaitCommand(Command):
    tooltip    = "Halts the program for a preset amount of time"
    icon       = Icons.wait_command

    def __init__(self, parent, shared, **kwargs):
        self.title       = "Wait"
        super(WaitCommand, self).__init__(parent)

        #Set default parameters that will show up on the window
        self.parameters = kwargs.get("parameters", {'time': 1.0})


        self.timeEdit = QtGui.QLineEdit()  #  Rotation textbox

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
        #Build the info inputed into the window into a Json and return it. Used in parent class

        newParameters = {'time': self.sanitizeFloat(self.timeEdit, self.parameters["time"])}

        return newParameters

    def getWidget(self, onDeleteFunction):
        #Verify that there are no None statements in the parameters
        if any(self.parameters) is None or self.parameters.__len__() == 0:#any(x is None for x in self.parameters.itervalues()):
            return None
        else:

            listWidget = CommandWidget(parent=self, onDeleteFunction=onDeleteFunction)
            listWidget.setIcon(self.icon)
            listWidget.setTitle(self.title)
            listWidget.setTip(self.tooltip)
            listWidget.setDescription(str(round(self.parameters['time'], 1)) + " seconds")
            return listWidget

    def run(self, shared):
        print "WaitCommand.run():\t Waiting for", self.parameters["time"], "seconds"
        sleep(self.parameters["time"])


class RefreshCommand(Command):
    """
    A command for refreshing the robots position by sending the robot information.
    It activates the robot.refresh() command, which detects if any movement variables have been changed
    and if they have sends that info over to the robot.
    """

    icon       = Icons.refresh_command
    tooltip    = "Send any changed position information to the robot. This will stop event processing for a moment."

    def __init__(self, parent, shared, **kwargs):
        self.title       = "Refresh Robot"
        super(RefreshCommand, self).__init__(parent)

        self.parameters = {}

    def getInfo(self):
        return self.parameters

    def getWidget(self, onDeleteFunction):
        #Verify that there are no None statements in the parameters

        listWidget = CommandWidget(parent=self, onDeleteFunction=onDeleteFunction)
        listWidget.setIcon(self.icon)
        listWidget.setTitle(self.title)
        listWidget.setTip(self.tooltip)

        listWidget.setDescription("")

        return listWidget

    def run(self, shared):
        shared.robot.refresh()


class GripCommand(Command):


    icon       = Icons.grip_command
    tooltip    = "Activate the robots gripper"

    def __init__(self, parent, shared, **kwargs):
        self.title       = "Activate Gripper"
        super(GripCommand, self).__init__(parent)


        #Since parameters is blank, no window will open up
        self.parameters = {}



    def getInfo(self):
        return self.parameters

    def getWidget(self, onDeleteFunction):
        #Verify that there are no None statements in the parameters

        listWidget = CommandWidget(parent=self, onDeleteFunction=onDeleteFunction)
        listWidget.setIcon(self.icon)
        listWidget.setTitle(self.title)
        listWidget.setTip(self.tooltip)

        listWidget.setDescription("")

        return listWidget

    def run(self, shared):
        shared.robot.setGripper(True)


class DropCommand(Command):

    icon       = Icons.drop_command
    tooltip    = "Deactivate the robots gripper"

    def __init__(self, parent, shared, **kwargs):
        self.title       = "Deactivate Gripper"
        super(DropCommand, self).__init__(parent)


        #Since parameters is blank, no window will open up
        self.parameters = {}



    def getInfo(self):
        return self.parameters

    def getWidget(self, onDeleteFunction):
        #Verify that there are no None statements in the parameters

        listWidget = CommandWidget(parent=self, onDeleteFunction=onDeleteFunction)
        listWidget.setIcon(self.icon)
        listWidget.setTitle(self.title)
        listWidget.setTip(self.tooltip)

        listWidget.setDescription("")

        return listWidget

    def run(self, shared):
        shared.robot.setGripper(False)


class ColorTrackCommand(Command):
    tooltip    = "Tracks objects by looking for a certain color."
    icon       = Icons.colortrack_command

    def __init__(self, parent, shared, **kwargs):
        self.title       = "Move to Color"
        super(ColorTrackCommand, self).__init__(parent)
        print shared.robot
        self.parameters = kwargs.get("parameters",
                            {'cHue':  0,
                             'tHue': 0,
                             'lSat':  0,
                             'hSat': 0,
                             'lVal':  0,
                             'hVal': 0})

        #Pull color from robot here
        #shared = kwargs.get("shared", None)
        # if shared is not None:
        #     currentXYZ = shared.robot.currentCoord()
        #     self.parameters = {'x': round(currentXYZ[1], 1),
        #                        'y': round(currentXYZ[2], 1),
        #                        'z': round(currentXYZ[3], 1),
        #                        'rel': False,
        #                        'ref': True}




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
        print "ColorTrackCommand.scanColors(): Scanning colors!"

        if shared is None:
            print "ColorTrackCommand.scanColors(): ERROR: Tried to scan colors while shared was None!"
            return

        avgColor = shared.vision.bgr2hsv(shared.vision.getColor())
        percentTolerance = .3

        print "avgColor", avgColor
        self.cHueEdit.setText(str(round(avgColor[0])))
        self.tHueEdit.setText(str(30))  #Recommended tolerance
        self.lSatEdit.setText(str(round(avgColor[1] - avgColor[1] * percentTolerance, 5)))
        self.hSatEdit.setText(str(round(avgColor[1] + avgColor[1] * percentTolerance, 5)))
        self.lValEdit.setText(str(round(avgColor[2] - avgColor[2] * percentTolerance, 5)))
        self.hValEdit.setText(str(round(avgColor[2] + avgColor[2] * percentTolerance, 5)))

    def getInfo(self):
        #Build the info inputed into the window into a Json and return it. Used in parent class

        newParameters = {'cHue': self.sanitizeFloat(self.cHueEdit, self.parameters['cHue']),
                         'tHue': self.sanitizeFloat(self.tHueEdit, self.parameters['tHue']),
                         'lSat': self.sanitizeFloat(self.lSatEdit, self.parameters['lSat']),
                         'hSat': self.sanitizeFloat(self.hSatEdit, self.parameters['hSat']),
                         'lVal': self.sanitizeFloat(self.lValEdit, self.parameters['lVal']),
                         'hVal': self.sanitizeFloat(self.hValEdit, self.parameters['hVal'])}
        return newParameters

    def getWidget(self, onDeleteFunction):
        #Verify that there are no None statements in the parameters
        if any(self.parameters) is None or self.parameters.__len__() == 0:#any(x is None for x in self.parameters.itervalues()):
            return None
        else:

            listWidget = CommandWidget(parent=self, onDeleteFunction=onDeleteFunction)
            listWidget.setIcon(self.icon)
            listWidget.setTitle(self.title)
            listWidget.setTip(self.tooltip)
            listWidget.setDescription('Track objects with a hue of ' + str(self.parameters['cHue']))
            return listWidget

    def run(self, shared):
        print "ColorTrackCommand.run():\t Tracking colored objects! "

        #Build a function that will return the objects position whenever it is called, using the self.parameters
        objPos = lambda: shared.vision.findObjectColor(self.parameters['cHue'],
                                                       self.parameters['tHue'],
                                                       self.parameters['lSat'],
                                                       self.parameters['hSat'],
                                                       self.parameters['lVal'],
                                                       self.parameters['hVal'])
        objCoords = objPos()
        print "found object at pos", objCoords

        if objCoords is None: return

        print "current dimensions", shared.vision.vStream.dimensions
        #Robot.getDirectionToTarget(targetPos, screenDimensions, tolerance)
        direction = Robot.getDirectionToTarget(objCoords, shared.vision.vStream.dimensions, 10)
        print "chosen direction: ", direction
