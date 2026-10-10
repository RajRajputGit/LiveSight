"""Geometric primitives and point-in-polygon algorithms for LiveSight rules.

Conforms to Phase 3 requirements in 04_IMPLEMENTATION_PLAN.md:
- Point and Polygon representations (pixel and normalized coordinates)
- Point-in-polygon testing using ray-casting with documented boundary policy
- Bounding box reference point extraction (e.g. bottom-center)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Sequence, Tuple, Union

from vision.schemas import BoundingBox


@dataclass(frozen=True)
class Point:
    """2D coordinate representation (x, y)."""

    x: float
    y: float

    def as_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def as_int_tuple(self) -> Tuple[int, int]:
        return (int(round(self.x)), int(round(self.y)))


@dataclass(frozen=True)
class Polygon:
    """Closed 2D polygon defined by an ordered list of vertices."""

    vertices: Tuple[Point, ...]
    is_normalized: bool = False

    def __init__(
        self,
        vertices: Sequence[Union[Point, Tuple[float, float], Sequence[float]]],
        is_normalized: bool = False,
    ) -> None:
        """Initialize and validate polygon vertices.

        Args:
            vertices: Sequence of Points or (x, y) coordinate pairs.
            is_normalized: Whether coordinates are in [0.0, 1.0] range.
        """
        parsed: List[Point] = []
        for v in vertices:
            if isinstance(v, Point):
                parsed.append(v)
            elif isinstance(v, (tuple, list)) and len(v) >= 2:
                parsed.append(Point(float(v[0]), float(v[1])))
            else:
                raise ValueError(f"Invalid vertex format: {v}")

        if len(parsed) < 3:
            raise ValueError(
                f"A polygon requires at least 3 vertices, got {len(parsed)}."
            )

        # Check normalization bounds if declared normalized
        if is_normalized:
            for p in parsed:
                if not (0.0 <= p.x <= 1.0 and 0.0 <= p.y <= 1.0):
                    raise ValueError(
                        f"Normalized vertex ({p.x}, {p.y}) outside range [0.0, 1.0]."
                    )

        object.__setattr__(self, "vertices", tuple(parsed))
        object.__setattr__(self, "is_normalized", is_normalized)

    def to_pixel_coordinates(self, width: int, height: int) -> Polygon:
        """Convert a normalized polygon to pixel coordinates for given frame dimensions.

        If already in pixel coordinates, returns self.
        """
        if not self.is_normalized:
            return self

        if width <= 0 or height <= 0:
            raise ValueError(
                f"Invalid frame dimensions for coordinate scaling: width={width}, height={height}"
            )

        pixel_vertices = [
            Point(p.x * float(width), p.y * float(height))
            for p in self.vertices
        ]
        return Polygon(pixel_vertices, is_normalized=False)

    def contains_point(
        self,
        point: Point,
        on_boundary_inside: bool = True,
        eps: float = 1e-7,
    ) -> bool:
        """Evaluate if point is inside the polygon using ray-casting.

        Documented boundary rule:
        Points falling directly on a polygon edge or vertex are treated as inside
        when `on_boundary_inside=True` (default), avoiding boundary flicker.

        Args:
            point: The 2D test point.
            on_boundary_inside: Whether points on polygon edges count as inside.
            eps: Numerical tolerance for collinearity and segment tests.

        Returns:
            True if point is within or on the polygon boundary; False otherwise.
        """
        n = len(self.vertices)
        if n < 3:
            return False

        px, py = point.x, point.y

        # 1. Check if the point lies exactly on an edge or vertex
        for i in range(n):
            v1 = self.vertices[i]
            v2 = self.vertices[(i + 1) % n]

            if _is_point_on_segment(px, py, v1.x, v1.y, v2.x, v2.y, eps=eps):
                return on_boundary_inside

        # 2. Standard ray-casting (even-odd crossing rule)
        # Cast a horizontal ray to the right from (px, py)
        inside = False
        p1 = self.vertices[0]
        for i in range(1, n + 1):
            p2 = self.vertices[i % n]
            if (p1.y > py) != (p2.y > py):
                # Calculate x-intersection of edge with horizontal line y = py
                intersect_x = (p2.x - p1.x) * (py - p1.y) / (p2.y - p1.y) + p1.x
                if px < intersect_x:
                    inside = not inside
            p1 = p2

        return inside

    def as_numpy_points(self) -> List[Tuple[int, int]]:
        """Return integer coordinate list suitable for cv2.polylines and fillPoly."""
        return [p.as_int_tuple() for p in self.vertices]


def _is_point_on_segment(
    px: float,
    py: float,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    eps: float = 1e-7,
) -> bool:
    """Check if point (px, py) lies on line segment between (x1, y1) and (x2, y2)."""
    # Cross product to test collinearity: (y - y1)(x2 - x1) - (x - x1)(y2 - y1) == 0
    cross = (py - y1) * (x2 - x1) - (px - x1) * (y2 - y1)
    if abs(cross) > eps * max(1.0, abs(x2 - x1) + abs(y2 - y1)):
        return False

    # Check bounding box of segment
    if (
        min(x1, x2) - eps <= px <= max(x1, x2) + eps
        and min(y1, y2) - eps <= py <= max(y1, y2) + eps
    ):
        return True

    return False


def get_reference_point(
    bbox: BoundingBox,
    reference_type: str = "bottom_center",
) -> Point:
    """Compute the evaluation reference point for a bounding box.

    Supported reference types:
    - 'bottom_center' (default): Approximates ground-contact position for standing persons.
    - 'center': Geometric centroid of the bounding box.
    - 'bottom_left': Bottom-left corner.
    - 'bottom_right': Bottom-right corner.

    Args:
        bbox: Target BoundingBox.
        reference_type: Chosen reference point convention.

    Returns:
        Point instance in frame coordinates.
    """
    ref = reference_type.strip().lower()

    if ref == "bottom_center":
        return Point(x=(bbox.x1 + bbox.x2) / 2.0, y=bbox.y2)
    elif ref == "center":
        return Point(x=(bbox.x1 + bbox.x2) / 2.0, y=(bbox.y1 + bbox.y2) / 2.0)
    elif ref == "bottom_left":
        return Point(x=bbox.x1, y=bbox.y2)
    elif ref == "bottom_right":
        return Point(x=bbox.x2, y=bbox.y2)
    else:
        raise ValueError(
            f"Unsupported reference point type '{reference_type}'. "
            "Supported types: 'bottom_center', 'center', 'bottom_left', 'bottom_right'."
        )
