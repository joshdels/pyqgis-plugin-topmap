import os
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction
from .gui.login_dialog import LoginDialog

PLUGIN_NAME = "TopMap Sync"

class TopMapSync:
    def __init__(self, iface):
        self.iface = iface
        self.dialog = None

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "icon.png")
        self.action = QAction(
            QIcon(icon_path), "TopMap Sync", self.iface.mainWindow()
        )
        self.action.triggered.connect(self.run)

        # Add to toolbar
        self.iface.addToolBarIcon(self.action)

        # Add to Plugins menu
        self.iface.addPluginToMenu("&TopMap Sync", self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        self.iface.removePluginMenu("&TopMap Sync", self.action)

    def run(self):
        if self.dialog is None:
            self.dialog = LoginDialog(self.iface.mainWindow())
        
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()
