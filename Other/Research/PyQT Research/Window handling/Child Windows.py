import sys
from PyQt4 import QtGui, QtCore

#http://stackoverflow.com/questions/28597977/pyqt4-child-windows-do-not-minimize-to-windows-taskbar

class Parent(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(Parent, self).__init__(parent)
        w = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(w)
        self.button = QtGui.QPushButton('Create Child')
        self.text = QtGui.QTextEdit()
        layout.addWidget(self.button)
        layout.addWidget(self.text)
        self.setCentralWidget(w)
        self.setWindowTitle('Parent')
        self.button.clicked.connect(self.createChild)

    def createChild(self):
        self.dialog = QtGui.QMainWindow(self)

        #self.dialog.setParent(None)
        self.dialog.setWindowTitle('Child')
        self.dialog.show()

app = QtGui.QApplication(sys.argv)
p = Parent()
p.show()
sys.exit(app.exec_())