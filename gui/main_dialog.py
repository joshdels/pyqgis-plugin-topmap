import os
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog
from ..core.layer_info import get_active_layer_info

ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ui', 'main_dialog.ui')
ui_path = os.path.normpath(ui_path)

FORM_CLASS, _ = uic.loadUiType(ui_path)

class MainDialog(QDialog, FORM_CLASS):
    def __init__(self, iface, parent=None):
        super(MainDialog, self).__init__(parent)
        self.iface = iface  # store iface
        self.setupUi(self)
        self.refresh_button.clicked.connect(self.refresh_info)
        self.refresh_info()

    def refresh_info(self):
        name, count = get_active_layer_info(self.iface)  # pass iface
        if name:
            self.label_layer_name.setText(f"Layer: {name}")
            self.label_feature_count.setText(f"Features: {count}")
        else:
            self.label_layer_name.setText("No vector layer active")
            self.label_feature_count.setText("")
