



# #EXAMPLE 1: Python wrapper is created but C++ object isn't
# from PyQt4.QtCore import QObject
# class MyObject(QObject):
#     def __init__(self):
#         QObject.__init__(self)   #Without this line of code, the program crashes
#         self.field = 7
#
# obj = MyObject()
# print(obj.field)
# obj.setObjectName("New object")



# #EXAMPLE 2: Python wrapper is garbage-collected but C++ object still exists
# from PyQt4.QtGui import QApplication, QLabel
# def createLabel():
#     label = QLabel("Hello, world!")
#     label.show()
#     return label            #Without this line
#
# app = QApplication([])
# label = createLabel()       #Without the label =
#
# app.exec_()

from PyQt4.QtCore import QTimer
from PyQt4.QtGui import QApplication, QWidget

app = QApplication([])

widget = QWidget()
widget.setWindowTitle("Dead widget")
widget.deleteLater()

QTimer.singleShot( 0, app.quit)  # Make the application quit just after start
app.exec_()                      # Execute the application to call deleteLater()

print(widget.windowTitle())