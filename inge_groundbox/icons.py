# SPDX-License-Identifier: GPL-3.0-or-later
"""
inge_groundbox/icons.py
=====================
Wektorowe ikony SVG oraz generowanie QIcon dla paska narzędzi i menu w IngeTrazo.
Wszystkie ikony są osadzone bezpośrednio w kodzie – zero zewnętrznych plików graficznych.
"""
from __future__ import annotations

from typing import Any

# ===========================================================================
# Definicje wektorowe SVG dla 7 narzędzi GroundBox
# ===========================================================================

# 1. Główna ikona wtyczki GroundBox
SVG_GROUNDBOX_MAIN = """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <path d="M4 38 L24 8 L44 38 Z" fill="#4CAF50" stroke="#2E7D32" stroke-width="2"/>
  <path d="M24 8 L24 38 L44 38 Z" fill="#388E3C" opacity="0.6"/>
  <path d="M4 38 L24 24 L44 38" fill="none" stroke="#81C784" stroke-width="2"/>
  <circle cx="24" cy="8" r="3" fill="#FFC107"/>
</svg>"""

# 2. From Scratch (Siatka trójkątów)
SVG_FROM_SCRATCH = """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect x="6" y="6" width="36" height="36" rx="3" fill="#E8F5E9" stroke="#388E3C" stroke-width="2"/>
  <line x1="6" y1="24" x2="42" y2="24" stroke="#4CAF50" stroke-width="2"/>
  <line x1="24" y1="6" x2="24" y2="42" stroke="#4CAF50" stroke-width="2"/>
  <line x1="6" y1="24" x2="24" y2="6" stroke="#81C784" stroke-width="1.5" stroke-dasharray="3,2"/>
  <line x1="24" y1="42" x2="42" y2="24" stroke="#81C784" stroke-width="1.5" stroke-dasharray="3,2"/>
  <line x1="6" y1="24" x2="24" y2="42" stroke="#81C784" stroke-width="1.5" stroke-dasharray="3,2"/>
  <line x1="24" y1="6" x2="42" y2="24" stroke="#81C784" stroke-width="1.5" stroke-dasharray="3,2"/>
  <circle cx="24" cy="24" r="3" fill="#2E7D32"/>
</svg>"""

# 3. From Contours (Z warstwic)
SVG_FROM_CONTOURS = """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <path d="M4 40 C14 36, 20 42, 44 38" fill="none" stroke="#2E7D32" stroke-width="3"/>
  <path d="M6 28 C16 22, 26 30, 42 24" fill="none" stroke="#4CAF50" stroke-width="3"/>
  <path d="M10 16 C18 10, 28 18, 38 12" fill="none" stroke="#81C784" stroke-width="3"/>
  <line x1="12" y1="39" x2="16" y2="27" stroke="#A5D6A7" stroke-width="1.5"/>
  <line x1="24" y1="41" x2="26" y2="29" stroke="#A5D6A7" stroke-width="1.5"/>
  <line x1="26" y1="29" x2="28" y2="17" stroke="#A5D6A7" stroke-width="1.5"/>
  <line x1="38" y1="25" x2="36" y2="13" stroke="#A5D6A7" stroke-width="1.5"/>
  <circle cx="28" cy="14" r="2.5" fill="#FF9800"/>
</svg>"""

# 4. Smoove (Płynne rzeźbienie / Wytłaczanie)
SVG_SMOOVE = """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <ellipse cx="24" cy="36" rx="18" ry="7" fill="#C8E6C9" stroke="#4CAF50" stroke-width="2"/>
  <path d="M8 36 C12 36, 16 14, 24 14 C32 14, 36 36, 40 36" fill="#81C784" opacity="0.6" stroke="#2E7D32" stroke-width="2.5"/>
  <line x1="24" y1="22" x2="24" y2="6" stroke="#D32F2F" stroke-width="3"/>
  <polygon points="24,3 20,9 28,9" fill="#D32F2F"/>
  <circle cx="24" cy="14" r="3" fill="#FFC107"/>
</svg>"""

# 5. Stamp (Odcisk w terenie)
SVG_STAMP = """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <!-- Półka płaska -->
  <polygon points="14,14 34,14 30,22 10,22" fill="#9E9E9E" stroke="#616161" stroke-width="2"/>
  <!-- Skarpa opadająca do terenu -->
  <polygon points="10,22 30,22 42,38 6,38" fill="#81C784" stroke="#388E3C" stroke-width="2"/>
  <!-- Strzałka w dół -->
  <line x1="22" y1="4" x2="22" y2="12" stroke="#1976D2" stroke-width="2.5"/>
  <polygon points="22,14 19,10 25,10" fill="#1976D2"/>
  <line x1="6" y1="38" x2="42" y2="38" stroke="#2E7D32" stroke-width="3"/>
</svg>"""

# 6. Drape (Rzutowanie linii na teren)
SVG_DRAPE = """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <!-- Górna linia źródłowa -->
  <line x1="8" y1="10" x2="40" y2="10" stroke="#D32F2F" stroke-width="3"/>
  <!-- Strzałki rzutowania -->
  <line x1="14" y1="12" x2="14" y2="24" stroke="#F44336" stroke-width="1.5" stroke-dasharray="2,2"/>
  <line x1="24" y1="12" x2="24" y2="22" stroke="#F44336" stroke-width="1.5" stroke-dasharray="2,2"/>
  <line x1="34" y1="12" x2="34" y2="28" stroke="#F44336" stroke-width="1.5" stroke-dasharray="2,2"/>
  <!-- Falujący teren -->
  <path d="M4 32 C14 22, 24 38, 44 26" fill="none" stroke="#2E7D32" stroke-width="3.5"/>
  <!-- Rzutowana ścieżka na terenie -->
  <path d="M8 30 C16 23, 26 36, 40 28" fill="none" stroke="#FF9800" stroke-width="2"/>
</svg>"""

# 7. Add Detail (Dodaj detal / Podział siatki)
SVG_ADD_DETAIL = """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <polygon points="24,6 6,38 42,38" fill="#E8F5E9" stroke="#2E7D32" stroke-width="2"/>
  <!-- Podział na 4 trójkąty -->
  <line x1="15" y1="22" x2="33" y2="22" stroke="#388E3C" stroke-width="1.5"/>
  <line x1="15" y1="22" x2="24" y2="38" stroke="#388E3C" stroke-width="1.5"/>
  <line x1="33" y1="22" x2="24" y2="38" stroke="#388E3C" stroke-width="1.5"/>
  <!-- Znak plus -->
  <circle cx="37" cy="11" r="8" fill="#1976D2"/>
  <line x1="37" y1="6" x2="37" y2="16" stroke="#FFFFFF" stroke-width="2.5"/>
  <line x1="32" y1="11" x2="42" y2="11" stroke="#FFFFFF" stroke-width="2.5"/>
</svg>"""

# 8. Flip Edge (Odwróć krawędź)
SVG_FLIP_EDGE = """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <polygon points="6,24 24,6 42,24 24,42" fill="#E8F5E9" stroke="#2E7D32" stroke-width="2"/>
  <!-- Stara przekątna (przekreślona) -->
  <line x1="24" y1="6" x2="24" y2="42" stroke="#9E9E9E" stroke-width="2" stroke-dasharray="3,3"/>
  <!-- Nowa przekątna (aktywna) -->
  <line x1="6" y1="24" x2="42" y2="24" stroke="#D32F2F" stroke-width="2.5"/>
  <!-- Zakrzywiona strzałka obrotu -->
  <path d="M19 16 C22 13, 26 13, 29 16" fill="none" stroke="#FF9800" stroke-width="2"/>
  <polygon points="31,16 28,13 28,19" fill="#FF9800"/>
</svg>"""


# ===========================================================================
# Konwersja SVG do QIcon (Qt PySide6 / PyQt5)
# ===========================================================================

def get_qicon(svg_data: str) -> Any:
    """Generuje obiekt QIcon bezpośrednio z łańcucha SVG."""
    try:
        from PySide6.QtGui import QIcon, QPixmap
        from PySide6.QtCore import QByteArray
    except ImportError:
        try:
            from PyQt5.QtGui import QIcon, QPixmap
            from PyQt5.QtCore import QByteArray
        except ImportError:
            return None

    try:
        pix = QPixmap()
        byte_data = QByteArray(svg_data.encode("utf-8"))
        pix.loadFromData(byte_data, "SVG")
        return QIcon(pix)
    except Exception:
        return QIcon()


# Gotowe fabryki ikon
def icon_groundbox() -> Any:
    return get_qicon(SVG_GROUNDBOX_MAIN)

icon_sandbox = icon_groundbox

def icon_from_scratch() -> Any:
    return get_qicon(SVG_FROM_SCRATCH)

def icon_from_contours() -> Any:
    return get_qicon(SVG_FROM_CONTOURS)

def icon_smoove() -> Any:
    return get_qicon(SVG_SMOOVE)

def icon_stamp() -> Any:
    return get_qicon(SVG_STAMP)

def icon_drape() -> Any:
    return get_qicon(SVG_DRAPE)

def icon_add_detail() -> Any:
    return get_qicon(SVG_ADD_DETAIL)

def icon_flip_edge() -> Any:
    return get_qicon(SVG_FLIP_EDGE)
