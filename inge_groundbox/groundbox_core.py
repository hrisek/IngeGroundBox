# SPDX-License-Identifier: GPL-3.0-or-later
"""
inge_groundbox/groundbox_core.py
============================
Rdzeń logiki GroundBox oparty na rzeczywistym API IngeTrazo (core.mesh / core.history):

* ``TerrainEditCommand``  – cofalna (Ctrl+Z) edycja siatki ISTNIEJĄCEJ grupy terenu
  (``mesh.capture_state`` / ``restore_state``). ``SnapshotImport`` tego nie potrafi.
* ``knife_cut``            – wierne „Drape”: linie 2D rozcinają trójkąty terenu,
  powstała siatka jest szczelna (wspólne wierzchołki na liniach cięcia).
* ``rebuild_terrain_mesh`` – przebudowa siatki grupy w miejscu: krawędzie rzutowane są
  TWARDE (widoczne), reszta MIĘKKA – dokładnie jak w SketchUpie, więc Wiadro Farby
  maluje cały obszar ograniczony rzutowanym obrysem.
* ``smoove_weights`` / ``stamp_weights`` – model wag wierzchołków; podgląd na żywo
  przesuwa wierzchołki przez ``mesh.place_vertex`` (unieważnia cache GPU).
"""
from __future__ import annotations

import math
from typing import Any, Iterable, Sequence

try:
    from PySide6.QtGui import QMatrix4x4, QVector3D
except ImportError:  # testy offline
    from .operations import QMatrix4x4, QVector3D  # type: ignore

try:
    from core.history import Command as _BaseCommand  # type: ignore
except ImportError:
    class _BaseCommand:  # type: ignore
        def do(self, scene): ...
        def undo(self, scene): ...

from .constants import PLUGIN_KEY

Pt2 = tuple[float, float]
Pt3 = tuple[float, float, float]
Tri = list[Pt3]

HARD_TOL = 2e-4      # odległość krawędzi od linii rzutowania, by uznać ją za twardą


# ===========================================================================
# 1. Historia (Undo/Redo) dla edycji istniejącej grupy
# ===========================================================================

class TerrainEditCommand(_BaseCommand):
    """Jeden krok Undo/Redo dla edycji siatki grupy terenu.

    ``before`` to ``mesh.capture_state()`` sprzed edycji. Jeśli ``after`` nie
    podano, ``mutate(mesh)`` zostanie wykonane w ``do`` i stan po nim zapamiętany.
    Gdy edycję wykonano już na żywo (Smoove/Stamp), podaje się gotowe ``after``.
    """

    def __init__(self, mesh: Any, before: dict, after: dict | None = None, mutate=None):
        self.mesh = mesh
        self.before = before
        self.after = after
        self.mutate = mutate
        self.before_attrs = [dict(getattr(f, "attrs", {}) or {}) for f in getattr(mesh, "faces", [])]
        self.after_attrs = [dict(getattr(f, "attrs", {}) or {}) for f in getattr(mesh, "faces", [])] if after is not None else None

    def _apply_attrs(self, attrs):
        if not attrs:
            return
        faces = getattr(self.mesh, "faces", [])
        if len(faces) == len(attrs):
            for f, a in zip(faces, attrs):
                f.attrs = dict(a)

    def do(self, scene) -> None:
        if self.after is None:
            if self.mutate is not None:
                self.mutate(self.mesh)
            self.after = self.mesh.capture_state()
            self.after_attrs = [dict(getattr(f, "attrs", {}) or {}) for f in getattr(self.mesh, "faces", [])]
        else:
            self.mesh.restore_state(self.after)
            self._apply_attrs(self.after_attrs)
        _bump(scene, self.mesh)

    def undo(self, scene) -> None:
        self.mesh.restore_state(self.before)
        self._apply_attrs(self.before_attrs)
        _bump(scene, self.mesh)


def _bump(scene, mesh) -> None:
    try:
        mesh._chunk_dirty = True
        mesh._mut_serial = getattr(mesh, "_mut_serial", 0) + 1
        if hasattr(mesh, "version"):
            mesh.version += 1
    except Exception:
        pass
    if scene is not None and hasattr(scene, "version"):
        scene.version += 1


def execute_terrain_edit(viewport: Any, mesh: Any, before: dict,
                         after: dict | None = None, mutate=None) -> None:
    """Wykonuje edycję terenu przez historię widoku i odświeża ekran."""
    cmd = TerrainEditCommand(mesh, before, after, mutate)
    hist = getattr(viewport, "history", None)
    if hist is not None:
        hist.execute(cmd)
        err = getattr(hist, "last_error", None)
        if err:
            raise RuntimeError(err)
    else:
        cmd.do(getattr(viewport, "scene", None))
    refresh(viewport)


def refresh(viewport: Any) -> None:
    if viewport is None:
        return
    for name in ("notify_scene_changed", "update"):
        fn = getattr(viewport, name, None)
        if callable(fn):
            try:
                fn()
            except Exception:
                pass
    scene = getattr(viewport, "scene", None)
    if scene is not None:
        for sname in ("notify_scene_changed", "notify_modified", "update"):
            sfn = getattr(scene, sname, None)
            if callable(sfn):
                try:
                    sfn()
                except Exception:
                    pass


# ===========================================================================
# 2. Zaznaczenie, grupy terenu, transformacje
# ===========================================================================

def get_selection(app_or_vp: Any) -> list:
    """Prawdziwe zaznaczenie IngeTrazo leży w ``scene.selection`` (set)."""
    scene = getattr(app_or_vp, "scene", None)
    if scene is None:
        vp = getattr(app_or_vp, "viewport", None)
        scene = getattr(vp, "scene", None)
    sel = getattr(scene, "selection", None) if scene is not None else None
    return list(sel) if sel else []


def is_terrain_group(obj: Any) -> bool:
    ext = getattr(obj, "ext", None) or {}
    try:
        if isinstance(ext, dict) and ext.get(PLUGIN_KEY, {}).get("type") == "Terrain":
            return True
    except Exception:
        pass
    name = str(getattr(obj, "name", "") or "").lower()
    return ("teren" in name or "terrain" in name) and getattr(obj, "mesh", None) is not None


def mark_terrain(group: Any, origin: str = "Manual") -> None:
    try:
        if getattr(group, "ext", None) is None:
            group.ext = {}
        group.ext.setdefault(PLUGIN_KEY, {})
        group.ext[PLUGIN_KEY]["type"] = "Terrain"
        group.ext[PLUGIN_KEY].setdefault("origin", origin)
    except Exception:
        pass


def find_terrain(scene: Any, selection: Sequence[Any] = ()) -> Any | None:
    for obj in selection:
        if is_terrain_group(obj):
            return obj
    for obj in getattr(scene, "groups", []) if scene is not None else []:
        if is_terrain_group(obj):
            return obj
    return None


def _xform(group: Any):
    x = getattr(group, "xform", None) if group is not None else None
    return x


def to_world(group: Any, p: Any) -> QVector3D:
    q = qv(p)
    x = _xform(group)
    return x.map(q) if (x is not None and hasattr(x, "map")) else q


def to_local(group: Any, p: Any) -> QVector3D:
    q = qv(p)
    x = _xform(group)
    if x is None or not hasattr(x, "inverted"):
        return q
    inv, ok = x.inverted()
    return inv.map(q) if ok else q


def qv(p: Any) -> QVector3D:
    if isinstance(p, QVector3D):
        return QVector3D(p)
    if hasattr(p, "position"):
        return QVector3D(p.position)
    return QVector3D(float(p[0]), float(p[1]), float(p[2]))


def t3(p: Any) -> Pt3:
    if hasattr(p, "position"):
        p = p.position
    if hasattr(p, "x") and callable(p.x):
        return (float(p.x()), float(p.y()), float(p.z()))
    return (float(p[0]), float(p[1]), float(p[2]))


# ===========================================================================
# 3. Zbieranie linii (Drape) i obrysu (Stamp) z zaznaczenia – w świecie
# ===========================================================================

def collect_world_segments(selection: Sequence[Any], exclude: Any = None) -> list[tuple[Pt3, Pt3]]:
    """Wszystkie odcinki z zaznaczonych krawędzi / ścianek / grup (w świecie)."""
    segs: list[tuple[Pt3, Pt3]] = []

    def edge_pts(e, grp):
        a = getattr(e, "v0", None)
        b = getattr(e, "v1", None)
        if a is None or b is None:
            return None
        return t3(to_world(grp, a.position)), t3(to_world(grp, b.position))

    def walk(obj, grp):
        if obj is None or obj is exclude:
            return
        if hasattr(obj, "v0") and hasattr(obj, "v1"):           # Edge
            s = edge_pts(obj, grp)
            if s:
                segs.append(s)
            return
        if hasattr(obj, "loop") and hasattr(obj, "attrs"):        # Face
            pts = [t3(to_world(grp, v.position)) for v in obj.loop]
            for i in range(len(pts)):
                segs.append((pts[i], pts[(i + 1) % len(pts)]))
            return
        mesh = getattr(obj, "mesh", None)
        if mesh is not None:                                      # Group
            for e in getattr(mesh, "edges", []):
                if getattr(e, "soft", False) or getattr(e, "hidden", False):
                    continue
                s = edge_pts(e, obj)
                if s:
                    segs.append(s)
            for ch in getattr(obj, "children", None) or []:
                walk(ch, obj)

    for o in selection:
        walk(o, None)
    return [s for s in segs if math.dist(s[0][:2], s[1][:2]) > 1e-6]


def collect_footprint(selection: Sequence[Any], exclude: Any = None, picked=None):
    """Obrys odcisku (Stamp): shapely Polygon 2D w świecie + rzędna Z obrysu.

    Źródła: zaznaczona ścianka, grupa (rzut wszystkich ścianek = obrys bryły),
    lub zamknięta pętla krawędzi. ``picked`` = (face, group) wskazane kliknięciem.
    """
    from shapely.geometry import Polygon
    from shapely.ops import polygonize, unary_union

    polys = []
    zs: list[float] = []

    def add_face(f, grp):
        pts = [t3(to_world(grp, v.position)) for v in f.loop]
        if len(pts) < 3:
            return
        p = Polygon([(x, y) for x, y, _ in pts])
        if not p.is_valid:
            p = p.buffer(0)
        if p.area > 1e-6:
            polys.append(p)
            zs.extend(z for _, _, z in pts)

    def walk(obj, grp):
        if obj is None or obj is exclude:
            return
        if hasattr(obj, "loop") and hasattr(obj, "attrs"):
            add_face(obj, grp)
            return
        mesh = getattr(obj, "mesh", None)
        if mesh is not None:
            for f in getattr(mesh, "faces", []):
                add_face(f, obj)
            for ch in getattr(obj, "children", None) or []:
                walk(ch, obj)

    if picked is not None and picked[0] is not None:
        add_face(picked[0], picked[1])
    else:
        for o in selection:
            walk(o, None)
        if not polys:
            segs = collect_world_segments([o for o in selection if hasattr(o, "v0")], exclude)
            if segs:
                from shapely.geometry import LineString
                lines = unary_union([LineString([s[0][:2], s[1][:2]]) for s in segs])
                polys = [p for p in polygonize(lines) if p.area > 1e-6]
                zs = [z for s in segs for z in (s[0][2], s[1][2])]
    if not polys:
        return None, None
    shape = unary_union(polys).buffer(0)
    if shape.geom_type == "MultiPolygon":
        shape = max(shape.geoms, key=lambda g: g.area)
    # Zewnętrzny obrys (bez otworów) – odcisk to pełna półka.
    shape = Polygon(shape.exterior.coords)
    z = min(zs) if zs else 0.0
    return shape, z


# ===========================================================================
# 4. Triangulacja wielokąta (earcut, z otworami)
# ===========================================================================

def _area2(pts: Sequence[Pt2]) -> float:
    return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
               for i in range(len(pts))) * 0.5


def _earclip(pts: list[Pt2]) -> list[tuple[Pt2, Pt2, Pt2]]:
    """Ear clipping prostego wielokąta (CCW lub CW). Zachowuje punkty współliniowe."""
    if len(pts) < 3:
        return []
    if _area2(pts) < 0:
        pts = pts[::-1]
    idx = list(range(len(pts)))
    out = []

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    guard = 0
    while len(idx) > 3 and guard < 10000:
        guard += 1
        n = len(idx)
        clipped = False
        for k in range(n):
            i0, i1, i2 = idx[(k - 1) % n], idx[k], idx[(k + 1) % n]
            a, b, c = pts[i0], pts[i1], pts[i2]
            if cross(a, b, c) <= 1e-14:
                continue
            ok = True
            for j in idx:
                if j in (i0, i1, i2):
                    continue
                p = pts[j]
                if (cross(a, b, p) >= -1e-12 and cross(b, c, p) >= -1e-12
                        and cross(c, a, p) >= -1e-12):
                    ok = False
                    break
            if ok:
                out.append((a, b, c))
                idx.pop(k)
                clipped = True
                break
        if not clipped:
            # Zdegenerowane resztki (punkty współliniowe) – usuń najbardziej płaski wierzchołek.
            best = min(range(n), key=lambda k: abs(cross(pts[idx[(k - 1) % n]], pts[idx[k]], pts[idx[(k + 1) % n]])))
            a, b, c = pts[idx[(best - 1) % n]], pts[idx[best]], pts[idx[(best + 1) % n]]
            if abs(cross(a, b, c)) > 1e-14:
                out.append((a, b, c))
            idx.pop(best)
    if len(idx) == 3:
        a, b, c = (pts[i] for i in idx)
        if abs(cross(a, b, c)) > 1e-14:
            out.append((a, b, c))
    return out


def triangulate_polygon(poly) -> list[tuple[Pt2, Pt2, Pt2]]:
    """Triangulacja shapely Polygon (z otworami). mapbox_earcut gdy dostępny."""
    from shapely.geometry import Polygon
    if poly.is_empty or poly.area < 1e-10:
        return []
    ext = list(poly.exterior.coords)[:-1]
    holes = [list(r.coords)[:-1] for r in poly.interiors]
    try:
        import mapbox_earcut as earcut  # wbudowany w IngeTrazo
        import numpy as np
        rings = [ext] + holes
        verts = np.array([p for r in rings for p in r], dtype=np.float64).reshape(-1, 2)
        ends = np.cumsum([len(r) for r in rings]).astype(np.uint32)
        ids = earcut.triangulate_float64(verts, ends).reshape(-1, 3)
        res = []
        for i, j, k in ids:
            a, b, c = tuple(verts[i]), tuple(verts[j]), tuple(verts[k])
            if abs(_area2([a, b, c])) > 1e-14:
                res.append((a, b, c))
        if res:
            return res
    except Exception:
        pass
    if holes:
        # Rozetnij wielokąt pionową linią przez pierwszy otwór i trianguluj części.
        from shapely.geometry import LineString
        from shapely.ops import split
        hx = Polygon(holes[0]).representative_point().x
        miny, maxy = poly.bounds[1] - 1.0, poly.bounds[3] + 1.0
        try:
            parts = split(poly, LineString([(hx, miny), (hx, maxy)]))
            res = []
            for g in parts.geoms:
                if isinstance(g, Polygon):
                    res.extend(triangulate_polygon(g))
            return res
        except Exception:
            return []
    return _earclip(ext)


# ===========================================================================
# 5. Interpolacja Z i cięcie nożowe (Drape)
# ===========================================================================

def plane_z(x: float, y: float, tri: Tri) -> float:
    (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = tri
    ux, uy, uz = x1 - x0, y1 - y0, z1 - z0
    vx, vy, vz = x2 - x0, y2 - y0, z2 - z0
    a = uy * vz - uz * vy
    b = uz * vx - ux * vz
    c = ux * vy - uy * vx
    if abs(c) < 1e-12:
        return (z0 + z1 + z2) / 3.0
    return z0 - (a * (x - x0) + b * (y - y0)) / c


def ccw(tri: Tri) -> Tri:
    if _area2([p[:2] for p in tri]) < 0:
        return [tri[0], tri[2], tri[1]]
    return tri


def knife_cut(tris: Sequence[Tri], attrs: Sequence[dict], lines2d: Sequence[Sequence[Pt2]]):
    """Rozcina trójkąty terenu liniami 2D. Zwraca (trójkąty, atrybuty).

    Dla każdego trójkąta przecinanego liniami: noding brzegu + linii,
    polygonize → kawałki → earcut. Wierzchołki na liniach mają Z z płaszczyzny
    trójkąta macierzystego, więc sąsiedzi dzielą identyczne punkty (szczelność).
    """
    from shapely.geometry import LineString, Polygon
    from shapely.ops import polygonize, unary_union
    from shapely.prepared import prep

    lines = [LineString(l) for l in lines2d if len(l) >= 2]
    if not lines:
        return list(tris), list(attrs)
    cutter = unary_union(lines)
    pcut = prep(cutter)
    out_t: list[Tri] = []
    out_a: list[dict] = []
    for tri, at in zip(tris, attrs):
        tp = Polygon([p[:2] for p in tri])
        if tp.area < 1e-12 or not pcut.intersects(tp):
            out_t.append(tri)
            out_a.append(at)
            continue
        inside = tp.buffer(1e-5, 1, join_style=2).intersection(cutter)
        if inside.is_empty or tp.intersection(cutter).length < 1e-9:
            out_t.append(tri)
            out_a.append(at)
            continue
        pieces = [p for p in polygonize(unary_union([tp.exterior, inside]))
                  if p.area > 1e-12 and tp.contains(p.representative_point())]
        if not pieces or abs(sum(p.area for p in pieces) - tp.area) > max(1e-4, 1e-4 * tp.area):
            out_t.append(tri)
            out_a.append(at)
            continue
        for pc in pieces:
            for a, b, c in triangulate_polygon(pc):
                t = [(a[0], a[1], plane_z(a[0], a[1], tri)),
                     (b[0], b[1], plane_z(b[0], b[1], tri)),
                     (c[0], c[1], plane_z(c[0], c[1], tri))]
                out_t.append(ccw(t))
                out_a.append(at)
    return out_t, out_a


def ring_lines(poly) -> list[list[Pt2]]:
    """Linie brzegowe (zewnętrzne + otwory) wielokąta shapely jako listy punktów."""
    geoms = getattr(poly, "geoms", [poly])
    res = []
    for g in geoms:
        if g.is_empty:
            continue
        res.append([tuple(c) for c in g.exterior.coords])
        res.extend([tuple(c) for c in r.coords] for r in g.interiors)
    return res


# ===========================================================================
# 6. Odczyt i przebudowa siatki terenu w miejscu
# ===========================================================================

def read_terrain(mesh: Any) -> tuple[list[Tri], list[dict], list[tuple[Pt2, Pt2]]]:
    """Extracts local triangles, their attributes, and existing HARD inner edges."""
    tris: list[Tri] = []
    attrs: list[dict] = []
    for f in getattr(mesh, "faces", []):
        a = dict(getattr(f, "attrs", {}) or {})
        raw_loop = getattr(f, "loop", None)
        if raw_loop is not None:
            loop = [t3(getattr(v, "position", v)) for v in raw_loop]
        elif hasattr(f, "vertices"):
            loop = [t3(v) for v in f.vertices]
        else:
            continue

        if len(loop) == 3 and not getattr(f, "hole_loops", None):
            tris.append(ccw(loop))
            attrs.append(a)
            continue
        try:
            for p0, p1, p2 in f.triangulate():
                tris.append(ccw([t3(p0), t3(p1), t3(p2)]))
                attrs.append(a)
        except Exception:
            for i in range(1, len(loop) - 1):
                tris.append(ccw([loop[0], loop[i], loop[i + 1]]))
                attrs.append(a)
    hard = []
    for e in getattr(mesh, "edges", []):
        if not getattr(e, "soft", False) and len(getattr(e, "faces", [])) >= 2:
            v0 = getattr(e, "v0", None)
            v1 = getattr(e, "v1", None)
            if v0 is not None and v1 is not None:
                hard.append((t3(getattr(v0, "position", v0))[:2], t3(getattr(v1, "position", v1))[:2]))
    return tris, attrs, hard


def rebuild_terrain_mesh(mesh: Any, tris: Sequence[Tri], attrs: Sequence[dict],
                         hard_segments: Sequence[tuple[Pt2, Pt2]] = (),
                         all_hard: bool = False) -> None:
    """Clears the mesh and rebuilds it in-place within the same Mesh object (preserving Undo/Redo).

    Edges along ``hard_segments`` are marked hard (visible); outer terrain boundary is hard;
    interior edges are soft (hidden) unless all_hard is True.
    """
    if hasattr(mesh, "clear") and callable(mesh.clear):
        mesh.clear()
    else:
        for f in list(getattr(mesh, "faces", [])):
            if hasattr(mesh, "remove_face"):
                mesh.remove_face(f)
        if hasattr(mesh, "faces"):
            mesh.faces.clear()
        if hasattr(mesh, "edges"):
            mesh.edges.clear()
        if hasattr(mesh, "vertices"):
            mesh.vertices.clear()

    for tri, at in zip(tris, attrs):
        f = mesh.add_face([QVector3D(*p) for p in tri])
        if f is not None:
            f.attrs = dict(at)

    tree = None
    geoms = []
    try:
        from shapely.geometry import LineString, Point
        from shapely.strtree import STRtree
        geoms = [LineString([a, b]) for a, b in hard_segments if math.dist(a, b) > 1e-9]
        if geoms:
            tree = STRtree(geoms)
    except Exception:
        tree = None

    for e in getattr(mesh, "edges", []):
        boundary = len(getattr(e, "faces", [])) < 2
        hard = boundary or all_hard
        if not hard and tree is not None:
            try:
                from shapely.geometry import Point
                v0_pos = getattr(e.v0, "position", e.v0)
                v1_pos = getattr(e.v1, "position", e.v1)
                a = t3(v0_pos)[:2]
                b = t3(v1_pos)[:2]
                m = Point((a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5)
                for i in tree.query(m.buffer(HARD_TOL)):
                    g = geoms[int(i)] if not hasattr(i, "geom_type") else i
                    if (g.distance(Point(a)) < HARD_TOL and g.distance(Point(b)) < HARD_TOL
                            and g.distance(m) < HARD_TOL):
                        hard = True
                        break
            except Exception:
                pass
        e.soft = not hard
        e.hidden = False
    mesh._chunk_dirty = True
    if hasattr(mesh, "version"):
        mesh.version += 1


# ===========================================================================
# 7. Wagi wierzchołków: Smoove i Stamp
# ===========================================================================

def smoove_falloff(t: float) -> float:
    """Profil SketchUp Smoove: kosinusowy (1 w środku, 0 na brzegu, gładki)."""
    if t >= 1.0:
        return 0.0
    if t <= 0.0:
        return 1.0
    return 0.5 * (1.0 + math.cos(math.pi * t))


FALLOFFS = {
    "cosine": smoove_falloff,
    "linear": lambda t: max(0.0, 1.0 - t),
    "smoothstep": lambda t: 0.0 if t >= 1 else 1.0 - (3 * t * t - 2 * t * t * t),
    "gaussian": lambda t: 0.0 if t >= 1 else math.exp(-4.0 * t * t) * (1 - t),
}


def smoove_weights(mesh: Any, center_local: QVector3D, radius: float,
                   profile: str = "cosine", only: set | None = None):
    """{Vertex: (oryginalna_pozycja, waga)} dla wierzchołków w zasięgu pędzla (2D)."""
    fn = FALLOFFS.get(profile, smoove_falloff)
    cx, cy = center_local.x(), center_local.y()
    res = {}
    for v in getattr(mesh, "vertices", []):
        if only is not None and v not in only:
            continue
        p = v.position
        d = math.hypot(p.x() - cx, p.y() - cy)
        if d < radius:
            w = fn(d / radius)
            if w > 1e-6:
                res[v] = (QVector3D(p), w)
    return res


def apply_dz(mesh: Any, weights: dict, dz: float) -> None:
    for v, (p0, w) in weights.items():
        mesh.place_vertex(v, QVector3D(p0.x(), p0.y(), p0.z() + dz * w))


def stamp_weights(mesh: Any, pad_local, offset: float):
    """{Vertex: (oryg_pozycja, waga)}: 1 w obrysie, liniowe opadanie do 0 na offsecie."""
    from shapely.geometry import Point
    from shapely.prepared import prep
    pp = prep(pad_local.buffer(1e-4))
    bnd = pad_local.exterior
    res = {}
    for v in getattr(mesh, "vertices", []):
        p = v.position
        pt = Point(p.x(), p.y())
        if pp.contains(pt):
            res[v] = (QVector3D(p), 1.0)
            continue
        if offset > 1e-4:
            d = bnd.distance(pt)
            if d < offset + 1e-4:
                t = min(1.0, max(0.0, d / offset))
                res[v] = (QVector3D(p), 1.0 - t)
    return res


def apply_pad(mesh: Any, weights: dict, pad_z: float) -> None:
    for v, (p0, w) in weights.items():
        z = p0.z() + (pad_z - p0.z()) * w
        mesh.place_vertex(v, QVector3D(p0.x(), p0.y(), z))


def earthwork(mesh: Any, before_pos: dict) -> tuple[float, float]:
    """(wykop, nasyp) w m³ z przesunięć wierzchołków (pryzmy trójkątów)."""
    cut = fill = 0.0
    for f in getattr(mesh, "faces", []):
        loop = f.loop
        if len(loop) < 3:
            continue
        dzs = [v.position.z() - before_pos[v].z() if v in before_pos else 0.0 for v in loop]
        if not any(abs(d) > 1e-6 for d in dzs):
            continue
        pts = [(v.position.x(), v.position.y()) for v in loop]
        area = abs(_area2(pts))
        dz = sum(dzs) / len(dzs)
        if dz > 0:
            fill += area * dz
        else:
            cut -= area * dz
    return cut, fill


def local_polygon(group: Any, poly_world):
    """Przenosi shapely Polygon ze świata do układu lokalnego grupy (rzut XY)."""
    from shapely.geometry import Polygon
    x = _xform(group)
    if x is None:
        return poly_world
    def m(c):
        q = to_local(group, QVector3D(c[0], c[1], 0.0))
        return (q.x(), q.y())
    return Polygon([m(c) for c in poly_world.exterior.coords],
                   [[m(c) for c in r.coords] for r in poly_world.interiors])


# ===========================================================================
# 8. Operacje wysokiego poziomu: Drape i Stamp
# ===========================================================================

def _segments_local(group, segs_world):
    out = []
    for a, b in segs_world:
        la = to_local(group, QVector3D(*a))
        lb = to_local(group, QVector3D(*b))
        out.append(((la.x(), la.y()), (lb.x(), lb.y())))
    return out


def drape_plan(segs_local, road_width: float = 0.0):
    """(linie_cięcia, twarde_odcinki, obszary_do_malowania) dla Drape."""
    from shapely.geometry import LineString
    from shapely.ops import polygonize, unary_union
    if road_width > 1e-6:
        merged = unary_union([LineString([a, b]) for a, b in segs_local])
        band = merged.buffer(road_width * 0.5, cap_style=2, join_style=2, mitre_limit=3.0)
        cut = ring_lines(band)
        hard = [(l[i], l[i + 1]) for l in cut for i in range(len(l) - 1)]
        return cut, hard, band
    cut = [[a, b] for a, b in segs_local]
    lines = unary_union([LineString([a, b]) for a, b in segs_local])
    regions = [p for p in polygonize(lines) if p.area > 1e-6]
    region = unary_union(regions) if regions else None
    return cut, list(segs_local), region


def drape_onto_terrain(viewport, terrain, segs_world, road_width: float = 0.0,
                       paint_attrs: dict | None = None) -> int:
    """SketchUp Drape: linie rzutowane pionowo stają się twardymi krawędziami terenu.

    Zamknięte obrysy (np. działka) tworzą obszar, który można pomalować wiadrem
    (otoczony twardymi krawędziami); z ``paint_attrs`` jest malowany od razu.
    Zwraca liczbę ścianek terenu po operacji.
    """
    from shapely.prepared import prep
    from shapely.geometry import Point
    mesh = terrain.mesh
    segs = _segments_local(terrain, segs_world)
    if not segs:
        raise ValueError("Brak linii do rzutowania.")
    cut, hard_new, region = drape_plan(segs, road_width)
    preg = prep(region.buffer(1e-7)) if (region is not None and paint_attrs) else None
    before = mesh.capture_state()

    def mutate(m):
        tris, attrs, _h = read_terrain(m)
        hard_old = _stored_hard(terrain)
        nt, na = knife_cut(tris, attrs, cut)
        if preg is not None:
            for i, t in enumerate(nt):
                cx = (t[0][0] + t[1][0] + t[2][0]) / 3.0
                cy = (t[0][1] + t[1][1] + t[2][1]) / 3.0
                if preg.contains(Point(cx, cy)):
                    a = dict(na[i])
                    a.update(paint_attrs)
                    na[i] = a
        allh = list(hard_old) + list(hard_new)
        _store_hard(terrain, allh)
        rebuild_terrain_mesh(m, nt, na, allh)

    execute_terrain_edit(viewport, mesh, before, mutate=mutate)
    return len(mesh.faces)


def stamp_cut(terrain, pad_local, offset: float, pad_attrs: dict | None = None,
              slope_attrs: dict | None = None, slope_steps: int = 1) -> None:
    """Wcina obrys półki i zewnętrzną krawędź skarpy w siatkę terenu.

    offset: szerokość skarpy (m).
    slope_steps: 1 = pojedyncza, czysta skarpa inżynierska bez sztucznych pasm/chodników.
    pad_attrs: atrybuty/materiał półki (obrys odciśnięty).
    slope_attrs: atrybuty/materiał samej skarpy.
    """
    from shapely.prepared import prep
    from shapely.geometry import Point
    mesh = terrain.mesh
    rings = [pad_local]
    outer_pad = None
    if offset > 1e-4:
        outer_pad = pad_local.buffer(offset, 4, join_style=1)
        rings.append(outer_pad)

    cut = []
    for r in rings:
        cut.extend(ring_lines(r))

    hard_new = [(l[i], l[i + 1]) for l in ring_lines(pad_local) for i in range(len(l) - 1)]
    if outer_pad is not None:
        hard_new.extend([(l[i], l[i + 1]) for l in ring_lines(outer_pad) for i in range(len(l) - 1)])

    ppad = prep(pad_local.buffer(1e-4))
    pouter = prep(outer_pad.buffer(1e-4)) if outer_pad is not None else None

    tris, attrs, _h = read_terrain(mesh)
    hard_old = _stored_hard(terrain)
    nt, na = knife_cut(tris, attrs, cut)

    for i, t in enumerate(nt):
        cx = (t[0][0] + t[1][0] + t[2][0]) / 3.0
        cy = (t[0][1] + t[1][1] + t[2][1]) / 3.0
        pt = Point(cx, cy)
        if pad_attrs and ppad.contains(pt):
            a = dict(na[i])
            a.update(pad_attrs)
            na[i] = a
        elif slope_attrs and pouter is not None and pouter.contains(pt):
            a = dict(na[i])
            a.update(slope_attrs)
            na[i] = a

    allh = list(hard_old) + hard_new
    _store_hard(terrain, allh)
    rebuild_terrain_mesh(mesh, nt, na, allh)


def stamp_terrain(viewport, terrain, footprint_world, footprint_z: float,
                  offset: float, pad_z: float | None = None,
                  pad_attrs: dict | None = None,
                  slope_attrs: dict | None = None) -> tuple[float, float]:
    """Stamp jednym wywołaniem (panel boczny). Zwraca (wykop, nasyp) w m³."""
    from .geometry import point_z_on_triangle
    mesh = terrain.mesh
    pad_local = local_polygon(terrain, footprint_world)

    if pad_z is None:
        # Automatyczna rzędna: średnia wysokość terenu pod obrysem
        tris, _, _ = read_terrain(mesh)
        elevs = []
        for pt in pad_local.exterior.coords:
            for tri in tris:
                z = point_z_on_triangle(pt[0], pt[1], tri)
                if z is not None:
                    elevs.append(z)
                    break
        if elevs:
            z_local = sum(elevs) / len(elevs)
        else:
            z_local = to_local(terrain, QVector3D(0, 0, footprint_z)).z()
    else:
        z_local = to_local(terrain, QVector3D(0, 0, pad_z)).z()

    before = mesh.capture_state()
    cut_fill = [0.0, 0.0]

    def mutate(m):
        stamp_cut(terrain, pad_local, offset, pad_attrs=pad_attrs,
                  slope_attrs=slope_attrs, slope_steps=1)
        weights = stamp_weights(m, pad_local, offset)
        orig = {v: p for v, (p, _w) in weights.items()}
        apply_pad(m, weights, z_local)
        c, f = earthwork(m, orig)
        cut_fill[0] = c
        cut_fill[1] = f

    execute_terrain_edit(viewport, mesh, before, mutate=mutate)
    return cut_fill[0], cut_fill[1]


def _stored_hard(group) -> list:
    """Twarde linie (Drape/Stamp) zapamiętane w group.ext – reszta siatki jest miękka."""
    try:
        d = group.ext.get(PLUGIN_KEY, {}) if isinstance(group.ext, dict) else {}
        return [(tuple(a), tuple(b)) for a, b in d.get("hard_lines", [])]
    except Exception:
        return []


def _store_hard(group, segs) -> None:
    try:
        if getattr(group, "ext", None) is None:
            group.ext = {}
        group.ext.setdefault(PLUGIN_KEY, {})["hard_lines"] = [
            [list(map(float, a)), list(map(float, b))] for a, b in segs]
    except Exception:
        pass
