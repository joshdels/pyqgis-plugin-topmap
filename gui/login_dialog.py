from PyQt5 import QtWidgets, uic
from ..core.login import TopMapApiClient
import os


class LoginDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        ui_path = os.path.join(os.path.dirname(__file__), "..", "ui", "login_dialog.ui")
        uic.loadUi(ui_path, self)

        self.api = TopMapApiClient()

        self.signinButton.clicked.connect(self.handle_login)

    def handle_login(self):
        username = self.usernameInput.text()
        password = self.passwordInput.text()
        remember = self.rememberCheckbox.isChecked()

        if not username or not password:
            QtWidgets.QMessageBox.warning(self, "Login", "Enter username and password")
            return

        try:
            token = self.api.login(username, password)
            QtWidgets.QMessageBox.information(self, "Success", "Login sucessful!")
            if remember:
                self.save_token(token)
            self.accept()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Login failed", str(e))

    def save_token(self, token):
        settings = QtWidgets.QSettings("TopMap", "TopMapPlugin")
        settings.setValue("token", token)
