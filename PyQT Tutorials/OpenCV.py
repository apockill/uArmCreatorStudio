import sys
import cv2
from PyQt4 import QtGui, QtCore


class QtCapture(QtGui.QWidget):
    def __init__(self, *args):
        super(QtGui.QWidget, self).__init__()
        QtGui.QWidget.__init__(self)
        self.capture = None

        self.playBtn  = QtGui.QPushButton('Play')
        self.pauseBtn = QtGui.QPushButton('Pause')

        self.playBtn.clicked.connect(self.start)
        self.pauseBtn.clicked.connect(self.stop)


        vbox = QtGui.QVBoxLayout(self)
        vbox.addWidget(self.playBtn)
        vbox.addWidget(self.pauseBtn)

        self.fps = 24
        self.cap = cv2.VideoCapture(0)
        self.video_frame = QtGui.QLabel()


        vbox.addWidget(self.video_frame)

        self.setLayout(vbox)
        self.setWindowTitle('Control Panel')
        self.show()
        self.start()

    def setFPS(self, fps):
        self.fps = fps

    def nextFrameSlot(self):
        ret, frame = self.cap.read()
        # My webcam yields frames in BGR format

        frame = cv2.cvtColor(frame, cv2.cv.CV_BGR2RGB)

        img = QtGui.QImage(frame, frame.shape[1], frame.shape[0], QtGui.QImage.Format_RGB888)
        pix = QtGui.QPixmap.fromImage(img)
        self.video_frame.setPixmap(pix)

    def start(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.nextFrameSlot)
        self.timer.start(1000./self.fps)

    def stop(self):
        self.timer.stop()




if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    window = QtCapture()
    sys.exit(app.exec_())