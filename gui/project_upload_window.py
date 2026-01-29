from PyQt5 import QtCore, QtWidgets, uic
from ..core.topmap_api import TopMapApiClient
import os


class ProjectUploadWindow(QtWidgets.QMainWindow):
    """Project list"""

    def __init__(self, api, parent=None):
        super().__init__(parent)

        ui_path = os.path.join(
            os.path.dirname(__file__), "..", "ui", "project_new_window.ui"
        )
        uic.loadUi(ui_path, self)

        if api is None:
            raise ValueError("ProjectUploadWindows requires a logged-in API key")

        self.api = api

        # Connect buttons
        self.createBtn.clicked.connect(self.on_create_clicked)
        self.helpBtn.clicked.connect(self.on_temprary_clicked)
        self.closeBtn.clicked.connect(self.close)

    def on_temprary_clicked(self):
        """Handle 'Update Details' button click (placeholder)."""
        QtWidgets.QMessageBox.information(self, "Update", "Feature coming soon!")

    def closeEvent(self, event):
        event.accept()

    def on_create_clicked(self):
        name = self.projectNameInput.text()
        description = self.descriptionInput.toPlainText()
        is_private = self.privateCheckbox.isChecked()

        payload = {
            "name": name,
            "description": description,
            "is_private": is_private,
        }

        update_project = self.api.create_project(payload)

        QtWidgets.QMessageBox.information(
            self, "Project Created", f"Project created successfully:\n{update_project}"
        )
