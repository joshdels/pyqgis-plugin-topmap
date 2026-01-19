import os
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction
from .gui.main_dialog import MainDialog


class HelloLayerInfo:
    def __init__(self, iface):
        self.iface = iface
        self.dialog = None

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "icon.png")
        self.action = QAction(
            QIcon(icon_path), "Hello Layer Info", self.iface.mainWindow()
        )
        self.action.triggered.connect(self.run)

        # Add to toolbar
        self.iface.addToolBarIcon(self.action)

        # Add to Plugins menu
        self.iface.addPluginToMenu("&Hello Layer Info", self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        self.iface.removePluginMenu("&Hello Layer Info", self.action)

    def run(self):
        if not self.dialog:
            self.dialog = MainDialog(self.iface)  # pass iface here
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()
