# SPDX-License-Identifier: GPL-3.0-or-later
"""
inge_groundbox/ui.py
==================
Główny panel boczny wtyczki GroundBox dla IngeTrazo:
Zakładki dla wszystkich 7 narzędzi GroundBox:
1. Od podstaw (From Scratch)
2. Z warstwic (From Contours)
3. Rzeźbienie (Smoove)
4. Odcisk (Stamp)
5. Rzutowanie (Drape)
6. Edycja siatki (TIN: Flip Edge, Add Detail)
7. Analiza i Raport (pole 3D, ΔZ, kubatury, eksport CSV, generowanie poziomic)
"""
from __future__ import annotations

import csv
import logging
from typing import Any

from .constants import (
    DEFAULT_CONTOURS,
    DEFAULT_DRAPE,
    DEFAULT_FROM_SCRATCH,
    DEFAULT_SMOOVE,
    DEFAULT_STAMP,
    PLUGIN_KEY,
)
from .dialogs import TerrainReportDialog
from .i18n import get_lang, set_lang, tr
from .operations import (
    QMatrix4x4,
    commit_group_to_scene,
    extract_triangles_from_group,
    find_terrain_group,
    op_apply_add_detail,
    op_apply_drape,
    op_apply_slope_analysis,
    op_apply_smoove_numeric,
    op_apply_stamp,
    op_create_from_contours,
    op_create_from_scratch,
    op_create_terrain_skirt,
    op_reset_terrain_colors,
    resolve_scene,
    resolve_viewport,
    to_point3d,
    to_qvector3d,
)
from .geometry import calculate_slope_distribution
from .terrain_mesh import calculate_mesh_statistics, generate_terrain_contours

log = logging.getLogger(f"ingetrazo.plugins.{PLUGIN_KEY}")

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDoubleSpinBox,
        QFileDialog,
        QFormLayout,
        QFrame,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QSizePolicy,
        QSlider,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    try:
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import (
            QCheckBox,
            QComboBox,
            QDoubleSpinBox,
            QFileDialog,
            QFormLayout,
            QFrame,
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QMessageBox,
            QPushButton,
            QScrollArea,
            QSizePolicy,
            QSlider,
            QTabWidget,
            QVBoxLayout,
            QWidget,
        )
    except ImportError:
        class QWidget: pass
        class QTabWidget: pass


class GroundBoxPanel(QWidget):
    """
    Panel boczny 'GroundBox' integrujący wszystkie narzędzia piaskownicy w zasobniku bocznym (Tray).
    """

    def __init__(self, app: Any, parent: Any = None):
        super().__init__(parent)
        self._app = app
        app._groundbox_panel_ref = self
        app._sandbox_panel_ref = self

        self.setWindowTitle(tr("panel_title"))
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(4, 4, 4, 4)
        root_layout.setSpacing(6)

        # Nagłówek panelu z przełącznikiem języka (EN [domyślny] / PL)
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(4, 2, 4, 2)
        self.lang_lbl = QLabel(tr("lang_selector_label"))
        top_bar.addWidget(self.lang_lbl)
        top_bar.addStretch(1)

        self.combo_lang = QComboBox()
        self.combo_lang.addItem("🇬🇧 English", "en")
        self.combo_lang.addItem("🇵🇱 Polski", "pl")
        current_idx = 1 if get_lang() == "pl" else 0
        self.combo_lang.setCurrentIndex(current_idx)
        self.combo_lang.currentIndexChanged.connect(self._on_lang_changed)
        top_bar.addWidget(self.combo_lang)
        root_layout.addLayout(top_bar)

        # Kontener zakładek
        self.tabs = QTabWidget(self)
        self.tabs.setDocumentMode(True)
        root_layout.addWidget(self.tabs)

        self._rebuild_tabs()

    def _rebuild_tabs(self) -> None:
        """Rebuilds all tabs dynamically in the currently active language (preserving values)."""
        current_idx = self.tabs.currentIndex() if hasattr(self, "tabs") and self.tabs.count() > 0 else 0
        if current_idx < 0:
            current_idx = 0

        # Snapshot of existing user inputs if available
        saved = {}
        if hasattr(self, "sc_size_x"):
            try:
                saved = {
                    "sc_size_x": self.sc_size_x.value(),
                    "sc_size_y": self.sc_size_y.value(),
                    "sc_spacing": self.sc_spacing.value(),
                    "sc_base_z": self.sc_base_z.value(),
                    "sc_pattern": self.sc_pattern.currentData(),
                    "ct_seg": self.ct_seg.value(),
                    "ct_prune": self.ct_prune.value(),
                    "ct_soft": self.ct_soft.isChecked(),
                    "sm_radius": self.sm_radius.value(),
                    "sm_strength": self.sm_slider_str.value(),
                    "sm_falloff": self.sm_falloff.currentData(),
                    "sm_direct_dz": self.sm_direct_dz.value(),
                    "st_offset": self.st_offset.value(),
                    "st_auto": self.st_chk_auto.isChecked(),
                    "st_elev": self.st_elev.value(),
                    "dr_width": self.dr_width.value(),
                    "dr_paint": self.dr_paint.isChecked(),
                    "sp_interval": self.sp_interval.value(),
                    "sp_skirt_depth": self.sp_skirt_depth.value() if hasattr(self, "sp_skirt_depth") else 1.0,
                }
            except Exception:
                pass

        self.tabs.clear()
        self.tabs.addTab(self._build_scratch_tab(), tr("tab_from_scratch"))
        self.tabs.addTab(self._build_contours_tab(), tr("tab_contours"))
        self.tabs.addTab(self._build_smoove_tab(), tr("tab_smoove"))
        self.tabs.addTab(self._build_stamp_tab(), tr("tab_stamp"))
        self.tabs.addTab(self._build_drape_tab(), tr("tab_drape"))
        self.tabs.addTab(self._build_mesh_ops_tab(), tr("tab_mesh_ops"))
        self.tabs.addTab(self._build_analysis_tab(), tr("tab_analysis"))

        # Restore saved input values
        if saved:
            try:
                if "sc_size_x" in saved: self.sc_size_x.setValue(saved["sc_size_x"])
                if "sc_size_y" in saved: self.sc_size_y.setValue(saved["sc_size_y"])
                if "sc_spacing" in saved: self.sc_spacing.setValue(saved["sc_spacing"])
                if "sc_base_z" in saved: self.sc_base_z.setValue(saved["sc_base_z"])
                if "sc_pattern" in saved and saved["sc_pattern"]:
                    idx = self.sc_pattern.findData(saved["sc_pattern"])
                    if idx >= 0: self.sc_pattern.setCurrentIndex(idx)
                if "ct_seg" in saved: self.ct_seg.setValue(saved["ct_seg"])
                if "ct_prune" in saved: self.ct_prune.setValue(saved["ct_prune"])
                if "ct_soft" in saved: self.ct_soft.setChecked(saved["ct_soft"])
                if "sm_radius" in saved: self.sm_radius.setValue(saved["sm_radius"])
                if "sm_strength" in saved: self.sm_slider_str.setValue(saved["sm_strength"])
                if "sm_falloff" in saved and saved["sm_falloff"]:
                    idx = self.sm_falloff.findData(saved["sm_falloff"])
                    if idx >= 0: self.sm_falloff.setCurrentIndex(idx)
                if "sm_direct_dz" in saved: self.sm_direct_dz.setValue(saved["sm_direct_dz"])
                if "st_offset" in saved: self.st_offset.setValue(saved["st_offset"])
                if "st_auto" in saved: self.st_chk_auto.setChecked(saved["st_auto"])
                if "st_elev" in saved: self.st_elev.setValue(saved["st_elev"])
                if "dr_width" in saved: self.dr_width.setValue(saved["dr_width"])
                if "dr_paint" in saved: self.dr_paint.setChecked(saved["dr_paint"])
                if "sp_interval" in saved: self.sp_interval.setValue(saved["sp_interval"])
                if "sp_skirt_depth" in saved and hasattr(self, "sp_skirt_depth"): self.sp_skirt_depth.setValue(saved["sp_skirt_depth"])
            except Exception:
                pass

        self.tabs.setCurrentIndex(current_idx)
        self.setWindowTitle(tr("panel_title"))
        if hasattr(self, "lang_lbl"):
            self.lang_lbl.setText(tr("lang_selector_label"))

    def _on_lang_changed(self, idx: int) -> None:
        new_lang = self.combo_lang.currentData()
        if new_lang != get_lang():
            set_lang(new_lang)
            self._rebuild_tabs()

    # =======================================================================
    # 1. Zakładka: From Scratch (Od podstaw)
    # =======================================================================

    def _build_scratch_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        form = QFormLayout()
        self.sc_size_x = _make_double_spin(DEFAULT_FROM_SCRATCH["size_x"], 1.0, 10000.0, 5.0, " m")
        form.addRow(tr("size_x_label"), self.sc_size_x)

        self.sc_size_y = _make_double_spin(DEFAULT_FROM_SCRATCH["size_y"], 1.0, 10000.0, 5.0, " m")
        form.addRow(tr("size_y_label"), self.sc_size_y)

        self.sc_spacing = _make_double_spin(DEFAULT_FROM_SCRATCH["spacing"], 0.1, 100.0, 0.5, " m")
        form.addRow(tr("spacing_label"), self.sc_spacing)

        self.sc_base_z = _make_double_spin(DEFAULT_FROM_SCRATCH["base_z"], -1000.0, 5000.0, 1.0, " m")
        form.addRow(tr("base_z_label"), self.sc_base_z)

        self.sc_pattern = QComboBox()
        self.sc_pattern.addItem(tr("pattern_alternating"), "alternating")
        self.sc_pattern.addItem(tr("pattern_uniform"), "uniform")
        form.addRow(tr("pattern_label"), self.sc_pattern)

        self.sc_material = QComboBox()
        self.sc_material.addItems([tr("mat_grass"), tr("mat_soil"), tr("mat_sand"), tr("mat_rock")])
        form.addRow(tr("material_label"), self.sc_material)

        layout.addLayout(form)

        btn_gen = QPushButton(tr("btn_generate_scratch"))
        btn_gen.setStyleSheet("font-weight: bold; padding: 6px;")
        btn_gen.clicked.connect(self._on_generate_scratch)
        layout.addWidget(btn_gen)

        btn_tool = QPushButton(tr("btn_scratch_tool"))
        btn_tool.clicked.connect(self._on_activate_scratch_tool)
        layout.addWidget(btn_tool)

        layout.addStretch(1)
        return w

    def _on_generate_scratch(self):
        try:
            grp = op_create_from_scratch(
                self._app,
                size_x=self.sc_size_x.value(),
                size_y=self.sc_size_y.value(),
                spacing=self.sc_spacing.value(),
                base_z=self.sc_base_z.value(),
                pattern=self.sc_pattern.currentData(),
                material_name=self.sc_material.currentText(),
            )
            faces_n = len(grp.mesh.faces) if grp and hasattr(grp, "mesh") and hasattr(grp.mesh, "faces") else "OK"
            verts_n = len(grp.mesh.vertices) if grp and hasattr(grp, "mesh") and hasattr(grp.mesh, "vertices") else "OK"
            _show_status(self._app, tr("msg_terrain_created", faces=faces_n, verts=verts_n), 5000)
        except Exception as e:
            import traceback
            err = f"{e}\n\n{traceback.format_exc()}"
            log.exception(err)
            try:
                QMessageBox.critical(self, tr("err_title_scratch"), f"{tr('err_label')}:\n\n{e}")
            except Exception:
                pass
            _show_status(self._app, f"{tr('err_label')}: {e}", 5000)

    def _on_activate_scratch_tool(self):
        from .tools import FromScratchTool
        tool = FromScratchTool(self._app)
        _set_active_tool(self._app, tool)

    # =======================================================================
    # 2. Zakładka: From Contours (Z warstwic)
    # =======================================================================

    def _build_contours_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        lbl = QLabel(tr("contours_info"))
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(lbl)

        form = QFormLayout()
        self.ct_seg = _make_double_spin(DEFAULT_CONTOURS["max_segment_len"], 0.5, 50.0, 0.5, " m")
        form.addRow(tr("max_seg_len"), self.ct_seg)

        self.ct_prune = _make_double_spin(DEFAULT_CONTOURS["prune_boundary_ratio"], 1.5, 10.0, 0.5, " x")
        form.addRow(tr("prune_boundary"), self.ct_prune)

        self.ct_soft = QCheckBox(tr("soft_edges_label"))
        self.ct_soft.setChecked(DEFAULT_CONTOURS["soft_edges"])
        form.addRow("", self.ct_soft)

        self.ct_material = QComboBox()
        self.ct_material.addItems([tr("mat_grass"), tr("mat_soil"), tr("mat_rock")])
        form.addRow(tr("material_label"), self.ct_material)

        layout.addLayout(form)

        btn_gen = QPushButton(tr("btn_generate_contours"))
        btn_gen.setStyleSheet("font-weight: bold; padding: 6px;")
        btn_gen.clicked.connect(self._on_generate_contours)
        layout.addWidget(btn_gen)

        layout.addStretch(1)
        return w

    def _on_generate_contours(self):
        vp = resolve_viewport(self._app)
        scene = resolve_scene(self._app, vp)
        selection = list(_sel_of(vp)) if vp else []
        if not selection and scene and hasattr(scene, "selection"):
            selection = list(scene.selection)

        if not selection and scene and hasattr(scene, "loose_mesh") and scene.loose_mesh:
            loose_edges = getattr(scene.loose_mesh, "edges", [])
            if loose_edges:
                selection = list(loose_edges)

        if not selection:
            msg = tr("msg_select_contours_prompt")
            try:
                QMessageBox.warning(self, tr("err_title_contours"), msg)
            except Exception:
                pass
            _show_status(self._app, tr("msg_select_contours"), 5000)
            return

        try:
            res = op_create_from_contours(
                self._app,
                selection,
                max_segment_len=self.ct_seg.value(),
                prune_boundary_ratio=self.ct_prune.value(),
                material_name=self.ct_material.currentText(),
                soft_edges=self.ct_soft.isChecked(),
            )
            if res is not None:
                faces_n = len(res.mesh.faces) if hasattr(res, "mesh") and hasattr(res.mesh, "faces") else "OK"
                verts_n = len(res.mesh.vertices) if hasattr(res, "mesh") and hasattr(res.mesh, "vertices") else "OK"
                _show_status(self._app, tr("msg_terrain_created", faces=faces_n, verts=verts_n), 5000)
            else:
                _show_status(self._app, tr("msg_contours_failed"), 4000)
        except Exception as e:
            import traceback
            err = f"{e}\n\n{traceback.format_exc()}"
            log.exception(err)
            try:
                QMessageBox.critical(self, tr("err_title_contours"), f"{tr('err_label')}:\n\n{e}")
            except Exception:
                pass
            _show_status(self._app, f"{tr('err_label')}: {e}", 5000)

    # =======================================================================
    # 3. Zakładka: Smoove (Rzeźbienie)
    # =======================================================================

    def _build_smoove_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        lbl = QLabel(tr("smoove_hint"))
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(lbl)

        form = QFormLayout()

        # Promień
        self.sm_radius = _make_double_spin(DEFAULT_SMOOVE["radius"], 0.5, 300.0, 1.0, " m")
        form.addRow(tr("brush_radius"), self.sm_radius)

        # Siła
        h_str = QHBoxLayout()
        self.sm_slider_str = QSlider(Qt.Horizontal)
        self.sm_slider_str.setRange(1, 100)
        self.sm_slider_str.setValue(int(DEFAULT_SMOOVE["strength"] * 100))
        self.sm_lbl_str = QLabel(f"{DEFAULT_SMOOVE['strength']:.2f}")
        self.sm_lbl_str.setMinimumWidth(32)
        self.sm_slider_str.valueChanged.connect(lambda v: self.sm_lbl_str.setText(f"{v/100:.2f}"))
        h_str.addWidget(self.sm_slider_str)
        h_str.addWidget(self.sm_lbl_str)
        str_w = QWidget()
        str_w.setLayout(h_str)
        form.addRow(tr("brush_strength"), str_w)

        # Profil opadania
        self.sm_falloff = QComboBox()
        self.sm_falloff.addItem(tr("falloff_cosine"), "cosine")
        self.sm_falloff.addItem(tr("falloff_gaussian"), "gaussian")
        self.sm_falloff.addItem(tr("falloff_linear"), "linear")
        self.sm_falloff.addItem(tr("falloff_smoothstep"), "smoothstep")
        form.addRow(tr("falloff_label"), self.sm_falloff)

        layout.addLayout(form)

        btn_act = QPushButton(tr("btn_activate_smoove"))
        btn_act.setStyleSheet("font-weight: bold; padding: 6px;")
        btn_act.clicked.connect(self._on_activate_smoove)
        layout.addWidget(btn_act)

        # Rozdzielacz i sekcja numeryczna
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep)

        lbl_dir = QLabel(f"<b>{tr('smoove_direct_title')}</b>")
        layout.addWidget(lbl_dir)

        form_dir = QFormLayout()
        self.sm_direct_dz = _make_double_spin(1.5, -100.0, 100.0, 0.5, " m")
        form_dir.addRow(tr("elevation_dz_label"), self.sm_direct_dz)
        layout.addLayout(form_dir)

        btn_direct = QPushButton(tr("btn_smoove_direct"))
        btn_direct.setToolTip(tr("btn_smoove_direct_hint"))
        btn_direct.clicked.connect(self._on_apply_smoove_direct)
        layout.addWidget(btn_direct)

        layout.addStretch(1)
        return w

    def _on_activate_smoove(self):
        from .tools import SmooveTool
        tool = SmooveTool(self._app)
        tool.brush_radius = self.get_brush_radius()
        tool.brush_strength = self.get_brush_strength()
        tool.falloff_profile = self.get_falloff_profile()
        _set_active_tool(self._app, tool)

    def _on_apply_smoove_direct(self):
        vp = resolve_viewport(self._app)
        scene = resolve_scene(self._app, vp)
        selection = list(_sel_of(vp)) if vp else []
        if not selection and scene and hasattr(scene, "selection"):
            selection = list(scene.selection)

        terrain = find_terrain_group(scene, selection)
        if terrain is None:
            msg = tr("msg_select_terrain_smoove")
            try:
                QMessageBox.warning(self, tr("err_title_smoove"), msg)
            except Exception:
                pass
            _show_status(self._app, msg, 4000)
            return

        mesh = getattr(terrain, "mesh", None)
        if mesh is None or not getattr(mesh, "vertices", []):
            _show_status(self._app, tr("msg_terrain_no_mesh"), 3000)
            return

        verts_pts = [to_point3d(v) for v in mesh.vertices]
        min_x = min(p[0] for p in verts_pts)
        max_x = max(p[0] for p in verts_pts)
        min_y = min(p[1] for p in verts_pts)
        max_y = max(p[1] for p in verts_pts)
        mid_z = sum(p[2] for p in verts_pts) / len(verts_pts)
        center_pt = ((min_x + max_x) * 0.5, (min_y + max_y) * 0.5, mid_z)

        try:
            moved = op_apply_smoove_numeric(
                self._app,
                terrain,
                center_pt,
                radius=self.get_brush_radius(),
                delta_z=self.sm_direct_dz.value(),
                falloff=self.get_falloff_profile(),
            )
            _show_status(self._app, tr("msg_smoove_direct_done", moved=moved, dz=self.sm_direct_dz.value()), 5000)
        except Exception as e:
            import traceback
            log.exception(f"Smoove direct: {e}\n{traceback.format_exc()}")
            _show_status(self._app, f"{tr('err_label')} (Smoove): {e}", 4000)

    def get_brush_radius(self) -> float:
        return self.sm_radius.value()

    def get_brush_strength(self) -> float:
        return self.sm_slider_str.value() / 100.0

    def get_falloff_profile(self) -> str:
        return self.sm_falloff.currentData()

    # =======================================================================
    # 4. Zakładka: Stamp (Odcisk)
    # =======================================================================

    def _build_stamp_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        lbl = QLabel(tr("stamp_info"))
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(lbl)

        form = QFormLayout()
        self.st_offset = _make_double_spin(DEFAULT_STAMP["offset_distance"], 0.1, 50.0, 0.5, " m")
        form.addRow(tr("offset_dist_label"), self.st_offset)

        self.st_chk_auto = QCheckBox(tr("auto_elev_check"))
        self.st_chk_auto.setChecked(True)
        form.addRow("", self.st_chk_auto)

        self.st_elev = _make_double_spin(0.0, -1000.0, 5000.0, 0.5, " m")
        self.st_elev.setEnabled(False)
        self.st_chk_auto.toggled.connect(lambda c: self.st_elev.setEnabled(not c))
        form.addRow(tr("pad_elevation_label"), self.st_elev)

        self.st_pad_mat = QComboBox()
        self.st_pad_mat.addItems([tr("mat_concrete"), tr("mat_terrace_tile"), tr("mat_crushed_stone"), tr("mat_asphalt")])
        form.addRow(tr("pad_material_label"), self.st_pad_mat)

        self.st_slope_mat = QComboBox()
        self.st_slope_mat.addItems([tr("mat_slope_ground"), tr("mat_grass"), tr("mat_stones")])
        form.addRow(tr("slope_material_label"), self.st_slope_mat)

        layout.addLayout(form)

        btn_stamp = QPushButton(tr("btn_apply_stamp"))
        btn_stamp.setStyleSheet("font-weight: bold; padding: 6px;")
        btn_stamp.clicked.connect(self._on_apply_stamp)
        layout.addWidget(btn_stamp)

        btn_tool = QPushButton(tr("btn_stamp_tool"))
        btn_tool.clicked.connect(self._on_activate_stamp_tool)
        layout.addWidget(btn_tool)

        layout.addStretch(1)
        return w

    def _on_apply_stamp(self):
        vp = resolve_viewport(self._app)
        scene = resolve_scene(self._app, vp)
        selection = list(_sel_of(vp)) if vp else []
        if not selection and scene and hasattr(scene, "selection"):
            selection = list(scene.selection)

        terrain = find_terrain_group(scene, selection)

        footprint = None
        for obj in selection:
            if obj is not terrain and (hasattr(obj, "vertices") or hasattr(obj, "mesh")):
                footprint = obj
                break

        if terrain is None or footprint is None:
            msg = tr("msg_select_footprint_terrain")
            try:
                QMessageBox.warning(self, tr("err_title_stamp"), msg)
            except Exception:
                pass
            _show_status(self._app, msg, 4000)
            return

        try:
            cut, fill, net = op_apply_stamp(
                self._app,
                footprint,
                terrain,
                offset_dist=self.st_offset.value(),
                target_elevation=None if self.st_chk_auto.isChecked() else self.st_elev.value(),
                pad_material=self.st_pad_mat.currentText(),
                slope_material=self.st_slope_mat.currentText(),
            )
            _show_status(self._app, tr("msg_stamp_done", cut=cut, fill=fill), 5000)
            try:
                QMessageBox.information(
                    self,
                    tr("stamp_result_title"),
                    tr("msg_stamp_success_box", cut=cut, fill=fill, net=net),
                )
            except Exception:
                pass
        except Exception as e:
            import traceback
            err = f"{e}\n\n{traceback.format_exc()}"
            log.exception(err)
            try:
                QMessageBox.critical(self, tr("err_title_stamp"), f"{tr('err_label')}:\n\n{e}")
            except Exception:
                pass
            _show_status(self._app, f"{tr('err_label')} (Stamp): {e}", 5000)

    def _on_activate_stamp_tool(self):
        from .tools import StampTool
        tool = StampTool(self._app)
        _set_active_tool(self._app, tool)

    # =======================================================================
    # 5. Zakładka: Drape (Rzutowanie)
    # =======================================================================

    def _build_drape_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        lbl = QLabel(tr("drape_info"))
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(lbl)

        form = QFormLayout()
        self.dr_width = _make_double_spin(0.0, 0.0, 30.0, 0.5, " m")
        self.dr_width.setToolTip(tr("road_width_hint"))
        form.addRow(tr("road_width_label"), self.dr_width)

        self.dr_mat = QComboBox()
        self.dr_mat.addItems([tr("mat_asphalt"), tr("mat_paving"), tr("mat_gravel"), tr("mat_path")])
        form.addRow(tr("drape_mat_label"), self.dr_mat)

        self.dr_paint = QCheckBox(tr("drape_paint_check"))
        self.dr_paint.setChecked(True)
        form.addRow("", self.dr_paint)

        layout.addLayout(form)

        btn_drape = QPushButton(tr("btn_apply_drape"))
        btn_drape.setStyleSheet("font-weight: bold; padding: 6px;")
        btn_drape.clicked.connect(self._on_apply_drape)
        layout.addWidget(btn_drape)

        btn_tool = QPushButton(tr("btn_drape_tool"))
        btn_tool.clicked.connect(self._on_activate_drape_tool)
        layout.addWidget(btn_tool)

        layout.addStretch(1)
        return w

    def _on_apply_drape(self):
        vp = resolve_viewport(self._app)
        scene = resolve_scene(self._app, vp)
        selection = list(_sel_of(vp)) if vp else []
        if not selection and scene and hasattr(scene, "selection"):
            selection = list(scene.selection)

        terrain = find_terrain_group(scene, selection)
        path_edges = [obj for obj in selection if obj is not terrain]

        if terrain is None or not path_edges:
            msg = tr("msg_select_drape_lines")
            try:
                QMessageBox.warning(self, tr("err_title_drape"), msg)
            except Exception:
                pass
            _show_status(self._app, msg, 4000)
            return

        try:
            count = op_apply_drape(
                self._app,
                path_edges,
                terrain,
                road_width=self.dr_width.value(),
                material_name=self.dr_mat.currentText(),
                paint=self.dr_paint.isChecked(),
            )
            _show_status(self._app, tr("msg_drape_done", n=count), 5000)
        except Exception as e:
            import traceback
            err = f"{tr('err_title_drape')}:\n\n{e}\n\n{traceback.format_exc()}"
            log.exception(err)
            try:
                QMessageBox.critical(self, tr("err_title_drape"), f"{tr('err_label')}:\n\n{err}")
            except Exception:
                pass
            _show_status(self._app, f"{tr('err_title_drape')}: {e}", 5000)

    def _on_activate_drape_tool(self):
        from .tools import DrapeTool
        tool = DrapeTool(self._app)
        _set_active_tool(self._app, tool)

    # =======================================================================
    # 6. Zakładka: Edycja siatki (TIN)
    # =======================================================================

    def _build_mesh_ops_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        lbl = QLabel(tr("mesh_ops_hint"))
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(lbl)

        btn_flip = QPushButton(tr("btn_flip_edge_tool"))
        btn_flip.setStyleSheet("padding: 6px;")
        btn_flip.clicked.connect(self._on_activate_flip_tool)
        layout.addWidget(btn_flip)

        btn_detail = QPushButton(tr("btn_add_detail_tool"))
        btn_detail.setStyleSheet("padding: 6px;")
        btn_detail.clicked.connect(self._on_activate_detail_tool)
        layout.addWidget(btn_detail)

        btn_subdiv = QPushButton(tr("btn_subdivide_selection"))
        btn_subdiv.clicked.connect(self._on_subdivide_selection)
        layout.addWidget(btn_subdiv)

        layout.addStretch(1)
        return w

    def _on_activate_flip_tool(self):
        from .tools import FlipEdgeTool
        tool = FlipEdgeTool(self._app)
        _set_active_tool(self._app, tool)

    def _on_activate_detail_tool(self):
        from .tools import AddDetailTool
        tool = AddDetailTool(self._app)
        _set_active_tool(self._app, tool)

    def _on_subdivide_selection(self):
        vp = resolve_viewport(self._app)
        scene = resolve_scene(self._app, vp)
        selection = list(_sel_of(vp)) if vp else []
        if not selection and scene and hasattr(scene, "selection"):
            selection = list(scene.selection)

        terrain = find_terrain_group(scene, selection)
        if terrain is None:
            try:
                QMessageBox.warning(self, tr("err_title_detail"), tr("msg_no_terrain"))
            except Exception:
                pass
            _show_status(self._app, tr("msg_no_terrain"), 3000)
            return

        try:
            count = op_apply_add_detail(self._app, terrain)
            _show_status(self._app, tr("msg_detail_added", n=count), 4000)
            vp = resolve_viewport(self._app)
            if vp:
                if hasattr(vp, "notify_scene_changed") and callable(vp.notify_scene_changed):
                    vp.notify_scene_changed()
                if hasattr(vp, "update") and callable(vp.update):
                    vp.update()
        except Exception as e:
            import traceback
            err = f"{tr('err_title_detail')}:\n\n{e}\n\n{traceback.format_exc()}"
            log.exception(err)
            try:
                QMessageBox.critical(self, tr("err_title_detail"), f"{tr('err_label')}:\n\n{err}")
            except Exception:
                pass
            _show_status(self._app, f"{tr('err_label')}: {e}", 5000)

    # =======================================================================
    # 7. Zakładka: Analiza & Raport
    # =======================================================================

    def _build_analysis_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        # 1. Metryki ogólne terenu
        box_stats = QGroupBox(tr("terrain_stats_title"))
        form = QFormLayout(box_stats)

        self.lbl_faces = QLabel("0")
        form.addRow(tr("stat_faces"), self.lbl_faces)

        self.lbl_verts = QLabel("0")
        form.addRow(tr("stat_vertices"), self.lbl_verts)

        self.lbl_area_3d = QLabel("0.00 m²")
        form.addRow(tr("stat_3d_area"), self.lbl_area_3d)

        self.lbl_area_2d = QLabel("0.00 m²")
        form.addRow(tr("stat_2d_area"), self.lbl_area_2d)

        self.lbl_min_z = QLabel("0.00 m")
        form.addRow(tr("stat_min_z"), self.lbl_min_z)

        self.lbl_max_z = QLabel("0.00 m")
        form.addRow(tr("stat_max_z"), self.lbl_max_z)

        self.lbl_delta_z = QLabel("0.00 m")
        form.addRow(tr("stat_height_diff"), self.lbl_delta_z)

        self.lbl_slope_avg = QLabel("0.0%")
        form.addRow(tr("stat_avg_slope"), self.lbl_slope_avg)

        self.lbl_slope_max = QLabel("0.0%")
        form.addRow(tr("stat_max_slope"), self.lbl_slope_max)

        layout.addWidget(box_stats)

        btn_refresh = QPushButton(tr("btn_refresh_stats"))
        btn_refresh.clicked.connect(self._refresh_stats)
        layout.addWidget(btn_refresh)

        btn_csv = QPushButton("📊  " + tr("btn_export_csv"))
        btn_csv.clicked.connect(self._export_csv_report)
        layout.addWidget(btn_csv)

        # 2. Analiza spadków (Heatmap)
        box_slope = QGroupBox(tr("slope_analysis_title"))
        v_slope = QVBoxLayout(box_slope)

        form_bands = QFormLayout()
        badges_info = [
            ("#26a640", "slope_band_1"),
            ("#40c747", "slope_band_2"),
            ("#8cd138", "slope_band_3"),
            ("#c7e02e", "slope_band_4"),
            ("#f5e026", "slope_band_5"),
            ("#f5b31f", "slope_band_6"),
            ("#f5801f", "slope_band_7"),
            ("#eb5924", "slope_band_8"),
            ("#d92e2e", "slope_band_9"),
            ("#8c1440", "slope_band_10"),
        ]
        self.lbl_slope_bands = []
        for i, (hex_col, key) in enumerate(badges_info):
            lbl_badge = QLabel(f"<span style='color: {hex_col}; font-weight: bold;'>■</span> {tr(key)}:")
            lbl_val = QLabel("0.00 m² (0.0%)")
            form_bands.addRow(lbl_badge, lbl_val)
            self.lbl_slope_bands.append(lbl_val)
            setattr(self, f"lbl_slope_band{i}", lbl_val)
        v_slope.addLayout(form_bands)

        btn_slope = QPushButton(tr("btn_apply_slope"))
        btn_slope.setStyleSheet("font-weight: bold; padding: 5px;")
        btn_slope.clicked.connect(self._on_apply_slope_analysis)
        v_slope.addWidget(btn_slope)

        btn_reset_col = QPushButton(tr("btn_reset_colors"))
        btn_reset_col.clicked.connect(self._on_reset_terrain_colors)
        v_slope.addWidget(btn_reset_col)

        layout.addWidget(box_slope)

        # 3. Zamknięcie bryły 3D (Solid Skirt)
        box_skirt = QGroupBox(tr("skirt_box_title"))
        form_skirt = QFormLayout(box_skirt)

        self.sp_skirt_depth = _make_double_spin(1.0, 0.1, 100.0, 0.5, " m")
        form_skirt.addRow(tr("skirt_depth_label"), self.sp_skirt_depth)

        self.cb_skirt_mat = QComboBox()
        self.cb_skirt_mat.addItems([tr("mat_soil_ground"), tr("mat_concrete_box")])
        form_skirt.addRow(tr("skirt_mat_label"), self.cb_skirt_mat)

        btn_skirt = QPushButton(tr("btn_create_skirt"))
        btn_skirt.setStyleSheet("font-weight: bold; padding: 5px;")
        btn_skirt.clicked.connect(self._on_create_skirt)
        form_skirt.addRow(btn_skirt)

        layout.addWidget(box_skirt)

        # 4. Generowanie poziomic z terenu
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep)

        form_c = QFormLayout()
        self.sp_interval = _make_double_spin(1.0, 0.1, 50.0, 0.5, " m")
        form_c.addRow(tr("contour_interval"), self.sp_interval)
        layout.addLayout(form_c)

        btn_contours = QPushButton(tr("btn_generate_terrain_contours"))
        btn_contours.clicked.connect(self._generate_contours_from_terrain)
        layout.addWidget(btn_contours)

        layout.addStretch(1)
        return w

    def _refresh_stats(self):
        vp = resolve_viewport(self._app)
        scene = resolve_scene(self._app, vp)
        selection = list(_sel_of(vp)) if vp else []
        if not selection and scene and hasattr(scene, "selection"):
            selection = list(scene.selection)

        terrain = find_terrain_group(scene, selection)
        if terrain is None:
            _show_status(self._app, tr("msg_no_terrain"), 3000)
            return

        try:
            triangles = extract_triangles_from_group(terrain)
            stats = calculate_mesh_statistics(triangles)
            slope_info = calculate_slope_distribution(triangles)
            stats.update(slope_info)

            self.lbl_faces.setText(str(stats["face_count"]))
            self.lbl_verts.setText(str(stats["vertex_count"]))
            self.lbl_area_3d.setText(f"{stats['area_3d']:.2f} m²")
            self.lbl_area_2d.setText(f"{stats['area_2d']:.2f} m²")
            self.lbl_min_z.setText(f"{stats['min_z']:.2f} m")
            self.lbl_max_z.setText(f"{stats['max_z']:.2f} m")
            self.lbl_delta_z.setText(f"{stats['delta_z']:.2f} m")
            self.lbl_slope_avg.setText(f"{slope_info['avg_slope_pct']:.1f}% ({slope_info['avg_slope_deg']:.1f}°)")
            self.lbl_slope_max.setText(f"{slope_info['max_slope_pct']:.1f}% ({slope_info['max_slope_deg']:.1f}°)")

            areas = slope_info.get("band_areas", [0.0] * 10)
            pcts = slope_info.get("band_pcts", [0.0] * 10)
            for i in range(10):
                lbl = getattr(self, f"lbl_slope_band{i}", None)
                if lbl is not None and i < len(areas) and i < len(pcts):
                    lbl.setText(f"{areas[i]:.2f} m² ({pcts[i]:.1f}%)")
        except Exception as e:
            _show_status(self._app, f"{tr('err_label')}: {e}", 4000)

    def _export_csv_report(self):
        vp = resolve_viewport(self._app)
        scene = resolve_scene(self._app, vp)
        selection = list(_sel_of(vp)) if vp else []
        if not selection and scene and hasattr(scene, "selection"):
            selection = list(scene.selection)

        terrain = find_terrain_group(scene, selection)
        if terrain is None:
            _show_status(self._app, tr("msg_no_terrain"), 3000)
            return

        try:
            triangles = extract_triangles_from_group(terrain)
            stats = calculate_mesh_statistics(triangles)
            slope_info = calculate_slope_distribution(triangles)
            stats.update(slope_info)

            dlg = TerrainReportDialog(stats, parent=self)
            dlg.exec()
        except Exception as e:
            _show_status(self._app, f"{tr('err_label')}: {e}", 4000)

    def _on_apply_slope_analysis(self):
        vp = resolve_viewport(self._app)
        scene = resolve_scene(self._app, vp)
        selection = list(_sel_of(vp)) if vp else []
        if not selection and scene and hasattr(scene, "selection"):
            selection = list(scene.selection)

        terrain = find_terrain_group(scene, selection)
        if terrain is None:
            _show_status(self._app, tr("msg_no_terrain"), 3000)
            return

        try:
            dist = op_apply_slope_analysis(self._app, terrain)
            triangles = extract_triangles_from_group(terrain)
            self.lbl_slope_avg.setText(f"{dist['avg_slope_pct']:.1f}% ({dist['avg_slope_deg']:.1f}°)")
            self.lbl_slope_max.setText(f"{dist['max_slope_pct']:.1f}% ({dist['max_slope_deg']:.1f}°)")
            areas = dist.get("band_areas", [0.0] * 10)
            pcts = dist.get("band_pcts", [0.0] * 10)
            for i in range(10):
                lbl = getattr(self, f"lbl_slope_band{i}", None)
                if lbl is not None and i < len(areas) and i < len(pcts):
                    lbl.setText(f"{areas[i]:.2f} m² ({pcts[i]:.1f}%)")

            msg = tr("msg_slope_applied", n=len(triangles), avg=dist["avg_slope_pct"], max=dist["max_slope_pct"])
            _show_status(self._app, msg, 5000)
        except Exception as e:
            import traceback
            err = f"{tr('err_title_slope')}:\n\n{e}\n\n{traceback.format_exc()}"
            log.exception(err)
            try:
                QMessageBox.critical(self, tr("err_title_slope"), f"{tr('err_label')}:\n\n{err}")
            except Exception:
                pass
            _show_status(self._app, f"{tr('err_title_slope')}: {e}", 4000)

    def _on_reset_terrain_colors(self):
        vp = resolve_viewport(self._app)
        scene = resolve_scene(self._app, vp)
        selection = list(_sel_of(vp)) if vp else []
        if not selection and scene and hasattr(scene, "selection"):
            selection = list(scene.selection)

        terrain = find_terrain_group(scene, selection)
        if terrain is None:
            _show_status(self._app, tr("msg_no_terrain"), 3000)
            return

        ok = op_reset_terrain_colors(self._app, terrain)
        _show_status(self._app, tr("msg_colors_reset"), 4000)

    def _on_create_skirt(self):
        vp = resolve_viewport(self._app)
        scene = resolve_scene(self._app, vp)
        selection = list(_sel_of(vp)) if vp else []
        if not selection and scene and hasattr(scene, "selection"):
            selection = list(scene.selection)

        terrain = find_terrain_group(scene, selection)
        if terrain is None:
            _show_status(self._app, tr("msg_no_terrain"), 3000)
            return

        depth = self.sp_skirt_depth.value()
        mat_text = self.cb_skirt_mat.currentText()
        mat_name = "Concrete / Paving" if ("Beton" in mat_text or "Concrete" in mat_text) else "Soil / Ground"

        try:
            solid_grp = op_create_terrain_skirt(
                self._app,
                terrain,
                depth_offset=depth,
                material_name=mat_name,
            )
            base_z = solid_grp.ext.get(PLUGIN_KEY, {}).get("base_z", 0.0) if hasattr(solid_grp, "ext") else 0.0
            msg = tr("msg_skirt_created", z=base_z, walls="OK", caps="OK")
            _show_status(self._app, msg, 5000)
        except Exception as e:
            import traceback
            err = f"{tr('err_title_skirt')}:\n\n{e}\n\n{traceback.format_exc()}"
            log.exception(err)
            try:
                QMessageBox.critical(self, tr("err_title_skirt"), f"{tr('err_label')}:\n\n{err}")
            except Exception:
                pass
            _show_status(self._app, f"{tr('err_title_skirt')}: {e}", 4000)

    def _generate_contours_from_terrain(self):
        vp = resolve_viewport(self._app)
        scene = resolve_scene(self._app, vp)
        selection = list(_sel_of(vp)) if vp else []
        if not selection and scene and hasattr(scene, "selection"):
            selection = list(scene.selection)

        terrain = find_terrain_group(scene, selection)
        if terrain is None:
            _show_status(self._app, tr("msg_no_terrain"), 3000)
            return

        try:
            triangles = extract_triangles_from_group(terrain)
            segments = generate_terrain_contours(triangles, interval_z=self.sp_interval.value())
            if not segments:
                _show_status(self._app, tr("msg_no_contours_found"), 3000)
                return

            try:
                from core.group import Group
                from core.mesh import Mesh
            except ImportError:
                from .operations import Group, Mesh

            mesh = Mesh()
            for s in segments:
                mesh.add_edge(to_qvector3d(s[0]), to_qvector3d(s[1]))

            grp = Group(mesh=mesh, name=tr("contours_group_name", dz=self.sp_interval.value()))
            grp.xform = QMatrix4x4()
            commit_group_to_scene(self._app, grp, select=True)
            _show_status(self._app, tr("msg_contours_generated", n=len(segments)), 4000)
        except Exception as e:
            import traceback
            err = f"{tr('err_title_contours_gen')}:\n\n{e}\n\n{traceback.format_exc()}"
            log.exception(err)
            try:
                QMessageBox.critical(self, tr("err_title_contours_gen"), f"{tr('err_label')}:\n\n{err}")
            except Exception:
                pass
            _show_status(self._app, f"{tr('err_title_contours_gen')}: {e}", 4000)


# ===========================================================================
# Pomocnicze funkcje widgetów
# ===========================================================================

def _make_double_spin(val, min_v, max_v, step, suffix) -> QDoubleSpinBox:
    s = QDoubleSpinBox()
    s.setRange(min_v, max_v)
    s.setValue(val)
    s.setSingleStep(step)
    s.setSuffix(suffix)
    s.setDecimals(2)
    return s


def _show_status(app: Any, msg: str, ms: int = 4000) -> None:
    vp = resolve_viewport(app)
    if vp and hasattr(vp, "flash_status") and callable(vp.flash_status):
        vp.flash_status(msg, ms)
    win = getattr(app, "window", None) or getattr(app, "main_window", None)
    if win and hasattr(win, "statusBar") and callable(win.statusBar):
        sb = win.statusBar()
        if sb and hasattr(sb, "showMessage"):
            sb.showMessage(msg, ms)


def _set_active_tool(app: Any, tool: Any) -> None:
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


def _sel_of(vp):
    try:
        s = getattr(getattr(vp, 'scene', None), 'selection', None)
        if s is None:
            s = getattr(vp, 'selection', None)
        return list(s) if s else []
    except Exception:
        return []


# Moduł zgodności wstecznej dla klasy panelu
SandboxPanel = GroundBoxPanel
