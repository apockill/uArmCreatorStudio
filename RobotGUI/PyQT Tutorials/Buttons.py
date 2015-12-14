# -*- coding: utf-8 -*-

"""
ZetCode PyQt4 tutorial

This program creates a quit
button. When we press the button,
the application terminates.

author: Jan Bodnar
website: zetcode.com
last edited: October 2011
"""

import sys
from PyQt4 import QtGui, QtCore


class Example(QtGui.QWidget):

    def __init__(self):
        super(Example, self).__init__()

        self.initUI()

    def initUI(self):

        qbtn = QtGui.QPushButton('Quit', self)
        qbtn.clicked.connect(QtCore.QCoreApplication.instance().quit)
        qbtn.resize(qbtn.sizeHint())
        qbtn.move(50, 50)

        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('Quit button')
        self.show()

def main():

    app = QtGui.QApplication(sys.argv)
    ex = Example()

    sys.exit(app.exec_())



if __name__ == '__main__':
    main()