"""Unit tests for rules/geometry.py."""

import pytest

from rules.geometry import Point, Polygon, get_reference_point
from vision.schemas import BoundingBox


def test_point_representation():
    p = Point(10.5, 20.3)
    assert p.as_tuple() == (10.5, 20.3)
    assert p.as_int_tuple() == (10, 20)


def test_polygon_validation():
    # Less than 3 vertices must raise ValueError
    with pytest.raises(ValueError, match="at least 3 vertices"):
        Polygon([(0, 0), (1, 1)])

    # Normalized polygon vertex > 1.0 must raise ValueError
    with pytest.raises(ValueError, match="outside range"):
        Polygon([(0, 0), (1.5, 0), (1.0, 1.0)], is_normalized=True)


def test_polygon_to_pixel_coordinates():
    poly = Polygon([(0.1, 0.2), (0.8, 0.2), (0.8, 0.9)], is_normalized=True)
    pixel_poly = poly.to_pixel_coordinates(1000, 500)

    assert not pixel_poly.is_normalized
    assert pixel_poly.vertices[0] == Point(100.0, 100.0)
    assert pixel_poly.vertices[1] == Point(800.0, 100.0)
    assert pixel_poly.vertices[2] == Point(800.0, 450.0)


def test_point_in_polygon_ray_casting():
    # Square from (100, 100) to (300, 300)
    poly = Polygon([(100, 100), (300, 100), (300, 300), (100, 300)])

    # Interior point
    assert poly.contains_point(Point(200, 200)) is True

    # Exterior points
    assert poly.contains_point(Point(50, 200)) is False
    assert poly.contains_point(Point(350, 200)) is False
    assert poly.contains_point(Point(200, 50)) is False
    assert poly.contains_point(Point(200, 350)) is False

    # Boundary points (documented policy: inside)
    assert poly.contains_point(Point(100, 200), on_boundary_inside=True) is True
    assert poly.contains_point(Point(100, 100), on_boundary_inside=True) is True


def test_point_in_concave_polygon():
    # L-shaped polygon
    poly = Polygon([(0, 0), (200, 0), (200, 100), (100, 100), (100, 200), (0, 200)])

    # Inside lower-left
    assert poly.contains_point(Point(50, 50)) is True
    # Inside upper-left
    assert poly.contains_point(Point(50, 150)) is True
    # Inside lower-right
    assert poly.contains_point(Point(150, 50)) is True
    # In the cut-out corner (exterior)
    assert poly.contains_point(Point(150, 150)) is False


def test_reference_point_calculation():
    bbox = BoundingBox(x1=100.0, y1=100.0, x2=200.0, y2=400.0)

    # bottom_center: x=(100+200)/2 = 150, y=400
    p_bc = get_reference_point(bbox, "bottom_center")
    assert p_bc == Point(150.0, 400.0)

    # center: x=150, y=(100+400)/2 = 250
    p_c = get_reference_point(bbox, "center")
    assert p_c == Point(150.0, 250.0)

    # bottom_left: x=100, y=400
    p_bl = get_reference_point(bbox, "bottom_left")
    assert p_bl == Point(100.0, 400.0)

    # bottom_right: x=200, y=400
    p_br = get_reference_point(bbox, "bottom_right")
    assert p_br == Point(200.0, 400.0)

    with pytest.raises(ValueError, match="Unsupported reference point type"):
        get_reference_point(bbox, "invalid_ref_type")
