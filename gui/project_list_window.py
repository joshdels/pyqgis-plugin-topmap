import os
import shutil
import requests
from datetime import datetime

from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtCore import pyqtSignal
from qgis.core import QgsSettings


from ..core.topmap_api import TopMapApiClient
from ..core.project_manager import ProjectSettingsManager
from .project_create_window import ProjectUploadPage


class ProjectlistPage(QtWidgets.QWidget):
    """Project list"""

    openProject = pyqtSignal(dict)
    createProject = pyqtSignal()
    closeClicked = pyqtSignal()
    statusMessage = pyqtSignal(str)

    def __init__(self, api=None, parent=None):
        super().__init__(parent)

        ui_path = os.path.join(
            os.path.dirname(__file__), "..", "ui", "projects_list_window.ui"
        )
        uic.loadUi(ui_path, self)

        self.refresh_directory_display()

        # Other Windows
        self.api = api or TopMapApiClient()
        self.projectTable.doubleClicked.connect(self.on_table_double_clicked)

        # Buttons
        self.closeBtn.clicked.connect(self.closeClicked.emit)
        self.newBtn.clicked.connect(self.create_new_project)
        self.loadBtn.clicked.connect(self.load_projects_to_folder)
        self.editBtn.clicked.connect(self.on_edit_clicked)
        self.refreshBtn.clicked.connect(self.populate_project_list)
        self.folderBtn.clicked.connect(self.on_open_project_clicked)
        self.helpBtn.clicked.connect(self.on_help_clicked)
        self.logoutBtn.clicked.connect(self.logout)

        # Fetch Data from the API
        self.populate_project_list()
        self.get_user_profile()

    # -------------------------
    # Button Handlers
    # -------------------------
    def create_new_project(self) -> None:
        self.createProject.emit()

    def on_edit_clicked(self) -> None:
        QtWidgets.QMessageBox.information(self, "Update", "Feature coming soon!")

    def on_refresh_clicked(self) -> None:
        QtWidgets.QMessageBox.information(self, "Update", "Feature coming soon!")

    def on_open_project_clicked(self) -> None:
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Root")
        if path:
            ProjectSettingsManager.set_root_dir(path)
            self.refresh_directory_display()
            self.statusMessage.emit("Project root updated.")

    def refresh_directory_display(self):
        """Update the label that sits below the 'Set Root Folder' button."""
        current_path = ProjectSettingsManager.get_root_dir()
        if current_path:
            display_path = (
                (current_path[:27] + "...") if len(current_path) > 30 else current_path
            )
            self.rootPathLabel.setText(display_path)
            self.rootPathLabel.setToolTip(current_path)
            self.rootPathLabel.setStyleSheet(
                "color: #2e7d32; font-size: 10px; font-style: bold;"
            )
        else:
            self.rootPathLabel.setText("⚠️ Root Folder Not Set")
            self.rootPathLabel.setStyleSheet(
                "color: #d32f2f; font-size: 10px; font-style: bold;"
            )

    def update_project(self):
        """Handle 'Update Details' button click (placeholder)."""
        QtWidgets.QMessageBox.information(self, "Update", "Feature coming soon!")

    def on_help_clicked(self) -> None:
        QtWidgets.QMessageBox.information(self, "Update", "Feature coming soon!")

    # -------------------------
    # User Information
    # -------------------------
    def get_user_profile(self):
        """Fetch user information from the API"""
        try:
            user_details = self.api.get_user_profile()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "API Error", str(e))
            return

        self.usernameLabel.setText(user_details.get("username", "user"))

        profile_info = user_details.get("profile", {})

    def logout(self):
        """Logout the user and close the window"""

        try:
            if self.api:
                self.api.logout()
        except Exception as e:
            print(f"Logout API Error")

        settings = QgsSettings()
        settings.remove("TopMap")

        self.usernameLabel.clear()
        self.api = None

        QtWidgets.QMessageBox.information(self, "Logout", "You have been logged out.")
        self.close()

    def closeEvent(self, event):
        self.api = None
        event.accept()

    def populate_project_list(self):
        """Fetch projects from the API"""
        try:
            projects = self.api.get_projects()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "API Error", str(e))
            return

        table = self.projectTable
        table.setRowCount(len(projects))
        table.setSortingEnabled(True)

        for idx, project in enumerate(projects, start=1):
            row = idx - 1

            item1 = QtWidgets.QTableWidgetItem(project.get("name", ""))
            item1.setFlags(item1.flags() ^ QtCore.Qt.ItemIsEditable)
            item1.setData(QtCore.Qt.UserRole, project)
            table.setItem(row, 0, item1)

            raw_date = project.get("created_at", "")

            try:
                if raw_date.endswith("Z"):
                    raw_date = raw_date.replace("Z", "+00:00")

                dt = datetime.fromisoformat(raw_date)
                formatted_date = dt.strftime("%Y-%m-%d -- %H:%M -- (%Z)")
            except Exception:
                formatted_date = raw_date

            item2 = QtWidgets.QTableWidgetItem(formatted_date)
            item2.setFlags(item2.flags() ^ QtCore.Qt.ItemIsEditable)
            table.setItem(row, 1, item2)

        table.setColumnWidth(0, 460)
        table.setColumnWidth(1, 200)

    def load_projects_to_folder(self):
        """Load project files to local folder and cleanup deleted projects."""
        try:
            projects = self.api.get_projects()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "API Error", str(e))
            return

        root_dir = ProjectSettingsManager.get_root_dir()
        if not root_dir:
            QtWidgets.QMessageBox.warning(
                self,
                "No root Folder",
                "Please set a root folder first using the 'Set Folder Button'",
            )
            return

        base_path = os.path.join(root_dir, "TopMapSync")
        os.makedirs(base_path, exist_ok=True)

        # ----------------- Cleanup -----------------
        project_names_api = set(
            "".join(c for c in p["name"] if c.isalnum() or c in " _-").rstrip()
            for p in projects
        )

        local_folders = set(os.listdir(base_path))
        for folder in local_folders:
            folder_path = os.path.join(base_path, folder)
            if folder not in project_names_api and os.path.isdir(folder_path):
                try:
                    shutil.rmtree(folder_path)
                    print(f"Removed local folder deleted in backend: {folder_path}")
                except Exception as e:
                    print(f"Failed to remove folder {folder_path}: {e}")

        # ----------------- Download -----------------
        for project in projects:
            folder_name = project["name"]
            safe_folder_name = "".join(
                c for c in folder_name if c.isalnum() or c in " _-"
            ).rstrip()
            project_path = os.path.join(base_path, safe_folder_name)
            os.makedirs(project_path, exist_ok=True)

            files = project.get("files", [])
            if not files:
                print(f"No files in project: {folder_name}")
                continue

            for file in files:
                file_url = file["file"]
                file_name = file["name"]

                name_part, extension = os.path.splitext(file_name)

                clean_name = "".join(
                    c for c in name_part if c.isalnum() or c in " _-"
                ).rstrip()

                safe_file_name = f"{clean_name}{extension}"
                file_path = os.path.join(project_path, safe_file_name)

                try:
                    r = requests.get(file_url, stream=True, timeout=15, headers={})
                    r.raise_for_status()

                    with open(file_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"Downloaded {file_name} to {project_path}")
                except Exception as e:
                    print(f"Failed to download {file_name}: {e}")

        QtWidgets.QMessageBox.information(
            self,
            "Projects Loaded!",
            f"All projects from the database loaded successfully!\n\nLocation: {base_path}",
        )

    def on_table_double_clicked(self, index):
        """This runs when you double click"""
        row = index.row()
        project_data = self.projectTable.item(row, 0).data(QtCore.Qt.UserRole)

        if project_data:
            self.openProject.emit(project_data)
