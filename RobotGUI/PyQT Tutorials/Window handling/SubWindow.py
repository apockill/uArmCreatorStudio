from PyQt4 import QtGui
import sys

#http://stackoverflow.com/questions/13309255/basic-help-needed-in-pyqt4

class SubWindow(QtGui.QDialog):
    def __init__(self):
        super(SubWindow , self).__init__()     
        label = QtGui.QLabel("Hey, subwindow here!",self);

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow , self).__init__()     
        self.window()

    def window(self):
        Action = QtGui.QAction(QtGui.QIcon('action.png') , 'action' , self)          
        Action.triggered.connect(self.a)

        mb = self.menuBar()
        option = mb.addMenu('File')
        option.addAction(Action)

        self.show()

    def a(self):

        s = SubWindow()
        s.exec_()

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    mw = MainWindow()
    sys.exit(app.exec_())