import pytest
from modules.geospatial.geometry import area_hectares, centroid, validate_point


def square(lat, lon, side_m):
    import math
    dlat = side_m / 111_320; dlon = side_m / (111_320 * math.cos(math.radians(lat)))
    return {"type": "Polygon", "coordinates": [[[lon, lat], [lon + dlon, lat], [lon + dlon, lat + dlat], [lon, lat + dlat], [lon, lat]]]}


def test_area_100m_square_is_one_hectare():
    assert abs(area_hectares(square(28.6, -106.1, 100)) - 1.0) < 0.02


def test_centroid_and_validation():
    lat, lon = centroid(square(28.6, -106.1, 100))
    assert abs(lat - 28.6) < 0.001
    with pytest.raises(ValueError):
        validate_point(100, 0)
