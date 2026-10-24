# SPDX-License-Identifier: GPL-3.0-or-later
"""
inge_groundbox/math_utils.py
==========================
Moduł zgodności wstecznej (Re-export).
"""
from __future__ import annotations

from .generators import (
    Point3D,
    Triangle,
    apply_smoove,
    drape_path_onto_terrain,
    extract_triangles_from_group,
    generate_flat_grid,
    ray_triangle_intersect,
    smoove_falloff,
    triangulate_contour_points,
)

__all__ = [
    "ray_triangle_intersect",
    "drape_path_onto_terrain",
    "smoove_falloff",
    "apply_smoove",
    "generate_flat_grid",
    "triangulate_contour_points",
    "extract_triangles_from_group",
    "Point3D",
    "Triangle",
]
