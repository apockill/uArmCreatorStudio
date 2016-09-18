# uArm Creator Studio

uArm Creator studio is a visual programming language heavily inspired by YoYo Game Maker, but instead it's for programming robot arms. This software has a heavy emphasis on making computer vision accessible to users, and making it dead simple to program your robot arm to do complex tasks. YoYo Game Maker inspired me as a child because it taught me the basics of programming when I was ten, and let me learn more and more as I grew more experienced. It scales from low experience to high experience applications very well, which is why I thought of it so much while making this. 

I originally started this project because I didn't like how much work it took to get my robot arm to do simple tasks. I wanted a quick and easy way to move the robot to different way-points, and maybe pick up objects and drop them. The project scope quickly evolved, and I decided that I wanted it to be focused heavily on computer vision. I figured that most folks don't have the time to build their own libraries for integrating computer vision with robot arms, and that they might want to just use vision to accomplish simple tasks. However, in order to make this worthwhile, I wanted to make it incredibly easy to use- even for non-programmers- while not alienating experienced programmers.

 Furthermore, I didn't want to spend a huge amount of time making Visual Programming Language (VPL) focused code without also making an equally useful API. Thus, I split the project up into two sections: GUI code, and Logic code. By doing this, it's entirely possible to do everything you could do using the click-and-drag interface, entirely in python script. Furthermore, it's possible to make a script using the GUI then run it without any GUI. 

## Getting Started

Since you're looking at the Github page, I'll assume you don't want to download an .exe and run the program from there, and that you instead want to run it from source. Here's how this goes down!



### Prerequisites

This package uses several libraries within it. It should be entirely multi platform, but I appreciate any feedback that says otherwise.

* python 3.4.4
 * [Download](https://www.python.org/downloads/release/python-344/)

* PyQt5: 
 * [Installation Tutorial](http://pyqt.sourceforge.net/Docs/PyQt5/installation.html)
 
* OpenCV 3.1 
 * [How to for Windows](http://docs.opencv.org/3.1.0/d3/d52/tutorial_windows_install.html#gsc.tab=0) 
 * [How to for Linux](http://docs.opencv.org/trunk/d7/d9f/tutorial_linux_install.html#gsc.tab=0)
* pyserial
 * Use `pip install pyserial` in command line
* numpy
 * Use `pip install numpy` in command line
* PyInstaller (optional)
	* I use PyInstaller to package everything into an EXE. Use my Build.spec file to build everything without hassle, and to include icons.
 

### Installing

Clone the repository, extract it, and keep the structure the same. If you have all of the dependencies and are ready to roll, then open MainGUI.py and run it. Assuming everything works, a window will pop up, and you're in business! If not, email me at Alex.D.Thiel@gmail.com and we can hash out the issue. I'm interested in figuring out what kinds of problems people run into to make the build process easier.

If you have a uArm:
Make sure you have the right communication protocol uploaded onto your uArm's Arduino board, or else this won't work at all. This GUI uses a custom communication protocol (although that might change soon- uFactory is adopting my com protocol). To make sure, go to Robot Firmware and import the approprate libraries from the Libraries To Import folder, and then upload the .ino file in the CommunicationProtocol folder to your uArm.

### Project Structure
The project is seperated by "Logic" and "GUI" elements. This was to force myself to write completely GUI independent logic code, thus you can do anything you can do in the GUI by scripting directly with Logic code. It's a pain, but it's possible!

* Logic Overview
	* Commands.py and Events.py
		* This is where all of the logic for each command and event is defined. If you make a custom Command, you must have a CommandsGUI.py implimentation and a Commands.py implimentation, with the same name- that's how the Interpreter instantiates the object from a string. Vice versa for creating custom Events
	* Environment.py
		* This is a singleton object that holds the Robot, VideoStream, Settings, and ObjectManager classes.
		* This was done since commands and events need various things during instantiation, and environment is a great way to pass them around. Furthermore, it simplified the seperation of Logic and GUI tremendously.
	* Interpreter.py
		* This is, well, the interpreter of the project. When you press "play" on the gui, all of the code gets saved as a JSON, the exact same as the save format the project uses, then passed to the Interpreter, which then instantiates all of the events from Events.py and commands from Commands.py.
		* The Interpreter can be run threaded or not threaded. It's designed for both.
		* The Interpreter can run interpreters within it. This is how the "Run Task" and "Run Function" commands work- by generating an interpreter with a seperate script and running it.
		* Interpreters can run recursively, as well, and catch recursion limit exceptions and call for the script to end.
		* The interpreter also handles the namespace for variables that are created and used during the script. It has a function to reset the namespace as well.
		* Since exec and eval functions are used in the Interpreter, it is incredibly unsafe to run anyone elses .task files without checking the commands to make sure they are safe. Just like running code from someone else, make sure to check it first! I am not responsible for what other people do with this software.
	* Vision.py
		* This handles all vision requests throughout the GUI.
		* All tracking in the GUI works as such: You "add" a target to track, and vision passes work off to a VideoStream thread to look for objects. Then, you query Vision if the object has been seen recently, and it will look through a history of "tracked" objects, and tell you the latest time the object was seen, it's position, orientation, and accuracy. More info in the module.
		* It holds the definitions of PlaneTracker and CascadeTracker, which are the trackers I use for different tracking tasks. Almost all tracking is done with PlaneTracker, but I do face tracking/eye tracking/smile tracking using CascadeTracker. These trackers should not be called directly, always use the functions inside of Vision to use them.
	* Video.py
		* This holds VideoStream, which is my threaded video capturing class, which can also do computer vision work by passing "work" functions, or "filter" functions to the VideoStream. No Vision code is actually in here.
	* Robot.py
		* This is a wrapper around CommunicationProtocol.py which caches position and makes moving easy.
		* Since connecting to Serial can take a while, it has a threaded connection function, which should last 1-5 seconds then end the thread. Thus, all functions designed to be thread safe.
	* CommunicationProtocol.py
		* This is what you change if you want to make a custom robot arm compatible with this software.
		* It's also thread-safe. I still don't recommend abusing that though, since I can't imagine a use case for sending commands from two seperate threads.
	* RobotVision.py
		* This is a module that has functions that use both the Robot and Vision. It's a convenient way to reuse complex vision/robot functions instead of having repetative code in Commands.py
	* ObjectManager.py and Resources.py
		* ObjectManager is what handles the saving and loading of things like Motion recordings, Vision objects, Functions, or whatever else might be added in the future.
		* Resources.py is where the Trackable, MotionPath, Function objects are defined. All new resources should be defined in Resources.py, because that's where ObjectManager searches when instantiating objects. It parses the filename, the first word is the "type", then checks Resources.py to see if that type exists, and if it does, it creates that object and gives it the directory to load it's information from.
	* Global.py
		* Holds a custom print function, which can redirect prints to the GUI's console when the GUI is being used.
* GUI Overview
 * MainGUI.py
	  * Handles the main window, settings page, and is the center for all things GUI
 * ControlPanelGUI.py
	 * This contains the EventList, CommandList, and the ControlPanel widgets, which are essential. EventList is the list that holds the events, to the left of the CommandList.   Each "Event" item holds its own individual CommandList reference. The ControlPanel handles which CommandList is currently in view.
 * CommandsGUI.py
	 * Stores all of the windows for the commands, and the click-and-drag aspect of things. If you want to add a new command, you go here first.
 * EventsGUI.py
	 * Stores all of the Events that can be placed in the program. If you want to add a new event, you go here first.
 * CalibrationsGUI.py
	 * This holds the window and logic for calibrations that the user can do with the robot. If you want to run without a GUI, just use the GUI for calibration which get automatically saved in Resources/Settings.txt, then run your script using the saved calibration.
 * ObjectManagerGUI.py
	 * This handles the "Resources" menu on the toolbar, and works with ObjectManager.py to save new objects.
 * CommonGUI and CameraGUI:
	 * These are convenient widgets I use throughout the project.
 * Paths.py
	 * What you would expect- holds paths for icons and other GUI elements.

## Authors
**Alex Thiel**

I'm a student studying a bachelors in robotics at ASU. I'm working as a Software Engineer at uFactory, developing
uArm Creator Studio.

[Github](https://github.com/apockill)

[Youtube](https://www.youtube.com/channel/UCIZ37TU8Exl6Pr-m2SSN-DA)

Contact me at Alex.D.Thiel@Gmail.com

## Contributing
**王诗阳 Shiyang Wang** - *Icon Design*

**[Tyler Compton](https://github.com/velovix)** - *Created the UCS icon, provided valuable advice for certain language design questions, and helped in many other ways.*


## License

This project is called uArmCreatorStudio. uArmCreatorStudio is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version. uArmCreatorStudio is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with uArmCreatorStudio. If not, see <http://www.gnu.org/licenses/>.

## Acknowledgments

Thank you to everyone at uFactory for giving me free reign over this project during my internship, and allowing me the space to be creative and develop new ideas without fear of the consequences of failure.

Special thanks to 周亚琴 Poppy Zhou and 罗俊茂 Lorder Luo for helping me at every step of the way with marketing, promotion, bug testing, and much much more.