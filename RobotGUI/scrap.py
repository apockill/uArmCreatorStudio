from PyQt4 import QtGui, QtCore
import math

def getActual(x1, y1, baseAngle):
    angle = math.radians(baseAngle) - math.radians(90)

    x = x1 * math.cos(angle) - y1 * math.sin(angle)
    y = x1 * math.sin(angle) + y1 * math.cos(angle)
    print x,y



getActual(-1,0, 45)