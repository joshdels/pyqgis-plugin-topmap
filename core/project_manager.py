import os
from qgis.core import QgsSettings


class ProjectSettingsManager:
    """The Settings of the TopMap Sync Settings"""

    ROOT_KEY = "TopMap/project_root"

    @classmethod
    def get_root_dir(cls):
        settings = QgsSettings()
        return settings.value(cls.ROOT_KEY, "")

    @classmethod
    def set_root_dir(cls, path):
        settings = QgsSettings()
        settings.setValue(cls.ROOT_KEY, path)

    @classmethod
    def get_project_path(cls, project_name):
        root = cls.get_root_dir()
        if not root:
            return None
        return os.path.join(root, project_name)
