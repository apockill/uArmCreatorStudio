import random
import Paths
import random  # TODO: Remove this after testing
import numpy             as np
import Logic.RobotVision as rv
from PyQt5               import QtCore, QtWidgets, QtGui
from CameraGUI           import CameraSelector
from Logic.Global        import printf
from Logic.ObjectManager import TrackableObject
from time                import sleep  # Used only for waiting for robot in CoordCalibrations, page 5


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

        self.setMinimumHeight(480)
        self.setMinimumWidth(640)
        self.setLayout(mainHLayout)
        self.setWindowTitle('Calibrations')
        self.setWindowIcon(QtGui.QIcon(Paths.calibrate))



    def updateLabels(self):
        # Check if motionCalibrations already exist
        movCalib = self.newSettings["motionCalibrations"]
        if movCalib["stationaryMovement"] is not None:
            self.motionLbl.setText(" Stationary Movement: " + str(movCalib["stationaryMovement"]) +
                                   "     Active Movement: " + str(movCalib["activeMovement"]))

        coordCalib = self.newSettings["coordCalibrations"]
        if coordCalib["ptPairs"] is not None:
            self.coordLbl.setText("Calibration has been run before. " + str(len(coordCalib["ptPairs"])) +
                                  " points of data were collected.")

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
        robot.setSpeed(10)
        robot.setServos(all=True)
        robot.setPos( x=-15, y=-15, z=20)
        robot.refresh()

        # Move robot left and right while getting new frames for "moves" amount of samples
        for move in range(0, moves):

            robot.setPos(x=30 * direction, y=0, z=0, relative=True)   #end position
            robot.refresh(override=True)
            sleep(.1)
            while robot.getMoving():
                vStream.waitForNewFrame()

                totalMotion += vision.getMotion()

                samples += 1

            direction *= -1

        # Calculate average amount of motion when robot is moving rapidly
        highMovement = totalMotion / samples


        self.newSettings["motionCalibrations"]["stationaryMovement"] = round(  noMovement, 1)
        self.newSettings["motionCalibrations"]["activeMovement"]     = round(highMovement, 1)


        self.updateLabels()
        printf("CalibrateView.calibrateMotion(): Function complete! New motion settings: ", noMovement, highMovement)

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

        # If "Robot Marker" object doesn't exist
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

        # Make sure everything is ready
        vStream.setPaused(False)

        coordWizard = CoordWizard(self.env, startFromScratch, parent=self)
        coordWizard.exec_()
        coordWizard.close()
        coordWizard.deleteLater()

        # If the user finished the wizard correctly, then continue
        if coordWizard.result():
            newCoordCalib   = coordWizard.getNewCoordCalibrations()
            self.newSettings["coordCalibrations"]["ptPairs"] = newCoordCalib["ptPairs"]
            self.newSettings["coordCalibrations"]["failPts"] = newCoordCalib["failPts"]

            newGroundCalib = coordWizard.getNewGroundCalibration()
            self.newSettings["coordCalibrations"]["groundPos"] = newGroundCalib

        self.updateLabels()

    def getSettings(self):
        return self.newSettings



# class MotionWizard(QtWidgets.QWizardPage):


class CoordWizard(QtWidgets.QWizard):
    def __init__(self, environment, startFromScratch, parent):
        super(CoordWizard, self).__init__(parent)

        self.allPages = startFromScratch

        self.env = environment  # Used in close event to shut down vision

        # Set the robot to the home position
        robot = environment.getRobot()
        robot.setServos(all=True)
        robot.setPos(x=0, y=-15, z=15)
        robot.refresh()
        robot.setServos(all=False)
        robot.refresh()

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
        vision.trackerEndStopClear()

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

        imageLbl.setPixmap(QtGui.QPixmap(Paths.robot_cam_overview))

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
        self.getRobotCoords = robot.getCurrentCoord
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
        movie = QtGui.QMovie(Paths.robot_lower_head)
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
                coord = self.getRobotCoords()
                sumCoords += np.float32(coord)
            self.groundCoords = list(map(float, sumCoords / samples))

            printf("CWPage2.nextPressed(): New ground coordinates set: ", self.groundCoords)

class CWPage3(QtWidgets.QWizardPage):
    def __init__(self, parent):
        super(CWPage3, self).__init__(parent)

        # For the sake of getting more information, save the robots position when centered on the camera
        # self.groundCenterCoord = robot.getCurrentCoord()
        # print("new ground: ", self.groundCenterCoord)

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
        imgOneLbl.setPixmap(QtGui.QPixmap(Paths.make_sticker))
        imgTwoLbl.setPixmap(QtGui.QPixmap(Paths.sticker_on_head))

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
        prompt = "Make sure the robot's head is in the center of the camera view. Then, click the mouse on the top "  +\
                 "\nright corner of the marker, and drag it to the bottom right corner of the marker.\n\n"            +\
                 "The camera will begin tracking the marker. Try to have more than 500 points on the marker. Move\n"  +\
                 "the robot around and make sure that the object can be recognized for the majority of the cameras\n" +\
                 "view.\n"

        stepLbl    = QtWidgets.QLabel("Step 4: Selecting the Marker")
        promptLbl  = QtWidgets.QLabel(prompt)
        movieLbl   = QtWidgets.QLabel("Could not find example gif")  # Displays a gif of selecting the marker


        # Set the animated gif on the movieLbl
        movie = QtGui.QMovie(Paths.selecting_marker)
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
        trackable = TrackableObject("Robot Marker")
        trackable.addNewView(image      = frame,
                             rect       = rect,
                             pickupRect = None,
                             height     = None)
        target = self.vision.tracker.createTarget(trackable.getViews()[0])

        # Analyze it, and make sure it's a valid target. If not, return the camera to selection mode.
        if len(target.descrs) == 0 or len(target.keypoints) == 0:
            self.cameraWidget.takeAnother()
            return


        self.objManager.deleteObject("Robot Marker")  # Delete any previous end effector file
        self.newRobotMrkr = trackable
        self.objManager.saveObject(self.newRobotMrkr)
        self.completeChanged.emit()


        # If the object was not very good, warn the user. Otherwise, state the # of points on the object
        if len(target.descrs) < 350:
            self.hintLbl.setText("Your selected marker is not very detailed, or is too small, only " +
                                 str(len(target.descrs)) + " points were found.\n"
                                 "Tracking may not be very accurate.")
        else:
            self.hintLbl.setText("Found " + str(len(target.descrs)) + " Points")


        # Turn on the camera, and start tracking
        self.cameraWidget.play()
        self.vision.trackerAddStartTrack(self.newRobotMrkr)

    def tryAgain(self):
        self.newRobotMrkr = None
        self.completeChanged.emit()
        self.hintLbl.setText("")
        self.cameraWidget.play()
        self.cameraWidget.takeAnother()
        self.vision.trackerEndStopClear()


    def isComplete(self):
        return self.newRobotMrkr is not None

    def close(self):
        self.cameraWidget.close()
        self.vision.trackerEndStopClear()

class CWPage5(QtWidgets.QWizardPage):
    def __init__(self, environment, getGroundCoord, parent):
        super(CWPage5, self).__init__(parent)

        # Initialize GUI globals
        self.getGroundCoord  = getGroundCoord  # This is used once runCalibration is started
        self.startBtn        = QtWidgets.QPushButton("Start Calibration")
        self.hintLbl         = QtWidgets.QLabel("\n\n\n\n\n\t\t\t\t") # Add newlines since window resizing is screwed up
        self.newCalibrations = None
        self.successComplete = False

        self.startBtn.clicked.connect(lambda: self.runCalibration(environment))
        self.initUI()

    def initUI(self):
        self.startBtn.setMaximumWidth(130)

        prompt = "When you press the Start Calibration button, the robot will go through a set of predefined moves\n"+\
                 "and record the information that it needs. The program will freeze for a minute. " \
                 "Before beginning:\n\n\n" + \
                 "1) Make sure that the robot's head is more or less centered under the cameras view, and the\n" \
                 "    Robot Marker is being tracked.\n" \
                 "2) Make sure there is ample space for the robot to move around.\n" + \
                 "3) Make sure the robot is immobile, and mounted to the ground. If you move the robot,\n" + \
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
        col1.addWidget(self.hintLbl)
        col1.addWidget(self.startBtn)
        col1.addStretch(1)

        mainHLayout = QtWidgets.QHBoxLayout()
        mainHLayout.addLayout(col1)

        self.setLayout(mainHLayout)


    def runCalibration(self, env):

        # Pull from the environment and start the tracking
        vStream    = env.getVStream()
        robot      = env.getRobot()
        vision     = env.getVision()
        objManager = env.getObjectManager()

        #   Start tracking the robots marker
        rbMarker = objManager.getObject("Robot Marker")
        vision.clearTargets()   # Make sure there are no duplicate objects being tracked
        vision.trackerAddStartTrack(rbMarker)


        # Keep a list of errors that occured while running, to present to the user after calibration
        errors = []


        # A list of robot Coord and camera Coords, where each index of robPts corresponds to the cameraPoint index
        newCalibrations = {"ptPairs": [], "failPts": []}


        # Set the robot to the home position, set the speed, and other things for the calibration
        robot.setServos(all=True)
        robot.setSpeed(15)
        robot.refresh()

        zLower = self.getGroundCoord()[2] + 1.5
        robot.setPos(x=robot.home["x"], y=robot.home["y"], z=zLower)
        robot.refresh()
        sleep(1)


        # Generate a large set of points to test the robot, and put them in testCoords
        testCoords    = []
        direction  = True

        # Test the z on 4 xy points
        zTest = int(round(zLower, 0))  # Since range requires an integer, round zLower just for this case
        for z in range(zTest, 25, 1): testCoords += [[0,  -15, z]]
        for z in range(zTest, 25, 2): testCoords += [[-8, -11, z]]
        for z in range(zTest, 25, 2): testCoords += [[-5, -13, z]]
        for z in range(zTest, 25, 2): testCoords += [[-5, -17, z]]
        for z in range(zTest, 25, 2): testCoords += [[-8, -19, z]]
        for z in range(zTest, 25, 2): testCoords += [[ 8, -11, z]]
        for z in range(zTest, 25, 2): testCoords += [[ 5, -13, z]]
        for z in range(zTest, 25, 2): testCoords += [[ 5, -17, z]]
        for z in range(zTest, 25, 2): testCoords += [[ 8, -19, z]]


        # Test very near the base of the robot, but avoid the actual base
        for x in range(-20,  -8,  1): testCoords += [[x, -5, zLower]]
        for x in range(  8,  20,  1): testCoords += [[x, -5, zLower]]
        for x in range( 20,   7, -1): testCoords += [[x, -6, zLower]]
        for x in range( -7, -20, -1): testCoords += [[x, -6, zLower]]
        for x in range(-20,  -6,  1): testCoords += [[x, -7, zLower]]
        for x in range(  6,  20,  1): testCoords += [[x, -7, zLower]]

        # Scan the entire board row by row
        for y in range(-8, -25, -1):  # [-8, -11, -15, -19, -25]:
            if direction:
                for x in range(20, -20, -1): testCoords += [[x, y, zLower]]
            else:
                for x in range(-20, 20,  1): testCoords += [[x, y, zLower]]
            direction = not direction



        printf("CWPage5.runCalibration(): Testing ", len(testCoords), " coordinate points")


        # Begin testing every coordinate in the testCoords array, and recording the results into newCalibrations
        seenLast = True
        for coord in testCoords:
            if not seenLast: # Skip in areas where there is low visibility
                seenLast = True
                continue

            printf("CWPage5.runCalibration(): Testing point ", coord)

            # Move the robot to the coordinate
            robot.setPos(x=coord[0], y=coord[1], z=coord[2])
            robot.refresh()
            robot.wait()
            sleep(.2)

            # Now that the robot is at the desired position, get the avg location
            vStream.waitForNewFrame()
            frameAge, marker = vision.getObjectLatestRecognition(rbMarker)

            # Make sure the object was found in a recent frame
            if not frameAge == 0 or marker.center is None:
                printf("CWPage5.runCalibration(): Marker was not recognized.")
                seenLast = False
                newCalibrations['failPts'].append(coord)
                continue

            if marker.ptCount < 50:
                printf("CWPage5.runCalibration(): Disregarding frame. Only ", marker.ptCount, "tracker pts were found")
                continue

            # Make sure the robot is still connected before recording the results
            if not robot.connected():
                errors.append("Robot was disconnected during calibration")
                break


            # Since the camera found the object, now read the robots location through camera, and record both results
            actCoord = robot.getCurrentCoord()
            dist = ((actCoord[0] - coord[0])**2 + (actCoord[1] - coord[1])**2 + (actCoord[2] - coord[2])**2)**.5
            if dist < 2.5:
                newCalibrations["ptPairs"].append([marker.center, coord])
            else:
                print("Distance was too high: ", dist)

        robot.setPos(**robot.home)
        robot.refresh()
        # Prune the list down to 20 less than the original size, find the best set out of those
        minPointCount = 6
        # prunedSize = int(len(newCalibrations["ptPairs"]) * .90)
        # if prunedSize > minPointCount:
        #     bestScore, bestPtPairs = self.pruneCalibrationSet(prunedSize, newCalibrations["ptPairs"])
        #     newCalibrations["ptPairs"] = bestPtPairs
        #     print("Final calibrations: ", bestPtPairs)

        # Check the percent of points that were found vs amount of points that were in the testCoord array
        if len(newCalibrations["ptPairs"]) < minPointCount:
            # If not enough points were found, append an error to the error array
            if len(newCalibrations["ptPairs"]) == 0:
                errors.append("The marker was never seen! Try restarting the calibration and setting the marker again,"
                              "\n\t\tand making sure that the robot's head is, in fact, in view of the camera")
            else:
                errors.append("The marker was not recognized in enough points- it was only seen " +
                          str(len(newCalibrations["ptPairs"])) + " time(s)!\n\t\tIt must be seen at least " +
                            str(minPointCount) + " times.\n" +
                          "\t\tTry making sure that the robot's head is centered in the middle of the cameras view,\n"
                          "\t\tor try placing the camera in a higher location.")


        # Return the robot to home and turn off tracking
        vision.trackerEndStopClear()
        robot.setPos(**robot.home)
        robot.refresh()


        self.endCalibration(errors, newCalibrations, len(testCoords))

    def endCalibration(self, errors, newCalibrations, totalPointCount):

        # Print out the errors, and set the appropriate GUI elements
        hintText = ""
        if len(errors):
            hintText += "Calibration did not complete successfully. The following errors occured:\n"
            for error in errors:
                hintText += "\t- " + error + "\n"
            self.successComplete = False
            self.startBtn.setText("Restart Calibration")
        else:
            hintText += "Calibration was successful, " + str(len(newCalibrations["ptPairs"])) + "/"  +\
                         str(totalPointCount) + " points were found.\nResults will be saved when you click Apply " +\
                        "on the calibrations page. Feel free to try this again.\n" +\
                        "Make sure to repeat this calibration whenever you move your camera or move your robot."
            self.successComplete = True
            self.startBtn.setDisabled(True)

        self.hintLbl.setText(hintText)
        self.setFixedSize(self.layout().sizeHint())


        self.completeChanged.emit()

        # Now, update the settings if the calibration ran correctly
        if len(errors) == 0:
            self.newCalibrations = newCalibrations

    def pruneCalibrationSet(self, newSize, ptPairs):
        """
        This function looks a bit complicated, but its purpose is simple: input a list of ptPairs, and it will return
        an optimized set of size newSize. It does this by "scoring" how good each point is, then returning the set
        with the best points.

        The way it does this is by generating many many different combinations of set newSize, and doing the following:
            Create a camera->Robot transform
            Create a Robot->Camera transform
            input a point into the cam->rob transform then put it into rob->cam transform and see how different it is.

            If its similar, then the transform is good.

        It does this with many points and with many sets, and then adds an "error" to each point in each set, then
        chooses the points with the lowest error.
        :param newSize:
        :param ptPairs:
        :return:
        """
        import random  # TODO: Remove this after testing
        import numpy             as np
        import Logic.RobotVision as rv

        def getRandomSet(length, ptPairs):
            ptPairs     = ptPairs[:]
            randPtPairs = []
            chosenIndexes = []
            for i in range(0, length):
                randIndex = random.randint(0, len(ptPairs) - 1)
                randPtPairs.append(ptPairs[randIndex])
                chosenIndexes.append(randIndex)
                del ptPairs[randIndex]

            return randPtPairs, ptPairs, chosenIndexes

        def testPointSetError(testPtPairs, testPoints):
            # Test the error for every point in the transform, return a root-mean-squared error value
            camToRob = rv.createTransformFunc(testPtPairs, direction=1)
            robToCam = rv.createTransformFunc(testPtPairs, direction=-1)

            errorSum = 0
            for pt in testPoints:
                # Transform to robot coordinates then back to camera coordinates and find the difference
                posRob    = camToRob(pt)        # rv.getPositionTransform(pt, testPtPairs, direction=1)
                posCam    = robToCam(posRob)  # rv.getPositionTransform(posRob, testPtPairs, direction=-1)
                errorSum += sum((pt - posCam) ** 2) ** .5
            return errorSum  / len(testPoints)


        printf("CWPage5.getBestCalibrationSet.(): Pruning set to size ", newSize, " out of original ", len(ptPairs))

        if len(ptPairs) <= newSize:
            return newCalibration

        # Get real points to test each random ptPair set on
        testPoints  = np.asarray(random.sample(ptPairs, 10))[:, 0]

        pointError = [[i, 0, 0] for i in range(0, len(ptPairs))]   # (point index, # samples, error sum)
        bestScore  = -1
        bestSet    = None
        samples    = 500
        avgError   = 0
        for i in range(0, samples):

            randPtPairs, leftoverPtPairs, chosenIndexes = getRandomSet(newSize, ptPairs)

            error     = testPointSetError(randPtPairs, testPoints)
            avgError += error

            # Record the error from this set onto every point that was in the set.
            for i in chosenIndexes:
                pointError[i][1] += 1                   # Samples
                pointError[i][2] += error            # Error sum

            if error < bestScore or bestScore == -1:
                bestSet = randPtPairs
                bestScore = error
                print(bestScore)
        avgError /= samples

        bestIndexes = sorted(pointError, key=lambda pt:  pt[2] / pt[1] if pt[1] > 0 else 1000)
        bestSet = []

        for i in range(0, newSize):
            bestSet.append(ptPairs[bestIndexes[i][0]])

        error = testPointSetError(bestSet, testPoints)

        printf("CWPage5.pruneCalibrationSet(): Average error: ", avgError, " bestSet ", bestScore, " der. set: ", error)
        if error < avgError:
            printf("CWPage5.pruneCalibrationSet(): Returning derived set")
            return error, bestSet
        else:

            printf("CWPage5.pruneCalibrationSet(): Found set is worse than the average. Returning bestSet.")
            return bestScore, bestSet





    def isComplete(self):
        return self.successComplete




