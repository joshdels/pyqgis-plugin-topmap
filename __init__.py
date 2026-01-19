from .topmap_sync import TopMapSync

def classFactory(iface):
    """Load TopMap Sync Plugin."""
    return TopMapSync(iface)