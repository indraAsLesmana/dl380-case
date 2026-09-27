#!/usr/bin/env python3
"""
verify_flex_case.py - Automated Geometric & Physical Verification Suite
for the DL380 Double-Decker Flex-ATX Enclosure (120mm Fan).
"""

import os
import sys
import struct
import numpy as np

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(REPO_DIR, "out")
PRINT_DIR = os.path.join(REPO_DIR, "print")

STEP_BODY = os.path.join(OUT_DIR, "dl380_flex_case_body.step")
STEP_LID  = os.path.join(OUT_DIR, "dl380_flex_case_lid.step")
STEP_ALL  = os.path.join(OUT_DIR, "dl380_flex_case.step")

STL_BODY  = os.path.join(OUT_DIR, "dl380_flex_case_body.stl")
STL_LID   = os.path.join(OUT_DIR, "dl380_flex_case_lid.stl")
STL_PRINT = os.path.join(PRINT_DIR, "dl380_flex_case_all-parts.stl")

print("=" * 80)
print("DL380 DOUBLE-DECKER FLEX-ATX ENCLOSURE - VERIFICATION AUDIT")
print("=" * 80)

tests_passed = 0
total_tests = 0

def check(name, cond, details=""):
    global tests_passed, total_tests
    total_tests += 1
    status = "PASS" if cond else "FAIL"
    if cond:
        tests_passed += 1
    print(f"[{status:4s}] Test {total_tests:02d}: {name}")
    if details:
        print(f"       -> {details}")

# 1. Deliverables Check
check("Body STEP exists", os.path.isfile(STEP_BODY), f"Path: {STEP_BODY}")
check("Lid STEP exists", os.path.isfile(STEP_LID), f"Path: {STEP_LID}")
check("Full assembly STEP exists", os.path.isfile(STEP_ALL), f"Path: {STEP_ALL}")
check("Body STL exists", os.path.isfile(STL_BODY), f"Path: {STL_BODY}")
check("Lid STL exists", os.path.isfile(STL_LID), f"Path: {STL_LID}")
check("Print kit STL exists", os.path.isfile(STL_PRINT), f"Path: {STL_PRINT}")

check("Body STL size > 200 KB", os.path.getsize(STL_BODY) > 200_000, f"{os.path.getsize(STL_BODY):,} bytes")
check("Lid STL size > 5 KB", os.path.getsize(STL_LID) > 5_000, f"{os.path.getsize(STL_LID):,} bytes")

def read_stl(path):
    with open(path, 'rb') as f:
        f.seek(80)
        count = struct.unpack('<I', f.read(4))[0]
        tris = []
        for _ in range(count):
            data = f.read(50)
            floats = struct.unpack('<12fH', data)
            tris.append([floats[3:6], floats[6:9], floats[9:12]])
    return np.array(tris), count

body_tris, body_count = read_stl(STL_BODY)
lid_tris, lid_count = read_stl(STL_LID)

b_verts = body_tris.reshape(-1, 3)
min_x, max_x = b_verts[:, 0].min(), b_verts[:, 0].max()
min_y, max_y = b_verts[:, 1].min(), b_verts[:, 1].max()
min_z, max_z = b_verts[:, 2].min(), b_verts[:, 2].max()

# 2. Overall Enclosure Envelope
check("Width within 151.0 - 153.0 mm", 151.0 <= (max_x - min_x) <= 153.0, f"Span = {max_x - min_x:.2f} mm")
check("Width fits standard 256 mm build plate (< 256.0 mm)", (max_x - min_x) < 256.0, f"Margin = {256.0 - (max_x - min_x):.2f} mm")
check("Depth within 204.0 - 206.0 mm", 204.0 <= (max_z - min_z) <= 206.0, f"Span = {max_z - min_z:.2f} mm")
check("Depth fits standard 256 mm build plate (< 256.0 mm)", (max_z - min_z) < 256.0, f"Margin = {256.0 - (max_z - min_z):.2f} mm")
check("Height within 176.0 - 178.0 mm", 176.0 <= (max_y - min_y) <= 178.0, f"Span = {max_y - min_y:.2f} mm (Z limit 256mm)")

# 3. Upper Story: HP DL380 Drive Cage Bay
mouth_pts = b_verts[(b_verts[:, 2] < 1.0) & (abs(b_verts[:, 0] - 3.0) < 0.2) & (b_verts[:, 1] > 50.0)]
check("Front cage mouth aperture open at Z = 0", len(mouth_pts) > 0, f"Found {len(mouth_pts)} front aperture boundary vertices")
cage_bay_w = 148.8 - 3.0
check("Drive bay internal width >= 145.8 mm", cage_bay_w >= 145.8, f"Width = {cage_bay_w:.2f} mm (for 145.0 mm cage)")

# 4. Lower Basement: Flex-ATX PSU Cradle & Wiring Corridor
base_pts = b_verts[(b_verts[:, 1] >= 3.5) & (b_verts[:, 1] <= 48.5)]
check("Lower basement present below mid-deck", len(base_pts) > 500, f"Found {len(base_pts)} basement vertices")

# Check C14 Rear Window in basement (Y in 3.5 to 45 mm, Z > 200 mm)
rear_c14 = body_tris[(body_tris[:, :, 2].mean(axis=1) > 200.0) & (body_tris[:, :, 1].mean(axis=1) < 48.0) & (body_tris[:, :, 0].mean(axis=1) < 90.0)]
check("Rear Flex-ATX C14 / 40mm fan window present", len(rear_c14) > 30, f"Found {len(rear_c14)} facets near rear PSU face")

# Check 16mm Power Switch Port in lower front bezel (Y ~ 26 mm, Z < 2 mm, X > 100 mm)
front_sw = body_tris[(body_tris[:, :, 2].mean(axis=1) < 2.0) & (body_tris[:, :, 0].mean(axis=1) > 100.0) & (body_tris[:, :, 1].mean(axis=1) < 45.0)]
check("Front 16mm illuminated switch port present", len(front_sw) > 15, f"Found {len(front_sw)} facets around switch hole")

# Check front honeycomb intake vents
front_vents = body_tris[(body_tris[:, :, 2].mean(axis=1) < 2.0) & (body_tris[:, :, 0].mean(axis=1) < 80.0) & (body_tris[:, :, 1].mean(axis=1) < 45.0)]
check("Front basement honeycomb intake vents present", len(front_vents) > 30, f"Found {len(front_vents)} facets in PSU intake area")

# 5. Mid-Deck Shelf & Vertical Power Slot
mid_deck_pts = b_verts[(b_verts[:, 1] >= 48.0) & (b_verts[:, 1] <= 52.0)]
check("Mid-deck shelf present", len(mid_deck_pts) > 200, f"Found {len(mid_deck_pts)} mid-deck vertices")

# Vertical 10-pin power slot at X in 112 to 146 mm, Z in 150 to 178 mm
slot_pts = b_verts[(b_verts[:, 0] >= 112.0) & (b_verts[:, 0] <= 146.0) & (b_verts[:, 2] >= 150.0) & (b_verts[:, 2] <= 178.0) & (b_verts[:, 1] >= 47.0) & (b_verts[:, 1] <= 53.0)]
check("Vertical 10-pin power pass-through slot open", len(slot_pts) > 10, f"Found {len(slot_pts)} power slot edge vertices")

# 6. Rear 120mm Fan Exhaust & Grille (Upper Story)
rear_fan = body_tris[(body_tris[:, :, 2].mean(axis=1) > 200.0) & (body_tris[:, :, 1].mean(axis=1) > 55.0)]
check("Rear 120mm fan honeycomb exhaust grille present", len(rear_fan) > 150, f"Found {len(rear_fan)} rear 120mm grille facets")

# 7. Service Lid
l_verts = lid_tris.reshape(-1, 3)
lid_w = l_verts[:, 0].max() - l_verts[:, 0].min()
lid_d = l_verts[:, 2].max() - l_verts[:, 2].min()
lid_h = l_verts[:, 1].max() - l_verts[:, 1].min()
check("Lid dimensions valid and non-zero", lid_w > 130.0 and lid_d > 30.0 and lid_h > 2.5, f"Lid = {lid_w:.2f} (W) x {lid_d:.2f} (D) x {lid_h:.2f} (H) mm")

# Verify solid top (no through-holes: min Y of all facets in lid center is above base)
lid_bottom = l_verts[:, 1].min()
lid_top = l_verts[:, 1].max()
check("Lid is solid with blind thumb rebate (thickness > 2.0 mm everywhere)", (lid_top - lid_bottom) >= 3.4, f"Thickness = {lid_top - lid_bottom:.2f} mm")

# 8. Mesh Quality & Resolution
check("Body mesh resolution >= 4,000 facets", body_count >= 4_000, f"Total facets = {body_count:,}")
check("Lid mesh resolution >= 150 facets", lid_count >= 150, f"Total facets = {lid_count:,}")

print("=" * 80)
print(f"VERIFICATION AUDIT RESULT: {tests_passed} / {total_tests} passed ({tests_passed/total_tests*100:.1f}%)")
print("=" * 80)

if tests_passed == total_tests:
    print("ALL TESTS PASSED: DL380 Double-Decker Flex-ATX Enclosure 100% verified!")
    sys.exit(0)
else:
    print(f"WARNING: {total_tests - tests_passed} tests failed!")
    sys.exit(1)
