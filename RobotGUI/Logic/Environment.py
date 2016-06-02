from copy                  import deepcopy
from threading             import Thread
from RobotGUI.Logic.Global import printf, FpsTimer
from RobotGUI.Logic.Robot  import Robot
from RobotGUI.Logic        import Video, Events, Commands

class Environment:
    """
    Environment holds the following thing and handles their shutdown:
        - vStream object
        - Vision object
        - Robot object
        - Interpreter objects

    This will also be a platform for storing "Heavy" objects that will be used in the program. ie, image recognition
    files, anything that can't be stored in plaintext in the scriptfile that won't change during the program should
    be here. It can load and save objects in a special uObject class that might have derivatives of types:
        uVisionObject       Might contain pictures, image maps, huge arrays with keypoints, who knows.
        uMotionPathObject   Might contain long lists of moves, speeds, or even mathematical functions for the bot to
                            follow.
        uScriptObject       Might contain a whole other script within it that would be able to run entirely within
                            the program and spawn its own environment and interpreter.

    All loading, adding replacing, and saving of objects should be done through this class.
    All objects will have a "getSaveData" implimented.
    """

    def __init__(self, settings):

        # Set up environment objects
        self.__vStream      = Video.VideoStream(None)       # Gets frames constantly
        self.__robot        = Robot(None)
        self.__settings     = settings
        self.__vision       = Video.Vision(self.__vStream)  # Performs computer vision tasks, using images from vStream


        self.__interpreter  = Interpreter(self)

        # This keeps track of objects that have been self.addObject()'d, so self.saveObjects() actually saves them.
        self.changedObjects = []


    # Handling Vision Objects
    def saveObjects(self, filename):
        # Any objects that have been "changed" will be saved. All other objects won't be touched.
        # This should lead to faster save times, since the user will probably save on a whim.

        # Checks if an interpreter is currently running before doing anything.
        pass

    def loadObjects(self, filename):
        # Load all objects into the environment

        # Checks if an interpreter is currently running before doing anything.
        pass

    def addObject(self, object):
        # Adds an object to the pool.

        # Checks if an interpreter is currently running before doing anything.

        # Checks if the object already exists, if so, it will replace the old one, and put itself in self.changedObjects

        pass


    def getInterpreter(self):
        # Returns an Interpreter() object with the script loaded and parsed.
        return self.__interpreter

    def getRobot(self):
        return self.__robot

    def getVStream(self):
        return self.__vStream

    def getVision(self):
        return self.__vision

    def getSettings(self):
        return self.__settings


    def close(self):
        # This will shut down the vStream, any running interpreters, the robot, etc.
        self.__interpreter.endThread()
        self.__vStream.endThread()
        pass



class Interpreter:
    def __init__(self, parent):
        self.env        = parent
        self.mainThread = None
        self.killApp    = True
        self.script     = None

        self.events     = []    # A list of events, and their corresponding commands

    # Functions for GUI to use
    def loadScript(self, script):
        # Creates each event, loads it with its appropriate commandList, and then adds that event to self.events
        self.script = deepcopy(script)

        for _, eventSave in enumerate(script):
            eventType = getattr(Events, eventSave['typeLogic'])
            event = eventType(parameters=eventSave['parameters'])

            for _, commandSave in enumerate(eventSave['commandList']):
                commandType = getattr(Commands, commandSave['typeLogic'])
                event.addCommand(commandType(commandSave['parameters']))

            self.addEvent(event)


    # Generic Functions for API and GUI to use
    def startThread(self):
        # Start the program thread
        if self.mainThread is None:
            self.killApp    = False
            self.mainThread = Thread(target=self.programThread)
            self.mainThread.start()
        else:
            printf("Interpreter.startThread(): ERROR: Tried to run programThread, but there was already one running!")

    def endThread(self):
        # Close the thread that is currently running at the first chance it gets. Return True or False

        printf("Interpreter.startThread(): Closing program thread.")

        self.killApp = True

        if self.mainThread is not None:
            self.mainThread.join(3000)

            if self.mainThread.is_alive():
                printf("Interpreter.startThread(): ERROR: Thread was told to close but did not")
                return False
            else:
                self.mainThread = None
                self.events = []
                return True



    def programThread(self):
        # This is where the script you create actually gets run.
        print("\n\n\n ##### STARTING PROGRAM #####\n")

        self.env.getRobot().setServos(servo1=True, servo2=True, servo3=True, servo4=True)
        self.env.getRobot().refresh()

        timer = FpsTimer(fps=10)

        while not self.killApp:
            timer.wait()
            if not timer.ready(): continue

            for event in self.events:
                if self.killApp: break

                if event.isActive(self.env):
                    print("Running event", event)

        pass


    def addEvent(self, event):
        self.events.append(event)


    def isRunning(self):
        """
        The interpreter will now check comprehensively every function you have, if it requires a camera, if it requires
        a robot, if it requires an object, and check if all of those things are ready (query the robot, check the
        vStream, check the objects saved in the Environment. If everything is ready, it will start a thread and begin
        running.
        :return:
        """
        return not self.killApp or self.mainThread is not None

    def getStatus(self):
        # Returns information about what event is being run, the index of the command being run, and the actual command.
        pass


    # def __parseScript(self, script):
    #     """
    #     Script is a variable that comes the same was as a savefile comes- a list of events and their parameters, with
    #     each event carrying a list of commands and their parameters.
    #     """
    #













    # def moveXYZ(self, shared):
    #     printf("MoveXYZCommand.run(): Moving robot to ",
    #            self.parameters['x'], " ",
    #            self.parameters['y'], " ",
    #            self.parameters['z'], " ")
    #     shared.getRobot().setPos(x=self.parameters['x'],
    #                              y=self.parameters['y'],
    #                              z=self.parameters['z'],
    #                              relative=self.parameters['rel'])
    #
    #     # if self.refCheck.isChecked():  shared.getRobot().refresh()

