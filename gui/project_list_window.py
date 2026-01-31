import os

from PyQt5 import QtCore, QtWidgets, uic
from qgis.core import QgsSettings

from ..core.topmap_api import TopMapApiClient
from ..core.project_manager import ProjectSettingsManager
from .project_upload_window import ProjectUploadWindow


class ProjectlistWindow(QtWidgets.QMainWindow):
    """Project list"""

    def __init__(self, api=None, parent=None):
        super().__init__(parent)

        ui_path = os.path.join(
            os.path.dirname(__file__), "..", "ui", "projects_list_window.ui"
        )
        uic.loadUi(ui_path, self)

        # --- ADD THIS TO INJECT THE PATH LABEL ---
        self.refresh_directory_display()

        # Other Windows
        self.api = api or TopMapApiClient()
        self.projectTable.doubleClicked.connect(self.on_table_double_clicked)

        # Buttons
        self.newBtn.clicked.connect(self.create_new_project)
        self.loadBtn.clicked.connect(self.load_projects_to_folder)
        self.editBtn.clicked.connect(self.on_edit_clicked)
        self.refreshBtn.clicked.connect(self.populate_project_list)
        self.folderBtn.clicked.connect(self.on_open_project_clicked)
        self.helpBtn.clicked.connect(self.on_help_clicked)
        self.closeBtn.clicked.connect(self.close)
        self.logoutBtn.clicked.connect(self.logout)

        # Fetch Data from the API
        self.populate_project_list()
        self.get_user_profile()

    # -------------------------
    # Button Handlers
    # -------------------------
    def create_new_project(self) -> None:
        self.project_upload_window = ProjectUploadWindow(api=self.api)
        self.project_upload_window.show()

    def on_edit_clicked(self) -> None:
        QtWidgets.QMessageBox.information(self, "Update", "Feature coming soon!")

    def on_refresh_clicked(self) -> None:
        QtWidgets.QMessageBox.information(self, "Update", "Feature coming soon!")

    def on_open_project_clicked(self) -> None:
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Root")
        if path:
            ProjectSettingsManager.set_root_dir(path)
            self.refresh_directory_display()
            self.statusBar().showMessage(f"Project root updated.", 3000)

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

    # -------------------------
    # Logout
    # -------------------------
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

    # -------------------------
    # Table Logic
    # -------------------------
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

            item2 = QtWidgets.QTableWidgetItem(project.get("created_at", ""))
            item2.setFlags(item2.flags() ^ QtCore.Qt.ItemIsEditable)
            table.setItem(row, 1, item2)

    def load_projects_to_folder(self):
        """Load the file sto pc"""
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

        for project in projects:
            folder_name = project["name"]
            sefe_folder_name = "".join(
                c for c in folder_name if c.isalnum() or c in " _-"
            ).rstrip()
            project_path = os.path.join(base_path, sefe_folder_name)
            os.makedirs(project_path, exist_ok=True)

            files = project.get("files", [])
            if not files:
                print(f"No files in project: {folder_name}")
                continue

            for file in files:
                file_url = file["file"]
                file_name = file["name"]
                safe_file_name = "".join(
                    c for c in file_name if c.isalnum() or c in " ._-"
                ).rstrip()
                file_path = os.path.join(project_path, safe_file_name)

                try:
                    r = self.api.session.get(file_url, stream=True, timeout=10)
                    r.raise_for_status()
                    with open(file_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"Downloaded {file_name} to {project_path}")
                except Exception as e:
                    print(f"Failed to download {file_name}: {e}")

    def on_table_double_clicked(self, index):
        """This runs when you double click"""
        row = index.row()
        project_data = self.projectTable.item(row, 0).data(QtCore.Qt.UserRole)

        if project_data:
            from .project_details_window import ProjectDetailsWindow

            self.details_window = ProjectDetailsWindow(
                project_data,
                parent=self,
                api=self.api,
                username=self.usernameLabel.text(),
            )
            self.details_window.show()
        else:
            print("No data found in the userRole for this row")
