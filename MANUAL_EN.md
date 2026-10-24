# IngeGroundBox – Comprehensive User Manual

Welcome to the official User Manual for **IngeGroundBox**, the professional engineering terrain modeling and openBIM plugin for **IngeTrazo**.

---

## Table of Contents

1. [Introduction & Core Concepts](#1-introduction--core-concepts)
2. [Installation & Getting Started](#2-installation--getting-started)
3. [User Interface Overview](#3-user-interface-overview)
4. [Tool-by-Tool Guide](#4-tool-by-tool-guide)
   - [4.1 From Scratch (Od podstaw)](#41-from-scratch)
   - [4.2 From Contours (Z warstwic)](#42-from-contours)
   - [4.3 Smoove Sculpting (Wytłaczanie)](#43-smoove-sculpting)
   - [4.4 Stamp Pad & Batters (Odcisk)](#44-stamp-pad--batters)
   - [4.5 Drape Path & Roads (Rzutowanie)](#45-drape-path--roads)
   - [4.6 Add Detail (Dodaj detal)](#46-add-detail)
   - [4.7 Flip Edge (Odwróć krawędź)](#47-flip-edge)
5. [Engineering Calculations & openBIM](#5-engineering-calculations--openbim)
   - [Earthwork Quantities (Cut & Fill)](#51-earthwork-quantities-cut--fill)
   - [Contour Slicer (Auto-Contouring)](#52-contour-slicer-auto-contouring)
   - [Surface Area & Elevation Reports](#53-surface-area--elevation-reports)
   - [openBIM IFC Export](#54-openbim-ifc-export)
6. [Best Practices & Troubleshooting](#6-best-practices--troubleshooting)

---

## 1. Introduction & Core Concepts

### What is a TIN Mesh?
A **TIN (Triangulated Irregular Network)** is a vector-based digital representation of the Earth's surface formed by an irregular network of contiguous, non-overlapping triangles. Unlike a regular raster heightmap (DEM), a TIN can:
* Adapt locally to high-relief areas (steep slopes, retaining walls, road curbs).
* Maintain sharp elevation discontinuities without stepping artifacts.
* Carry geometric and semantic BIM attributes (materials, boundary classifications).

### Why IngeGroundBox?
In standard CAD tools, working with terrain is often cumbersome. **IngeGroundBox** brings the ease and fluid tactile feel of SketchUp Sandbox into **IngeTrazo**, coupled with civil engineering precision:
* 100% non-destructive with native Undo/Redo (`Ctrl+Z`).
* Conforming topology without cracking or hanging nodes.
* Automatic IFC classification for BIM projects.

---

## 2. Installation & Getting Started

### Installation Paths
Copy `inge_groundbox.py` and the `inge_groundbox/` folder into your IngeTrazo plugins directory:

* **Windows:**
  ```text
  %APPDATA%\ingetrazo\plugins\
  ```
  *(Full path: `C:\Users\<Username>\AppData\Roaming\ingetrazo\plugins\`)*
* **Linux:**
  ```text
  ~/.local/share/ingetrazo/plugins/
  ```

### Verification
Upon launching IngeTrazo:
1. A new toolbar named **GroundBox** appears at the top of your main viewport.
2. The **GroundBox** menu appears under **Extensions**.
3. The **GroundBox** dock panel appears in your sidebar tray.
4. Right-clicking any terrain or contour selection displays contextual GroundBox actions.

---

## 3. User Interface Overview

IngeGroundBox provides three complementary UI methods:

```
┌────────────────────────────────────────────────────────────────────────┐
│ [⬡] [〰] [🖌] [🔲] [⬇] [➕] [🔄]  <-- Top GroundBox Toolbar             │
├─────────────────────────────────────────┬──────────────────────────────┤
│                                         │ ╔══════════════════════════╗ │
│                                         │ ║ GroundBox Panel [🇬🇧 EN] ║ │
│                                         │ ╠══════════════════════════╣ │
│                                         │ ║ [From Scratch] [Smoove]  ║ │
│                                         │ ║ [Stamp] [Drape] [Mesh]   ║ │
│         3D Viewport Workspace           │ ║ [Analysis & Report]      ║ │
│                                         │ ║                          ║ │
│                                         │ ║  Interactive Controls    ║ │
│                                         │ ║  Sliders, Spinboxes      ║ │
│                                         │ ║  & Export Buttons        ║ │
│                                         │ ╚══════════════════════════╝ │
└─────────────────────────────────────────┴──────────────────────────────┘
```

1. **Toolbar:** Quick one-click activation of all 7 tools.
2. **Side Tray Panel:** Detailed numeric parameter adjustments (brush radius, road widths, materials, reports).
3. **Context Menu:** Right-click directly on selected geometry in the 3D viewport.

---

## 4. Tool-by-Tool Guide

---

### 4.1 From Scratch

Creates a new, horizontal planar terrain grid of uniform triangular cells.

#### Two Operating Modes:
1. **Interactive 3-Click Mode (Recommended):**
   * Click **Draw Terrain Interactively (3 Clicks)** in the side panel or run the tool.
   * **Click 1:** Set the origin / corner point $P_0$.
   * **Click 2:** Set the length and orientation along the X-axis $P_1$.
   * **Click 3:** Set the width along the Y-axis $P_2$.
2. **Numeric Dialog Mode:**
   * Open the **From Scratch** tab in the side panel.
   * Specify **Width X** (e.g. `60.0 m`), **Length Y** (e.g. `60.0 m`), **Grid Spacing** (e.g. `3.0 m`), and **Base Elevation Z**.
   * Choose diagonal pattern:
     * **Alternating (Diamond / Checkerboard):** Naprzemienny – Prevents diagonal bias when sculpting with Smoove.
     * **Uniform (/):** Simple diagonal lines.
   * Click **Generate Terrain Grid**.

> [!TIP]
> A grid spacing between **2.0 m and 5.0 m** is ideal for architectural site modeling. For fine landscaping, use 1.0 m.

---

### 4.2 From Contours

Generates a continuous 3D TIN terrain from surveyor contour curves, splines, or spot elevations.

#### Workflow:
1. Draw or import contour lines at their respective $Z$ elevations (e.g., using Line or Arc tools).
2. Select all contour curves in the viewport or using the Outliner.
3. Click the **From Contours** icon (〰) on the toolbar or side panel.
4. Set triangulation parameters in the dialog:
   * **Max Segment Length:** Curves are automatically densified with vertices at this maximum distance.
   * **Prune Boundary Ratio:** Automatically removes overly elongated triangles on the outer perimeter.
   * **Soft Edges:** Turns on smooth visual shading across internal triangle seams.
5. Click **OK** – the terrain group is constructed and automatically classified as `IfcSite`.

---

### 4.3 Smoove Sculpting

Organic soft-selection brush for vertical sculpting of hills, berms, swales, and ditches.

#### Workflow:
1. Select the **Smoove** tool (🖌) on the toolbar.
2. Set your **Brush Radius ($R$)** and **Brush Strength** in the side panel.
3. Choose the **Falloff Profile**:
   * **Cosine:** Authentic SketchUp profile – smooth S-curve transition from 1.0 at center to 0.0 at radius.
   * **Gaussian:** Bell curve with very soft feathered borders.
   * **Linear:** Conical deformation.
   * **Smoothstep:** Hermite cubic polynomial falloff.
4. **Sculpting in Viewport:**
   * Move the cursor over the terrain – a dynamic red boundary circle shows the brush radius.
   * **Click and drag** vertically (up or down). The mesh deforms interactively in real time.
   * Release the left mouse button to commit the change.
   * Press `Esc` at any time during drag to cancel without modifying geometry.

---

### 4.4 Stamp Pad & Batters

Stamps building footprints, parking lots, or terraces into uneven terrain, generating transition slopes.

#### Workflow:
1. Create a 2D or 3D footprint (a closed polygon, face, or group) representing the building foundation or terrace.
2. Move it above or across the terrain.
3. Select the footprint object.
4. Click the **Stamp** tool (🔲).
5. Click on the target terrain surface.
6. A dialog allows adjusting:
   * **Slope Offset Distance ($d$):** Horizontal width of the transition batter slopes.
   * **Pad Elevation ($Z$):** Height of the flat shelf (or check *Automatic Elevation* to place it at the average terrain height beneath the footprint).
   * **Pad Material:** e.g., Concrete / Paving.
   * **Slope Material:** e.g., Grass or Soil.
7. Click **Execute** – the terrain is stamped, slopes are created, and the status bar displays the exact **Cut** and **Fill** volumes.

---

### 4.5 Drape Path & Roads

Projects 2D road centerlines, walking trails, sidewalks, or property boundaries vertically onto 3D terrain.

#### Workflow:
1. Draw your road centerlines or boundaries above the terrain in the XY plane.
2. Select both the line geometry and the terrain group.
3. Click the **Drape** tool (⬇).
4. In the side panel or dialog:
   * **Road Width = 0.0 m:** Performs a direct knife-cut along the lines, splitting the terrain triangles.
   * **Road Width > 0.0 m (e.g. 4.0 m):** Extrudes a horizontal road ribbon centered along the path and imprints it onto the terrain.
   * Select the **Road Material** (Asphalt, Pavement, Gravel, Park Path).
5. Click **Apply Drape** – the terrain is partitioned, road edges are set to hard (visible), and the road surface receives the chosen material and `IfcRoad` classification.

---

### 4.6 Add Detail

Locally increases mesh resolution in areas requiring fine sculpting without overloading the entire model.

#### Two Modes of Operation:
1. **Interactive Click Mode (Default):**
   * Activate the **Add Detail** tool (➕) from the toolbar or panel.
   * Hover over the terrain and **click on any triangle or edge**.
   * The targeted triangle is immediately subdivided into 4 smaller triangles ($1 \to 4$ midpoint subdivision).
   * **Conforming Bisection:** Adjacent triangles sharing split edges are automatically bisected ($1 \to 2$) to eliminate T-junctions, hanging vertices, and surface cracks.
   * Continue clicking to add detail wherever needed.
2. **Bulk Selection Subdivision:**
   * Select a terrain group or specific faces.
   * In the **TIN Mesh Edit** tab of the side panel, click **Subdivide Selected Triangles (x4)**.

---

### 4.7 Flip Edge

Rotates the shared diagonal between two adjacent triangles in a convex quad.

#### Workflow:
1. Activate the **Flip Edge** tool (🔄).
2. Click on any interior edge between two triangles.
3. If the two triangles form a convex quadrilateral, the diagonal flips to the opposite pair of vertices.
4. **Engineering Uses:**
   * Correct artificial ridges and valleys.
   * Direct stormwater runoff to swales.
   * Ensure grading lines match architectural plans.

---

## 5. Engineering Calculations & openBIM

### 5.1 Earthwork Quantities (Cut & Fill)
During Stamp operations and terrain remodeling, IngeGroundBox calculates prismoidal volume shifts:
$$\Delta V = \sum_{i} A_i \cdot \frac{\Delta z_{i,1} + \Delta z_{i,2} + \Delta z_{i,3}}{3}$$
* **Cut ($m^3$):** Soil removed below the original natural grade.
* **Fill ($m^3$):** Compacted soil placed above the original grade.
* **Net Balance:** $\text{Fill} - \text{Cut}$.

### 5.2 Contour Slicer (Auto-Contouring)
To generate topographical survey lines from your 3D terrain:
1. Open the **Analysis & Report** tab.
2. Enter the **Contour Step ($\Delta Z$)**, e.g., `1.0 m` or `0.5 m`.
3. Click **Generate Contours from Terrain**.
4. 3D polyline contours are generated as separate curve objects at each elevation plane.

### 5.3 Surface Area & Elevation Reports
In the **Analysis & Report** tab, click **Refresh Metrics**:
* **True 3D Surface Area:** Actual area of all sloped triangular facets.
* **Planar 2D Area:** Projected footprint area on the XY plane.
* **Elevation Range:** $Z_{\min}$, $Z_{\max}$, and total relief difference $\Delta Z$.
* **Average & Max Slopes (% and °):** Area-weighted average gradient and maximum local slope.
* **Export to CSV:** Exports all quantities (including slope distribution) to an Excel-ready semicolon-delimited CSV file with `utf-8-sig` encoding.

### 5.4 Slope Analysis & Heatmap
In the **Analysis & Report** tab, this tool computes individual triangle gradient vectors relative to the horizontal plane and visualizes slopes using 10 standard civil engineering and urban planning thresholds covering 0% to 100%+:
* 🟢 **0 – 5% (Flat):** Ideal for building footprints, drainage, and sports fields.
* 🟢 **5 – 10% (Gentle):** Suitable for pedestrian walkways, accessible ramps, and local roads.
* 🟢 **10 – 15% (Moderate):** Upper limit for vehicular access ramps and residential roads.
* 🟡 **15 – 20% (Rolling):** Mountain roads, steep approaches; limit for tractor mowing.
* 🟡 **20 – 30% (Steep):** Stepped construction required; terraced building envelopes.
* 🟠 **30 – 40% (Very Steep):** Natural turf-stabilized embankments (1:3 to 1:2.5).
* 🟠 **40 – 50% (Embankment 1:2):** Standard civil cut/fill slope (26.6°); geotechnical stabilization.
* 🔴 **50 – 70% (Embankment 1:1.5):** Steep engineered slopes (33.7°); riprap or bio-revetment required.
* 🔴 **70 – 100% (Slope 1:1):** Extreme embankments up to 45°; reinforced earth or gabions.
* 🟣 **> 100% (Cliff / Wall >45°):** Retaining walls, bedrock escarpments, and sheer drops.

**How to use:**
1. Select the target terrain group.
2. In the **Analysis & Report** tab, click **🎨 Color Terrain by Slope**.
3. The terrain is dynamically shaded with heatmap colors and the area breakdown table is populated.
4. To revert to natural grass or paved materials, click **↺ Reset Original Materials** (the operation is 100% non-destructive).

### 5.5 Watertight 3D Solid Base (Skirt)
Standard CAD terrains are open 2.5D surfaces without true solid volume. To convert an open TIN surface into a solid block:
1. Select the terrain group.
2. In the **Analysis & Report** tab, specify the **Base depth offset (m)** below the lowest terrain point $Z_{\min}$ (default `1.0 m`).
3. Choose the wall/base material (e.g. *Soil / Ground* or *Concrete Substructure*).
4. Click **📦 Create 3D Solid Base (Skirt)**.
5. The algorithm traces perimeter loops, extrudes vertical side walls, and caps the base using ear-clipping polygon triangulation. The resulting geometry is a **0-boundary-edge 100% Manifold Solid** classified under BIM as **`IfcGeographicElement`** (*Solid Terrain Base*), ready for 3D printing and geomechanical cut/fill sectioning.

### 5.6 openBIM IFC Export
IngeGroundBox automatically tags your components with buildingSMART standard IFC classes:
* Terrain surface $\to$ **`IfcSite`**
* Sub-grade stratum $\to$ **`IfcGeotechnicalStratum`**
* Draped road corridors $\to$ **`IfcRoad`**
* Solid terrain base $\to$ **`IfcGeographicElement`**

When exporting your IngeTrazo project to IFC (`File ▸ Export ▸ IFC`), your terrain is recognized by BIM coordinators in Revit, ArchiCAD, Tekla, and Solibri.

---

## 6. Best Practices & Troubleshooting

| Issue | Solution |
| :--- | :--- |
| **"No terrain group found" message** | Ensure your terrain is grouped. If loose mesh, select it and create a Group, or name the group "Terrain" / "Teren". |
| **Triangles stretching too far on borders** | When using *From Contours*, increase the *Prune Boundary Ratio* or manually trim outer edges. |
| **Sculpting performance feels slow** | Use *Add Detail* only in specific zones where you need smooth curves; avoid subdividing the entire 100,000-face terrain unnecessarily. |
| **Lines not cutting terrain during Drape** | Ensure your lines extend completely across the intended boundary and lie above the terrain surface in the XY plane. |
| **Language change** | Select **English** or **Polski** in the dropdown located at the top-right corner of the GroundBox sidebar panel. |
