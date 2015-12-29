import serial
import serial.tools.list_ports
from UArmForPython.uarm_python import Uarm

def getConnectedRobots():
    #FIND THE ROBOTS ARDUINO PORT AND CREATE ser1 TO CONNECT TO IT
    ports = list(serial.tools.list_ports.comports())
    # for intex, port in enumerate(ports):
    #     if "FTDIBUS" in port[2]:
    #         print "Found arduino on port: ", port[0]
    #         ser1 = serial.Serial(port[0], 9600, timeout=0)  #Create connection
    return ports

class Robot():
    """
    X:
    Y:
    Z: Ground level is at 6.5cm
    """
    def __init__(self):
        self.pos = {'x':       0.0,
                    'y':       0.0,
                    'z':       0.0,
                    'wrist':   0.0,
                    'grabber': 0.0,
                    'touch':     0}
        self.uArm = None

    def moveTo(self, **kwargs):
        relative = kwargs.get('relative',     False)
        waitFor  = kwargs.get('waitForRobot', False)  #If true, waitForRobot() will be run at the end of the function

        #HANDLE ANY OTHER COMMANDS, INCLUDING POLAR COMMANDS
        for name, value in kwargs.items():  #Cycles through any variable that might have been in the kwargs. This is any position command!

            if name in self.pos:  #If it is a position statement.
                if self.pos[name] is "": continue
                if relative:
                    self.pos[name] += value
                else:
                    self.pos[name] = value


        success = self.sendPos()

        if waitFor and success: self.waitForRobot()

    def setPos(self, **kwargs):
        relative = kwargs.get('relative',     False)

        for name, value in kwargs.items():  #Cycles through any variable that might have been in the kwargs. This is any position command!
            if name in self.pos:  #If it is a position statement.
                if self.pos[name] is "": continue
                if relative:
                    self.pos[name] += value
                else:
                    self.pos[name] = value

    def sendPos(self):
        #Sends all positional data in self.pos to the robot

        if self.uArm is None:
            print "Robot.sendPos() ERROR: Tried sending command while uArm is None"
            return False

        self.uArm.moveToKw(x=self.pos['x'],
                           y=self.pos['y'],
                           z=self.pos['z'])
        return True


    def setuArm(self, com):
        #TODO: Impliment a handshake with the robot here
        self.uArm = Uarm(com)

    def waitForRobot(self):
        #Todo: add communication with robot
        sleep(.75)


