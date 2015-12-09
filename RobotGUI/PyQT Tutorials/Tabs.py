from PyQt4 import QtGui
from PyQt4 import QtCore
import sys



class SubWindow(QtGui.QWidget):
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

    def identifyClk(self, obj):
        print obj

class MainWindow(QtGui.QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.initUI()

    def initUI(self):
        tabs	= QtGui.QTabWidget()
        pushButton1 = QtGui.QPushButton("QPushButton 1")
        pushButton2 = QtGui.QPushButton("QPushButton 2")

        tab1	= SubWindow(0)
        tab2	= SubWindow(1)
        tab3	= SubWindow(2)


        #Resize width and height
        tabs.resize(250, 150)

        #Move QTabWidget to x:300,y:300
        tabs.move(300, 300)

        tabs.addTab(tab1,"Tab 1")
        tabs.addTab(tab2,"Tab 2")
        tabs.addTab(tab3,"Tab 3")

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(tabs)
        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox)

        self.setLayout(vbox)
        self.setGeometry(600, 600, 640, 480)
        self.setWindowTitle("Tabs and classes test!")
        self.show()

if __name__ == '__main__':
    app 	= QtGui.QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())