

class Event:
    def __init__(self):
        self.parameters = {}


class InitEvent(Event):
    def __init__(self, parameters):
        super(InitEvent, self).__init__()
        self.hasBeenRun = False

    def isActive(self, shared):
        # Returns true or false if this event should be activated

        if self.hasBeenRun:
            return False
        else:
            self.hasBeenRun = True
            return True