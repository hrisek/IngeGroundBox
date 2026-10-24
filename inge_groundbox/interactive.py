# SPDX-License-Identifier: GPL-3.0-or-later
"""
inge_groundbox/interactive.py
===========================
Interaktywne narzędzia GroundBox – wierne odwzorowanie przebiegu pracy ze SketchUpa,
zbudowane na rzeczywistym API narzędzi IngeTrazo (``tools.base.Tool``):

* ``on_click`` (wciśnięcie), ``on_hover`` (ruch, także z wciśniętym przyciskiem),
  ``on_release`` (puszczenie), ``on_value`` (wpis w polu Pomiary / VCB),
  ``drag_plane`` (pionowa płaszczyzna, by kursor mierzył wysokość w METRACH).

SmooveTool  – kliknij teren → przeciągnij w górę/dół → puść (lub kliknij drugi raz).
              Przed kliknięciem wpisz liczbę = promień; w trakcie = wysokość.
StampTool   – zaznacz obrys (ścianka/grupa) → kliknij teren → ruch w górę/dół
              ustala wysokość półki → kliknij. Wpisz liczbę: przed kliknięciem terenu
              = odsunięcie skarpy, w trakcie = przesunięcie półki w Z.
DrapeTool   – zaznacz krawędzie/obrys → kliknij teren → linie zostają wszyte jako
              twarde krawędzie, zamknięte obszary można malować wiadrem.
"""
from __future__ import annotations

import math
from typing import Any

try:
    from tools.base import Tool
except ImportError:
    class Tool:  # type: ignore
        uses_snap = True
        def on_activate(self, viewport): ...
        def on_deactivate(self, viewport): ...

try:
    from PySide6.QtGui import QMatrix4x4, QVector3D
except ImportError:
    from .operations import QMatrix4x4, QVector3D  # type: ignore

try:
    from core.group import Group
    from core.mesh import Mesh
except ImportError:
    from .operations import Group, Mesh  # type: ignore

from .constants import DEFAULT_FROM_SCRATCH, PLUGIN_KEY
from .geometry import Point3D, point_in_polygon_2d
from .i18n import tr
from .operations import (
    find_terrain_group,
    op_apply_add_detail_at_point,
    op_apply_flip_edge,
    to_point3d,
    to_qvector3d,
)
from .terrain_mesh import find_closest_interior_edge
from . import groundbox_core as sc


# ---------------------------------------------------------------------------
# Wspólne pomocniki
# ---------------------------------------------------------------------------

PALETTE = [
    (("asfalt", "asphalt", "droga", "road"), (0.30, 0.30, 0.32)),
    (("kostk", "paving", "bruk", "beton", "concrete"), (0.62, 0.60, 0.56)),
    (("szuter", "żwir", "gravel"), (0.72, 0.68, 0.58)),
    (("ścież", "path", "ziemia", "soil", "skarpa", "slope", "grunt"), (0.55, 0.42, 0.28)),
    (("taras", "płyta", "terrace", "tile"), (0.70, 0.66, 0.60)),
    (("piasek", "sand"), (0.86, 0.78, 0.55)),
    (("kamie", "rock", "skała", "narzut", "stone"), (0.50, 0.50, 0.48)),
    (("traw", "grass"), (0.36, 0.58, 0.25)),
]


def paint_attrs(name: str | None) -> dict | None:
    if not name:
        return None
    low = name.lower()
    rgb = (0.80, 0.55, 0.35)
    for keys, col in PALETTE:
        if any(k in low for k in keys):
            rgb = col
            break
    return {"color": (*rgb, 1.0), "back_color": (*rgb, 1.0), "mat": name}


def _panel(app):
    return getattr(app, "_groundbox_panel_ref", None) or getattr(app, "_sandbox_panel_ref", None) if app is not None else None


def _flash(vp, text, ms=6000):
    fn = getattr(vp, "flash_status", None)
    if callable(fn):
        try:
            fn(text, ms)
        except Exception:
            pass


def _screen(ctx):
    s = getattr(ctx, "screen", None)
    if s is None:
        return None
    try:
        return (float(s.x()), float(s.y()))
    except Exception:
        return None


def _pick_group(vp, ctx):
    """(face, group) pod kursorem – grupa, przez którą trafiono ściankę."""
    s = _screen(ctx)
    if s is None or vp is None:
        return None, None
    for name in ("pick_face_placement", "pick_face_any"):
        fn = getattr(vp, name, None)
        if callable(fn):
            try:
                face, grp = fn(s[0], s[1])
                if face is not None:
                    return face, grp
            except Exception:
                pass
    return None, None


def _owner_terrain(vp, grp):
    """Grupa terenu odpowiadająca trafionemu obiektowi (także zagnieżdżonemu)."""
    if grp is None:
        return None
    if sc.is_terrain_group(grp):
        return grp
    scene = getattr(vp, "scene", None)
    for g in getattr(scene, "groups", []) if scene is not None else []:
        if g is grp:
            return g
        stack = list(getattr(g, "children", None) or [])
        while stack:
            c = stack.pop()
            if c is grp:
                return g if sc.is_terrain_group(g) else grp
            stack.extend(getattr(c, "children", None) or [])
    return grp


def _vertical_plane(vp, point: QVector3D):
    """Płaszczyzna pionowa przez ``point`` zwrócona do kamery (pomiar wysokości)."""
    cam = getattr(vp, "camera", None)
    eye = None
    try:
        eye = cam.eye()
    except Exception:
        pass
    if eye is None:
        n = QVector3D(0.0, -1.0, 0.0)
    else:
        n = QVector3D(eye.x() - point.x(), eye.y() - point.y(), 0.0)
        if n.length() < 1e-6:
            n = QVector3D(0.0, -1.0, 0.0)
    return QVector3D(point), n.normalized()


def _circle(center: QVector3D, r: float, n: int = 48):
    pts = [QVector3D(center.x() + r * math.cos(2 * math.pi * i / n),
                     center.y() + r * math.sin(2 * math.pi * i / n), center.z())
           for i in range(n)]
    return [(pts[i], pts[(i + 1) % n]) for i in range(n)]


# ===========================================================================
# 1. Smoove
# ===========================================================================

class SmooveTool(Tool):
    name = "Smoove"
    description = "Smoothly sculpts terrain in Z axis using a brush with soft cosine falloff."
    uses_snap = False
    wireframe_color = (1.0, 0.45, 0.0, 1.0)

    def __init__(self, app: Any = None):
        self._app = app
        self.radius = 5.0
        self.profile = "cosine"
        self.vcb_label = tr("vcb_radius")
        self._hover_pins: list[tuple[QVector3D, QVector3D]] = []
        self._hover_terrain = None
        self._last_pin_pos: tuple[float, float] | None = None
        self._reset()

    def _reset(self):
        self._vp = getattr(self, "_vp", None)
        self._terrain = None
        self._center_w: QVector3D | None = None
        self._cursor_w: QVector3D | None = None
        self._before = None
        self._weights = {}
        self._press_z = 0.0
        self._press_px = None
        self._moved = False
        self._dz = 0.0
        self._hover_pins = []
        self._hover_terrain = None
        self._last_pin_pos = None
        self.vcb_label = tr("vcb_radius")

    @property
    def start_point(self):
        return self._center_w

    def on_activate(self, viewport):
        self._vp = viewport
        p = _panel(self._app)
        if p is not None:
            try:
                self.radius = float(p.get_brush_radius())
                self.profile = p.get_falloff_profile() or "cosine"
            except Exception:
                pass
        self._reset()
        _flash(viewport, tr("smoove_interactive_start", r=self.radius), 9000)

    def on_deactivate(self, viewport):
        self._cancel(viewport, quiet=True)

    def drag_plane(self, viewport):
        if self._center_w is None:
            return None
        return _vertical_plane(viewport, self._center_w)

    # --- synchronizacja z panelem na żywo (bez wyłączania narzędzia) ---
    def _sync_panel(self):
        p = _panel(self._app)
        if p is None:
            return
        try:
            self.radius = float(p.get_brush_radius())
            self.profile = p.get_falloff_profile() or "cosine"
            self.strength = float(p.get_brush_strength())
        except Exception:
            pass

    def _gain(self):
        # Siła 0.50 = teren podąża 1:1 za kursorem; 1.00 = 2x szybciej; 0.10 = precyzyjnie.
        return max(0.02, 2.0 * float(getattr(self, "strength", 0.5)))

    def rubber_band_lines(self):
        c = self._center_w or self._cursor_w
        if c is None:
            return []
        if self._center_w is None:
            # Przed kliknięciem: okrąg zasięgu pędzla + pionowe pomarańczowe szpilki profilu dzwonu
            lines = _circle(c, self.radius)
            if self._hover_pins:
                lines.extend(self._hover_pins)
            return lines
        else:
            # W trakcie przeciągania: podniesiony okrąg + pionowa oś + szpilki rzeczywistego odkształcenia
            lift = QVector3D(c.x(), c.y(), c.z() + self._dz)
            lines = _circle(lift, self.radius)
            lines.append((QVector3D(self._center_w), lift))
            if self._weights and self._terrain:
                for v, (p0, w) in self._weights.items():
                    pw0 = sc.to_world(self._terrain, p0)
                    lift_z = self._dz * w
                    lines.append((pw0, QVector3D(pw0.x(), pw0.y(), pw0.z() + lift_z)))
            return lines

    def _update_hover_pins(self, vp, ctx):
        """Błyskawiczne obliczenie pomarańczowych szpilek profilu deformacji (tylko wierzchołki, 0 ms lag)."""
        terrain = self._hover_terrain
        if terrain is None or getattr(terrain, "mesh", None) is None:
            _face, grp = _pick_group(vp, ctx)
            terrain = _owner_terrain(vp, grp)
            if terrain is None:
                terrain = find_terrain_group(getattr(vp, "scene", None), sc.get_selection(vp))
            self._hover_terrain = terrain

        if terrain is None or getattr(terrain, "mesh", None) is None:
            self._hover_pins = []
            return

        mesh = terrain.mesh
        center_l = sc.to_local(terrain, ctx.world)
        cx, cy = center_l.x(), center_l.y()
        r = self.radius
        r2 = r * r
        pins = []
        h_preview = max(0.4, min(2.5, 0.25 * r))

        for v in getattr(mesh, "vertices", []):
            p = v.position
            dx = p.x() - cx
            dy = p.y() - cy
            d2 = dx * dx + dy * dy
            if d2 < r2:
                d = math.sqrt(d2)
                w = sc.smoove_falloff(d / r)
                if w > 0.04:
                    pw = sc.to_world(terrain, p)
                    pins.append((pw, QVector3D(pw.x(), pw.y(), pw.z() + h_preview * w)))

        self._hover_pins = pins

    def on_hover(self, ctx):
        vp = ctx.viewport
        if self._center_w is None:
            if hasattr(ctx, "world") and ctx.world is not None:
                self._cursor_w = QVector3D(ctx.world)
                cur_x, cur_y = float(ctx.world.x()), float(ctx.world.y())
                last = self._last_pin_pos
                if last is None or math.hypot(cur_x - last[0], cur_y - last[1]) > 0.10:
                    self._last_pin_pos = (cur_x, cur_y)
                    self._update_hover_pins(vp, ctx)
                vp.update()
            return

        # W trakcie przeciągania (drag):
        if not hasattr(ctx, "world") or ctx.world is None:
            return

        new_dz = (float(ctx.world.z()) - self._press_z) * self._gain()
        if abs(new_dz - self._dz) < 0.001:
            return

        self._dz = new_dz
        s = _screen(ctx)
        if s and self._press_px and math.dist(s, self._press_px) > 4:
            self._moved = True

        # Błyskawiczna zmiana pozycji Z wyłącznie dla wierzchołków w promieniu pędzla
        sc.apply_dz(self._terrain.mesh, self._weights, self._dz)
        self._terrain.mesh._chunk_dirty = True
        vp.update()

    def on_click(self, ctx):
        vp = ctx.viewport
        if self._center_w is not None:
            self._commit(vp)
            return

        self._sync_panel()
        face, grp = _pick_group(vp, ctx)
        terrain = _owner_terrain(vp, grp)
        if terrain is None:
            terrain = find_terrain_group(getattr(vp, "scene", None), sc.get_selection(vp))

        if terrain is None or getattr(terrain, "mesh", None) is None:
            _flash(vp, tr("smoove_interactive_no_mesh"), 4000)
            return

        mesh = terrain.mesh
        center_l = sc.to_local(terrain, ctx.world)
        weights = sc.smoove_weights(mesh, center_l, self.radius, self.profile)
        if not weights:
            _flash(vp, tr("smoove_interactive_no_verts"), 5000)
            return

        self._terrain = terrain
        self._before = mesh.capture_state()
        self._weights = weights
        self._center_w = QVector3D(ctx.world)
        self._press_z = float(ctx.world.z())
        self._press_px = _screen(ctx)
        self._moved = False
        self._dz = 0.0
        self.vcb_label = tr("vcb_height")
        _flash(vp, tr("smoove_interactive_drag", dz=0.0), 3000)
        vp.update()

    def on_release(self, viewport):
        if self._center_w is not None and self._moved:
            self._commit(viewport)

    def on_value(self, viewport, value):
        if self._center_w is None:
            if value > 0:
                self.radius = float(value)
                p = _panel(self._app)
                try:
                    p.sm_radius.setValue(self.radius)   # panel = jedno źródło prawdy
                except Exception:
                    pass
                _flash(viewport, f"Smoove: {tr('vcb_radius')} = {self.radius:.2f} m", 3000)
                viewport.update()
                return True
            return False
        self._dz = float(value)
        sc.apply_dz(self._terrain.mesh, self._weights, self._dz)
        self._commit(viewport)
        return True

    def on_cancel(self, viewport):
        self._cancel(viewport)

    def _cancel(self, viewport, quiet=False):
        if self._terrain is not None and self._before is not None:
            self._terrain.mesh.restore_state(self._before)
            self._terrain.mesh._chunk_dirty = True
            sc.refresh(viewport)
            if not quiet:
                _flash(viewport, tr("smoove_interactive_cancel"), 2000)
        self._reset()

    def _commit(self, viewport):
        terrain, before = self._terrain, self._before
        dz = self._dz
        if terrain is None or before is None:
            self._reset()
            return
        if abs(dz) < 1e-6:
            self._cancel(viewport, quiet=True)
            return
        try:
            sc.execute_terrain_edit(viewport, terrain.mesh, before, after=terrain.mesh.capture_state())
            _flash(viewport, tr("smoove_interactive_done", dz=dz), 4000)
        except Exception as e:
            terrain.mesh.restore_state(before)
            sc.refresh(viewport)
            _flash(viewport, f"Smoove {tr('err_label')}: {e}", 6000)
        self._reset()


# ===========================================================================
# 2. Stamp
# ===========================================================================

class StampTool(Tool):
    name = "Stamp"
    description = "Stamps a building or pad footprint into terrain with batter slopes."
    uses_snap = False
    wireframe_color = (1.0, 0.45, 0.0, 1.0)

    def __init__(self, app: Any = None):
        self._app = app
        self.offset = 2.0
        self._footprint = None   # shapely Polygon (world)
        self._fz = 0.0
        self.vcb_label = tr("vcb_offset")
        self._reset()

    def _reset(self):
        self._terrain = None
        self._before = None
        self._weights = {}
        self._orig = {}
        self._pad_local = None
        self._anchor: QVector3D | None = None
        self._press_z = 0.0
        self._pad_z = 0.0
        self._dz = 0.0
        self.vcb_label = tr("vcb_offset")

    @property
    def start_point(self):
        return self._anchor

    def on_activate(self, viewport):
        self._vp = viewport
        p = _panel(self._app)
        if p is not None and hasattr(p, "st_offset"):
            try:
                self.offset = float(p.st_offset.value())
            except Exception:
                pass
        self._reset()
        sel = sc.get_selection(viewport)
        terrain = sc.find_terrain(viewport.scene, sel)
        self._footprint, self._fz = (None, 0.0)
        try:
            self._footprint, self._fz = sc.collect_footprint(
                [o for o in sel if not sc.is_terrain_group(o)], exclude=terrain)
        except Exception:
            self._footprint = None
        if self._footprint is None:
            _flash(viewport, tr("stamp_interactive_pick_footprint"), 9000)
        else:
            _flash(viewport, tr("stamp_interactive_pick_terrain", offset=self.offset), 9000)

    def on_deactivate(self, viewport):
        self._cancel(viewport, quiet=True)

    def drag_plane(self, viewport):
        if self._anchor is None:
            return None
        return _vertical_plane(viewport, self._anchor)

    def rubber_band_lines(self):
        if self._footprint is None:
            return []
        z = (self._pad_z if self._anchor is not None else self._fz)
        lines = []
        inner_shp = self._footprint
        outer_shp = None
        try:
            outer_shp = inner_shp.buffer(self.offset, join_style=1)
        except Exception:
            pass

        # 1. Obrys wewnętrzny (półka)
        for ring in sc.ring_lines(inner_shp):
            for a, b in zip(ring[:-1], ring[1:]):
                lines.append((QVector3D(a[0], a[1], z), QVector3D(b[0], b[1], z)))

        # 2. Obrys zewnętrzny i przestrzenne promienie skarpy (3D batter slope rays)
        if outer_shp is not None:
            z_outer = self._base_pad if getattr(self, "_base_pad", None) is not None else z
            for ring in sc.ring_lines(outer_shp):
                for a, b in zip(ring[:-1], ring[1:]):
                    lines.append((QVector3D(a[0], a[1], z_outer), QVector3D(b[0], b[1], z_outer)))

            try:
                from shapely.geometry import Point
                ext_coords = list(inner_shp.exterior.coords)
                pts_to_project = []
                for i in range(len(ext_coords) - 1):
                    p0 = ext_coords[i]
                    p1 = ext_coords[i + 1]
                    pts_to_project.append(p0)
                    seg_len = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
                    if seg_len > 4.0:
                        n_sub = int(seg_len // 3.0)
                        for s in range(1, n_sub + 1):
                            t = s / (n_sub + 1)
                            pts_to_project.append((p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t))

                out_ext = outer_shp.exterior
                for pt in pts_to_project:
                    nearest_dist = out_ext.project(Point(pt))
                    nearest_pt = out_ext.interpolate(nearest_dist)
                    p_in_3d = QVector3D(pt[0], pt[1], z)
                    p_out_3d = QVector3D(nearest_pt.x, nearest_pt.y, z_outer)
                    lines.append((p_in_3d, p_out_3d))
            except Exception:
                pass

        return lines

    def on_hover(self, ctx):
        if self._anchor is None:
            return
        self._dz = float(ctx.world.z()) - self._press_z
        self._apply()
        sc.refresh(ctx.viewport)
        _flash(ctx.viewport, tr("stamp_interactive_hover", pad_z=self._pad_z), 2000)

    def _apply(self):
        base = self._base_pad
        self._pad_z = base + self._dz
        zl = sc.to_local(self._terrain, QVector3D(0, 0, self._pad_z)).z()
        sc.apply_pad(self._terrain.mesh, self._weights, zl)

    def on_click(self, ctx):
        vp = ctx.viewport
        if self._anchor is not None:
            self._commit(vp)
            return
        face, grp = _pick_group(vp, ctx)
        if self._footprint is None:
            if face is None:
                _flash(vp, tr("stamp_interactive_pick_footprint"), 4000)
                return
            fp, fz = sc.collect_footprint([], picked=(face, grp))
            if fp is None:
                _flash(vp, tr("stamp_interactive_pick_footprint"), 4000)
                return
            self._footprint, self._fz = fp, fz
            _flash(vp, tr("stamp_interactive_pick_terrain", offset=self.offset), 8000)
            vp.update()
            return
        terrain = _owner_terrain(vp, grp)
        if terrain is None or getattr(terrain, "mesh", None) is None:
            _flash(vp, tr("stamp_interactive_pick_terrain", offset=self.offset), 4000)
            return
        mesh = terrain.mesh
        self._terrain = terrain
        self._before = mesh.capture_state()
        try:
            p = _panel(self._app)
            mat = p.st_pad_mat.currentText() if (p is not None and hasattr(p, "st_pad_mat")) else None
            slope_mat = p.st_slope_mat.currentText() if (p is not None and hasattr(p, "st_slope_mat")) else None
            self._pad_local = sc.local_polygon(terrain, self._footprint)
            sc.stamp_cut(terrain, self._pad_local, self.offset, pad_attrs=paint_attrs(mat),
                         slope_attrs=paint_attrs(slope_mat), slope_steps=1)
            self._weights = sc.stamp_weights(mesh, self._pad_local, self.offset)
            self._orig = {v: p0 for v, (p0, _w) in self._weights.items()}
        except Exception as e:
            mesh.restore_state(self._before)
            sc.refresh(vp)
            self._reset()
            _flash(vp, f"Stamp {tr('err_label')}: {e}", 6000)
            return

        # Sample average terrain elevation under the footprint
        try:
            from .geometry import point_z_on_triangle
            tris, _, _ = sc.read_terrain(mesh)
            elevs = []
            for pt in self._pad_local.exterior.coords:
                for tri in tris:
                    z = point_z_on_triangle(pt[0], pt[1], tri)
                    if z is not None:
                        elevs.append(z)
                        break
            if elevs:
                avg_loc_z = sum(elevs) / len(elevs)
                self._base_pad = float(sc.to_world(terrain, QVector3D(0, 0, avg_loc_z)).z())
            else:
                self._base_pad = self._fz
        except Exception:
            self._base_pad = self._fz

        self._anchor = QVector3D(ctx.world)
        self._press_z = float(ctx.world.z())
        self._dz = 0.0
        self.vcb_label = tr("vcb_offset_z")
        self._apply()
        sc.refresh(vp)

    def on_value(self, viewport, value):
        if self._anchor is None:
            if value > 0:
                self.offset = float(value)
                _flash(viewport, f"Stamp: {tr('vcb_offset')} = {self.offset:.2f} m", 3000)
                viewport.update()
                return True
            return False
        self._dz = float(value)
        self._apply()
        self._commit(viewport)
        return True

    def on_cancel(self, viewport):
        self._cancel(viewport)

    def _cancel(self, viewport, quiet=False):
        if self._terrain is not None and self._before is not None:
            self._terrain.mesh.restore_state(self._before)
            sc.refresh(viewport)
            if not quiet:
                _flash(viewport, f"Stamp: {tr('btn_close')}", 2000)
        self._reset()

    def _commit(self, viewport):
        terrain, before = self._terrain, self._before
        if terrain is None:
            return
        cut, fill = sc.earthwork(terrain.mesh, self._orig)
        try:
            sc.execute_terrain_edit(viewport, terrain.mesh, before, after=terrain.mesh.capture_state())
            _flash(viewport, tr("stamp_interactive_done", pad_z=self._pad_z, cut=cut, fill=fill), 8000)
        except Exception as e:
            terrain.mesh.restore_state(before)
            sc.refresh(viewport)
            _flash(viewport, f"Stamp {tr('err_label')}: {e}", 6000)
        self._reset()


# ===========================================================================
# 3. Drape
# ===========================================================================

class DrapeTool(Tool):
    name = "Drape"
    description = "Projects lines, paths, or roads vertically onto the terrain surface."
    uses_snap = False

    def __init__(self, app: Any = None):
        self._app = app
        self._segs = []

    def on_activate(self, viewport):
        sel = sc.get_selection(viewport)
        terrain = sc.find_terrain(viewport.scene, sel)
        self._segs = sc.collect_world_segments(
            [o for o in sel if not sc.is_terrain_group(o)], exclude=terrain)
        if not self._segs:
            _flash(viewport, tr("drape_interactive_no_sel"), 9000)
        else:
            _flash(viewport, tr("drape_interactive_ready", n=len(self._segs)), 9000)

    def on_deactivate(self, viewport):
        self._segs = []

    def rubber_band_lines(self):
        if not self._segs:
            return []
        lines = []
        width = 0.0
        p = _panel(self._app)
        if p is not None and hasattr(p, "dr_width"):
            try:
                width = float(p.dr_width.value())
            except Exception:
                width = 0.0

        if width <= 0.01:
            for a, b in self._segs:
                lines.append((QVector3D(*a), QVector3D(*b)))
        else:
            hw = width * 0.5
            for a, b in self._segs:
                # Oś ścieżki / drogi
                lines.append((QVector3D(*a), QVector3D(*b)))

                dx = b[0] - a[0]
                dy = b[1] - a[1]
                L = math.hypot(dx, dy)
                if L > 1e-6:
                    nx = -dy / L * hw
                    ny = dx / L * hw

                    # Krawędzie lewa i prawa (krawężniki / obrys pasa drogowego)
                    al = QVector3D(a[0] + nx, a[1] + ny, a[2])
                    bl = QVector3D(b[0] + nx, b[1] + ny, b[2])
                    lines.append((al, bl))

                    ar = QVector3D(a[0] - nx, a[1] - ny, a[2])
                    br = QVector3D(b[0] - nx, b[1] - ny, b[2])
                    lines.append((ar, br))

                    # Poprzeczki wstęgi drogi
                    lines.append((al, ar))
                    lines.append((bl, br))
        return lines

    def on_click(self, ctx):
        vp = ctx.viewport
        if not self._segs:
            _flash(vp, tr("drape_interactive_no_sel"), 5000)
            return
        face, grp = _pick_group(vp, ctx)
        terrain = _owner_terrain(vp, grp)
        if terrain is None or getattr(terrain, "mesh", None) is None:
            _flash(vp, tr("msg_select_drape_lines"), 4000)
            return
        p = _panel(self._app)
        width = 0.0
        mat = None
        try:
            if p is not None:
                width = float(p.dr_width.value())
                if getattr(p, "dr_paint", None) is not None and p.dr_paint.isChecked():
                    mat = p.dr_mat.currentText()
        except Exception:
            pass
        try:
            n = sc.drape_onto_terrain(vp, terrain, self._segs, width, paint_attrs(mat))
            _flash(vp, tr("drape_interactive_done", n=n), 8000)
        except Exception as e:
            _flash(vp, f"Drape {tr('err_label')}: {e}", 6000)
            return
        self._segs = []
        win = vp.window() if hasattr(vp, "window") else None
        if win is not None and hasattr(win, "_activate_tool"):
            try:
                win._activate_tool("select")
            except Exception:
                pass


# ===========================================================================
# 4. From Scratch (Siatka od podstaw - 3 kliknięcia)
# ===========================================================================

class FromScratchTool(Tool):
    """Interactive rectangular terrain grid drawing:
    1. Origin (P0)
    2. Length & Orientation (P1)
    3. Width (P2)
    Real-time visual grid rubberband lines (SketchUp Sandbox style).
    """
    name = "From Scratch"
    description = "Interactive rectangular terrain grid drawing: 1. Origin, 2. Length/Direction, 3. Width."
    uses_snap = True
    wireframe_color = (0.95, 0.45, 0.16, 1.0)

    def __init__(self, app: Any = None):
        super().__init__()
        self._app = app
        self.spacing = DEFAULT_FROM_SCRATCH["spacing"]
        self._pattern = DEFAULT_FROM_SCRATCH.get("pattern", "alternating")
        self._material = DEFAULT_FROM_SCRATCH.get("material", "Natural Grass")
        self.vcb_label = tr("vcb_grid")
        self._reset()

    def _reset(self):
        self._step = 0  # 0: waiting for p0, 1: waiting for p1, 2: waiting for p2
        self._p0: QVector3D | None = None
        self._p1: QVector3D | None = None
        self._cursor: QVector3D | None = None
        self.vcb_label = tr("vcb_grid")

    @property
    def start_point(self) -> QVector3D | None:
        return self._p0

    def on_activate(self, viewport):
        self._sync_panel()
        self._reset()
        _flash(viewport, tr("scratch_interactive_step1", sp=self.spacing), 9000)

    def on_deactivate(self, viewport):
        self._reset()

    def _sync_panel(self):
        p = _panel(self._app)
        if p is None:
            return
        try:
            if hasattr(p, "sc_spacing"):
                self.spacing = float(p.sc_spacing.value())
            if hasattr(p, "sc_pattern"):
                self._pattern = p.sc_pattern.currentData() or "alternating"
            if hasattr(p, "sc_material"):
                self._material = p.sc_material.currentText() or "Natural Grass"
        except Exception:
            pass

    def on_hover(self, ctx):
        self._cursor = QVector3D(ctx.world)
        if self._step == 0:
            self._sync_panel()
        vp = ctx.viewport
        if vp is not None and hasattr(vp, "update"):
            vp.update()

    def rubber_band_lines(self):
        cur = self._cursor
        if cur is None:
            return []
        if self._step == 1 and self._p0 is not None:
            return [(QVector3D(self._p0), QVector3D(cur))]
        if self._step == 2 and self._p0 is not None and self._p1 is not None:
            p0 = self._p0
            p1 = self._p1
            u = p1 - p0
            len_u = u.length()
            if len_u < 1e-4:
                return [(p0, cur)]
            u_dir = u / len_u
            v_perp = QVector3D(-u_dir.y(), u_dir.x(), 0.0)
            if v_perp.length() < 0.1:
                v_perp = QVector3D(0.0, 0.0, 1.0)
            v_perp = v_perp.normalized()
            proj_v = QVector3D.dotProduct(cur - p1, v_perp)
            v_vec = v_perp * proj_v
            len_v = abs(proj_v)

            c0 = p0
            c1 = p1
            c2 = p1 + v_vec
            c3 = p0 + v_vec

            lines = [(c0, c1), (c1, c2), (c2, c3), (c3, c0)]

            # Rysowanie linii wewnętrznych siatki w czasie rzeczywistym (styl SketchUp)
            if len_v > 0.1 and self.spacing > 0.05:
                cols = max(1, int(round(len_u / self.spacing)))
                rows = max(1, int(round(len_v / self.spacing)))
                if cols <= 60 and rows <= 60:
                    for c in range(1, cols):
                        t = c / cols
                        a = c0 + (c1 - c0) * t
                        b = c3 + (c2 - c3) * t
                        lines.append((a, b))
                    for r in range(1, rows):
                        t = r / rows
                        a = c0 + (c3 - c0) * t
                        b = c1 + (c2 - c1) * t
                        lines.append((a, b))
            return lines
        return []

    def on_click(self, ctx):
        vp = ctx.viewport
        w = QVector3D(ctx.world)
        if self._step == 0:
            self._sync_panel()
            self._p0 = w
            self._step = 1
            self.vcb_label = tr("vcb_length")
            _flash(vp, tr("scratch_interactive_step2", x=w.x(), y=w.y()), 9000)
            vp.update()
            return

        if self._step == 1:
            if self._p0 is None or (w - self._p0).length() < 1e-4:
                return
            self._p1 = w
            self._step = 2
            self.vcb_label = tr("vcb_width")
            len_u = (self._p1 - self._p0).length()
            _flash(vp, tr("scratch_interactive_step3", len_u=len_u), 9000)
            vp.update()
            return

        if self._step == 2:
            self._commit(vp)

    def on_value(self, viewport, value):
        if self._step == 0:
            if value > 0:
                self.spacing = float(value)
                p = _panel(self._app)
                try:
                    if p is not None and hasattr(p, "sc_spacing"):
                        p.sc_spacing.setValue(self.spacing)
                except Exception:
                    pass
                _flash(viewport, f"From Scratch: {tr('vcb_grid')} = {self.spacing:.2f} m", 3000)
                viewport.update()
                return True
            return False

        if self._step == 1:
            if value > 0 and self._p0 is not None:
                d = (self._cursor - self._p0) if self._cursor else QVector3D(1, 0, 0)
                d = QVector3D(d.x(), d.y(), 0.0)
                if d.length() < 1e-4:
                    d = QVector3D(1, 0, 0)
                self._p1 = self._p0 + d.normalized() * float(value)
                self._step = 2
                self.vcb_label = tr("vcb_width")
                _flash(viewport, tr("scratch_interactive_step3", len_u=float(value)), 9000)
                viewport.update()
                return True
            return False

        if self._step == 2:
            if value > 0:
                self._commit(viewport, override_width=float(value))
                return True
            return False

    def on_cancel(self, viewport):
        self._reset()
        _flash(viewport, f"From Scratch: {tr('btn_close')}", 2000)
        viewport.update()

    def _commit(self, viewport, override_width: float | None = None):
        if self._p0 is None or self._p1 is None:
            self._reset()
            return
        p0 = self._p0
        p1 = self._p1
        u = p1 - p0
        len_u = u.length()
        if len_u < 1e-4:
            self._reset()
            return
        u_dir = u / len_u
        v_perp = QVector3D(-u_dir.y(), u_dir.x(), 0.0)
        if v_perp.length() < 0.1:
            v_perp = QVector3D(0.0, 0.0, 1.0)
        v_perp = v_perp.normalized()

        if override_width is not None:
            proj_v = QVector3D.dotProduct(self._cursor - p1, v_perp) if self._cursor else 1.0
            sign = 1.0 if proj_v >= 0 else -1.0
            v_dir = v_perp * sign
            len_v = override_width
        else:
            cur = self._cursor if self._cursor is not None else p1
            proj_v = QVector3D.dotProduct(cur - p1, v_perp)
            len_v = abs(proj_v)
            if len_v < 1e-4:
                len_v = self.spacing * 2.0
                sign = 1.0
            else:
                sign = 1.0 if proj_v >= 0 else -1.0
            v_dir = v_perp * sign

        sp = max(0.1, self.spacing)
        cols = max(1, int(math.ceil(len_u / sp)))
        rows = max(1, int(math.ceil(len_v / sp)))

        mesh = Mesh()
        attrs = paint_attrs(self._material) or {"color": (0.36, 0.58, 0.25, 1.0), "back_color": (0.36, 0.58, 0.25, 1.0)}

        # Wektor normalny siatki
        cross_z = u_dir.x() * v_dir.y() - u_dir.y() * v_dir.x()
        flip = cross_z < 0

        # Wierzchołki siatki w przestrzeni świata 3D
        grid = []
        for r in range(rows + 1):
            row_pts = []
            yr = (r / rows) * len_v
            for c in range(cols + 1):
                xc = (c / cols) * len_u
                pt = p0 + u_dir * xc + v_dir * yr
                row_pts.append(pt)
            grid.append(row_pts)

        # Ścianki (trójkąty) z naprzemiennymi przekątnymi (diamond pattern)
        pat = self._pattern
        for r in range(rows):
            for c in range(cols):
                bl = grid[r][c]
                br = grid[r][c + 1]
                tr = grid[r + 1][c + 1]
                tl = grid[r + 1][c]

                if (r + c) % 2 == 1 if pat == "alternating" else False:
                    t1 = [bl, br, tl]
                    t2 = [br, tr, tl]
                else:
                    t1 = [bl, br, tr]
                    t2 = [bl, tr, tl]

                if flip:
                    t1 = [t1[0], t1[2], t1[1]]
                    t2 = [t2[0], t2[2], t2[1]]

                f1 = mesh.add_face(t1)
                f2 = mesh.add_face(t2)

                for f in (f1, f2):
                    if f is not None:
                        f.attrs = dict(attrs)

        # Widoczna siatka kwadratów/trójkątów (zgodnie z opcją z panelu i SketchUp From Scratch)
        for e in mesh.edges:
            e.soft = False
            e.hidden = False

        grp = Group(mesh=mesh, name="Terrain (From Scratch)")
        grp.component = False
        grp.xform = QMatrix4x4()
        sc.mark_terrain(grp, origin="FromScratch")
        try:
            if getattr(grp, "ext", None) is None:
                grp.ext = {}
            grp.ext.setdefault(PLUGIN_KEY, {})
            grp.ext[PLUGIN_KEY]["spacing"] = sp
            grp.ext[PLUGIN_KEY]["size_x"] = len_u
            grp.ext[PLUGIN_KEY]["size_y"] = len_v
        except Exception:
            pass

        # Dodanie grupy do sceny z pełnym wsparciem Undo
        from .operations import commit_group_to_scene
        try:
            commit_group_to_scene(self._app, grp, select=True)
            _flash(viewport, tr("scratch_interactive_done", w=len_u, h=len_v, sp=sp, n=len(mesh.faces)), 6000)
        except Exception as e:
            _flash(viewport, f"From Scratch {tr('err_label')}: {e}", 5000)

        self._reset()
        viewport.update()


# ===========================================================================
# 5. FlipEdgeTool – Odwracanie przekątnej z podglądem na żywo (HUD)
# ===========================================================================

class FlipEdgeTool(Tool):
    """Interaktywne narzędzie do odwracania przekątnej w czworokącie siatki terenu TIN."""
    name = "Flip Edge"
    description = "Click on an inner terrain edge to flip its diagonal."
    uses_snap = False
    wireframe_color = (0.0, 0.85, 1.0, 1.0)

    def __init__(self, app: Any = None):
        self._app = app
        self._vp = None
        self._hover_edge: tuple[QVector3D, QVector3D] | None = None
        self._preview_diag: tuple[QVector3D, QVector3D] | None = None
        self._hover_terrain = None
        self._hover_pt: Point3D | None = None

    def on_activate(self, viewport):
        self._vp = viewport
        self._hover_edge = None
        self._preview_diag = None
        self._hover_terrain = None
        _flash(viewport, tr("msg_flip_edge_hint"), 8000)

    def on_deactivate(self, viewport):
        self._hover_edge = None
        self._preview_diag = None
        self._hover_terrain = None
        if viewport:
            viewport.update()

    def rubber_band_lines(self):
        lines = []
        if self._hover_edge is not None:
            lines.append((self._hover_edge[0], self._hover_edge[1]))
        if self._preview_diag is not None:
            lines.append((self._preview_diag[0], self._preview_diag[1]))
        return lines

    def on_hover(self, ctx):
        vp = getattr(ctx, "viewport", None)
        if vp is None or not hasattr(ctx, "world") or ctx.world is None:
            return

        face, grp = _pick_group(vp, ctx)
        terrain = _owner_terrain(vp, grp)
        if terrain is None:
            terrain = find_terrain_group(getattr(vp, "scene", None), sc.get_selection(vp))

        if terrain is None or getattr(terrain, "mesh", None) is None:
            if self._hover_edge is not None:
                self._hover_edge = None
                self._preview_diag = None
                self._hover_terrain = None
                vp.update()
            return

        self._hover_terrain = terrain
        click_world = (float(ctx.world.x()), float(ctx.world.y()), float(ctx.world.z()))
        self._hover_pt = click_world

        pt_loc_qv = sc.to_local(terrain, to_qvector3d(click_world))
        pt_loc = (float(pt_loc_qv.x()), float(pt_loc_qv.y()), float(pt_loc_qv.z()))

        tris, _attrs, _h = sc.read_terrain(terrain.mesh)
        edge_info = find_closest_interior_edge(tris, pt_loc, pick_radius=8.0)

        if edge_info is not None:
            (ea, eb), (opp0, opp1), is_convex = edge_info
            ea_w = sc.to_world(terrain, to_qvector3d(ea))
            eb_w = sc.to_world(terrain, to_qvector3d(eb))
            opp0_w = sc.to_world(terrain, to_qvector3d(opp0))
            opp1_w = sc.to_world(terrain, to_qvector3d(opp1))
            self._hover_edge = (ea_w, eb_w)
            self._preview_diag = (opp0_w, opp1_w) if is_convex else None
        else:
            self._hover_edge = None
            self._preview_diag = None

        vp.update()

    def on_click(self, ctx):
        vp = getattr(ctx, "viewport", None)
        face, grp = _pick_group(vp, ctx)
        terrain = _owner_terrain(vp, grp) or self._hover_terrain
        if terrain is None:
            terrain = find_terrain_group(getattr(vp, "scene", None), sc.get_selection(vp))

        click_pt = self._hover_pt
        if click_pt is None and hasattr(ctx, "world") and ctx.world is not None:
            click_pt = to_point3d(ctx.world)

        if terrain is None or click_pt is None:
            _flash(vp, tr("msg_no_terrain"), 3000)
            return

        try:
            ok = op_apply_flip_edge(self._app, terrain, click_pt)
            if ok:
                _flash(vp, tr("msg_edge_flipped"), 2500)
                self.on_hover(ctx)
            else:
                _flash(vp, tr("msg_edge_cannot_flip"), 2500)
        except Exception as e:
            _flash(vp, f"{tr('err_label')}: {e}", 3000)


# ===========================================================================
# 6. AddDetailTool – Zagęszczanie siatki z podglądem na żywo (HUD)
# ===========================================================================

class AddDetailTool(Tool):
    """Interaktywne narzędzie do lokalnego zagęszczania siatki (podział trójkąta na 4)."""
    name = "Add Detail"
    description = "Click on a terrain triangle or edge to subdivide it into 4 smaller triangles."
    uses_snap = False
    wireframe_color = (1.0, 0.80, 0.0, 1.0)

    def __init__(self, app: Any = None):
        self._app = app
        self._vp = None
        self._hover_lines: list[tuple[QVector3D, QVector3D]] = []
        self._hover_terrain = None
        self._hover_pt: Point3D | None = None

    def on_activate(self, viewport):
        self._vp = viewport
        self._hover_lines = []
        self._hover_terrain = None
        _flash(viewport, tr("msg_add_detail_active"), 8000)

    def on_deactivate(self, viewport):
        self._hover_lines = []
        self._hover_terrain = None
        if viewport:
            viewport.update()

    def rubber_band_lines(self):
        return self._hover_lines

    def on_hover(self, ctx):
        vp = getattr(ctx, "viewport", None)
        if vp is None or not hasattr(ctx, "world") or ctx.world is None:
            return

        face, grp = _pick_group(vp, ctx)
        terrain = _owner_terrain(vp, grp)
        if terrain is None:
            terrain = find_terrain_group(getattr(vp, "scene", None), sc.get_selection(vp))

        if terrain is None or getattr(terrain, "mesh", None) is None:
            if self._hover_lines:
                self._hover_lines = []
                self._hover_terrain = None
                vp.update()
            return

        self._hover_terrain = terrain
        click_world = (float(ctx.world.x()), float(ctx.world.y()), float(ctx.world.z()))
        self._hover_pt = click_world

        pt_loc_qv = sc.to_local(terrain, to_qvector3d(click_world))
        pt_loc = (float(pt_loc_qv.x()), float(pt_loc_qv.y()), float(pt_loc_qv.z()))

        tris, _attrs, _h = sc.read_terrain(terrain.mesh)
        target_tri = None
        for tri in tris:
            if point_in_polygon_2d(pt_loc, tri):
                target_tri = tri
                break
        if target_tri is None:
            closest_d = float("inf")
            for tri in tris:
                c = ((tri[0][0] + tri[1][0] + tri[2][0]) / 3.0,
                     (tri[0][1] + tri[1][1] + tri[2][1]) / 3.0,
                     (tri[0][2] + tri[1][2] + tri[2][2]) / 3.0)
                d = math.hypot(pt_loc[0] - c[0], pt_loc[1] - c[1])
                if d < closest_d and d < 15.0:
                    closest_d = d
                    target_tri = tri

        if target_tri is not None:
            v0, v1, v2 = target_tri
            m01 = ((v0[0] + v1[0]) * 0.5, (v0[1] + v1[1]) * 0.5, (v0[2] + v1[2]) * 0.5)
            m12 = ((v1[0] + v2[0]) * 0.5, (v1[1] + v2[1]) * 0.5, (v1[2] + v2[2]) * 0.5)
            m20 = ((v2[0] + v0[0]) * 0.5, (v2[1] + v0[1]) * 0.5, (v2[2] + v0[2]) * 0.5)

            m01_w = sc.to_world(terrain, to_qvector3d(m01))
            m12_w = sc.to_world(terrain, to_qvector3d(m12))
            m20_w = sc.to_world(terrain, to_qvector3d(m20))

            self._hover_lines = [
                (m01_w, m12_w),
                (m12_w, m20_w),
                (m20_w, m01_w),
            ]
        else:
            self._hover_lines = []

        vp.update()

    def on_click(self, ctx):
        vp = getattr(ctx, "viewport", None)
        face, grp = _pick_group(vp, ctx)
        terrain = _owner_terrain(vp, grp) or self._hover_terrain
        if terrain is None:
            terrain = find_terrain_group(getattr(vp, "scene", None), sc.get_selection(vp))

        click_pt = self._hover_pt
        if click_pt is None and hasattr(ctx, "world") and ctx.world is not None:
            click_pt = to_point3d(ctx.world)

        if terrain is None or click_pt is None:
            _flash(vp, tr("msg_no_terrain"), 3000)
            return

        try:
            ok, count = op_apply_add_detail_at_point(self._app, terrain, click_pt)
            if ok:
                _flash(vp, tr("msg_detail_added", n=count), 2500)
                self.on_hover(ctx)
            else:
                _flash(vp, tr("msg_detail_missed"), 2500)
        except Exception as e:
            _flash(vp, f"{tr('err_label')}: {e}", 3000)
