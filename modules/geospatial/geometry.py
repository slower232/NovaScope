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


def in_chihuahua(lat: float, lon: float) -> bool:
    from config.constants import CHIHUAHUA_BBOX
    la0, la1, lo0, lo1 = CHIHUAHUA_BBOX
    return la0 <= lat <= la1 and lo0 <= lon <= lo1


def validate_chihuahua(lat: float, lon: float):
    """Esta versión solo cubre Chihuahua: rechaza ubicaciones fuera de la caja envolvente aproximada."""
    validate_point(lat, lon)
    if not in_chihuahua(lat, lon):
        raise ValueError("outside_chihuahua")
    return lat, lon


def validate_polygon_chihuahua(geojson: dict):
    """Valida forma, rango y cobertura; rechaza polígonos autointersectantes simples (bowtie) y de área nula."""
    ring = polygon_ring(geojson)
    for lon, lat in ring:
        validate_chihuahua(lat, lon)
    if area_hectares(geojson) <= 0:
        raise ValueError("zero_area")
    pts = ring[:-1]
    n = len(pts)

    def ccw(a, b, c): return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])
    def inter(a, b, c, d): return ccw(a, c, d) != ccw(b, c, d) and ccw(a, b, c) != ccw(a, b, d)
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            if inter(pts[i], pts[(i + 1) % n], pts[j], pts[(j + 1) % n]):
                raise ValueError("self_intersecting")
    return True
