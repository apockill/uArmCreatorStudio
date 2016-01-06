__author__ = 'AlexThiel'
import uarm_python
from time import sleep

uarm = uarm_python .Uarm("COM9")
#uarm.moveToWithTime(0, -25, 25, 5)
uarm.moveToWithTime(-15, -10,  6, 0)
sleep(3)
print "start"
uarm.moveToWithTime(15, -25,  25, 0)
print "Done"
