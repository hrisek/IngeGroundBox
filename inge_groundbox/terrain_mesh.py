# SPDX-License-Identifier: GPL-3.0-or-later
"""
inge_groundbox/terrain_mesh.py
============================
Algorytmy manipulacji siatką TIN (Triangulated Irregular Network):
- From Scratch (siatka płaska z naprzemiennymi przekątnymi)
- From Contours (triangulacja warstwic z adaptacyjną densyfikacją)
- Stamp (wycinanie terenu, płaska półka i skarpy przejściowe)
- Drape (krojenie siatki terenu rzutowanymi liniami)
- Add Detail (podział trójkątów 1-do-4)
- Flip Edge (odwracanie przekątnych w czworokącie)
- Delaunay Mesh Optimizer (automatyczne wygładzanie topologii)
- Slicer poziomic (generowanie warstwic z terenu)
"""
from __future__ import annotations

import math
from typing import Sequence

from .geometry import (
    Point2D,
    Point3D,
    Triangle,
    cut_triangle_by_polygon_both_2d,
    ensure_ccw_2d,
    ensure_ccw_tri,
    offset_polygon_2d,
    plane_z,
    point_in_polygon_2d,
    point_z_on_triangle,
    ray_triangle_intersect,
    signed_area_2d,
    split_triangle_by_lines_2d,
    triangulate_points_2d,
    v_add,
    v_dist_2d,
    v_dist_3d,
    v_len,
    v_scale,
    v_sub,
)


# ===========================================================================
# 1. From Scratch – Płaska siatka TIN
# ===========================================================================

def generate_flat_grid(
    size_x: float,
    size_y: float,
    spacing: float,
    base_z: float = 0.0,
    pattern: str = "alternating",
) -> list[Triangle]:
    """
    Tworzy prostokątną siatkę TIN o wymiarach size_x × size_y z rozstawem spacing.
    Układ przekątnych:
    - 'alternating': naprzemienne przekątne (diamond pattern - styl SketchUp),
      co zapobiega asymetrii przy rzeźbieniu pędzlem Smoove.
    - 'uniform': jednolite przekątne (/).
    """
    if spacing <= 0.0:
        raise ValueError(f"Rozstaw siatki musi być > 0, otrzymano: {spacing}")
    if size_x <= 0.0 or size_y <= 0.0:
        raise ValueError(f"Wymiary muszą być dodatnie ({size_x} × {size_y})")

    cols = max(1, int(math.ceil(size_x / spacing)))
    rows = max(1, int(math.ceil(size_y / spacing)))

    triangles: list[Triangle] = []

    for r in range(rows):
        for c in range(cols):
            x0 = c * spacing
            y0 = r * spacing
            x1 = min(x0 + spacing, size_x)
            y1 = min(y0 + spacing, size_y)

            bl: Point3D = (x0, y0, base_z)
            br: Point3D = (x1, y0, base_z)
            tr: Point3D = (x1, y1, base_z)
            tl: Point3D = (x0, y1, base_z)

            # Wybór przekątnej
            if pattern == "alternating" and (r + c) % 2 == 1:
                # Przekątna br–tl
                triangles.append([bl, br, tl])
                triangles.append([br, tr, tl])
            else:
                # Przekątna bl–tr
                triangles.append([bl, br, tr])
                triangles.append([bl, tr, tl])

    return triangles


# ===========================================================================
# 2. From Contours – Generowanie terenu z warstwic
# ===========================================================================

def build_terrain_from_contours(
    contour_curves: Sequence[Sequence[Point3D]],
    max_segment_len: float = 4.0,
    prune_boundary_ratio: float = 3.5,
) -> list[Triangle]:
    """
    Tworzy ciągłą siatkę terenu TIN ze zbioru krzywych/polilinii warstwic.
    1. Adaptacyjnie densyfikuje długie segmenty krzywych.
    2. Wykonuje triangulację Delaunaya w rzucie XY.
    3. Przycina nadmiarowe trójkąty na zewnętrznych wklęsłościach brzegu.
    """
    all_points: list[Point3D] = []

    for curve in contour_curves:
        pts = list(curve)
        if len(pts) < 2:
            all_points.extend(pts)
            continue

        for i in range(len(pts) - 1):
            p0 = pts[i]
            p1 = pts[i + 1]
            seg_len = v_dist_3d(p0, p1)
            all_points.append(p0)

            # Densyfikacja jeśli segment jest za długi
            if max_segment_len > 0.0 and seg_len > max_segment_len:
                num_subdiv = int(math.ceil(seg_len / max_segment_len))
                for s in range(1, num_subdiv):
                    t = s / num_subdiv
                    inter_pt = (
                        p0[0] + (p1[0] - p0[0]) * t,
                        p0[1] + (p1[1] - p0[1]) * t,
                        p0[2] + (p1[2] - p0[2]) * t,
                    )
                    all_points.append(inter_pt)

        all_points.append(pts[-1])

    if len(all_points) < 3:
        return []

    # Oblicz średnią długość krawędzi do kryterium przycinania brzegu
    avg_len = max_segment_len if max_segment_len > 0.0 else 5.0
    cutoff = avg_len * prune_boundary_ratio if prune_boundary_ratio > 0.0 else None

    # Triangulacja Delaunaya
    triangles = triangulate_points_2d(all_points, max_edge_len=cutoff)
    return triangles


# ===========================================================================
# 3. Stamp – Odcisk w terenie (Półka + Skarpa przejściowa)
# ===========================================================================

def build_stamp_geometry(
    footprint_pts_3d: list[Point3D],
    terrain_triangles: list[Triangle],
    offset_dist: float,
    target_elevation: float | None = None,
) -> tuple[list[Triangle], list[Triangle], list[Triangle], float, float, float]:
    """
    Tworzy geometrię odcisku (Stamp) w terenie:
    1. Oblicza obrys poduszki/półki (pad) oraz odsunięcie skarpy (outer_poly).
    2. Dokonuje RZECZYWISTEGO wycięcia geometrii (CSG Mesh Cut) w siatce terenu
       wzdłuż zewnętrznej linii skarpy, interpolując rzędne Z na krawędzi cięcia.
    3. Generuje trójkąty płaskiej półki na zadanym poziomie Z.
    4. Generuje trójkąty skarpy (batter slopes) płynnie łączące brzeg półki z wyciętym terenem.
    5. Zwraca: (wszystkie_trójkąty, trójkąty_półki, trójkąty_skarpy, cut_m3, fill_m3, net_m3)
    """
    poly_2d: list[Point2D] = [(p[0], p[1]) for p in footprint_pts_3d]
    poly_2d = ensure_ccw_2d(poly_2d)

    # 1. Określ poziom posadowienia Z jeśli nie podano jawnie
    if target_elevation is None:
        elevations = []
        for pt in poly_2d:
            for tri in terrain_triangles:
                z = point_z_on_triangle(pt[0], pt[1], tri)
                if z is not None:
                    elevations.append(z)
                    break
        target_elevation = (sum(elevations) / len(elevations)) if elevations else footprint_pts_3d[0][2]

    # 2. Oblicz obwiednię skarpy (outer offset polygon)
    outer_poly_2d = offset_polygon_2d(poly_2d, offset_dist)
    outer_poly_2d = ensure_ccw_2d(outer_poly_2d)

    # 3. Prawdziwe geometryczne cięcie terenu (Mesh Boolean Cut)
    # Wszystkie trójkąty przecinające outer_poly_2d zostają precyzyjnie docięte do brzegu!
    retained_terrain: list[Triangle] = []
    for tri in terrain_triangles:
        out_tris, _in_tris = cut_triangle_by_polygon_both_2d(tri, outer_poly_2d)
        retained_terrain.extend(out_tris)

    # 4. Trójkąty płaskiej półki (pad) na poziomie target_elevation
    pad_triangles: list[Triangle] = []
    try:
        from shapely.geometry import Polygon  # type: ignore
        import shapely.ops  # type: ignore
        sh_pad = Polygon(poly_2d)
        if not sh_pad.is_valid:
            sh_pad = sh_pad.buffer(0)
        for t in shapely.ops.triangulate(sh_pad):
            if sh_pad.covers(t.representative_point()):
                c = list(t.exterior.coords)[:-1]
                if len(c) == 3:
                    tri3d = [(pt[0], pt[1], float(target_elevation)) for pt in c]
                    pad_triangles.append(ensure_ccw_tri(tri3d))
    except Exception:
        pad_pts_3d: list[Point3D] = [(pt[0], pt[1], float(target_elevation)) for pt in poly_2d]
        pad_triangles = triangulate_points_2d(pad_pts_3d)

    # 5. Trójkąty skarpy (przejście między outer_poly_2d a poly_2d)
    slope_triangles: list[Triangle] = []
    try:
        from shapely.geometry import Point, Polygon  # type: ignore
        import shapely.ops  # type: ignore
        sh_outer = Polygon(outer_poly_2d)
        sh_inner = Polygon(poly_2d)
        if not sh_outer.is_valid:
            sh_outer = sh_outer.buffer(0)
        if not sh_inner.is_valid:
            sh_inner = sh_inner.buffer(0)

        slope_poly = sh_outer.difference(sh_inner)
        sub_slope_polys = getattr(slope_poly, "geoms", [slope_poly])

        for sp in sub_slope_polys:
            if not isinstance(sp, Polygon) or sp.area < 1e-8:
                continue
            raw_tris = shapely.ops.triangulate(sp)
            for rt in raw_tris:
                if sp.covers(rt.representative_point()):
                    coords = list(rt.exterior.coords)[:-1]
                    if len(coords) == 3:
                        t3d = []
                        for pt in coords:
                            p_pt = Point(pt)
                            d_inner = p_pt.distance(sh_inner.boundary)
                            d_outer = p_pt.distance(sh_outer.boundary)
                            total_d = d_inner + d_outer
                            factor = (d_inner / total_d) if total_d > 1e-9 else 0.0

                            # Wysokość terenu pierwotnego w punkcie pt
                            z_orig = None
                            for tri in terrain_triangles:
                                z_test = point_z_on_triangle(pt[0], pt[1], tri)
                                if z_test is not None:
                                    z_orig = z_test
                                    break
                            if z_orig is None:
                                z_orig = float(target_elevation)

                            # Płynne przejście wysokości
                            z_interp = (1.0 - factor) * float(target_elevation) + factor * z_orig
                            t3d.append((pt[0], pt[1], z_interp))
                        slope_triangles.append(ensure_ccw_tri(t3d))
    except Exception:
        # Awaryjny fallback triangulacji pasma
        pass

    # 6. Oblicz bilans mas ziemnych (Cut & Fill)
    new_stamp_tris = pad_triangles + slope_triangles
    cut_vol = 0.0
    fill_vol = 0.0

    for tri in new_stamp_tris:
        area_2d = abs(signed_area_2d(tri))
        cx = (tri[0][0] + tri[1][0] + tri[2][0]) / 3.0
        cy = (tri[0][1] + tri[1][1] + tri[2][1]) / 3.0
        z_new = (tri[0][2] + tri[1][2] + tri[2][2]) / 3.0

        z_old = None
        for otri in terrain_triangles:
            z = point_z_on_triangle(cx, cy, otri)
            if z is not None:
                z_old = z
                break

        if z_old is not None:
            dz = z_new - z_old
            if dz > 0.001:
                fill_vol += area_2d * dz
            elif dz < -0.001:
                cut_vol += area_2d * abs(dz)

    net_vol = fill_vol - cut_vol
    final_terrain = retained_terrain + new_stamp_tris
    return (final_terrain, pad_triangles, slope_triangles, cut_vol, fill_vol, net_vol)


# ===========================================================================
# 4. Drape – Rzutowanie i wycinanie geometrii w terenie
# ===========================================================================

def build_drape_geometry(
    drape_curves_3d: list[list[Point3D]],
    terrain_triangles: list[Triangle],
    road_width: float = 0.0,
) -> tuple[list[Triangle], list[Triangle]]:
    """
    Rzutuje linie lub obrysy dróg na siatkę terenu:
    - Jeśli road_width > 0: tworzy wstęgę drogi i kroi siatkę terenu tak, że
      droga staje się osobną grupą ścianek w siatce (z materiałem drogowym).
      Zwraca: (trójkąty_terenu_poza_drogą, trójkąty_pasa_drogi)
    - Jeśli road_width == 0: rozcina trójkąty terenu wzdłuż linii rzutowania,
      osadzając rzutowane krawędzie wierzchołek po wierzchołku w siatce terenu.
      Zwraca: (wszystkie_rozcięte_trójkąty_terenu, [])
    """
    if not drape_curves_3d or not terrain_triangles:
        return (list(terrain_triangles), [])

    if road_width > 0.0:
        # 1. Tryb wstęgi drogi (wielokąt bufora)
        try:
            from shapely.geometry import LineString, Polygon  # type: ignore
            from shapely.ops import unary_union  # type: ignore
            lines = [LineString([(p[0], p[1]) for p in c]) for c in drape_curves_3d if len(c) >= 2]
            if not lines:
                return (list(terrain_triangles), [])
            road_buffer = unary_union([l.buffer(road_width * 0.5, cap_style="flat", join_style="mitre") for l in lines])
            road_polys = getattr(road_buffer, "geoms", [road_buffer])

            non_road_tris: list[Triangle] = []
            road_tris: list[Triangle] = []

            for tri in terrain_triangles:
                curr_outs = [tri]
                curr_ins = []
                for rp in road_polys:
                    if not isinstance(rp, Polygon) or rp.area < 1e-8:
                        continue
                    coords = list(rp.exterior.coords)[:-1]
                    next_outs = []
                    for ot in curr_outs:
                        o_sub, i_sub = cut_triangle_by_polygon_both_2d(ot, coords)
                        next_outs.extend(o_sub)
                        curr_ins.extend(i_sub)
                    curr_outs = next_outs

                non_road_tris.extend(curr_outs)
                road_tris.extend(curr_ins)

            return (non_road_tris, road_tris)
        except Exception:
            return (list(terrain_triangles), [])
    else:
        # 2. Tryb cięcia wzdłuż linii rzutowania (linia staje się krawędzią siatki)
        drape_lines_2d = [[(p[0], p[1]) for p in c] for c in drape_curves_3d if len(c) >= 2]
        draped_terrain: list[Triangle] = []

        for tri in terrain_triangles:
            sub_tris = split_triangle_by_lines_2d(tri, drape_lines_2d)
            draped_terrain.extend(sub_tris)

        return (draped_terrain, [])


# ===========================================================================
# 4. Add Detail – Podział trójkątów (1-do-4 Midpoint Subdivision)
# ===========================================================================

def subdivide_triangles_midpoint(
    triangles: Sequence[Triangle],
    target_indices: Sequence[int] | None = None,
) -> list[Triangle]:
    """
    Dzieli każdy wskazany trójkąt na 4 mniejsze przez punkty środkowe krawędzi.
    Zachowuje ciągłość topologiczną wierzchołków.
    """
    subdivided: list[Triangle] = []
    indices_set = set(target_indices) if target_indices is not None else None

    # Słownik punktów środkowych krawędzi dla spójności
    edge_midpoints: dict[tuple[int, int, int, int], Point3D] = {}

    def get_midpoint(p1: Point3D, p2: Point3D) -> Point3D:
        # Normalizowany klucz krawędzi
        k1 = (int(round(p1[0] * 1000)), int(round(p1[1] * 1000)), int(round(p1[2] * 1000)))
        k2 = (int(round(p2[0] * 1000)), int(round(p2[1] * 1000)), int(round(p2[2] * 1000)))
        ekey = (min(k1, k2), max(k1, k2))
        if ekey not in edge_midpoints:
            edge_midpoints[ekey] = (
                (p1[0] + p2[0]) * 0.5,
                (p1[1] + p2[1]) * 0.5,
                (p1[2] + p2[2]) * 0.5,
            )
        return edge_midpoints[ekey]

    for idx, tri in enumerate(triangles):
        if indices_set is not None and idx not in indices_set:
            subdivided.append(tri)
            continue

        v0, v1, v2 = tri[0], tri[1], tri[2]
        m01 = get_midpoint(v0, v1)
        m12 = get_midpoint(v1, v2)
        m20 = get_midpoint(v2, v0)

        # 4 trójkąty o orientacji CCW
        subdivided.append([v0, m01, m20])
        subdivided.append([v1, m12, m01])
        subdivided.append([v2, m20, m12])
        subdivided.append([m01, m12, m20])

    return subdivided


def add_detail_at_point(
    triangles: list[Triangle],
    attrs: list[dict],
    click_pt: Point3D,
    pick_radius: float = 15.0,
    bisect_neighbors: bool = True,
) -> tuple[list[Triangle], list[dict], bool]:
    """
    Interactively subdivides the triangle or edge nearest to click_pt into smaller triangles.
    If bisect_neighbors is True, neighboring triangles sharing subdivided edges
    are bisected (1-to-2) to prevent T-junctions (cracks/hanging vertices).
    Returns: (new_triangles, new_attrs, success)
    """
    if not triangles:
        return triangles, attrs, False

    def p_key(p: Point3D) -> tuple[int, int, int]:
        return (int(round(p[0] * 1000)), int(round(p[1] * 1000)), int(round(p[2] * 1000)))

    def p_mid(a: Point3D, b: Point3D) -> Point3D:
        return ((a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5, (a[2] + b[2]) * 0.5)

    target_idx = None
    min_dist = float("inf")
    closest_idx = None

    for idx, tri in enumerate(triangles):
        if point_in_polygon_2d(click_pt, tri):
            target_idx = idx
            break
        cx = (tri[0][0] + tri[1][0] + tri[2][0]) / 3.0
        cy = (tri[0][1] + tri[1][1] + tri[2][1]) / 3.0
        cz = (tri[0][2] + tri[1][2] + tri[2][2]) / 3.0
        d = math.hypot(click_pt[0] - cx, click_pt[1] - cy)
        if d < min_dist:
            min_dist = d
            closest_idx = idx

    if target_idx is None:
        if closest_idx is None or min_dist > pick_radius:
            return triangles, attrs, False
        target_idx = closest_idx

    target_tri = triangles[target_idx]
    target_attr = attrs[target_idx] if target_idx < len(attrs) else {}

    v0, v1, v2 = target_tri[0], target_tri[1], target_tri[2]
    m01 = p_mid(v0, v1)
    m12 = p_mid(v1, v2)
    m20 = p_mid(v2, v0)

    # 4 new triangles for the target (CCW)
    new_sub = [
        ensure_ccw_tri([v0, m01, m20]),
        ensure_ccw_tri([v1, m12, m01]),
        ensure_ccw_tri([v2, m20, m12]),
        ensure_ccw_tri([m01, m12, m20]),
    ]
    new_sub_attrs = [dict(target_attr) for _ in range(4)]

    # Edge midpoints for bisection
    k0, k1, k2 = p_key(v0), p_key(v1), p_key(v2)
    edge_splits = {
        (min(k0, k1), max(k0, k1)): m01,
        (min(k1, k2), max(k1, k2)): m12,
        (min(k2, k0), max(k2, k0)): m20,
    }

    result_tris: list[Triangle] = []
    result_attrs: list[dict] = []

    for idx, tri in enumerate(triangles):
        at = attrs[idx] if idx < len(attrs) else {}
        if idx == target_idx:
            result_tris.extend(new_sub)
            result_attrs.extend(new_sub_attrs)
            continue

        if not bisect_neighbors:
            result_tris.append(tri)
            result_attrs.append(at)
            continue

        # Check if tri shares one of the split edges
        split_found = False
        for i in range(3):
            ea = tri[i]
            eb = tri[(i + 1) % 3]
            ekey = (min(p_key(ea), p_key(eb)), max(p_key(ea), p_key(eb)))
            if ekey in edge_splits:
                mid_pt = edge_splits[ekey]
                v_opp = tri[(i + 2) % 3]
                t_a = ensure_ccw_tri([ea, mid_pt, v_opp])
                t_b = ensure_ccw_tri([mid_pt, eb, v_opp])
                result_tris.extend([t_a, t_b])
                result_attrs.extend([dict(at), dict(at)])
                split_found = True
                break

        if not split_found:
            result_tris.append(tri)
            result_attrs.append(at)

    return result_tris, result_attrs, True


# ===========================================================================
# 5. Flip Edge – Odwracanie przekątnej czworokąta w siatce TIN
# ===========================================================================

def point_to_segment_dist_3d(p: Point3D, a: Point3D, b: Point3D) -> float:
    """Oblicza najmniejszą odległość euklidesową od punktu P do odcinka 3D [A, B]."""
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    ap = (p[0] - a[0], p[1] - a[1], p[2] - a[2])
    l2 = ab[0] * ab[0] + ab[1] * ab[1] + ab[2] * ab[2]
    if l2 < 1e-12:
        return math.dist(p, a)
    t = max(0.0, min(1.0, (ap[0] * ab[0] + ap[1] * ab[1] + ap[2] * ab[2]) / l2))
    closest = (a[0] + t * ab[0], a[1] + t * ab[1], a[2] + t * ab[2])
    return math.dist(p, closest)


def find_closest_interior_edge(
    triangles: Sequence[Triangle],
    click_pt: Point3D,
    pick_radius: float = 8.0,
) -> tuple[tuple[Point3D, Point3D], tuple[Point3D, Point3D], bool] | None:
    """
    Wyszukuje wewnętrzną krawędź terenu położoną najbliżej punktu click_pt.
    Zwraca: ((ea, eb), (opp0, opp1), is_convex) lub None jeśli brak krawędzi w zasięgu.
    """
    def p_key(p: Point3D) -> tuple[int, int]:
        return (int(round(p[0] * 1000)), int(round(p[1] * 1000)))

    edges_to_tris: dict[tuple[int, int, int, int], list[int]] = {}
    edges_coords: dict[tuple[int, int, int, int], tuple[Point3D, Point3D]] = {}

    for t_idx, tri in enumerate(triangles):
        for i in range(3):
            p_a = tri[i]
            p_b = tri[(i + 1) % 3]
            ka = p_key(p_a)
            kb = p_key(p_b)
            ekey = (min(ka, kb)[0], min(ka, kb)[1], max(ka, kb)[0], max(ka, kb)[1])
            if ekey not in edges_to_tris:
                edges_to_tris[ekey] = []
                edges_coords[ekey] = (p_a, p_b)
            edges_to_tris[ekey].append(t_idx)

    best_dist = float("inf")
    best_candidate = None

    for ekey, tri_list in edges_to_tris.items():
        if len(tri_list) != 2:
            continue
        ea, eb = edges_coords[ekey]
        d = point_to_segment_dist_3d(click_pt, ea, eb)
        if d < best_dist and d <= pick_radius:
            t0 = triangles[tri_list[0]]
            t1 = triangles[tri_list[1]]
            opp0_list = [v for v in t0 if p_key(v) != p_key(ea) and p_key(v) != p_key(eb)]
            opp1_list = [v for v in t1 if p_key(v) != p_key(ea) and p_key(v) != p_key(eb)]
            if opp0_list and opp1_list:
                opp0 = opp0_list[0]
                opp1 = opp1_list[0]
                is_convex = _segments_intersect_2d(opp0, opp1, ea, eb)
                best_dist = d
                best_candidate = ((ea, eb), (opp0, opp1), is_convex)

    return best_candidate


def flip_mesh_edge(
    triangles: list[Triangle],
    click_pt: Point3D,
    pick_radius: float = 8.0,
) -> tuple[list[Triangle], bool]:
    """
    Znajduje krawędź najbliższą punktowi click_pt współdzieloną przez 2 trójkąty.
    Jeśli czworokąt jest wypukły, odwraca przekątną.
    Zwraca: (zaktualizowana_lista_trójkątów, czy_sukces)
    """
    def p_key(p: Point3D) -> tuple[int, int]:
        return (int(round(p[0] * 1000)), int(round(p[1] * 1000)))

    edges_to_tris: dict[tuple[int, int, int, int], list[int]] = {}
    edges_coords: dict[tuple[int, int, int, int], tuple[Point3D, Point3D]] = {}

    for t_idx, tri in enumerate(triangles):
        for i in range(3):
            p_a = tri[i]
            p_b = tri[(i + 1) % 3]
            ka = p_key(p_a)
            kb = p_key(p_b)
            ekey = (min(ka, kb)[0], min(ka, kb)[1], max(ka, kb)[0], max(ka, kb)[1])
            if ekey not in edges_to_tris:
                edges_to_tris[ekey] = []
                edges_coords[ekey] = (p_a, p_b)
            edges_to_tris[ekey].append(t_idx)

    best_dist = float("inf")
    best_pair: tuple[int, int] | None = None
    best_edge_pts: tuple[Point3D, Point3D] | None = None

    for ekey, tri_list in edges_to_tris.items():
        if len(tri_list) != 2:
            continue
        ea, eb = edges_coords[ekey]
        d = point_to_segment_dist_3d(click_pt, ea, eb)
        if d < best_dist and d <= pick_radius:
            best_dist = d
            best_pair = (tri_list[0], tri_list[1])
            best_edge_pts = (ea, eb)

    if best_pair is None or best_edge_pts is None:
        return (triangles, False)

    t0_idx, t1_idx = best_pair
    t0 = triangles[t0_idx]
    t1 = triangles[t1_idx]
    ea, eb = best_edge_pts

    opp0_list = [v for v in t0 if p_key(v) != p_key(ea) and p_key(v) != p_key(eb)]
    opp1_list = [v for v in t1 if p_key(v) != p_key(ea) and p_key(v) != p_key(eb)]
    if not opp0_list or not opp1_list:
        return (triangles, False)

    opp0 = opp0_list[0]
    opp1 = opp1_list[0]

    # Sprawdź czy nowa przekątna opp0–opp1 przecina starą ea–eb w 2D (wypukłość czworokąta)
    if not _segments_intersect_2d(opp0, opp1, ea, eb):
        return (triangles, False)

    # Utwórz dwa nowe trójkąty z odwróconą przekątną
    tri_a = [opp0, ea, opp1]
    tri_b = [opp0, opp1, eb]

    # Zapewnij orientację CCW
    if signed_area_2d(tri_a) < 0.0:
        tri_a = [tri_a[0], tri_a[2], tri_a[1]]
    if signed_area_2d(tri_b) < 0.0:
        tri_b = [tri_b[0], tri_b[2], tri_b[1]]

    new_triangles = list(triangles)
    new_triangles[t0_idx] = tri_a
    new_triangles[t1_idx] = tri_b

    return (new_triangles, True)


def _segments_intersect_2d(p1: Point3D, p2: Point3D, p3: Point3D, p4: Point3D) -> bool:
    """Sprawdza właściwe przecięcie dwóch odcinków 2D wewnątrz ich długości."""
    def ccw(a, b, c):
        return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])
    return (ccw(p1, p3, p4) != ccw(p2, p3, p4)) and (ccw(p1, p2, p3) != ccw(p1, p2, p4))


# ===========================================================================
# 6. Statystyki terenu i Slicer Poziomic
# ===========================================================================

def calculate_mesh_statistics(triangles: Sequence[Triangle]) -> dict[str, float | int]:
    """Oblicza parametry geometryczne siatki terenu."""
    if not triangles:
        return {
            "face_count": 0, "vertex_count": 0,
            "area_3d": 0.0, "area_2d": 0.0,
            "min_z": 0.0, "max_z": 0.0, "delta_z": 0.0,
        }

    all_verts = set()
    area_3d = 0.0
    area_2d = 0.0
    min_z = float("inf")
    max_z = float("-inf")

    for tri in triangles:
        for v in tri:
            all_verts.add((int(round(v[0]*1000)), int(round(v[1]*1000)), int(round(v[2]*1000))))
            min_z = min(min_z, v[2])
            max_z = max(max_z, v[2])

        # Pole 2D
        area_2d += abs(signed_area_2d(tri))

        # Pole 3D (długość iloczynu wektorowego)
        e1 = v_sub(tri[1], tri[0])
        e2 = v_sub(tri[2], tri[0])
        area_3d += 0.5 * v_len(
            (
                e1[1] * e2[2] - e1[2] * e2[1],
                e1[2] * e2[0] - e1[0] * e2[2],
                e1[0] * e2[1] - e1[1] * e2[0],
            )
        )

    return {
        "face_count": len(triangles),
        "vertex_count": len(all_verts),
        "area_3d": area_3d,
        "area_2d": area_2d,
        "min_z": min_z if min_z != float("inf") else 0.0,
        "max_z": max_z if max_z != float("-inf") else 0.0,
        "delta_z": (max_z - min_z) if min_z != float("inf") else 0.0,
    }


def generate_terrain_contours(
    triangles: Sequence[Triangle],
    interval_z: float = 1.0,
) -> list[list[Point3D]]:
    """
    Kroi trójwymiarową siatkę terenu płaszczyznami poziomymi Z = k * interval_z
    i generuje odcinki warstwic (poziomic).
    """
    if interval_z <= 0.0 or not triangles:
        return []

    stats = calculate_mesh_statistics(triangles)
    min_z = float(stats["min_z"])
    max_z = float(stats["max_z"])

    k_start = int(math.floor(min_z / interval_z)) + 1
    k_end = int(math.floor(max_z / interval_z))

    contour_segments: list[list[Point3D]] = []

    for k in range(k_start, k_end + 1):
        target_z = k * interval_z
        for tri in triangles:
            # Sprawdź które krawędzie trójkąta przecinają poziom target_z
            pts_intersect: list[Point3D] = []
            for i in range(3):
                p0 = tri[i]
                p1 = tri[(i + 1) % 3]
                z0, z1 = p0[2], p1[2]

                if (z0 <= target_z <= z1) or (z1 <= target_z <= z0):
                    if abs(z1 - z0) > 1e-9:
                        t = (target_z - z0) / (z1 - z0)
                        ix = p0[0] + (p1[0] - p0[0]) * t
                        iy = p0[1] + (p1[1] - p0[1]) * t
                        pts_intersect.append((ix, iy, target_z))

            if len(pts_intersect) >= 2:
                contour_segments.append([pts_intersect[0], pts_intersect[1]])

    return contour_segments
