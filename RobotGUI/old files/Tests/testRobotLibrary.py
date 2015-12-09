from RobotArm import Robot
from time import sleep


if '__main__' == __name__:
    sleep(3)


    while True:

        Robot.moveTo(height=0, stretch=float(raw_input('stretch?:')), relative=False)
        sleep(.1)
        Robot.moveTo(height = -40, relative=False)