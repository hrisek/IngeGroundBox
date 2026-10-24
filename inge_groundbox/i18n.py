# SPDX-License-Identifier: GPL-3.0-or-later
"""
inge_groundbox/i18n.py
====================
Dual-language interface localization (English EN [default] and Polish PL).
"""
from __future__ import annotations

# English is the default language across the plugin
_current_lang = "en"


def get_system_lang() -> str:
    """Returns the active plugin language (defaults to 'en')."""
    return _current_lang


def set_lang(lang: str) -> None:
    """Sets the active plugin language ('en' or 'pl')."""
    global _current_lang
    if lang in ("en", "pl"):
        _current_lang = lang


def get_lang() -> str:
    return _current_lang


TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        # Titles & Menus
        "plugin_title": "GroundBox Terrain",
        "menu_groundbox": "GroundBox Terrain",
        "menu_sandbox": "GroundBox Terrain",
        "toolbar_name": "GroundBox",
        "panel_title": "GroundBox",
        "lang_selector_label": "Language / Język:",
        "open_panel_tooltip": "Open GroundBox side panel",

        # Tools: Names & Descriptions
        "tool_from_scratch": "From Scratch",
        "tool_from_scratch_desc": "Generates a flat rectangular terrain TIN mesh with specified spacing.",
        "tool_from_contours": "From Contours",
        "tool_from_contours_desc": "Generates a 3D terrain TIN mesh from selected contour lines.",
        "tool_smoove": "Smoove",
        "tool_smoove_desc": "Smoothly sculpts terrain in Z axis using a brush with soft cosine falloff.",
        "tool_stamp": "Stamp",
        "tool_stamp_desc": "Stamps a building footprint into terrain, creating a flat pad and batter slopes.",
        "tool_drape": "Drape",
        "tool_drape_desc": "Projects lines, paths, or roads vertically onto the terrain surface.",
        "tool_add_detail": "Add Detail",
        "tool_add_detail_desc": "Subdivides selected triangles or clicked edges to increase resolution.",
        "tool_flip_edge": "Flip Edge",
        "tool_flip_edge_desc": "Flips the diagonal between two adjacent triangles to control drainage and ridges.",

        # Panel Tabs
        "tab_from_scratch": "From Scratch",
        "tab_contours": "From Contours",
        "tab_smoove": "Smoove",
        "tab_stamp": "Stamp",
        "tab_drape": "Drape",
        "tab_mesh_ops": "TIN Mesh Edit",
        "tab_analysis": "Analysis & Report",

        # Tab 1: From Scratch Parameters
        "size_x_label": "Width X (m):",
        "size_y_label": "Length Y (m):",
        "spacing_label": "Grid Spacing (m):",
        "base_z_label": "Base Elevation Z (m):",
        "pattern_label": "Diagonal Pattern:",
        "pattern_alternating": "Alternating (Diamond / Checkerboard)",
        "pattern_uniform": "Uniform (Diagonal /)",
        "material_label": "Terrain Material:",
        "mat_grass": "Natural Grass",
        "mat_soil": "Soil / Ground",
        "mat_sand": "Sand",
        "mat_rock": "Rock",
        "btn_generate_scratch": "⬡  Generate Terrain Grid",
        "btn_scratch_tool": "📐  Draw Terrain Interactively (3 Clicks)",

        # Tab 2: From Contours Parameters
        "contours_info": "Select contour edges or polylines at various Z elevations, then click below.",
        "max_seg_len": "Max segment length (m):",
        "prune_boundary": "Prune long boundary triangles:",
        "soft_edges_label": "Smooth facet seams (Soft edges):",
        "btn_generate_contours": "〰  Create Terrain from Selected Contours",

        # Tab 3: Smoove Parameters
        "brush_radius": "Brush Radius (m):",
        "brush_strength": "Brush Strength:",
        "falloff_label": "Falloff Profile:",
        "falloff_cosine": "Cosine (Authentic SketchUp)",
        "falloff_gaussian": "Gaussian (Bell curve)",
        "falloff_linear": "Linear (Cone)",
        "falloff_smoothstep": "Smoothstep",
        "btn_activate_smoove": "🖌  Activate Smoove Tool",
        "smoove_hint": "Instructions: Click on terrain and drag up or down. Press Esc to cancel.",
        "smoove_direct_title": "Direct Height Extrusion (ΔZ):",
        "elevation_dz_label": "Height ΔZ:",
        "btn_smoove_direct": "Extrude Terrain by ΔZ",
        "btn_smoove_direct_hint": "Deforms selected terrain by specified height with chosen radius and falloff.",

        # Tab 4: Stamp Parameters
        "stamp_info": "1. Select footprint/face.\n2. Click Stamp.\n3. Click target terrain.",
        "offset_dist_label": "Slope offset distance (m):",
        "pad_elevation_label": "Pad elevation Z (m):",
        "auto_elev_check": "Automatic elevation (average under footprint)",
        "pad_material_label": "Pad material:",
        "slope_material_label": "Slope material:",
        "mat_concrete": "Concrete / Paving",
        "mat_terrace_tile": "Terrace Tile",
        "mat_crushed_stone": "Crushed Stone / Gravel",
        "mat_slope_ground": "Ground Slope / Soil",
        "mat_stones": "Field Stones / Rocks",
        "btn_apply_stamp": "🔲  Execute Stamp into Terrain",
        "btn_stamp_tool": "🔲  Activate Stamp Tool",

        # Tab 5: Drape Parameters
        "drape_info": "Select lines/edges above terrain, select the terrain group, and click below.",
        "road_width_label": "Road ribbon width (m):",
        "road_width_hint": "(0.0 = project lines directly, >0 = extrude road ribbon)",
        "drape_paint_check": "Paint area inside draped boundary",
        "drape_mat_label": "Road material:",
        "mat_asphalt": "Road Asphalt",
        "mat_paving": "Pavement / Cobblestone",
        "mat_gravel": "Gravel",
        "mat_path": "Park Path",
        "btn_apply_drape": "⬇  Drape Lines onto Terrain",
        "btn_drape_tool": "⬇  Activate Drape Tool",

        # Tab 6: Mesh Operations (TIN)
        "btn_flip_edge_tool": "🔄  Tool: Flip Edge",
        "btn_add_detail_tool": "➕  Tool: Add Detail (Click in Viewport)",
        "btn_subdivide_selection": "◬  Subdivide Selected Triangles (x4)",
        "btn_optimize_delaunay": "✨  Optimize Mesh (Delaunay Flip)",
        "mesh_ops_hint": "Flip Edge allows you to instantly fix ridges, valleys, and water flow directions.",

        # Tab 7: Analysis & Report
        "terrain_stats_title": "Terrain Metrics & Quantities",
        "stat_faces": "Triangle count:",
        "stat_vertices": "Vertex count:",
        "stat_3d_area": "True 3D surface area:",
        "stat_2d_area": "Planar 2D footprint area:",
        "stat_min_z": "Lowest point (Z min):",
        "stat_max_z": "Highest point (Z max):",
        "stat_height_diff": "Height difference (ΔZ):",
        "stat_cut_vol": "Cut volume:",
        "stat_fill_vol": "Fill volume:",
        "stat_avg_slope": "Average slope:",
        "stat_max_slope": "Maximum slope:",
        "stat_slope_band": "Slope band",
        "slope_band_1": "0 – 5% (Flat)",
        "slope_band_2": "5 – 10% (Gentle)",
        "slope_band_3": "10 – 15% (Moderate)",
        "slope_band_4": "15 – 20% (Rolling)",
        "slope_band_5": "20 – 30% (Steep)",
        "slope_band_6": "30 – 40% (Very Steep)",
        "slope_band_7": "40 – 50% (Embankment 1:2)",
        "slope_band_8": "50 – 70% (Embankment 1:1.5)",
        "slope_band_9": "70 – 100% (Slope 1:1)",
        "slope_band_10": "> 100% (Cliff / Wall >45°)",
        "slope_analysis_title": "Slope Analysis (Heatmap)",
        "btn_apply_slope": "🎨  Color Terrain by Slope",
        "btn_reset_colors": "↺  Reset Original Materials",
        "msg_slope_applied": "Applied slope heatmap analysis ({n} triangles, avg: {avg:.1f}%, max: {max:.1f}%).",
        "msg_colors_reset": "Terrain colors restored to original materials.",
        "err_title_slope": "GroundBox Error (Slope Analysis)",
        "skirt_box_title": "3D Solid Terrain (Watertight Skirt)",
        "skirt_depth_label": "Base depth offset (m):",
        "skirt_mat_label": "Base material:",
        "mat_soil_ground": "Soil / Ground",
        "mat_concrete_box": "Concrete Substructure",
        "btn_create_skirt": "📦  Create 3D Solid Base (Skirt)",
        "msg_skirt_created": "Created watertight 3D Solid terrain with skirt (Base Z = {z:.2f} m, +{walls} wall faces, +{caps} bottom faces).",
        "err_title_skirt": "GroundBox Error (3D Skirt)",
        "btn_refresh_stats": "Refresh Metrics",
        "btn_export_csv": "Export CSV Report",
        "btn_generate_terrain_contours": "Generate Contours from Terrain",
        "contour_interval": "Contour step (m):",

        # Dialogs & Export
        "btn_close": "Close",
        "table_prop_header": "Property / Metric",
        "table_val_header": "Value",
        "export_csv_title": "Save Terrain Report",
        "export_csv_success": "Report exported successfully to:\n{filename}",
        "export_csv_error": "Failed to save CSV file:\n{e}",

        # Status & Error Messages
        "msg_select_contours": "Please select contour lines or curves to build terrain.",
        "msg_select_contours_prompt": "No contour lines or edges selected.\n\nInstructions to create terrain from contours:\n1. Draw contour curves at different Z elevations (using Line or Arc tools).\n2. Select the drawn lines.\n3. Click 'Create Terrain from Contours'.",
        "msg_no_terrain": "No terrain group found. Please select a terrain or create one From Scratch.",
        "msg_terrain_created": "Terrain generated: {faces} triangles, {verts} vertices.",
        "msg_smoove_active": "Smoove active | R={r:.1f} m | Strength={s:.2f} | LMB+drag to sculpt",
        "msg_smoove_done": "Sculpting finished ({n} vertices updated).",
        "msg_select_terrain_smoove": "Select a terrain group to sculpt.",
        "msg_terrain_no_mesh": "Terrain group contains no mesh geometry.",
        "msg_smoove_direct_done": "Extruded terrain: moved {moved} vertices by {dz:+.2f} m.",
        "msg_select_footprint_terrain": "Select building footprint (closed face/polygon) and target terrain.",
        "msg_stamp_done": "Stamp applied successfully (Cut: {cut:.2f} m³, Fill: {fill:.2f} m³).",
        "msg_stamp_success_box": "Stamp applied successfully!\n\nCut: {cut:.2f} m³\nFill: {fill:.2f} m³\nNet balance: {net:+.2f} m³",
        "msg_select_drape_lines": "Select path lines (edges) and target terrain group.",
        "msg_drape_done": "Draped lines onto terrain: added {n} edges and split faces.",
        "msg_edge_flipped": "Edge diagonal flipped successfully.",
        "msg_edge_cannot_flip": "Edge cannot be flipped (not a convex quad).",
        "msg_flip_edge_hint": "Flip Edge: Click on an inner terrain edge to flip its diagonal.",
        "msg_detail_added": "Detail added: subdivided mesh into {n} triangles.",
        "msg_add_detail_active": "Add Detail active: Click on a terrain triangle or edge to subdivide it into 4.",
        "msg_detail_missed": "Click was outside terrain bounds.",
        "msg_optimized": "Optimized terrain via Delaunay flipping ({n} edges flipped).",
        "msg_no_contours_found": "No contours generated in specified elevation range.",
        "msg_contours_generated": "Generated {n} contour segments.",

        # Error Dialog Titles
        "err_title_scratch": "GroundBox Error (From Scratch)",
        "err_title_contours": "GroundBox Error (From Contours)",
        "err_title_smoove": "GroundBox Error (Smoove)",
        "err_title_stamp": "GroundBox Error (Stamp)",
        "err_title_drape": "GroundBox Error (Drape)",
        "err_title_detail": "GroundBox Error (Add Detail)",
        "err_title_contours_gen": "GroundBox Error (Contours)",

        # Additional Material & Status Labels
        "err_label": "Error",
        "msg_success_title": "Success",
        "stamp_result_title": "GroundBox: Stamp Result",
        "contours_group_name": "Contours (ΔZ={dz:.1f}m)",
        "msg_contours_failed": "Failed to create terrain. Ensure contour lines are selected.",
        "mat_slope_ground": "Ground Slope",
        "mat_stones": "Stones / Riprap",
        "vcb_radius": "Radius",
        "vcb_height": "Height",
        "vcb_offset": "Offset",
        "vcb_offset_z": "Z Offset",
        "vcb_grid": "Grid",
        "vcb_length": "Length",
        "vcb_width": "Width",

        # Interactive Viewport Tool Prompts
        "smoove_interactive_start": "Smoove: Click on terrain and drag up/down (radius {r:.2f} m - type a number to change).",
        "smoove_interactive_drag": "Smoove: Offset {dz:+.3f} m - click/release to confirm; type value + Enter; Esc = cancel.",
        "smoove_interactive_no_mesh": "Smoove: Click directly on terrain surface (mesh group).",
        "smoove_interactive_no_verts": "Smoove: No vertices within brush radius - increase radius or use Add Detail.",
        "smoove_interactive_cancel": "Smoove: Cancelled.",
        "smoove_interactive_done": "Smoove: Terrain moved by {dz:+.3f} m (Ctrl+Z to undo).",
        "stamp_interactive_pick_footprint": "Stamp: Click the footprint face (building/pad) you want to stamp.",
        "stamp_interactive_pick_terrain": "Stamp: Click terrain under footprint (batter offset {offset:.2f} m - type a number to change).",
        "stamp_interactive_hover": "Stamp: Pad elevation {pad_z:.3f} m - click to finish; type offset + Enter; Esc = cancel.",
        "stamp_interactive_done": "Stamp: Pad at {pad_z:.2f} m. Cut {cut:.2f} m³, Fill {fill:.2f} m³ (Ctrl+Z to undo).",
        "drape_interactive_no_sel": "Drape: First select edges or outline (e.g. plot/road), then choose Drape and click terrain.",
        "drape_interactive_ready": "Drape: {n} segments ready - click terrain to project onto.",
        "drape_interactive_done": "Drape: Embedded lines into terrain ({n} faces). Paint area using Paint Bucket (Ctrl+Z to undo).",
        "scratch_interactive_step1": "From Scratch (Step 1/3): Click origin point for terrain grid (Grid = {sp:.2f} m - type value + Enter to change).",
        "scratch_interactive_step2": "From Scratch (Step 2/3): Corner ({x:.1f}, {y:.1f}). Click second point (length/direction) or type length + Enter.",
        "scratch_interactive_step3": "From Scratch (Step 3/3): Length = {len_u:.2f} m. Drag width and click to create grid (or type width + Enter).",
        "scratch_interactive_done": "Created terrain grid: {w:.1f} m × {h:.1f} m (grid {sp:.2f} m, {n} triangles). Ctrl+Z to undo.",
    },
    "pl": {
        # Tytuły i menu
        "plugin_title": "GroundBox (Modelowanie Terenu)",
        "menu_groundbox": "GroundBox",
        "menu_sandbox": "GroundBox",
        "toolbar_name": "GroundBox",
        "panel_title": "GroundBox",
        "lang_selector_label": "Język / Language:",
        "open_panel_tooltip": "Otwórz boczny panel GroundBox",

        # Narzędzia - nazwy i opisy
        "tool_from_scratch": "Od podstaw (From Scratch)",
        "tool_from_scratch_desc": "Tworzy płaską, poziomą siatkę terenu o zadanym rozstawie i wymiarach.",
        "tool_from_contours": "Z warstwic (From Contours)",
        "tool_from_contours_desc": "Tworzy trójwymiarową siatkę terenu (TIN) z zaznaczonych linii warstwic.",
        "tool_smoove": "Wytłaczanie (Smoove)",
        "tool_smoove_desc": "Płynnie rzeźbi teren w osi Z za pomocą pędzla o zadanym promieniu (Smooth-Move).",
        "tool_stamp": "Pieczęć (Stamp)",
        "tool_stamp_desc": "Odciska obrys budynku lub płaszczyzny w terenie, tworząc półkę i skarpy przejściowe.",
        "tool_drape": "Rzutowanie (Drape)",
        "tool_drape_desc": "Rzutuje linie i ścieżki (drogi, chodniki, granice) pionowo na powierzchnię terenu.",
        "tool_add_detail": "Dodaj detal (Add Detail)",
        "tool_add_detail_desc": "Dzieli wybrane trójkąty lub krawędzie, zwiększając gęstość siatki do rzeźbienia.",
        "tool_flip_edge": "Odwróć krawędź (Flip Edge)",
        "tool_flip_edge_desc": "Odwraca przekątną między dwoma sąsiednimi trójkątami, zmieniając kierunek spływu/skarpy.",

        # Zakładki panelu
        "tab_from_scratch": "Od podstaw",
        "tab_contours": "Z warstwic",
        "tab_smoove": "Rzeźbienie (Smoove)",
        "tab_stamp": "Odcisk (Stamp)",
        "tab_drape": "Rzutowanie (Drape)",
        "tab_mesh_ops": "Edycja siatki (TIN)",
        "tab_analysis": "Analiza & Raport",

        # Parametry From Scratch
        "size_x_label": "Szerokość X (m):",
        "size_y_label": "Długość Y (m):",
        "spacing_label": "Rozstaw siatki (m):",
        "base_z_label": "Wysokość bazowa Z (m):",
        "pattern_label": "Układ przekątnych:",
        "pattern_alternating": "Naprzemienny (Diamond / Szachownica)",
        "pattern_uniform": "Jednolity (Ukośny /)",
        "material_label": "Materiał terenu:",
        "mat_grass": "Trawa naturalna",
        "mat_soil": "Ziemia / Grunt",
        "mat_sand": "Piasek",
        "mat_rock": "Skała",
        "btn_generate_scratch": "⬡  Generuj Siatkę Terenu",
        "btn_scratch_tool": "📐  Rysuj Teren Interaktywnie (3 Kliknięcia)",

        # Parametry From Contours
        "contours_info": "Zaznacz linie, polilinie lub łuki na różnych wysokościach Z, a następnie kliknij przycisk poniżej.",
        "max_seg_len": "Maks. długość segmentu (m):",
        "prune_boundary": "Odrzucaj dalekie krawędzie zewnętrzne:",
        "soft_edges_label": "Zmiękczaj łagodne krawędzie (Smooth shading):",
        "btn_generate_contours": "〰  Utwórz Teren z Zaznaczonych Warstwic",

        # Parametry Smoove
        "brush_radius": "Promień pędzla (m):",
        "brush_strength": "Siła rzeźbienia:",
        "falloff_label": "Profil opadania (Falloff):",
        "falloff_cosine": "Cosinus (Oryginał SketchUp)",
        "falloff_gaussian": "Gauss (Dzwon)",
        "falloff_linear": "Liniowy (Stożek)",
        "falloff_smoothstep": "Gładki (Smoothstep)",
        "btn_activate_smoove": "🖌  Aktywuj Narzędzie Smoove",
        "smoove_hint": "Instrukcja: Kliknij na teren i przeciągnij myszą w górę lub w dół. Wciśnij Esc aby anulować.",
        "smoove_direct_title": "Wytłaczanie o zadaną wysokość (ΔZ):",
        "elevation_dz_label": "Wysokość ΔZ:",
        "btn_smoove_direct": "Wytłocz teren o ΔZ",
        "btn_smoove_direct_hint": "Deformuje zaznaczony teren o zadaną wysokość z wybranym promieniem i profilem opadania.",

        # Parametry Stamp
        "stamp_info": "1. Zaznacz obrys budynku lub płaszczyznę.\n2. Kliknij Odcisk.\n3. Wskaż docelowy teren.",
        "offset_dist_label": "Szerokość skarpy / odsunięcie (m):",
        "pad_elevation_label": "Wysokość posadowienia Z (m):",
        "auto_elev_check": "Wysokość automatyczna (średnia terenu)",
        "pad_material_label": "Materiał półki:",
        "slope_material_label": "Materiał skarpy:",
        "mat_concrete": "Bruk / Beton",
        "mat_terrace_tile": "Płyta tarasowa",
        "mat_crushed_stone": "Szuter / Żwir",
        "mat_slope_ground": "Skarpa ziemna / Grunt",
        "mat_stones": "Kamienie / Narzut",
        "btn_apply_stamp": "🔲  Wykonaj Odcisk w Terenie",
        "btn_stamp_tool": "🔲  Aktywuj Narzędzie Odcisku",

        # Parametry Drape
        "drape_info": "Zaznacz linie ścieżki (lub drogę) nad terenem, zaznacz grupę terenu i kliknij poniżej.",
        "road_width_label": "Szerokość pasa drogowego (m):",
        "road_width_hint": "(0.0 = rzutowanie samej linii, >0 = wytłoczenie pasa drogowego)",
        "drape_paint_check": "Pomaluj obszar wewnątrz obrysu",
        "drape_mat_label": "Materiał drogi:",
        "mat_asphalt": "Asfalt drogowy",
        "mat_paving": "Bruk / Kostka",
        "mat_gravel": "Szuter / Żwir",
        "mat_path": "Ścieżka parkowa",
        "btn_apply_drape": "⬇  Rzutuj Linie na Teren (Drape)",
        "btn_drape_tool": "⬇  Aktywuj Narzędzie Rzutowania",

        # Edycja siatki (TIN)
        "btn_flip_edge_tool": "🔄  Narzędzie: Odwróć Krawędź (Flip Edge)",
        "btn_add_detail_tool": "➕  Narzędzie: Dodaj Detal (Kliknij w terenie)",
        "btn_subdivide_selection": "◬  Podziel Zaznaczone Trójkąty (x4)",
        "btn_optimize_delaunay": "✨  Optymalizuj Siatkę (Delaunay Flip)",
        "mesh_ops_hint": "Narzędzie 'Odwróć krawędź' pozwala natychmiast korygować grzbiety, doliny i kierunki spływu wody.",

        # Analiza i raport
        "terrain_stats_title": "Parametry i Statystyki Terenu",
        "stat_faces": "Liczba trójkątów:",
        "stat_vertices": "Liczba wierzchołków:",
        "stat_3d_area": "Powierzchnia rzeczywista 3D:",
        "stat_2d_area": "Powierzchnia w rzucie 2D:",
        "stat_min_z": "Najniższy punkt (Z min):",
        "stat_max_z": "Najwyższy punkt (Z max):",
        "stat_height_diff": "Różnica wysokości (ΔZ):",
        "stat_cut_vol": "Objętość wykopu (Cut):",
        "stat_fill_vol": "Objętość nasypu (Fill):",
        "stat_avg_slope": "Średni spadek:",
        "stat_max_slope": "Maksymalny spadek:",
        "stat_slope_band": "Przedział spadku",
        "slope_band_1": "0 – 5% (Płaski)",
        "slope_band_2": "5 – 10% (Łagodny)",
        "slope_band_3": "10 – 15% (Umiarkowany)",
        "slope_band_4": "15 – 20% (Średni)",
        "slope_band_5": "20 – 30% (Stromy)",
        "slope_band_6": "30 – 40% (Bardzo stromy)",
        "slope_band_7": "40 – 50% (Skarpa 1:2)",
        "slope_band_8": "50 – 70% (Skarpa 1:1.5)",
        "slope_band_9": "70 – 100% (Skarpa 1:1)",
        "slope_band_10": "> 100% (Urwisko / Mur >45°)",
        "slope_analysis_title": "Analiza spadków terenu (Heatmap)",
        "btn_apply_slope": "🎨  Pokoloruj wg spadków",
        "btn_reset_colors": "↺  Przywróć oryginalne materiały",
        "msg_slope_applied": "Zastosowano mapę spadków ({n} trójkątów, śr: {avg:.1f}%, maks: {max:.1f}%).",
        "msg_colors_reset": "Przywrócono oryginalne kolory i materiały terenu.",
        "err_title_slope": "Błąd GroundBox (Analiza spadków)",
        "skirt_box_title": "Zamknięcie bryły 3D (Cokół terenu)",
        "skirt_depth_label": "Głębokość cokołu (m):",
        "skirt_mat_label": "Materiał cokołu:",
        "mat_soil_ground": "Grunt / Podłoże",
        "mat_concrete_box": "Beton fundamentowy",
        "btn_create_skirt": "📦  Utwórz bryłę 3D (Cokół)",
        "msg_skirt_created": "Utworzono litą bryłę 3D terenu z cokołem (Spód Z = {z:.2f} m, +{walls} ścianek bocznych, +{caps} ścianek dna).",
        "err_title_skirt": "Błąd GroundBox (Bryła 3D)",
        "btn_refresh_stats": "Odśwież Statystyki",
        "btn_export_csv": "Eksportuj Raport do CSV",
        "btn_generate_terrain_contours": "Generuj Poziomice z Terenu (Contours)",
        "contour_interval": "Skok poziomic (m):",

        # Dialogi i eksport
        "btn_close": "Zamknij",
        "table_prop_header": "Właściwość / Parametr",
        "table_val_header": "Wartość",
        "export_csv_title": "Zapisz Raport Terenu",
        "export_csv_success": "Pomyślnie zapisano raport do:\n{filename}",
        "export_csv_error": "Nie udało się zapisać pliku CSV:\n{e}",

        # Komunikaty statusu i błędy
        "msg_select_contours": "Zaznacz krawędzie lub polilinie warstwic, aby utworzyć teren.",
        "msg_select_contours_prompt": "Nie zaznaczono żadnych krawędzi ani warstwic.\n\nInstrukcja tworzenia terenu z warstwic:\n1. Narysuj linie poziomic na różnych wysokościach Z (narzędziem Linia lub Łuk).\n2. Zaznacz narysowane linie.\n3. Kliknij 'Utwórz z warstwic'.",
        "msg_no_terrain": "Nie znaleziono grupy terenu w scenie. Zaznacz teren lub utwórz go z siatki.",
        "msg_terrain_created": "Utworzono teren: {faces} trójkątów, {verts} wierzchołków.",
        "msg_smoove_active": "Smoove aktywny | Promień={r:.1f} m | Siła={s:.2f} | LPM+przeciągnij = rzeźbienie",
        "msg_smoove_done": "Zakończono rzeźbienie terenu (zmodyfikowano {n} wierzchołków).",
        "msg_select_terrain_smoove": "Zaznacz grupę terenu, aby wytłoczyć jej rzeźbę.",
        "msg_terrain_no_mesh": "Grupa terenu nie zawiera siatki.",
        "msg_smoove_direct_done": "Wytłoczono teren: przesunięto {moved} wierzchołków o {dz:+.2f} m.",
        "msg_select_footprint_terrain": "Zaznacz obrys budynku (zamknięty wielokąt/ściankę) oraz grupę terenu.",
        "msg_stamp_done": "Pomyślnie odciśnięto obrys w terenie (Wykop: {cut:.2f} m³, Nasyp: {fill:.2f} m³).",
        "msg_stamp_success_box": "Pomyślnie wykonano odcisk w terenie!\n\nWykop: {cut:.2f} m³\nNasyp: {fill:.2f} m³\nBilans netto: {net:+.2f} m³",
        "msg_select_drape_lines": "Zaznacz linie ścieżki (krawędzie) oraz grupę terenu.",
        "msg_drape_done": "Zrzutowano linie na teren: dodano {n} krawędzi i podzielono płaszczyzny.",
        "msg_edge_flipped": "Pomyślnie odwrócono przekątną krawędzi.",
        "msg_edge_cannot_flip": "Krawędź nie może zostać odwrócona (nie tworzy wypukłego czworokąta).",
        "msg_flip_edge_hint": "Flip Edge: Kliknij na wewnętrzną krawędź terenu, aby odwrócić przekątną.",
        "msg_detail_added": "Zwiększono szczegółowość: podzielono siatkę na {n} trójkątów.",
        "msg_add_detail_active": "Dodaj detal aktywny: Kliknij na trójkąt w terenie, aby podzielić na 4 mniejsze.",
        "msg_detail_missed": "Kliknięto poza obszarem terenu.",
        "msg_optimized": "Zoptymalizowano siatkę metodą Delaunaya (odwrócono {n} krawędzi).",
        "msg_no_contours_found": "Brak poziomic w zadanym zakresie wysokości.",
        "msg_contours_generated": "Wygenerowano {n} odcinków poziomic.",

        # Tytuły błędów
        "err_title_scratch": "Błąd GroundBox (From Scratch)",
        "err_title_contours": "Błąd GroundBox (From Contours)",
        "err_title_smoove": "Błąd GroundBox (Smoove)",
        "err_title_stamp": "Błąd GroundBox (Stamp)",
        "err_title_drape": "Błąd GroundBox (Drape)",
        "err_title_detail": "Błąd GroundBox (Add Detail)",
        "err_title_contours_gen": "Błąd GroundBox (Poziomice)",

        # Dodatkowe etykiety materiałów i statusu
        "err_label": "Błąd",
        "msg_success_title": "Sukces",
        "stamp_result_title": "GroundBox: Wynik Odcisku (Stamp)",
        "contours_group_name": "Poziomice (ΔZ={dz:.1f}m)",
        "msg_contours_failed": "Nie udało się utworzyć terenu. Upewnij się, że zaznaczono linie warstwic.",
        "mat_slope_ground": "Skarpa gruntowa",
        "mat_stones": "Kamienie / Narzut",
        "vcb_radius": "Promień",
        "vcb_height": "Wysokość",
        "vcb_offset": "Odsunięcie",
        "vcb_offset_z": "Przesunięcie Z",
        "vcb_grid": "Siatka",
        "vcb_length": "Długość",
        "vcb_width": "Szerokość",

        # Komunikaty interaktywnych narzędzi viewportu
        "smoove_interactive_start": "Smoove: kliknij teren i przeciągnij w górę/dół (promień {r:.2f} m – wpisz liczbę, aby zmienić).",
        "smoove_interactive_drag": "Smoove: przesunięcie {dz:+.3f} m – kliknij/puść, aby zatwierdzić; wpisz wartość + Enter; Esc = anuluj.",
        "smoove_interactive_no_mesh": "Smoove: kliknij bezpośrednio na powierzchnię terenu (grupę z siatką).",
        "smoove_interactive_no_verts": "Smoove: w promieniu pędzla nie ma wierzchołków – zwiększ promień albo użyj Dodaj detal.",
        "smoove_interactive_cancel": "Smoove: anulowano.",
        "smoove_interactive_done": "Smoove: teren przesunięty o {dz:+.3f} m (Ctrl+Z cofa).",
        "stamp_interactive_pick_footprint": "Stamp: kliknij ściankę obrysu (budynek/półkę), który chcesz odcisnąć.",
        "stamp_interactive_pick_terrain": "Stamp: kliknij teren pod obrysem (odsunięcie skarpy {offset:.2f} m – wpisz liczbę, aby zmienić).",
        "stamp_interactive_hover": "Stamp: wysokość półki {pad_z:.3f} m – kliknij, aby zakończyć; wpisz przesunięcie + Enter; Esc = anuluj.",
        "stamp_interactive_done": "Stamp: półka na {pad_z:.2f} m. Wykop {cut:.2f} m³, nasyp {fill:.2f} m³ (Ctrl+Z cofa).",
        "drape_interactive_no_sel": "Drape: najpierw zaznacz krawędzie lub obrys, potem wybierz Drape i kliknij teren.",
        "drape_interactive_ready": "Drape: {n} odcinków gotowych – kliknij teren, na który mają zostać rzutowane.",
        "drape_interactive_done": "Drape: wszyto linie w teren ({n} ścianek). Obszar wewnątrz obrysu pomalujesz Wiadrem farby (Ctrl+Z cofa).",
        "scratch_interactive_step1": "Od podstaw (Krok 1/3): Kliknij punkt początkowy siatki terenu (Siatka = {sp:.2f} m – wpisz wartość + Enter, aby zmienić).",
        "scratch_interactive_step2": "Od podstaw (Krok 2/3): Narożnik ({x:.1f}, {y:.1f}). Kliknij drugi punkt (długość i kierunek) lub wpisz długość + Enter.",
        "scratch_interactive_step3": "Od podstaw (Krok 3/3): Długość = {len_u:.2f} m. Rozciągnij szerokość i kliknij, aby utworzyć siatkę (lub wpisz szerokość + Enter).",
        "scratch_interactive_done": "Utworzono siatkę terenu: {w:.1f} m × {h:.1f} m (siatka {sp:.2f} m, {n} trójkątów). Ctrl+Z cofa.",
    },
}


def tr(key: str, lang: str | None = None, **kwargs) -> str:
    """Retrieves localized text string with English as default fallback."""
    target_lang = lang or _current_lang
    d = TRANSLATIONS.get(target_lang, TRANSLATIONS["en"])
    txt = d.get(key, TRANSLATIONS["en"].get(key, key))
    if kwargs:
        try:
            return txt.format(**kwargs)
        except Exception:
            return txt
    return txt
