__author__ = 'AlexThiel'
import uarm_python
from time import sleep

uarm = uarm_python .Uarm("COM9")
uarm.moveTo(0, -15, 15)
uarm.servoDetach(2)
uarm.servoDetach(3)
uarm.servoAttach(2)
