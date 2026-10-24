# SPDX-License-Identifier: GPL-3.0-or-later
"""
IngeGroundBox: GroundBox Terrain Modeling Plugin for IngeTrazo.
Advanced Engineering & BIM Triangulated Irregular Network (TIN) modeling:
1. From Scratch (Od podstaw)
2. From Contours (Z warstwic)
3. Smoove (Wytłaczanie / Rzeźbienie)
4. Stamp (Odcisk platformy i skarpy)
5. Drape (Rzutowanie dróg i ścieżek)
6. Add Detail (Dodaj detal / Zagęszczanie siatki)
7. Flip Edge (Odwróć krawędź)
"""
import logging
from pathlib import Path
import sys

log = logging.getLogger("ingetrazo.plugins.inge_groundbox")

_PLUGIN_DIR = str(Path(__file__).resolve().parent)
if _PLUGIN_DIR not in sys.path:
    sys.path.insert(0, _PLUGIN_DIR)

try:
    from inge_groundbox import (
        AddDetailTool,
        DrapeTool,
        FlipEdgeTool,
        FromScratchTool,
        SmooveTool,
        StampTool,
        setup,
    )
except Exception as e:
    log.exception(f"IngeGroundBox: Error loading package inge_groundbox / Błąd ładowania: {e}")
    raise
