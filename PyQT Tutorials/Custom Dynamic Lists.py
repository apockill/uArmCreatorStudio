import sys
from PyQt5 import QtWidgets, QtCore, QtGui

class CommandList(QtWidgets.QListWidget):
    def __init__(self, type, parent=None):
        super(CommandList, self).__init__(parent)
        #self.setIconSize(QtCore.QSize(124, 124))
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setAcceptDrops(True)




        #self.connect(self.listWidgetA, QtCore.SIGNAL("dropped"), self.items_dropped)

        #self.listWidgetA.currentItemChanged.connect(self.item_clicked)

    def addCommand(self, num, name):
        command = CommandItem()
        command.setTextUp(num)
        command.setTextDown(name)
        command.setIcon("lolkek.png")
        listWidgetItem = QtWidgets.QListWidgetItem(self)
        listWidgetItem.setSizeHint(command.sizeHint())
        self.addItem(listWidgetItem)
        self.setItemWidget(listWidgetItem, command)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super(CommandList, self).dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            super(CommandList, self).dragMoveEvent(event)

    def dropEvent(self, event):
        #print 'dropEvent', event
        # if event.mimeData().hasUrls():
        #     event.setDropAction(QtCore.Qt.CopyAction)
        #     event.accept()
        #     links = []
        #     for url in event.mimeData().urls():
        #         links.append(str(url.toLocalFile()))
        #     self.emit(QtCore.SIGNAL("dropped"), links)
        # else:
        event.setDropAction(QtCore.Qt.MoveAction)
        super(CommandList, self).dropEvent(event)


class CommandItem(QtWidgets.QWidget):
    def __init__ (self, parent = None):
        super(CommandItem, self).__init__(parent)
        self.textQVBoxLayout = QtWidgets.QVBoxLayout()
        self.textUpQLabel    = QtWidgets.QLabel()
        self.textDownQLabel  = QtWidgets.QLabel()
        self.textQVBoxLayout.addWidget(self.textUpQLabel)
        self.textQVBoxLayout.addWidget(self.textDownQLabel)
        self.allQHBoxLayout  = QtWidgets.QHBoxLayout()
        self.iconQLabel      = QtWidgets.QLabel()
        self.allQHBoxLayout.addWidget(self.iconQLabel, 0)
        self.allQHBoxLayout.addLayout(self.textQVBoxLayout, 1)
        self.setLayout(self.allQHBoxLayout)
        # setStyleSheet
        self.textUpQLabel.setStyleSheet('''
            color: rgb(0, 0, 255);
        ''')
        self.textDownQLabel.setStyleSheet('''
            color: rgb(255, 0, 0);
        ''')

    def setTextUp (self, text):
        self.textUpQLabel.setText(text)

    def setTextDown (self, text):
        self.textDownQLabel.setText(text)

    def setIcon (self, imagePath):
        self.iconQLabel.setPixmap(QtGui.QPixmap(imagePath))


class MainWindow (QtWidgets.QMainWindow):
    def __init__ (self):
        super(MainWindow, self).__init__()


        myBoxLayout = QtWidgets.QVBoxLayout()
        mainWidget = QtWidgets.QWidget()
        mainWidget.setLayout(myBoxLayout)
        self.setCentralWidget(mainWidget)
        self.commandList = CommandList(self)
        myBoxLayout.addWidget(self.commandList)

        # Create QListWidget

        for index, name, icon in [
            ('No.1', 'Meyoko',  'icon.png'),
            ('No.2', 'Nyaruko', 'icon.png'),
            ('No.3', 'Louise',  'icon.png')]:

            self.commandList.addCommand(index, name)



app = QtWidgets.QApplication([])
window = MainWindow()
window.show()
sys.exit(app.exec_())