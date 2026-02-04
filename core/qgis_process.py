import os
from qgis.core import (
    QgsProject,
    QgsRasterLayer,
    QgsRasterPipe,
    QgsRasterFileWriter,
)


class QgisRasterProcessor:
    def __init__(self, project: QgsProject, project_folder: str):
        self.project = project
        self.project_folder = project_folder

    def process_rasters(self):
        errors = []

        rasters = [
            layer
            for layer in self.project.mapLayers().values()
            if isinstance(layer, QgsRasterLayer)
        ]

        for raster in rasters:
            try:
                safe_name = raster.name().replace(" ", "_")
                style_path = os.path.join(self.project_folder, f"{safe_name}.qml")

                # Save style
                raster.saveNamedStyle(style_path)

                # Export raster
                new_path = self.save_raster_to_project(raster)

                # Reload raster
                new_raster = QgsRasterLayer(new_path, raster.name())
                if not new_raster.isValid():
                    raise RuntimeError("Reloaded raster is invalid")

                # Restore style
                if os.path.exists(style_path):
                    new_raster.loadNamedStyle(style_path)
                    new_raster.triggerRepaint()

                # Replace layer
                self.project.removeMapLayer(raster.id())
                self.project.addMapLayer(new_raster)

            except Exception as e:
                errors.append(f"{raster.name()}: {e}")

        return errors

    def save_raster_to_project(self, raster: QgsRasterLayer) -> str:
        if not raster.isValid():
            raise RuntimeError(f"Invalid raster: {raster.name()}")

        safe_name = raster.name().replace(" ", "_")
        output_path = os.path.join(self.project_folder, f"{safe_name}.tif")

        provider = raster.dataProvider()

        pipe = QgsRasterPipe()
        if not pipe.set(provider.clone()):
            raise RuntimeError("Failed to set raster pipe")

        writer = QgsRasterFileWriter(output_path)
        writer.setOutputFormat("GTiff")

        result = writer.writeRaster(
            pipe,
            provider.xSize(),
            provider.ySize(),
            provider.extent(),
            raster.crs(),
        )

        if result != QgsRasterFileWriter.NoError:
            raise RuntimeError(f"Raster write failed: {result}")

        return output_path
