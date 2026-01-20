from PyQt5 import QtCore, QtWidgets, uic
from ..core.topmap_api import TopMapApiClient
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

        # Populate table initially
        self.populate_project_list()

    # -------------------------
    # Button Handlers
    # -------------------------
    def create_new_project(self) -> None:
        pass

    def on_sync_clicked(self) -> None:
        pass

    def on_edit_clicked(self) -> None:
        pass

    def on_refresh_clicked(self) -> None:
        pass

    def on_open_project_clicked(self) -> None:
        pass

    def on_help_clicked(self) -> None:
        pass

    # -------------------------
    # Logout
    # -------------------------
    def logout(self):
        """Logout the user and close the window"""
        settings = QgsSettings()
        settings.remove("TopMap/token")
        settings.remove("TopMap/username")
        settings.remove("TopMap/remember")
        QtWidgets.QMessageBox.information(self, "Logout", "You have been logged out.")
        self.close()

    # -------------------------
    # Table Logic
    # -------------------------
    def closeEvent(self, event):
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

            item2 = QtWidgets.QTableWidgetItem(project.get("owner", "Unknown"))
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

            self.details_window = ProjectDetailsWindow(project_data, self)
            self.details_window.show()
        else:
            print("No data found in the userRole for this row")
