from PyQt5 import QtWidgets, QtWidgets, QtCore
import sys, os

class ThumbListWidget(QtWidgets.QListWidget):
    def __init__(self, type, parent=None):
        super(ThumbListWidget, self).__init__(parent)
        self.setIconSize(QtCore.QSize(124, 124))
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
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
        print('dropEvent', event)
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


class Dialog_01(QtWidgets.QMainWindow):
    def __init__(self):
        super(QtWidgets.QMainWindow, self).__init__()
        self.listItems = {}

        myQWidget = QtWidgets.QWidget()
        myBoxLayout = QtWidgets.QVBoxLayout()
        myQWidget.setLayout(myBoxLayout)
        self.setCentralWidget(myQWidget)

        self.listWidgetA = ThumbListWidget(self)
        for i in range(12):
            QtWidgets.QListWidgetItem( 'Item ' + str(i), self.listWidgetA)
        myBoxLayout.addWidget(self.listWidgetA)

        self.listWidgetB = ThumbListWidget(self)
        myBoxLayout.addWidget(self.listWidgetB)

        self.connect(self.listWidgetA, QtCore.SIGNAL("dropped"), self.items_dropped)
        self.listWidgetA.currentItemChanged.connect(self.item_clicked)

        self.connect(self.listWidgetB, QtCore.SIGNAL("dropped"), self.items_dropped)
        self.listWidgetB.currentItemChanged.connect(self.item_clicked)

    def items_dropped(self, arg):
        print('items_dropped', arg)

    def item_clicked(self, arg):
        print(arg)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    dialog_1 = Dialog_01()
    dialog_1.show()
    dialog_1.resize(480,320)
    sys.exit(app.exec_())