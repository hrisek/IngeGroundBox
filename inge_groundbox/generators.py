# SPDX-License-Identifier: GPL-3.0-or-later
"""
inge_groundbox/generators.py
==========================
Moduł kompatybilności wstecznej (Re-export API).
Wszystkie funkcje matematyczne i triangulacji zostały rozwinięte w modułach:
- geometry.py
- terrain_mesh.py
- operations.py
"""
from __future__ import annotations

from .geometry import (
    Point3D,
    Triangle,
    apply_smoove,
    drape_path_onto_terrain,
    ray_triangle_intersect,
    smoove_falloff,
    triangulate_points_2d,
)
from .operations import extract_triangles_from_group
from .terrain_mesh import generate_flat_grid


def triangulate_contour_points(points):
    """Zgodność wsteczna z wczesną wersją Fazy 1."""
    return triangulate_points_2d(points)


__all__ = [
    "Point3D",
    "Triangle",
    "generate_flat_grid",
    "triangulate_contour_points",
    "triangulate_points_2d",
    "smoove_falloff",
    "apply_smoove",
    "ray_triangle_intersect",
    "drape_path_onto_terrain",
    "extract_triangles_from_group",
]
