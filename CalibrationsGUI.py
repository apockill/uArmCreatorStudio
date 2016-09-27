"""
This software was designed by Alexander Thiel
Github handle: https://github.com/apockill
Email: Alex.D.Thiel@Gmail.com


The software was designed originaly for use with a robot arm, particularly uArm (Made by uFactory, ufactory.cc)
It is completely open source, so feel free to take it and use it as a base for your own projects.

If you make any cool additions, feel free to share!


License:
    This file is part of uArmCreatorStudio.
    uArmCreatorStudio is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    uArmCreatorStudio is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with uArmCreatorStudio.  If not, see <http://www.gnu.org/licenses/>.
"""
import CommandsGUI
import EventsGUI
import Paths
import numpy             as np
from time                import sleep  # Used only for waiting for robot in CoordCalibrations
from PyQt5               import QtCore, QtWidgets, QtGui
from CameraGUI           import CameraSelector
from Logic.Global        import printf
from Logic.Resources     import TrackableObject

__author__ = "Alexander Thiel"



class CalibrateWindow(QtWidgets.QDialog):
    """
    This is the dashboard where the user can calibrate different aspects of their robot.
    Things like motion calibration for the camera, color calibration, focus calibration, and maybe even eventually
    visual servo-ing calibrations
    """

    def __init__(self, coordSettings, motionSettings, environment, parent):
        super(CalibrateWindow, self).__init__(parent)
        self.motionSettings = motionSettings
        self.coordSettings  = coordSettings

        self.env            = environment

        # Use this when the user doesn't have the appropriate requirements for a calibration
        okBtn = QtWidgets.QMessageBox.Ok
        self.showError   = lambda message: QtWidgets.QMessageBox.question(self, 'Error', message, okBtn)
        self.cameraError = lambda: self.showError("A camera must be connected to run this calibration.")
        self.robotError  = lambda: self.showError("A robot must be connected to run this calibration.")

        self.nextStep    = lambda message: QtWidgets.QMessageBox.question(self, 'Instructions', message, okBtn)


        # The label for the current known information for each calibration test. Label is changed in updateLabels()
        self.motionLbl = QtWidgets.QLabel("No information for this calibration")
        self.coordLbl  = QtWidgets.QLabel("No information for this calibration")
        self.initUI()

        self.updateLabels()

    def initUI(self):
        def createIconLayout(commandOrEvent):
            # Returns a QLabel with a pixmap set with a picture from the specified path, and a caption to go next to it
            title = commandOrEvent.title
            icon  = QtGui.QPixmap(commandOrEvent.icon)
            pictureLbl = QtWidgets.QLabel()
            pictureLbl.setPixmap(icon)

            layout = QtWidgets.QHBoxLayout()
            layout.addWidget(pictureLbl)
            return layout

        motionBtn = QtWidgets.QPushButton("Calibrate Motion Detection")
        coordBtn  = QtWidgets.QPushButton("Calibrate Camera/Robot Position")
        cancelBtn = QtWidgets.QPushButton("Cancel")
        applyBtn  = QtWidgets.QPushButton("Apply")


        motionBtn.clicked.connect(self.calibrateMotion)
        coordBtn.clicked.connect(self.calibrateCoordinates)
        applyBtn.clicked.connect(self.accept)
        cancelBtn.clicked.connect(self.reject)


        maxWidth  = 250
        motionBtn.setFixedWidth(maxWidth)
        coordBtn.setFixedWidth(maxWidth)
        cancelBtn.setFixedWidth(130)
        applyBtn.setFixedWidth(130)

        # Add the relevant claibration buttons and labels here
        row1 = QtWidgets.QHBoxLayout()
        row2 = QtWidgets.QHBoxLayout()
        row3 = QtWidgets.QHBoxLayout()
        row4 = QtWidgets.QHBoxLayout()

        row1.addWidget(      coordBtn)
        row1.addStretch(1)
        row1.addWidget( self.coordLbl)

        row2.addStretch(1)
        row2.addLayout(createIconLayout(CommandsGUI.MoveRelativeToObjectCommand))
        row2.addLayout(createIconLayout(CommandsGUI.MoveWristRelativeToObjectCommand))
        row2.addLayout(createIconLayout(CommandsGUI.PickupObjectCommand))
        row2.addLayout(createIconLayout(CommandsGUI.TestObjectAngleCommand))



        row3.addWidget(     motionBtn)
        row3.addStretch(1)
        row3.addWidget(self.motionLbl)

        row4.addStretch(1)
        row4.addLayout(createIconLayout(EventsGUI.MotionEvent))



        # Place the rows into the middle layout.
        middleVLayout = QtWidgets.QVBoxLayout()
        middleVLayout.addLayout(row1)
        middleVLayout.addLayout(row2)
        middleVLayout.addSpacing(50)
        middleVLayout.addLayout(row3)
        middleVLayout.addLayout(row4)
        middleVLayout.addStretch(1)


        # Set up Cancel and Apply buttons
        leftVLayout = QtWidgets.QVBoxLayout()
        leftVLayout.addStretch(1)
        leftVLayout.addWidget(cancelBtn, QtCore.Qt.AlignRight)
        rightVLayout = QtWidgets.QVBoxLayout()
        rightVLayout.addStretch(1)
        rightVLayout.addWidget(applyBtn, QtCore.Qt.AlignLeft)


        # Create the final layout with the leftVLayout, middleVLayout, and rightVLayout
        mainHLayout = QtWidgets.QHBoxLayout()
        mainHLayout.addStretch(3)
        mainHLayout.addLayout(leftVLayout)
        mainHLayout.addLayout(middleVLayout)
        mainHLayout.addLayout(rightVLayout)
        mainHLayout.addStretch(3)

        self.setMinimumHeight(400)
        self.setLayout(mainHLayout)
        self.setWindowTitle('Calibrations')
        self.setWindowIcon(QtGui.QIcon(Paths.calibrate))


    def updateLabels(self):
        # Check if motionCalibrations already exist
        movCalib = self.motionSettings
        if movCalib["stationaryMovement"] is not None:
            self.motionLbl.setText(" Stationary Movement: " + str(movCalib["stationaryMovement"]) +
                                   "     Active Movement: " + str(movCalib["activeMovement"]))

        coordCalib = self.coordSettings
        if coordCalib["ptPairs"] is not None:
            self.coordLbl.setText("Calibration has been run before. " + str(len(coordCalib["ptPairs"])) +
                                  " points of data were collected.")

    def calibrateMotion(self):
        # Shake the robot left and right while getting frames to get a threshold for "high" movement between frames
        showStep = lambda step, message: QtWidgets.QMessageBox.question(self, 'Step ' + str(step),
                                                                        'Step ' + str(step) + "\n\n" + message,
                                                                        QtWidgets.QMessageBox.Ok)

        vStream = self.env.getVStream()
        vision  = self.env.getVision()
        robot   = self.env.getRobot()

        # Check that there is a valid camera connected
        if not vStream.connected():
            printf("GUI| No Camera Connected!")
            self.cameraError()
            return

        # Check that there is a valid robot connected
        if not robot.connected():
            printf("GUI| No uArm connected!")
            self.robotError()
            return


        showStep(1, "Do not make any movement in the cameras view until the next message appears.")

        # Get movement while nothing is happening
        totalMotion = 0.0
        samples     = 75
        for i in range(0, samples):
            vision.waitForNewFrames()
            totalMotion += vision.getMotion()
        noMovement = totalMotion / samples


        # Get movement while robot is moving
        totalMotion = 0.0
        moves       = 10
        samples     = 0
        direction   = 1  #If the robot is going right or left next

        # Start position
        robot.setSpeed(22)
        robot.setActiveServos(all=True)
        robot.setPos( x=-15, y=robot.home["y"], z=robot.home["z"])

        # Move robot left and right while getting new frames for "moves" amount of samples
        for move in range(0, moves):

            robot.setPos(x=30 * direction, y=0, z=0, relative=True, wait=False)   #end position
            sleep(.1)
            while robot.getMoving():
                vision.waitForNewFrames()
                newMotion = vision.getMotion()
                if newMotion > noMovement:
                    totalMotion += vision.getMotion()
                    samples += 1

            direction *= -1


        # Make sure samples were retrieved. If not, discard the calib information and exit.
        if samples == 0: return


        # Calculate average amount of motion when robot is moving rapidly
        highMovement = totalMotion / samples


        self.motionSettings["stationaryMovement"] = round(  noMovement, 1)
        self.motionSettings["activeMovement"]     = round(highMovement, 1)


        self.updateLabels()
        printf("GUI| Function complete! New settings: ", noMovement, ", ", highMovement)

    def calibrateCoordinates(self):
        vStream      = self.env.getVStream()
        robot        = self.env.getRobot()
        objManager   = self.env.getObjectManager()
        robotTracker = objManager.getObject("Robot Marker")

        # If Camera not connected
        if not vStream.connected():
            self.cameraError()
            return

        # If robot not connected
        if not robot.connected():
            self.robotError()
            return

        # If Robot Marker trackable object doesn't exist
        startFromScratch = True  # Whether or not the user skip to automated calibration or not
        if robotTracker is not None:

            message = QtWidgets.QMessageBox()
            message.setWindowTitle("Skip to Calibration?")
            message.addButton(QtWidgets.QPushButton('I want to set a new Robot Marker'), QtWidgets.QMessageBox.YesRole)
            message.addButton(QtWidgets.QPushButton('Skip to Automatic Calibration'), QtWidgets.QMessageBox.NoRole)
            message.setText("It appears this is not the first time you have run this tutorial.\n\n" +
                            "Would you like to start from scratch, or skip to the automated calibration?\n\n" +
                            "(Automated calibration only works if the robot has the same marker on the top" +
                            " of its head as it did when you first ran this calibration.)\n")
            reply = message.exec_()

            # QtWidgets.QMessageBox.addButton
            if reply == 0: startFromScratch = True
            if reply == 1: startFromScratch = False


        coordWizard = CoordWizard(self.env, startFromScratch, parent=self)
        coordWizard.exec_()
        coordWizard.close()
        coordWizard.deleteLater()

        # If the user finished the wizard correctly, then continue
        if coordWizard.result():
            newCoordCalib   = coordWizard.getNewCoordCalibrations()
            self.coordSettings["ptPairs"] = newCoordCalib["ptPairs"]
            self.coordSettings["failPts"] = newCoordCalib["failPts"]

            newGroundCalib = coordWizard.getNewGroundCalibration()
            self.coordSettings["groundPos"] = newGroundCalib

        self.updateLabels()

    def getMotionSettings(self):
        return self.motionSettings

    def getCoordSettings(self):
        return self.coordSettings

    def getSettings(self):
        pass




class CoordWizard(QtWidgets.QWizard):
    def __init__(self, environment, startFromScratch, parent):
        super(CoordWizard, self).__init__(parent)

        self.allPages = startFromScratch

        self.env = environment  # Used in close event to shut down vision

        # Set the robot to the home position
        robot = environment.getRobot()
        robot.setActiveServos(all=True)
        robot.setPos(**robot.home)
        robot.setActiveServos(all=False)

        # Create the wizard pages and add them to the sequence
        if self.allPages:
            self.page3 = CWPage3(parent=self)
            self.page4 = CWPage4(environment, parent=self)

        self.page1 = CWPage1(parent=self)
        self.page2 = CWPage2(robot, parent=self)
        self.page5 = CWPage5(environment, self.getNewGroundCalibration, parent=self)
        self.button(QtWidgets.QWizard.NextButton).clicked.connect(lambda: self.page2.nextPressed(self.currentId()))


        self.addPage(self.page1)
        self.addPage(self.page2)
        if self.allPages:
            self.addPage(self.page3)
            self.addPage(self.page4)
        self.addPage(self.page5)


        # Aesthetic details
        self.setWindowTitle("Coordinate Calibration Wizard")
        self.setWindowIcon(QtGui.QIcon(Paths.objectWizard))

    def getNewCoordCalibrations(self):
        return self.page5.newCalibrations

    def getNewGroundCalibration(self):
        return self.page2.groundCoords


    def closeEvent(self, event):
        # Close any pages that have active widgets, such as the cameraWidget. This will trigger each page's close func.
        self.page1.close()
        self.page2.close()
        if self.allPages:
            self.page3.close()
            self.page4.close()
        self.page5.close()

        vision = self.env.getVision()
        vision.endAllTrackers()

class CWPage1(QtWidgets.QWizardPage):
    def __init__(self, parent):
        super(CWPage1, self).__init__(parent)

        # Create GUI objects

        self.initUI()

    def initUI(self):

        prompt = "The algorithms in this software will only work if the\n"    \
                 "camera is placed above the robot, and doesn't move. \n\n"   \
                 "Please find a way to mount your webcam above the robot,\n"  \
                 "in such a way that it has a wide field of view of the\n"    \
                 "robots workspace.\n"                                        \


        welcomeLbl = QtWidgets.QLabel("Welcome Coordinate Calibration Wizard!\n")
        introLbl   = QtWidgets.QLabel("This will walk you through teaching the camera the position of the robot.")
        step1Lbl   = QtWidgets.QLabel("\n\nStep 1: Setup")
        promptLbl  = QtWidgets.QLabel(prompt)
        imageLbl   = QtWidgets.QLabel()

        imageLbl.setPixmap(QtGui.QPixmap(Paths.help_cam_overview))

        # Set titles bold
        bold = QtGui.QFont()
        bold.setBold(True)
        step1Lbl.setFont(bold)

        # Make the title larger than everything else
        bold.setPointSize(15)
        welcomeLbl.setFont(bold)


        # Place the GUI objects vertically
        stepCol  = QtWidgets.QVBoxLayout()
        stepCol.addWidget(step1Lbl)
        stepCol.addWidget(promptLbl)
        stepCol.addStretch(1)

        imageCol = QtWidgets.QVBoxLayout()
        imageCol.addWidget(imageLbl)

        stepRow = QtWidgets.QHBoxLayout()
        stepRow.addLayout(stepCol)
        stepRow.addStretch(1)
        stepRow.addLayout(imageCol)



        mainVLayout = QtWidgets.QVBoxLayout()
        mainVLayout.addWidget(welcomeLbl)
        mainVLayout.addWidget(introLbl)
        mainVLayout.addLayout(stepRow)

        # self.setMinimumHeight(750)
        # self.setMinimumWidth(700)
        self.setLayout(mainVLayout)

class CWPage2(QtWidgets.QWizardPage):
    def __init__(self, robot, parent):
        super(CWPage2, self).__init__(parent)


        # This is set in self.nextPressed
        self.robot = robot
        self.groundCoords = None
        self.initUI()

    def initUI(self):

        prompt = "Mount the robot to the ground so that it doesn't move\n"         \
                 "around, to avoid doing this calibration every time the \n"        \
                 "robot is moved.\n\n"                                          \
                 "Without moving the robots base, lower the head of the robot \n"   \
                 "until the suction cup is barely touching the ground, as shown\n"  \
                 "on the video to the right.\n\n"                                   \
                 "Make sure the top of the robots head is still near the \n"        \
                 "center of the cameras view, and the sucker is touching the\n" \
                 "ground."


        step1Lbl   = QtWidgets.QLabel("\n\nStep 2: Robot Placement")
        promptLbl  = QtWidgets.QLabel(prompt)
        movieLbl   = QtWidgets.QLabel("Could not find example gif")


        # Set the animated gif on the movieLbl
        movie = QtGui.QMovie(Paths.help_lower_head)
        movieLbl.setMovie(movie)
        movie.start()


        # Set titles bold
        bold = QtGui.QFont()
        bold.setBold(True)
        step1Lbl.setFont(bold)

        # Place the GUI objects vertically
        col1  = QtWidgets.QVBoxLayout()
        col1.addWidget(step1Lbl)
        col1.addWidget(promptLbl)
        col1.addStretch(1)

        col2 = QtWidgets.QVBoxLayout()
        col2.addWidget(movieLbl)
        col2.addStretch(1)



        mainHLayout = QtWidgets.QHBoxLayout()
        mainHLayout.addLayout(col1)
        mainHLayout.addLayout(col2)

        self.setLayout(mainHLayout)

    def nextPressed(self, currentID):
        # If next is pressed, warn the user about placing the robots head on the ground

        if currentID == 2:
            self.robot.setActiveServos(all=False)
            warn = QtWidgets.QMessageBox()
            warn.setWindowTitle("Getting Height of Ground")
            warn.addButton(QtWidgets.QPushButton('Yes, the end effector is touching the ground'),
                           QtWidgets.QMessageBox.YesRole)
            warn.setText("Important!\nBefore continuing, make sure the robots end effector is touching the ground, "
                         "and that it is centered below the camera. The program will read the robots coordinates.\n\n")
            reply = warn.exec_()


            # Get several samples of the robots current position, and put the average into self.groundCoords
            samples = 10
            sumCoords = np.float32([0, 0, 0])
            for i in range(0, samples):
                coord = self.robot.getCoords()
                sumCoords += np.float32(coord)
            self.groundCoords = list(map(float, sumCoords / samples))
            self.robot.setPos(z=self.groundCoords[2] + .5)
            self.robot.setActiveServos(servo0=False)
            printf("GUI| New ground coordinates set: ", self.groundCoords)

class CWPage3(QtWidgets.QWizardPage):
    def __init__(self, parent):
        super(CWPage3, self).__init__(parent)

        self.initUI()

    def initUI(self):

        prompt = "In order to track the robot, there must be a marker of some\n"    \
                 "sort on the robot. If you have a QR code or detailed \n"          \
                 "sticker, then place it on the robots head.\n\n"                   \
                 "If you do not have anything readily avaliable, get a piece \n"    \
                 "of tape- make sure it's not reflective (non plastic tape is\n"    \
                 "best), draw on it (as show on the right), and place it on\n"      \
                 "the robots head.\n\n"                                             \
                 "There must be a lot of detail on the marker in order to\n"        \
                 "track properly. If you finish this tutorial and tracking is\n"    \
                 "not sufficient, then draw on the marker to add more detail."


        step1Lbl   = QtWidgets.QLabel("\n\nStep 3: Make a Robot Marker")
        promptLbl  = QtWidgets.QLabel(prompt)
        imgOneLbl  = QtWidgets.QLabel()
        imgTwoLbl  = QtWidgets.QLabel()



        # Set the images on the img labels
        imgOneLbl.setPixmap(QtGui.QPixmap(Paths.help_make_sticker))
        imgTwoLbl.setPixmap(QtGui.QPixmap(Paths.help_marker_on_head))

        # Set titles bold
        bold = QtGui.QFont()
        bold.setBold(True)
        step1Lbl.setFont(bold)

        # Place the GUI objects vertically
        col1  = QtWidgets.QVBoxLayout()
        col1.addWidget(step1Lbl)
        col1.addWidget(promptLbl)
        col1.addStretch(1)

        col2 = QtWidgets.QVBoxLayout()
        col2.addWidget(imgOneLbl)
        col2.addWidget(imgTwoLbl)
        col2.addStretch(1)

        mainHLayout = QtWidgets.QHBoxLayout()
        mainHLayout.addLayout(col1)
        mainHLayout.addLayout(col2)

        self.setLayout(mainHLayout)

class CWPage4(QtWidgets.QWizardPage):

    def __init__(self, environment, parent):
        super(CWPage4, self).__init__(parent)

        # The final object is stored here:
        self.newRobotMrkr    = None

        # Create global GUI objects
        self.hintLbl  = QtWidgets.QLabel("")  # This will tell the user how many points are on the object
        self.movieLbl = QtWidgets.QLabel("")  # Changes the gif depending on what the user is having trouble with
        self.selMovie = QtGui.QMovie(Paths.help_sel_marker)  # Help with selecting the marker
        self.detMovie = QtGui.QMovie(Paths.help_add_detail)  # Help with adding detail to marker


        # Get the Environment objects that will be used
        self.vision       = environment.getVision()
        self.robot        = environment.getRobot()
        self.objManager   = environment.getObjectManager()

        # Create the camera widget and set it up
        self.cameraWidget = CameraSelector(environment.getVStream(), parent=self)
        self.cameraWidget.play()
        self.cameraWidget.objSelected.connect(self.objectSelected)

        self.initUI()

    def initUI(self):
        prompt = "Make sure the robot's head is in the center of the camera view. Then, click the mouse on the top "  +\
                 "\nright corner of the marker, and drag it to the bottom right corner of the marker.\n\n"            +\
                 "The camera will begin tracking the marker. Try to have more than 500 points on the marker. Move\n"  +\
                 "the robot around and make sure that the object can be recognized for the majority of the cameras\n" +\
                 "view.\n"

        stepLbl    = QtWidgets.QLabel("Step 4: Selecting the Marker")
        promptLbl  = QtWidgets.QLabel(prompt)


        # Set the animated gif on the movieLbl

        self.movieLbl.setMovie(self.selMovie)
        self.selMovie.start()
        self.detMovie.start()


        # Set titles bold
        bold = QtGui.QFont()
        bold.setBold(True)
        stepLbl.setFont(bold)
        self.hintLbl.setFont(bold)

        # Create a special row for the camera that will force it to remain in the center, regardless of size changes
        camRow = QtWidgets.QHBoxLayout()
        camRow.addWidget(self.cameraWidget)
        camRow.addStretch(1)
        camRow.addWidget(self.movieLbl)

        # Place the GUI objects vertically
        col1 = QtWidgets.QVBoxLayout()
        col1.addWidget(stepLbl)
        col1.addWidget(promptLbl)
        col1.addWidget(self.hintLbl)
        col1.addLayout(camRow)

        mainHLayout = QtWidgets.QHBoxLayout()
        mainHLayout.addLayout(col1)

        self.setLayout(mainHLayout)

    def objectSelected(self):
        """
            Runs when the user has selected an object on the CameraSelector widget.
            It will verify if the object is trackable (has enough points), if so, it will set the vision to tracking
            mode, generate a "trackable" object, and set the camera to play.

            Then, it will display information about the object next to the camera, so that the user can decide if
            they want to keep this selected object or try again.

            If there are not enough keypoints, the program will warn the user that this is a bad idea. If there are
            zero keypoints, it won't allow the user to track it, and will automatically revert the camera to
            selection mode.
        """

        # Reset any previous markers
        self.newRobotMrkr = None
        self.completeChanged.emit()
        self.hintLbl.setText("")
        self.vision.endAllTrackers()
        self.movieLbl.setMovie(self.selMovie)
        self.movieLbl.show()

        rect     = self.cameraWidget.getSelectedRect()
        frame    = self.cameraWidget.getSelectedFrame()
        h, w, _  = frame.shape

        # Get the "target" object from the image and rectangle
        trackable = TrackableObject("Robot Marker")
        trackable.addNewView(image      = frame,
                             rect       = rect,
                             pickupRect = [0, 0, h, w],
                             height     = 0)

        target = self.vision.planeTracker.createTarget(trackable.getViews()[0])

        # Analyze it, and make sure it's a valid target. If not, return the camera to selection mode.
        if len(target.descrs) == 0 or len(target.keypoints) == 0:
            self.cameraWidget.takeAnother()
            self.hintLbl.setText("You must select an object with more detail.")
            return

        if len(target.descrs) < 450:
            self.movieLbl.setMovie(self.detMovie)
            self.hintLbl.setText("Your selected marker does not have enough detail. Only " + str(len(target.descrs)) +
                                 " points were found.\nAdd detail to your marker and try again.")
            self.cameraWidget.takeAnother()
            return

        self.objManager.deleteObject("Robot Marker")  # Delete any previous end effector file
        self.newRobotMrkr = trackable
        self.objManager.saveObject(self.newRobotMrkr)
        self.completeChanged.emit()


        # If the object was not very good, warn the user. Otherwise, state the # of points on the object
        if len(target.descrs) < 600:
            self.movieLbl.setMovie(self.detMovie)
            self.hintLbl.setText("Your selected marker is not very detailed, or is too small, only " +
                                 str(len(target.descrs)) + " points were found.\n"
                                 "Tracking may not be very accurate.")
        else:
            self.hintLbl.setText("Found " + str(len(target.descrs)) + " Points")

        # Turn on the camera, and start tracking
        self.cameraWidget.play()
        self.vision.addTarget(self.newRobotMrkr)

    def isComplete(self):
        return self.newRobotMrkr is not None

    def close(self):
        self.cameraWidget.close()
        self.vision.endAllTrackers()

class CWPage5(QtWidgets.QWizardPage):

    def __init__(self, environment, getGroundCoord, parent):
        super(CWPage5, self).__init__(parent)

        # Initialize Globals
        self.env             = environment
        self.getGroundCoord  = getGroundCoord  # This is used to pull a value from a previous QWizard page
        self.testRunning     = False  # Keeps track if there's a test currently running, to not have multiple ongoing
        self.cancelTest      = True   # Used when dialog is closed to stop the calibration
        self.newCalibrations = None   # The final caibration JSON to go into settings. Set in endCalibration.


        # Initialize GUI globals
        self.startBtn       = QtWidgets.QPushButton("Start Calibration")
        self.hintLbl        = QtWidgets.QLabel("\n\n\n\n\n\t\t\t\t")  # Add newlines since window resizing is broken
        self.testLbl        = QtWidgets.QLabel()        # Updates during calibration to notify user of progress
        self.progressBar    = QtWidgets.QProgressBar()  # Tells the user how far the calibration is from completion
        self.timer          = None   # Used to hold singleshot timers for getPoint during calibration

        self.startBtn.clicked.connect(self.startCalibration)
        self.initUI()

    def initUI(self):
        self.startBtn.setMaximumWidth(130)
        self.progressBar.setMinimum(0)
        self.progressBar.hide()
        self.testLbl.hide()

        prompt = "When you press the Start Calibration button, the robot will go through a set of predefined moves\n"\
                 "and record the information that it needs." \
                 "Before beginning:\n\n\n" \
                 "1) Make sure that the robot's head is more or less centered under the cameras view, and the\n" \
                 "    Robot Marker is being tracked.\n" \
                 "2) Make sure there is ample space for the robot to move around.\n" \
                 "3) Make sure the robot is immobile, and mounted to the ground. If you move the robot,\n" \
                 "    you will have to re-run this calibration.\n"

        step1Lbl   = QtWidgets.QLabel("\n\nFinal Step:")
        promptLbl  = QtWidgets.QLabel(prompt)

        # Set titles bold
        bold = QtGui.QFont()
        bold.setBold(True)
        step1Lbl.setFont(bold)
        self.hintLbl.setFont(bold)

        # Place the GUI objects vertically
        col1  = QtWidgets.QVBoxLayout()
        col1.addWidget(step1Lbl)
        col1.addWidget(promptLbl)
        col1.addStretch(1)
        col1.addWidget(self.testLbl)
        col1.addWidget(self.progressBar)
        col1.addWidget(self.hintLbl)
        col1.addWidget(self.startBtn)


        mainHLayout = QtWidgets.QHBoxLayout()
        mainHLayout.addLayout(col1)

        self.setLayout(mainHLayout)


    def startCalibration(self):

        if self.testRunning is True: return

        # Pull from the environment and start the tracking
        robot      = self.env.getRobot()
        vision     = self.env.getVision()
        objManager = self.env.getObjectManager()


        #   Start tracking the robots marker
        rbMarker = objManager.getObject("Robot Marker")
        vision.endAllTrackers()
        vision.addTarget(rbMarker)


        # Set the robot to the home position, set the speed, and other things for the calibration
        robot.setActiveServos(all=True)
        robot.setSpeed(10)

        # Move the robot up a certain offset from the ground coordinate
        zLower = float(round(self.getGroundCoord()[2] + 2.0, 2))
        robot.setPos(x=robot.home["x"], y=robot.home["y"], z=zLower)
        sleep(1)


        # Generate a large set of points to test the robot, and put them in testCoords
        testCoords    = []

        # Test the z on 3 xy points
        zTest = int(round(zLower, 0))  # Since range requires an integer, round zLower just for this case
        for x in range(  -20, 20, 4): testCoords += [[x,  15,    11]]  # Center of XYZ grid
        for y in range(    8, 24, 4): testCoords += [[ 0,  y,    11]]
        for z in range(zTest, 19, 1): testCoords += [[ 0, 15,     z]]

        # for x in range(  -20, 20, 1): testCoords += [[x,  15, zTest]]  # Center of XY, Bottom z
        # for y in range(    8, 25, 1): testCoords += [[ 0,  y, zTest]]
        # for z in range(zTest, 25): testCoords += [[ 0, 15,     z]]

        for x in range(  -20, 20, 4): testCoords += [[x,  15,    17]]  # Center of XY, top z
        for y in range(   12, 24, 4): testCoords += [[ 0,  y,    17]]



        direction  = int(1)
        for y in range(12, 25, 2):
            for x in range(-20 * direction, 20 * direction, 2 * direction):
                testCoords += [[x, y, zTest]]
            direction *= -1



        printf("GUI| Testing ", len(testCoords), " coordinate points")


        # Begin testing every coordinate in the testCoords array, and recording the results into newCalibrations
        self.cancelTest  = False
        self.testRunning = True
        self.hintLbl.setText("")
        self.testLbl.setText("")
        self.progressBar.setMaximum(len(testCoords))
        self.progressBar.setValue(0)
        self.progressBar.show()
        self.testLbl.show()
        self.startBtn.hide()
        getFirstPoint = lambda: self.getPoint(0, [], {"ptPairs": [], "failPts": []}, testCoords)
        self.timer    = QtCore.QTimer.singleShot(10, getFirstPoint)

    def endCalibration(self, errors, newCalibrations, testCoords):
        robot      = self.env.getRobot()
        vision     = self.env.getVision()
        self.testRunning = False
        self.cancelTest  = True
        self.startBtn.show()
        self.testLbl.hide()
        self.progressBar.hide()

        robot.setPos(**robot.home)

        # Prune the list down to 20 less than the original size, find the best set out of those
        minPointCount = 10

        # Check the percent of points that were found vs amount of points that were in the testCoord array
        if len(newCalibrations["ptPairs"]) < minPointCount:
            # If not enough points were found, append an error to the error array
            if len(newCalibrations["ptPairs"]) == 0:
                errors.append("The robot marker was never seen! Try restarting the calibration and creating the"
                        "\n\t  marker again, making sure that the robot's head is in view of the camera."
                        "\n\n\t  Also make sure that the area in the camera view is clear, blank, without too much"
                        "\n\t  detail around it- try having a clear workspace with white paper as a background.")
            else:
                errors.append("The marker was not recognized in enough points- it was only seen "           +
                          str(len(newCalibrations["ptPairs"])) + " time(s)!"
                          "\n\t  It must be seen at least " +
                          str(minPointCount) + " times." +
                          "\n\n\t  Try making sure that the robot's head is centered in the middle of the cameras"
                          "\n\t  view in the previous step, and try placing the camera in a higher location."
                          "\n\n\t  Also make sure that the area around the camera view is clear, blank, without too"
                          "\n\t  much detail around it- try having a clear workspace with white paper as a background.")


        # Return the robot to home and turn off tracking
        vision.endAllTrackers()
        robot.setPos(**robot.home)



        # Print out the errors, and set the appropriate GUI elements
        hintText = ""
        if len(errors):
            hintText += "Calibration did not complete successfully. The following errors occured:\n"
            for error in errors:
                hintText += "\t- " + error + "\n"
            self.newCalibrations = None
            self.startBtn.setText("Try Again")
        else:
            hintText += "Calibration was successful, " + str(len(newCalibrations["ptPairs"])) + "/"  +\
                     str(len(testCoords)) + " points were found.\nResults will be saved when you click Apply " +\
                     "on the calibrations page. Feel free to try this again.\n" +\
                     "Make sure to repeat this calibration whenever you move your camera or move your robot."
            self.testLbl.setPixmap(QtGui.QPixmap(Paths.help_star))
            self.testLbl.show()
            self.newCalibrations = newCalibrations
            self.startBtn.setDisabled(True)

        self.hintLbl.setText(hintText)
        self.setFixedSize(self.layout().sizeHint())


        # Update the "Finished" button
        self.completeChanged.emit()

    def getPoint(self, currentPoint, errors, newCalibrations, testCoords):
        self.testRunning = True
        if self.cancelTest:
            self.testRunning = False
            return

        # Here we update the GUI element for telling the user how many valid points have been tested, and progress
        successCount = len(newCalibrations["ptPairs"])
        recFailCount = len(newCalibrations["failPts"])
        # print("failcoutn: ", recFailCount)
        text  = "Calibration Progress: \n"
        if currentPoint > len(testCoords) * .25:
            if recFailCount / currentPoint > .85:  # If over 85% of tests failed so far
                text += "    Progress Report: The robot marker has failed to be recognized " + \
                        str(recFailCount) + " times\n"
            else:
                text += "    Progress Report: The calibration is going well.\n"


        text += "    Testing Point:\t" + str(currentPoint) + "/" + str(len(testCoords)) + "\n"
        text += "    Valid Points: \t" + str(successCount) + "\n"
        # text += "    Failed Points:\t" + str(currentPoint - successCount) + "\n"

        self.testLbl.setText(text)


        # Get variables that will be used
        robot      = self.env.getRobot()
        vision     = self.env.getVision()
        rbMarker   = self.env.getObjectManager().getObject("Robot Marker")
        singleShot = lambda: QtCore.QTimer.singleShot(10, lambda: self.getPoint(currentPoint, errors,
                                                                        newCalibrations, testCoords))


        if currentPoint >= len(testCoords):
            self.endCalibration(errors, newCalibrations, testCoords)
            return
        self.progressBar.setValue(currentPoint)
        coord = testCoords[currentPoint]
        currentPoint += 1


        printf("GUI| Testing point ", coord)

        # Move the robot to the coordinate
        robot.setPos(x=coord[0], y=coord[1], z=coord[2])
        vision.waitForNewFrames(3)

        # Now that the robot is at the desired position, get the avg location
        frameAge, marker = vision.getObjectLatestRecognition(rbMarker)


        # Make sure the robot is still connected before checking anything else
        if not robot.connected():
            errors.append("Robot was disconnected during calibration")
            self.endCalibration(errors, newCalibrations, testCoords)
            return


        # Make sure the object was found in a recent frame
        if marker is None or not frameAge < 2:
            printf("GUI| Marker was not recognized.")
            newCalibrations['failPts'].append(coord)
            self.timer = singleShot()
            return


        newCalibrations["ptPairs"].append([marker.center, coord])
        self.timer = singleShot()

    def isComplete(self):

        return self.newCalibrations is not None

    def close(self):
        self.cancelTest = True  # Stops the calibration from creating another singleshot

        vision = self.env.getVision()
        robot  = self.env.getRobot()
        vision.endAllTrackers()
        robot.setPos(wait=False, **robot.home)








