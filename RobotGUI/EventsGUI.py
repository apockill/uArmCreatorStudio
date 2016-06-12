from PyQt5           import QtGui, QtCore, QtWidgets
from RobotGUI        import Icons
from RobotGUI.Logic import Global
from RobotGUI.Logic.Global import printf


class EventWidget(QtWidgets.QWidget):
    """
    This is the widget that appears on the EventList.
    It's supposed to be prettier than the normal list items.
    """
    def __init__(self, parent):
        super(EventWidget, self).__init__(parent)
        self.title       = QtWidgets.QLabel()
        self.icon        = QtWidgets.QLabel("No icon found.")
        self.initUI()


    def initUI(self):
        font = QtGui.QFont()
        font.setBold(True)
        self.title.setFont(font)

        mainHLayout = QtWidgets.QHBoxLayout()
        mainHLayout.addWidget(self.icon)
        mainHLayout.addWidget(self.title, QtCore.Qt.AlignLeft)

        self.setLayout(mainHLayout)

    def setTitle(self, text):
        self.title.setText(text)

    def setIcon(self, icon):
        self.icon.setPixmap(QtGui.QPixmap(icon))

    def setTip(self, tip):
        self.setToolTip(tip)


class EventPromptWindow(QtWidgets.QDialog):
    def __init__(self, parent):
        super(EventPromptWindow, self).__init__(parent)
        self.accepted         = False
        self.chosenEvent      = None  #What event the user chose to add (changed in btnClicked() function)
        self.chosenParameters = None

        self.buttonWidth = 130
        self.initButtons()
        self.initButtonMenus()
        self.initUI()

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)  # TODO: Investigate adding this to command windows
        self.exec_()  #Open self, and prevent anyone clicking on other windows


    def initUI(self):


        # Create grid layout
        grid = QtWidgets.QGridLayout()

        # Left column
        grid.addWidget(      self.initBtn, 0, 0, QtCore.Qt.AlignLeft)
        grid.addWidget(      self.stepBtn, 1, 0, QtCore.Qt.AlignLeft)
        grid.addWidget(   self.destroyBtn, 2, 0, QtCore.Qt.AlignLeft)

        # Right column
        grid.addWidget(  self.keyboardBtn, 0, 1, QtCore.Qt.AlignLeft)
        # grid.addWidget( self.intersectBtn, 1, 1, QtCore.Qt.AlignLeft)
        grid.addWidget(       self.tipBtn, 1, 1, QtCore.Qt.AlignLeft)
        grid.addWidget(    self.motionBtn, 2, 1, QtCore.Qt.AlignLeft)

        # Set up Cancel button in it's own layout:
        cancelLayout = QtWidgets.QHBoxLayout()
        cancelLayout.addWidget(self.cancelBtn)


        # Create main layout
        mainVLayout = QtWidgets.QVBoxLayout()
        mainVLayout.addLayout(grid)
        mainVLayout.addLayout(cancelLayout, QtCore.Qt.AlignHCenter)


        # Finalize everything
        self.setLayout(mainVLayout)
        self.setFixedSize(self.sizeHint())  #Make the window a fixed size
        self.setWindowTitle('Add an Event')

    def initButtons(self):

        # Create the cancel button
        self.cancelBtn    = QtWidgets.QPushButton('Cancel')
        self.cancelBtn    .setFixedWidth(self.buttonWidth * 1.5)
        self.cancelBtn    .setFixedHeight(25)
        self.cancelBtn    .setIcon(QtGui.QIcon(Icons.cancel))


        # Create Event Buttons
        self.initBtn      = self.getNewButton( 'Initialization', InitEventGUI.icon)
        self.destroyBtn   = self.getNewButton( 'End of Program', DestroyEventGUI.icon)
        self.keyboardBtn  = self.getNewButton(       'Keyboard', KeypressEventGUI.icon)
        self.stepBtn      = self.getNewButton(           'Step', StepEventGUI.icon)
        self.tipBtn       = self.getNewButton(     'Tip Sensor', TipEventGUI.icon)
        self.intersectBtn = self.getNewButton(      'Intersect', Icons.intersect_event)
        self.motionBtn    = self.getNewButton(         'Motion', MotionEventGUI.icon)


        # CONNECT BUTTONS THAT DON'T HAVE MENUS
        self.initBtn      .clicked.connect(lambda: self.btnClicked(InitEventGUI))
        self.destroyBtn   .clicked.connect(lambda: self.btnClicked(DestroyEventGUI))
        self.stepBtn      .clicked.connect(lambda: self.btnClicked(StepEventGUI))
        self.tipBtn       .clicked.connect(lambda: self.btnClicked(TipEventGUI))
        self.motionBtn    .clicked.connect(lambda: self.btnClicked(MotionEventGUI))
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
        # Set up Menus for buttons that have menus:

        ######################     KEYBOARD MENU     ######################
        keyboardMnu = QtWidgets.QMenu()

        # Create Letters Sub Menu
        self.lettersSubMnu = QtWidgets.QMenu("Letters") # Has to be self or something glitches with garbage collection.
        alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I','J', 'K', 'L', 'M',
                    'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
        for letter in alphabet:
            # About the lambda letter=letter:. I don't know why it fixes the problem, but it does. Here's a better
            # Explanation: http://stackoverflow.com/questions/4578861/connecting-slots-and-signals-in-pyqt4-in-a-loop
            self.lettersSubMnu.addAction(letter, lambda letter=letter: self.btnClicked(KeypressEventGUI, params={"checkKey": letter}))

        # Create Digits Sub Menu
        self.digitsSubMnu = QtWidgets.QMenu("Digits")
        digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        for index, digit in enumerate(digits):
            self.digitsSubMnu.addAction(digit, lambda digit=digit: self.btnClicked(KeypressEventGUI, params={"checkKey": digit}))

        # Add Sub Menus
        keyboardMnu.addMenu(self.lettersSubMnu)
        keyboardMnu.addMenu(self.digitsSubMnu)
        self.keyboardBtn.setMenu(keyboardMnu)


        ######################     MOTION MENU     ######################
        newMotionBtn = lambda params: self.btnClicked(MotionEventGUI, params=params)
        motionMnu = QtWidgets.QMenu()
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
        intersectMnu = QtWidgets.QMenu()
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

        newButton = QtWidgets.QPushButton(buttonText)
        newButton.setStyleSheet("Text-align:left")
        newButton.setFixedWidth(self.buttonWidth)
        newButton.setIcon(QtGui.QIcon(icon))
        return newButton


class EventGUI:
    def __init__(self):
        """
        self.parameters is used for events like KeyPressEvent where one class can handle multiple types of events
        such as A KeyPress or ZKeypress. THe self.parameters makes sure that you can differentiate between events
        when adding new ones, so you can make sure there aren't two 'A Keypress' events.
        """
        self.commandList = None
        self.parameters = {}

    def dressWidget(self, widget):
        widget.setIcon(self.icon)
        widget.setTitle(self.title)
        widget.setTip(self.tooltip)
        return widget

    # def runCommands(self, shared):
    #     commandsOrdered = self.commandList.getCommandsOrdered()
    #
    #     for command in commandsOrdered:
    #         command.run(shared)



########## EVENTS ##########

class InitEventGUI(EventGUI):
    title     = 'Initialization'
    tooltip   = 'Activates once each time the program is run'
    icon      = Icons.creation_event
    logicPair = 'InitEvent'

    def __init__(self, parameters):
        super(InitEventGUI, self).__init__()


class DestroyEventGUI(EventGUI):
    title     = 'End of Program'
    tooltip   = 'Activates once, when the program is ended'
    icon      = Icons.destroy_event
    logicPair = 'DestroyEvent'

    def __init__(self, parameters):
        super(DestroyEventGUI, self).__init__()


class StepEventGUI(EventGUI):
    title     = 'Step'
    tooltip   = 'Activates every time the events are refreshed'
    icon      = Icons.step_event
    logicPair = 'StepEvent'

    def __init__(self, parameters):
        super(StepEventGUI, self).__init__()


class KeypressEventGUI(EventGUI):
    icon      = Icons.keyboard_event
    logicPair = 'KeypressEvent'

    def __init__(self, parameters):
        super(KeypressEventGUI, self).__init__()
        self.parameters = parameters

    def dressWidget(self, widget):
        widget.setIcon(self.icon)
        widget.setTitle('Keypress ' + self.parameters["checkKey"])
        widget.setTip('Activates when the letter ' + self.parameters["checkKey"] + " is pressed")
        return widget


class MotionEventGUI(EventGUI):
    """
    This event activates when the sensor on the tip of the robots sucker is pressed/triggered
    """

    icon = Icons.motion_event
    logicPair = 'MotionEvent'

    def __init__(self, parameters):
        super(MotionEventGUI, self).__init__()
        self.parameters = parameters

    def dressWidget(self, widget):
        widget.setIcon(self.icon)
        widget.setTitle('Motion ' + self.parameters["low"] + "-" + self.parameters["high"])
        widget.setTip('Activates when there is motion detected')

        return widget


class TipEventGUI(EventGUI):
    """
    This event activates when the sensor on the tip of the robots sucker is pressed/triggered
    """

    title     = 'Tip'
    tooltip   = 'Activates when the sensor on the tip of the arm is pressed'
    icon      = Icons.tip_event
    logicPair = 'TipEvent'

    def __init__(self, parameters):
        super(TipEventGUI, self).__init__()









