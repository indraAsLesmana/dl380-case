# DL380 Flex Case - Slicer Auto-Support Comparison Guide

This directory contains the **Clean (Zero CAD Supports)** variant of the DL380 Modular Flex-ATX Case, allowing you to directly test, visualize, and benchmark the slicer's built-in support generation (Normal vs Tree) against our pre-engineered DfAM sacrificial columns.

---

## 1. Head-to-Head Slicing Benchmark Results

*Sourced directly from Elegoo Slicer CLI (OrcaSlicer 2.4 engine) targeting the Elegoo Centauri Carbon 2 with Elegoo Rapid PETG (0.20mm Standard, 4 walls, 15% Gyroid infill).*

| File (.3mf) | Variant | Slicer Support Mode | Total Filament | Estimated Time |
| :--- | :--- | :--- | :--- | :--- |
| `01_dl380_front_case.3mf` | Standard (DfAM Sup) | Normal (Auto, Build-Plate) | **601.0 g** | **1d 21h 58m 33s** |
| `02_dl380_back_case.3mf` | Standard (DfAM Sup) | Normal (Auto, Build-Plate) | **389.8 g** | **1d 5h 4m 29s** |
| `03_dl380_service_lid.3mf` | Lid | Disabled (None) | **18.9 g** | **1h 10m 38s** |
| `01_dl380_front_case_clean_normal_sup.3mf` | Clean (No CAD Sup) | Normal (Auto, Build-Plate) | **491.2 g** | **1d 9h 50m 8s** |
| `01_dl380_front_case_clean_tree_sup.3mf` | Clean (No CAD Sup) | Tree (Auto, Build-Plate) | **777.6 g** | **3d 3h 26m 4s** |
| `01_dl380_front_case_clean_no_sup.3mf` | Clean (No CAD Sup) | Disabled (None) | **490.4 g** | **1d 9h 45m 42s** |
| `02_dl380_back_case_clean_normal_sup.3mf` | Clean (No CAD Sup) | Normal (Auto, Build-Plate) | **345.4 g** | **1d 0h 8m 30s** |
| `02_dl380_back_case_clean_tree_sup.3mf` | Clean (No CAD Sup) | Tree (Auto, Build-Plate) | **538.0 g** | **2d 2h 6m 43s** |
| `02_dl380_back_case_clean_no_sup.3mf` | Clean (No CAD Sup) | Disabled (None) | **337.2 g** | **23h 6m 55s** |

---

## 2. Architectural Comparison: DfAM Built-in vs Slicer Auto-Support

| Feature / Criteria | Standard DfAM Built-in Columns | Slicer Normal Auto Support | Slicer Tree Auto Support |
| :--- | :--- | :--- | :--- |
| **Aperture & Void Access** | Designed for needle-nose pliers removal through existing front/rear windows | Fills large rectangular blocks from the bed | Snakes branches inward from outer bed |
| **Ceiling Finish** | Pre-scored 0.35mm neck + castellated teeth prevent PETG sagging & fusion | May fuse to PETG bridges if Z-gap < 0.20mm | Low contact surface, easy release |
| **Mid-Deck / Cable Hole** | Through-hole column supports both floors from a single rigid foundation | Cannot cross floors without resting on finished parts | Can branch through apertures |
| **Bed Adhesion Stability** | Rigid cubic cross-braced towers (zero deflection under 300 mm/s) | Solid box columns | Tall branches can wobble on high-speed CoreXY |

---

## 3. How to Use These Deliverables in Elegoo Slicer / OrcaSlicer

1. **Pre-configured .3MF Projects**:
   - `01_dl380_front_case_clean_normal_sup.3mf`: Clean Front Case with Slicer Normal Auto-Support configured.
   - `01_dl380_front_case_clean_tree_sup.3mf`: Clean Front Case with Slicer Tree Auto-Support configured.
   - `02_dl380_back_case_clean_normal_sup.3mf`: Clean Back Case with Slicer Normal Auto-Support configured.
   - `02_dl380_back_case_clean_tree_sup.3mf`: Clean Back Case with Slicer Tree Auto-Support configured.
   - `01_dl380_front_case_clean_no_sup.3mf` / `02_dl380_back_case_clean_no_sup.3mf`: Support turned OFF (ideal for custom painting manual support enforcers).
2. **Raw Bed STLs**:
   - `01_front_case_clean_bed.stl`
   - `02_back_case_clean_bed.stl`
   Import these STLs directly if you want to experiment with custom support painted regions, hybrid infill, or different slicer forks.
