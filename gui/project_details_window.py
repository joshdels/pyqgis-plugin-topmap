import os
from PyQt5 import QtWidgets, uic
from qgis.core import QgsSettings


class ProjectDetailsWindow(QtWidgets.QMainWindow):
    """Window to view and edit project details."""

    def __init__(self, project_data, parent=None):
        super().__init__(parent)

        # Load the UI
        ui_path = os.path.join(
            os.path.dirname(__file__), "..", "ui", "project_details_window.ui"
        )
        uic.loadUi(ui_path, self)

        self.project_data = project_data
        self.display_data()

        # Connect buttons
        self.closeButton.clicked.connect(self.close)
        self.pushButton.clicked.connect(self.update_project)
        self.logoutButton.clicked.connect(self.logout)

    def logout(self):
        """Logout the user and close the window."""
        settings = QgsSettings()
        settings.remove("TopMap/token")
        settings.remove("TopMap/username")
        settings.remove("TopMap/remember")

        QtWidgets.QMessageBox.information(
            self, "Logout", "You have been logged out."
        )
        self.close()

    def display_data(self):
        """Populate UI widgets with project data."""
        self.projectNameInput.setText(self.project_data.get("name", ""))
        self.descriptionInput.setPlainText(
            self.project_data.get("description", "No description provided.")
        )
        self.ownerInput.setText(self.project_data.get("owner", "Unknown"))
        self.folderPathInput.setText(self.project_data.get("file", ""))
        self.usernameLabel.setText(self.project_data.get("owner", "User"))

    def update_project(self):
        """Handle 'Update Details' button click (placeholder)."""
        QtWidgets.QMessageBox.information(
            self, "Update", "Feature coming soon!"
        )
