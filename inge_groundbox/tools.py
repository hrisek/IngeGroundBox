# SPDX-License-Identifier: GPL-3.0-or-later
"""
inge_groundbox/tools.py
=====================
Interaktywne narzędzia viewportu dla wtyczki GroundBox w IngeTrazo:
1. SmooveTool      – interaktywne rzeźbienie pędzlem z podglądem HUD
2. FromScratchTool – interaktywne tworzenie siatki terenu (3 kliknięcia)
3. StampTool       – interaktywny odcisk obrysu w terenie
4. DrapeTool       – interaktywne rzutowanie linii na teren
5. AddDetailTool   – kliknij na trójkąt, aby podzielić go na 4 części
6. FlipEdgeTool    – kliknij na krawędź, aby odwrócić przekątną
"""
from __future__ import annotations

import math
from typing import Any, List, Optional, Tuple

try:
    from tools.base import Tool
except ImportError:
    class Tool:
        name = "BaseTool"
        shortcut = None
        description = ""
        def __init__(self): pass
        def on_activate(self, viewport): pass
        def on_deactivate(self, viewport): pass

from .constants import DEFAULT_FROM_SCRATCH, DEFAULT_SMOOVE, PLUGIN_KEY
from .geometry import Point3D, apply_smoove, v_dist_3d
from .i18n import tr
from .operations import (
    extract_triangles_from_group,
    find_terrain_group,
    op_apply_add_detail,
    op_apply_add_detail_at_point,
    op_apply_drape,
    op_apply_flip_edge,
    op_apply_stamp,
    op_commit_smoove,
    op_create_from_scratch,
    resolve_viewport,
    set_vertex_coord,
    to_point3d,
    to_qvector3d,
)

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QPen, QVector3D
except ImportError:
    try:
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QColor, QPen, QVector3D
    except ImportError:
        class Qt:
            DashLine = 2
            SolidLine = 1
        class QColor:
            def __init__(self, r, g, b, a=255): pass
        class QPen:
            def __init__(self, *a): pass
            def setWidth(self, w): pass
            def setStyle(self, s): pass
        class QVector3D:
            def __init__(self, x=0.0, y=0.0, z=0.0):
                self._x, self._y, self._z = float(x), float(y), float(z)
            def x(self): return self._x
            def y(self): return self._y
            def z(self): return self._z


# ===========================================================================
# Re-export full interactive tools (Smoove, From Scratch, Stamp, Drape, Add Detail, Flip Edge)
# ===========================================================================
from .interactive import (
    AddDetailTool,
    DrapeTool,
    FlipEdgeTool,
    FromScratchTool,
    SmooveTool,
    StampTool,
)


# ===========================================================================
# Pomocniki współrzędnych i konwersji
# ===========================================================================

def _extract_ctx_screen_xy(ctx: Any) -> tuple[int | None, int | None]:
    """Wyciąga współrzędne pikselowe kursora ze zdarzenia ctx."""
    if hasattr(ctx, "pos"):
        p = ctx.pos
        if hasattr(p, "x"):
            return (int(p.x()), int(p.y()))
        elif isinstance(p, (tuple, list)) and len(p) >= 2:
            return (int(p[0]), int(p[1]))
    if hasattr(ctx, "screen"):
        p = ctx.screen
        if hasattr(p, "x"):
            return (int(p.x()), int(p.y()))
        elif isinstance(p, (tuple, list)) and len(p) >= 2:
            return (int(p[0]), int(p[1]))
    if hasattr(ctx, "px") and hasattr(ctx, "py"):
        try:
            return (int(ctx.px), int(ctx.py))
        except Exception:
            pass
    if hasattr(ctx, "x") and hasattr(ctx, "y"):
        try:
            return (int(ctx.x), int(ctx.y))
        except Exception:
            pass
    return (None, None)


def _extract_ctx_point(ctx: Any) -> Point3D | None:
    """Niezawodnie odczytuje punkt 3D ze zdarzenia myszy (Snap -> World -> Raycast na płaszczyznę Z=0)."""
    # 1. Snap (wierzchołek, krawędź)
    if hasattr(ctx, "snap") and ctx.snap is not None:
        pt = getattr(ctx.snap, "point", None)
        if pt is not None:
            return to_point3d(pt)

    # 2. Punkt w świecie (np. trafienie promienia w siatkę)
    if hasattr(ctx, "world") and ctx.world is not None:
        try:
            return to_point3d(ctx.world)
        except Exception:
            pass

    # 3. Kliknięcie w pustą przestrzeń / płaszczyznę gruntu Z=0
    vp = getattr(ctx, "viewport", None)
    px, py = _extract_ctx_screen_xy(ctx)
    if vp is not None and px is not None and py is not None:
        pt = _screen_to_world(vp, px, py)
        if pt is not None:
            return pt

    return None


def _screen_to_world(viewport: Any, px: int, py: int) -> Point3D | None:
    """Konwertuje piksele ekranu na punkt 3D na płaszczyźnie modelu lub gruncie Z=0."""
    for method_name in ("snap_world_point", "pixels_to_world", "screen_to_world"):
        if hasattr(viewport, method_name) and callable(getattr(viewport, method_name)):
            try:
                pt = getattr(viewport, method_name)(px, py)
                if pt is not None:
                    return to_point3d(pt)
            except Exception:
                pass

    if hasattr(viewport, "screen_to_plane") and callable(viewport.screen_to_plane):
        try:
            res = viewport.screen_to_plane(px, py, z=0.0)
            if res is not None:
                if isinstance(res, (tuple, list)) and len(res) == 2:
                    return (float(res[0]), float(res[1]), 0.0)
                return to_point3d(res)
        except Exception:
            pass

    # Unprojection za pomocą kamery
    try:
        cam = getattr(viewport, "camera", None)
        if cam is not None and hasattr(cam, "unproject_ray"):
            origin, direction = cam.unproject_ray(px, py)
            dz = float(direction.z()) if hasattr(direction, "z") else float(direction[2])
            oz = float(origin.z()) if hasattr(origin, "z") else float(origin[2])
            ox = float(origin.x()) if hasattr(origin, "x") else float(origin[0])
            oy = float(origin.y()) if hasattr(origin, "y") else float(origin[1])
            dx = float(direction.x()) if hasattr(direction, "x") else float(direction[0])
            dy = float(direction.y()) if hasattr(direction, "y") else float(direction[1])

            if abs(dz) > 1e-6:
                t = -oz / dz
                if t > 0:
                    return (ox + dx * t, oy + dy * t, 0.0)
    except Exception:
        pass

    return None


def _world_to_px(viewport: Any, world_pt: Point3D) -> tuple[float, float] | None:
    try:
        res = viewport.world_to_pixels(to_qvector3d(world_pt))
        if res is not None:
            return (float(res[0]), float(res[1]))
    except Exception:
        pass
    try:
        app = getattr(viewport, "app", None)
        if app is not None and hasattr(app, "world_to_pixels"):
            px, py, in_front = app.world_to_pixels([[world_pt[0], world_pt[1], world_pt[2]]])
            if in_front:
                return (float(px[0]), float(py[0]))
    except Exception:
        pass
    return None






def _sel_of(vp):
    try:
        s = getattr(getattr(vp, 'scene', None), 'selection', None)
        if s is None:
            s = getattr(vp, 'selection', None)
        return list(s) if s else []
    except Exception:
        return []
