from PyQt5 import QtWidgets

app = QtWidgets.QApplication([])

button = QtWidgets.QPushButton("Click to Exit")
button.setWindowTitle("Goodbye World")
button.clicked.connect(app.quit)

buttonX = QtWidgets.QPushButton("OK button")
buttonX.setWindowTitle("Nothing todo")
buttonX.clicked.connect(app.quit)

button.show()
buttonX.show()

app.exec()
