# SPDX-License-Identifier: GPL-3.0-or-later
"""
inge_groundbox/geometry.py
========================
Czysty moduł matematyczno-geometryczny – brak zależności od Qt czy IngeTrazo.
Obsługuje algorytmy triangulacji Delaunaya, raycasting, przecięcia, rzutowanie,
funkcje opadania (falloff) oraz obliczanie mas ziemnych (cut & fill).
"""
from __future__ import annotations

import math
from typing import Any, Sequence

Point3D = tuple[float, float, float]
Point2D = tuple[float, float]
Triangle = list[Point3D]  # Zawsze 3 wierzchołki (x, y, z)


# ===========================================================================
# 1. Podstawowe operacje wektorowe 2D / 3D
# ===========================================================================

def v_add(a: Point3D, b: Point3D) -> Point3D:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def v_sub(a: Point3D, b: Point3D) -> Point3D:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def v_scale(a: Point3D, s: float) -> Point3D:
    return (a[0] * s, a[1] * s, a[2] * s)


def v_dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def v_cross(a: Point3D, b: Point3D) -> Point3D:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def v_len(a: Sequence[float]) -> float:
    return math.sqrt(sum(x * x for x in a))


def v_dist_2d(a: Sequence[float], b: Sequence[float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def v_dist_3d(a: Point3D, b: Point3D) -> float:
    return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2 + (a[2] - b[2])**2)


def v_normalize(a: Point3D) -> Point3D:
    l = v_len(a)
    if l < 1e-12:
        return (0.0, 0.0, 1.0)
    return (a[0] / l, a[1] / l, a[2] / l)


def newell_normal(pts: Sequence[Point3D]) -> Point3D:
    """Oblicza wektor normalny wielokąta metodą Newella w 3D."""
    n = len(pts)
    if n < 3:
        return (0.0, 0.0, 1.0)
    nx = 0.0
    ny = 0.0
    nz = 0.0
    for i in range(n):
        c = pts[i]
        nxt = pts[(i + 1) % n]
        nx += (c[1] - nxt[1]) * (c[2] + nxt[2])
        ny += (c[2] - nxt[2]) * (c[0] + nxt[0])
        nz += (c[0] - nxt[0]) * (c[1] + nxt[1])
    return v_normalize((nx, ny, nz))


def signed_area_2d(pts: Sequence[Point2D | Point3D]) -> float:
    """Pole ze znakiem w 2D (metoda sznurowania Gaussa). >0 oznacza obieg CCW."""
    n = len(pts)
    if n < 3:
        return 0.0
    return 0.5 * sum(
        pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1]
        for i in range(n)
    )


def ensure_ccw_2d(pts: list[Point2D | Point3D]) -> list[Point2D | Point3D]:
    """Wymusza obieg przeciwny do ruchu wskazówek zegara (CCW) w rzucie 2D."""
    if signed_area_2d(pts) < 0.0:
        return list(reversed(pts))
    return pts


# ===========================================================================
# 2. Triangulacja Delaunaya w 2D (Bowyer-Watson + Scipy fallback)
# ===========================================================================

def triangulate_points_2d(
    points_3d: Sequence[Point3D],
    max_edge_len: float | None = None,
) -> list[Triangle]:
    """
    Wykonuje triangulację Delaunaya w płaszczyźnie XY dla chmury punktów 3D.
    Wysokości Z są interpolowane bezpośrednio z wierzchołków wejściowych.

    Wspiera:
    - Scipy Delaunay jeśli dostępne (bardzo szybkie)
    - Wbudowany, czysty algorytm Bowyera-Watsona (zero zależności)
    """
    pts = list(points_3d)
    # Usuń duplikaty w rzucie 2D zachowując najwyższą rzędną Z (jak w GroundBox)
    by_key: dict[tuple[int, int], Point3D] = {}
    scale = 10000.0  # tolerancja 0.1 mm

    for p in pts:
        key = (int(round(p[0] * scale)), int(round(p[1] * scale)))
        if key not in by_key or p[2] > by_key[key][2]:
            by_key[key] = (float(p[0]), float(p[1]), float(p[2]))

    unique_pts = list(by_key.values())

    if len(unique_pts) < 3:
        return []

    # 1. Próba użycia scipy
    triangles: list[Triangle] = []
    use_scipy = False
    try:
        from scipy.spatial import Delaunay  # type: ignore
        pts_2d = [[p[0], p[1]] for p in unique_pts]
        tri = Delaunay(pts_2d)
        for simplex in tri.simplices:
            p0 = unique_pts[simplex[0]]
            p1 = unique_pts[simplex[1]]
            p2 = unique_pts[simplex[2]]
            triangles.append([p0, p1, p2])
        use_scipy = True
    except Exception:
        use_scipy = False

    # 2. Próba użycia Shapely Delaunay
    if not use_scipy or not triangles:
        try:
            from shapely.geometry import MultiPoint  # type: ignore
            import shapely.ops  # type: ignore
            mp = MultiPoint([(p[0], p[1]) for p in unique_pts])
            pt_map = {(round(p[0], 4), round(p[1], 4)): p[2] for p in unique_pts}
            sh_tris = shapely.ops.triangulate(mp)
            for st in sh_tris:
                coords = list(st.exterior.coords)[:-1]
                if len(coords) == 3:
                    triangles.append([
                        (coords[0][0], coords[0][1], pt_map.get((round(coords[0][0], 4), round(coords[0][1], 4)), 0.0)),
                        (coords[1][0], coords[1][1], pt_map.get((round(coords[1][0], 4), round(coords[1][1], 4)), 0.0)),
                        (coords[2][0], coords[2][1], pt_map.get((round(coords[2][0], 4), round(coords[2][1], 4)), 0.0)),
                    ])
        except Exception:
            triangles = []

    # 3. Czysty fallback Bowyer-Watson jeśli brak scipy/shapely lub błąd
    if not triangles:
        triangles = _bowyer_watson_delaunay(unique_pts)

    # 3. Zapewnij orientację CCW (normalne skierowane ku górze w stronę +Z)
    oriented_tris: list[Triangle] = []
    for tri in triangles:
        if signed_area_2d(tri) < 0.0:
            tri = [tri[0], tri[2], tri[1]]

        # Opcjonalne odrzucanie zbyt długich trójkątów na krawędziach
        if max_edge_len is not None and max_edge_len > 0:
            e0 = v_dist_2d(tri[0], tri[1])
            e1 = v_dist_2d(tri[1], tri[2])
            e2 = v_dist_2d(tri[2], tri[0])
            if max(e0, e1, e2) > max_edge_len:
                continue

        oriented_tris.append(tri)

    return oriented_tris


def _bowyer_watson_delaunay(points: list[Point3D]) -> list[Triangle]:
    """Czysta, niezależna implementacja algorytmu Bowyera-Watsona w 2D."""
    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)

    dx = max_x - min_x
    dy = max_y - min_y
    delta_max = max(dx, dy, 1.0)
    mid_x = (min_x + max_x) * 0.5
    mid_y = (min_y + max_y) * 0.5

    # Super-trójkąt obejmujący wszystkie punkty
    p1 = (mid_x - 20 * delta_max, mid_y - delta_max, 0.0)
    p2 = (mid_x, mid_y + 20 * delta_max, 0.0)
    p3 = (mid_x + 20 * delta_max, mid_y - delta_max, 0.0)

    triangles: list[list[Point3D]] = [[p1, p2, p3]]

    for point in points:
        px, py, _ = point
        bad_triangles = []

        for tri in triangles:
            # Sprawdź czy punkt leży wewnątrz okręgu opisanego na trójkącie
            if _point_in_circumcircle_2d((px, py), tri):
                bad_triangles.append(tri)

        # Znajdź wielokąt brzegu luki (krawędzie występujące dokładnie raz)
        polygon = []
        for tri in bad_triangles:
            edges = [
                (tri[0], tri[1]),
                (tri[1], tri[2]),
                (tri[2], tri[0]),
            ]
            for edge in edges:
                is_shared = False
                for other in bad_triangles:
                    if other is tri:
                        continue
                    other_edges = [
                        (other[0], other[1]),
                        (other[1], other[2]),
                        (other[2], other[0]),
                    ]
                    for oe in other_edges:
                        if (_pts_eq_2d(edge[0], oe[0]) and _pts_eq_2d(edge[1], oe[1])) or \
                           (_pts_eq_2d(edge[0], oe[1]) and _pts_eq_2d(edge[1], oe[0])):
                            is_shared = True
                            break
                    if is_shared:
                        break
                if not is_shared:
                    polygon.append(edge)

        # Usuń wadliwe trójkąty
        for tri in bad_triangles:
            triangles.remove(tri)

        # Zbuduj nowe trójkąty łącząc punkt z krawędziami wielokąta
        for edge in polygon:
            triangles.append([edge[0], edge[1], point])

    # Usuń trójkąty połączone z super-trójkątem
    super_verts = (p1, p2, p3)
    final_triangles: list[Triangle] = []
    for tri in triangles:
        touches_super = any(
            any(_pts_eq_2d(v, sv) for sv in super_verts)
            for v in tri
        )
        if not touches_super:
            final_triangles.append(tri)

    return final_triangles


def _pts_eq_2d(p1: Sequence[float], p2: Sequence[float], tol: float = 1e-6) -> bool:
    return abs(p1[0] - p2[0]) < tol and abs(p1[1] - p2[1]) < tol


def _point_in_circumcircle_2d(p: Point2D, tri: list[Point3D]) -> bool:
    """Sprawdza czy punkt p=(x, y) leży wewnątrz okręgu opisanego na trójkącie tri w 2D."""
    ax, ay = tri[0][0], tri[0][1]
    bx, by = tri[1][0], tri[1][1]
    cx, cy = tri[2][0], tri[2][1]
    px, py = p[0], p[1]

    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-12:
        return False

    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d

    r_sq = (ax - ux)**2 + (ay - uy)**2
    dist_sq = (px - ux)**2 + (py - uy)**2
    return dist_sq < r_sq - 1e-10


# ===========================================================================
# 3. Raycasting i przecięcia Möller–Trumbore
# ===========================================================================

def ray_triangle_intersect(
    ray_origin: Point3D,
    ray_dir: Point3D,
    tri: Triangle,
) -> Point3D | None:
    """Algorytm Möller–Trumbore przecięcia promienia z trójkątem 3D."""
    EPSILON = 1e-8
    v0, v1, v2 = tri
    e1 = v_sub(v1, v0)
    e2 = v_sub(v2, v0)

    h = v_cross(ray_dir, e2)
    a = v_dot(e1, h)

    if -EPSILON < a < EPSILON:
        return None  # Promień równoległy do trójkąta

    f = 1.0 / a
    s = v_sub(ray_origin, v0)
    u = f * v_dot(s, h)

    if u < -EPSILON or u > 1.0 + EPSILON:
        return None

    q = v_cross(s, e1)
    v = f * v_dot(ray_dir, q)

    if v < -EPSILON or u + v > 1.0 + EPSILON:
        return None

    t = f * v_dot(e2, q)
    if t < EPSILON:
        return None

    return (
        ray_origin[0] + ray_dir[0] * t,
        ray_origin[1] + ray_dir[1] * t,
        ray_origin[2] + ray_dir[2] * t,
    )


def point_z_on_triangle(px: float, py: float, tri: Triangle) -> float | None:
    """Oblicza wysokość Z punktu (px, py) na trójkącie metodą barycentryczną."""
    hit = ray_triangle_intersect((px, py, 10000.0), (0.0, 0.0, -1.0), tri)
    if hit is not None:
        return hit[2]
    return None


def drape_path_onto_terrain(
    path_points: Sequence[Point3D],
    terrain_triangles: Sequence[Triangle],
) -> list[Point3D]:
    """Rzutuje ciąg punktów pionowo w dół na siatkę terenu."""
    ray_dir = (0.0, 0.0, -1.0)
    draped: list[Point3D] = []

    for px, py, pz in path_points:
        origin = (px, py, 10000.0)
        hit: Point3D | None = None

        for tri in terrain_triangles:
            inter = ray_triangle_intersect(origin, ray_dir, tri)
            if inter is not None:
                if hit is None or inter[2] > hit[2]:
                    hit = inter

        draped.append(hit if hit is not None else (px, py, pz))

    return draped


# ===========================================================================
# 4. Funkcje opadania (Smoove Falloffs)
# ===========================================================================

def smoove_falloff(dist: float, radius: float, profile: str = "cosine") -> float:
    """
    Oblicza wagę opadania w [0.0, 1.0] dla zadanego promienia.
    Profile: 'cosine' (SketchUp), 'gaussian', 'linear', 'smoothstep'.
    """
    if radius <= 0.0 or dist >= radius:
        return 0.0
    t = dist / radius  # t in [0, 1)

    if profile == "gaussian":
        return math.exp(-3.0 * (t * t))
    elif profile == "linear":
        return 1.0 - t
    elif profile == "smoothstep":
        return 1.0 - (3.0 * t * t - 2.0 * t * t * t)
    else:
        # Domyślny Cosine (standard z GroundBox)
        return 0.5 * (1.0 + math.cos(math.pi * t))


def apply_smoove(
    vertices: Sequence[Point3D],
    center: Point3D,
    radius: float,
    delta_z: float,
    profile: str = "cosine",
) -> list[Point3D]:
    """Przesuwa wierzchołki w osi Z zgodnie z funkcją pędzla Smoove."""
    cx, cy, _ = center
    result: list[Point3D] = []
    for x, y, z in vertices:
        dist = math.hypot(x - cx, y - cy)
        weight = smoove_falloff(dist, radius, profile)
        new_z = z + delta_z * weight
        result.append((x, y, new_z))
    return result


# ===========================================================================
# 5. Geometria Odcisku (Stamp) i Odsunięcie Wielokąta
# ===========================================================================

def offset_polygon_2d(poly: list[Point2D], offset_dist: float) -> list[Point2D]:
    """
    Wykonuje odsunięcie (buffer/offset) wielokąta 2D na zewnątrz.
    Zabezpieczenie przed samoprzecięciami i szpicami (Miter Limit).
    """
    # 1. Próba użycia Shapely
    try:
        from shapely.geometry import Polygon  # type: ignore
        sp = Polygon(poly)
        buffered = sp.buffer(offset_dist, join_style="mitre", mitre_limit=3.0)
        if not buffered.is_empty and hasattr(buffered, "exterior"):
            coords = list(buffered.exterior.coords)[:-1]
            return ensure_ccw_2d(coords)
    except Exception:
        pass

    # 2. Wbudowany czysty algorytm dwusiecznych narożników (Miter Bisector)
    poly = ensure_ccw_2d(poly)
    n = len(poly)
    if n < 3:
        return poly

    out_poly: list[Point2D] = []
    for i in range(n):
        p_prev = poly[(i - 1 + n) % n]
        p_curr = poly[i]
        p_next = poly[(i + 1) % n]

        # Wektory krawędzi
        v1 = (p_curr[0] - p_prev[0], p_curr[1] - p_prev[1])
        v2 = (p_next[0] - p_curr[0], p_next[1] - p_curr[1])

        l1 = math.hypot(v1[0], v1[1])
        l2 = math.hypot(v2[0], v2[1])
        if l1 < 1e-9 or l2 < 1e-9:
            out_poly.append(p_curr)
            continue

        # Normalne prawe (dla CCW skierowane na zewnątrz)
        n1 = (v1[1] / l1, -v1[0] / l1)
        n2 = (v2[1] / l2, -v2[0] / l2)

        # Wektor dwusiecznej
        bisector = (n1[0] + n2[0], n1[1] + n2[1])
        b_len = math.hypot(bisector[0], bisector[1])

        if b_len < 0.1:  # Narożnik bardzo ostry lub prosty powrót
            miter_scale = 1.0
            bx, by = n1[0], n1[1]
        else:
            bx = bisector[0] / b_len
            by = bisector[1] / b_len
            cos_half = n2[0] * bx + n2[1] * by
            miter_scale = 1.0 / max(0.25, cos_half)  # Miter limit <= 4.0

        offset_pt = (
            p_curr[0] + bx * offset_dist * miter_scale,
            p_curr[1] + by * offset_dist * miter_scale,
        )
        out_poly.append(offset_pt)

    return out_poly


def point_in_polygon_2d(pt: Point2D | Point3D, poly: Sequence[Point2D | Point3D]) -> bool:
    """Ray-casting test zawierania punktu w wielokącie 2D."""
    x, y = pt[0], pt[1]
    inside = False
    n = len(poly)
    for i in range(n):
        p1 = poly[i]
        p2 = poly[(i + 1) % n]
        if ((p1[1] > y) != (p2[1] > y)) and (x < (p2[0] - p1[0]) * (y - p1[1]) / (p2[1] - p1[1] + 1e-12) + p1[0]):
            inside = not inside
    return inside


# ===========================================================================
# 6. Obliczanie mas ziemnych (Cut & Fill Volume)
# ===========================================================================

def calculate_cut_fill(
    triangles_old: Sequence[Triangle],
    triangles_new: Sequence[Triangle],
) -> tuple[float, float, float]:
    """
    Oblicza objętość wykopu (Cut), nasypu (Fill) oraz bilans mas (Net) w m³.
    Zwraca: (cut_volume, fill_volume, net_balance)
    """
    cut_vol = 0.0
    fill_vol = 0.0

    # Próbkujemy wysokości w siatce regularnej lub centroidach trójkątów
    for tri in triangles_new:
        area_2d = abs(signed_area_2d(tri))
        if area_2d < 1e-6:
            continue

        cx = (tri[0][0] + tri[1][0] + tri[2][0]) / 3.0
        cy = (tri[0][1] + tri[1][1] + tri[2][1]) / 3.0
        new_z = (tri[0][2] + tri[1][2] + tri[2][2]) / 3.0

        # Znajdź wysokość terenu pierwotnego w punkcie (cx, cy)
        old_z = None
        for otri in triangles_old:
            z_cand = point_z_on_triangle(cx, cy, otri)
            if z_cand is not None:
                old_z = z_cand
                break

        if old_z is not None:
            diff_z = new_z - old_z
            if diff_z > 0.001:
                fill_vol += area_2d * diff_z
            elif diff_z < -0.001:
                cut_vol += area_2d * abs(diff_z)

    net_balance = fill_vol - cut_vol
    return (cut_vol, fill_vol, net_balance)


# ===========================================================================
# 7. Operacje boolowskie na siatce (CSG Stamp & Drape Cutter)
# ===========================================================================

def plane_z(
    x: float,
    y: float,
    p0: Sequence[float],
    p1: Sequence[float],
    p2: Sequence[float],
) -> float:
    """Interpoluje wysokość Z w punkcie (x, y) leżącym na płaszczyźnie trójkąta (p0, p1, p2)."""
    u = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
    v = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])
    a = u[1] * v[2] - u[2] * v[1]
    b = u[2] * v[0] - u[0] * v[2]
    c = u[0] * v[1] - u[1] * v[0]
    if abs(c) < 1e-7:
        return (p0[2] + p1[2] + p2[2]) / 3.0
    return p0[2] - (a * (x - p0[0]) + b * (y - p0[1])) / c


def cut_triangle_by_polygon_both_2d(
    tri: Triangle,
    clip_poly_coords: Sequence[Sequence[float]],
) -> tuple[list[Triangle], list[Triangle]]:
    """
    Kroi trójkąt 3D terenu wielokątem 2D (np. obrysem odcisku Stamp).
    Zwraca: (trójkąty_na_zewnątrz, trójkąty_wewnątrz)
    Wszystkie nowe wierzchołki mają rzędną Z dokładnie na płaszczyźnie trójkąta.
    Orientacja CCW jest zachowywana.
    """
    try:
        from shapely.geometry import Polygon  # type: ignore
        import shapely.ops  # type: ignore
    except ImportError:
        # Fallback jeśli brak shapely
        c = ((tri[0][0] + tri[1][0] + tri[2][0]) / 3.0, (tri[0][1] + tri[1][1] + tri[2][1]) / 3.0)
        if point_in_polygon_2d(c, clip_poly_coords):
            return [], [ensure_ccw_tri(tri)]
        return [ensure_ccw_tri(tri)], []

    t_poly = Polygon([(p[0], p[1]) for p in tri])
    c_poly = Polygon([(p[0], p[1]) for p in clip_poly_coords])

    if not t_poly.is_valid:
        t_poly = t_poly.buffer(0)
    if not c_poly.is_valid:
        c_poly = c_poly.buffer(0)

    if not t_poly.intersects(c_poly):
        return [ensure_ccw_tri(tri)], []
    if c_poly.contains(t_poly):
        return [], [ensure_ccw_tri(tri)]

    out_geom = t_poly.difference(c_poly)
    in_geom = t_poly.intersection(c_poly)

    out_tris: list[Triangle] = []
    in_tris: list[Triangle] = []

    def _process_geom(geom: Any, target: list[Triangle]) -> None:
        if geom is None or geom.is_empty:
            return
        sub_polys = getattr(geom, "geoms", [geom])
        for sp in sub_polys:
            if not isinstance(sp, Polygon) or sp.area < 1e-8:
                continue
            raw_tris = shapely.ops.triangulate(sp)
            for rt in raw_tris:
                if sp.covers(rt.representative_point()):
                    coords = list(rt.exterior.coords)[:-1]
                    if len(coords) == 3:
                        t3d = [(pt[0], pt[1], plane_z(pt[0], pt[1], tri[0], tri[1], tri[2])) for pt in coords]
                        target.append(ensure_ccw_tri(t3d))

    _process_geom(out_geom, out_tris)
    _process_geom(in_geom, in_tris)
    return out_tris, in_tris


def split_triangle_by_lines_2d(
    tri: Triangle,
    lines_coords: Sequence[Sequence[Sequence[float]]],
) -> list[Triangle]:
    """
    Rozcina trójkąt terenu 3D zadanymi liniami rzutowania (Drape).
    Dzięki temu rzutowane krawędzie stają się rzeczywistymi krawędziami siatki terenu.
    """
    try:
        from shapely.geometry import LineString, MultiLineString, Polygon  # type: ignore
        from shapely.ops import split, unary_union  # type: ignore
        import shapely.ops  # type: ignore
    except ImportError:
        return [ensure_ccw_tri(tri)]

    t_poly = Polygon([(p[0], p[1]) for p in tri])
    if not t_poly.is_valid:
        t_poly = t_poly.buffer(0)

    sh_lines = []
    for lc in lines_coords:
        if len(lc) >= 2:
            sh_lines.append(LineString([(p[0], p[1]) for p in lc]))

    if not sh_lines:
        return [ensure_ccw_tri(tri)]

    union_lines = unary_union(sh_lines)
    inter = t_poly.intersection(union_lines)
    if inter.is_empty or getattr(inter, "length", 0.0) < 1e-5:
        return [ensure_ccw_tri(tri)]

    try:
        split_res = split(t_poly, inter)
    except Exception:
        return [ensure_ccw_tri(tri)]

    sub_tris: list[Triangle] = []
    sub_polys = getattr(split_res, "geoms", [split_res])
    for sp in sub_polys:
        if not isinstance(sp, Polygon) or sp.area < 1e-8:
            continue
        raw = shapely.ops.triangulate(sp)
        for rt in raw:
            if sp.covers(rt.representative_point()):
                coords = list(rt.exterior.coords)[:-1]
                if len(coords) == 3:
                    t3d = [(pt[0], pt[1], plane_z(pt[0], pt[1], tri[0], tri[1], tri[2])) for pt in coords]
                    sub_tris.append(ensure_ccw_tri(t3d))

    return sub_tris if sub_tris else [ensure_ccw_tri(tri)]


def ensure_ccw_tri(tri: Triangle) -> Triangle:
    """Upewnia się, że trójkąt w 2D ma orientację CCW (normalna skierowana w górę)."""
    if signed_area_2d(tri) < 0.0:
        return [tri[0], tri[2], tri[1]]
    return tri


# ===========================================================================
# 8. Analiza spadków (Slope Analysis & Classification)
# ===========================================================================

# 10 standardowych pasm inżynieryjnych nachylenia (kolory RGBA od 0.0 do 1.0)
COLOR_SLOPE_B1 = [0.15, 0.65, 0.25, 1.0]   # 0% - 5% (Ciemna zieleń / Flat)
COLOR_SLOPE_B2 = [0.25, 0.78, 0.28, 1.0]   # 5% - 10% (Zieleń / Gentle)
COLOR_SLOPE_B3 = [0.55, 0.82, 0.22, 1.0]   # 10% - 15% (Jasna zieleń / Moderate)
COLOR_SLOPE_B4 = [0.78, 0.88, 0.18, 1.0]   # 15% - 20% (Limonkowy / Rolling)
COLOR_SLOPE_B5 = [0.96, 0.88, 0.15, 1.0]   # 20% - 30% (Żółty / Steep)
COLOR_SLOPE_B6 = [0.96, 0.70, 0.12, 1.0]   # 30% - 40% (Bursztyn / Very Steep)
COLOR_SLOPE_B7 = [0.96, 0.50, 0.12, 1.0]   # 40% - 50% (Pomarańczowy / Embankment 1:2)
COLOR_SLOPE_B8 = [0.92, 0.35, 0.14, 1.0]   # 50% - 70% (Ciemny pomarańcz / 1:1.5)
COLOR_SLOPE_B9 = [0.85, 0.18, 0.18, 1.0]   # 70% - 100% (Czerwony / Slope 1:1)
COLOR_SLOPE_B10 = [0.55, 0.08, 0.25, 1.0]  # > 100% (Bordowy / Cliff >45°)

# Backward compatibility aliases
COLOR_SLOPE_FLAT = COLOR_SLOPE_B1
COLOR_SLOPE_GENTLE = COLOR_SLOPE_B3
COLOR_SLOPE_MODERATE = COLOR_SLOPE_B5
COLOR_SLOPE_STEEP = COLOR_SLOPE_B9


def calculate_triangle_slope(tri: Triangle) -> tuple[float, float]:
    """
    Oblicza nachylenie trójkąta terenu względem płaszczyzny poziomej XY.
    Zwraca: (kąt_w_stopniach, spadek_w_procentach)
    """
    (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = tri
    ux, uy, uz = x1 - x0, y1 - y0, z1 - z0
    vx, vy, vz = x2 - x0, y2 - y0, z2 - z0
    nx = uy * vz - uz * vy
    ny = uz * vx - ux * vz
    nz = ux * vy - uy * vx
    n_len = math.sqrt(nx * nx + ny * ny + nz * nz)
    if n_len < 1e-12:
        return 0.0, 0.0

    nx /= n_len
    ny /= n_len
    nz /= n_len
    if nz < 0:
        nx, ny, nz = -nx, -ny, -nz

    cos_theta = max(0.0, min(1.0, nz))
    theta_rad = math.acos(cos_theta)
    slope_deg = math.degrees(theta_rad)

    if cos_theta > 1e-6:
        slope_pct = math.tan(theta_rad) * 100.0
    else:
        slope_pct = 999.0
    return slope_deg, slope_pct


def slope_to_color(slope_pct: float) -> list[float]:
    """Zwraca kolor RGB dla zadanego spadku procentowego (10 pasm inżynieryjnych)."""
    if slope_pct < 5.0:
        return list(COLOR_SLOPE_B1)
    elif slope_pct < 10.0:
        return list(COLOR_SLOPE_B2)
    elif slope_pct < 15.0:
        return list(COLOR_SLOPE_B3)
    elif slope_pct < 20.0:
        return list(COLOR_SLOPE_B4)
    elif slope_pct < 30.0:
        return list(COLOR_SLOPE_B5)
    elif slope_pct < 40.0:
        return list(COLOR_SLOPE_B6)
    elif slope_pct < 50.0:
        return list(COLOR_SLOPE_B7)
    elif slope_pct < 70.0:
        return list(COLOR_SLOPE_B8)
    elif slope_pct < 100.0:
        return list(COLOR_SLOPE_B9)
    else:
        return list(COLOR_SLOPE_B10)


def calculate_slope_distribution(triangles: Sequence[Triangle]) -> dict[str, Any]:
    """
    Analizuje statystyki nachylenia dla zbioru trójkątów.
    Zwraca: {
        'avg_slope_deg': float,
        'avg_slope_pct': float,
        'max_slope_deg': float,
        'max_slope_pct': float,
        'band_areas': [area_b1, ..., area_b10],
        'band_pcts': [pct_b1, ..., pct_b10],
        'total_area_2d': float,
        'total_area_3d': float,
    }
    """
    if not triangles:
        return {
            "avg_slope_deg": 0.0, "avg_slope_pct": 0.0,
            "max_slope_deg": 0.0, "max_slope_pct": 0.0,
            "band_areas": [0.0] * 10,
            "band_pcts": [0.0] * 10,
            "total_area_2d": 0.0, "total_area_3d": 0.0,
        }

    total_area_2d = 0.0
    total_area_3d = 0.0
    weighted_deg_sum = 0.0
    weighted_pct_sum = 0.0
    max_deg = 0.0
    max_pct = 0.0

    band_areas = [0.0] * 10

    for tri in triangles:
        area_2d = abs(signed_area_2d(tri))
        if area_2d < 1e-8:
            continue

        deg, pct = calculate_triangle_slope(tri)
        max_deg = max(max_deg, deg)
        max_pct = max(max_pct, pct)

        total_area_2d += area_2d
        weighted_deg_sum += deg * area_2d
        weighted_pct_sum += pct * area_2d

        # Pole 3D
        e1 = v_sub(tri[1], tri[0])
        e2 = v_sub(tri[2], tri[0])
        cp = v_cross(e1, e2)
        area_3d = 0.5 * v_len(cp)
        total_area_3d += area_3d

        if pct < 5.0:
            band_areas[0] += area_2d
        elif pct < 10.0:
            band_areas[1] += area_2d
        elif pct < 15.0:
            band_areas[2] += area_2d
        elif pct < 20.0:
            band_areas[3] += area_2d
        elif pct < 30.0:
            band_areas[4] += area_2d
        elif pct < 40.0:
            band_areas[5] += area_2d
        elif pct < 50.0:
            band_areas[6] += area_2d
        elif pct < 70.0:
            band_areas[7] += area_2d
        elif pct < 100.0:
            band_areas[8] += area_2d
        else:
            band_areas[9] += area_2d

    avg_deg = (weighted_deg_sum / total_area_2d) if total_area_2d > 1e-8 else 0.0
    avg_pct = (weighted_pct_sum / total_area_2d) if total_area_2d > 1e-8 else 0.0

    band_pcts = [
        (a / total_area_2d * 100.0) if total_area_2d > 1e-8 else 0.0
        for a in band_areas
    ]

    return {
        "avg_slope_deg": avg_deg,
        "avg_slope_pct": avg_pct,
        "max_slope_deg": max_deg,
        "max_slope_pct": max_pct,
        "band_areas": band_areas,
        "band_pcts": band_pcts,
        "total_area_2d": total_area_2d,
        "total_area_3d": total_area_3d,
    }


# ===========================================================================
# 9. Tworzenie pełnej bryły 3D (Solid Skirt / Podbudowa terenu)
# ===========================================================================

def extract_boundary_loops(triangles: Sequence[Triangle]) -> list[list[Point3D]]:
    """
    Wyodrębnia zorientowane pętle krawędzi brzegowych z otwartej siatki TIN.
    Każda pętla jest ułożona w ciąg wierzchołków CCW.
    """
    def p_key(p: Sequence[float]) -> tuple[int, int, int]:
        return (int(round(p[0] * 1000)), int(round(p[1] * 1000)), int(round(p[2] * 1000)))

    directed_edges: dict[tuple[tuple[int, int, int], tuple[int, int, int]], tuple[Point3D, Point3D]] = {}
    for tri in triangles:
        for i in range(3):
            a, b = tri[i], tri[(i + 1) % 3]
            ka, kb = p_key(a), p_key(b)
            directed_edges[(ka, kb)] = (a, b)

    boundary_edges = []
    for (ka, kb), (a, b) in directed_edges.items():
        if (kb, ka) not in directed_edges:
            boundary_edges.append((a, b))

    if not boundary_edges:
        return []

    adj: dict[tuple[int, int, int], tuple[Point3D, Point3D]] = {}
    for a, b in boundary_edges:
        adj[p_key(a)] = (a, b)

    loops: list[list[Point3D]] = []
    visited: set[tuple[int, int, int]] = set()

    for start_k in list(adj.keys()):
        if start_k in visited:
            continue
        curr_k = start_k
        loop: list[Point3D] = []
        loop_visited: set[tuple[int, int, int]] = set()

        while curr_k in adj and curr_k not in loop_visited:
            loop_visited.add(curr_k)
            visited.add(curr_k)
            a, b = adj[curr_k]
            loop.append(a)
            curr_k = p_key(b)

        if len(loop) >= 3:
            loops.append(loop)

    return loops


def generate_terrain_skirt(
    triangles: Sequence[Triangle],
    base_z: float,
) -> tuple[list[Triangle], list[Triangle], list[Triangle]]:
    """
    Tworzy ściany pionowe (skirt) i dno, zamykając otwartą siatkę terenu w szczelną bryłę 3D (Solid).
    Zwraca: (top_triangles, side_wall_triangles, bottom_cap_triangles)
    """
    loops = extract_boundary_loops(triangles)
    side_walls: list[Triangle] = []
    bottom_caps: list[Triangle] = []

    for loop in loops:
        n = len(loop)
        # 1. Pionowe ściany boczne (outward-facing)
        for i in range(n):
            a = loop[i]
            b = loop[(i + 1) % n]
            a_bot = (a[0], a[1], float(base_z))
            b_bot = (b[0], b[1], float(base_z))

            t1 = [a, a_bot, b]
            t2 = [b, a_bot, b_bot]
            side_walls.append(t1)
            side_walls.append(t2)

    # 2. Płaskie dno zoptymalizowane pod kątem lekkości i estetyki
    # Wykorzystujemy triangulację 2D wyłącznie na punktach obrysu (Delaunay),
    # dzięki czemu dno jest eleganckie, zrównoważone i nie kopiuje zbędnych dziesiątek tysięcy
    # wewnętrznych wierzchołków z góry terenu.
    for loop in loops:
        bot_tris = triangulate_bottom_cap(loop, base_z)
        bottom_caps.extend(bot_tris)

    return list(triangles), side_walls, bottom_caps


def triangulate_bottom_cap(loop: Sequence[Point3D], base_z: float) -> list[Triangle]:
    """
    Tworzy czystą, zrównoważoną i niskopoligonową triangulację dna bryły (Delaunay 2D).
    Wykorzystuje wyłącznie punkty obrysu zewnętrznego (zamiast powielania dziesiątek tysięcy
    wewnętrznych wierzchołków z góry terenu) oraz eliminuje ostre wachlarze trójkątów z jednego narożnika.
    """
    if len(loop) < 3:
        return []

    loop_2d = [(p[0], p[1]) for p in loop]

    # 1. Próba triangulacji Delaunaya 2D za pomocą Shapely
    try:
        from shapely.geometry import Polygon
        from shapely.ops import triangulate
        poly = Polygon(loop_2d)
        if poly.is_valid and poly.area > 1e-6:
            dt_polys = triangulate(poly)
            bot_tris: list[Triangle] = []
            poly_buffered = poly.buffer(1e-4)
            for tp in dt_polys:
                if poly_buffered.covers(tp.representative_point()):
                    c = list(tp.exterior.coords)[:3]
                    p0 = (c[0][0], c[0][1], float(base_z))
                    p1 = (c[1][0], c[1][1], float(base_z))
                    p2 = (c[2][0], c[2][1], float(base_z))
                    # Wektor normalny skierowany w dół (-Z):
                    if signed_area_2d([p0, p1, p2]) > 0:
                        bot_tris.append([p0, p2, p1])
                    else:
                        bot_tris.append([p0, p1, p2])
            if bot_tris:
                return bot_tris
    except Exception:
        pass

    # 2. Zrównoważony fallback: Centroid Fan (każdy odcinek obwodu łączony ze środkiem ciężkości)
    # Zamiast ostrego wachlarza z jednego narożnika, tworzy symetryczny, promienisty podział
    cx = sum(p[0] for p in loop) / len(loop)
    cy = sum(p[1] for p in loop) / len(loop)
    center_pt = (cx, cy, float(base_z))

    bot_tris = []
    n = len(loop)
    for i in range(n):
        a = (loop[i][0], loop[i][1], float(base_z))
        b = (loop[(i + 1) % n][0], loop[(i + 1) % n][1], float(base_z))
        # Skierowany w dół (-Z)
        tri = [b, a, center_pt]
        if signed_area_2d(tri) > 0:
            tri = [tri[0], tri[2], tri[1]]
        bot_tris.append(tri)

    return bot_tris


def earclip_polygon_2d(pts: Sequence[Point2D]) -> list[tuple[Point2D, Point2D, Point2D]]:
    """Pure-Python triangulacja prostego wielokąta 2D (ear clipping)."""
    if len(pts) < 3:
        return []
    pts_list = list(pts)
    if signed_area_2d([(p[0], p[1], 0.0) for p in pts_list]) < 0:
        pts_list = pts_list[::-1]
    idx = list(range(len(pts_list)))
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
            a, b, c = pts_list[i0], pts_list[i1], pts_list[i2]
            if cross(a, b, c) <= 1e-12:
                continue
            ok = True
            for j in idx:
                if j in (i0, i1, i2):
                    continue
                p = pts_list[j]
                if (cross(a, b, p) >= -1e-11 and cross(b, c, p) >= -1e-11
                        and cross(c, a, p) >= -1e-11):
                    ok = False
                    break
            if ok:
                out.append((a, b, c))
                idx.pop(k)
                clipped = True
                break
        if not clipped:
            break

    if len(idx) == 3:
        out.append((pts_list[idx[0]], pts_list[idx[1]], pts_list[idx[2]]))
    return out

