
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
    def __init__(self):
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


class StepEvent(Event):
    def __init__(self):
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


class TipEvent(Event):
    """
    This event activates when the sensor on the tip of the robots sucker is pressed/triggered
    """
    def __init__(self):
        Event.__init__(self)

    def getWidget(self):
        listWidget = EventWidget()
        listWidget.setIcon(Icons.tip_event)
        listWidget.setTitle('Tip')
        listWidget.setTip('Activates when the sensor on the tip of the arm is pressed')

        return listWidget

    def isActive(self):
        #Global.robot.getTipSensor()
        #Since this is a "step" event, it will run each time the events are checked
        return True

