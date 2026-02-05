import os
from qgis.core import (
    QgsProject,
    QgsRasterLayer,
    QgsRasterPipe,
    QgsRasterFileWriter,
    QgsVectorLayer,
    QgsVectorFileWriter,
)


class QgisRasterProcessor:
    def __init__(self, project: QgsProject, project_folder: str):
        self.project = project
        self.project_folder = project_folder

    def process_rasters(self):
        errors = []
        rasters = [
            l
            for l in self.project.mapLayers().values()
            if isinstance(l, QgsRasterLayer)
        ]

        for raster in rasters:
            try:
                safe_name = raster.name().replace(" ", "_")
                style_path = os.path.join(self.project_folder, f"{safe_name}.qml")

                # Save style
                raster.saveNamedStyle(style_path)

                # Export raster
                absolute_new_path = self.save_raster_to_project(raster)
                new_raster = QgsRasterLayer(absolute_new_path, raster.name())

                if not new_raster.isValid():
                    raise RuntimeError(
                        f"Failed to load exported raster: {absolute_new_path}"
                    )

                # Restore raster style
                new_raster.loadNamedStyle(style_path)

                # Maintain tree position
                old_id = raster.id()
                root = self.project.layerTreeRoot()
                old_node = root.findLayer(old_id)

                self.project.addMapLayer(new_raster, False)

                if old_node:
                    parent = old_node.parent()
                    idx = parent.children().index(old_node)
                    parent.insertLayer(idx, new_raster)
                else:
                    root.addLayer(new_raster)

                self.project.removeMapLayer(old_id)

            except Exception as e:
                errors.append(f"Raster {raster.name()}: {e}")
        return errors

    def save_raster_to_project(self, raster: QgsRasterLayer) -> str:
        safe_name = raster.name().replace(" ", "_")
        output_path = os.path.join(self.project_folder, f"{safe_name}.tif")
        provider = raster.dataProvider()
        pipe = QgsRasterPipe()
        pipe.set(provider.clone())
        writer = QgsRasterFileWriter(output_path)
        writer.setOutputFormat("GTiff")
        writer.writeRaster(
            pipe, provider.xSize(), provider.ySize(), provider.extent(), raster.crs()
        )
        return output_path


class QgisVectorProcessor:
    def __init__(self, project: QgsProject, project_folder: str):
        self.project = project
        self.project_folder = project_folder
        self.gpkg_path = os.path.join(self.project_folder, "data.gpkg")

    def process_vector(self):
        errors = []
        vectors = [
            l
            for l in self.project.mapLayers().values()
            if isinstance(l, QgsVectorLayer)
        ]

        # Determine if we need to start a fresh file or append
        first_layer = True

        for vector in vectors:
            try:
                table_name = vector.name().replace(" ", "_").lower()

                options = QgsVectorFileWriter.SaveVectorOptions()
                options.driverName = "GPKG"
                options.layerName = table_name

                # FIX: If it's the first layer, recreate the whole file.
                # If not, just overwrite the specific layer inside the file.
                if first_layer:
                    options.actionOnExistingFile = (
                        QgsVectorFileWriter.CreateOrOverwriteFile
                    )
                    first_layer = False
                else:
                    options.actionOnExistingFile = (
                        QgsVectorFileWriter.CreateOrOverwriteLayer
                    )

                context = self.project.transformContext()
                # Use V3 to avoid unpacking error
                res, err, _, _ = QgsVectorFileWriter.writeAsVectorFormatV3(
                    vector, self.gpkg_path, context, options
                )

                if res != QgsVectorFileWriter.NoError:
                    raise RuntimeError(f"Write error: {err}")

                # Load new layer and save style to DB
                source_path = f"{self.gpkg_path}|layername={table_name}"
                new_vector = QgsVectorLayer(source_path, vector.name(), "ogr")

                if new_vector.isValid():
                    # Save style directly into the GPKG
                    new_vector.saveStyleToDatabase(table_name, "", True, "")

                    # Swap logic
                    old_id = vector.id()
                    self.project.addMapLayer(new_vector, False)

                    # Move position in tree
                    root = self.project.layerTreeRoot()
                    old_node = root.findLayer(old_id)
                    if old_node:
                        old_node.parent().insertLayer(
                            old_node.parent().children().index(old_node), new_vector
                        )

                    self.project.removeMapLayer(old_id)

            except Exception as e:
                errors.append(f"Vector {vector.name()}: {str(e)}")

        return errors
