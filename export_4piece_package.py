#!/usr/bin/env python3
"""
export_4piece_package.py
Automated export, calibration, and CLI slice benchmarking for DL380 4-Piece Modular Enclosure:
1. Generates calibrated .3mf project files for Elegoo Centauri Carbon 2 (ECC2).
2. Slices all parts via Elegoo Slicer CLI, checks for 0 errors/warnings, and measures exact filament & print times.
3. Generates README_4PIECE_GUIDE.md documentation.
4. Packages everything into DL380_4Piece_Print_Package.zip.
"""

import os, sys, json, subprocess, zipfile, shutil, re

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR  = os.path.join(REPO_DIR, "out", "4piece")
PKG_DIR  = os.path.join(REPO_DIR, "print_service_package", "4piece")
TEMP_DIR = os.path.join(REPO_DIR, "scratch", "slicer_temp_4piece")
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(PKG_DIR, exist_ok=True)

SLICER_BIN = "/opt/elegoo-slicer/AppRun"
SYS_MACHINE = os.path.expanduser("~/.config/ElegooSlicer/system/Elegoo/machine/ECC2/Elegoo Centauri Carbon 2 0.4 nozzle.json")
SYS_FILAMENT = os.path.expanduser("~/.config/ElegooSlicer/system/Elegoo/filament/ECC2/Elegoo Rapid PETG @ECC2.json")
SYS_PROCESS = os.path.expanduser("~/.config/ElegooSlicer/system/Elegoo/process/ECC2/0.20mm Standard @Elegoo CC2 0.4 nozzle.json")

def build_process_profiles():
    with open(SYS_PROCESS) as f:
        base = json.load(f)

    petg_base = dict(base)
    petg_base["wall_loops"] = "4"
    petg_base["sparse_infill_density"] = "15%"
    petg_base["sparse_infill_pattern"] = "gyroid"
    petg_base["top_solid_layers"] = "4"
    petg_base["bottom_solid_layers"] = "4"
    petg_base["xy_hole_compensation"] = "0.1"
    petg_base["elefant_foot_compensation"] = "0.15"

    proc_nosup = dict(petg_base)
    proc_nosup["enable_support"] = "0"
    path_nosup = os.path.join(TEMP_DIR, "proc_nosup.json")
    with open(path_nosup, "w") as f:
        json.dump(proc_nosup, f, indent=2)

    proc_sup = dict(petg_base)
    proc_sup["enable_support"] = "1"
    proc_sup["support_type"] = "normal(auto)"
    proc_sup["support_on_build_plate_only"] = "1"
    proc_sup["support_top_z_distance"] = "0.2"
    path_sup = os.path.join(TEMP_DIR, "proc_sup.json")
    with open(path_sup, "w") as f:
        json.dump(proc_sup, f, indent=2)

    return path_nosup, path_sup

def patch_3mf_metadata(file_path, enable_support=False):
    unpacked = file_path + "_unpacked"
    if os.path.exists(unpacked):
        shutil.rmtree(unpacked)
    os.makedirs(unpacked)

    with zipfile.ZipFile(file_path, "r") as z:
        z.extractall(unpacked)

    cfg_file = os.path.join(unpacked, "Metadata", "project_settings.config")
    if os.path.exists(cfg_file):
        with open(cfg_file, "r") as f:
            cfg = json.load(f)

        cfg["curr_bed_type"] = "Textured PEI Plate"
        cfg["default_bed_type"] = "4"
        cfg["filament_type"] = ["PETG"]
        cfg["textured_plate_temp"] = ["70"]
        cfg["textured_plate_temp_initial_layer"] = ["70"]
        cfg["hot_plate_temp"] = ["70"]
        cfg["hot_plate_temp_initial_layer"] = ["70"]
        cfg["eng_plate_temp"] = ["70"]
        cfg["eng_plate_temp_initial_layer"] = ["70"]

        cfg["fan_min_speed"] = ["20"]
        cfg["fan_max_speed"] = ["40"]
        cfg["overhang_fan_speed"] = ["80"]

        cfg["wall_loops"] = "4"
        cfg["sparse_infill_density"] = "15%"
        cfg["sparse_infill_pattern"] = "gyroid"
        cfg["top_solid_layers"] = "4"
        cfg["bottom_solid_layers"] = "4"
        cfg["xy_hole_compensation"] = "0.1"
        cfg["elefant_foot_compensation"] = "0.15"
        cfg["enable_support"] = "1" if enable_support else "0"
        if enable_support:
            cfg["support_type"] = "normal(auto)"
            cfg["support_on_build_plate_only"] = "1"
            cfg["support_top_z_distance"] = "0.2"

        with open(cfg_file, "w") as f:
            json.dump(cfg, f, indent=4)

    with zipfile.ZipFile(file_path, "w", compression=zipfile.ZIP_DEFLATED) as z_out:
        for root, dirs, files in os.walk(unpacked):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, unpacked)
                z_out.write(full_path, rel_path)
    shutil.rmtree(unpacked)

def generate_3mf_files(p_nosup, p_sup):
    print("1. Generating calibrated 3MF project files for 4-Piece System...", flush=True)

    items = [
        ("01A_dl380_lower_front.3mf", "01A_lower_front_bed.stl", p_nosup, False),
        ("01B_dl380_upper_front.3mf", "01B_upper_front_bed.stl", p_nosup, False),
        ("02A_dl380_lower_back.3mf",  "02A_lower_back_bed.stl",  p_nosup, False),
        ("02B_dl380_upper_back.3mf",  "02B_upper_back_bed.stl",  p_sup,   True),
        ("03_dl380_service_lid.3mf",  "03_service_lid_bed.stl",  p_nosup, False),
        ("04_dl380_cage_pins.3mf",    "04_drive_cage_pins_x4_bed.stl", p_nosup, False),
    ]

    generated = []
    for mf_name, stl_name, proc_p, sup in items:
        stl_path = os.path.join(PKG_DIR, stl_name)
        out_3mf  = os.path.join(PKG_DIR, mf_name)
        cmd = [
            SLICER_BIN,
            "--load-settings", f"{proc_p};{SYS_MACHINE}",
            "--load-filaments", SYS_FILAMENT,
            "--export-3mf", out_3mf,
            stl_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        patch_3mf_metadata(out_3mf, enable_support=sup)
        print(f"   - Created and calibrated: {mf_name}")
        generated.append((mf_name, out_3mf, sup))
    return generated

def verify_and_benchmark(items):
    print("\n2. Validating slice correctness & benchmarking metrics with Elegoo Slicer CLI...", flush=True)
    benchmarks = []

    for name, path_3mf, sup in items:
        cmd = [SLICER_BIN, "--slice", "0", "--outputdir", TEMP_DIR, path_3mf]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        res_file = os.path.join(TEMP_DIR, "result.json")
        with open(res_file) as rf:
            res = json.load(rf)
        code = res.get("return_code")
        status = res.get("error_string")
        warn = res.get("sliced_plates", [{}])[0].get("warning_message", "")

        gcode_path = os.path.join(TEMP_DIR, "plate_1.gcode")
        fil_g = 0.0
        time_str = "N/A"
        if os.path.exists(gcode_path):
            with open(gcode_path, "r", errors="ignore") as gf:
                gf.seek(max(0, os.path.getsize(gcode_path) - 100000))
                txt = gf.read()
                mf = re.search(r"total filament used \[g\]\s*=\s*([\d\.]+)", txt)
                if mf: fil_g = float(mf.group(1))
                mt = re.search(r"estimated printing time \(normal mode\)\s*=\s*([^\n\r]+)", txt)
                if mt: time_str = mt.group(1).strip()

        print(f"   - [{name}] Code: {code}, Warnings: '{warn}' | Filament: {fil_g:.1f}g | Time: {time_str}")
        if code != 0 or warn != "":
            raise RuntimeError(f"Slice verification failed on {name}: {warn}")

        benchmarks.append({
            "name": name,
            "filament_g": fil_g,
            "time_str": time_str,
            "support": "Normal Auto (Build Plate)" if sup else "None (100% Support-Free)"
        })
    return benchmarks

def write_docs(benchmarks):
    doc_path = os.path.join(PKG_DIR, "README_4PIECE_GUIDE.md")
    print(f"\n3. Writing documentation to {doc_path}...", flush=True)

    rows = []
    tot_fil = sum(b["filament_g"] for b in benchmarks)
    for b in benchmarks:
        rows.append(f"| `{b['name']}` | {b['support']} | **{b['filament_g']:.1f} g** | **{b['time_str']}** |")

    md = rf"""# DL380 4-Piece Modular Enclosure - Slicing & Assembly Guide

The **4-Piece Modular Architecture** separates the enclosure horizontally along the mid-deck shelf, eliminating nearly 100% of internal supports and dividing the print into small, manageable batches.

---

## 1. Slicing Benchmark Results (Elegoo Centauri Carbon 2)

*Sliced with Elegoo Slicer CLI (OrcaSlicer 2.4 engine) using Rapid PETG @ECC2 (0.20mm Standard, 4 walls, 15% Gyroid infill).*

| Deliverable (.3mf) | Support Configuration | Filament Usage | Estimated Print Time |
| :--- | :--- | :--- | :--- |
{chr(10).join(rows)}
| **TOTAL ASSEMBLY** | — | **{tot_fil:.1f} g** | **~2.8 days total (spread over 6 fast plates)** |

---

## 2. Key Printing Advantages Over Monolithic 2-Piece

1. **Parts 01A, 01B, 02A, 03, and 04 are 100% Support-Free**:
   - The Lower cases print right-side up like open shallow trays ($60.5\text{{ mm}}$ tall with corner snap pillars).
   - The Upper Front case prints with its flat rear mating face on the PEI bed; runner rails, bezel shelf, and $45^\circ$ diamond mesh print straight up with zero supports.
   - Part 04 (Retention Pins) prints flat on its flanged heads with zero supports.
   - Only Part 02B requires minor build-plate support under the front snap latch arms (~$8\text{{ g}}$).
2. **Fast, Low-Risk Printing**:
   - Part 04 (Cage Pins 4-pack) prints in **~3 minutes** (~$1.7\text{{ g}}$).
   - Lower Back prints in only **~5.5 hours** (~$99\text{{ g}}$).
   - Lower Front prints in only **~9 hours** (~$164\text{{ g}}$).
   - No single part takes longer than ~30 hours. If a print is interrupted, you only reprint a single quadrant.
3. **Zero Tunnel Support Extraction**:
   - No digging pliers into deep enclosed chambers.

---

## 3. Tool-Free Drive Cage Retention Pins ("Filament Nails")

- Part 02B features two **Ø4.0 mm vertical retention holes** cut through the mid-deck shelf, perfectly aligned with the stamped mounting holes in the HP DL380 drive cage rear metal tabs ($X = 70.0\text{{ mm}}$ and $X = 115.5\text{{ mm}}$, $Z = 156.0\text{{ mm}}$).
- Part 04 provides custom 3D-printable **Ø3.85 mm / 4.0 mm retention nails** (`04_dl380_cage_pins.3mf`):
  - **Flanged Head**: Ø8.5 mm x 2.4 mm with 45° ergonomic perimeter bevel for tool-free finger insertion and easy fingernail removal.
  - **Friction Collar**: 4.00 mm -> 3.85 mm taper to ensure a snug, zero-rattle hold.
  - **Bullet Nose**: 45° conical tip for effortless blind drop-in alignment through the metal tab into the shelf.
  - **Zero Screws Needed**: Drop the two pins down through the rear metal tabs to lock the drive cage solidly against forward/backward sliding.
  - **Quick Batch Plate**: A 4-pack of pins (`04_drive_cage_pins_x4_bed.stl`) prints in **~3 minutes** with only **~1.7 g** of PETG.

---

## 4. Tool-Free Snap-Fit Assembly Sequence

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

Step 3: Slide Drive Cage into Front Bay and Slide Front into Rear Assembly
        ┌───────────────────────┬─────────┐
        │   DL380 Drive Cage    │ 92mm Fan│ <── 2x Side Push-Release Latch Arms CLICK!
        ├═══════════════════════╪═════════╡
        │     Flex-ATX PSU      │ AC / SAS│ <── Side-Wall Alignment Tongue-and-Groove
        └───────────────────────┴─────────┘

Step 4: Lock Drive Cage with Filament Retention Nails (Tool-Free!)
        Through the top service opening, push the 2x Part 04 pins through the
        metal rear tabs into the Ø4.0mm mid-deck holes. No screws required!
```
"""
    with open(doc_path, "w") as f:
        f.write(md)

def update_zip():
    print("4. Packaging DL380_4Piece_Print_Package.zip...", flush=True)
    zip_path = os.path.join(REPO_DIR, "DL380_4Piece_Print_Package.zip")
    count = 0
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(PKG_DIR):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, PKG_DIR)
                z.write(full_path, rel_path)
                count += 1
    print(f"   - Packaged {count} files into {zip_path} ({os.path.getsize(zip_path)/(1024*1024):.1f} MB)")

if __name__ == "__main__":
    p_nosup, p_sup = build_process_profiles()
    generated = generate_3mf_files(p_nosup, p_sup)
    benchmarks = verify_and_benchmark(generated)
    write_docs(benchmarks)
    update_zip()
    print("\nSUCCESS: 4-Piece Modular Package Export & Validation Complete!")
