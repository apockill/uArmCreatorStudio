from PyQt4.QtGui import * 
from PyQt4.QtCore import * 
import sys
 
def main():  
    app 	= QApplication(sys.argv)
    table 	= QTableWidget()
    tableItem 	= QTableWidgetItem()
    
    # initiate table
    table.setWindowTitle("QTableWidget Example @pythonspot.com")
    table.resize(400, 250)
    table.setRowCount(4)
    table.setColumnCount(2)
    
    # set data
    table.setItem(0,0, QTableWidgetItem("Item (1,1)"))
    table.setItem(0,1, QTableWidgetItem("Item (1,2)"))
    table.setItem(1,0, QTableWidgetItem("Item (2,1)"))
    table.setItem(1,1, QTableWidgetItem("Item (2,2)"))
    table.setItem(2,0, QTableWidgetItem("Item (3,1)"))
    table.setItem(2,1, QTableWidgetItem("Item (3,2)"))
    table.setItem(3,0, QTableWidgetItem("Item (4,1)"))
    table.setItem(3,1, QTableWidgetItem("Item (4,2)"))
 
    # show table
    table.show()
    return app.exec_()
 
if __name__ == '__main__':
    main()