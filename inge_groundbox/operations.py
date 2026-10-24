# SPDX-License-Identifier: GPL-3.0-or-later
"""
inge_groundbox/operations.py
==========================
Warstwa transakcyjna (History & Scene) dla wtyczki GroundBox w IngeTrazo.
Wszystkie operacje modyfikujące model są przeprowadzane przez SnapshotImport / SnapshotMutation,
z poprawną obsługą obiektów QVector3D, Mesh i Group.
"""
from __future__ import annotations

import copy
import logging
import math
from typing import Any, Sequence

from .constants import (
    COLOR_GRASS_BACK,
    COLOR_GRASS_FRONT,
    COLOR_PAD_BACK,
    COLOR_PAD_FRONT,
    COLOR_ROAD_BACK,
    COLOR_ROAD_FRONT,
    COLOR_ROCK_BACK,
    COLOR_ROCK_FRONT,
    COLOR_SAND_BACK,
    COLOR_SAND_FRONT,
    COLOR_SLOPE_BACK,
    COLOR_SLOPE_FRONT,
    COLOR_SOIL_BACK,
    COLOR_SOIL_FRONT,
    IFC_CLASS_ROAD,
    IFC_CLASS_SITE,
    PLUGIN_KEY,
)
from .geometry import (
    Point3D,
    Triangle,
    calculate_slope_distribution,
    calculate_triangle_slope,
    drape_path_onto_terrain,
    generate_terrain_skirt,
    slope_to_color,
)
from .terrain_mesh import (
    build_drape_geometry,
    build_stamp_geometry,
    build_terrain_from_contours,
    flip_mesh_edge,
    generate_flat_grid,
    subdivide_triangles_midpoint,
)

log = logging.getLogger(f"ingetrazo.plugins.{PLUGIN_KEY}")

# ---------------------------------------------------------------------------
# Importy Qt (QVector3D, QMatrix4x4)
# ---------------------------------------------------------------------------
try:
    from PySide6.QtGui import QMatrix4x4, QVector3D
except ImportError:
    try:
        from PyQt5.QtGui import QMatrix4x4, QVector3D
    except ImportError:
        class QVector3D:  # type: ignore
            def __init__(self, x=0.0, y=0.0, z=0.0):
                if isinstance(x, QVector3D):
                    self._x, self._y, self._z = x._x, x._y, x._z
                elif isinstance(x, (tuple, list)) and len(x) >= 3:
                    self._x, self._y, self._z = float(x[0]), float(x[1]), float(x[2])
                else:
                    self._x, self._y, self._z = float(x), float(y), float(z)
            def x(self): return self._x
            def y(self): return self._y
            def z(self): return self._z
            def setX(self, x): self._x = float(x)
            def setY(self, y): self._y = float(y)
            def setZ(self, z): self._z = float(z)

        class QMatrix4x4:  # type: ignore
            def map(self, q): return q
            def inverted(self): return self, True

# ---------------------------------------------------------------------------
# Importy jądra IngeTrazo
# ---------------------------------------------------------------------------
try:
    from core.group import Group
    from core.history import SnapshotImport
    from core.mesh import Edge, Face, Mesh
except ImportError:
    try:
        import model
        Group = getattr(model, "Group", None)
        Mesh = getattr(model, "Mesh", None)
        SnapshotImport = lambda fn: fn
        if Group is None or Mesh is None:
            raise ImportError("model classes not found")
    except ImportError:
        class MockVertex:
            def __init__(self, pos):
                self.position = pos

        class Mesh:  # type: ignore
            def __init__(self):
                self.faces = []
                self.edges = []
                self.vertices = []
            def clear(self):
                self.faces.clear()
                self.edges.clear()
                self.vertices.clear()
            def capture_state(self):
                return {"faces": list(self.faces), "edges": list(self.edges)}
            def restore_state(self, state):
                self.faces = list(state.get("faces", []))
                self.edges = list(state.get("edges", []))
            def place_vertex(self, v, qv):
                v.position = qv
            def add_face(self, loop):
                f = Face(loop)
                self.faces.append(f)
                return f
            def add_edge(self, p1, p2):
                e = Edge(p1, p2)
                self.edges.append(e)
                return e

        class Face:  # type: ignore
            def __init__(self, verts):
                self.vertices = verts
                self.loop = [MockVertex(p) for p in verts]
                self.attrs = {}

        class Edge:  # type: ignore
            def __init__(self, p1, p2):
                self.v0 = MockVertex(p1)
                self.v1 = MockVertex(p2)
                self.vertices = [p1, p2]
                self.soft = False

        class Group:  # type: ignore
            def __init__(self, mesh=None, name=""):
                self.mesh = mesh or Mesh()
                self.name = name
                self.children = []
                self.xform = QMatrix4x4()
                self.ext = {}
                self.ifc = {}
            def adopt(self, children):
                self.children.extend(children)

        SnapshotImport = lambda fn: fn


# ===========================================================================
# 1. Konwertery punktów (QVector3D <-> tuple)
# ===========================================================================

def to_qvector3d(pt: Any) -> QVector3D:
    """Konwertuje punkt (krotkę, listę, Vertex, QVector3D) na obiekt QVector3D wymagany przez IngeTrazo Mesh."""
    if isinstance(pt, QVector3D):
        return pt
    if hasattr(pt, "position"):
        pos = pt.position
        if isinstance(pos, QVector3D):
            return pos
        pt = pos
    if hasattr(pt, "x"):
        if callable(pt.x):
            return QVector3D(float(pt.x()), float(pt.y()), float(pt.z()))
        return QVector3D(float(pt.x), float(pt.y), float(pt.z))
    return QVector3D(float(pt[0]), float(pt[1]), float(pt[2]))


def to_point3d(pt: Any) -> Point3D:
    """Konwertuje obiekt punktu na czystą krotkę (float, float, float)."""
    if hasattr(pt, "position"):
        pt = pt.position
    if hasattr(pt, "x"):
        if callable(pt.x):
            return (float(pt.x()), float(pt.y()), float(pt.z()))
        return (float(pt.x), float(pt.y), float(pt.z))
    return (float(pt[0]), float(pt[1]), float(pt[2]))


def set_vertex_coord(v: Any, x: float, y: float, z: float) -> None:
    """Ustawia współrzędne wierzchołka w obiekcie Vertex IngeTrazo."""
    if hasattr(v, "position"):
        pos = v.position
        if hasattr(pos, "setX"):
            pos.setX(float(x))
            pos.setY(float(y))
            pos.setZ(float(z))
        else:
            v.position = QVector3D(float(x), float(y), float(z))
    else:
        try:
            v.x = float(x)
            v.y = float(y)
            v.z = float(z)
        except Exception:
            pass


# ===========================================================================
# 2. Rozpoznawanie Viewportu i Sceny
# ===========================================================================

def resolve_viewport(app: Any) -> Any:
    """Niezawodnie odnajduje obiekt Viewport z aplikacji IngeTrazo."""
    for attr in ("viewport", "view", "_viewport", "_view"):
        vp = getattr(app, attr, None)
        if vp is not None:
            return vp

    win = getattr(app, "window", None) or getattr(app, "main_window", None)
    if win is not None:
        for attr in ("viewport", "view", "_viewport", "_view"):
            vp = getattr(win, attr, None)
            if vp is not None:
                return vp
        for meth in ("get_viewport", "active_viewport"):
            if hasattr(win, meth) and callable(getattr(win, meth)):
                try:
                    vp = getattr(win, meth)()
                    if vp is not None:
                        return vp
                except Exception:
                    pass
    return None


def resolve_scene(app: Any, viewport: Any = None) -> Any:
    """Zwraca obiekt Scene z aplikacji lub widoku."""
    if hasattr(app, "scene") and app.scene is not None:
        return app.scene
    vp = viewport or resolve_viewport(app)
    if vp is not None and hasattr(vp, "scene") and vp.scene is not None:
        return vp.scene
    return None


# ===========================================================================
# 3. Fabryka grup i dodawanie do sceny
# ===========================================================================

def build_terrain_group_from_triangles(
    triangles: list[Triangle],
    name: str = "Terrain (GroundBox)",
    material_name: str = "Natural Grass",
    soft_edges: bool = True,
) -> Any:
    """Builds a valid Group object with Mesh() and faces from QVector3D loops."""
    mesh = Mesh()
    attrs = _get_material_attrs(material_name)

    for tri in triangles:
        # ALWAYS QVector3D list for IngeTrazo C++ engine
        loop = [to_qvector3d(p) for p in tri]
        f = mesh.add_face(loop)
        if f is not None and hasattr(f, "attrs"):
            f.attrs = {
                "color": list(attrs["color"]),
                "back_color": list(attrs["back_color"]),
                "mat": material_name,
            }

    if soft_edges and hasattr(mesh, "edges"):
        for e in mesh.edges:
            setattr(e, "soft", True)

    group = Group(mesh=mesh, name=name)
    group.component = False
    group.xform = QMatrix4x4()
    group.ext = {}
    group.ifc = {}
    return group


def commit_group_to_scene(app: Any, group: Any, select: bool = True) -> None:
    """Adds a group to the scene using the History system (Undo/Redo via SnapshotImport)."""
    vp = resolve_viewport(app)
    scene = resolve_scene(app, vp)

    if vp is None or scene is None:
        raise RuntimeError("Error: Active viewport or scene not found in IngeTrazo.")

    def mutate(sc: Any):
        sc.groups.append(group)
        if select and hasattr(sc, "selection") and sc.selection is not None:
            try:
                sc.selection.clear()
                if hasattr(sc.selection, "add"):
                    sc.selection.add(group)
                elif hasattr(sc.selection, "append"):
                    sc.selection.append(group)
            except Exception:
                pass
        if hasattr(sc, "version"):
            sc.version += 1

    # Wykonaj przez historię
    if hasattr(vp, "history") and vp.history is not None:
        vp.history.execute(SnapshotImport(mutate))
    else:
        mutate(scene)

    if hasattr(vp, "notify_scene_changed") and callable(vp.notify_scene_changed):
        vp.notify_scene_changed()
    if hasattr(vp, "update") and callable(vp.update):
        vp.update()


# ===========================================================================
# 4. Wyciąganie geometrii ze sceny
# ===========================================================================

def extract_triangles_from_group(group: Any) -> list[Triangle]:
    """Wyciąga wszystkie trójkąty z siatki grupy."""
    triangles: list[Triangle] = []
    mesh = getattr(group, "mesh", None)
    if mesh is None:
        return triangles

    for face in getattr(mesh, "faces", []):
        try:
            verts = [to_point3d(v) for v in getattr(face, "vertices", [])]
            if len(verts) == 3:
                triangles.append(verts)
            elif len(verts) == 4:
                triangles.append([verts[0], verts[1], verts[2]])
                triangles.append([verts[0], verts[2], verts[3]])
            elif len(verts) > 4:
                for i in range(1, len(verts) - 1):
                    triangles.append([verts[0], verts[i], verts[i + 1]])
        except Exception:
            continue
    return triangles


def find_terrain_group(scene: Any, selection: Sequence[Any]) -> Any | None:
    """Wyszukuje grupę terenu w selekcji lub w scenie."""
    candidates = list(selection) if selection else []
    if scene is not None:
        candidates.extend(getattr(scene, "groups", []))

    # 1. Sprawdź metadane pluginu
    for obj in candidates:
        try:
            ext = getattr(obj, "ext", None) or {}
            if PLUGIN_KEY in ext:
                if ext[PLUGIN_KEY].get("type") == "Terrain":
                    return obj
        except Exception:
            continue

    # 2. Sprawdź nazwę
    for obj in candidates:
        name = getattr(obj, "name", "").lower()
        if "teren" in name or "terrain" in name or "groundbox" in name or "sandbox" in name:
            return obj

    # 3. Zaznaczona grupa z siatką
    for obj in (selection or []):
        mesh = getattr(obj, "mesh", None)
        if mesh is not None and len(getattr(mesh, "faces", [])) >= 2:
            return obj

    return None


def _extract_pt_from_node(v: Any, xform: Any = None) -> Point3D | None:
    if hasattr(v, "position"):
        pos = v.position
    else:
        pos = v
    if hasattr(pos, "x"):
        if callable(pos.x):
            pt = (float(pos.x()), float(pos.y()), float(pos.z()))
        else:
            pt = (float(pos.x), float(pos.y), float(pos.z))
    elif isinstance(pos, (tuple, list)) and len(pos) >= 3:
        pt = (float(pos[0]), float(pos[1]), float(pos[2]))
    else:
        return None

    if xform is not None and hasattr(xform, "map"):
        try:
            q = to_qvector3d(pt)
            mapped = xform.map(q)
            return (float(mapped.x()), float(mapped.y()), float(mapped.z()))
        except Exception:
            pass
    return pt


def extract_contour_curves(selection: Sequence[Any]) -> list[list[Point3D]]:
    """
    Wyciąga uporządkowane polilinie z zaznaczonych krawędzi (Edges), ścianek (Faces) lub grup,
    oraz punkty wysokościowe i pionowe tyczki geodezyjne (survey stakes) w GroundBox.
    W pionowych kreskach najwyższy punkt (max Z) jest traktowany jako rzędna terenu.
    """
    edges_list: list[tuple[Point3D, Point3D]] = []
    spot_points: list[Point3D] = []

    def _add_segment(p0: Point3D | None, p1: Point3D | None) -> None:
        if not p0 or not p1:
            return
        d_xy = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        d_z = abs(p1[2] - p0[2])
        # Pionowa kreska (tyczka geodezyjna / survey stake)
        if d_xy < 1e-3 and d_z > 1e-4:
            top_z = max(p0[2], p1[2])
            spot_points.append(((p0[0] + p1[0]) * 0.5, (p0[1] + p1[1]) * 0.5, top_z))
        elif _dist(p0, p1) > 1e-5:
            edges_list.append((p0, p1))

    def _process_obj(obj: Any, parent_xform: Any = None) -> None:
        if obj is None:
            return

        # 0. Samodzielny punkt / wierzchołek geodezyjny (np. CPoint, GuidePoint, Vertex bez krawędzi)
        if hasattr(obj, "position") and not hasattr(obj, "v0") and not hasattr(obj, "vertices"):
            pt = _extract_pt_from_node(obj, parent_xform)
            if pt:
                spot_points.append(pt)
            return

        # Krotka / lista 3D bezpośrednio
        if isinstance(obj, (tuple, list)) and len(obj) == 3 and all(isinstance(c, (int, float)) for c in obj):
            spot_points.append((float(obj[0]), float(obj[1]), float(obj[2])))
            return

        # 1. Krawędź Edge w IngeTrazo (posiada v0 i v1)
        if hasattr(obj, "v0") and hasattr(obj, "v1"):
            p0 = _extract_pt_from_node(obj.v0, parent_xform)
            p1 = _extract_pt_from_node(obj.v1, parent_xform)
            _add_segment(p0, p1)
            return

        # 2. Odcinek ze start i end
        if hasattr(obj, "start") and hasattr(obj, "end"):
            p0 = _extract_pt_from_node(obj.start, parent_xform)
            p1 = _extract_pt_from_node(obj.end, parent_xform)
            _add_segment(p0, p1)
            return

        # 3. Krawędzie z dwoma wierzchołkami w obj.vertices
        if hasattr(obj, "vertices") and not hasattr(obj, "faces") and len(obj.vertices) == 2:
            p0 = _extract_pt_from_node(obj.vertices[0], parent_xform)
            p1 = _extract_pt_from_node(obj.vertices[1], parent_xform)
            _add_segment(p0, p1)
            return

        # 4. Obiekt Face (obwód ścianki)
        if hasattr(obj, "vertices") and len(obj.vertices) >= 3:
            v_pts = [_extract_pt_from_node(v, parent_xform) for v in obj.vertices]
            v_pts = [p for p in v_pts if p is not None]
            if len(v_pts) >= 3:
                for i in range(len(v_pts)):
                    _add_segment(v_pts[i], v_pts[(i + 1) % len(v_pts)])
            return

        # 5. Obiekt Group (kontener siatki CAD)
        if hasattr(obj, "mesh") and obj.mesh is not None:
            xform = getattr(obj, "xform", None) or parent_xform
            mesh = obj.mesh
            for e in getattr(mesh, "edges", []):
                _process_obj(e, xform)
            for f in getattr(mesh, "faces", []):
                _process_obj(f, xform)
            if not getattr(mesh, "edges", None) and not getattr(mesh, "faces", None):
                for v in getattr(mesh, "vertices", []):
                    _process_obj(v, xform)
            for child in getattr(obj, "children", []):
                _process_obj(child, xform)
            return

    for item in (selection or []):
        _process_obj(item)

    # Łączenie w ciągłe polilinie z tolerancją 5 cm (pozwala na łączenie importów DXF)
    curves: list[list[Point3D]] = []
    pool = list(edges_list)
    tol = 0.05

    while pool:
        p0, p1 = pool.pop(0)
        chain = [p0, p1]

        extended = True
        while extended:
            extended = False
            head = chain[0]
            tail = chain[-1]

            if len(chain) >= 3 and _dist(head, tail) < tol:
                break

            for idx, (q0, q1) in enumerate(pool):
                if _dist(tail, q0) < tol:
                    chain.append(q1)
                    pool.pop(idx)
                    extended = True
                    break
                elif _dist(tail, q1) < tol:
                    chain.append(q0)
                    pool.pop(idx)
                    extended = True
                    break
                elif _dist(head, q1) < tol:
                    chain.insert(0, q0)
                    pool.pop(idx)
                    extended = True
                    break
                elif _dist(head, q0) < tol:
                    chain.insert(0, q1)
                    pool.pop(idx)
                    extended = True
                    break

        if len(chain) >= 2:
            curves.append(chain)

    # Dodaj punkty wysokościowe i wierzchołki tyczek geodezyjnych jako elementy 1-punktowe
    for pt in spot_points:
        curves.append([pt])

    return curves


def _dist(p1: Point3D, p2: Point3D) -> float:
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2)



# ===========================================================================
# 5. Narzędzia Materiałów i BIM
# ===========================================================================

def _get_material_attrs(material_name: str) -> dict[str, Any]:
    mat_lower = material_name.lower()
    if "soil" in mat_lower or "ziemia" in mat_lower:
        front, back = COLOR_SOIL_FRONT, COLOR_SOIL_BACK
    elif "sand" in mat_lower or "piasek" in mat_lower:
        front, back = COLOR_SAND_FRONT, COLOR_SAND_BACK
    elif "rock" in mat_lower or "skała" in mat_lower:
        front, back = COLOR_ROCK_FRONT, COLOR_ROCK_BACK
    elif "road" in mat_lower or "asfalt" in mat_lower:
        front, back = COLOR_ROAD_FRONT, COLOR_ROAD_BACK
    else:
        front, back = COLOR_GRASS_FRONT, COLOR_GRASS_BACK

    return {
        "color": list(front[:3]),
        "back_color": list(back[:3]),
        "mat": material_name,
    }


def _tag_bim(group: Any, ifc_class: str, name: str) -> None:
    try:
        if getattr(group, "ifc", None) is None:
            group.ifc = {}
        group.ifc["class"] = ifc_class
        group.ifc["name"] = name
    except Exception:
        pass
    try:
        import core.bim as bim
        bim.tag_group(group, ifc_class)
    except Exception:
        pass


# ===========================================================================
# 6. Operacje Geometryczne (From Scratch, Contours, Smoove, Stamp itp.)
# ===========================================================================

def op_create_from_scratch(
    app: Any,
    size_x: float,
    size_y: float,
    spacing: float,
    base_z: float = 0.0,
    pattern: str = "alternating",
    material_name: str = "Natural Grass",
) -> Any:
    """Generates flat terrain grid and adds it to the scene."""
    triangles = generate_flat_grid(size_x, size_y, spacing, base_z, pattern)
    if not triangles:
        raise ValueError("No triangles generated for given dimensions.")

    created_group = build_terrain_group_from_triangles(
        triangles,
        name="Terrain (From Scratch)",
        material_name=material_name,
        soft_edges=False,
    )
    if getattr(created_group, "ext", None) is None:
        created_group.ext = {}
    created_group.ext[PLUGIN_KEY] = {
        "type": "Terrain",
        "origin": "FromScratch",
        "spacing": spacing,
        "size_x": size_x,
        "size_y": size_y,
    }
    _tag_bim(created_group, IFC_CLASS_SITE, "Terrain from Scratch (GroundBox)")
    commit_group_to_scene(app, created_group, select=True)
    return created_group


def op_create_from_contours(
    app: Any,
    selection: Sequence[Any],
    max_segment_len: float = 4.0,
    prune_boundary_ratio: float = 3.5,
    material_name: str = "Natural Grass",
    soft_edges: bool = True,
) -> Any:
    """Creates a continuous TIN terrain mesh from selected contour lines."""
    curves = extract_contour_curves(selection)
    if not curves:
        raise ValueError("No contour edges or polylines selected.")

    triangles = build_terrain_from_contours(curves, max_segment_len, prune_boundary_ratio)
    if not triangles:
        raise ValueError("Contour triangulation failed. Ensure points are not collinear.")

    created_group = build_terrain_group_from_triangles(
        triangles,
        name="Terrain from Contours",
        material_name=material_name,
        soft_edges=soft_edges,
    )
    if getattr(created_group, "ext", None) is None:
        created_group.ext = {}
    created_group.ext[PLUGIN_KEY] = {
        "type": "Terrain",
        "origin": "FromContours",
        "curves_count": len(curves),
    }
    _tag_bim(created_group, IFC_CLASS_SITE, "Terrain from Contours (GroundBox)")
    commit_group_to_scene(app, created_group, select=True)
    return created_group

def _terrain_rebuild(app: Any, terrain_group: Any, tris, attrs) -> None:
    """Rebuilds terrain mesh for an EXISTING group in the same Mesh object (Undo works)."""
    from . import groundbox_core as sc
    vp = resolve_viewport(app)
    mesh = terrain_group.mesh
    _old, _oa, hard = sc.read_terrain(mesh)

    # Detect if the terrain mesh originally had visible (hard) interior edges (e.g. From Scratch)
    orig_interior = [e for e in getattr(mesh, "edges", []) if len(getattr(e, "faces", [])) >= 2]
    all_hard = bool(orig_interior and not any(getattr(e, "soft", False) for e in orig_interior))

    before = mesh.capture_state()
    sc.execute_terrain_edit(vp, mesh, before,
                            mutate=lambda m: sc.rebuild_terrain_mesh(m, tris, attrs, hard, all_hard=all_hard))


def op_commit_smoove(app: Any, terrain_group: Any, new_vertices: Sequence[Point3D]) -> None:
    """Records new vertex positions as a single Undo step."""
    from . import groundbox_core as sc
    vp = resolve_viewport(app)
    mesh = terrain_group.mesh
    before = mesh.capture_state()

    def mutate(m):
        for v, p in zip(list(m.vertices), new_vertices):
            m.place_vertex(v, to_qvector3d(p))

    sc.execute_terrain_edit(vp, mesh, before, mutate=mutate)


def op_apply_smoove_numeric(app, terrain_group, center_pt, radius, delta_z, falloff="cosine") -> int:
    from . import groundbox_core as sc
    vp = resolve_viewport(app)
    mesh = terrain_group.mesh
    w = sc.smoove_weights(mesh, sc.to_local(terrain_group, to_qvector3d(center_pt)), radius, falloff)
    if not w:
        raise ValueError("No vertices within brush radius.")
    before = mesh.capture_state()
    sc.execute_terrain_edit(vp, mesh, before, mutate=lambda m: sc.apply_dz(m, w, delta_z))
    return len(w)


def op_apply_stamp(app, footprint_obj, terrain_group, offset_dist=2.0, target_elevation=None,
                   pad_material="Concrete / Paving", slope_material="Ground Slope"):
    """Stamp from panel: footprint from selection, pad at footprint elevation or specified elevation."""
    from . import groundbox_core as sc
    from .interactive import paint_attrs
    vp = resolve_viewport(app)
    objs = footprint_obj if isinstance(footprint_obj, (list, tuple)) else [footprint_obj]
    poly, fz = sc.collect_footprint(objs, exclude=terrain_group)
    if poly is None:
        raise ValueError("No footprint found to stamp.")
    cut, fill = sc.stamp_terrain(
        vp, terrain_group, poly, fz, offset_dist,
        pad_z=target_elevation,
        pad_attrs=paint_attrs(pad_material),
        slope_attrs=paint_attrs(slope_material),
    )
    return cut, fill, fill - cut


def op_apply_drape(app, path_edges, terrain_group, road_width=0.0, material_name=None,
                   paint: bool = False) -> int:
    from . import groundbox_core as sc
    from .interactive import paint_attrs
    vp = resolve_viewport(app)
    segs = sc.collect_world_segments(path_edges, exclude=terrain_group)
    if not segs:
        raise ValueError("No edges selected for drape.")
    attrs = paint_attrs(material_name) if (paint or road_width > 0) else None
    return sc.drape_onto_terrain(vp, terrain_group, segs, road_width, attrs)


def op_apply_add_detail_at_point(app: Any, terrain_group: Any, click_pt: Point3D) -> tuple[bool, int]:
    """Interactively subdivides the terrain triangle at click_pt with conforming neighbor bisection."""
    from . import groundbox_core as sc
    from .terrain_mesh import add_detail_at_point

    # Convert click_pt to local group coordinates
    pt_loc_qv = sc.to_local(terrain_group, to_qvector3d(click_pt))
    pt_loc = (float(pt_loc_qv.x()), float(pt_loc_qv.y()), float(pt_loc_qv.z()))

    tris, attrs, _h = sc.read_terrain(terrain_group.mesh)
    if not tris:
        return False, 0

    new_tris, new_attrs, ok = add_detail_at_point(tris, attrs, pt_loc, pick_radius=15.0, bisect_neighbors=True)
    if not ok:
        return False, 0

    _terrain_rebuild(app, terrain_group, new_tris, new_attrs)
    return True, len(new_tris)


def op_apply_add_detail(app: Any, terrain_group: Any) -> int:
    """Subdivides all triangles in the terrain mesh (1-to-4), preserving attributes and hard edges."""
    from . import groundbox_core as sc
    tris, attrs, _h = sc.read_terrain(terrain_group.mesh)
    if not tris:
        raise ValueError("No triangles found in terrain.")
    out_t, out_a = [], []
    for t, a in zip(tris, attrs):
        m01 = tuple((t[0][i] + t[1][i]) / 2 for i in range(3))
        m12 = tuple((t[1][i] + t[2][i]) / 2 for i in range(3))
        m20 = tuple((t[2][i] + t[0][i]) / 2 for i in range(3))
        for nt in ([t[0], m01, m20], [m01, t[1], m12], [m20, m12, t[2]], [m01, m12, m20]):
            out_t.append(list(nt))
            out_a.append(dict(a))
    _terrain_rebuild(app, terrain_group, out_t, out_a)
    return len(out_t)


def op_apply_flip_edge(app: Any, terrain_group: Any, click_pt: Point3D) -> bool:
    """Flips the diagonal between two adjacent triangles in the terrain."""
    from . import groundbox_core as sc
    from .terrain_mesh import flip_mesh_edge
    mesh = getattr(terrain_group, "mesh", None)
    if mesh is None:
        return False

    # Convert click_pt to local group coordinates so distances match triangles
    pt_loc_qv = sc.to_local(terrain_group, to_qvector3d(click_pt))
    click_pt_loc = (float(pt_loc_qv.x()), float(pt_loc_qv.y()), float(pt_loc_qv.z()))

    tris, attrs, _h = sc.read_terrain(mesh)
    if not tris:
        return False

    new_tris, ok = flip_mesh_edge(tris, click_pt_loc, pick_radius=8.0)
    if not ok:
        return False

    _terrain_rebuild(app, terrain_group, new_tris, attrs)
    return True


# ===========================================================================
# 7. Analiza spadków (Slope Heatmap) i Bryła 3D (Solid Skirt)
# ===========================================================================

def op_apply_slope_analysis(app: Any, terrain_group: Any) -> dict[str, Any]:
    """
    Calculates slope for each face in the terrain mesh and colors faces with an engineering heatmap.
    Preserves original material/color for later restoration.
    Rebuilds mesh with RGBA colors in-place to ensure OpenGL chunk buffers are updated.
    Returns slope distribution statistics dict.
    """
    from . import groundbox_core as sc
    mesh = getattr(terrain_group, "mesh", None)
    if mesh is None:
        raise ValueError("Terrain group has no mesh.")

    tris, attrs, _h = sc.read_terrain(mesh)
    if not tris:
        raise ValueError("No triangles found in terrain.")

    dist = calculate_slope_distribution(tris)

    new_attrs = []
    for tri, at in zip(tris, attrs):
        deg, pct = calculate_triangle_slope(tri)
        col = slope_to_color(pct)
        a = dict(at)
        if "orig_color" not in a:
            a["orig_color"] = list(a.get("color", [0.42, 0.65, 0.32, 1.0]))
        if "orig_back_color" not in a:
            a["orig_back_color"] = list(a.get("back_color", a["orig_color"]))
        a["color"] = list(col)
        a["back_color"] = list(col)
        a["slope_deg"] = deg
        a["slope_pct"] = pct
        new_attrs.append(a)

    _terrain_rebuild(app, terrain_group, tris, new_attrs)
    return dist


def op_reset_terrain_colors(app: Any, terrain_group: Any) -> bool:
    """Restores original face colors prior to slope analysis."""
    from . import groundbox_core as sc
    mesh = getattr(terrain_group, "mesh", None)
    if mesh is None:
        return False

    tris, attrs, _h = sc.read_terrain(mesh)
    if not tris:
        return False

    restored_attrs = []
    has_orig = False
    for a in attrs:
        ra = dict(a)
        if "orig_color" in ra:
            has_orig = True
            ra["color"] = list(ra["orig_color"])
            if "orig_back_color" in ra:
                ra["back_color"] = list(ra["orig_back_color"])
            else:
                ra["back_color"] = list(ra["orig_color"])
        restored_attrs.append(ra)

    if has_orig:
        _terrain_rebuild(app, terrain_group, tris, restored_attrs)
        return True
    return False


def op_create_terrain_skirt(
    app: Any,
    terrain_group: Any,
    depth_offset: float = 1.0,
    material_name: str = "Soil / Ground",
) -> Any:
    """
    Creates vertical skirt walls and a flat bottom cap, turning an open TIN terrain into a 100% closed, watertight 3D Solid.
    """
    triangles = extract_triangles_from_group(terrain_group)
    if not triangles:
        raise ValueError("Terrain contains no triangle geometry.")

    min_z = min(v[2] for tri in triangles for v in tri)
    base_z = min_z - abs(depth_offset)

    top_tris, side_tris, bot_tris = generate_terrain_skirt(triangles, base_z)

    mesh = Mesh()
    top_attrs = _get_material_attrs("Natural Grass")
    side_attrs = _get_material_attrs(material_name)

    # 1. Górna powierzchnia terenu (zachowaj materiał)
    for tri in top_tris:
        f = mesh.add_face([to_qvector3d(p) for p in tri])
        if f is not None and hasattr(f, "attrs"):
            f.attrs = {
                "color": list(top_attrs["color"]),
                "back_color": list(top_attrs["back_color"]),
                "mat": "Natural Grass",
            }

    # 2. Pionowe ściany boczne (materiał gruntu/podbudowy)
    for tri in side_tris:
        f = mesh.add_face([to_qvector3d(p) for p in tri])
        if f is not None and hasattr(f, "attrs"):
            f.attrs = {
                "color": list(side_attrs["color"]),
                "back_color": list(side_attrs["back_color"]),
                "mat": material_name,
            }

    # 3. Płaskie dno
    for tri in bot_tris:
        f = mesh.add_face([to_qvector3d(p) for p in tri])
        if f is not None and hasattr(f, "attrs"):
            f.attrs = {
                "color": list(side_attrs["color"]),
                "back_color": list(side_attrs["back_color"]),
                "mat": material_name,
            }

    # 4. Zmiękczenie przekątnych na pionowych ścianach bocznych (czyste, eleganckie pionowe ścianki)
    diag_keys = set()
    for loop in extract_boundary_loops(triangles):
        n = len(loop)
        for i in range(n):
            a = loop[i]
            b = loop[(i + 1) % n]
            a_bot = (a[0], a[1], float(base_z))
            k1 = (int(round(a_bot[0]*1000)), int(round(a_bot[1]*1000)), int(round(a_bot[2]*1000)))
            k2 = (int(round(b[0]*1000)), int(round(b[1]*1000)), int(round(b[2]*1000)))
            diag_keys.add((min(k1, k2), max(k1, k2)))

    def _pt_key(v):
        p = getattr(v, "position", v)
        if hasattr(p, "x"): return (int(round(p.x()*1000)), int(round(p.y()*1000)), int(round(p.z()*1000)))
        return (int(round(p[0]*1000)), int(round(p[1]*1000)), int(round(p[2]*1000)))

    for e in getattr(mesh, "edges", []):
        v0k = _pt_key(getattr(e, "v0", None))
        v1k = _pt_key(getattr(e, "v1", None))
        if (min(v0k, v1k), max(v0k, v1k)) in diag_keys:
            e.soft = True

    group_name = f"{getattr(terrain_group, 'name', 'Terrain')} (3D Solid)"
    solid_group = Group(mesh=mesh, name=group_name)
    solid_group.component = False
    solid_group.xform = QMatrix4x4()
    solid_group.ext = {
        PLUGIN_KEY: {
            "type": "Terrain",
            "origin": "SolidSkirt",
            "base_z": base_z,
            "depth_offset": depth_offset,
            "is_solid": True,
        }
    }
    _tag_bim(solid_group, "IfcGeographicElement", "Solid Terrain Base")
    commit_group_to_scene(app, solid_group, select=True)
    return solid_group


def _find_in_scene(scene: Any, obj: Any) -> Any | None:
    return obj
