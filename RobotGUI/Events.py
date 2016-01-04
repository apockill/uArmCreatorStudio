from PyQt4 import QtGui, QtCore
import Icons
import Global




class EventWidget(QtGui.QWidget):
    """
    This is the widget that appears on the EventList.
    It's supposed to be prettier than the normal list items.
    """
    def __init__(self, parent = None):
        super(EventWidget, self).__init__(parent)
        self.title       = QtGui.QLabel()
        self.icon        = QtGui.QLabel("No icon found.")
        self.initUI()

    def initUI(self):
        font = QtGui.QFont()
        font.setBold(True)
        self.title.setFont(font)

        mainHLayout = QtGui.QHBoxLayout()
        mainHLayout.addWidget(self.icon)
        mainHLayout.addWidget(self.title, QtCore.Qt.AlignLeft)

        self.setLayout(mainHLayout)

    def setTitle(self, text):
        self.title.setText(text)

    def setIcon(self, icon):
        self.icon.setPixmap(QtGui.QPixmap(icon))

    def setTip(self, tip):
        self.setToolTip(tip)


class EventPromptWindow(QtGui.QDialog):
    def __init__(self):
        super(EventPromptWindow, self).__init__()
        self.accepted         = False
        self.chosenEvent      = None  #What event the user chose to add (changed in btnClicked() function)
        self.chosenParameters = None
        self.initUI()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.exec_()  #Open self, and prevent anyone clicking on other windows


    def initUI(self):
        self.initButtons()
        self.initButtonMenus()

        #Create grid layout
        grid = QtGui.QGridLayout()
            #Left column
        grid.addWidget(      self.initBtn, 0, 0, QtCore.Qt.AlignLeft)
        grid.addWidget(      self.stepBtn, 1, 0, QtCore.Qt.AlignLeft)
        grid.addWidget(   self.destroyBtn, 2, 0, QtCore.Qt.AlignLeft)
            #Right column
        grid.addWidget(  self.keyboardBtn, 0, 1, QtCore.Qt.AlignLeft)
        grid.addWidget( self.intersectBtn, 1, 1, QtCore.Qt.AlignLeft)
        grid.addWidget(       self.tipBtn, 2, 1, QtCore.Qt.AlignLeft)


        #Set up Cancel button in it's own layout:
        cancelLayout = QtGui.QHBoxLayout()
        cancelLayout.addWidget(self.cancelBtn)


        #Create main layout
        mainVLayout = QtGui.QVBoxLayout()
        mainVLayout.addLayout(grid)
        mainVLayout.addLayout(cancelLayout, QtCore.Qt.AlignHCenter)


        #Finalize everything
        self.setLayout(mainVLayout)
        self.setFixedSize(self.sizeHint())  #Make the window a fixed size
        self.setWindowTitle('Add an Event')


    def initButtons(self):
        buttonWidth = 115
        #Create the cancel button
        self.cancelBtn    = QtGui.QPushButton('Cancel')
        self.cancelBtn    .setFixedWidth(buttonWidth * 1.5)
        self.cancelBtn    .setFixedHeight(25)
        self.cancelBtn    .setIcon(QtGui.QIcon(Icons.cancel))


        #Create Event Buttons
        self.initBtn      = self.getNewButton('Initialization', Icons.creation_event)
        self.destroyBtn   = self.getNewButton('End of Program', Icons.destroy_event)
        self.keyboardBtn  = self.getNewButton(      'Keyboard', Icons.keyboard_event)
        self.stepBtn      = self.getNewButton(          'Step', Icons.step_event)
        self.tipBtn       = self.getNewButton(    'Tip Sensor', Icons.tip_event)
        self.intersectBtn = self.getNewButton(     'Intersect', Icons.intersect_event)


        #CONNECT BUTTONS THAT DON'T HAVE MENUS
        self.initBtn      .clicked.connect(lambda: self.btnClicked(InitEvent))
        self.destroyBtn   .clicked.connect(lambda: self.btnClicked(DestroyEvent))
        self.stepBtn      .clicked.connect(lambda: self.btnClicked(StepEvent))
        self.tipBtn       .clicked.connect(lambda: self.btnClicked(TipEvent))
        self.cancelBtn    .clicked.connect(self.cancelClicked)

    def initButtonMenus(self):
        """
        initBtn         NO menu
        keyboardBtn     Has menu
        stepBtn         Has menu
        intersectBtn    Has menu
        cancelBtn       NO menu
        :return:
        """
        #Set up Menus for buttons that have menus:

        #KEYBOARD MENU
        keyboardMnu = QtGui.QMenu()
        keyboardMnu.addAction(   '<Up>', lambda: self.btnClicked('Up Clicked'))
        keyboardMnu.addAction( '<Down>', lambda: self.btnClicked('Down Clicked'))
        keyboardMnu.addAction( '<Left>', lambda: self.btnClicked('Left Clicked'))
        keyboardMnu.addAction('<Right>', lambda: self.btnClicked('Right Clicked'))

            #Create Letters Sub Menu
        self.lettersSubMnu = QtGui.QMenu("Letters")  #Has to be self or else doesn't work. Don't know why...
        alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I','J', 'K', 'L', 'M',
                    'N', 'O', 'P', 'Q','R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
        for letter in alphabet:
            #About the lambda letter=letter:. I don't know why it fixes the problem, but it does. Here's a better
            #Explanation: http://stackoverflow.com/questions/4578861/connecting-slots-and-signals-in-pyqt4-in-a-loop
            self.lettersSubMnu.addAction(letter, lambda letter=letter: self.btnClicked(KeypressEvent, parameters={"checkKey": letter}))

            #Create Digits Sub Menu
        self.digitsSubMnu = QtGui.QMenu("Digits")  #Has to be self or else doesn't work. Don't know why...
        digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        for index, digit in enumerate(digits):
            self.digitsSubMnu.addAction(digit, lambda digit=digit: self.btnClicked(digit))

            #Add Sub Menus
        keyboardMnu.addMenu(self.lettersSubMnu)
        keyboardMnu.addMenu(self.digitsSubMnu)
        self.keyboardBtn.setMenu(keyboardMnu)



        #INTERSECT MENU
        intersectMnu = QtGui.QMenu()
        intersectMnu.addAction('Intersect +X Boundary', lambda: self.btnClicked("+X"))
        intersectMnu.addAction('Intersect -X Boundary', lambda: self.btnClicked("-X"))
        intersectMnu.addAction('Intersect  X Boundary', lambda: self.btnClicked("X"))
        intersectMnu.addAction('Intersect +Y Boundary', lambda: self.btnClicked("+Y"))
        intersectMnu.addAction('Intersect -Y Boundary', lambda: self.btnClicked("-Y"))
        intersectMnu.addAction('Intersect  Y Boundary', lambda: self.btnClicked("Y"))
        self.intersectBtn.setMenu(intersectMnu)


    def btnClicked(self, eventType, **kwargs):
        print "EventWindow.buttonSelected():\t Event Type ", eventType, "selected"
        self.chosenEvent      = eventType
        self.chosenParameters = kwargs.get("parameters", None)
        self.accepted = True
        self.close()

    def cancelClicked(self, event):
        self.close()

    def getNewButton(self, buttonText, icon):
        buttonWidth = 115

        newButton = QtGui.QPushButton(buttonText)
        newButton.setStyleSheet("Text-align:left")
        newButton.setFixedWidth(buttonWidth)
        newButton.setIcon(QtGui.QIcon(icon))
        return newButton




########## EVENTS ##########
class Event(object):
    def __init__(self):
        """
        self.parameters is used for events like KeyPressEvent where one class can handle multiple types of events
        such as A KeyPress or ZKeypress. THe self.parameters makes sure that you can differentiate between events
        when adding new ones, so you can make sure there aren't two 'A Keypress' events.
        """
        self.commandList = None
        self.parameters = {}

    def runCommands(self):
        commandsOrdered = self.commandList.getCommandsOrdered()
        print commandsOrdered
        for command in commandsOrdered:
            command.run()


class InitEvent(Event):
    def __init__(self, parameters):
        super(InitEvent, self).__init__()
        self.hasBeenRun = False

    def getWidget(self):
        listWidget = EventWidget()
        listWidget.setIcon(Icons.creation_event)
        listWidget.setTitle('Initialization')
        listWidget.setTip('Activates once each time the program is run')
        return listWidget

    def isActive(self):
        #Returns true or false if this event should be activated

        if self.hasBeenRun:
            return False
        else:
            return True

    def runCommands(self):
        #Intercept the parent class events so that you can set self.hasBeenRun to true
        Event.runCommands(self)
        self.hasBeenRun = True


class DestroyEvent(Event):
    def __init__(self, parameters):
        super(DestroyEvent, self).__init__()

    def getWidget(self):
        listWidget = EventWidget()
        listWidget.setIcon(Icons.destroy_event)
        listWidget.setTitle('End of Program')
        listWidget.setTip('Activates once, when the program is ended')
        return listWidget

    def isActive(self):
        #This event always returns false, because it is run DIRECTLY by the ControlPanel.programThread()
        #programThread() will check if the event exists. If it does, it will run all of its commands.
        #Otherwise, this event will never run while the program is running.

        return False


class StepEvent(Event):
    def __init__(self, parameters):
        Event.__init__(self)

    def getWidget(self):
        listWidget = EventWidget()
        listWidget.setIcon(Icons.step_event)
        listWidget.setTitle('Step')
        listWidget.setTip('Activates every time the events are refreshed')

        return listWidget

    def isActive(self):
        #Since this is a "step" event, it will run each time the events are checked
        return True


class KeypressEvent(Event):
    def __init__(self, parameters):
        Event.__init__(self)

        self.parameters = parameters

    def getWidget(self):
        listWidget = EventWidget()
        listWidget.setIcon(Icons.keyboard_event)
        listWidget.setTitle('Keypress ' + self.parameters["checkKey"])
        listWidget.setTip('Activates when the letter ' + self.parameters["checkKey"] + " is pressed")
        return listWidget

    def isActive(self):
        if ord(self.parameters["checkKey"]) in Global.keysPressed:
            return True
        else:
            return False
        # if len(Global.keysPressed) > 0:
        #     return True
        # else:
        #     return False


class MotionEvent(Event):
    """
    This event activates when the sensor on the tip of the robots sucker is pressed/triggered
    """
    def __init__(self):
        Event.__init__(self)

    def getWidget(self):
        listWidget = EventWidget()
        listWidget.setIcon(Icons.tip_event)
        listWidget.setTitle('Motion Detected')
        listWidget.setTip('Activates when there is motion detected')

        return listWidget

    def isActive(self):
        print Global.robot.getTipSensor()
        #Since this is a "step" event, it will run each time the events are checked
        return True

class TipEvent(Event):
    """
    This event activates when the sensor on the tip of the robots sucker is pressed/triggered
    """
    def __init__(self, parameters):
        Event.__init__(self)

    def getWidget(self):
        listWidget = EventWidget()
        listWidget.setIcon(Icons.tip_event)
        listWidget.setTitle('Tip')
        listWidget.setTip('Activates when the sensor on the tip of the arm is pressed')

        return listWidget

    def isActive(self):
        return Global.robot.getTipSensor()








