import os

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtXml import QDomDocument

from qgis.core import (
    QgsVectorLayer,
    QgsProject,
    QgsVectorFileWriter,
    QgsSettings,
    QgsCoordinateReferenceSystem,
    QgsFields,
    QgsWkbTypes,
    QgsRasterLayer,
)

from ..core.project_manager import ProjectSettingsManager


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
        self.loadButton.clicked.connect(self.on_load_clicked)  # testing
        self.syncButton.clicked.connect(self.update_project)  # testing
        self.helpButton.clicked.connect(self.update_project)  # testing
        self.closeButton.clicked.connect(self.close)
        self.logoutButton.clicked.connect(self.logout)
        self.deleteBtn.clicked.connect(self.on_delete_clicked)
        self.geoBtn.clicked.connect(self.on_geopackage_clicked)

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
        """Load the QGIS project into QGIS"""
        project_name = self.project_data.get("name")

        if not project_name:
            QtWidgets.QMessageBox.warning(
                self, "Load Project", "Project folder not found."
            )

        root_dir = ProjectSettingsManager.get_root_dir()
        if not root_dir or not os.path.exists(root_dir):
            QtWidgets.QMessageBox.warning(
                self, "Load Project", "Root folder not set or does not exists."
            )
            return

        project_folder = os.path.join(root_dir, "TopMapSync", project_name)
        if not os.path.exists(project_folder):
            QtWidgets.QMessageBox.warning(
                self, "Load Project", f"Project folder not found:\n{project_folder}"
            )
            return

        qgz_files = [f for f in os.listdir(project_folder) if f.endswith(".qgz")]
        if not qgz_files:
            QtWidgets.QMessageBox.warning(
                self, "Load Project", "No .qgz file found in the project folder."
            )
            return

        project_file = os.path.join(project_folder, qgz_files[0])
        try:
            QgsProject.instance().read(project_file)
            QtWidgets.QMessageBox.information(
                self, "Load Project", f"Project loaded: {qgz_files[0]}"
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Load Project", f"Failed to load project\n{str(e)}"
            )

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

    def on_geopackage_clicked(self):
        """Create GeoPackage and export all layers to it"""

        project_name = self.project_data.get("name")
        if not project_name:
            QtWidgets.QMessageBox.warning(self, "GeoPackage", "Project name not found.")
            return

        root_dir = ProjectSettingsManager.get_root_dir()
        if not root_dir or not os.path.exists(root_dir):
            QtWidgets.QMessageBox.warning(
                self, "GeoPackage", "Root directory not set or missing."
            )
            return

        project_folder = os.path.join(root_dir, "TopMapSync", project_name)
        os.makedirs(project_folder, exist_ok=True)

        gpkg_path = os.path.join(project_folder, "data.gpkg")

        # Get all layers from QGIS
        layers = QgsProject.instance().mapLayers().values()
        vector_layers = [l for l in layers if isinstance(l, QgsVectorLayer)]

        if not vector_layers:
            QtWidgets.QMessageBox.information(
                self, "GeoPackage", "No vector layers found in QGIS."
            )
            return

        # Save layer info INCLUDING styles before removing
        layers_to_export = []
        for layer in vector_layers:
            layers_to_export.append(
                {
                    "layer": layer.clone(),
                    "name": layer.name().replace(" ", "_"),
                    "style": layer.styleManager().style(
                        layer.styleManager().currentStyle()
                    ),
                }
            )

        # Remove all layers from QGIS to unlock the GeoPackage
        QgsProject.instance().removeAllMapLayers()

        # Export each vector layer
        errors = []
        success_count = 0
        first_layer = True

        for layer_data in layers_to_export:
            layer_name = layer_data["name"]
            layer = layer_data["layer"]

            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "GPKG"
            options.layerName = layer_name

            # First layer creates/overwrites the file, rest append
            if first_layer:
                options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
                first_layer = False
            else:
                options.actionOnExistingFile = (
                    QgsVectorFileWriter.CreateOrOverwriteLayer
                )

            error = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer,
                gpkg_path,
                QgsProject.instance().transformContext(),
                options,
            )

            if error[0] != QgsVectorFileWriter.NoError:
                errors.append(f"{layer_name}: {error[1]}")
            else:
                # After successful export, save the style INSIDE the GeoPackage
                uri = f"{gpkg_path}|layername={layer_name}"
                temp_layer = QgsVectorLayer(uri, layer_name, "ogr")
                if temp_layer.isValid():
                    # Get the style XML
                    style_doc = QDomDocument()
                    layer.exportNamedStyle(style_doc)

                    # Import and save to the GeoPackage database
                    temp_layer.importNamedStyle(style_doc)
                    temp_layer.saveStyleToDatabase(
                        "default",  # style name
                        "",  # description
                        True,  # use as default
                        "",  # ui file path
                    )
                success_count += 1

        # Reload layers from GeoPackage
        self._reload_layers_from_gpkg(gpkg_path)

        # Show result
        if errors:
            QtWidgets.QMessageBox.warning(
                self,
                "GeoPackage",
                f"Exported {success_count} layers.\n\nErrors:\n" + "\n".join(errors),
            )
        else:
            QtWidgets.QMessageBox.information(
                self,
                "GeoPackage",
                f"Successfully exported {success_count} layers to GeoPackage!",
            )

    def _reload_layers_from_gpkg(self, gpkg_path):
        """Reload all layers from the GeoPackage"""
        from osgeo import ogr

        try:
            ds = ogr.Open(gpkg_path)
            if not ds:
                return

            for i in range(ds.GetLayerCount()):
                ogr_layer = ds.GetLayerByIndex(i)
                layer_name = ogr_layer.GetName()

                uri = f"{gpkg_path}|layername={layer_name}"
                vlayer = QgsVectorLayer(uri, layer_name, "ogr")
                if vlayer.isValid():
                    # Load style from the GeoPackage's internal database
                    styles = vlayer.listStylesInDatabase()
                    if styles[1]:  # If styles exist
                        vlayer.loadNamedStyle(gpkg_path, True)  # Load from database

                    QgsProject.instance().addMapLayer(vlayer)

            ds = None

        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Reload Layers", f"Error reloading layers: {str(e)}"
            )
