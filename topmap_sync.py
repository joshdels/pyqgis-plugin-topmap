import os
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction
from qgis.core import QgsSettings

from .gui.login_dialog import LoginDialog
from .core.topmap_api import TopMapApiClient
from .gui.main_window import MainWindow
from .gui.project_details_window import ProjectDetailsPage
from .gui.project_list_window import ProjectlistPage
from .gui.project_create_window import ProjectUploadPage

PLUGIN_NAME = "TopMap Sync"


class TopMapSync:
    """Main controller for the TopMap Sync plugin."""

    def __init__(self, iface):
        self.iface = iface
        self.login: LoginDialog | None = None
        self.action: QAction | None = None

    def initGui(self):
        """Set up toolbar button and menu entry."""
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "icon.png")
        self.action = QAction(QIcon(icon_path), PLUGIN_NAME, self.iface.mainWindow())
        self.action.setObjectName("TopMapSyncAction")
        self.action.setWhatsThis("Connect to TopMapSync database")
        self.action.setStatusTip(PLUGIN_NAME)

        # Add to toolbar and menu
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(f"&{PLUGIN_NAME}", self.action)

        # Connect click to plugin entry point
        self.action.triggered.connect(self.run)

    def unload(self):
        """Clean up toolbar and menu on plugin unload."""
        if self.action:
            self.iface.removeToolBarIcon(self.action)
            self.iface.removePluginMenu(f"&{PLUGIN_NAME}", self.action)

    def run(self):
        """Plugin entry point when user clicks the icon."""
        settings = QgsSettings()
        saved_token = settings.value("TopMap/token", "")

        api = TopMapApiClient()

        if saved_token:
            api.token = saved_token
            api.session.headers.update({"Authorization": f"Token {saved_token}"})
            try:
                user_details = api.get_user_profile()
                self.username = user_details.get("username", "user")
            except Exception as e:
                self.username = "user"
                print(f"Failed to fetch user profile: {e}")

            self.open_main(api)
        else:
            self.login = LoginDialog(self.iface.mainWindow())
            if self.login.exec_():
                api = self.login.api
                try:
                    user_details = api.get_user_profile()
                    self.username = user_details.get("username", "user")
                except Exception as e:
                    self.username = "user"
                    print(f"Failed to fetch user profile: {e}")
                self.open_main(api)

    # CONTROLLERS

    def open_main(self, api):
        self.main_window = MainWindow(api, parent=self.iface.mainWindow())

        project_list = ProjectlistPage(api=api)
        self.main_window.push_page(project_list)

        project_list.closeClicked.connect(self.main_window.close)

        # signals in main window
        project_list.createProject.connect(
            lambda: self.open_create_project(api, self.username)
        )
        project_list.openProject.connect(
            lambda data: self.open_project_details(api, data, self.username)
        )

        self.main_window.show()

    def open_create_project(self, api, username):
        page = ProjectUploadPage(api=api, username=username, parent=self.main_window)
        page.backClicked.connect(self.main_window.pop_page)
        page.projectCreated.connect(self.open_project_created)
        page.closeClicked.connect(self.main_window.close)
        self.main_window.push_page(page)

    def open_project_created(self):
        self.main_window.pop_page()

        current = self.main_window.stack.currentWidget()
        if hasattr(current, "populate_project_list"):
            current.populate_project_list()

    def on_project_deleted(self):
        self.main_window.pop_page()

    def open_project_details(self, api, project_data, username):
        page = ProjectDetailsPage(
            project_data=project_data,
            api=api,
            username=username,
            parent=self.main_window,
        )

        page.backClicked.connect(self.main_window.pop_page)
        page.projectDeleted.connect(self.on_project_deleted)
        page.closeClicked.connect(self.main_window.close)
        self.main_window.push_page(page)
