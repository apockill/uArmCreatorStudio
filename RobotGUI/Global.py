__author__ = 'AlexThiel'


def init():

    global keysPressed
    keysPressed    = []        #Used in keyboardEvent. Updated through Main.Application.notify()




spaceFunc = lambda n: ''.join(' ' for _ in xrange(n))
def printf(*args):
    buildString = ""
    for i in args:
        buildString += str(i)

    buildString = buildString.lstrip()  #Strip whitespace from beginning of string

    #Do string formatting
    if ':' in buildString:
        splitIndex = buildString.index(':')

        boilerPlate = buildString[:splitIndex].lstrip()
        content     = buildString[splitIndex + 1:].lstrip()

        spaces = int((35 - len(boilerPlate)))       #How many spaces ahead the content column should be
        if spaces > 0:

            spacesString = spaceFunc(spaces)
            boilerPlate +=  spacesString

        buildString = boilerPlate + content


    print buildString
