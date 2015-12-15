import serial
import serial.tools.list_ports
from time import sleep

def getConnectedRobots():
    #FIND THE ROBOTS ARDUINO PORT AND CREATE ser1 TO CONNECT TO IT
    ports = list(serial.tools.list_ports.comports())
    # for intex, port in enumerate(ports):
    #     if "FTDIBUS" in port[2]:
    #         print "Found arduino on port: ", port[0]
    #         ser1 = serial.Serial(port[0], 9600, timeout=0)  #Create connection
    return ports

class Robot():
    def __init__(self):
        self.pos = {'rotation': 0.0,
                    'stretch':  0.0,
                    'height':   0.0,
                    'wrist':    0.0,
                    'grabber':  0.0,
                    'touch':      0}
        self.serial = None

    def moveTo(self, **kwargs):
        relative = kwargs.get('relative', False)
        waitFor  = kwargs.get('waitForRobot', False)  #If true, waitForRobot() will be run at the end of the function

        #HANDLE ANY OTHER COMMANDS, INCLUDING POLAR COMMANDS
        for name, value in kwargs.items():  #Cycles through any variable that might have been in the kwargs. This is any position command!

            if name in self.pos:  #If it is a position statement.
                if self.pos[name] is "": continue
                if relative:
                    self.pos[name] += value
                else:
                    self.pos[name] = value
        self.sendPos()

        if waitFor: self.waitForRobot()

    def sendPos(self):
        #Sends all positional data in self.pos to the robot

        if self.serial is None:
            print "Robot.sendPos() ERROR: Tried sending command while Serial is None"
            return


        self.serial.write('%s:%s' % ('r', round(self.pos['rotation'], 2)))
        self.serial.write('%s:%s' % ('s', round(self.pos[ 'stretch'], 2)))
        self.serial.write('%s:%s' % ('h', round(self.pos[  'height'], 2)))
        self.serial.write('%s:%s' % ('w', round(self.pos[   'wrist'], 2)))


        # except:
        #     print "Robot.sendPos(): ERROR: Failed to send moveTo command to Robot!"

    def setSerial(self, com):
        #TODO: Impliment a handshake with the robot here
        self.serial = serial.Serial(com, 9600, timeout=0)  #Create connection

    def waitForRobot(self):
        #Todo: add communication with robot
        sleep(.75)