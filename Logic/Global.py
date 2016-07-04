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
    def __init__(self, fps):
        self.stepDelay = (1 / float(fps))
        # self.readyForNext = lambda lastTime: time() - lastTime >= self.stepDelay
        self.lastTime = time()

    def wait(self):
        waitTime = self.stepDelay - (time() - self.lastTime)
        if waitTime > .005: sleep(waitTime)


    def ready(self):
        isReady = time() - self.lastTime >= self.stepDelay
        if isReady: self.lastTime = time()

        return isReady


def ensurePathExists(path):
    '''
        This is a cross platform, race-condition free way of checking if a directory exists. It's used every time
        an object is loaded and saved
    '''
    try:
        dir = os.path.dirname(path)
        print("path", path, "dir", dir)
        os.makedirs(dir)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

