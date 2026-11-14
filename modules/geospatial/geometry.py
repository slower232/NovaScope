"""Geometría de parcelas sin dependencias pesadas (GeoJSON -> superficie, centroide)."""
import math

EARTH_R = 6371008.8  # m


def polygon_ring(geojson: dict):
    g = geojson.get("geometry", geojson)
    if g.get("type") != "Polygon":
        raise ValueError("Se esperaba un Polygon GeoJSON")
    ring = g["coordinates"][0]
    if len(ring) < 4:
        raise ValueError("Polígono con menos de 3 vértices")
    for lon, lat in ring:
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise ValueError("Coordenadas fuera de rango")
    return ring


def area_hectares(geojson: dict) -> float:
    """Área geodésica aproximada con proyección equirectangular local (error <0.5 % en parcelas)."""
    ring = polygon_ring(geojson)
    lat0 = math.radians(sum(p[1] for p in ring) / len(ring))
    pts = [(math.radians(lon) * EARTH_R * math.cos(lat0), math.radians(lat) * EARTH_R) for lon, lat in ring]
    s = sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]))
    return abs(s) / 2 / 10_000


def centroid(geojson: dict):
    ring = polygon_ring(geojson)[:-1]
    return (sum(p[1] for p in ring) / len(ring), sum(p[0] for p in ring) / len(ring))  # lat, lon


def validate_point(lat: float, lon: float):
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError("Coordenadas fuera de rango")
    return lat, lon
