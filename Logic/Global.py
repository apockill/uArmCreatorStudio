import os
import errno
import json
from time import time, sleep

"""
Global is a set of functions that are used in many places around the project and are very general use.
It also holds the actual global variable "keysPressed".
"""


# Initiate the keysPressed global variable
def init():
    global keysPressed
    keysPressed    = []        #Used in keyboardEvent. Updated through Main.Application.notify()



spaceFunc = lambda n: ''.join(' ' for _ in range(n)) # For printf
def printf(*args):
    buildString = ""

    for i in args:
        buildString += str(i)

    buildString = buildString.lstrip()  #Strip whitespace from beginning of string

    # Do string formatting
    if ':' in buildString:
        splitIndex = buildString.index(':')

        boilerPlate = buildString[:splitIndex].lstrip()
        content     = buildString[splitIndex + 1:].lstrip()

        spaces = int((35 - len(boilerPlate)))       #How many spaces ahead the content column should be
        if spaces > 0:

            spacesString = spaceFunc(spaces)
            boilerPlate +=  spacesString

        buildString = boilerPlate + content


    print(buildString)


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

