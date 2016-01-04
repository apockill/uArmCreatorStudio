__author__ = 'AlexThiel'
import uarm_python
from time import sleep

uarm = uarm_python .Uarm("COM9")
uarm.moveToWithTime(0, -15, 15, 1)
while True:
    print "Status:", uarm.stopperStatus()
