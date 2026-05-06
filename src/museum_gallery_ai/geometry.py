from __future__ import annotations

from .models import Point

EPSILON = 1e-9


def point_in_polygon(point: Point, polygon: tuple[Point, ...]) -> bool:
    """Return True when a point is inside or on the boundary of a polygon."""
    x, y = point
    inside = False
    n = len(polygon)
    if n < 3:
        return False

    previous_x, previous_y = polygon[-1]
    for current_x, current_y in polygon:
        if _point_on_segment(point, (previous_x, previous_y), (current_x, current_y)):
            return True
        intersects = (current_y > y) != (previous_y > y)
        if intersects:
            x_intersection = (previous_x - current_x) * (y - current_y) / (previous_y - current_y) + current_x
            if x <= x_intersection:
                inside = not inside
        previous_x, previous_y = current_x, current_y
    return inside


def line_side(point: Point, start: Point, end: Point) -> float:
    return (end[0] - start[0]) * (point[1] - start[1]) - (end[1] - start[1]) * (point[0] - start[0])


def crossing_direction(previous: Point, current: Point, start: Point, end: Point) -> str | None:
    previous_side = line_side(previous, start, end)
    current_side = line_side(current, start, end)
    if abs(previous_side) < EPSILON or abs(current_side) < EPSILON:
        return None
    if previous_side < 0 < current_side:
        return "positive"
    if previous_side > 0 > current_side:
        return "negative"
    return None


def _point_on_segment(point: Point, start: Point, end: Point) -> bool:
    cross = line_side(point, start, end)
    if abs(cross) > EPSILON:
        return False
    min_x, max_x = sorted((start[0], end[0]))
    min_y, max_y = sorted((start[1], end[1]))
    return min_x - EPSILON <= point[0] <= max_x + EPSILON and min_y - EPSILON <= point[1] <= max_y + EPSILON
