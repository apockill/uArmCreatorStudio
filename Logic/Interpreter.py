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
import traceback
from Logic        import Global
from threading    import Thread
from Logic.Global import printf, FpsTimer, wait, getModuleClasses
from Logic        import Events, Commands
__author__ = "Alexander Thiel"




class Interpreter:
    """
    This is where the script is actually run. The most convenient method is to create a script with the GUI,
    then use self.initializeScript(script) to actually get the script into the interpreter, then use startThread()
    to begin the script. You can also do startThread(threaded=False).
    """

    def __init__(self, environment, nameSpace=None):
        """
        :param environment: Environment class, from Environment.py
        """

        self.env        = environment
        self.mainThread = None    # The thread on which the script runs on. Is None while thread is not running.
        self.__exiting  = False   # When True, the script thread will attempt to close ASAP
        self.events     = []      # A list of events, and their corresponding commands


        # A dictionary of what event and command is currently running, returned in self.getStatus()
        self.currRunning = {"event": -1, "command": -1}


        # Namespace is all  the builtins and variables that the user creates during a session in the interpreter
        self.nameSpace = nameSpace
        if self.nameSpace is None:
            self.cleanNamespace()
        else:
            # Make sure if the nameSpace was passed, the "interpreter" val works
            self.nameSpace["interpreter"] = self


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

        errors = {}  # Keep track of missing components for commands that are initialized

        # Create each event
        for _, eventSave in enumerate(script):
            # Get the "Logic" code for this event, stored in Events.py
            eventType = eventClasses[eventSave['type']]
            event     = eventType(self.env, self, parameters=eventSave['parameters'])
            self.addEvent(event)

            # Record any errors related to the creation of this event
            for error in event.errors:
                    if error not in errors: errors[error] = []
                    errors[error].append(eventSave['type'])


            # Create the commandList for this event
            for _, commandSave in enumerate(eventSave['commandList']):
                # Get the "Logic" code for this command, stored in Commands.py
                commandType = commandClasses[commandSave['type']]
                command     = commandType(self.env, self, parameters=commandSave['parameters'])
                event.addCommand(command)

                # Record any errors related to the creation of this command
                for error in command.errors:
                    if error not in errors: errors[error] = []
                    errors[error].append(commandSave['type'])


        # Get rid of duplicates in the errors
        for error in errors:
            errors[error] = list(set(errors[error]))

        printf("Interpreter| ", len(errors), " errors occured while initializing the script.")
        return errors



    # Generic Functions for API and GUI to use
    def startThread(self, threaded=True):
        # Start the program thread

        if self.mainThread is None:
            self.currRunning = {"event": -1, "command": -1}


            if threaded:
                global exitErrors
                exitErrors = None
                self.mainThread  = Thread(target=self.__programThread)
                self.mainThread.setDaemon(True)
                self.mainThread.start()
            else:
                self.__programThread()
        else:
            printf("Interpreter| ERROR: Tried to run programThread, but there was already one running!")

    def addEvent(self, event):
        self.events.append(event)


    # Status functions
    def threadRunning(self):
        return self.mainThread is not None

    def getStatus(self):
        # Returns an index of the (event, command) that is currently being run
        return self.currRunning.copy()

    def getExitErrors(self):
        # If the interpreter exited itself without being told by the program or user, it will have an exitError
        global exitErrors
        return exitErrors

    def isExiting(self):
        global exitingFlag
        return exitingFlag

    def setExiting(self, value):
        printf("Interpreter| Setting Interpreter to Exiting mode.")
        global exitingFlag

        self.env.getRobot().setExiting(value)
        self.env.getVision().setExiting(value)


        exitingFlag = value


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
            - repr
            - property
            - hasattr
            - help
            - input

        """

        # Reset self.__variables with the default values/functions #
        safeList = ['acos', 'asin', 'atan',   'atan2', 'ceil',   'cos',  'cosh', 'degrees', 'log10',
                       'e',  'exp', 'fabs',   'floor', 'fmod', 'frexp', 'hypot',   'ldexp',   'log',
                    'modf',   'pi',  'pow', 'radians',  'sin',  'sinh',  'sqrt',     'tan',  'tanh']


        variables = dict([(k, getattr(math, k)) for k in safeList])
        variables['math'] = math

        customPrint   = lambda *args: printf("Output| ", *args)
        robot         = self.env.getRobot()
        vision        = self.env.getVision()
        settings      = self.env.getSettings()
        resources     = self.env.getObjectManager()
        vStream       = self.env.getVStream()
        newSleep      = lambda time: wait(time, self.isExiting)
        isExiting     = self.isExiting


        # Add Python builtins, and also the extra ones (above)
        builtins = {      "abs":       abs,            "dict":            dict,  "__import__":  __import__,
                          "all":       all,             "hex":             hex,       "slice":       slice,
                          "any":       any,          "divmod":          divmod,      "sorted":      sorted,
                        "ascii":     ascii,       "enumerate":       enumerate,       "range":       range,
                          "bin":       bin,             "int":             int,         "str":         str,
                         "bool":      bool,      "isinstance":      isinstance,         "ord":         ord,
                    "bytearray": bytearray,          "filter":          filter,  "issubclass":  issubclass,
                        "bytes":     bytes,           "float":           float,        "iter":        iter,
                     "callable":  callable,             "len":             len,        "type":        type,
                          "chr":       chr,       "frozenset":       frozenset,        "list":        list,
                       "locals":    locals,             "zip":             zip,        "vars":        vars,
                      "globals":   globals,             "map":             map,    "reversed":    reversed,
                      "complex":   complex,             "max":             max,       "round":       round,
                      "delattr":   delattr,            "hash":            hash,         "set":         set,
                          "min":       min,             "oct":             oct,         "sum":         sum,
                          "pow":       pow,           "super":           super,       "print": customPrint,
                        "tuple":     tuple,           "robot":           robot,   "resources":   resources,
                       "vision":    vision,        "settings":        settings,     "vStream":     vStream,
                        "sleep":  newSleep,  "scriptStopping":       isExiting, "classmethod": classmethod,
                       "object":    object, "__build_class__": __build_class__,    "__name__":  "__main__",
                           "env": self.env,     "interpreter": self}



        namespace = {}
        namespace.update(commandClasses)
        namespace.update(eventClasses)
        namespace.update(variables)
        namespace.update(builtins)
        namespace.update({"__author__": "Alexander Thiel"})

        self.nameSpace = namespace

    def evaluateExpression(self, expression):

        # Returns value, success. Value is the output of the expression, and 'success' is whether or not it crashed.
        # If it crashes, it returns None, but some expressions might return none, so 'success' variable is still needed.
        # Side note: I would have to do ~66,000 eval operations to lag the program by one second.

        answer = None

        try:
            answer = eval(expression, self.nameSpace)
        except Exception as e:
            # Print a traceback of the error to the console
            printTraceback()

            # Save an error report so the GUI can show it to the user
            global exitErrors
            exitErrors = {type(e).__name__ + " in Expression " + str(expression): [str(e)]}

            # Stop the interpreter
            self.setExiting(True)


        if answer is None:
            return None, False

        return answer, True

    def evaluateScript(self, script):


        try:
            exec(script, self.nameSpace)
        except Exception as e:
            # Print a traceback of the error to the console
            printTraceback()

            # Save an error report so the GUI can show it to the user
            global exitErrors
            exitErrors = {type(e).__name__ + " While Evaluating Script": [str(e)]}

            # Stop the interpreter
            self.setExiting(True)

            return False

        return True

    def createChildInterpreter(self, script, nameSpace=None):
        """
            This function is special, in the sense that it creates another interpreter that runs inside of this one,
            with a specified filename or script, and starts it immediately.
        """
        # if self.env.isInterpreterExiting: return


        child = Interpreter(self.env, nameSpace=nameSpace)
        errors = child.initializeScript(script)

        if len(errors):
            printf("Interpreter| ERROR: Tried to run a task that did not meet the requirements. Errors:\n", errors)

            self.setExiting(True)

            # Set the crashErrors so that the GUI can later show a message to the user explaining why the program ended
            global exitErrors
            exitErrors = errors

        return child



    # The following functions are for interpreter to use within itself.
    def __programThread(self):
        printf("Interpreter| ##### STARTING PROGRAM #####\n")

        fpsTimer = FpsTimer(fps=30)

        # Main program loop - where events are checked and run
        while not self.isExiting():
            # Maintain constant FPS using an FPSTimer
            fpsTimer.wait()
            if not fpsTimer.ready(): continue


            # currRunning keeps track of what was run, so the GUI can draw it
            self.currRunning = {"event": -1, "command": -1}



            # Check every event, in order of the list
            exitCommand = False  # If the interpreter reached an "ExitProgram" command
            for index, event in enumerate(self.events):
                if self.isExiting(): break
                if not event.isActive(): continue

                # If the event has been activated, run the commandList
                self.currRunning["event"] = self.events.index(event)
                exitCommand = self.interpretCommandList(event.commandList)
                if exitCommand: break
            if exitCommand: break


        self.events     = []
        printf("Interpreter| Interpreter Thread Ended")
        self.mainThread = None

    def interpretCommandList(self, commandList):
        """
        This will run through every command in an events commandList, and account for Conditionals and code blocks.

        It returns True if the interpreter reached an "ExitProgram" command
        """

        index         = 0  # The current command that is being considered for running


        # Check each command, run the ones that should be run
        while index < len(commandList):
            if self.isExiting(): break


            # Run the command
            command    = commandList[index]
            self.currRunning["command"] = index

            try:
                evaluation = command.run()
            except Exception as e:
                printf("Interpreter| ERROR: ", command.__class__.__name__, type(e).__name__, ": ", e)
                global exitErrors
                exitErrors = {type(e).__name__ + " in " + command.__class__.__name__ + " " : [str(e)]}
                self.setExiting(True)



            if self.isExiting(): break  # This speeds up ending recursed Interpreters


            # If the command returned an "Exit event" command, then exit the event evaluation
            if evaluation == "ExitProgram":
                return True
                # self.setExiting(True)
                # break

            # If the command returned an "Exit Program" command, exit the program
            if evaluation == "ExitEvent":
                break


            # If its false, skip to the next indent of the same indentation, or an "Else" command
            if evaluation is False:
                index = self.__getNextIndex(index, commandList)
            else:
                # If an else command is the next block, decide whether or not to skip it
                if index + 1 < len(commandList) and type(commandList[index + 1]) is Commands.ElseCommand:
                    # If the evaluation was true, then DON'T run the else command
                    index = self.__getNextIndex(index + 1, commandList)


            # Every time you hit an "End Block", check if it's a loop, and if so, go back to that area
            if index - 1 >  0 and type(command) is Commands.EndBlockCommand:
                lastIndex = self.__getLastIndex(index, commandList)

                if lastIndex + 1 < len(commandList) and type(commandList[lastIndex + 1]) is Commands.LoopCommand:  # type(commandList[lastIndex]) is Commands.LoopCommand:
                    index = lastIndex

            index += 1

        return False

    def __getNextIndex(self, index, commandList):
        """
        Find the next index that has the same indentation level as the current index
        """

        skipToIndent = 0
        nextIndent   = 0
        for i in range(index + 1, len(commandList)):
            commandType = type(commandList[i])

            if commandType is Commands.StartBlockCommand: nextIndent += 1

            if nextIndent == skipToIndent:
                index = i - 1
                break

            # If there are no commands
            if i == len(commandList) - 1:
                index = i
                break


            if commandType is Commands.EndBlockCommand:   nextIndent -= 1

        return index

    def __getLastIndex(self, index, commandList):
        """
        Find the last index that has the same indentation level as the current index
        """

        skipToIndent = 0
        nextIndent   = 0
        for i in range(index,  -1, -1):
            commandType = type(commandList[i])

            if commandType is Commands.EndBlockCommand:   nextIndent += 1

            if nextIndent == skipToIndent:
                index = i - 1
                break

            # If there are no commands
            if i == 0: break

            if commandType is Commands.StartBlockCommand: nextIndent -= 1

        # if index - 1 >= 0:
        #     index -= 1

        return index



"""
This is a global call for only the interpreter to pay attention to, and when it is True, the Interpreter and any command
inside of it will try to exit as quickly as possible. This global is so that recursively running Interpreters can
exit quickly, and there's passing around of an exit variable all the time.
"""
global exitingFlag
exitingFlag = False


"""
This variable is so that if the Interpreter needs to end abruptly, it'll write down the erros,
and the GUI will later display them to the user in a message.

This variable can be retrieved using Interpreter.getExitErrors()
"""
global exitErrors
exitErrors = None


"""
This is a dictionary of each command Type in Commands.py, and each event Type in Events.py
This is used so that loading scripts will be faster in Interpreter.initializeScript
Furthermore, its safer than using getattr("Commands", thecommand) since it doesn't pull any other modules that are
imported in Commands. This way people can't have save files that run arbitrary code. They can only access
types that are classes in Commands.py and Events.py
"""
commandClasses = Global.getModuleClasses(Commands)
eventClasses   = Global.getModuleClasses(Events)

"""
This function will print the latest stacktrace error in a format that is friendly to the Console widget
"""
printTraceback    = lambda: printf("Interpreter| \n" + "-" * 35 + "ERROR" + "-" * 35 + "\n",
                                            traceback.format_exc(), "-" * 75 + "\n")