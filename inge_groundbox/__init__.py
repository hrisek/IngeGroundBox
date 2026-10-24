# SPDX-License-Identifier: GPL-3.0-or-later
"""
inge_groundbox/__init__.py
========================
Punkt wejścia rozszerzenia GroundBox dla środowiska IngeTrazo:
Zestaw narzędzi modelowania terenu GroundBox dla IngeTrazo:
- Pasek narzędzi Toolbar z 7 ikonami (From Scratch, From Contours, Smoove, Stamp, Drape, Add Detail, Flip Edge)
- Panel boczny w zasobniku Tray ze szczegółową kontrolą i analizą terenu
- Menu Extensions ▸ GroundBox Terrain
- Menu kontekstowe (prawy przycisk myszy po zaznaczeniu terenu lub warstwic)
"""
from __future__ import annotations

import logging
import os
import sys
import traceback
from typing import Any

# Zabezpieczenie ścieżek wyszukiwania modułów
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PLUGINS_DIR = os.path.dirname(_THIS_DIR)
for _p in (_THIS_DIR, _PLUGINS_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from .constants import PLUGIN_KEY, PLUGIN_NAME
    from .i18n import tr
    from .icons import (
        icon_add_detail,
        icon_drape,
        icon_flip_edge,
        icon_from_contours,
        icon_from_scratch,
        icon_groundbox, icon_sandbox,
        icon_smoove,
        icon_stamp,
    )
    from .tools import (
        AddDetailTool,
        DrapeTool,
        FlipEdgeTool,
        FromScratchTool,
        SmooveTool,
        StampTool,
    )
    from .ui import GroundBoxPanel, SandboxPanel
except ImportError:
    from constants import PLUGIN_KEY, PLUGIN_NAME
    from i18n import tr
    from icons import (
        icon_add_detail,
        icon_drape,
        icon_flip_edge,
        icon_from_contours,
        icon_from_scratch,
        icon_groundbox, icon_sandbox,
        icon_smoove,
        icon_stamp,
    )
    from tools import (
        AddDetailTool,
        DrapeTool,
        FlipEdgeTool,
        FromScratchTool,
        SmooveTool,
        StampTool,
    )
    from ui import GroundBoxPanel, SandboxPanel

try:
    from PySide6.QtCore import QSize, Qt, QTimer
    from PySide6.QtGui import QAction
    from PySide6.QtWidgets import QMenu, QToolBar, QToolButton
except ImportError:
    try:
        from PyQt5.QtCore import QSize, Qt, QTimer
        from PyQt5.QtGui import QAction
        from PyQt5.QtWidgets import QMenu, QToolBar, QToolButton
    except ImportError:
        pass

log = logging.getLogger(f"ingetrazo.plugins.{PLUGIN_KEY}")


# ===========================================================================
# 1. Główna funkcja setup(app)
# ===========================================================================

def setup(app: Any) -> None:
    """Rejestruje wtyczkę w środowisku IngeTrazo (Extension API v2)."""
    app.key = PLUGIN_KEY
    main_icon = icon_groundbox()

    # Inicjalizacja panelu bocznego
    panel_widget = None
    dock = None
    try:
        panel_widget = GroundBoxPanel(app)
        dock = app.add_panel(tr("panel_title"), panel_widget)
        app._groundbox_dock_ref = dock
        app._sandbox_dock_ref = dock
        app.show_panel(dock)
    except Exception as e:
        log.warning(f"GroundBox: Nie udało się zainstalować panelu bocznego: {e}")

    # 1. Pasek narzędzi Toolbar w oknie głównym (wierny klon paska SketchUp)
    try:
        _install_toolbar(app, dock, panel_widget)
    except Exception as e:
        log.warning(f"GroundBox: Błąd instalacji Toolbara: {e}")

    # 2. Pozycja w menu głównym
    try:
        sub = app.add_menu(tr("menu_groundbox"))
        if dock is not None:
            sub.addAction(main_icon, tr("panel_title"), lambda: app.show_panel(dock))
            sub.addSeparator()

        sub.addAction(icon_from_scratch(), tr("tool_from_scratch"), lambda: _activate(app, FromScratchTool))
        sub.addAction(icon_from_contours(), tr("tool_from_contours"), lambda: _run_contours(app))
        sub.addAction(icon_smoove(), tr("tool_smoove"), lambda: _activate(app, SmooveTool))
        sub.addAction(icon_stamp(), tr("tool_stamp"), lambda: _activate(app, StampTool))
        sub.addAction(icon_drape(), tr("tool_drape"), lambda: _activate(app, DrapeTool))
        sub.addAction(icon_add_detail(), tr("tool_add_detail"), lambda: _activate(app, AddDetailTool))
        sub.addAction(icon_flip_edge(), tr("tool_flip_edge"), lambda: _activate(app, FlipEdgeTool))
    except Exception as e:
        log.warning(f"GroundBox: Błąd rejestracji menu: {e}")

    # 3. Menu kontekstowe pod prawym przyciskiem myszy
    try:
        app.add_context_menu(lambda menu, selection: _build_context_menu(app, menu, selection, dock))
    except Exception as e:
        log.warning(f"GroundBox: Błąd rejestracji menu kontekstowego: {e}")

    # 4. Rejestracja narzędzi w systemie narzędzi IngeTrazo
    _register_tools(app)


# ===========================================================================
# 2. Pasek Narzędzi Toolbar (SketchUp Sandbox Clone)
# ===========================================================================

def _install_toolbar(app: Any, dock: Any, panel_widget: Any) -> None:
    """Tworzy dedykowany pasek narzędzi 'GroundBox' ze wszystkimi 7 narzędziami."""
    win = getattr(app, "window", None) or getattr(app, "main_window", None)
    if win is None or not hasattr(win, "addToolBar"):
        return

    obj_name = "extension_groundbox_toolbar"
    if win.findChild(QToolBar, obj_name) is not None:
        return  # Już istnieje

    tb = QToolBar(tr("toolbar_name"), win)
    tb.setObjectName(obj_name)
    tb.setMovable(True)
    tb.setFloatable(True)
    tb.setIconSize(QSize(24, 24))
    tb.setToolButtonStyle(Qt.ToolButtonIconOnly)
    win.addToolBar(Qt.TopToolBarArea, tb)

    def add_btn(icon, text, tooltip, callback):
        act = QAction(icon, text, win)
        act.setToolTip(tooltip)
        act.triggered.connect(lambda _c=False: callback())
        tb.addAction(act)
        return act

    # Przycisk 1: Otwórz panel Sandbox
    add_btn(icon_groundbox(), tr("panel_title"), tr("open_panel_tooltip"), lambda: _open_panel(app, 0))
    tb.addSeparator()

    # Przycisk 2: From Scratch
    add_btn(icon_from_scratch(), tr("tool_from_scratch"), tr("tool_from_scratch_desc"), lambda: _activate(app, FromScratchTool, 0))

    # Przycisk 3: From Contours
    add_btn(icon_from_contours(), tr("tool_from_contours"), tr("tool_from_contours_desc"), lambda: _run_contours(app))

    # Przycisk 4: Smoove
    add_btn(icon_smoove(), tr("tool_smoove"), tr("tool_smoove_desc"), lambda: _activate(app, SmooveTool, 2))

    # Przycisk 5: Stamp
    add_btn(icon_stamp(), tr("tool_stamp"), tr("tool_stamp_desc"), lambda: _activate(app, StampTool, 3))

    # Przycisk 6: Drape
    add_btn(icon_drape(), tr("tool_drape"), tr("tool_drape_desc"), lambda: _activate(app, DrapeTool, 4))

    tb.addSeparator()

    # Przycisk 7: Add Detail
    add_btn(icon_add_detail(), tr("tool_add_detail"), tr("tool_add_detail_desc"), lambda: _activate(app, AddDetailTool, 5))

    # Przycisk 8: Flip Edge
    add_btn(icon_flip_edge(), tr("tool_flip_edge"), tr("tool_flip_edge_desc"), lambda: _activate(app, FlipEdgeTool, 5))

    # Zabezpieczenie przed garbage collectorem
    win._groundbox_toolbar_ref = tb
    win._sandbox_toolbar_ref = tb


# ===========================================================================
# 3. Menu kontekstowe (Prawy przycisk myszy)
# ===========================================================================

def _build_context_menu(app: Any, menu: Any, selection: Any, dock: Any) -> None:
    """Dodaje akcje GroundBox do menu kontekstowego w zależności od typu zaznaczenia."""
    vp = getattr(app, "viewport", None)
    if vp is None:
        return

    sel_list = list(selection) if selection else []
    from .operations import find_terrain_group
    terrain = find_terrain_group(vp.scene if vp else None, sel_list)

    has_edges = any(
        (hasattr(obj, "vertices") and not hasattr(obj, "faces")) or
        (hasattr(obj, "start") and hasattr(obj, "end"))
        for obj in sel_list
    )

    if terrain is not None or has_edges:
        menu.addSeparator()

        # Jeśli zaznaczono linie warstwic
        if has_edges and terrain is None:
            act_ct = menu.addAction(icon_from_contours(), f"GroundBox: {tr('tool_from_contours')}")
            act_ct.triggered.connect(lambda _c=False: QTimer.singleShot(0, lambda: _run_contours(app)))

        # Jeśli zaznaczono teren
        if terrain is not None:
            act_sm = menu.addAction(icon_smoove(), f"GroundBox: {tr('tool_smoove')}")
            act_sm.triggered.connect(lambda _c=False: _activate(app, SmooveTool))

            act_dp = menu.addAction(icon_drape(), f"GroundBox: {tr('tool_drape')}")
            act_dp.triggered.connect(lambda _c=False: _activate(app, DrapeTool))

            act_st = menu.addAction(icon_stamp(), f"GroundBox: {tr('tool_stamp')}")
            act_st.triggered.connect(lambda _c=False: _activate(app, StampTool))

            act_fl = menu.addAction(icon_flip_edge(), f"GroundBox: {tr('tool_flip_edge')}")
            act_fl.triggered.connect(lambda _c=False: _activate(app, FlipEdgeTool))

            act_dt = menu.addAction(icon_add_detail(), f"GroundBox: {tr('tool_add_detail')}")
            act_dt.triggered.connect(lambda _c=False: _activate(app, AddDetailTool))


# ===========================================================================
# 4. Pomocnicze funkcje aktywacji narzędzi
# ===========================================================================

def _open_panel(app: Any, tab_index: int | None = None) -> None:
    """Otwiera boczny panel GroundBox i opcjonalnie przełącza na wybraną zakładkę."""
    dock = getattr(app, "_groundbox_dock_ref", None) or getattr(app, "_sandbox_dock_ref", None)
    if dock and hasattr(app, "show_panel"):
        try:
            app.show_panel(dock)
        except Exception:
            pass
    panel = getattr(app, "_groundbox_panel_ref", None) or getattr(app, "_sandbox_panel_ref", None)
    if panel and tab_index is not None and hasattr(panel, "tabs"):
        try:
            panel.tabs.setCurrentIndex(tab_index)
        except Exception:
            pass


def _activate(app: Any, ToolClass: Any, tab_index: int | None = None) -> None:
    """Aktywuje narzędzie w widoku 3D viewportu oraz synchronizuje boczny panel."""
    tool = ToolClass(app)
    from .operations import resolve_viewport
    vp = resolve_viewport(app)
    if vp:
        if hasattr(vp, "set_active_tool") and callable(vp.set_active_tool):
            vp.set_active_tool(tool)
        elif hasattr(vp, "active_tool"):
            if hasattr(vp.active_tool, "on_deactivate"):
                try:
                    vp.active_tool.on_deactivate(vp)
                except Exception:
                    pass
            vp.active_tool = tool
            if hasattr(tool, "on_activate"):
                tool.on_activate(vp)
        elif hasattr(app, "set_active_tool"):
            app.set_active_tool(tool)
        if hasattr(vp, "setFocus"):
            vp.setFocus()

    if tab_index is not None:
        _open_panel(app, tab_index)


def _run_contours(app: Any) -> None:
    _open_panel(app, 1)
    from .operations import resolve_scene, resolve_viewport
    vp = resolve_viewport(app)
    scene = resolve_scene(app, vp)
    selection = list(_sel_of(vp)) if vp else []
    if not selection and scene and hasattr(scene, "selection"):
        selection = list(scene.selection)

    if not selection and scene and hasattr(scene, "loose_mesh") and scene.loose_mesh:
        loose_edges = getattr(scene.loose_mesh, "edges", [])
        if loose_edges:
            selection = list(loose_edges)

    if not selection:
        win = getattr(app, "window", None) or (vp.window() if vp and hasattr(vp, "window") else None)
        msg = tr("msg_select_contours_prompt")
        try:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(win, tr("err_title_contours"), msg)
        except Exception:
            pass
        if vp and hasattr(vp, "flash_status"):
            vp.flash_status(tr("msg_select_contours"), 5000)
        return

    from .dialogs import FromContoursDialog
    win = getattr(app, "window", None) or (vp.window() if vp and hasattr(vp, "window") else None)
    dlg = FromContoursDialog(parent=win)
    if dlg.exec():
        params = dlg.get_params()
        from .operations import op_create_from_contours
        try:
            res = op_create_from_contours(
                app,
                selection,
                max_segment_len=params["max_segment_len"],
                prune_boundary_ratio=params["prune_boundary_ratio"],
                material_name=params["material"],
                soft_edges=params["soft_edges"],
            )
            if res is not None and vp and hasattr(vp, "flash_status"):
                faces_n = len(res.mesh.faces) if hasattr(res, "mesh") and hasattr(res.mesh, "faces") else "OK"
                verts_n = len(res.mesh.vertices) if hasattr(res, "mesh") and hasattr(res.mesh, "vertices") else "OK"
                vp.flash_status(tr("msg_terrain_created", faces=faces_n, verts=verts_n), 5000)
        except Exception as e:
            import traceback
            err = f"{e}\n\n{traceback.format_exc()}"
            log.exception(err)
            try:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(win, tr("err_title_contours"), f"{tr('err_label')}:\n\n{e}")
            except Exception:
                pass
            if vp and hasattr(vp, "flash_status"):
                vp.flash_status(f"{tr('err_label')}: {e}", 5000)


def _register_tools(app: Any) -> None:
    for ToolCls, tool_id in (
        (FromScratchTool, "inge_groundbox.from_scratch"),
        (SmooveTool,      "inge_groundbox.smoove"),
        (StampTool,       "inge_groundbox.stamp"),
        (DrapeTool,       "inge_groundbox.drape"),
        (AddDetailTool,   "inge_groundbox.add_detail"),
        (FlipEdgeTool,    "inge_groundbox.flip_edge"),
    ):
        try:
            app.register_tool(ToolCls(app), id=tool_id)
        except Exception:
            pass


def _sel_of(vp):
    try:
        s = getattr(getattr(vp, 'scene', None), 'selection', None)
        if s is None:
            s = getattr(vp, 'selection', None)
        return list(s) if s else []
    except Exception:
        return []
