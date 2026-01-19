# core/layer_info.py
from qgis.core import QgsVectorLayer

def get_active_layer_info(iface):
    """Return (layer_name, feature_count) of the currently active vector layer"""
    layer = iface.activeLayer()
    if layer and isinstance(layer, QgsVectorLayer):
        return layer.name(), layer.featureCount()
    return None, None
