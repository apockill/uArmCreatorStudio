from PyQt4 import QtGui, QtCore
import Icons
import Global




class CommandWidget(QtGui.QWidget):
    def __init__(self, parent = None):
        super(CommandWidget, self).__init__(parent)
        self.title       = QtGui.QLabel()
        self.description = QtGui.QLabel()
        self.icon        = QtGui.QLabel("No icon found.")

        font = QtGui.QFont()
        font.setBold(True)
        self.title.setFont(font)

        leftLayout  = QtGui.QVBoxLayout()
        rightLayout = QtGui.QVBoxLayout()

        leftLayout.addWidget(self.icon)

        rightLayout.setSpacing(1)
        rightLayout.addWidget(self.title)
        rightLayout.addWidget(self.description)

        mainHLayout = QtGui.QHBoxLayout()
        mainHLayout.addLayout(leftLayout)
        mainHLayout.addLayout(rightLayout, QtCore.Qt.AlignLeft)
        # self.textQVBoxLayout.addWidget(self.textUpQLabel)
        # self.textQVBoxLayout.addWidget(self.textDownQLabel)
        # self.allQHBoxLayout.addWidget(self.iconQLabel, 0)
        # self.allQHBoxLayout.addLayout(self.textQVBoxLayout, 1)

        self.setLayout(mainHLayout)

    def setTitle(self, text):
        self.title.setText(text)

    def setDescription(self, text):
        self.description.setText(text)

    def setIcon(self, icon):
        self.icon.setPixmap(QtGui.QPixmap(icon))


class CommandMenuWidget(QtGui.QWidget):
    def __init__(self, addCmndFunc):
        super(CommandMenuWidget, self).__init__()
        self.addCmndFunc = addCmndFunc
        self.initUI()

    def initUI(self):


        moveXYZButton = QtGui.QPushButton()
        moveXYZButton.setIcon(QtGui.QIcon(Icons.xyz_command))
        moveXYZButton.setIconSize(QtCore.QSize(32, 32))
        moveXYZButton.clicked.connect(lambda: self.addCmndFunc(MoveXYZCommand))

        detachButton  = QtGui.QPushButton()
        detachButton.setIcon(QtGui.QIcon(Icons.detach_command))
        detachButton.setIconSize(QtCore.QSize(32, 32))
        detachButton.clicked.connect(lambda: self.addCmndFunc(DetachCommand))

        attachButton  = QtGui.QPushButton()
        attachButton.setIcon(QtGui.QIcon(Icons.attach_command))
        attachButton.setIconSize(QtCore.QSize(32, 32))
        attachButton.clicked.connect(lambda: self.addCmndFunc(AttachCommand))

        grid = QtGui.QGridLayout()
        grid.addWidget(moveXYZButton, 0, 0, QtCore.Qt.AlignTop)
        grid.addWidget( detachButton, 1, 0, QtCore.Qt.AlignTop)
        grid.addWidget( attachButton, 2, 0, QtCore.Qt.AlignTop)
        self.setLayout(grid)




########## COMMANDS ##########
class Command(QtGui.QDialog):
    def __init__(self, parent):

        super(Command, self).__init__(parent)

        #self.parameters = {}  #Will be filled with parameters for the particular command
        self.accepted    = False
        self.mainVLayout = QtGui.QVBoxLayout()
       # self.parameters = {"type": type(self)}
        self.initBaseUI()
        #self.setAttribute( QtCore.Qt.WA_DeleteOnClose)

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

        self.setLayout(grid)
        self.setWindowTitle(self.title)

    def applyClicked(self):
        self.accepted = True
        self.close()

    def cancelClicked(self):
        self.close()

    def openView(self):  #Open window\
        #Run the info window and prevent other windows from being clicked while open:

        print "Command.openView():\t About to execute self..."
        self.exec_()
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
            print "c was not accepted"
            print 'CommandWindow.openView():\t User Canceled.'


class MoveXYZCommand(Command):
    def __init__(self, parent, **kwargs):
        self.title       = "Move XYZ"
        super(MoveXYZCommand, self).__init__(parent)

        #Set default parameters that will show up on the window
        self.icon        = Icons.xyz_command
        currentXYZ = Global.robot.currentCoord()
        self.parameters = kwargs.get("parameters",
                            {'x': round(currentXYZ[1], 1),
                             'y': round(currentXYZ[2], 1),
                             'z': round(currentXYZ[3], 1),
                             'rel': False})



        self.rotEdit     = QtGui.QLineEdit()  #  Rotation textbox
        self.strEdit     = QtGui.QLineEdit()  #  Stretch textbox
        self.hgtEdit     = QtGui.QLineEdit()  #  Height textbox
        self.relCheck    = QtGui.QCheckBox()  #  "relative" CheckBox
        self.initUI()
        self.setWindowIcon(QtGui.QIcon(self.icon))

    def initUI(self):
        #Set up all the labels for the inputs
        rotLabel = QtGui.QLabel('X:')
        strLabel = QtGui.QLabel('Y:')
        hgtLabel = QtGui.QLabel('Z:')
        relLabel = QtGui.QLabel('Relative')

        #Fill the textboxes with the default parameters
        self.rotEdit.setText(str(self.parameters['x']))
        self.strEdit.setText(str(self.parameters['y']))
        self.hgtEdit.setText(str(self.parameters['z']))
        self.relCheck.setChecked(self.parameters['rel'])


        row1 = QtGui.QHBoxLayout()
        row2 = QtGui.QHBoxLayout()
        row3 = QtGui.QHBoxLayout()
        row4 = QtGui.QHBoxLayout()

        row1.addWidget(rotLabel, QtCore.Qt.AlignRight)
        row1.addWidget(self.rotEdit, QtCore.Qt.AlignJustify)

        row2.addWidget(strLabel, QtCore.Qt.AlignRight)
        row2.addWidget(self.strEdit, QtCore.Qt.AlignJustify)

        row3.addWidget(hgtLabel, QtCore.Qt.AlignRight)
        row3.addWidget(self.hgtEdit, QtCore.Qt.AlignJustify)

        row4.addWidget(relLabel, QtCore.Qt.AlignRight)
        row4.addWidget(self.relCheck, QtCore.Qt.AlignJustify)

        self.mainVLayout.addLayout(row1)
        self.mainVLayout.addLayout(row2)
        self.mainVLayout.addLayout(row3)
        self.mainVLayout.addLayout(row4)


    def getInfo(self):
        #Build the info inputed into the window into a Json and return it. Used in parent class

        newParameters = {'x': self.sanitizeFloat(self.rotEdit.text(), self.parameters["x"]),
                         'y': self.sanitizeFloat(self.strEdit.text(), self.parameters["y"]),
                         'z': self.sanitizeFloat(self.hgtEdit.text(), self.parameters["z"]),
                         'rel': self.relCheck.isChecked()}

        return newParameters

    def sanitizeFloat(self, input, fallback):
        #Sanitize input from the user
            try:
                intInput = float(input)
            except:
                intInput = fallback
            return intInput

    def getWidget(self):
        #Verify that there are no None statements in the parameters
        if any(self.parameters) is None or self.parameters.__len__() == 0:#any(x is None for x in self.parameters.itervalues()):
            return None
        else:
            listWidget = CommandWidget()
            listWidget.setIcon(self.icon)
            listWidget.setTitle(self.title)
            listWidget.setDescription('X: '                + str(int(self.parameters['x'])) +
                                           '   Y: '        + str(int(self.parameters['y'])) +
                                           '   Z: '        + str(int(self.parameters['z'])) +
                                           '   Relative: ' + str(    self.parameters['rel']))
            return listWidget

    def run(self):
        print "MoveXYZCommand.run():\t Moving robot to ", self.parameters['x'], self.parameters['y'], self.parameters['z']
        Global.robot.setPos(x=self.parameters['x'],
                            y=self.parameters['y'],
                            z=self.parameters['z'],
                            relative=self.parameters['rel'])


class DetachCommand(Command):
    """
    A command for detaching the servos of the robot
    """
    def __init__(self, parent, **kwargs):
        self.title       = "Detach Servos"
        super(DetachCommand, self).__init__(parent)
        #Command.__init__(self)

        #Set default parameters that will show up on the window
        self.icon       = Icons.detach_command
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
        row1.addWidget(self.srvo1Box, QtCore.Qt.AlignLeft)

        row2.addWidget(label2, QtCore.Qt.AlignRight)
        row2.addWidget(self.srvo2Box, QtCore.Qt.AlignLeft)

        row3.addWidget(label3, QtCore.Qt.AlignRight)
        row3.addWidget(self.srvo3Box, QtCore.Qt.AlignLeft)

        row4.addWidget(label4, QtCore.Qt.AlignRight)
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

    def getWidget(self):
        #Verify that there are no None statements in the parameters
        if any(self.parameters) is None or self.parameters.__len__() == 0:#any(x is None for x in self.parameters.itervalues()):
            return None
        else:
            listWidget = CommandWidget()
            listWidget.setIcon(self.icon)
            listWidget.setTitle(self.title)

            descriptionBuild = "Servos"
            if self.parameters["servo1"]: descriptionBuild += "  Rotation"
            if self.parameters["servo2"]: descriptionBuild += "  Stretch"
            if self.parameters["servo3"]: descriptionBuild += "  Height"
            if self.parameters["servo4"]: descriptionBuild += "  Wrist"

            listWidget.setDescription(descriptionBuild)

            return listWidget

    def run(self):
        print "DetachCommand.run():\t Detaching servos ", self.parameters['servo1'], \
                                                        self.parameters['servo2'], \
                                                        self.parameters['servo3'], \
                                                        self.parameters['servo4']
        if self.parameters['servo1']: Global.robot.setServos(servo1=False)
        if self.parameters['servo2']: Global.robot.setServos(servo2=False)
        if self.parameters['servo3']: Global.robot.setServos(servo3=False)
        if self.parameters['servo4']: Global.robot.setServos(servo4=False)


class AttachCommand(Command):
    """
    A command for detaching the servos of the robot
    """
    def __init__(self, parent, **kwargs):
        self.title       = "Attach Servos"
        super(AttachCommand, self).__init__(parent)
        #Command.__init__(self)

        #Set default parameters that will show up on the window
        self.icon       = Icons.attach_command
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
        row1.addWidget(self.srvo1Box, QtCore.Qt.AlignLeft)

        row2.addWidget(label2, QtCore.Qt.AlignRight)
        row2.addWidget(self.srvo2Box, QtCore.Qt.AlignLeft)

        row3.addWidget(label3, QtCore.Qt.AlignRight)
        row3.addWidget(self.srvo3Box, QtCore.Qt.AlignLeft)

        row4.addWidget(label4, QtCore.Qt.AlignRight)
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

    def getWidget(self):
        #Verify that there are no None statements in the parameters
        if any(self.parameters) is None or self.parameters.__len__() == 0:#any(x is None for x in self.parameters.itervalues()):
            return None
        else:
            listWidget = CommandWidget()
            listWidget.setIcon(self.icon)
            listWidget.setTitle(self.title)

            descriptionBuild = "Servos"
            if self.parameters["servo1"]: descriptionBuild += "  Rotation"
            if self.parameters["servo2"]: descriptionBuild += "  Stretch"
            if self.parameters["servo3"]: descriptionBuild += "  Height"
            if self.parameters["servo4"]: descriptionBuild += "  Wrist"

            listWidget.setDescription(descriptionBuild)

            return listWidget

    def run(self):
        print "DetachCommand.run():\t Detaching servos ", self.parameters['servo1'], \
                                                        self.parameters['servo2'], \
                                                        self.parameters['servo3'], \
                                                        self.parameters['servo4']
        pos = Global.robot.currentCoord()
        Global.robot.setPos(x=pos[1], y=pos[2], z=pos[3])  #This makes the robot attach at the current position it's at
        if self.parameters['servo1']: Global.robot.setServos(servo1=True)
        if self.parameters['servo2']: Global.robot.setServos(servo2=True)
        if self.parameters['servo3']: Global.robot.setServos(servo3=True)
        if self.parameters['servo4']: Global.robot.setServos(servo4=True)







