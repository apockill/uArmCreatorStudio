from PyQt4 import QtGui, QtCore
from Global import printf
import Icons
import Global




class EventWidget(QtGui.QWidget):
    """
    This is the widget that appears on the EventList.
    It's supposed to be prettier than the normal list items.
    """
    def __init__(self, parent):
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
    def __init__(self, parent):
        super(EventPromptWindow, self).__init__(parent)
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
        grid.addWidget(    self.motionBtn, 2, 1, QtCore.Qt.AlignLeft)

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
        self.initBtn      = self.getNewButton( 'Initialization',     InitEvent.icon)
        self.destroyBtn   = self.getNewButton( 'End of Program',  DestroyEvent.icon)
        self.keyboardBtn  = self.getNewButton(       'Keyboard', KeypressEvent.icon)
        self.stepBtn      = self.getNewButton(           'Step',     StepEvent.icon)
        self.tipBtn       = self.getNewButton(     'Tip Sensor',      TipEvent.icon)
        self.intersectBtn = self.getNewButton(      'Intersect', Icons.intersect_event)
        self.motionBtn    = self.getNewButton('Motion Detected',   MotionEvent.icon)


        #CONNECT BUTTONS THAT DON'T HAVE MENUS
        self.initBtn      .clicked.connect(lambda: self.btnClicked(InitEvent))
        self.destroyBtn   .clicked.connect(lambda: self.btnClicked(DestroyEvent))
        self.stepBtn      .clicked.connect(lambda: self.btnClicked(StepEvent))
        self.tipBtn       .clicked.connect(lambda: self.btnClicked(TipEvent))
        self.motionBtn    .clicked.connect(lambda: self.btnClicked(MotionEvent))
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

        ######################     KEYBOARD MENU     ######################
        keyboardMnu = QtGui.QMenu()
            #Create Letters Sub Menu
        self.lettersSubMnu = QtGui.QMenu("Letters")  #Has to be self or something glitches with garbage collection....
        alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I','J', 'K', 'L', 'M',
                    'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
        for letter in alphabet:
            #About the lambda letter=letter:. I don't know why it fixes the problem, but it does. Here's a better
            #Explanation: http://stackoverflow.com/questions/4578861/connecting-slots-and-signals-in-pyqt4-in-a-loop
            self.lettersSubMnu.addAction(letter, lambda letter=letter: self.btnClicked(KeypressEvent, params={"checkKey": letter}))

            #Create Digits Sub Menu
        self.digitsSubMnu = QtGui.QMenu("Digits")
        digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        for index, digit in enumerate(digits):
            self.digitsSubMnu.addAction(digit, lambda digit=digit: self.btnClicked(KeypressEvent, params={"checkKey": digit}))

            #Add Sub Menus
        keyboardMnu.addMenu(self.lettersSubMnu)
        keyboardMnu.addMenu(self.digitsSubMnu)
        self.keyboardBtn.setMenu(keyboardMnu)


        ######################     MOTION MENU     ######################
        newMotionBtn = lambda params: self.btnClicked(MotionEvent, params=params)
        motionMnu = QtGui.QMenu()
        motionMnu.addAction(   'Low and Above', lambda: newMotionBtn({"low":  "Low", "high":  "Inf"}))
        motionMnu.addAction('Medium and Above', lambda: newMotionBtn({"low":  "Med", "high":  "Inf"}))
        motionMnu.addAction(  'High and Above', lambda: newMotionBtn({"low": "High", "high":  "Inf"}))
        motionMnu.addSeparator()
        motionMnu.addAction(   'Low and Below', lambda: newMotionBtn({"low": "None", "high":  "Low"}))
        motionMnu.addAction('Medium and Below', lambda: newMotionBtn({"low": "None", "high":  "Med"}))
        motionMnu.addAction(  'High and Below', lambda: newMotionBtn({"low": "None", "high": "High"}))
        motionMnu.addSeparator()
        motionMnu.addAction(   'Low to Medium', lambda: newMotionBtn({"low":  "Low", "high":  "Med"}))
        motionMnu.addAction(  'Medium to High', lambda: newMotionBtn({"low":  "Med", "high": "High"}))
        motionMnu.addAction(     'Low to High', lambda: newMotionBtn({"low":  "Low", "high": "High"}))

        self.motionBtn.setMenu(motionMnu)

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
        printf("EventWindow.buttonSelected(): Event Type ", eventType, "selected")
        self.chosenEvent      = eventType
        self.chosenParameters = kwargs.get("params", None)
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

    def runCommands(self, shared):
        commandsOrdered = self.commandList.getCommandsOrdered()

        for command in commandsOrdered:
            command.run(shared)


class InitEvent(Event):
    icon = Icons.creation_event
    def __init__(self, parameters):
        super(InitEvent, self).__init__()
        self.hasBeenRun = False

    def getWidget(self, widget):
        widget.setIcon(self.icon)
        widget.setTitle('Initialization')
        widget.setTip('Activates once each time the program is run')
        return widget

    def isActive(self, shared):
        #Returns true or false if this event should be activated

        if self.hasBeenRun:
            return False
        else:
            return True

    def runCommands(self, shared):
        #Intercept the parent class events so that you can set self.hasBeenRun to true
        Event.runCommands(self, shared)
        self.hasBeenRun = True


class DestroyEvent(Event):
    icon = Icons.destroy_event
    def __init__(self, parameters):
        super(DestroyEvent, self).__init__()

    def getWidget(self, widget):
        widget.setIcon(self.icon)
        widget.setTitle('End of Program')
        widget.setTip('Activates once, when the program is ended')
        return widget

    def isActive(self, shared):
        #This event always returns false, because it is run DIRECTLY by the ControlPanel.programThread()
        #programThread() will check if the event exists. If it does, it will run all of its commands.
        #Otherwise, this event will never run while the program is running.
        return False


class StepEvent(Event):
    icon = Icons.step_event
    def __init__(self, parameters):
        Event.__init__(self)

    def getWidget(self, widget):
        widget.setIcon(self.icon)
        widget.setTitle('Step')
        widget.setTip('Activates every time the events are refreshed')

        return widget

    def isActive(self, shared):
        #Since this is a "step" event, it will run each time the events are checked
        return True


class KeypressEvent(Event):
    icon = Icons.keyboard_event

    def __init__(self, parameters):
        Event.__init__(self)
        self.parameters = parameters

    def getWidget(self, widget):
        widget.setIcon(self.icon)
        widget.setTitle('Keypress ' + self.parameters["checkKey"])
        widget.setTip('Activates when the letter ' + self.parameters["checkKey"] + " is pressed")
        return widget

    def isActive(self, shared):
        if ord(self.parameters["checkKey"]) in Global.keysPressed:
            return True
        else:
            return False


class MotionEvent(Event):
    """
    This event activates when the sensor on the tip of the robots sucker is pressed/triggered
    """
    icon = Icons.motion_event

    def __init__(self, parameters):
        Event.__init__(self)
        self.parameters = parameters

        #Constants for movement. These are set the first time isActive() is run
        self.low  = None
        self.med  = None
        self.high = None


    def getWidget(self, widget):
        widget.setIcon(self.icon)
        widget.setTitle('Motion ' + self.parameters["low"] + "-" + self.parameters["high"])
        widget.setTip('Activates when there is motion detected')

        return widget

    def isActive(self, shared):
        if self.low is None:  #If this is the first time the event is being done, calculate the thresholds
            calib      = shared.settings["motionCalibrations"]
            stationary = calib["stationaryMovement"]
            active     = calib["activeMovement"]

            diff  = (active - stationary) / 3
            self.low  = diff
            self.med  = diff * 2
            self.high = diff * 3


        currentMotion = shared.vision.getMotion()

        active = True

        if self.parameters["low"] == "Low":
            active = active and self.low < currentMotion
        if self.parameters["low"] == "Med":
            active = active and self.med < currentMotion
        if self.parameters["low"] == "High":
            active = active and self.high < currentMotion

        if self.parameters["high"] == "Low":
            active = active and currentMotion < self.low
        if self.parameters["high"] == "Med":
            active = active and currentMotion < self.med
        if self.parameters["high"] == "High":
            active = active and currentMotion < self.high



        return active  #self.parameters["lowThreshold"] < motion < self.parameters["upperThreshold"]


class TipEvent(Event):
    """
    This event activates when the sensor on the tip of the robots sucker is pressed/triggered
    """
    icon = Icons.tip_event

    def __init__(self, parameters):
        Event.__init__(self)

    def getWidget(self, widget):
        widget.setIcon(self.icon)
        widget.setTitle('Tip')
        widget.setTip('Activates when the sensor on the tip of the arm is pressed')

        return widget

    def isActive(self, shared):
        return shared.robot.getTipSensor()








