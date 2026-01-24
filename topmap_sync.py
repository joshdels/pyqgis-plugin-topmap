import os
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction
from qgis.core import QgsSettings

from .gui.login_dialog import LoginDialog
from .gui.project_list_window import ProjectlistWindow
from .core.topmap_api import TopMapApiClient

PLUGIN_NAME = "TopMap Sync"


class TopMapSync:
    """Main controller for the TopMap Sync plugin."""

    def __init__(self, iface):
        self.iface = iface
        self.window: ProjectlistWindow | None = None
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

        if saved_token:
            # Already authenticated, show project list
            self.show_project_list(token=saved_token)
        else:
            # Prompt login
            self.login = LoginDialog(self.iface.mainWindow())
            if self.login.exec_():
                self.show_project_list(api=self.login.api)

    def show_project_list(
        self, api: TopMapApiClient | None = None, token: str | None = None
    ):
        """
        Open the Project List window.

        If token is provided without api, create a new TopMapApiClient
        and set the token.
        """
        # Prepare API client
        if token and not api:
            api = TopMapApiClient()
            api.token = token
            api.session.headers.update({"Authorization": f"Token {token}"})

        # Create window if not already open
        if self.window:
            self.window.close()
            self.window = None

        self.window = ProjectlistWindow(api=api, parent=self.iface.mainWindow())

        # Show and populate the table
        self.window.show()
        self.window.populate_project_list()
