# SPDX-License-Identifier: GPL-3.0-or-later
"""
inge_groundbox/constants.py
=========================
Stałe, metadane pluginu, domyślne parametry i klasy BIM dla wtyczki GroundBox.
"""
from __future__ import annotations

PLUGIN_NAME = "GroundBox Terrain"
PLUGIN_KEY = "inge_groundbox"
PLUGIN_LEGACY_KEYS = ("inge_sandbox", "inge_groundbox")
PLUGIN_VERSION = "1.0.0"
PLUGIN_AUTHOR = "IngeTrazo Community"

# --- Tagi i klasy BIM IFC ---
IFC_CLASS_SITE = "IfcSite"
IFC_CLASS_GEOTECH = "IfcGeotechnicalStratum"
IFC_CLASS_EARTHWORKS = "IfcEarthworksFill"
IFC_CLASS_ROAD = "IfcRoad"

# --- Domyślne kolory podwójnych ścianek (Newell CCW awers/rewers) ---
# Trawa / Teren naturalny
COLOR_GRASS_FRONT = (0.42, 0.65, 0.32, 1.0)
COLOR_GRASS_BACK = (0.38, 0.58, 0.28, 1.0)

# Ziemia / Grunt
COLOR_SOIL_FRONT = (0.55, 0.44, 0.33, 1.0)
COLOR_SOIL_BACK = (0.48, 0.38, 0.28, 1.0)

# Piasek
COLOR_SAND_FRONT = (0.82, 0.75, 0.55, 1.0)
COLOR_SAND_BACK = (0.75, 0.68, 0.48, 1.0)

# Skała
COLOR_ROCK_FRONT = (0.60, 0.60, 0.62, 1.0)
COLOR_ROCK_BACK = (0.52, 0.52, 0.54, 1.0)

# Odcisk (Stamp) – płyta posadowienia / beton / tłuczeń
COLOR_PAD_FRONT = (0.72, 0.72, 0.74, 1.0)
COLOR_PAD_BACK = (0.65, 0.65, 0.67, 1.0)

# Skarpa (Stamp transition)
COLOR_SLOPE_FRONT = (0.48, 0.58, 0.35, 1.0)
COLOR_SLOPE_BACK = (0.42, 0.52, 0.30, 1.0)

# Droga / Ścieżka (Drape)
COLOR_ROAD_FRONT = (0.28, 0.28, 0.30, 1.0)
COLOR_ROAD_BACK = (0.24, 0.24, 0.26, 1.0)

# --- Domyślne parametry narzędzi ---
DEFAULT_FROM_SCRATCH = {
    "size_x": 60.0,
    "size_y": 60.0,
    "spacing": 3.0,
    "base_z": 0.0,
    "pattern": "alternating",  # "alternating" (diamond) lub "uniform"
    "material": "Trawa (Grass)",
}

DEFAULT_SMOOVE = {
    "radius": 10.0,
    "strength": 0.5,
    "falloff": "cosine",  # "cosine", "gaussian", "linear", "smoothstep"
}

DEFAULT_STAMP = {
    "offset_distance": 2.0,  # odsunięcie skarpy (m)
    "target_elevation": None,  # None = auto (średnia pod obrysem)
    "pad_material": "Bruk / Beton",
    "slope_material": "Skarpa gruntowa",
}

DEFAULT_DRAPE = {
    "road_width": 0.0,  # 0.0 = rzutowanie samych linii, >0 = pas drogowy o szerokości W
    "elevate_offset": 0.005,  # 5mm w górę aby uniknąć Z-fighting
    "material": "Asfalt / Droga",
}

DEFAULT_CONTOURS = {
    "max_segment_len": 5.0,  # maksymalna długość segmentu warstwicy przed densyfikacją
    "prune_boundary_ratio": 3.5,  # współczynnik odrzucania zbyt długich trójkątów na obrzeżach
    "soft_edges": True,
}
