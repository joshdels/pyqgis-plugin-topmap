import os
import shutil
from osgeo import ogr
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtXml import QDomDocument

from qgis.core import (
    QgsVectorLayer,
    QgsProject,
    QgsVectorFileWriter,
    QgsSettings,
    QgsRasterLayer,
)

from ..core.project_manager import ProjectSettingsManager


class ProjectDetailsPage(QtWidgets.QWidget):
    """Window to view and edit project details."""

    projectDeleted = pyqtSignal()
    backClicked = pyqtSignal()
    closeClicked = pyqtSignal()
    logoutClicked = pyqtSignal()

    def __init__(self, project_data, parent=None, api=None, username=None):
        super().__init__(parent)

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
        self.backBtn.clicked.connect(self.backClicked.emit)
        self.closeBtn.clicked.connect(self.closeClicked.emit)
        self.loadButton.clicked.connect(self.on_load_clicked)
        self.syncButton.clicked.connect(self.on_sync_clicked)
        self.helpBtn.clicked.connect(self.update_project)  # testing
        self.closeBtn.clicked.connect(self.close)
        self.logoutButton.clicked.connect(self.logout)
        self.deleteBtn.clicked.connect(self.on_delete_clicked)
        self.containerizeBtn.clicked.connect(self.on_containerize_clicked)

    def logout(self):
        """Logout the user and close the window."""
        settings = QgsSettings()
        settings.remove("TopMap/token")
        settings.remove("TopMap/username")
        settings.remove("TopMap/remember")

        QtWidgets.QMessageBox.information(self, "Logout", "You have been logged out.")
        self.logoutClicked.emit()

    def display_data(self):
        """Populate UI widgets with project data."""
        self.projectNameInput.setText(self.project_data.get("name", ""))
        self.descriptionInput.setPlainText(
            self.project_data.get("description", "No description provided.")
        )

    def update_project(self):
        """Handle 'Update Details' button click (placeholder)."""
        QtWidgets.QMessageBox.information(self, "Update", "Feature coming soon!")

    def on_load_clicked(self):
        """Load the project, restoring layer order and styles."""
        project_name = self.project_data.get("name")
        if not project_name:
            QtWidgets.QMessageBox.warning(
                self, "Load Project", "Project name not found."
            )
            return

        root_dir = ProjectSettingsManager.get_root_dir()
        if not root_dir or not os.path.exists(root_dir):
            QtWidgets.QMessageBox.warning(
                self, "Load Project", "Root directory not set or does not exist."
            )
            return

        project_folder = os.path.join(root_dir, "TopMapSync", project_name)
        if not os.path.exists(project_folder):
            QtWidgets.QMessageBox.warning(
                self, "Load Project", f"Project folder not found:\n{project_folder}"
            )
            return

        # Check if data files exist
        gpkg_path = os.path.join(project_folder, "data.gpkg")
        qgz_files = [f for f in os.listdir(project_folder) if f.endswith(".qgz")]

        if not qgz_files:
            QtWidgets.QMessageBox.warning(
                self, "Load Project", "No .qgz file found in project folder."
            )
            return

        qgz_path = os.path.join(project_folder, qgz_files[0])

        try:
            QgsProject.instance().clear()

            success = QgsProject.instance().read(qgz_path)

            if not success:
                QtWidgets.QMessageBox.warning(
                    self, "Load Project", "Failed to load .qgz file."
                )
                return

            # Check how many layers were loaded
            loaded_layers = QgsProject.instance().mapLayers()
            layer_count = len(loaded_layers)

            if layer_count == 0:
                # If no layers loaded, try manual loading from files
                QtWidgets.QMessageBox.information(
                    self,
                    "Load Project",
                    f"Project file has no layers. Attempting to load from data files...",
                )

                # Load layers manually from GeoPackage and rasters
                layer_count = self._load_layers_from_files(project_folder, gpkg_path)

                if layer_count == 0:
                    QtWidgets.QMessageBox.warning(
                        self,
                        "Load Project",
                        f"Could not load any layers.\n\n"
                        f"Try using the Containerize button to rebuild the project.",
                    )
                    return

            QtWidgets.QMessageBox.information(
                self,
                "Load Project",
                f"Project loaded successfully!\n\n"
                f"Project: {project_name}\n"
                f"Layers loaded: {layer_count}",
            )

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Load Project", f"Error loading project:\n{str(e)}"
            )

    def _load_layers_from_files(self, project_folder, gpkg_path):
        """Manually load layers from GeoPackage and raster files."""
        layer_count = 0

        # Load GeoPackage layers
        if os.path.exists(gpkg_path):
            try:
                ds = ogr.Open(gpkg_path)
                if ds:
                    for i in range(ds.GetLayerCount()):
                        layer_name = ds.GetLayerByIndex(i).GetName()
                        uri = f"{gpkg_path}|layername={layer_name}"
                        vlayer = QgsVectorLayer(uri, layer_name, "ogr")

                        if vlayer.isValid():
                            # Load style from GeoPackage
                            styles = vlayer.listStylesInDatabase()
                            if styles[1]:
                                vlayer.loadNamedStyle(gpkg_path, True)

                            QgsProject.instance().addMapLayer(vlayer)
                            layer_count += 1
                    ds = None
            except Exception as e:
                print(f"Error loading GeoPackage: {e}")

        # Load raster layers
        for file in os.listdir(project_folder):
            if file.lower().endswith((".tif", ".tiff")):
                raster_path = os.path.join(project_folder, file)
                layer_name = os.path.splitext(file)[0]

                rlayer = QgsRasterLayer(raster_path, layer_name)
                if rlayer.isValid():
                    QgsProject.instance().addMapLayer(rlayer)

                    # Try to load QML style if it exists
                    qml_path = os.path.join(project_folder, f"{layer_name}.qml")
                    if os.path.exists(qml_path):
                        rlayer.loadNamedStyle(qml_path)

                    layer_count += 1

        return layer_count

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

    def on_containerize_clicked(self):
        """Create GeoPackage for vectors and copy rasters, preserving order and styles."""

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
        qgz_path = os.path.join(project_folder, f"{project_name}.qgz")

        layers = list(QgsProject.instance().mapLayers().values())
        if not layers:
            QtWidgets.QMessageBox.information(
                self, "GeoPackage", "No layers found in QGIS."
            )
            return

        # ------------------ Collect layer info BEFORE removing ------------------
        layer_order = []
        vector_layers = []
        raster_info = {}  # name -> (src_path, dst_path, qml_path)

        for layer in layers:
            layer_order.append(layer.name())
            if isinstance(layer, QgsVectorLayer):
                vector_layers.append(layer.clone())
            elif isinstance(layer, QgsRasterLayer):
                src_path = layer.dataProvider().dataSourceUri()
                # Handle raster paths with parameters
                if "|" in src_path:
                    src_path = src_path.split("|")[0]

                dst_path = os.path.join(project_folder, os.path.basename(src_path))
                qml_path = os.path.join(project_folder, f"{layer.name()}.qml")

                # Save style BEFORE removing layers
                layer.saveNamedStyle(qml_path)

                raster_info[layer.name()] = (src_path, dst_path, qml_path)

        # ------------------ Remove layers to unlock files ------------------
        QgsProject.instance().removeAllMapLayers()

        # ------------------ Export vector layers to GeoPackage ------------------
        errors = []
        success_count = 0
        first_layer = True

        for layer in vector_layers:
            layer_name = layer.name().replace(" ", "_")
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "GPKG"
            options.layerName = layer_name
            options.actionOnExistingFile = (
                QgsVectorFileWriter.CreateOrOverwriteFile
                if first_layer
                else QgsVectorFileWriter.CreateOrOverwriteLayer
            )
            first_layer = False

            err = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer, gpkg_path, QgsProject.instance().transformContext(), options
            )
            if err[0] != QgsVectorFileWriter.NoError:
                errors.append(f"{layer_name}: {err[1]}")
            else:
                # Save style inside GeoPackage
                uri = f"{gpkg_path}|layername={layer_name}"
                temp_layer = QgsVectorLayer(uri, layer_name, "ogr")
                if temp_layer.isValid():
                    style_doc = QDomDocument()
                    layer.exportNamedStyle(style_doc)
                    temp_layer.importNamedStyle(style_doc)
                    temp_layer.saveStyleToDatabase("default", "", True, "")
                success_count += 1

        # ------------------ Copy raster layers to project folder ------------------
        raster_count = 0
        for name, (src_path, dst_path, qml_path) in raster_info.items():
            if os.path.exists(src_path):
                if src_path != dst_path:
                    try:
                        shutil.copy2(src_path, dst_path)
                        raster_count += 1
                    except Exception as e:
                        errors.append(f"Raster copy {name}: {str(e)}")

        # ------------------ Reload layers with RELATIVE paths ------------------
        for name in layer_order:
            # Try vector
            safe_name = name.replace(" ", "_")
            uri = f"{gpkg_path}|layername={safe_name}"
            vlayer = QgsVectorLayer(uri, name, "ogr")
            if vlayer.isValid():
                styles = vlayer.listStylesInDatabase()
                if styles[1]:
                    vlayer.loadNamedStyle(gpkg_path, True)
                QgsProject.instance().addMapLayer(vlayer)
                continue

            # Try raster
            if name in raster_info:
                src_path, dst_path, qml_path = raster_info[name]

                # Create NEW raster layer from copied file
                rlayer = QgsRasterLayer(dst_path, name)
                if rlayer.isValid():
                    QgsProject.instance().addMapLayer(rlayer)
                    # Load style if QML file exists
                    if os.path.exists(qml_path):
                        rlayer.loadNamedStyle(qml_path)

        # ------------------ Configure project for portability ------------------
        # Set project file location
        QgsProject.instance().setFileName(qgz_path)

        # Enable relative paths - CRITICAL for portability
        QgsProject.instance().writeEntry("Paths", "Absolute", False)

        # Set project home path
        QgsProject.instance().setPresetHomePath(project_folder)
        QgsProject.instance().homePath = project_folder

        # ------------------ Save QGIS project file (.qgz) ------------------
        try:
            success = QgsProject.instance().write()
            if not success:
                errors.append("Failed to write .qgz project file")
            else:
                # Verify layers were saved
                reloaded_layers = QgsProject.instance().mapLayers()
                if len(reloaded_layers) == 0:
                    errors.append("WARNING: Project saved but no layers found!")
        except Exception as e:
            errors.append(f"Error saving .qgz: {str(e)}")

        # ------------------ Show result ------------------
        msg = f"Successfully containerized and saved project!\n\n"
        msg += f"Exported {success_count} vector layers to GeoPackage\n"
        if raster_count:
            msg += f"Copied {raster_count} raster files\n"
        msg += f"Saved portable project as: {project_name}.qgz\n"
        msg += f"Project uses relative paths (portable)\n"
        msg += f"\nLocation: {project_folder}"

        if errors:
            msg += "\n\nErrors:\n" + "\n".join(errors)

        QtWidgets.QMessageBox.information(self, "Containerize Project", msg)

    def on_sync_clicked(self):
        project_id = self.project_data.get("id")
        project_name = self.project_data.get("name")

        if not project_id or not project_name:
            QtWidgets.QMessageBox.warning(self, "Sync", "Project ID or name not found")
            return

        root_dir = ProjectSettingsManager.get_root_dir()
        if not root_dir or not os.path.exists(root_dir):
            QtWidgets.QMessageBox.warning(
                self, "Sync", "Root directory not set or missing."
            )
            return

        project_folder = os.path.join(root_dir, "TopMapSync", project_name)
        if not os.path.exists(project_folder):
            QtWidgets.QMessageBox.warning(
                self, "Sync", f"Project folder not found:\n{project_folder}"
            )
            return

        # Folder Looping
        uploaded_count = 0
        errors = []

        for root, dirs, files in os.walk(project_folder):
            for filename in files:
                # Only allow project files
                if not (filename.endswith((".qgz", ".gpkg", ".qml", ".tif", ".tiff"))):
                    continue

                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, project_folder)

                try:
                    result = self.api.upload_file(
                        project_id, full_path, relative_path=rel_path
                    )
                    uploaded_count += 1
                    print(f"Uploaded: {rel_path} -> {result}")
                except Exception as e:
                    errors.append(f"{rel_path}: {str(e)}")

        if errors:
            QtWidgets.QMessageBox.warning(
                self,
                "Sync Completed",
                f"Uploaded {uploaded_count} files with errors:\n" + "\n".join(errors),
            )
        else:
            QtWidgets.QMessageBox.information(
                self, "Sync Completed", f"Successfully uploaded {uploaded_count} files!"
            )
