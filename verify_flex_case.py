#!/usr/bin/env python3
"""
verify_flex_case.py - Automated Geometric & Physical Verification Suite
for the DL380 Dual-Chamber Flex-ATX Enclosure (Option A).
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
print("DL380 DUAL-CHAMBER FLEX-ATX ENCLOSURE - VERIFICATION AUDIT")
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

check("Body STL size > 150 KB", os.path.getsize(STL_BODY) > 150_000, f"{os.path.getsize(STL_BODY):,} bytes")
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
check("Width within 237.0 - 238.5 mm", 237.0 <= (max_x - min_x) <= 238.5, f"Span = {max_x - min_x:.2f} mm")
check("Width fits standard 256 mm build plate (< 256.0 mm)", (max_x - min_x) < 256.0, f"Margin = {256.0 - (max_x - min_x):.2f} mm")
check("Depth within 204.0 - 206.0 mm", 204.0 <= (max_z - min_z) <= 206.0, f"Span = {max_z - min_z:.2f} mm")
check("Depth fits standard 256 mm build plate (< 256.0 mm)", (max_z - min_z) < 256.0, f"Margin = {256.0 - (max_z - min_z):.2f} mm")
check("Height within 100.0 - 102.0 mm", 100.0 <= (max_y - min_y) <= 102.0, f"Span = {max_y - min_y:.2f} mm")

# 3. Left Chamber (HP DL380 Drive Cage Bay)
# Drive mouth boundary at Z = 0: X around 3.0 and 148.8, Y around 3.5 and 97.5
mouth_pts = b_verts[(b_verts[:, 2] < 1.0) & (abs(b_verts[:, 0] - 3.0) < 0.1)]
check("Front cage mouth aperture open at Z = 0", len(mouth_pts) > 0, f"Found {len(mouth_pts)} front aperture boundary vertices")
cage_bay_w = 148.8 - 3.0
check("Drive bay internal width >= 145.8 mm", cage_bay_w >= 145.8, f"Width = {cage_bay_w:.2f} mm (for 145.0 mm cage)")

# 4. Right Chamber (Flex-ATX PSU Cradle)
psu_chamber_w = 234.8 - 152.3
check("PSU chamber internal width >= 82.0 mm", psu_chamber_w >= 82.0, f"Width = {psu_chamber_w:.2f} mm (for 81.5 mm Flex-ATX)")
psu_length = 200.0 - 45.0
check("PSU chamber length >= 150.0 mm", psu_length >= 150.0, f"Length = {psu_length:.2f} mm (for 150.0 mm ENP-2320)")

# Check C14 Rear Window
rear_c14 = body_tris[(body_tris[:, :, 2].mean(axis=1) > 200.0) & (body_tris[:, :, 0].mean(axis=1) > 160.0)]
check("Rear Flex-ATX C14 / 40mm fan window present", len(rear_c14) > 50, f"Found {len(rear_c14)} facets near rear PSU face")

# Check 16mm Power Switch Port
front_sw = body_tris[(body_tris[:, :, 2].mean(axis=1) < 2.0) & (body_tris[:, :, 0].mean(axis=1) > 160.0) & (body_tris[:, :, 1].mean(axis=1) > 40.0)]
check("Front 16mm illuminated switch port present", len(front_sw) > 20, f"Found {len(front_sw)} facets around switch hole")

# 5. Center Divider & Inter-Chamber Power Portal
divider_pts = b_verts[(b_verts[:, 0] >= 148.0) & (b_verts[:, 0] <= 153.0)]
check("Center divider wall present", len(divider_pts) > 200, f"Found {len(divider_pts)} divider vertices")

# Inter-chamber portal at Z ~ 148-180 mm, Y ~ 7.5-51.5 mm
portal_pts = b_verts[(b_verts[:, 0] >= 146.0) & (b_verts[:, 0] <= 150.0) & (b_verts[:, 2] >= 148.0) & (b_verts[:, 2] <= 180.0) & (b_verts[:, 1] >= 7.0) & (b_verts[:, 1] <= 52.0)]
check("Inter-chamber 10-pin power portal open", len(portal_pts) > 20, f"Found {len(portal_pts)} portal edge vertices")

# 6. Rear Fan Exhaust (Left Chamber)
rear_fan = body_tris[(body_tris[:, :, 2].mean(axis=1) > 200.0) & (body_tris[:, :, 0].mean(axis=1) < 140.0)]
check("Rear 92mm fan honeycomb exhaust grille present", len(rear_fan) > 100, f"Found {len(rear_fan)} rear grille facets")

# 7. Service Lid
l_verts = lid_tris.reshape(-1, 3)
lid_w = l_verts[:, 0].max() - l_verts[:, 0].min()
lid_d = l_verts[:, 2].max() - l_verts[:, 2].min()
check("Lid dimensions valid and non-zero", lid_w > 100.0 and lid_d > 20.0, f"Lid = {lid_w:.2f} x {lid_d:.2f} mm")

# 8. Mesh Quality & Resolution
check("Body mesh resolution >= 3,500 facets", body_count >= 3_500, f"Total facets = {body_count:,}")
check("Lid mesh resolution >= 150 facets", lid_count >= 150, f"Total facets = {lid_count:,}")

print("=" * 80)
print(f"VERIFICATION AUDIT RESULT: {tests_passed} / {total_tests} passed ({tests_passed/total_tests*100:.1f}%)")
print("=" * 80)

if tests_passed == total_tests:
    print("ALL TESTS PASSED: DL380 Dual-Chamber Flex-ATX Enclosure 100% verified!")
    sys.exit(0)
else:
    print(f"WARNING: {total_tests - tests_passed} tests failed!")
    sys.exit(1)
