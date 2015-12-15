import sys
from PyQt4 import QtCore
from PyQt4 import QtGui

class MainWindow(QtGui.QMainWindow):
    count = 0

    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
        self.mdi = QtGui.QMdiArea()
        self.setCentralWidget(self.mdi)
        bar = self.menuBar()

        fileMnu = bar.addMenu("File")
        fileMnu.addAction("New")
        fileMnu.addAction("cascade")
        fileMnu.addAction("Tiled")
        fileMnu.triggered[QtGui.QAction].connect(self.windowaction)

        self.setWindowTitle("MDI demo")

    def windowaction(self, q):
        print "triggered"

        if q.text() == "New":
            MainWindow.count = MainWindow.count+1  #Only for naming the window
            sub = SubWindow(MainWindow.count)
            # sub = QMdiSubWindow()
            # sub.setWidget(QTextEdit())
            # sub.setWindowTitle("subwindow" + str(MainWindow.count))

            self.mdi.addSubWindow(sub)
            sub.show()

        if q.text() == "cascade":
            self.mdi.cascadeSubWindows()

        if q.text() == "Tiled":
            self.mdi.tileSubWindows()

class SubWindow(QtGui.QDialog):
    def __init__(self, identity):
        super(SubWindow, self).__init__()
        self.identity = identity
        self.initUI()

    def initUI(self):

        identifyBtn = QtGui.QPushButton('Identify', self)
        identifyBtn.clicked.connect(lambda: self.identifyClk(self.identity))
        identifyBtn.resize(identifyBtn.sizeHint())

        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(identifyBtn)

        vbox = QtGui.QVBoxLayout()
        vbox.addStretch(1)
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('Identity: ' + str(self.identity))
        #self.show()

    def identifyClk(self, obj):
        print obj


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec_())