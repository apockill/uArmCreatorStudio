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
import os
import errno
from time import time, sleep

__author__ = "Alexander Thiel"

"""
Global is a set of functions that are used in many places around the project and are very general use.

It also holds the actual global variable "keysPressed", and "printRedirectFunc". More documentation below.
"""


# Special 'sleep' commands that can exit immediately if 'exitFunc()' returns false
def wait(waitTime, exitFunc):
    """
    This is a convenience function for waiting a certain amount of time. The idea is that the exitFunc will
    quit the wait at any point that it returns True. This is so that when the interpreter is stopped, all
    commands will exit quickly and easily.
    """
    waitUntilTime(time() + waitTime, exitFunc)


    # # While sleeping, make sure that the script has not been shut down
    # start = time()
    # while time() - start < waitTime - .05:
    #     if exitFunc(): return
    #     sleep(.1)
    #
    # sleep(waitTime - (time() - start))

def waitUntilTime(timeMS, exitFunc):
    """
    Waits until a certain time is reached
    :param timeMS:  time in miliseconds since some 1970
    :param exitFunc: A function that, if returns True, will exit the sleep immediately
    :return:
    """

    if exitFunc(): return

    while time() < timeMS - 0.075:
        if exitFunc(): return
        sleep(.07)


    # Sleep the last little bit, for extra accuracy
    now = time()
    if now < timeMS:
        sleep(timeMS - now)

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
        self.lastTime  = float(1)  # The first time is 1, so the script will always run immediately
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



# Initiate Global Variables
def init():
    global keysPressed
    global printRedirectFunc
    global exitScriptFlag

    """
      Used in keyboardEvent. Updated through Main.Application.notify() Format: ['a', 'b', '5', 'z']
      Characters are stored while key is pressed, and removed when key is released
    """
    keysPressed        = []


    """
      When this function is set, all print "strings" will be sent to it before printing normally
      The use case is for the Console widget. If printRedirectFunc = Console.write, then all prints will print on there
    """
    printRedirectFunc  = lambda classString, string: None  # print(classString + " "*(30 - len(classString)) + string)



# Functions for my special print function
"""def getCallerFunction(skip=2, printModule=True, printClass=True, printFunction=True):
    '''Get a name of a caller in the format module.class.method

       `skip` specifies how many levels of stack to skip while getting caller
       name. skip=1 means "who calls me", skip=2 "who calls my caller" etc.

       An empty string is returned if skipped levels exceed stack height
    '''
    stack = inspect.stack()
    start = 0 + skip
    if len(stack) < start + 1:
        return ''
    parentframe = stack[start][0]

    name = []
    if printModule:

        module = inspect.getmodule(parentframe)
        # `modname` can be None when frame is executed directly in console
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
"""

def printf(*args):
    """
    This function appends the Class and Function name to every function that runs in the program. This is immeasurably
    helpful for debugging.
    """

    # Start building the printString
    buildString = ""


    # Concatenate arguments, same as normal print statements
    for i in args: buildString += str(i)


    # Strip whitespace from beginning of string
    buildString = buildString.lstrip()


    # Split the string into a "header" and "content"
    if "|" in buildString:
        splitIndex  = buildString.index("| ")
        header      = buildString[:splitIndex]
        content     = buildString[splitIndex + 2:]
    else:
        header = ""
        content = buildString




    # Send the string to the printRedirectFunction for the ConsoleWidget to recieve
    global printRedirectFunc
    printRedirectFunc(header, content)


    # # Format the space between the boilerplate and content
    # boilerPlate = getCallerFunction(printModule=printModule, printClass=printClass, printFunction=printFunction)



    # Filter out any serial communication since it clutters up the console
    if "Communication" in header: return


    print(header + " " * (15 - len(header)) + content)




def ensurePathExists(path):
    """
        This is a cross platform, race-condition free way of checking if a directory exists, and if it doesn't,
        creating that directory. It's used every time an object is loaded and saved
    """
    try:
        directory = os.path.dirname(path)
        os.makedirs(directory)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def getModuleClasses(module):
    """
    This will get all of the classes defined in a module, with the format
    {"className": class, "className": class}

    This is used to not do getattr directly on a module, so as to avoid weird vulnerabilities,
    and allow for quick security patches in the future.
    """
    return dict([(name, cls) for name, cls in module.__dict__.items() if isinstance(cls, type)])