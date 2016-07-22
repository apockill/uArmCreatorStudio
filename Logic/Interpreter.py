"""
This software was designed by Alexander Thiel
Github handle: https://github.com/apockill
Email: Alex.D.Thiel@Gmail.com


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
import math
import json
from time         import sleep
from copy         import deepcopy
from threading    import Thread
from Logic.Global import printf, FpsTimer, wait
from Logic        import Events, Commands
__author__ = "Alexander Thiel"



class Interpreter:
    """
    This is where the script is actually run. The most convenient method is to create a script with the GUI,
    then use self.loadScript(script) to actually get the script into the interpreter, then use startThread()
    to begin the script.

    Since an interpreter can run another interpreter inside of it, there is a
    """

    def __init__(self, environment, parentExitFunc):


        self.parentExiting = parentExitFunc
        self.env           = environment
        self.mainThread    = None    # The thread on which the script runs on. Is None while thread is not running.
        self.__exiting     = False   # When True, the script thread will attempt to close ASAP
        self.events        = []      # A list of events, and their corresponding commands

        # For self.getStatus()
        self.currRunning   = []  # A dictionary of what has been run so far in the loop {eventIndex:[commandIndex's]}

        # Namespace is all  the builtins and variables that the user creates during a session in the interpreter
        self.nameSpace     = None
        self.cleanNamespace()


    def loadScriptFromFile(self, filename):
        """
        This is a function that will load a script from a file, then run self.loadScript on the loaded file, and return
        the errors that occurred while loading the script.

        If the script could not be found or loaded, it will return an "Could not open script" in the errors array.

        The script will return a boolean, True if the script was loaded successfully, and false if there was an error.
        """
        try:
            script = json.load( open(filename))
        except IOError:
            printf("ERROR: Task file ", filename, "not found!")
            self.env.updateSettings("lastOpenedFile", None)
            return False

        return self.initializeScript(script)

    def initializeScript(self, script):
        """
        Initializes each event in the script, Initializes each command in the script,
        places all the commands into the appropriate events,
        and returns all errors that occured during the build process.

        "script" is an already loaded script, of the format that EventList.getSaveData() would return.
        It looks something like [{Event here, commandList here}, {event here, commandList here}]
        To load a script from file, simply use Interpreter.loadScriptFromFile(filename)

        :param      env: Environment object
        :param      script: a loaded script from a .task file
        :return:    any errors that commands returned during instantiation
        """
        script = deepcopy(script)

        errors = {}  # Errors are returned from

        # Create each event
        for _, eventSave in enumerate(script):
            # Get the "Logic" code for this event, stored in Events.py
            eventType = getattr(Events, eventSave['typeLogic'])
            event     = eventType(self.env, self, parameters=eventSave['parameters'])
            self.addEvent(event)

            # Add any commands related to the creation of this event
            for error in event.errors:
                    if error not in errors: errors[error] = []
                    errors[error].append(eventSave['typeLogic'])


            # Create the commandList for this event
            for _, commandSave in enumerate(eventSave['commandList']):
                # Get the "Logic" code command, stored in Commands.py
                commandType = getattr(Commands, commandSave['typeLogic'])
                command     = commandType(self.env, self, commandSave['parameters'])
                event.addCommand(command)

                for error in command.errors:
                    if error not in errors: errors[error] = []
                    errors[error].append(commandSave['typeLogic'])


        # Get rid of repeat errors
        # errors = set(errors)
        printf(len(errors), " errors occured while initializing the script.")
        return errors


    # Generic Functions for API and GUI to use
    def startThread(self, threaded=True):
        # Start the program thread

        if self.mainThread is None:
            if self.parentExiting is None:
                self.cleanNamespace()
                robot  = self.env.getRobot()

                # Make sure vision and robot are not in exiting mode
                self.setExiting(False)

                robot.setActiveServos(all=True)
                robot.setSpeed(10)
                self.currRunning = {}

            if threaded:
                self.mainThread  = Thread(target=lambda: self.__programThread())
                self.mainThread.start()
            else:
                self.__programThread()
        else:
            printf("ERROR: Tried to run programThread, but there was already one running!")

    def addEvent(self, event):
        self.events.append(event)


    # Status functions
    def threadRunning(self):
        return self.mainThread is not None

    def getStatus(self):
        # Returns an index of the (event, command) that is currently being run

        if not self.threadRunning():
            return False

        currRunning = self.currRunning

        return currRunning

    def isExiting(self):
        # Commands that have the potential to take a long time (wait, pickup, that sort of thing) will use this to check
        # if they should exit immediately
        if self.parentExiting is not None and self.parentExiting():
            self.setExiting(True)

        return self.__exiting

    def setExiting(self, value):
        self.env.getRobot().setExiting(value)
        self.env.getVision().setExiting(value)
        self.__exiting = value


    # The following functions should never be called by user - only for Commands/Events to interact with Interpreter
    def cleanNamespace(self):
        """
        This function resets the self.variables namespace, and creates a variable called self.execBuiltins which
        holds the python builtin functions that are allowed in the Script command. It also adds several things
        as builtins.

        Extra Builtins
            - robot
            - vision
            - settings
            - resources
            - vStream


        Excluded Builtins
            - setattr
            - dir
            - next
            - id
            - object
            - staticmethod
            - eval
            - open
            - exec
            - format
            - getattr
            - memoryview
            - compile
            - classmethod
            - repr
            - property
            - __import__
            - hasattr
            - help
            - input

        """

        # Reset self.__variables with the default values/functions #
        safeList = ['acos', 'asin', 'atan', 'atan2', 'ceil', 'cos', 'cosh', 'degrees',
                    'e', 'exp', 'fabs', 'floor', 'fmod', 'frexp', 'hypot', 'ldexp', 'log', 'log10',
                    'modf', 'pi', 'pow', 'radians', 'sin', 'sinh', 'sqrt', 'tan', 'tanh']

        variables = dict([(k, getattr(math, k)) for k in safeList])
        variables['math'] = math


        robot         = self.env.getRobot()
        vision        = self.env.getVision()
        settings      = self.env.getSettings()
        resources     = self.env.getObjectManager()
        vStream       = self.env.getVStream()
        newSleep      = lambda time: wait(time, self.isExiting)
        isExiting     = self.isExiting
        # Add Python builtins, and also the extra ones (above)
        execBuiltins = {      "abs":       abs,       "dict":       dict,
                              "all":       all,        "hex":        hex,      "slice":      slice,
                              "any":       any,     "divmod":     divmod,     "sorted":     sorted,
                            "ascii":     ascii,  "enumerate":  enumerate,      "range":      range,
                              "bin":       bin,        "int":        int,        "str":        str,
                             "bool":      bool, "isinstance": isinstance,        "ord":        ord,
                        "bytearray": bytearray,     "filter":     filter, "issubclass": issubclass,
                            "bytes":     bytes,      "float":      float,       "iter":       iter,
                         "callable":  callable,        "len":        len,       "type":       type,
                              "chr":       chr,  "frozenset":  frozenset,       "list":       list,
                           "locals":    locals,        "zip":        zip,       "vars":       vars,
                          "globals":   globals,        "map":        map,   "reversed":   reversed,
                          "complex":   complex,        "max":        max,      "round":      round,
                          "delattr":   delattr,       "hash":       hash,        "set":        set,
                              "min":       min,        "oct":        oct,        "sum":        sum,
                              "pow":       pow,      "super":      super,      "print":     printf,
                            "tuple":     tuple,      "robot":      robot,  "resources":  resources,
                           "vision":    vision,   "settings":   settings,    "vStream":    vStream,
                            "sleep":  newSleep, "isStopping":  isExiting}

        execBuiltins = {"__builtins__": execBuiltins, "variables": variables, "__author__": "Alexander Thiel"}
        self.nameSpace = execBuiltins

    def evaluateExpression(self, expression):

        # Returns value, success. Value is the output of the expression, and 'success' is whether or not it crashed.
        # If it crashes, it returns None, but some expressions might return none, so 'success' variable is still needed.
        # Side note: I would have to do ~66,000 eval operations to lag the program by one second.

        answer = None

        try:
            answer = eval(expression, self.nameSpace)
        except Exception as e:
            printf("EVAL ERROR: ", type(e).__name__, " ", e)


        if answer is None:
            return None, False

        return answer, True

    def evaluateScript(self, script):

        # # Build the script inside of a function, so users can "return" out of it
        # script = '\n\t' + script.replace('\n', '\n\t')
        # script        = "def script():\n" + \
        #                     script + "\n" + \
        #                 "scriptReturn = script()"

        #  self.__variables["scriptReturn"] = None

        try:
            # self.execBuiltins["globals"] = self.__variables
            exec(script, self.nameSpace)

            # if self.__variables["scriptReturn"] is not None:
            #     print("Returned ", self.__variables["scriptReturn"])
        except Exception as e:
            printf("EXEC ERROR: ", type(e).__name__, ": ", e)
            return False

        return True

    def createChildInterpreter(self, filename, parentExitFunc):
        """
            This function is special, in the sense that it creates another interpreter that runs inside of this one,
            with a specified filename or script, and starts it immediately.
        """
        if parentExitFunc(): return
        print(parentExitFunc)
        # print("Starting child interpreter")
        child = Interpreter(self.env, parentExitFunc)
        errors = child.loadScriptFromFile(filename)
        if len(errors):
            print("Errors while initializing child: ", errors)
        child.startThread(threaded=False)


    # The following functions are *only* for interpreter to use within itself.
    def __programThread(self):
        printf("\n\n\n ##### STARTING PROGRAM #####\n")


        fpsTimer = FpsTimer(fps=30)

        # Main program loop - where events are checked and run
        while not self.isExiting():
            # Maintain constant FPS using an FPSTimer
            fpsTimer.wait()
            if not fpsTimer.ready(): continue


            # currRunning keeps track of what was run, so the GUI can draw it
            self.currRunning = {}


            # Check every event, in order of the list
            for index, event in enumerate(self.events):
                if self.isExiting(): break
                if not event.isActive(): continue

                # If the event has been activated, run the commandList
                self.__interpretEvent(event)


        # Check if a DestroyEvent exists, if so, run it's commandList
        destroyEvent = list(filter(lambda event: type(event) == Events.DestroyEvent, self.events))

        if len(destroyEvent):
            # Make sure the robot, vision, and interpreter can respond before running the destroy event
            self.setExiting(False)
            self.__interpretEvent(destroyEvent[0])

            # Set the robot, vision, and interpreter back to non-responsive mode after running the destroy event
            self.setExiting(True)

        self.mainThread = None
        self.events     = []
        self.setExiting(False)

    def __interpretEvent(self, event):
        """
        This will run through every command in an events commandList, and account for Conditionals and code blocks.

        """

        eventIndex    = self.events.index(event)
        commandList   = event.commandList
        index         = 0  # The current command that is being considered for running

        # Keep track of what commands are run in this event
        self.currRunning[eventIndex] = []


        # Check each command, run the ones that should be run
        while index < len(event.commandList):
            if self.isExiting(): break


            # Run the command
            command    = commandList[index]
            self.currRunning[eventIndex].append(index)
            evaluation = command.run()

            if self.isExiting(): break  # This speeds up ending recursed Interpreters

            # If the command returned an "Exit event" command, then exit the event evaluation
            if evaluation == "Kill":
                self.setExiting(True)
                break
            if evaluation == "Exit": break


            # If its false, skip to the next indent of the same indentation, or an "Else" command
            if evaluation is False:
                index = self.__getNextIndex(index, commandList)
            else:
                # If an else command is the next block, decide whether or not to skip it
                if index + 1 < len(commandList) and type(commandList[index + 1]) is Commands.ElseCommand:
                    # If the evaluation was true, then DON'T run the else command

                    index = self.__getNextIndex(index + 1, commandList)


            index += 1

    def __getNextIndex(self, index, commandList):
        # If its false, skip to the next indent of the same indentation, or an "Else" command


        skipToIndent = 0
        nextIndent   = 0
        for i in range(index + 1, len(commandList)):
            if type(commandList[i]) is Commands.StartBlockCommand: nextIndent += 1

            if nextIndent == skipToIndent:
                index = i - 1
                break

            # If there are no commands
            if i == len(commandList) - 1:
                index = i
                break


            if type(commandList[i]) is Commands.EndBlockCommand:   nextIndent -= 1



        return index
