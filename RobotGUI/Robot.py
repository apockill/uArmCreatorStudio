import serial
import serial.tools.list_ports

def getConnectedRobots():
    #FIND THE ROBOTS ARDUINO PORT AND CREATE ser1 TO CONNECT TO IT
    #TODO: MAKE A HANDSHAKE WITH THE ARDUINO TO CONFIRM IT IS A UARM
    ports = list(serial.tools.list_ports.comports())
    # for intex, port in enumerate(ports):
    #     if "FTDIBUS" in port[2]:
    #         print "Found arduino on port: ", port[0]
    #         ser1 = serial.Serial(port[0], 9600, timeout=0)  #Create connection
    return ports
