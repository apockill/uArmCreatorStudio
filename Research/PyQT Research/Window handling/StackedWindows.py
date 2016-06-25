import sys
from PyQt4 import QtGui

class ApplicationWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.stack = QtGui.QStackedWidget(self)
        self.View1 = QtGui.QLabel('View 1', self.stack)
        self.View2 = QtGui.QLabel('View 2', self.stack)
        self.stack.addWidget(self.View1)
        self.stack.addWidget(self.View2)
        self.setCentralWidget(self.stack)
        menu = self.menuBar().addMenu('&Views')
        menu.addAction('View 1', lambda: self.showView(0))
        menu.addAction('View 2', lambda: self.showView(1))

    def showView(self, index):
        self.stack.setCurrentIndex(index)

if __name__ == '__main__':

    qApp = QtGui.QApplication(sys.argv)
    aw = ApplicationWindow()
    aw.show()
    sys.exit(qApp.exec_())