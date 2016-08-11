import json
import sys
from time import sleep
from Logic.Environment import Environment
from Logic.Interpreter import Interpreter



taskPath     = "F:\\Google Drive\\Projects\\Git Repositories\\uArmCreatorStudio\\Resources\\Save Files\\test.task"
settingsPath = "F:\\Google Drive\\Projects\\Git Repositories\\uArmCreatorStudio\\Resources\\Settings.txt"
cascadePath  = "F:\\Google Drive\\Projects\\Git Repositories\\uArmCreatorStudio\\Resources\\"
objectsPath  = "F:\\Google Drive\\Projects\\Git Repositories\\uArmCreatorStudio\\Resources\\Objects"


print("Place this .py file in the same directory as uArmCreatorStudio.exe.")
print("Make sure the script works in GUI before trying it here")


# Create the environment. This will connect the robot and camera using Settings.txt
env = Environment(settingsPath=settingsPath, objectsPath=objectsPath, cascadePath=cascadePath)


# Wait for the robot and camera to connect in their seperate threads
print("Waiting 8 seconds for robot and camera to connect")
sleep(8)


# Create the interpreter
interpreter = Interpreter(env)


# Load the .task file you want to run
saveFile = json.load(open(taskPath))


# Load the task into the interpreter, and print the errors
errors = interpreter.initializeScript(saveFile)
print("The following errors occured while initializing the script:\n", errors)
if str(input("Do you want to continue and start the script? (Y/N)")).lower() == "n": sys.exit()

# Before starting script, move the robot to a home position
robot = env.getRobot()
robot.setPos(**robot.home)


# Start the task in another thread
interpreter.startThread(threaded=False)

env.close()
print("Errors during interpreter run: ", interpreter.getExitErrors())
