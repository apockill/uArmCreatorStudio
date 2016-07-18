import os
import errno
import inspect
from time import time, sleep
from threading import RLock
"""
Global is a set of functions that are used in many places around the project and are very general use.
It also holds the actual global variable "keysPressed".
"""


def wait(waitTime, exitFunc):
    """
    This is a convenience function for waiting a certain amount of time. The idea is that the exitFunc will
    quit the wait at any point that it returns True. This is so that when the interpreter is stopped, all
    commands will exit quickly and easily.
    """

    waitedTime = 0

    # While sleeping, make sure that the script has not been shut down
    start = time()
    while time() - start < waitTime - .05:
        if exitFunc(): return
        sleep(.05)

    sleep(waitTime - (time() - start))


def waitUntilTime(timeMS, exitFunc):
    # Waits until a certain time is reached, where timeMS is the time in miliseconds since some 1970

    if exitFunc(): return

    while time() < timeMS - 0.055:
        if exitFunc(): return
        sleep(.05)


    # Sleep the last little bit, for extra accuracy
    now = time()
    if now < timeMS:
        sleep(timeMS - now)


# Initiate Global Variables (called from
def init():
    global keysPressed
    global printRedirectFunc

    # Used in keyboardEvent. Updated through Main.Application.notify() Format: ['a', 'b', '5', 'z']
    # Characters are stored while key is pressed, and removed when key is released
    keysPressed        = []

    # When this function is set, all print "strings" will be sent to it before printing normally
    # The use case is for the Console widget. If printRedirectFunc = Console.write, then all prints will print on there
    printRedirectFunc  = lambda classString, string: None



# Gets the name of the caller of a function in a neatly formatted string
def caller_name(skip=2, printModule=True, printClass=True, printFunction=True):
    """Get a name of a caller in the format module.class.method

       `skip` specifies how many levels of stack to skip while getting caller
       name. skip=1 means "who calls me", skip=2 "who calls my caller" etc.

       An empty string is returned if skipped levels exceed stack height
    """
    stack = inspect.stack()
    start = 0 + skip
    if len(stack) < start + 1:
        return ''
    parentframe = stack[start][0]

    name = []
    if printModule:

        module = inspect.getmodule(parentframe)
        # `modname` can be None when frame is executed directly in console
        # TODO(techtonik): consider using __main__
        if module:
            name.append(module.__name__)

    # detect classname
    if printClass:
        if 'self' in parentframe.f_locals:
            # I don't know any way to detect call from the object method
            # XXX: there seems to be no way to detect static method call - it will
            #      be just a function call
            name.append(parentframe.f_locals['self'].__class__.__name__)


    if printFunction:
        codename = parentframe.f_code.co_name
        if codename != '<module>':  # top level usually
            name.append( codename)  # function or a method
    del parentframe

    return ".".join(name)



spaceFunc = lambda n: ''.join(' ' for _ in range(n))  # For printf
def printf(*args):
    """
    This function appends the Class and Function name to every function that runs in the program. This is immeasurably
    helpful for debugging.
    """


    # Create settings for the boilerplate information
    printModule   = False
    printFunction = False    # If false, no boilerplate will be printed
    printClass    = True

    indentLength  = 40      # Length of indent between boilerplate and content


    # Start building the printString
    buildString = ""


    # Concatenate arguments, same as normal print statements
    for i in args:
        buildString += str(i)


    # Strip whitespace from beginning of string
    buildString = buildString.lstrip()


    # Format the space between the boilerplate and content
    boilerPlate = caller_name(printModule=printModule, printClass=printClass, printFunction=printFunction)

    global printRedirectFunc
    printRedirectFunc(boilerPlate, buildString)


    # Filter out any serial communication since it clutters up the console
    if boilerPlate == "Device": return

    if len(boilerPlate) > 0:
        spaces = int((indentLength - len(boilerPlate)))       #How many spaces ahead the content column should be
        if spaces > 0:
            spacesString = spaceFunc(spaces)
            boilerPlate +=  spacesString

    buildString = boilerPlate + buildString
   #  print(buildString)






class FpsTimer:
    """
    This module helps keep scripts at a certain FPS. The Interpreter script uses this, as does the VideoThread.
    This will effectively decide whether or not to wait, and how much to wait, and time how long a script is taking
    inside of a loop.

    Usage example:

            fpsTimer = FpsTimer(fps=24)

            while True:
                fpsTimer.wait()
                if not fpsTimer.ready(): continue

                ### Script goes here ###
    """

    def __init__(self, fps):

        self.fps       = fps
        self.stepDelay = (1.0 / float(fps))
        self.lastTime  = float(time())
        self.isReady   = False
        self.mode      = 1

        self.currentFPS = 0

    def wait(self):
        elapsedTime = time() - self.lastTime


        # Check if the current FPS is less than the goal. If so, run immediately
        if not elapsedTime == 0:
            fps = 1.0 / elapsedTime
            if fps < self.fps:
                self.currentFPS = fps
                self.isReady = True
                return

        # Since the current FPS is higher than desired, wait the appropriate amount of time
        waitTime = self.stepDelay - elapsedTime
        if waitTime > .01:
            sleep(waitTime)
            self.currentFPS = 1.0 / (time() - self.lastTime)
        # Calculate FPS again
        self.isReady = True
        return

    def ready(self):

        if self.isReady:
            self.lastTime = time()
            self.isReady = False
            return True
        else:
            return False


def ensurePathExists(path):
    '''
        This is a cross platform, race-condition free way of checking if a directory exists. It's used every time
        an object is loaded and saved
    '''
    try:
        dir = os.path.dirname(path)
        os.makedirs(dir)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

