import os
from PyQt5 import QtWidgets, uic
from qgis.core import QgsSettings


class ProjectDetailsWindow(QtWidgets.QMainWindow):
    """Window to view and edit project details."""

    def __init__(self, project_data, parent=None, api=None, username=None):
        super().__init__(parent)

        # Load the UI
        ui_path = os.path.join(
            os.path.dirname(__file__), "..", "ui", "project_details_window.ui"
        )
        uic.loadUi(ui_path, self)

        self.project_data = project_data

        if username:
            self.usernameLabel.setText(username)
        else:
            self.usernameLabel.setText(self.project_data.get("user", "User1"))

        self.display_data()

        # Connect buttons
        self.loadButton.clicked.connect(self.update_project)  # testing
        self.syncButton.clicked.connect(self.update_project)  # testing
        self.helpButton.clicked.connect(self.update_project)  # testing
        self.closeButton.clicked.connect(self.close)
        self.logoutButton.clicked.connect(self.logout)

    def logout(self):
        """Logout the user and close the window."""
        settings = QgsSettings()
        settings.remove("TopMap/token")
        settings.remove("TopMap/username")
        settings.remove("TopMap/remember")

        QtWidgets.QMessageBox.information(self, "Logout", "You have been logged out.")
        self.close()

    def display_data(self):
        """Populate UI widgets with project data."""
        self.projectNameInput.setText(self.project_data.get("name", ""))
        self.descriptionInput.setPlainText(
            self.project_data.get("description", "No description provided.")
        )

        self.folderPathInput.setText(self.project_data.get("file", ""))

    def update_project(self):
        """Handle 'Update Details' button click (placeholder)."""
        QtWidgets.QMessageBox.information(self, "Update", "Feature coming soon!")


    def load_projects(self):
        """load all projects in the folder"""
        pass