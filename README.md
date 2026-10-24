# 🏔️ IngeGroundBox – Engineering Terrain Modeling (TIN) & openBIM for IngeTrazo

<div align="center">

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![IngeTrazo Compatibility](https://img.shields.io/badge/IngeTrazo-v0.5.8%20%7C%20v0.6%2B-brightgreen.svg)](https://github.com/ingelibre/ingetrazo)
[![Extension Catalog](https://img.shields.io/badge/Catalog-ingetrazo.com%2Fextensiones-blueviolet.svg)](https://ingetrazo.com/en/extensiones)
[![BIM: openBIM IFC](https://img.shields.io/badge/BIM-IfcSite%20%7C%20IfcRoad%20%7C%20IfcGeotech-orange.svg)](https://technical.buildingsmart.org/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Languages](https://img.shields.io/badge/UI%20Languages-English%20%7C%20Polski-yellow.svg)](#-multilingual-support)

**The ultimate civil engineering, landscape design, and TIN terrain modeling toolkit for the IngeTrazo 3D CAD/BIM ecosystem.**

[Overview](#-overview) • [Core Tools](#-the-7-core-terrain-tools) • [Engineering Features](#-advanced-engineering--openbim-features) • [Installation](#-installation-guide) • [Quickstart](#-quickstart--usage-guide) • [Catalog Discovery](#-ingetrazo-catalog--web-discovery) • [Documentation](#-documentation)

---

</div>

> 🌐 **Languages:** 🇬🇧 **English** | 🇵🇱 [Przejdź do wersji polskiej (README_PL.md)](README_PL.md)  
> 📖 **Full Guides:** 📘 [Comprehensive User Manual (English)](MANUAL_EN.md) | 📕 [Kompletna Instrukcja Obsługi (Polski)](MANUAL_PL.md)

---

## 🌍 Overview

**IngeGroundBox** is a high-precision terrain modeling (TIN – *Triangulated Irregular Network*) and civil infrastructure extension for the open-source CAD/BIM platform **IngeTrazo**.

Inspired by the iconic *Sandbox Tools* from SketchUp, **IngeGroundBox** completely reinvents and upgrades the concept for professional architectural, civil engineering, and landscape workflows. It bridges intuitive tactile 3D mesh sculpting with rigorous **openBIM IFC classification**, **automated earthwork volume estimation (Cut & Fill in $m^3$)**, **contour generation (Contour Slicer)**, **geotechnical slope gradient heatmaps**, and **one-click quantity takeoff reports (CSV)**.

```
       [ Geo-Survey Lines / Contours ]        [ Architectural Footprint ]
                     │                                     │
                     ▼                                     ▼
        ┌─────────────────────────┐           ┌─────────────────────────┐
        │   From Contours (TIN)   │           │    Stamp & Batters      │
        │  (Bowyer-Watson Delaunay│           │ (Cut & Fill calculation)│
        └────────────┬────────────┘           └────────────┬────────────┘
                     │                                     │
                     └─────────────────┬───────────────────┘
                                       ▼
                       ┌───────────────────────────────┐
                       │   IngeGroundBox Sculpting     │
                       │   • Smoove (Cosine falloff)   │
                       │   • Drape (Road cutting)      │
                       │   • Add Detail (Conforming)   │
                       │   • Flip Edge (Drainage fix)  │
                       └───────────────┬───────────────┘
                                       │
                     ┌─────────────────┴─────────────────┐
                     ▼                                   ▼
          ┌─────────────────────┐             ┌─────────────────────┐
          │     openBIM IFC     │             │ Engineering Reports │
          │  IfcSite / IfcRoad  │             │   Area 3D, ΔZ, CSV  │
          └─────────────────────┘             └─────────────────────┘
```

---

## 🛠️ The 7 Core Terrain Tools

IngeGroundBox integrates seamlessly into IngeTrazo's main interface with a dedicated top toolbar, dockable sidebar panel, and interactive viewport gizmos:

| Icon | Tool Name | Viewport Trigger | Description & Engineering Purpose |
| :---: | :--- | :--- | :--- |
| <img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/border-all.svg" width="20"/> | **From Scratch** | 3 Viewport Clicks | Generates a horizontal rectangular terrain TIN grid with customizable size, elevation, and cell resolution. Features an alternating diagonal (*diamond / checkerboard pattern*) to eliminate directional bias during sculpting, or classic uniform diagonals. |
| <img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/water.svg" width="20"/> | **From Contours** | Select Curves → Click | Reconstructs a seamless 3D topographic TIN surface from imported surveyor contour curves, splines, arcs, or spot height points using adaptive curve densification and Bowyer-Watson Delaunay triangulation with boundary pruning. |
| <img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/brush.svg" width="20"/> | **Smoove** | Click & Drag Vertically | Organic soft-selection brush sculpting in the vertical Z-axis. Features real-time viewport radius gizmo, four falloff profiles (*Cosine, Gaussian, Linear, Smoothstep*), and non-destructive `Ctrl+Z` Undo/Redo. |
| <img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/stamp.svg" width="20"/> | **Stamp** | Footprint → Click Terrain | Stamps building footprints, terraces, or foundation pads into sloping ground. Generates a level pad at target or automatic average elevation and creates transition batter slopes with custom offsets. |
| <img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/road.svg" width="20"/> | **Drape** | Lines & Mesh → Click | Projects 2D road centerlines, sidewalks, park trails, or site boundaries vertically onto 3D terrain. Uses exact planar knife-cutting to split triangles cleanly and automatically tags road ribbons with materials and IFC classes. |
| <img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/circle-plus.svg" width="20"/> | **Add Detail** | Click Face or Edge | Locally subdivides clicked triangles or edges into 4 smaller triangles with neighbor edge bisection to avoid cracks and T-junctions. Supports bulk selection subdivision for high-density landscaping areas. |
| <img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/arrows-rotate.svg" width="20"/> | **Flip Edge** | Click Shared Edge | Flips the shared diagonal between two adjacent triangles in any convex quad. Essential for correcting terrain ridgelines, swales, valley bottoms, and water drainage flow paths. |

---

## 🌟 Advanced Engineering & openBIM Features

### 🚜 1. Earthwork Quantities (Cut & Fill in $m^3$)
When stamping building pads or grading platforms, IngeGroundBox calculates exact earthwork volumetric displacements via triangular prismoidal integration:
* **$V_{\text{cut}}$ (Excavation):** Soil volume to be excavated from hillsides.
* **$V_{\text{fill}}$ (Embankment):** Soil volume to be deposited and compacted.
* **$\Delta V$ (Net Balance):** Net surplus or deficit, enabling instant earthwork mass balancing.

### 🏛️ 2. Native openBIM IFC Classification
All generated geometries are tagged out-of-the-box according to international buildingSMART standards:
* **`IfcSite` / `IfcGeotechnicalStratum`:** Topographic terrain surfaces.
* **`IfcRoad`:** Roads, driveways, pavements, and paths projected via Drape.
* **`IfcEarthworksFill` / `IfcFooting`:** Stamped construction pads and engineered slopes.

### 📈 3. Contour Slicer (Auto-Contouring)
Convert any imported 3D mesh or sculpted landscape into surveyor contour maps. The Slicer cuts through the terrain at customizable vertical intervals ($\Delta Z$, e.g., every 0.5 m, 1.0 m, or 2.0 m) and generates smooth 3D polyline contours ready for drafting or CAD export.

### 🎨 4. Geotechnical Slope Analysis & Gradient Heatmap
Analyze slope steepness across the entire site using 10 civil engineering and urban planning gradient brackets (0% to 100%+):
* 🟢 **0 – 5% (Flat):** Ideal for foundations, pedestrian plazas, sports fields.
* 🟢 **5 – 10% (Gentle):** Suitable for accessible ramps, sidewalks, local roads.
* 🟡 **10 – 20% (Moderate / Rolling):** Vehicular access ramps, mountain accessways.
* 🟠 **20 – 50% (Steep / Embankment):** Requires structural terracing or geotechnical slope stabilization (1:2).
* 🔴 **50 – 100% (Engineered Cuts 1:1.5 to 1:1):** Riprap or reinforced earth required.
* 🟣 **> 100% (Cliff / Wall >45°):** Retaining walls and sheer rock escarpments.
*(Non-destructive: original materials can be restored with a single click via `↺ Reset Original Materials`).*

### 📦 5. Watertight 3D Solid Base (Skirt)
Open 2.5D surfaces cannot be 3D printed or used for volumetric geotechnical solid representations. With **3D Solid Base (Skirt)**:
* Traces outer boundary loops (convex or concave).
* Extrudes vertical side skirts down to $Z_{\text{base}} = Z_{\min} - \text{offset}$.
* Closes the bottom with an inverted planar cap via ear-clipping triangulation.
* Produces a 100% manifold, watertight solid ready for **STL/OBJ 3D printing** or `IfcGeographicElement` export.

### 📊 6. Quantity Takeoff & CSV Export
The built-in analysis engine computes:
* **True 3D Surface Area ($m^2$)** vs. **Planar Projected 2D Footprint Area ($m^2$)**.
* Extreme elevation bounds ($Z_{\min}, Z_{\max}$) and relief delta ($\Delta Z$).
* Direct one-click export to **CSV** (`utf-8-sig` encoding) for **Microsoft Excel**, **LibreOffice Calc**, and cost-estimation spreadsheets.

### 🎨 7. Dual-Sided Newell Normal Materials
Surfaces feature outward Newell normal calculations with dual-sided materials (`attrs["color"]` on front, `attrs["back_color"]` on reverse) preventing black backface rendering artifacts:
* 🌿 **Natural Grass** (`#6BA652`)
* 🪵 **Soil / Ground** (`#8C7054`)
* 🏖 **Sand** (`#D1BF8C`)
* 🪨 **Rock** (`#99999E`)
* 🛣 **Road Asphalt** (`#47474D`)
* 🧱 **Paving / Concrete** (`#B8B8BD`)

---

## 🚀 Installation Guide

### Prerequisites
* **IngeTrazo** v0.5.8, v0.6+, or v1.x ([Download IngeTrazo](https://ingetrazo.com/))
* OS: **Windows 10 / 11** (64-bit), **Linux** (Ubuntu, Debian, Fedora, Arch), or **macOS**

---

### Option A: Automatic via IngeTrazo Extension Manager (Recommended)
1. Open **IngeTrazo**.
2. Go to the top menu: **`Extensions ▸ Manage extensions…`** (or browse [ingetrazo.com/en/extensiones](https://ingetrazo.com/en/extensiones)).
3. Search for **`IngeGroundBox`**.
4. Click **Install**. IngeTrazo will download, verify the package checksum, and activate it automatically!

---

### Option B: Manual Installation (ZIP / Git)

#### Step 1: Download the Extension
Clone the repository or download the latest release ZIP:
```bash
git clone https://github.com/your-username/Inge_GroundBox.git
```

#### Step 2: Copy to IngeTrazo Plugins Directory
Place `inge_groundbox.py` and the `inge_groundbox/` directory into your IngeTrazo user plugins folder:

* **🪟 Windows:**
  ```text
  %APPDATA%\ingetrazo\plugins\
  ```
  *(Typical path: `C:\Users\<YourUser>\AppData\Roaming\ingetrazo\plugins\`)*

  *Quick PowerShell command:*
  ```powershell
  Copy-Item -Path "inge_groundbox.py", "inge_groundbox" -Destination "$env:APPDATA\ingetrazo\plugins\" -Recurse -Force
  ```

* **🐧 Linux:**
  ```text
  ~/.local/share/ingetrazo/plugins/
  ```
  *(Respects `$XDG_DATA_HOME/ingetrazo/plugins/`)*

  *Quick Bash command:*
  ```bash
  mkdir -p ~/.local/share/ingetrazo/plugins/
  cp -r inge_groundbox.py inge_groundbox ~/.local/share/ingetrazo/plugins/
  ```

#### Step 3: Restart IngeTrazo
Restart IngeTrazo. You will immediately see:
1. The **GroundBox Toolbar** with 7 vector icons.
2. The **GroundBox Terrain** submenu under **Extensions**.
3. The dockable **GroundBox** sidebar panel.

---

## ⚡ Quickstart & Usage Guide

```
+-------------------------------------------------------------------------+
| [⬡] [〰] [🖌] [🔲] [⬇] [➕] [🔄]  <-- GroundBox Toolbar (Top Viewport)    |
+------------------------------------------+------------------------------+
|                                          | [ GroundBox Panel (EN | PL)] |
|                                          | ---------------------------- |
|                                          | [x] From Scratch  [x] Smoove |
|          3D Viewport Workspace           | [x] Stamp         [x] Drape  |
|                                          | [x] Mesh Details  [x] Report |
|                                          | ---------------------------- |
|                                          |  • Sliders, numeric inputs   |
|                                          |  • Slope heatmap & reports   |
|                                          |  • One-click CSV export      |
+------------------------------------------+------------------------------+
```

### 1. Generating a Site Mesh (From Scratch)
1. Click the **From Scratch** icon (⬡) or open the panel tab.
2. In the viewport, click 3 times:
   * **Click 1:** Site origin ($P_0$).
   * **Click 2:** Length and orientation ($P_1$).
   * **Click 3:** Width ($P_2$).
3. A clean triangular TIN grid is generated and ready for sculpting.

### 2. Triangulating Contours (From Contours)
1. Select your imported DXF/CAD contour curves or drawn 3D lines.
2. Click **From Contours** (〰).
3. Set your curve densification step and boundary pruning factor.
4. Click **OK** – the terrain is constructed via Bowyer-Watson Delaunay triangulation.

### 3. Sculpting Hills & Depressions (Smoove)
1. Activate the **Smoove** tool (🖌).
2. Adjust your **Brush Radius** and **Strength** in the sidebar.
3. Move your cursor over the terrain (red circle indicates radius).
4. Click and drag vertically. Release to commit, or press `Esc` to cancel.

### 4. Creating a Building Pad (Stamp)
1. Select a 2D or 3D closed footprint polygon positioned over the terrain.
2. Activate **Stamp** (🔲) and click on the terrain.
3. Set batter slope offset and pad elevation.
4. Click **Execute** – the pad is cut/filled, and volume displacment ($m^3$) is reported in the status bar!

### 5. Imprinting Roads & Borders (Drape)
1. Draw road centerlines or boundaries above the terrain.
2. Select both the lines and the terrain group.
3. Click **Drape** (⬇).
4. Set road width (0.0 m for knife cut, >0.0 m for asphalt ribbon).
5. Click **Apply Drape** – the mesh is partitioned with crisp road materials.

---

## ⌨️ Shortcuts & Interaction Reference

| Action | Viewport Trigger | Notes |
| :--- | :--- | :--- |
| **From Scratch (Interactive)** | Toolbar ⬡ or Side Panel | 3 clicks: Origin → Axis/Length → Width |
| **From Contours** | Select curves → Toolbar 〰 | Automatic Bowyer-Watson triangulation |
| **Smoove Sculpting** | Click mesh → Drag up/down | `Esc` cancels drag, LMB commits |
| **Stamp Construction Pad** | Select footprint → Click Stamp → Click terrain | Pad + transition slopes + Cut/Fill $m^3$ |
| **Drape Roads/Paths** | Select line(s) & terrain → Click Drape | Planar knife slicing + road material |
| **Add Detail** | Click triangle or edge | Subdivides 1-to-4 with neighbor bisection |
| **Flip Edge** | Click common quad diagonal | Swaps diagonal between 2 triangles |
| **Undo / Redo** | `Ctrl+Z` / `Ctrl+Y` | Full transactional history support |

---

## 🌐 IngeTrazo Catalog & Web Discovery

To ensure automated scrapers and bots index your extension on **[ingetrazo.com/en/extensiones](https://ingetrazo.com/en/extensiones)**:

### 1. Repository Topics / Tags
When hosting on GitHub, add the following topics to your repository settings (under the ⚙️ *About* section on the repository homepage):
```text
ingetrazo, ingetrazo-extension, ingetrazo-plugin, bim, cad, terrain, tin-mesh, earthworks, civil-engineering, python
```

### 2. Metadata Manifest (`extension.toml` / `inge_groundbox.toml`)
This repository includes a compliant **`extension.toml`** and **`inge_groundbox.toml`** adhering to the IngeTrazo extension schema:
```toml
id = "inge_groundbox"
name = "IngeGroundBox"
version = "1.0.0"
author = "IngeTrazo Community"
description = "Advanced Engineering Terrain Modeling (TIN), Sculpting & openBIM for IngeTrazo."
repository = "https://github.com/<your-username>/Inge_GroundBox"
license = "GPL-3.0-or-later"
min_ingetrazo_version = "0.5.8"
entrypoint = "inge_groundbox.py"
tags = ["terrain", "tin", "bim", "civil-engineering", "earthworks", "sandbox"]
```

### 3. Listing in the Official Catalog
To submit your extension to the official IngeTrazo catalog:
1. Fork [ingelibre/ingetrazo-extensions](https://github.com/ingelibre/ingetrazo-extensions).
2. Copy `inge_groundbox.toml` into `extensions/inge_groundbox.toml`.
3. Open a Pull Request. Once approved, the extension will appear on [ingetrazo.com/en/extensiones](https://ingetrazo.com/en/extensiones) and inside the in-app Extension Manager!

---

## 📦 Package Architecture

```text
Inge_GroundBox/
├── .github/workflows/         # Automated release & packaging workflow
│   └── release.yml            # Creates ZIP archive + SHA256 checksum on release
├── .gitignore                 # Excludes cache, bytecode, and IDE files
├── LICENSE                    # GNU General Public License v3.0 (GPL-3.0-or-later)
├── extension.toml             # Extension catalog manifest (IngeTrazo schema)
├── inge_groundbox.toml        # Official catalog entry for ingelibre/ingetrazo-extensions
├── inge_groundbox.py          # Top-level plugin bootstrap loader
├── README.md                  # International documentation (English)
├── README_PL.md               # Polish documentation (Polski)
├── MANUAL_EN.md               # Comprehensive User Manual (English)
├── MANUAL_PL.md               # Instrukcja Obsługi krok po kroku (Polski)
└── inge_groundbox/            # Core Python package
    ├── __init__.py            # setup(app), Toolbar, Menus, Context Menu hooks
    ├── constants.py           # BIM classes, default tolerances, materials
    ├── i18n.py                # Dual-language dictionary (EN / PL) & tr() helper
    ├── geometry.py            # Delaunay, ray-casting, falloff, 2D/3D math
    ├── terrain_mesh.py        # Mesh generators (From Scratch, Contours, Stamp, Drape)
    ├── groundbox_core.py      # Undo/Redo commands, knife-cutting, mesh rebuilding
    ├── operations.py          # IngeTrazo API adapters (viewport, history, BIM tagging)
    ├── tools.py               # Interactive viewport tools (AddDetail, Smoove, Stamp...)
    ├── interactive.py         # Dynamic interactive flows (3-click From Scratch, Smoove drag)
    ├── icons.py               # High-DPI scalable vector SVG icons and QIcon factory
    ├── dialogs.py             # Native Qt parameter dialogs and CSV export window
    ├── ui.py                  # Dockable side panel (GroundBoxPanel) with tabbed controls
    └── math_utils.py          # Linear algebra & geometric helper routines
```

---

## 🌐 Multilingual Support

IngeGroundBox features comprehensive built-in dual-language localization:
* **🇬🇧 English (EN):** Default for international users.
* **🇵🇱 Polski (PL):** Automatically detected on Polish system locales.
* **Instant Switching:** Change language on the fly using the selector at the top of the GroundBox side panel.

---

## 🤝 Contributing

Contributions, bug reports, and suggestions are warmly welcome!
1. Fork the Project.
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
3. Commit your Changes (`git commit -m 'Add AmazingFeature'`).
4. Push to the Branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## 📄 License

Distributed under the **GNU General Public License v3.0 (GPL-3.0-or-later)**. See [LICENSE](LICENSE) for details.  
Proudly developed for the **IngeTrazo** open-source CAD/BIM ecosystem.
