from PyQt4 import QtGui, QtCore
import sys, os

class ThumbListWidget(QtGui.QListWidget):
    def __init__(self, type, parent=None):
        super(ThumbListWidget, self).__init__(parent)
        self.setIconSize(QtCore.QSize(124, 124))
        self.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super(ThumbListWidget, self).dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            super(ThumbListWidget, self).dragMoveEvent(event)

    def dropEvent(self, event):
        print 'dropEvent', event
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
            links = []
            for url in event.mimeData().urls():
                links.append(str(url.toLocalFile()))
            self.emit(QtCore.SIGNAL("dropped"), links)
        else:
            event.setDropAction(QtCore.Qt.MoveAction)
            super(ThumbListWidget, self).dropEvent(event)


class Dialog_01(QtGui.QMainWindow):
    def __init__(self):
        super(QtGui.QMainWindow,self).__init__()

        myQWidget = QtGui.QWidget()
        myBoxLayout = QtGui.QVBoxLayout()
        myQWidget.setLayout(myBoxLayout)
        self.setCentralWidget(myQWidget)

        self.listWidgetA = ThumbListWidget(self)
        self.listWidgetB = ThumbListWidget(self)
        self.listWidgetC = ThumbListWidget(self)

        #Throw data on the list
        for i in range(12): 
            QtGui.QListWidgetItem( 'Item '+str(i), self.listWidgetA )
        for i in range(100,105):
            QtGui.QListWidgetItem( 'Item '+str(i), self.listWidgetC )
        
        self.connect(self.listWidgetA, QtCore.SIGNAL("dropped"), self.items_dropped)
        self.connect(self.listWidgetB, QtCore.SIGNAL("dropped"), self.items_dropped)
        self.connect(self.listWidgetC, QtCore.SIGNAL("dropped"), self.items_dropped)

        self.listWidgetA.currentItemChanged.connect(self.item_clicked)
        self.listWidgetB.currentItemChanged.connect(self.item_clicked)
        self.listWidgetC.currentItemChanged.connect(self.item_clicked)

        myBoxLayout.addWidget(self.listWidgetA)
        myBoxLayout.addWidget(self.listWidgetB)
        myBoxLayout.addWidget(self.listWidgetC)

    def items_dropped(self, arg):
        print 'items_dropped', arg

    def item_clicked(self, arg):
        print arg

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    dialog_1 = Dialog_01()
    dialog_1.show()
    dialog_1.resize(480,320)
    sys.exit(app.exec_())