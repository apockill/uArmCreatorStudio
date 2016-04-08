from RobotGUI import UArmTextCommunication
import math
from time import sleep





#
# def getActual(x1, y1, baseAngle):
#     angle = math.radians(baseAngle) - math.radians(90)
#
#     x = x1 * math.cos(angle) - y1 * math.sin(angle)
#     y = x1 * math.sin(angle) + y1 * math.cos(angle)
#     return  x,y




uarm = UArmTextCommunication.Uarm("COM5")

while True:
    uarm.moveToWithTime(int(input("x")), int(input("y")), 20, 1.5)
    print(uarm.currentCoord())
#uarm.moveToWithTime(x0, y0, 15, 5)
# x0 = 0
# y0 = -15
# uarm.moveToWithTime(x0, y0,  15, 2)
#
# x,y =  getActual(-10, -10, uarm.readAngle(1))
#
# print x, y
#
# uarm.moveToWithTime(x + x0, y + y0, 15, 5)

