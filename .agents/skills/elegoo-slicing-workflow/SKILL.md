---
name: elegoo-slicing-workflow
description: >-
  Guidance, best practices, and troubleshooting for slicing 3D models with Elegoo Slicer
  (OrcaSlicer fork) on the Elegoo Centauri Carbon 2 (ECC2). Use whenever preparing prints,
  resolving slicer warnings (floating cantilever, floating regions), configuring PETG bed
  temperatures, choosing between Normal vs Tree supports, or diagnosing multi-plate 3MF files.
---

# Elegoo Slicer (Centauri Carbon 2) Slicing & Troubleshooting Guide

This guide documents verified configurations, common pitfalls, and resolution workflows for slicing functional FDM prints using **Elegoo Slicer** (OrcaSlicer 2.4+ fork) targeting the **Elegoo Centauri Carbon 2 (ECC2)**.

---

## 1. Machine & Environment Setup

* **Target Printer**: Elegoo Centauri Carbon 2 (Build Volume: $256 \times 256 \times 256\text{ mm}$).
* **Slicer Executable**: `/opt/elegoo-slicer/AppRun` (or `/usr/bin/elegoo-slicer`).
* **Active System Profiles**:
  * Machine: `~/.config/ElegooSlicer/system/Elegoo/machine/ECC2/Elegoo Centauri Carbon 2 0.4 nozzle.json`
  * Filament: `~/.config/ElegooSlicer/system/Elegoo/filament/ECC2/Elegoo Rapid PETG @ECC2.json`
  * Process: `~/.config/ElegooSlicer/system/Elegoo/process/ECC2/0.20mm Standard @Elegoo CC2 0.4 nozzle.json`

---

## 2. Common Errors & Exact Solutions

### A. Red Banner: "Cool Plate is not suggested for use printing filament 1 (Elegoo Rapid PETG)..."

* **Symptom**: Slicer prevents slicing or shows a red error banner complaining bed temperature is $0^\circ\text{C}$.
* **Root Cause**: Elegoo Slicer / OrcaSlicer defaults `curr_bed_type` to `"Cool Plate"`. The Rapid PETG profile defines Cool Plate temperature as $0^\circ\text{C}$ (unsupported).
* **Fix**:
  1. In GUI: In the top-left plate dropdown, change **Bed Type** from **Cool Plate** to **Textured PEI Plate**.
  2. In 3MF `Metadata/project_settings.config`:
     ```json
     "curr_bed_type": "Textured PEI Plate",
     "default_bed_type": "4"
     ```
  3. This automatically engages the correct **$70^\circ\text{C}$** bed temperature for Rapid PETG.

---

### B. "Do I click Auto Orient All?" -> NEVER (DON'T)

* **Rule**: **NEVER click "Auto Orient" on pre-oriented CAD / bed STLs.**
* **Why**: Pre-oriented parts have been intentionally rotated so that:
  * Layer lines align with mechanical shear/bending stresses (critical for snap-fit arms).
  * 45° overhangs (like diamond ventilation mesh) are self-supporting.
  * Clicking Auto Orient rotates the model arbitrarily, ruining self-supporting geometry and requiring massive supports.

---

### C. Warning: "...has floating cantilever. Please re-orient the object or enable support generation."

* **Symptom**: The slicer warns of a floating cantilever (e.g. on horizontal snap arms at high Z elevations).
* **Rule**: **DO NOT IGNORE.** If ignored, the printer will extrude molten filament into mid-air, causing spaghetti and structural failure.
* **Support Choice: Normal vs Tree**:
  * **When to use Normal Support (`normal(auto)`) [RECOMMENDED for snap arms]**:
    * If the overhang has a direct vertical line down to the build plate.
    * **Filament Savings**: Consumes drastically less filament (~8.8g vs 50g+ for thick tree trunks).
    * **Print Speed**: Slices and prints significantly faster.
    * **Rigidity**: Forms sturdy, vibration-resistant rectangular vertical columns.
  * **When to use Tree Support (`tree(auto)`)**:
    * Only when the support must reach around or snake past another section of the model to reach the overhang.
* **Essential Support Settings**:
  * **`[x] On build plate only`**: Always enable to prevent support structures from growing on top of finished model surfaces.
  * **`Top Z distance: 0.20 mm` (or `0.25 mm`)**: Critical for PETG. Because PETG adheres strongly, a 0.20–0.25 mm gap ensures clean, tool-free snap-off without tearing the part.

---

### D. Warning: "...has floating regions. Please re-orient the object or enable support generation."

* **Symptom**: Slicer detects that a nominally flat plate has floating islands when flipped face-down on the bed.
* **Root Cause**: Features intended for grip (finger pads, pull ribs) were raised $+0.6$ to $+1.4\text{ mm}$ above the roof plane. Flipping the part face-down rests the entire weight on the tiny raised features, suspending the main plate in mid-air.
* **Design Fix**:
  * In CAD, **deboss / recess** the grip grooves ($-0.6\text{ mm}$ into the surface) like a battery door.
  * The outer face remains 100% planar on the PEI bed ($Z=0$), printing **100% support-free with 0 warnings**.

---

### E. Multi-Plate Tree Support Collision (`Potentially lost branch!`)

* **Symptom**: Slicing multiple tall objects on the same plate with tree support crashes CLI slicer with exit code 155 (`Error: Potentially lost branch!, critical: 1`).
* **Root Cause**: Automatic tree generation calculates branch trajectories that collide between adjacent parts.
* **Solution**:
  * Put parts on **dedicated plates** (`Plate 1`, `Plate 2`, `Plate 3`), or
  * Use separate `.3mf` files per part (e.g. `01_front_case.3mf`, `02_back_case.3mf`, `03_service_lid.3mf`).

---

## 3. Recommended Process Profile for Functional PETG Parts

| Setting | Recommended Value | Reason |
| :--- | :--- | :--- |
| **Layer Height** | `0.20 mm` Standard | Optimal balance of layer adhesion and detail |
| **Wall Loops** | `3` (1.2 mm solid perimeter) | Essential for snap-fit spring arm flexural strength |
| **Sparse Infill** | `15% Gyroid` | Isotropic load bearing; no crossing grid collisions |
| **Top / Bottom Shells**| `4` solid layers | Prevents pillowing and ensures watertight roofs |
| **Nozzle Temp** | `250°C` (Rapid PETG) | Maximum inter-layer bond strength |
| **Bed Temp** | `70°C` (Textured PEI) | Reliable first layer adhesion without warping |
| **Cooling Fan** | `20% - 50%` | Moderate cooling prevents PETG brittleness |

---

## 4. Headless CLI Slicing Commands

Run headless slicing and capture machine results:

```bash
# 1. Slice a 3MF file to check validity and warnings
/opt/elegoo-slicer/AppRun \
  --slice 0 \
  --outputdir /tmp \
  /path/to/project.3mf && cat /tmp/result.json

# 2. Slice with explicit custom process JSON
/opt/elegoo-slicer/AppRun \
  --load-settings "/path/to/custom_process.json;/home/indra/.config/ElegooSlicer/system/Elegoo/machine/ECC2/Elegoo Centauri Carbon 2 0.4 nozzle.json" \
  --load-filaments "/home/indra/.config/ElegooSlicer/system/Elegoo/filament/ECC2/Elegoo Rapid PETG @ECC2.json" \
  --slice 0 \
  --outputdir /tmp \
  /path/to/model.stl && cat /tmp/result.json
```

A clean, successful slice returns:
```json
{
  "error_string": "Success.",
  "return_code": 0,
  "sliced_plates": [
    {
      "id": 1,
      "warning_message": ""
    }
  ]
}
```
