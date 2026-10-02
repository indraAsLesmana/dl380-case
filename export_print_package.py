#!/usr/bin/env python3
"""
export_print_package.py
Automated export pipeline for DL380 Modular 2-Piece Flex-ATX Enclosure:
1. Generates bed-oriented STLs from production STEP models.
2. Generates calibrated ready-to-slice .3mf project files for Elegoo Centauri Carbon 2 (ECC2).
3. Applies full PETG print quality profile:
   - 4 wall loops (1.6 mm perimeter)
   - 15% Gyroid infill
   - 70°C Textured PEI Bed (default_bed_type=4)
   - filament_type = PETG (250-255°C nozzle)
   - xy_hole_compensation = +0.10 mm
   - elefant_foot_compensation = 0.15 mm
   - fan_min_speed = 20%, fan_max_speed = 40%, overhang = 80%
   - Back Case: Normal Support auto on build plate only (0.20 mm top-Z gap)
   - Front Case & Lid: 100% Support-free
4. Verifies slicing of all deliverables via Elegoo Slicer CLI.
5. Updates print package zip archive.
"""

import os, sys, json, subprocess, zipfile, shutil

# Setup FreeCAD path
sys.path.append("/usr/lib/freecad/lib")
import FreeCAD, Part, Mesh, MeshPart
from FreeCAD import Vector, Rotation, Placement

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR  = os.path.join(REPO_DIR, "out")
PKG_DIR  = os.path.join(REPO_DIR, "print_service_package")
TEMP_DIR = os.path.join(REPO_DIR, "scratch", "slicer_temp")
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(PKG_DIR, exist_ok=True)

SLICER_BIN = "/opt/elegoo-slicer/AppRun"
SYS_MACHINE = os.path.expanduser("~/.config/ElegooSlicer/system/Elegoo/machine/ECC2/Elegoo Centauri Carbon 2 0.4 nozzle.json")
SYS_FILAMENT = os.path.expanduser("~/.config/ElegooSlicer/system/Elegoo/filament/ECC2/Elegoo Rapid PETG @ECC2.json")
SYS_PROCESS = os.path.expanduser("~/.config/ElegooSlicer/system/Elegoo/process/ECC2/0.20mm Standard @Elegoo CC2 0.4 nozzle.json")

def generate_bed_stls():
    print("1. Generating bed-oriented STLs from production STEP models...", flush=True)
    step_f = os.path.join(OUT_DIR, "dl380_front_case.step")
    step_b = os.path.join(OUT_DIR, "dl380_back_case.step")
    step_l = os.path.join(OUT_DIR, "dl380_service_lid.step")

    for p in [step_f, step_b, step_l]:
        if not os.path.exists(p):
            raise FileNotFoundError(f"Missing required STEP model: {p}. Run dl380_flex_case.py first.")

    front = Part.read(step_f)
    back  = Part.read(step_b)
    lid   = Part.read(step_l)

    rot_body = Rotation(Vector(1, 0, 0), 90.0)
    rot_lid  = Rotation(Vector(1, 0, 0), -90.0)

    f_p = front.copy()
    f_p.Placement = Placement(Vector(0, 0, 0), rot_body)
    f_p.translate(Vector(-f_p.BoundBox.XMin, -f_p.BoundBox.YMin, -f_p.BoundBox.ZMin))

    b_p = back.copy()
    b_p.Placement = Placement(Vector(0, 0, 0), rot_body)
    b_p.translate(Vector(-b_p.BoundBox.XMin, -b_p.BoundBox.YMin, -b_p.BoundBox.ZMin))

    l_p = lid.copy()
    l_p.Placement = Placement(Vector(0, 0, 0), rot_lid)
    l_p.translate(Vector(-l_p.BoundBox.XMin, -l_p.BoundBox.YMin, -l_p.BoundBox.ZMin))

    m_f = MeshPart.meshFromShape(f_p, LinearDeflection=0.08, AngularDeflection=0.35)
    m_b = MeshPart.meshFromShape(b_p, LinearDeflection=0.08, AngularDeflection=0.35)
    m_l = MeshPart.meshFromShape(l_p, LinearDeflection=0.08, AngularDeflection=0.35)

    stl_f = os.path.join(PKG_DIR, "01_front_case_bed.stl")
    stl_b = os.path.join(PKG_DIR, "02_back_case_bed.stl")
    stl_l = os.path.join(PKG_DIR, "03_service_lid_bed.stl")

    m_f.write(stl_f)
    m_b.write(stl_b)
    m_l.write(stl_l)

    print(f"   - Front Case bed STL: {stl_f} ({m_f.CountFacets} facets)")
    print(f"   - Back Case bed STL:  {stl_b} ({m_b.CountFacets} facets)")
    print(f"   - Service Lid bed STL: {stl_l} ({m_l.CountFacets} facets)")
    return stl_f, stl_b, stl_l

def build_process_profiles():
    with open(SYS_PROCESS) as f:
        base = json.load(f)

    # Base functional PETG profile
    petg_base = dict(base)
    petg_base["wall_loops"] = "4"
    petg_base["sparse_infill_density"] = "15%"
    petg_base["sparse_infill_pattern"] = "gyroid"
    petg_base["top_solid_layers"] = "4"
    petg_base["bottom_solid_layers"] = "4"
    petg_base["xy_hole_compensation"] = "0.1"
    petg_base["elefant_foot_compensation"] = "0.15"

    # Profile 1: Support OFF (Front Case & Lid)
    proc_nosup = dict(petg_base)
    proc_nosup["enable_support"] = "0"
    path_nosup = os.path.join(TEMP_DIR, "proc_nosup.json")
    with open(path_nosup, "w") as f:
        json.dump(proc_nosup, f, indent=2)

    # Profile 2: Normal Support ON (Back Case Snap Arms)
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

        # 1. Force Textured PEI Bed and 70°C PETG temperatures (Fixes Issue #1)
        cfg["curr_bed_type"] = "Textured PEI Plate"
        cfg["default_bed_type"] = "4"
        cfg["filament_type"] = ["PETG"]
        cfg["textured_plate_temp"] = ["70"]
        cfg["textured_plate_temp_initial_layer"] = ["70"]
        cfg["hot_plate_temp"] = ["70"]
        cfg["hot_plate_temp_initial_layer"] = ["70"]
        cfg["eng_plate_temp"] = ["70"]
        cfg["eng_plate_temp_initial_layer"] = ["70"]

        # 2. Part cooling fan tuning for PETG layer adhesion (Fixes Issue #4)
        cfg["fan_min_speed"] = ["20"]
        cfg["fan_max_speed"] = ["40"]
        cfg["overhang_fan_speed"] = ["80"]

        # 3. Process settings (Fixes Issues #2, #3, #5)
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

    # Repack cleanly
    with zipfile.ZipFile(file_path, "w", compression=zipfile.ZIP_DEFLATED) as z_out:
        for root, dirs, files in os.walk(unpacked):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, unpacked)
                z_out.write(full_path, rel_path)
    shutil.rmtree(unpacked)

def generate_3mf_files(stl_f, stl_b, stl_l, proc_nosup, proc_sup):
    print("2. Generating ready-to-slice 3MF project files...", flush=True)

    items = [
        ("01_dl380_front_case.3mf", stl_f, proc_nosup, False),
        ("02_dl380_back_case.3mf",  stl_b, proc_sup,   True),
        ("03_dl380_service_lid.3mf", stl_l, proc_nosup, False),
    ]

    for filename, stl_path, proc_path, sup in items:
        out_3mf = os.path.join(PKG_DIR, filename)
        cmd = [
            SLICER_BIN,
            "--load-settings", f"{proc_path};{SYS_MACHINE}",
            "--load-filaments", SYS_FILAMENT,
            "--export-3mf", out_3mf,
            stl_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        patch_3mf_metadata(out_3mf, enable_support=sup)
        print(f"   - Created and patched: {filename}")

def verify_all_slices():
    print("3. Validating slice correctness with Elegoo Slicer CLI...", flush=True)
    for name in ["01_dl380_front_case.3mf", "02_dl380_back_case.3mf", "03_dl380_service_lid.3mf"]:
        p = os.path.join(PKG_DIR, name)
        cmd = [SLICER_BIN, "--slice", "0", "--outputdir", TEMP_DIR, p]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        res_file = os.path.join(TEMP_DIR, "result.json")
        with open(res_file) as f:
            res = json.load(f)
        status = res.get("error_string")
        code = res.get("return_code")
        warn = res.get("sliced_plates", [{}])[0].get("warning_message", "")
        print(f"   - [{name}] Return Code: {code}, Status: {status}, Warnings: '{warn}'")
        if code != 0 or warn != "":
            raise RuntimeError(f"Slice verification failed on {name}: {warn}")

def update_zip_package():
    print("4. Updating DL380_Flex_Case_Print_Package.zip...", flush=True)
    zip_path = os.path.join(REPO_DIR, "DL380_Flex_Case_Print_Package.zip")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for file in os.listdir(PKG_DIR):
            full_path = os.path.join(PKG_DIR, file)
            if os.path.isfile(full_path):
                z.write(full_path, file)
    print(f"   - Packaged {len(os.listdir(PKG_DIR))} files into {zip_path} ({os.path.getsize(zip_path)/(1024*1024):.1f} MB)")

if __name__ == "__main__":
    stl_f, stl_b, stl_l = generate_bed_stls()
    p_nosup, p_sup = build_process_profiles()
    generate_3mf_files(stl_f, stl_b, stl_l, p_nosup, p_sup)
    verify_all_slices()
    update_zip_package()
    print("SUCCESS: Production print package export & validation completed!")
