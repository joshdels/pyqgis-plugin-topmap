import os
from PyQt5 import QtCore, QtWidgets, uic
from ..core.topmap_api import TopMapApiClient
from qgis.core import QgsSettings


class LoginDialog(QtWidgets.QDialog):
    """
    Login dialog for TopMapSync plugin.

    Handles authentication via TopMap API. Saves token and user preferences
    in QGIS QgsSettings if "Remember me" is checked.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Load UI
        ui_path = os.path.join(os.path.dirname(__file__), "..", "ui", "login_dialog.ui")
        uic.loadUi(ui_path, self)

        self.api = TopMapApiClient()
        self.settings = QgsSettings()

        self.passwordInput.setEchoMode(QtWidgets.QLineEdit.Password)
        self.signinButton.clicked.connect(self.handle_login)
        self.showBtn.clicked.connect(self.toggle_password_visibility)
        self.showBtn.setCheckable(True)

        saved_username = self.settings.value("TopMap/username", "")
        self.usernameInput.setText(saved_username)

        self.registerLink.setText(
            '<a href="https://topmapsolutions.com/">Create account</a>'
        )
        self.registerLink.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
        self.registerLink.setOpenExternalLinks(True)

    def handle_login(self) -> None:
        """Attempt login with entered username and password."""
        username = self.usernameInput.text().strip()
        password = self.passwordInput.text()
        remember = self.rememberCheckbox.isChecked()

        if not username or not password:
            QtWidgets.QMessageBox.warning(
                self, "Login", "Please enter both username and password."
            )
            return

        try:
            token = self.api.login(username, password)

            self.api.token = token
            self.api.session.headers.update({"Authorization": f"Token {token}"})

            if remember:
                self.settings.setValue("TopMap/token", token)
                self.settings.setValue("TopMap/username", username)
                self.settings.setValue("TopMap/remember", True)
            else:
                self.settings.remove("TopMap/token")
                self.settings.setValue("TopMap/remember", False)

            self.accept()

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Login Failed", str(e))
            self.forgotLink.setVisible(True)

    def toggle_password_visibility(self, checked):
        if checked:
            self.passwordInput.setEchoMode(QtWidgets.QLineEdit.Normal)
            self.showBtn.setText("Hide")
        else:
            self.passwordInput.setEchoMode(QtWidgets.QLineEdit.Password)
            self.showBtn.setText("Show")
