__author__ = 'AlexThiel'


def init():
    #Global variables should only ever be used by Events, Commands, and the programThread method of ControlPanel
    #No where else. Seriously, this is a bad habit. I just couldn't figure out a way of sharing all the appropriate
    #Objects to each class and event properly while still communicating errors throughout all the different
    #layers of abstraction


    global robot
    global keysPressed
    #global promptSave


    keysPressed    = []        #Used in keyboardEvent
    robot          = None      #Used in any movement related commands, or position based events

    #promptSave  = False       #If true, when the user closes the program it will prompt them if they want to save


