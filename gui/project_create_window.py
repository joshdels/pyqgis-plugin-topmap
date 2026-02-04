import os

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import pyqtSignal
from qgis.core import QgsProject, QgsSettings

from ..core.project_manager import ProjectSettingsManager


class ProjectUploadPage(QtWidgets.QWidget):
    """Create a new project, upload to cloud, and initialize its local QGIS workspace."""

    projectCreated = pyqtSignal()
    backClicked = pyqtSignal()
    closeClicked = pyqtSignal()
    logoutClicked = pyqtSignal()

    def __init__(self, api, username=None, parent=None):
        super().__init__(parent)

        ui_path = os.path.join(
            os.path.dirname(__file__), "..", "ui", "project_new_window.ui"
        )
        uic.loadUi(ui_path, self)

        if api is None:
            raise ValueError("ProjectUploadWindows requires a logged-in API key")

        self.api = api
        self.username = username
        self.usernameLabel.setText(self.username or "user")

        # Connect buttons
        self.backBtn.clicked.connect(self.backClicked.emit)
        self.createBtn.clicked.connect(self.on_create_clicked)
        self.logoutBtn.clicked.connect(self.logout)
        self.helpBtn.clicked.connect(self.on_temprary_clicked)
        self.closeBtn.clicked.connect(self.closeClicked.emit)

    def on_temprary_clicked(self):
        """Placeholder handler for upcoming features."""
        QtWidgets.QMessageBox.information(self, "Update", "Feature coming soon!")

    def closeEvent(self, event):
        event.accept()

    def logout(self):
        """Logout the user and close the window"""
        try:
            if self.api:
                self.api.logout()

        except Exception as e:
            print(f"Logout API Error {e}")

        settings = QgsSettings()
        settings.remove("TopMap")

        self.usernameLabel.clear()
        self.api = None

        QtWidgets.QMessageBox.information(self, "Logout", "You have been logged out.")

        self.logoutClicked.emit()

    def on_create_clicked(self):
        name = self.projectNameInput.text()
        description = self.descriptionInput.toPlainText()
        is_private = self.privateCheckbox.isChecked()

        if not name:
            QtWidgets.QMessageBox.warning(
                self, "Validation Error", "Project name is required."
            )
            return

        payload = {
            "name": name,
            "description": description,
            "is_private": is_private,
        }

        try:
            created_project = self.api.create_project(payload)
            project_id = created_project.get("id")

            self.projectCreated.emit()

            root_dir = ProjectSettingsManager.get_root_dir()
            if root_dir and project_id:
                base_path = os.path.join(root_dir, "TopMapSync")
                os.makedirs(base_path, exist_ok=True)

                safe_folder_name = "".join(
                    c for c in name if c.isalnum() or c in " _-"
                ).rstrip()
                project_path = os.path.join(base_path, safe_folder_name)
                os.makedirs(project_path, exist_ok=True)

                qgz_path = os.path.join(project_path, f"{safe_folder_name}.qgz")
                created = self._create_qgz_file(qgz_path)

                if not created:
                    return

                QtWidgets.QMessageBox.information(
                    self,
                    "Project Created",
                    f"{name} created successfully!\n\n" f"Location: {project_path}",
                )
            else:
                QtWidgets.QMessageBox.information(
                    self,
                    "Project Created",
                    f"Project '{name}' created successfully!\n\n",
                )

            self.close()

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))
            return

    def _create_qgz_file(self, project_path: str) -> bool:
        project = QgsProject.instance()
        project.clear()

        success = project.write(project_path)

        if not success:
            QtWidgets.QMessageBox.warning(
                self,
                "Failed Initialization",
                "Failed to create QGIS project (.qgz) file",
            )
            return False

        return True
