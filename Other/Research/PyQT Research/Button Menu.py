
from PyQt4 import QtGui
import sys


class Main(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(Main, self).__init__(parent)
        pushbutton = QtGui.QPushButton('Popup Button')
        menu = QtGui.QMenu()
        menu.addAction('This is Action 1', self.Action1)
        menu.addAction('This is Action 2', self.Action2)
        pushbutton.setMenu(menu)
        self.setCentralWidget(pushbutton)

    def Action1(self):
        print('You selected Action 1')

    def Action2(self):
        print('You selected Action 2')


if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    main = Main()
    main.show()
    app.exec_()