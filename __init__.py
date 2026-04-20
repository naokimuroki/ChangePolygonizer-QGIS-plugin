def classFactory(iface):
    from .plugin import ChangePolygonizer
    return ChangePolygonizer(iface)