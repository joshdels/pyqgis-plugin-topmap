import os

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import pyqtSignal


from ..core.project_manager import ProjectSettingsManager
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
            # Create the project on the server
            created_project = self.api.create_project(payload)
            project_id = created_project.get("id")

            # Emit signal to refresh project list
            self.projectCreated.emit()

            root_dir = ProjectSettingsManager.get_root_dir()
            if root_dir and project_id:
                base_path = os.path.join(root_dir, "TopMapSync")
                os.makedirs(base_path, exist_ok=True)

                try:
                    result = self.api.download_project(project_id, base_path)

                    if result["downloaded_count"] > 0:
                        QtWidgets.QMessageBox.information(
                            self,
                            "Project Created",
                            f"Project '{name}' created successfully!\n\n"
                            f"Location: {result['project_path']}",
                        )
                    else:
                        safe_folder_name = "".join(
                            c for c in name if c.isalnum() or c in " _-"
                        ).rstrip()
                        project_path = os.path.join(base_path, safe_folder_name)
                        os.makedirs(project_path, exist_ok=True)

                except Exception as e:
                    QtWidgets.QMessageBox.warning(
                        self,
                        "Project Created",
                        f"Project '{name}' created on server.\n\n",
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
