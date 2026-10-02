# First Layer Bed Level Calibration (256x256 mm)
Target Printer: **Elegoo Centauri Carbon 2 (ECC2)** (Build Volume: $256 \times 256 \times 256\text{ mm}$)

This calibration kit verifies auto-bed-leveling (ABL), bed mesh tilt, and nozzle Z-offset across the entire $256 \times 256\text{ mm}$ textured PEI build plate. It prints **exactly 1 single layer ($Z = 0.20\text{ mm}$)**, consumes under **3 grams of filament**, and completes in **~10 minutes**.

---

## 1. Included Deliverables

| File | Description | Material & Target |
| :--- | :--- | :--- |
| **`bed_level_test_PLA_256x256.3mf`** | **Ready-to-Print 1-Click Project** for CC2 Sample PLA | Nozzle: 215°C, Bed: 60°C (PEI), 1 Layer, 2.89g |
| **`bed_level_test_PETG_256x256.3mf`** | **Ready-to-Print 1-Click Project** for Bambu PETG Basic | Nozzle: 255°C, Bed: 75°C (PEI), 1 Layer, 2.89g |
| **`bed_level_test_connected_256x256.stl`** | 5 Patches ($40 \times 40\text{ mm}$) + connecting perimeter & diagonal runners | **Recommended STL**: Peels off in 1 single sheet! |
| **`bed_level_test_5_squares_256x256.stl`** | 5 detached squares at 4 corners + center ($40 \times 40 \times 0.20\text{ mm}$) | Individual patch verification |
| **`bed_level_test_single_100x100.stl`** | Single centered square ($100 \times 100 \times 0.20\text{ mm}$) | Quick center Z-offset check |

---

## 2. How to Read Your First Layer Test

Inspect the 5 squares (Center, Front-Left, Front-Right, Back-Left, Back-Right) as they print:

1. **PERFECT First Layer (Target)**:
   * Smooth, uniform top surface.
   * Extrusion lines touch each other with **zero gaps** between strands.
   * Surface feels smooth like a plastic card when rubbing your fingernail across it (no rough ridges).
2. **Nozzle Too High (Z-Offset too positive / Gap too large)**:
   * Individual extrusion strands look like loose round spaghetti threads.
   * Visible gaps or daylight between adjacent extrusion lines.
   * Squares easily separate or don't stick to the PEI bed.
   * **Fix**: Lower Z-offset on the printer touchscreen by $-0.02\text{ mm}$ to $-0.05\text{ mm}$.
3. **Nozzle Too Low (Z-Offset too negative / Nozzle dragging)**:
   * Extrusion lines have raised, rough ridges where the nozzle plows through melted plastic.
   * Patch looks transparent or very thin in some spots.
   * Extruder makes clicking/skipping noises.
   * **Fix**: Raise Z-offset on the printer touchscreen by $+0.02\text{ mm}$ to $+0.05\text{ mm}$.

---

## 3. Recommended Slicer Settings

* **Layer Height**: `0.20 mm`
* **First Layer Height**: `0.20 mm`
* **Brim**: `None (OFF)`
* **Support**: `OFF`
* **Bed Type**: `Textured PEI Plate`
* **Sample PLA Settings**: Nozzle `210°C - 215°C`, Bed `55°C - 60°C`
* **Bambu PETG Basic Settings**: Nozzle `250°C - 255°C`, Bed `70°C - 75°C`
