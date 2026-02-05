import os
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import pyqtSignal

from qgis.core import (
    QgsProject,
    QgsProject,
    QgsSettings,
)

from ..core.project_manager import ProjectSettingsManager
from ..core.qgis_process import QgisRasterProcessor, QgisVectorProcessor


class ProjectDetailsPage(QtWidgets.QWidget):
    """Window to view and edit project details."""

    projectDeleted = pyqtSignal()
    backClicked = pyqtSignal()
    closeClicked = pyqtSignal()
    logoutClicked = pyqtSignal()

    def __init__(self, project_data, parent=None, api=None, username=None):
        super().__init__(parent)

        ui_path = os.path.join(
            os.path.dirname(__file__), "..", "ui", "project_details_window.ui"
        )
        uic.loadUi(ui_path, self)

        self.project_data = project_data
        self.api = api

        if username:
            self.usernameLabel.setText(username)
        else:
            self.usernameLabel.setText(self.project_data.get("user", "User1"))

        self.display_data()

        # Connect buttons
        self.backBtn.clicked.connect(self.backClicked.emit)
        self.closeBtn.clicked.connect(self.closeClicked.emit)
        self.loadButton.clicked.connect(self.on_load_clicked)
        self.syncButton.clicked.connect(self.on_sync_clicked)
        self.helpBtn.clicked.connect(self.update_project)  # testing
        self.closeBtn.clicked.connect(self.close)
        self.logoutButton.clicked.connect(self.logout)
        self.deleteBtn.clicked.connect(self.on_delete_clicked)
        self.containerizeBtn.clicked.connect(self.on_containerize_clicked)

    def logout(self):
        """Logout the user and close the window."""
        settings = QgsSettings()
        settings.remove("TopMap/token")
        settings.remove("TopMap/username")
        settings.remove("TopMap/remember")

        QtWidgets.QMessageBox.information(self, "Logout", "You have been logged out.")
        self.logoutClicked.emit()

    def display_data(self):
        """Populate UI widgets with project data."""
        self.projectNameInput.setText(self.project_data.get("name", ""))
        self.descriptionInput.setPlainText(
            self.project_data.get("description", "No description provided.")
        )

    def update_project(self):
        """Handle 'Update Details' button click (placeholder)."""
        QtWidgets.QMessageBox.information(self, "Update", "Feature coming soon!")

    def on_load_clicked(self):
        project_name = self.project_data.get("name")
        if not project_name:
            QtWidgets.QMessageBox.warning(
                self, "Load Project", "Project name not found."
            )
            return

        root_dir = ProjectSettingsManager.get_root_dir()
        if not root_dir or not os.path.exists(root_dir):
            QtWidgets.QMessageBox.warning(
                self, "Load Project", "Root directory not set or does not exist."
            )
            return

        project_folder = os.path.join(root_dir, "TopMapSync", project_name)
        if not os.path.exists(project_folder):
            QtWidgets.QMessageBox.warning(
                self, "Load Project", f"Project folder not found:\n{project_folder}"
            )
            return

        # Scan for .qgz files
        qgz_files = [f for f in os.listdir(project_folder) if f.endswith(".qgz")]
        if not qgz_files:
            QtWidgets.QMessageBox.warning(
                self, "Load Project", "No .qgz files found in project folder."
            )
            return

        qgz_path = os.path.join(project_folder, qgz_files[0])

        # Load project
        project = QgsProject.instance()
        success = project.read(qgz_path)

        if success:
            project.setPresetHomePath(project_folder)

            QtWidgets.QMessageBox.information(
                self, "Load Project", f"Project '{qgz_files[0]}' loaded successfully."
            )
        else:
            QtWidgets.QMessageBox.critical(
                self, "Load Project", f"Failed to load project '{qgz_files[0]}."
            )

    def on_sync_clicked(self):
        project_id = self.project_data.get("id")
        project_name = self.project_data.get("name")

        if not project_id or not project_name:
            QtWidgets.QMessageBox.warning(self, "Sync", "Project ID or name not found")
            return

        root_dir = ProjectSettingsManager.get_root_dir()
        if not root_dir or not os.path.exists(root_dir):
            QtWidgets.QMessageBox.warning(
                self, "Sync", "Root directory not set or missing."
            )
            return

        project_folder = os.path.join(root_dir, "TopMapSync", project_name)
        if not os.path.exists(project_folder):
            QtWidgets.QMessageBox.warning(
                self, "Sync", f"Project folder not found:\n{project_folder}"
            )
            return

        # Folder Looping
        uploaded_count = 0
        errors = []

        for root, dirs, files in os.walk(project_folder):
            for filename in files:
                # Only allow project files
                if not (filename.endswith((".qgz", ".gpkg", ".qml", ".tif", ".tiff"))):
                    continue

                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, project_folder)

                try:
                    result = self.api.upload_file(
                        project_id, full_path, relative_path=rel_path
                    )
                    uploaded_count += 1
                    print(f"Uploaded: {rel_path} -> {result}")
                except Exception as e:
                    errors.append(f"{rel_path}: {str(e)}")

        if errors:
            QtWidgets.QMessageBox.warning(
                self,
                "Sync Completed",
                f"Uploaded {uploaded_count} files with errors:\n" + "\n".join(errors),
            )
        else:
            QtWidgets.QMessageBox.information(
                self, "Sync Completed", f"Successfully uploaded {uploaded_count} files!"
            )

    def on_delete_clicked(self):
        project_id = self.project_data.get("id")

        if not project_id:
            QtWidgets.QMessageBox.warning(
                self, "Delete Project", "Project ID not found. Cannot delete"
            )

        reply = QtWidgets.QMessageBox.question(
            self,
            "Delete Project",
            "Are you sure you want to delete this project?\nThis action cannot undo",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )

        if reply != QtWidgets.QMessageBox.Yes:
            return

        try:
            self.api.delete_project(project_id)

            QtWidgets.QMessageBox.information(
                self, "Deleted", "Project deleted successfully."
            )

            self.projectDeleted.emit()
            self.close()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))

    def on_containerize_clicked(self):
        """Handles saving raster layers to folder, vectors to data.gpkg, and makes project portable."""
        project = QgsProject.instance()
        project_name = self.project_data.get("name")

        root_dir = ProjectSettingsManager.get_root_dir()
        project_folder = os.path.join(root_dir, "TopMapSync", project_name)
        os.makedirs(project_folder, exist_ok=True)

        qgz_path = os.path.join(project_folder, f"{project_name}.qgz")

        project.setFileName(qgz_path)
        project.setPresetHomePath(project_folder)
        project.writeEntry("Paths", "/Absolute", False)

        project.write()

        total_errors = []

        raster_processor = QgisRasterProcessor(project, project_folder)
        total_errors.extend(raster_processor.process_rasters())

        vector_processor = QgisVectorProcessor(project, project_folder)
        total_errors.extend(vector_processor.process_vector())

        success = project.write(qgz_path)

        if success:
            project.read(qgz_path)
            msg = "Project is now fully portable (Rasters + GPKG)!"
            if total_errors:
                msg += "\n\nWarnings: \n" + "\n".join(total_errors)
            QtWidgets.QMessageBox.information(self, "Success", msg)
        else:
            QtWidgets.QMessageBox.critical(self, "Error", "Failed to finalize project.")
