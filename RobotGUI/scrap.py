#!/usr/bin/python ~/workspace/pyqt/memory/main.py

from PyQt4 import QtCore, QtGui

class SampleDialog(QtGui.QDialog):
    def __init__(self, parent):
        super(SampleDialog, self).__init__(parent)
        self.setWindowTitle('Testing')
        self.resize(200, 100)

class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
        
        # create the menu
        test_menu = self.menuBar().addMenu('Testing')
        
        # create the menu actions
        exec_act  = test_menu.addAction('Exec Dialog')
        show_act  = test_menu.addAction('Show Dialog')
        count_act = test_menu.addAction('Show Count')
        
        # create the connections
        exec_act.triggered.connect( self.execDialog )
        show_act.triggered.connect( self.showDialog )
        count_act.triggered.connect( self.showCount )
    
    def execDialog(self):
        dlg = SampleDialog(self)
        dlg.exec_()
        
    def showDialog(self):
        dlg = SampleDialog(self)
        dlg.show()
    
    def showCount(self):
        count = len(self.findChildren(QtGui.QDialog))
        QtGui.QMessageBox.information(self, 'Dialog Count', str(count))

if ( __name__ == '__main__' ):
    app = None
    if ( not app ):
        app = QtGui.QApplication([])
    
    window = MainWindow()
    window.show()
    
    if ( app ):
        app.exec_()