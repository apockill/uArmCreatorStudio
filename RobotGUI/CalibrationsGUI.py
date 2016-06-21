from PyQt5                        import QtCore, QtWidgets, QtGui
from RobotGUI                     import Icons
from RobotGUI.CameraGUI           import CameraSelector
from RobotGUI.Logic.Global        import printf
from RobotGUI.Logic.ObjectManager import TrackableObject
from time                         import sleep  # Used only for waiting for robot in CoordCalibrations, page 5


class CalibrateWindow(QtWidgets.QDialog):
    """
    This is the dashboard where the user can calibrate different aspects of their robot.
    Things like motion calibration for the camera, color calibration, focus calibration, and maybe even eventually
    visual servo-ing calibrations
    """

    def __init__(self, environment, parent):
        super(CalibrateWindow, self).__init__(parent)

        self.env            = environment
        self.newSettings    = self.env.getSettings()

        # Use this when the user doesn't have the appropriate requirements for a calibration
        self.showError   = lambda message: QtWidgets.QMessageBox.question(self, 'Error', message, QtWidgets.QMessageBox.Ok)
        self.cameraError = lambda: self.showError("A camera must be connected to run this calibration.")
        self.robotError  = lambda: self.showError("A robot must be connected to run this calibration.")

        self.nextStep    = lambda message: QtWidgets.QMessageBox.question(self, 'Instructions', message, QtWidgets.QMessageBox.Ok)


        # The label for the current known information for each calibration test. Label is changed in updateLabels()
        self.motionLbl = QtWidgets.QLabel("No information for this calibration")
        self.coordLbl  = QtWidgets.QLabel("No information for this calibration")
        self.initUI()

        self.updateLabels()

    def initUI(self):

        motionBtn = QtWidgets.QPushButton("Calibrate Motion")
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

        row1.addWidget(      coordBtn)
        row1.addStretch(1)
        row1.addWidget( self.coordLbl)

        row2.addWidget(     motionBtn)
        row2.addStretch(1)
        row2.addWidget(self.motionLbl)




        # Place the rows into the middle layout.
        middleVLayout = QtWidgets.QVBoxLayout()
        middleVLayout.addLayout(row1)
        middleVLayout.addLayout(row2)
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
        self.setWindowIcon(QtGui.QIcon(Icons.calibrate))



    def updateLabels(self):
        # Check if motionCalibrations already exist
        movCalib = self.newSettings["motionCalibrations"]
        if movCalib["stationaryMovement"] is not None:
            self.motionLbl.setText(" Stationary Movement: " + str(movCalib["stationaryMovement"]) +
                                   "     Active Movement: " + str(movCalib["activeMovement"]))

    def calibrateMotion(self):
        # Shake the robot left and right while getting frames to get a threshold for "high" movement between frames


        vStream = self.env.getVStream()
        vision  = self.env.getVision()
        robot   = self.env.getRobot()

        # Check that there is a valid camera connected
        if not vStream.connected():
            printf("CalibrateView.calibrateMotion(): No Camera Connected!")
            self.cameraError()
            return

        # Check that there is a valid robot connected
        if not robot.connected():
            printf("CalibrateView.calibrateMotion(): No uArm connected!")
            self.robotError()
            return

        # Make sure VideoStream is collecting new frames
        vStream.setPaused(False)


        # Get movement while nothing is happening
        totalMotion = 0.0
        samples     = 75
        for i in range(0, samples):
            vStream.waitForNewFrame()
            totalMotion += vision.getMotion()
        noMovement = totalMotion / samples


        # Get movement while robot is moving
        totalMotion = 0.0
        moves       = 10
        samples     = 0
        direction   = 1  #If the robot is going right or left next

        # Start position
        robot.setPos( x=-15, y=-15, z=20)
        robot.refresh()

        # Move robot left and right while getting new frames for "moves" amount of samples
        for move in range(0, moves):
            robot.setPos(x=30 * direction, y=0, z=0, relative=True)   #end position

            while robot.getMoving():
                vStream.waitForNewFrame()
                totalMotion += vision.getMotion()
                samples += 1

            direction *= -1

        # Calculate average amount of motion when robot is moving rapidly
        highMovement = totalMotion / samples


        self.newSettings["motionCalibrations"]["stationaryMovement"] = round(  noMovement, 1)
        self.newSettings["motionCalibrations"]["activeMovement"]     = round(highMovement, 1)

        # Return the vStream to paused
        vStream.setPaused(True)
        self.updateLabels()
        printf("CalibrateView.calibrateMotion(): Function complete! New motion settings: ", self.newSettings)

    def calibrateCoordinates(self):
        vStream      = self.env.getVStream()
        vision       = self.env.getVision()
        robot        = self.env.getRobot()
        objManager   = self.env.getObjectManager()
        robotTracker = objManager.getObject("Robot Marker")

        # If Camera not connected
        # if vStream.connected():
        #     self.cameraError()
        #     return
        #
        # # If robot not connected
        # if not robot.connected():
        #     self.robotError()
        #     return
        #
        # If "Robot Marker" object doesn't exist
        startFromScratch = True  # Whether or not the user skip to automated calibration or not
        if robotTracker is not None:


            message = QtWidgets.QMessageBox()
            message.setWindowTitle("Skip to Calibration?")
            message.addButton(QtWidgets.QPushButton('I want to set a new Robot Marker'), QtWidgets.QMessageBox.YesRole)
            message.addButton(QtWidgets.QPushButton('Skip to Automatic Calibration'), QtWidgets.QMessageBox.NoRole)
            message.setText("It appears this is not the first time you have run this tutorial.\n\n"+\
                            "Would you like to start from scratch, or skip to the automated calibration?\n\n"+\
                            "(Automated calibration only works if the robot has the same marker on the top"+\
                            " of its head as it did when you first ran this calibration.)\n")
            reply = message.exec_()

            # QtWidgets.QMessageBox.addButton
            if reply == 0: startFromScratch = True
            if reply == 1: startFromScratch = False

        # Make sure everything is ready
        vStream.setPaused(False)

        wizard = CoordWizard(self.env, startFromScratch, parent=self)
        wizard.exec_()
        wizard.close()
        wizard.deleteLater()

    def getSettings(self):
        return self.newSettings



class CoordWizard(QtWidgets.QWizard):
    def __init__(self, environment, startFromScratch, parent):
        super(CoordWizard, self).__init__(parent)

        self.allPages = startFromScratch

        # Set the robot to the home position
        robot = environment.getRobot()
        robot.setServos(servo1=True, servo2=True, servo3=True, servo4=True)
        robot.setPos(x=0, y=-15, z=15)
        robot.refresh()

        # Create the wizard pages and add them to the sequence
        if self.allPages:
            self.page1 = CWPage1(parent=self)
            self.page2 = CWPage2(robot, parent=self)
            self.page3 = CWPage3(robot, parent=self)
            self.page4 = CWPage4(environment, parent=self)
        self.page5 = CWPage5(environment, parent=self)

        if self.allPages:
            self.addPage(self.page1)
            self.addPage(self.page2)
            self.addPage(self.page3)
            self.addPage(self.page4)
        self.addPage(self.page5)

        # Aesthetic details
        self.setWindowTitle("Coordinate Calibration Wizard")
        self.setWindowIcon(QtGui.QIcon(Icons.objectWizard))

    def closeEvent(self, event):
        # Close any pages that have active widgets, such as the cameraWidget. This will trigger each page's close func.
        if self.allPages:
            self.page1.close()
            self.page2.close()
            self.page3.close()
            self.page4.close()
        self.page5.close()


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

        imageLbl.setPixmap(QtGui.QPixmap(Icons.robot_cam_overview))

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

        robot.setServos(servo1=False, servo2=False, servo3=False, servo4=False)
        robot.refresh()

        self.initUI()

    def initUI(self):

        prompt = "Mark the location of where the legs are with a sticker\n"         \
                 "or a marker, to avoid doing this calibration every time\n"        \
                 "the robot is moved.\n\n"                                          \
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
        movie = QtGui.QMovie(Icons.robot_lower_head)
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

class CWPage3(QtWidgets.QWizardPage):
    def __init__(self, robot, parent):
        super(CWPage3, self).__init__(parent)

        # For the sake of getting more information, save the robots position when centered on the camera
        groundCenterCoord = robot.getCurrentCoord()


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


        step1Lbl   = QtWidgets.QLabel("\n\nStep 3: Robot Marker")
        promptLbl  = QtWidgets.QLabel(prompt)
        imgOneLbl  = QtWidgets.QLabel()
        imgTwoLbl  = QtWidgets.QLabel()



        # Set the images on the img labels
        imgOneLbl.setPixmap(QtGui.QPixmap(Icons.make_sticker))
        imgTwoLbl.setPixmap(QtGui.QPixmap(Icons.sticker_on_head))

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
        self.newObject    = None
        self.hintLbl      = QtWidgets.QLabel("")  # This will tell the user how many points are on the object


        # Get the Environment objects that will be used
        self.vision       = environment.getVision()
        self.objManager   = environment.getObjectManager()

        # Create the camera widget and set it up
        self.cameraWidget = CameraSelector(environment.getVStream().getFilteredWithID, parent=self)
        self.cameraWidget.play()
        self.cameraWidget.declinePicBtn.clicked.connect(self.tryAgain)
        self.cameraWidget.objSelected.connect(self.objectSelected)


        self.initUI()


    def initUI(self):
        prompt = "Make sure the robot is in the center of the camera view. Then, click the mouse on the top right\n"  +\
                 "corner of the marker, and drag it to the bottom right corner of the marker.\n\n"                    +\
                 "The camera will begin tracking the marker. Try to have more than 500 points on the marker. Move\n"  +\
                 "the robot around and make sure that the object can be recognized for the majority of the cameras\n" +\
                 "view.\n"

        stepLbl    = QtWidgets.QLabel("Step 4: Selecting the Marker")
        promptLbl  = QtWidgets.QLabel(prompt)
        movieLbl   = QtWidgets.QLabel("Could not find example gif")  # Displays a gif of selecting the marker


        # Set the animated gif on the movieLbl
        movie = QtGui.QMovie(Icons.selecting_marker)
        movieLbl.setMovie(movie)
        movie.start()


        # Set titles bold
        bold = QtGui.QFont()
        bold.setBold(True)
        stepLbl.setFont(bold)
        self.hintLbl.setFont(bold)

        # Create a special row for the camera that will force it to remain in the center, regardless of size changes
        camRow = QtWidgets.QHBoxLayout()
        camRow.addWidget(self.cameraWidget)
        camRow.addStretch(1)
        camRow.addWidget(movieLbl)

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

        frame, rect = self.cameraWidget.getSelected()


        # Get the "target" object from the image and rectangle
        sample = self.vision.tracker.getTarget(frame, rect)

        # Analyze it, and make sure it's a valid target. If not, return the camera to selection mode.
        if len(sample.descrs) == 0 or len(sample.keypoints) == 0:
            self.cameraWidget.takeAnother()
            return


        self.objManager.deleteObject("Robot Marker")  # Delete any previous end effector file
        self.newObject = TrackableObject("Robot Marker")
        self.newObject.addSample(sample)
        self.objManager.saveNewObject(self.newObject)
        self.completeChanged.emit()


        # If the object was not very good, warn the user. Otherwise, state the # of points on the object
        if len(sample.descrs) < 350:
            self.hintLbl.setText("Your selected marker is not very detailed, or is too small, only " +
                                 str(len(sample.descrs)) + " points were found.\n"
                                 "Tracking may not be very accurate.")
        else:
            self.hintLbl.setText("Found " + str(len(sample.descrs)) + " Points")


        # Turn on the camera, and start tracking
        self.cameraWidget.play()
        self.vision.addTargetSamples(self.newObject.getSamples())
        self.vision.startTracker()
        self.vision.addTrackerFilter()

    def tryAgain(self):
        self.newObject = None
        self.completeChanged.emit()
        self.hintLbl.setText("")
        self.cameraWidget.play()
        self.cameraWidget.takeAnother()
        self.vision.trackerEndStopClear()


    def isComplete(self):
        return self.newObject is not None

    def close(self):
        self.cameraWidget.close()
        self.vision.clearTargets()
        self.vision.endTracker()
        self.vision.endTrackerFilter()

class CWPage5(QtWidgets.QWizardPage):
    def __init__(self, environment, parent):
        super(CWPage5, self).__init__(parent)




        # Initialize GUI globals
        self.startBtn = QtWidgets.QPushButton("Start Calibration")



        self.startBtn.clicked.connect(lambda: self.runCalibration(environment))
        self.initUI()

    def initUI(self):
        self.startBtn.setMaximumWidth(130)

        prompt = "When you press the Start Calibration button, the robot will go through a set of predefined moves\n"+\
                 "and record the information that it needs. Before beginning:\n\n\n" + \
                 "1) Make sure that the robot is more or less centered under the cameras view, and the Robot Marker" + \
                 " is being tracked.\n" \
                 "2) Make sure there is ample space for the robot to move around.\n" + \
                 "3) Make sure the robot is immobile, and mounted to the ground. If you move the robot, " + \
                 "you will have to re-run this calibration.\n"


        step1Lbl   = QtWidgets.QLabel("\n\nFinal Step:")
        promptLbl  = QtWidgets.QLabel(prompt)
        imgOneLbl  = QtWidgets.QLabel()
        imgTwoLbl  = QtWidgets.QLabel()



        # Set the images on the img labels
        imgOneLbl.setPixmap(QtGui.QPixmap(Icons.make_sticker))
        imgTwoLbl.setPixmap(QtGui.QPixmap(Icons.sticker_on_head))

        # Set titles bold
        bold = QtGui.QFont()
        bold.setBold(True)
        step1Lbl.setFont(bold)

        # Place the GUI objects vertically
        col1  = QtWidgets.QVBoxLayout()
        col1.addWidget(step1Lbl)
        col1.addWidget(promptLbl)
        col1.addWidget(self.startBtn)
        col1.addStretch(1)



        mainHLayout = QtWidgets.QHBoxLayout()
        mainHLayout.addLayout(col1)

        self.setLayout(mainHLayout)

    def runCalibration(self, env):
        showError      = lambda message: QtWidgets.QMessageBox.question(self, 'Error', message, QtWidgets.QMessageBox.Ok)
        showRobotError = showError("Robot was disconnected during calibration!\n Calibration did not complete.")

        # Pull from the environment and start the tracking
        robot      = env.getRobot()
        vision     = env.getVision()
        objManager = env.getObjectManager()


        testCoords = [# Test along the X axis
                     [  0, -15, 15],
                     [  3, -15, 15],
                     [  6, -15, 15],
                     [  9, -15, 15],
                     [ 12, -15, 15],
                     [ -3, -15, 15],
                     [ -6, -15, 15],
                     [ -9, -15, 15],
                     [-12, -15, 15],
                     # Test along the Y axis
                     [  0, -18, 15],
                     [  0, -21, 15],
                     [  0, -24, 15],
                     [  0, -27, 15],
                     [  0, -14, 15],
                     [  0, -12, 15],
                     [  0,  -9, 15],
                     [  0,  -6, 15],
                     # Test along the Z axis
                     [  0, -15, 12],
                     [  0, -15,  9],
                     [  0, -15,  6],
                     [  0, -15, 14],
                     [  0, -15, 18],
                     [  0, -15, 21],
                     [  0, -15, 24],
                     [  0, -15, 25]]

        robotTarget = objManager.getObject("Robot Marker")
        vision.trackerAddStartTrack(robotTarget.getSamples())
        noErrors = True  # If false, the calibration results will not be saved


        # A list of robot Coord and camera Coords, where each index of robotPoints corresponds to the cameraPoint index
        newCalibrations = {"robotPoints": [], "cameraPoints": []}


        # Set the robot to the home position, make sure that the servos are all attached
        robot.setServos(servo1=True, servo2=True, servo3=True, servo4=True)
        robot.setSpeed(30)
        robot.refresh()


        # Begin testing every coordinate in the testCoords array, and recording the results into newCalibrations
        for coord in testCoords:
            printf("CWPage5.runCalibration(): Testing point ", coord)

            # Move the robot to the coordinate
            robot.setPos(x=coord[0], y=coord[1], z=coord[2])
            robot.refresh()


            # Wait for move to finish, make sure robot stays connected throughout
            while robot.getMoving(): sleep(.1)
            sleep(.25)


            # Make sure the robot is still connected before recording the results
            if not robot.connected():
                showRobotError()
                noErrors = False
                break

            # Record the robots actual position by reading the servos
            actualCoord = robot.getCurrentCoord()
            newCalibrations["robotPoints"].append(actualCoord)


        # Do error checking, to make sure everything ran smoothly
        if not len(newCalibrations["robotPoints"]) == len(newCalibrations["cameraPoints"]):
            noErrors = False


        # Here's where new settings are saved, if the calibration ran smoothly
        if noErrors:
            pass


    def close(self):
        self.vision.clearTargets()
        self.vision.endTracker()
        self.vision.endTrackerFilter()