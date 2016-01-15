import serial
from time import sleep

ser1 = serial.Serial("COM11", 115200, timeout=0)  #Create connection
sleep(.25)
ser1.write("M105\n")
sleep(.25)
ser1.write("G0X0Y0Z-100F20000")
sleep(.25)


serialCommand = raw_input("Command: ")
while not serialCommand == "Exit":
    ser1.write(serialCommand + "\n")
    sleep(.25)
    print ser1.readall()
    serialCommand = raw_input("Command: ")












