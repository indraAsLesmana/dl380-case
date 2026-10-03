# DL380 4-Piece Modular Enclosure - Slicing & Assembly Guide

The **4-Piece Modular Architecture** separates the enclosure horizontally along the mid-deck shelf, eliminating nearly 100% of internal supports and dividing the print into small, manageable batches.

---

## 1. Slicing Benchmark Results (Elegoo Centauri Carbon 2)

*Sliced with Elegoo Slicer CLI (OrcaSlicer 2.4 engine) using Rapid PETG @ECC2 (0.20mm Standard, 4 walls, 15% Gyroid infill).*

| Deliverable (.3mf) | Support Configuration | Filament Usage | Estimated Print Time |
| :--- | :--- | :--- | :--- |
| `01A_dl380_lower_front.3mf` | None (100% Support-Free) | **163.5 g** | **9h 46m 44s** |
| `01B_dl380_upper_front.3mf` | None (100% Support-Free) | **364.4 g** | **1d 4h 34m 59s** |
| `02A_dl380_lower_back.3mf` | None (100% Support-Free) | **98.0 g** | **6h 1m 8s** |
| `02B_dl380_upper_back.3mf` | Normal Auto (Build Plate) | **307.1 g** | **23h 47m 44s** |
| `03_dl380_service_lid.3mf` | None (100% Support-Free) | **17.0 g** | **1h 2m 10s** |
| **TOTAL ASSEMBLY** | — | **950.1 g** | **~2.8 days total (spread over 5 fast plates)** |

---

## 2. Key Printing Advantages Over Monolithic 2-Piece

1. **Parts 01A, 01B, 02A, and 03 are 100% Support-Free**:
   - The Lower cases print right-side up like open shallow trays ($60.5\text{ mm}$ tall with corner snap pillars).
   - The Upper Front case prints with its flat rear mating face on the PEI bed; runner rails, bezel shelf, and $45^\circ$ diamond mesh print straight up with zero supports.
   - Only Part 02B requires minor build-plate support under the front snap latch arms (~$8\text{ g}$).
2. **Fast, Low-Risk Printing**:
   - Lower Back prints in only **~5.5 hours** (~$99\text{ g}$).
   - Lower Front prints in only **~9 hours** (~$164\text{ g}$).
   - No single part takes longer than ~30 hours. If a print is interrupted, you only reprint a single quadrant.
3. **Zero Tunnel Support Extraction**:
   - No digging pliers into deep enclosed chambers.

---

## 3. Tool-Free Snap-Fit Assembly Sequence

```
Step 1: Click Upper Front (01B) down onto Lower Front (01A)
        ┌───────────────────────┐
        │  Upper Front (01B)    │  <── Drive cage bay & bezel
        ├═══════════════════════┤  <── 4x Corner Cantilever Snap Latches CLICK!
        │  Lower Front (01A)    │  <── PSU basement with pusher stops
        └───────────────────────┘

Step 2: Click Upper Back (02B) down onto Lower Back (02A)
        ┌─────────┐
        │ 02B Fan │  <── 92mm fan exhaust + service lid
        ├═════════┤  <── 2x Rear Corner Snap Latches CLICK!
        │ 02A PSU │  <── PSU rear opening & guide rails
        └─────────┘

Step 3: Slide Front Assembly into Rear Assembly
        ┌───────────────────────┬─────────┐
        │   DL380 Drive Cage    │ 92mm Fan│ <── 2x Side Push-Release Latch Arms CLICK!
        ├═══════════════════════╪═════════╡
        │     Flex-ATX PSU      │ AC / SAS│ <── Side-Wall Alignment Tongue-and-Groove
        └───────────────────────┴─────────┘
```
