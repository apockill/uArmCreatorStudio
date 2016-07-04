import serial
import serial.tools.list_ports
from time         import sleep
from Logic.Global import printf

# This is a library for controlling uArms that have Alex Thiel's Arduino communication protocol uploaded
def getConnectedRobots():
    # Returns any arduino serial ports in a list [port, port, port]
    # This is used to let the user choose the correct port that is their robot
    ports = list(serial.tools.list_ports.comports())
    return ports


class Uarm:

    def __init__(self, port, printResponses=False):
        self.printResponses = printResponses
        self.isConnected    = False
        self.serial         = None

        self.__connectToRobot(port)

        # For debug logs
        self.responseLog = []  # An array of tuples, of what was sent and what was recieved [(sent, recieved), ..(s, r)]

    def connected(self):
        # if self.serial is None:     return False
        if self.isConnected is False: return False
        # if not self.__handshake():  return False
        return True


    # Action commands
    def moveToWithSpeed(self, x, y, z, speed):
        x = str(round(    x, 2))
        y = str(round(    y, 2))
        z = str(round(    z, 2))
        t = str(round(speed, 2))
        cmnd = "moveX" + x + "Y" + y + "Z" + z + "S" + t
        return self.__send(cmnd)

    def moveWrist(self, angle):
        angle = str(round(angle, 3))
        cmnd = "handV" + angle
        return self.__send(cmnd)

    def gripperOn(self):
        cmnd = "pumpV1"
        return self.__send(cmnd)

    def gripperOff(self):
        cmnd = "pumpV0"
        return self.__send(cmnd)

    def servoAttach(self, servo_number):
        print("Attaching")
        servo_number = str(int(servo_number))
        cmnd = "attachS" + servo_number
        return self.__send(cmnd)

    def servoDetach(self, servo_number):
        print("uarm com: Detaching")
        servo_number = str(int(servo_number))
        cmnd = "detachS" + servo_number
        return self.__send(cmnd)

    def setBuzzer(self, frequency, duration):
        cmnd = "buzzF" + str(frequency) + "T" + str(duration)
        return self.__send(cmnd)


    # Get commands
    def getCurrentCoord(self):
        # Returns an array of the format [x, y, z] of the robots current location

        response  = self.__send("gcoords")

        parsedArgs = self.__parseArgs(response, "coords", ["x", "y", "z"])
        coordinate = [parsedArgs["x"], parsedArgs["y"], parsedArgs["z"]]

        return coordinate

    def getIsMoving(self):
        # Returns a 0 or a 1, depending on whether or not the robot is moving.

        response  = self.__send("gmoving")

        parsedArgs = self.__parseArgs(response, "moving", ["m"])
        return parsedArgs["m"]

    def getServoAngle(self, servo_number):
        # Returns an angle in degrees, of the servo

        cmnd = "gAngleS" + str(servo_number)
        response = self.__send(cmnd)
        parsedArgs = self.__parseArgs(response, "angle", ["a"])

        return parsedArgs["a"]

    def getTipSensor(self):
        # Returns 0 or 1, whether or not the tip sensor is currently activated

        response  = self.__send("gtip")
        parsedArgs = self.__parseArgs(response, "tip", ["v"])
        return (True, False)[int(parsedArgs['v'])]  # Flip the value and turn it into a boolean


    # Not to be used outside of library
    def __connectToRobot(self, port):
        try:
            self.serial = serial.Serial(port     = port,
                                        baudrate = 115200,
                                        parity   = serial.PARITY_NONE,
                                        stopbits = serial.STOPBITS_ONE,
                                        bytesize = serial.EIGHTBITS,
                                        timeout  = .1)
            self.isConnected = True
        except serial.SerialException as e:
            printf("Uarm.connectToRobot(): Could not connect to robot on port ", port)
            self.serial = None
            self.isConnected = False
        sleep(3)

    def __send(self, cmnd):
        # This command will send a command and recieve the robots response. There must always be a response!
        if not self.connected(): return None


        # Prepare and send the command to the robot
        cmndString = bytes("[" + cmnd + "]>", encoding='ascii')
        try:
            self.serial.write(cmndString)
        except serial.serialutil.SerialException as e:
            printf("UArm.__send(): ERROR ", e, "while sending command ", cmnd, ". Disconnecting Serial!")
            self.isConnected = False
            return False


        # Read the response from the robot (THERE MUST ALWAYS BE A RESPONSE!)
        response = ""
        while True:

            try:
                response += str(self.serial.read(), 'ascii')
            except serial.serialutil.SerialException as e:
                printf("UArm.__send(): ERROR ", e, "while sending command ", cmnd, ". Disconnecting Serial!")
                self.isConnected = False
                return False

            if "\n" in response:
                response = response[:-1]
                break

        # Save the response to a log variable, in case it's needed for debugging
        self.responseLog.append((cmnd, response))

        # Make sure the respone has the valid start and end characters
        if not (response.count('[') == 1 and response.count(']') == 1):
            printf("Uarm.read(): ERROR: The message ", response, " did not come with proper formatting!")


        # Clean up the response
        response = response.replace("[", "")
        response = response.replace("]", "")
        response = response.lower()


        # If the robot returned an error, print that out
        if "error" in response:
            printf("Uarm.read(): ERROR: Recieved error from robot: ", response)

        if self.printResponses:
            print(response)
        return response

    def __parseArgs(self, message, command, arguments):
        responseDict = {n: 0 for n in arguments}  #Fill the dictionary with zero's


        # Do error checking, in case communication didn't work
        if message is False:
            printf("Uarm.__parseArgs(): Since an error occured in communication, returning 0's for all arguments!")
            return responseDict

        if command not in message:
            printf("Uarm.__parseArgs(): ERROR: The message did not come with the appropriate command!")
            return responseDict


        # Get rid of the "command" part of the message, so it's just arguments and their numbers
        message = message.replace(command, "")


        # Get the arguments and place them into the array
        for i, arg in enumerate(arguments):
            if i < len(arguments) - 1:
                responseDict[arg] = message[message.find(arg) + 1: message.find(arguments[i + 1])]
            else:
                responseDict[arg] = message[message.find(arg) + 1:]

            responseDict[arg] = float(responseDict[arg])

        return responseDict




