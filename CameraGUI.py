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
import cv2
import Paths
from PyQt5        import QtWidgets, QtCore, QtGui
from Logic.Global import printf
__author__ = "Alexander Thiel"



def cvToPixFrame(image):
    # Convert a cv2 frame to a Qt PixFrame

    pixFrame               = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    height, width, channel = pixFrame.shape
    bytesPerLine           = 3 * width
    img                    = QtGui.QImage(pixFrame, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
    pix                    = QtGui.QPixmap.fromImage(img)

    return pix


class CameraWidget(QtWidgets.QWidget):
    """
    Creates a widget that will update at a certain fps, by calling for a new frame from the vStream object.

    :param getFrameFunction: A function that when called will return a frame
            that can be put in a QLabel. In this case the frame will come from
            a VideoStream object's getFrame function.
    :return:
    """


    def __init__(self, vStream, parent, fps=24.0):
        super(CameraWidget, self).__init__(parent)


        # Set up globals
        self.vStream          = vStream
        self.fps              = fps   # The maximum FPS the widget will update at
        self.paused           = True  # Keeps track of the video's state
        self.timer            = QtCore.QTimer()
        self.lastFrameID      = None

        self.timer.timeout.connect(self.nextFrameSlot)


        # Initialize UI Variables
        self.frameLbl    = QtWidgets.QLabel()
        self.hintLbl     = QtWidgets.QLabel()
        self.mainVLayout = QtWidgets.QVBoxLayout(self)  # Global because subclasses need it
        self.mainHLayout = QtWidgets.QHBoxLayout()


        # Initialize UI
        movie = QtGui.QMovie(Paths.help_connect_camera)
        self.frameLbl.setMovie(movie)
        movie.start()


        self.mainHLayout.setContentsMargins(0, 0, 0, 0)
        self.mainVLayout.setContentsMargins(0, 0, 0, 0)

        self.mainHLayout.addWidget(self.frameLbl)
        self.mainHLayout.addStretch(1)
        self.mainVLayout.addLayout(self.mainHLayout)

        self.setLayout(self.mainVLayout)


    def play(self):
        if self.paused:
            # Always get a frame immediately, so that any "resizing" functions will work properly in other widgets
            self.nextFrameSlot()
            self.timer.start(1000. / self.fps)

        self.paused = False

    def pause(self):
        if not self.paused:
            self.timer.stop()

        self.paused = True


    def setFrame(self, frame):
        """
            Convert a CV2 frame to a QPixMap and set the frameLbl to that
            When paused, you might want to have a custom frame showing. This is also useful for CameraSelector
            The nextFrameSlot also uses it to set frames.
        """
        if frame is None: return None
        self.frameLbl.setPixmap(cvToPixFrame(frame))

    def nextFrameSlot(self):
        if self.vStream.frameCount == self.lastFrameID: return

        frame   = self.vStream.getFilteredFrame()

        if frame is None: return

        # Convert the frame to a QPixMap and set the frameLbl to that
        self.lastFrameID = self.vStream.frameCount
        self.frameLbl.setPixmap(cvToPixFrame(frame))

    def closeEvent(self, event):
        self.pause()


class CameraSelector(CameraWidget):
    """
    This is a camerawidget that the user can draw rectangles over, and will return the area of the image that the user
    selected.
    """

    # This signal emits only when the user selects an image, or restarts the process.
    objSelected  = QtCore.pyqtSignal()


    def __init__(self, vStream, parent, hideRectangle=True):
        """

        :param hideRectangle: If True, then when something is selected, the rubber band won't go away.
        :param parent: The GUI Parent of this widget
        """
        super(CameraSelector, self).__init__(vStream, parent)

        # Set up the rubberBand specific variables (for rectangle drawing)
        self.rectangle     = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)
        self.hideRectangle = hideRectangle
        self.origin        = QtCore.QPoint()
        self.vStream       = vStream


        # When the user has something selected, this is a frame. Otherwise, it is None
        self.selectedImage = None
        self.selectedRect  = None  # The coordinates of the object inside of self.selectedImage. (x1,y1,x2,y2) format.


        # Make sure that the QRect is aligned with the picture by adding a stretch and setting the contents margins!
        self.layout().addStretch(1)  # Push the layout to the top, so the mouse commands align correctly


    # Selection related events
    def mousePressEvent(self, event):
        # If the user already has selected an image, leave.
        self.takeAnother()

        if event.button() == QtCore.Qt.LeftButton:

            # Make sure the click was within the boundaries of the frame
            width  = self.frameLbl.pixmap().width()
            height = self.frameLbl.pixmap().height()
            pos    = (event.pos().x(), event.pos().y())
            if not 0 < pos[0] < width:  return
            if not 0 < pos[1] < height: return


            # Get a frame from OpenCV, so that it can be cropped when the user releases the mouse button
            self.selectedImage = self.vStream.getFrame()

            if self.selectedImage is None:
                printf("GUI| ERROR: getCVFrame() returned None Frame! ")
                return

            # Set the rectangles position and unhide the rectangle
            self.origin = QtCore.QPoint(event.pos())
            self.rectangle.setGeometry(QtCore.QRect(self.origin, QtCore.QSize()))
            self.rectangle.show()

    def mouseMoveEvent(self, event):

        if not self.origin.isNull() and self.selectedRect is None:
            # Make sure the rectangle is bounded by the edge of the frame
            width  = self.frameLbl.pixmap().width()
            height = self.frameLbl.pixmap().height()
            pos    = (event.pos().x(), event.pos().y())

            # If it's not within the boundaries, then nothing will happen
            if not 0 < pos[0] < width:  return
            if not 0 < pos[1] < height: return

            self.rectangle.setGeometry(QtCore.QRect(self.origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event):

        if event.button() == QtCore.Qt.LeftButton and self.selectedRect is None:
            if self.hideRectangle: self.rectangle.hide()


            # Get the rectangle geometry
            pt = self.rectangle.geometry().getCoords()

            # Ensure that the selected area isn't incredibly small (aka, a quick click
            if pt[3] - pt[1] < 10 or pt[2] - pt[0] < 10:
                self.selectedImage = None
                self.selectedRect  = None
                return

            self.selectedRect  = pt
            self.objSelected.emit()


    def setRectangle(self, rect):
        # Used by other objects to set the location of the rectangle. rect is [[x1, y1], [x2, y2]]
        p1, p2 = rect
        p1 = QtCore.QPoint(p1[0], p1[1])
        p2 = QtCore.QPoint(p2[0], p2[1])
        self.rectangle.setGeometry(QtCore.QRect(p1, p2).normalized())
        self.rectangle.show()

    def getSelected(self):
        # Returns the image and the rectangle of the selection from the image
        return self.selectedImage, self.selectedRect

    def getSelectedRect(self):
        return self.selectedRect

    def getSelectedFrame(self):
        return self.selectedImage

    def takeAnother(self):
        # Return the widget to "take a picture" mode, throw away the old selected frame.
        self.selectedImage = None
        self.selectedRect  = None
        self.rectangle.hide()


    def closeEvent(self, event):
        self.pause()




