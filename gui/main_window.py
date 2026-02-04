from PyQt5 import QtWidgets, QtCore


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, api, parent=None):
        super().__init__(parent)

        self.api = api
        self.setWindowTitle("TopMap Sync")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        self.stack = QtWidgets.QStackedWidget()
        self.setMinimumSize(700, 700)
        self.setCentralWidget(self.stack)

    def push_page(self, widget):
        self.stack.addWidget(widget)
        self.stack.setCurrentWidget(widget)

    def pop_page(self):
        if self.stack.count() > 1:
            widget = self.stack.currentWidget()
            self.stack.removeWidget(widget)
            widget.deleteLater()
            self.stack.setCurrentIndex(self.stack.count() - 1)
