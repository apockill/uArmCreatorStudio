import serial
import serial.tools.list_ports
import Global
from threading import Thread
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
    def __init__(self, comPort):
        self.uArm = None
        self.home = {"x": 0, "y": -15, "z": 15}
        self.pos =     {'x':       0.0,
                        'y':       0.0,
                        'z':       0.0,
                        'wrist':   0.0,
                        'grabber': 0.0,
                        'touch':     0}

        #Every time uArm is connected correctly, all servos are attached. Update the values to match this.
            #Keep track of which servos are attached
        self.servoStatus = {1: True,
                            2: True,
                            3: True,
                            4: True}
            #If there is ever a change in a servos status, it is stored in this container until
            #the 'refresh' function is run
        self.newServoStatus =   {1: True,
                                 2: True,
                                 3: True,
                                 4: True}

        self.positionChanged = True
        self.running         = False  #If the setup Thread is running currently



    # def moveTo(self, **kwargs):
    #     relative = kwargs.get('relative',     False)
    #     waitFor  = kwargs.get('waitForRobot', False)  #If true, waitForRobot() will be run at the end of the function
    #
    #     #HANDLE ANY OTHER COMMANDS, INCLUDING POLAR COMMANDS
    #     for name, value in kwargs.items():  #Cycles through any variable that might have been in the kwargs. This is any position command!
    #
    #         if name in self.pos:  #If it is a position statement.
    #             if self.pos[name] is "": continue
    #             if relative:
    #                 self.pos[name] += value
    #             else:
    #                 self.pos[name] = value
    #
    #
    #     success = self.refreshPos()
    #
    #     if waitFor and success: self.waitForRobot()
        # def setDetached(self, **kwargs):


    def currentCoord(self):
        if self.uArm is None or self.running:
            print "Robot.currentCoord():\t Robot not found or setupThread is running, returning 0 for all coordinates.."
            return {1:0, 2:0, 3:0}
        else:
            print "Robot.currentCoord():\t Getting coordinates for robot..."
            return self.uArm.currentCoord()


    def setPos(self, **kwargs):
        relative = kwargs.get('relative', False)
        posBefore = dict(self.pos)

        for name, value in kwargs.items():  #Cycles through any variable that might have been in the kwargs. This is any position command!
            if name in self.pos:  #If it is a position statement.
                if self.pos[name] is "": continue
                if relative:
                    self.pos[name] += value
                else:
                    self.pos[name] = value

        #If this command has changed the position, or if the position was changed earlier
        self.positionChanged = (not (posBefore == self.pos)) or self.positionChanged
        print "positionchanged: ", self.positionChanged

    def setServos(self, **kwargs):
        #If anything changed, set the appropriate newServoStatus to reflect that
        self.newServoStatus[1] = kwargs.get('servo1', self.newServoStatus[1])
        self.newServoStatus[2] = kwargs.get('servo2', self.newServoStatus[2])
        self.newServoStatus[3] = kwargs.get('servo3', self.newServoStatus[3])
        self.newServoStatus[4] = kwargs.get('servo4', self.newServoStatus[4])

        #print "setServos run: ", self.newServoStatus, self.servoStatus


    def refresh(self):
            #Sends all positional data in self.pos to the robot

            if self.uArm is None or self.running:
                print "Robot.refresh() ERROR: Tried sending command while uArm is None or setupThread was running"
                return False

            self.updateServo(1)
            self.updateServo(2)
            self.updateServo(3)
            self.updateServo(4)

            if self.positionChanged:
                self.uArm.moveToWithTime(self.pos['x'], self.pos['y'], self.pos['z'], 0)
                self.positionChanged = False

    def updateServo(self, num):
        if not self.newServoStatus[num] == self.servoStatus[num]:
            if self.newServoStatus[num]:
                #Attach the servo
                self.uArm.servoAttach(num)
                self.servoStatus[num] = True
                self.positionChanged = True
                print "Robot.updateServo():\t Servo", num, "attached"
            else:
                #Detach the servo
                self.uArm.servoDetach(num)
                self.servoStatus[num] = False
                print "Robot.updateServo():\t Servo", num, "detached"


    def setupThread(self, com):
        try:
            self.uArm = Uarm(com)
            #self.servoDetach()
            print "Robot.setUArm():\t uArm successfully connected"

        except serial.SerialException:
            print "Robot.setUArm():\t ERROR SerialException while setting uArm to ", com
        self.running = False
        self.refresh()

    def setUArm(self, com):
        if com is not None and not self.running:
            print "Robot.setUArm():\t Setting uArm to com", com, "..."
            setupThread = Thread(target=lambda: self.setupThread(com))
            self.running = True
            setupThread.start()
        else:
            if self.running: print "Robot.setUArm()\t ERROR: setUArm() run while setupThread was already running!"
        self.setPos(**self.home)





