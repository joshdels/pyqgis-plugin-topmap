import os

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import pyqtSignal

from ..core.topmap_api import TopMapApiClient


class ProjectUploadWindow(QtWidgets.QMainWindow):
    """Project list"""

    projectCreated = pyqtSignal()

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

        try:
            self.api.create_project(payload)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))
            return

        self.projectCreated.emit()

        QtWidgets.QMessageBox.information(
            self, "Project Created", f"Project created successfully"
        )

        self.close()
