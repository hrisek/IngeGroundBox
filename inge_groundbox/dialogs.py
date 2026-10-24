# SPDX-License-Identifier: GPL-3.0-or-later
"""
inge_groundbox/dialogs.py
=======================
Natywne okna dialogowe Qt (PySide6 / PyQt5) dla narzędzi GroundBox:
- FromScratchDialog (parametry tworzenia nowej siatki)
- FromContoursDialog (parametry triangulacji warstwic)
- StampDialog (parametry odcisku i skarpowania)
- DrapeDialog (parametry rzutowania i dróg)
- TerrainReportDialog (raport ilościowy, statystyki i eksport CSV z utf-8-sig)
"""
from __future__ import annotations

import csv
from typing import Any

from .constants import (
    DEFAULT_CONTOURS,
    DEFAULT_DRAPE,
    DEFAULT_FROM_SCRATCH,
    DEFAULT_STAMP,
)
from .i18n import tr

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QDoubleSpinBox,
        QFileDialog,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QMessageBox,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
    )
except ImportError:
    try:
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import (
            QCheckBox,
            QComboBox,
            QDialog,
            QDialogButtonBox,
            QDoubleSpinBox,
            QFileDialog,
            QFormLayout,
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QMessageBox,
            QPushButton,
            QTableWidget,
            QTableWidgetItem,
            QVBoxLayout,
        )
    except ImportError:
        # Fallback dummy dla testów jednostkowych
        class QDialog: pass
        class QDialogButtonBox: pass


# ===========================================================================
# 1. Dialog: Od podstaw (From Scratch)
# ===========================================================================

class FromScratchDialog(QDialog):
    """Okno konfiguracji generowania siatki terenu From Scratch."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("tool_from_scratch"))
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.spin_x = _make_double_spin(DEFAULT_FROM_SCRATCH["size_x"], 1.0, 10000.0, 5.0, " m")
        form.addRow(tr("size_x_label"), self.spin_x)

        self.spin_y = _make_double_spin(DEFAULT_FROM_SCRATCH["size_y"], 1.0, 10000.0, 5.0, " m")
        form.addRow(tr("size_y_label"), self.spin_y)

        self.spin_spacing = _make_double_spin(DEFAULT_FROM_SCRATCH["spacing"], 0.1, 100.0, 0.5, " m")
        form.addRow(tr("spacing_label"), self.spin_spacing)

        self.spin_z = _make_double_spin(DEFAULT_FROM_SCRATCH["base_z"], -1000.0, 5000.0, 1.0, " m")
        form.addRow(tr("base_z_label"), self.spin_z)

        self.cb_pattern = QComboBox()
        self.cb_pattern.addItem(tr("pattern_alternating"), "alternating")
        self.cb_pattern.addItem(tr("pattern_uniform"), "uniform")
        form.addRow(tr("pattern_label"), self.cb_pattern)

        self.cb_material = QComboBox()
        self.cb_material.addItems([tr("mat_grass"), tr("mat_soil"), tr("mat_sand"), tr("mat_rock")])
        form.addRow(tr("material_label"), self.cb_material)

        layout.addLayout(form)

        bbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bbox.accepted.connect(self.accept)
        bbox.rejected.connect(self.reject)
        layout.addWidget(bbox)

    def get_params(self) -> dict[str, Any]:
        return {
            "size_x": self.spin_x.value(),
            "size_y": self.spin_y.value(),
            "spacing": self.spin_spacing.value(),
            "base_z": self.spin_z.value(),
            "pattern": self.cb_pattern.currentData(),
            "material": self.cb_material.currentText(),
        }


# ===========================================================================
# 2. Dialog: Z warstwic (From Contours)
# ===========================================================================

class FromContoursDialog(QDialog):
    """Okno konfiguracji triangulacji warstwic."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("tool_from_contours"))
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)

        info = QLabel(tr("contours_info"))
        info.setWordWrap(True)
        layout.addWidget(info)

        form = QFormLayout()
        self.spin_seg = _make_double_spin(DEFAULT_CONTOURS["max_segment_len"], 0.5, 50.0, 0.5, " m")
        form.addRow(tr("max_seg_len"), self.spin_seg)

        self.spin_prune = _make_double_spin(DEFAULT_CONTOURS["prune_boundary_ratio"], 1.5, 10.0, 0.5, " x")
        form.addRow(tr("prune_boundary"), self.spin_prune)

        self.chk_soft = QCheckBox(tr("soft_edges_label"))
        self.chk_soft.setChecked(DEFAULT_CONTOURS["soft_edges"])
        form.addRow("", self.chk_soft)

        self.cb_material = QComboBox()
        self.cb_material.addItems([tr("mat_grass"), tr("mat_soil"), tr("mat_rock")])
        form.addRow(tr("material_label"), self.cb_material)

        layout.addLayout(form)

        bbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bbox.accepted.connect(self.accept)
        bbox.rejected.connect(self.reject)
        layout.addWidget(bbox)

    def get_params(self) -> dict[str, Any]:
        return {
            "max_segment_len": self.spin_seg.value(),
            "prune_boundary_ratio": self.spin_prune.value(),
            "soft_edges": self.chk_soft.isChecked(),
            "material": self.cb_material.currentText(),
        }


# ===========================================================================
# 3. Dialog: Odcisk (Stamp)
# ===========================================================================

class StampDialog(QDialog):
    """Okno konfiguracji odcisku obrysu w terenie."""

    def __init__(self, parent=None, default_elevation: float = 0.0):
        super().__init__(parent)
        self.setWindowTitle(tr("tool_stamp"))
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)

        info = QLabel(tr("stamp_info"))
        info.setWordWrap(True)
        layout.addWidget(info)

        form = QFormLayout()

        self.spin_offset = _make_double_spin(DEFAULT_STAMP["offset_distance"], 0.1, 50.0, 0.5, " m")
        form.addRow(tr("offset_dist_label"), self.spin_offset)

        self.chk_auto_z = QCheckBox(tr("auto_elev_check"))
        self.chk_auto_z.setChecked(True)
        form.addRow("", self.chk_auto_z)

        self.spin_z = _make_double_spin(default_elevation, -500.0, 5000.0, 0.5, " m")
        self.spin_z.setEnabled(False)
        self.chk_auto_z.toggled.connect(lambda checked: self.spin_z.setEnabled(not checked))
        form.addRow(tr("pad_elevation_label"), self.spin_z)

        self.cb_pad_mat = QComboBox()
        self.cb_pad_mat.addItems([tr("mat_concrete"), tr("mat_terrace_tile"), tr("mat_crushed_stone"), tr("mat_asphalt")])
        form.addRow(tr("pad_material_label"), self.cb_pad_mat)

        self.cb_slope_mat = QComboBox()
        self.cb_slope_mat.addItems([tr("mat_slope_ground"), tr("mat_grass"), tr("mat_stones")])
        form.addRow(tr("slope_material_label"), self.cb_slope_mat)

        layout.addLayout(form)

        bbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bbox.accepted.connect(self.accept)
        bbox.rejected.connect(self.reject)
        layout.addWidget(bbox)

    def get_params(self) -> dict[str, Any]:
        return {
            "offset_distance": self.spin_offset.value(),
            "target_elevation": None if self.chk_auto_z.isChecked() else self.spin_z.value(),
            "pad_material": self.cb_pad_mat.currentText(),
            "slope_material": self.cb_slope_mat.currentText(),
        }


# ===========================================================================
# 4. Dialog: Rzutowanie (Drape)
# ===========================================================================

class DrapeDialog(QDialog):
    """Okno konfiguracji rzutowania linii na teren."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("tool_drape"))
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)

        info = QLabel(tr("drape_info"))
        info.setWordWrap(True)
        layout.addWidget(info)

        form = QFormLayout()

        self.spin_width = _make_double_spin(0.0, 0.0, 30.0, 0.5, " m")
        self.spin_width.setToolTip(tr("road_width_hint"))
        form.addRow(tr("road_width_label"), self.spin_width)

        self.cb_mat = QComboBox()
        self.cb_mat.addItems([tr("mat_asphalt"), tr("mat_paving"), tr("mat_gravel"), tr("mat_path")])
        form.addRow(tr("drape_mat_label"), self.cb_mat)

        layout.addLayout(form)

        bbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bbox.accepted.connect(self.accept)
        bbox.rejected.connect(self.reject)
        layout.addWidget(bbox)

    def get_params(self) -> dict[str, Any]:
        return {
            "road_width": self.spin_width.value(),
            "material": self.cb_mat.currentText(),
        }


# ===========================================================================
# 5. Dialog: Raport terenu i Eksport do CSV
# ===========================================================================

class TerrainReportDialog(QDialog):
    """Wyświetla zestawienie metryk terenu z opcją eksportu do CSV (utf-8-sig)."""

    def __init__(self, stats: dict[str, Any], parent=None):
        super().__init__(parent)
        self._stats = stats
        self.setWindowTitle(tr("terrain_stats_title"))
        self.resize(480, 520)

        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels([tr("table_prop_header"), tr("table_val_header")])
        self.table.horizontalHeader().setStretchLastSection(True)

        rows = [
            (tr("stat_faces"), str(stats.get("face_count", 0))),
            (tr("stat_vertices"), str(stats.get("vertex_count", 0))),
            (tr("stat_3d_area"), f"{stats.get('area_3d', 0.0):.2f} m²"),
            (tr("stat_2d_area"), f"{stats.get('area_2d', 0.0):.2f} m²"),
            (tr("stat_min_z"), f"{stats.get('min_z', 0.0):.2f} m"),
            (tr("stat_max_z"), f"{stats.get('max_z', 0.0):.2f} m"),
            (tr("stat_height_diff"), f"{stats.get('delta_z', 0.0):.2f} m"),
        ]

        if "cut_vol" in stats:
            rows.append((tr("stat_cut_vol"), f"{stats.get('cut_vol', 0.0):.2f} m³"))
        if "fill_vol" in stats:
            rows.append((tr("stat_fill_vol"), f"{stats.get('fill_vol', 0.0):.2f} m³"))
        if "avg_slope_pct" in stats:
            rows.append((tr("stat_avg_slope"), f"{stats.get('avg_slope_pct', 0.0):.1f}% ({stats.get('avg_slope_deg', 0.0):.1f}°)"))
        if "max_slope_pct" in stats:
            rows.append((tr("stat_max_slope"), f"{stats.get('max_slope_pct', 0.0):.1f}% ({stats.get('max_slope_deg', 0.0):.1f}°)"))
        if "band_areas" in stats and "band_pcts" in stats:
            band_names = [tr(f"slope_band_{i+1}") for i in range(10)]
            b_areas = stats.get("band_areas", [])
            b_pcts = stats.get("band_pcts", [])
            for i, name in enumerate(band_names):
                if i < len(b_areas) and i < len(b_pcts):
                    rows.append((f"{tr('stat_slope_band')} {name}", f"{b_areas[i]:.2f} m² ({b_pcts[i]:.1f}%)"))

        self.table.setRowCount(len(rows))
        for r, (prop, val) in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(prop))
            self.table.setItem(r, 1, QTableWidgetItem(val))

        layout.addWidget(self.table)

        btn_box = QHBoxLayout()
        btn_csv = QPushButton("📊  " + tr("btn_export_csv"))
        btn_csv.clicked.connect(self._export_csv)
        btn_box.addWidget(btn_csv)

        btn_close = QPushButton(tr("btn_close"))
        btn_close.clicked.connect(self.accept)
        btn_box.addWidget(btn_close)

        layout.addLayout(btn_box)

    def _export_csv(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, tr("export_csv_title"), "terrain_report.csv", "CSV (*.csv)"
        )
        if not filename:
            return

        try:
            # utf-8-sig for Microsoft Excel & LibreOffice Calc compatibility
            with open(filename, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow([tr("table_prop_header"), tr("table_val_header")])
                for r in range(self.table.rowCount()):
                    prop = self.table.item(r, 0).text()
                    val = self.table.item(r, 1).text()
                    writer.writerow([prop, val])

            QMessageBox.information(
                self, tr("msg_success_title"), tr("export_csv_success", filename=filename)
            )
        except Exception as e:
            QMessageBox.critical(self, tr("err_label"), tr("export_csv_error", e=e))


# ---------------------------------------------------------------------------
# Pomocnik widgetów
# ---------------------------------------------------------------------------

def _make_double_spin(val, min_v, max_v, step, suffix) -> QDoubleSpinBox:
    s = QDoubleSpinBox()
    s.setRange(min_v, max_v)
    s.setValue(val)
    s.setSingleStep(step)
    s.setSuffix(suffix)
    s.setDecimals(2)
    return s
