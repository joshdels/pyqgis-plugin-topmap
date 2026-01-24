from PyQt5 import QtCore, QtWidgets, uic
from ..core.topmap_api import TopMapApiClient
from ..core.project_manager import ProjectSettingsManager
from qgis.core import QgsSettings
import os


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
        self.newButton.clicked.connect(self.create_new_project)
        self.syncButton.clicked.connect(self.on_sync_clicked)
        self.editButton.clicked.connect(self.on_edit_clicked)
        self.refreshButton.clicked.connect(self.populate_project_list)
        self.folderButton.clicked.connect(self.on_open_project_clicked)
        self.helpButton.clicked.connect(self.on_help_clicked)
        self.closeButton.clicked.connect(self.close)
        self.logoutButton.clicked.connect(self.logout)

        # Fetch Data from the API
        self.populate_project_list()
        self.get_user_profile()

    # -------------------------
    # Button Handlers
    # -------------------------
    def create_new_project(self) -> None:
        QtWidgets.QMessageBox.information(self, "Update", "Feature coming soon!")

    def on_sync_clicked(self) -> None:
        QtWidgets.QMessageBox.information(self, "Update", "Feature coming soon!")

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

            item2 = QtWidgets.QTableWidgetItem(
                project.get("user", {}).get("username", "Unknown")
            )
            item2.setFlags(item2.flags() ^ QtCore.Qt.ItemIsEditable)
            table.setItem(row, 1, item2)

            item3 = QtWidgets.QTableWidgetItem(project.get("created_at", ""))
            item3.setFlags(item3.flags() ^ QtCore.Qt.ItemIsEditable)
            table.setItem(row, 2, item3)

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
