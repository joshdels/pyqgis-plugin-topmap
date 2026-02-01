import os

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import pyqtSignal
from qgis.core import QgsSettings


class ProjectDetailsWindow(QtWidgets.QMainWindow):
    """Window to view and edit project details."""

    projectDeleted = pyqtSignal()

    def __init__(self, project_data, parent=None, api=None, username=None):
        super().__init__(parent)

        # Load the UI
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
        self.loadButton.clicked.connect(self.update_project)  # testing
        self.syncButton.clicked.connect(self.update_project)  # testing
        self.helpButton.clicked.connect(self.update_project)  # testing
        self.closeButton.clicked.connect(self.close)
        self.logoutButton.clicked.connect(self.logout)
        self.deleteBtn.clicked.connect(self.on_delete_clicked)

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

    def on_load_clicked(self):
        """load all projects in the folder"""
        pass

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
