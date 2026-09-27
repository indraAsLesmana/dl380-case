#!/usr/bin/env python3
"""
dl380_flex_case.py - Parametric FreeCAD Model of a Double-Decker Desktop Enclosure
for an HP ProLiant DL380 G6/G7 8-bay 2.5" SFF Drive Cage, Enhance ENP-2320 Flex-ATX
Power Supply, and a High-Flow 120mm Rear Exhaust Fan.

Double-Decker Architecture:
  - Lower Basement (Y = 0.0 to 51.5 mm):
      * Enhance ENP-2320 Flex-ATX PSU (150.0 x 81.5 x 40.5 mm) seated on the left
        with 2.0 mm anti-vibration / airflow plinths.
      * Dedicated 62.3 mm wide lateral wiring corridor on the right side for cable
        slack, harnesses, and switch leads.
      * Front Panel:
          - Standard 16.2 mm illuminated latching metal power switch port.
          - Architectural hexagonal honeycomb intake vents directly aligned with the
            PSU intake path.
      * Rear Panel:
          - Standard Flex-ATX 3-hole flange mount (#6-32 / 3.5 mm).
          - C14 AC power inlet and 40 mm PSU exhaust cutout (72.0 x 32.0 mm).
  - Mid-Deck Shelf (Y = 48.5 to 51.5 mm):
      * 3.0 mm structural floor separating basement from upper chamber.
      * Direct vertical 10-pin power pass-through slot (32.0 x 24.0 mm) positioned
        directly below the DL380 backplane's lower-right power socket.
  - Upper Story (Y = 51.5 to 173.5 mm):
      * HP DL380 8-bay 2.5" SFF Drive Cage chamber (145.0 x 87.0 x 165.0 mm).
      * Internal bottom slider rails (14.0 x 3.5 mm) & ceiling guide ribs (5.0 x 3.5 mm).
      * Rear stop frame at Z = 162.0 to 165.0 mm to lock cage depth.
      * Forward upper aerodynamic transition shroud (34.2 mm tall, 12.0 mm deep)
        above the cage mouth to prevent front air short-circuiting.
      * Rear 120mm Fan Plenum (Z = 165.0 to 200.0 mm, 35.0 mm deep):
          - Accommodates standard 120 x 120 x 25 mm fans (e.g. Arctic P12, Noctua NF-A12x25).
          - Side guide rails for smooth drop-in fan alignment.
          - Large 115.0 mm diameter hexagonal honeycomb exhaust grille.
          - Standard 105.0 x 105.0 mm M4 fan screw mounting pattern.
          - Dual rear SAS cable pass-through ports (18.0 x 14.0 mm) for external HBA runs.
  - Service Lid & Roof (Y = 173.5 to 177.0 mm):
      * Recessed stepped perimeter ledge over the fan plenum (Z = 162.0 to 199.5 mm).
      * Matching drop-in service lid with 0.4 mm clearance.
      * Solid top surface with zero through-holes.
      * Ergonomic shallow blind thumb grip rebate on top (1.0 mm deep) for easy removal.

Enclosure Dimensions:
  - Width:  151.80 mm (fits standard 256 x 256 mm build plates)
  - Height: 177.00 mm (well within 256 mm Z build volume)
  - Depth:  205.00 mm
"""

import os
import sys
import math
import time
import FreeCAD as App
import Part
import Mesh
import MeshPart
from FreeCAD import Vector

# ==============================================================================
# 1. PARAMETERS & CONFIGURATION
# ==============================================================================

WALL            =   3.0    # mm  outer wall thickness
FLOOR_T         =   3.5    # mm  bottom floor thickness
MID_DECK_T      =   3.0    # mm  shelf between basement and upper chamber
ROOF_T          =   3.5    # mm  top roof thickness
REAR_WALL_T     =   5.0    # mm  rear wall thickness

# ---- Drive Cage Chamber (Upper Story) ----------------------------------------
CAGE_W          = 145.0    # mm  HP DL380 cage width
CAGE_H          =  87.0    # mm  HP DL380 cage height
CAGE_D          = 165.0    # mm  HP DL380 cage depth
FIT_CLEAR       =   0.4    # mm  clearance per side
INT_W           = CAGE_W + 2 * FIT_CLEAR   # 145.8 mm

CAGE_RAIL_H     =  14.0    # mm  bottom guide rail height
CAGE_RAIL_W     =   3.5    # mm  bottom guide rail thickness
CAGE_TOP_RIB_H  =   5.0    # mm  ceiling guide rib height
CAGE_TOP_RIB_W  =   3.5    # mm  ceiling guide rib thickness

# ---- Flex-ATX PSU Basement (Lower Story) -------------------------------------
PSU_W           =  81.5    # mm  Enhance ENP-2320 width
PSU_H           =  40.5    # mm  Enhance ENP-2320 height
PSU_L           = 150.0    # mm  Enhance ENP-2320 length
BASEMENT_H      =  45.0    # mm  clear internal height of basement

SWITCH_DIA      =  16.2    # mm  standard 16 mm metal push-button switch

# ---- 120mm Cooling Fan & Rear Plenum -----------------------------------------
FAN_SIZE        = 120.0    # mm  nominal 120 mm fan (Arctic P12, Noctua NF-A12)
FAN_D           =  25.0    # mm  fan depth
PLENUM_D        =  35.0    # mm  depth behind cage (Z = 165 to 200 mm)
FAN_APERTURE    = 115.0    # mm  grille bore diameter
FAN_PITCH       = 105.0    # mm  fan screw hole square pitch
UPPER_H         = FAN_SIZE + 2.0  # 122.0 mm clear internal height

# ---- Overall Dimensions ------------------------------------------------------
OUT_W           = WALL + INT_W + WALL                              # 151.80 mm
OUT_D           = CAGE_D + PLENUM_D + REAR_WALL_T                 # 205.00 mm
OUT_H           = FLOOR_T + BASEMENT_H + MID_DECK_T + UPPER_H + ROOF_T # 177.00 mm

# Key Coordinate Planes:
# X: [0, OUT_W] = [0.0, 151.8]
# Y: 0.0 (bottom floor)
#    Y_BASE_FLOOR = FLOOR_T = 3.5
#    Y_MID_DECK   = FLOOR_T + BASEMENT_H = 48.5
#    Y_UPPER_FLOOR= FLOOR_T + BASEMENT_H + MID_DECK_T = 51.5
#    Y_ROOF_LOWER = OUT_H - ROOF_T = 173.5
#    Y_ROOF_TOP   = OUT_H = 177.0
# Z: 0.0 at front mouth
#    Z_CAGE_STOP  = CAGE_D = 165.0
#    Z_PLEN_END   = CAGE_D + PLENUM_D = 200.0
#    Z_REAR_OUT   = OUT_D = 205.0

Y_BASE_FLOOR    = FLOOR_T
Y_MID_DECK      = FLOOR_T + BASEMENT_H
Y_UPPER_FLOOR   = FLOOR_T + BASEMENT_H + MID_DECK_T
Y_ROOF_LOWER    = OUT_H - ROOF_T
Z_CAGE_STOP     = CAGE_D
Z_PLEN_END      = CAGE_D + PLENUM_D

REPO_DIR        = os.path.dirname(os.path.abspath(__file__))
OUT_DIR         = os.path.join(REPO_DIR, "out")
PRINT_DIR       = os.path.join(REPO_DIR, "print")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(PRINT_DIR, exist_ok=True)

print("=" * 80)
print("DL380 DOUBLE-DECKER FLEX-ATX ENCLOSURE GENERATOR (120MM FAN)")
print(f"Chassis Envelope: {OUT_W:.2f} mm (W) x {OUT_H:.2f} mm (H) x {OUT_D:.2f} mm (D)")
print(f"Print Bed Footprint: {OUT_W:.1f} x {OUT_D:.1f} mm (fits 256x256 mm beds easily!)")
print("=" * 80, flush=True)

# ==============================================================================
# 2. HELPER FUNCTIONS
# ==============================================================================

def make_hex_prism(cell_w, depth, center_x, center_y, z_start):
    """Hexagonal prism with flat top/bottom, aligned with Z axis."""
    r = cell_w / math.sqrt(3.0)
    pts = []
    for i in range(6):
        ang = math.radians(30.0 + i * 60.0)
        pts.append(Vector(center_x + r * math.cos(ang), center_y + r * math.sin(ang), z_start))
    pts.append(pts[0])
    edges = [Part.makeLine(pts[i], pts[i+1]) for i in range(6)]
    wire = Part.Wire(edges)
    face = Part.Face(wire)
    return face.extrude(Vector(0, 0, depth))

# ==============================================================================
# 3. BUILD MAIN SOLID BODY
# ==============================================================================

print("1. Creating outer monolithic shell...", flush=True)
shell = Part.makeBox(OUT_W, OUT_H, OUT_D, Vector(0, 0, 0))

print("2. Hollowing lower basement void (PSU & wiring corridor)...", flush=True)
# Front wall of basement is 3.5 mm thick for switch & vents
base_void = Part.makeBox(INT_W, BASEMENT_H, Z_PLEN_END - 3.5 + 0.1,
                         Vector(WALL, Y_BASE_FLOOR, 3.5))

print("3. Hollowing upper chamber void (drive cage bay & 120mm plenum)...", flush=True)
upper_void = Part.makeBox(INT_W, UPPER_H, Z_PLEN_END + 2.0,
                          Vector(WALL, Y_UPPER_FLOOR, -2.0))

body = shell.cut(base_void).cut(upper_void)

# ------------------------------------------------------------------------------
# 4. Drive Cage Guide Rails & Stop Frame (Upper Story)
# ------------------------------------------------------------------------------
print("4. Modeling internal bottom slider rails, ceiling guide ribs, and stop frame...", flush=True)

# Bottom slider rails (elevates cage 14 mm off mid-deck, supporting side flanges)
rail_l = Part.makeBox(CAGE_RAIL_W, CAGE_RAIL_H, CAGE_D - 4.0, Vector(WALL, Y_UPPER_FLOOR, 4.0))
rail_r = Part.makeBox(CAGE_RAIL_W, CAGE_RAIL_H, CAGE_D - 4.0, Vector(WALL + INT_W - CAGE_RAIL_W, Y_UPPER_FLOOR, 4.0))

# Ceiling guide ribs (prevents upward tilting during drive insertion)
rib_l  = Part.makeBox(CAGE_TOP_RIB_W, CAGE_TOP_RIB_H, CAGE_D - 4.0,
                      Vector(WALL, Y_UPPER_FLOOR + CAGE_H + 2 * FIT_CLEAR - CAGE_TOP_RIB_H, 4.0))
rib_r  = Part.makeBox(CAGE_TOP_RIB_W, CAGE_TOP_RIB_H, CAGE_D - 4.0,
                      Vector(WALL + INT_W - CAGE_TOP_RIB_W, Y_UPPER_FLOOR + CAGE_H + 2 * FIT_CLEAR - CAGE_TOP_RIB_H, 4.0))

body = body.fuse(rail_l).fuse(rail_r).fuse(rib_l).fuse(rib_r)

# Rear stop frame at Z = 162.0 to 165.0 mm
stop_w = 12.0
stop_box = Part.makeBox(INT_W, UPPER_H, 3.0, Vector(WALL, Y_UPPER_FLOOR, CAGE_D - 3.0))
stop_hole = Part.makeBox(INT_W - 2 * stop_w, UPPER_H - 2 * stop_w, 5.0,
                         Vector(WALL + stop_w, Y_UPPER_FLOOR + stop_w, CAGE_D - 4.0))
stop_frame = stop_box.cut(stop_hole)
body = body.fuse(stop_frame)

# ------------------------------------------------------------------------------
# 5. Direct Vertical 10-Pin Power Pass-Through Slot
# ------------------------------------------------------------------------------
print("5. Cutting vertical 10-pin power pass-through slot in mid-deck shelf...", flush=True)
# Positioned at lower-right of cage: X = 112.8 to 144.8 mm, Z = 152.0 to 176.0 mm
power_slot = Part.makeBox(32.0, MID_DECK_T + 4.0, 24.0,
                          Vector(WALL + INT_W - 36.0, Y_UPPER_FLOOR - MID_DECK_T - 2.0, 152.0))
body = body.cut(power_slot)

# ------------------------------------------------------------------------------
# 6. Upper Aerodynamic Transition Shroud
# ------------------------------------------------------------------------------
print("6. Adding forward upper aerodynamic shroud above cage mouth...", flush=True)
shroud_lip = Part.makeBox(INT_W, UPPER_H - (CAGE_H + 2 * FIT_CLEAR), 12.0,
                          Vector(WALL, Y_UPPER_FLOOR + CAGE_H + 2 * FIT_CLEAR, 0.0))
body = body.fuse(shroud_lip)

# ------------------------------------------------------------------------------
# 7. 120mm Cooling Fan Mount & Honeycomb Exhaust Grille
# ------------------------------------------------------------------------------
print("7. Modeling 120mm rear fan mounting, side rails, and honeycomb exhaust grille...", flush=True)

fan_cx = WALL + INT_W / 2.0                    # 75.90 mm (centered)
fan_cy = Y_UPPER_FLOOR + FAN_SIZE / 2.0 + 1.0  # 112.50 mm (centered in 122mm clear height)
fan_cz = Z_PLEN_END - FAN_D                    # 175.00 mm

# 120mm Side Guide Rails (width = 120.0 mm centered)
fan_rail_l = Part.makeBox(3.0, FAN_SIZE, FAN_D, Vector(fan_cx - FAN_SIZE/2.0 - 3.0, Y_UPPER_FLOOR, fan_cz))
fan_rail_r = Part.makeBox(3.0, FAN_SIZE, FAN_D, Vector(fan_cx + FAN_SIZE/2.0, Y_UPPER_FLOOR, fan_cz))
body = body.fuse(fan_rail_l).fuse(fan_rail_r)

# Rear Honeycomb Exhaust Grille (115 mm diameter)
grille_cell = 9.5
grille_web  = 1.5
step_x = (grille_cell + grille_web) * math.sqrt(3.0) / 2.0
step_y = (grille_cell + grille_web) * 1.5
r_max  = (FAN_APERTURE / 2.0) - 2.0

hex_cuts = []
for row in range(-8, 9):
    cy = fan_cy + row * step_y * 0.5
    row_offset = (step_x * 0.5) if (row % 2 != 0) else 0.0
    for col in range(-8, 9):
        cx = fan_cx + col * step_x + row_offset
        dist = math.hypot(cx - fan_cx, cy - fan_cy)
        if dist + grille_cell / 2.0 < r_max:
            hex_cuts.append(make_hex_prism(grille_cell, REAR_WALL_T + 4.0, cx, cy, Z_PLEN_END - 2.0))

if hex_cuts:
    all_hex = hex_cuts[0]
    for h in hex_cuts[1:]:
        all_hex = all_hex.fuse(h)
    body = body.cut(all_hex)

# 4x 120mm Fan Mounting Screw Holes (105.0 mm square pattern, M4 / 4.2 mm)
for dx in (-FAN_PITCH / 2.0, FAN_PITCH / 2.0):
    for dy in (-FAN_PITCH / 2.0, FAN_PITCH / 2.0):
        hole = Part.makeCylinder(2.1, REAR_WALL_T + 4.0,
                                 Vector(fan_cx + dx, fan_cy + dy, Z_PLEN_END - 2.0), Vector(0, 0, 1))
        body = body.cut(hole)

# ------------------------------------------------------------------------------
# 8. Lower Basement: Flex-ATX PSU Cradle & Rear C14 Cutout
# ------------------------------------------------------------------------------
print("8. Modeling basement Flex-ATX PSU cradle, C14 cutouts, and rear mounting...", flush=True)

psu_x0 = WALL + 2.0                            # 5.0 mm
psu_cx = psu_x0 + PSU_W / 2.0                  # 45.75 mm
psu_z0 = Z_PLEN_END - PSU_L                    # 50.00 mm

# Support plinths under PSU (elevates PSU 2.0 mm for vibration dampening & bottom clearance)
plinth1 = Part.makeBox(PSU_W + 4.0, 2.0, 15.0, Vector(WALL, FLOOR_T, psu_z0 + 10.0))
plinth2 = Part.makeBox(PSU_W + 4.0, 2.0, 15.0, Vector(WALL, FLOOR_T, Z_PLEN_END - 25.0))
body = body.fuse(plinth1).fuse(plinth2)

# Flex-ATX Rear Wall Cutout (C14 AC inlet + 40mm fan exhaust)
c14_cut = Part.makeBox(72.0, 32.0, REAR_WALL_T + 4.0,
                       Vector(psu_cx - 36.0, FLOOR_T + 6.0, Z_PLEN_END - 2.0))
body = body.cut(c14_cut)

# 3x Standard Flex-ATX Rear Mounting Screw Holes (#6-32 / 3.8 mm)
for s_pt in [Vector(psu_cx - 36.0, FLOOR_T + 36.0, Z_PLEN_END - 2.0),
             Vector(psu_cx - 36.0, FLOOR_T + 6.0,  Z_PLEN_END - 2.0),
             Vector(psu_cx + 36.0, FLOOR_T + 6.0,  Z_PLEN_END - 2.0)]:
    s_hole = Part.makeCylinder(1.9, REAR_WALL_T + 4.0, s_pt, Vector(0, 0, 1))
    body = body.cut(s_hole)

# ------------------------------------------------------------------------------
# 9. Front Basement: 16mm Power Switch & Honeycomb Intake Vents
# ------------------------------------------------------------------------------
print("9. Adding front 16mm illuminated power switch port and PSU intake vents...", flush=True)

# Power switch centered in right wiring corridor of basement (X ~ 121.8 mm, Y ~ 26 mm)
sw_cx = WALL + INT_W - 30.0
sw_cy = FLOOR_T + BASEMENT_H / 2.0
sw_hole = Part.makeCylinder(SWITCH_DIA / 2.0, WALL + 4.0, Vector(sw_cx, sw_cy, -2.0), Vector(0, 0, 1))
body = body.cut(sw_hole)

# Intake vents on left front of basement (directly in front of PSU)
for row in range(-1, 3):
    cy = FLOOR_T + 22.0 + row * 8.0
    row_off = 4.0 if (row % 2 != 0) else 0.0
    for col in range(-3, 4):
        cx = psu_cx + col * 9.0 + row_off
        if abs(cx - psu_cx) < 32.0:
            vent = make_hex_prism(6.5, WALL + 4.0, cx, cy, -2.0)
            body = body.cut(vent)

# ------------------------------------------------------------------------------
# 10. Rear SAS Cable Egress Ports
# ------------------------------------------------------------------------------
print("10. Cutting dual rear SAS cable pass-through ports...", flush=True)
sas_slot1 = Part.makeBox(18.0, 14.0, REAR_WALL_T + 4.0,
                         Vector(fan_cx - 45.0, Y_UPPER_FLOOR + UPPER_H - 18.0, Z_PLEN_END - 2.0))
sas_slot2 = Part.makeBox(18.0, 14.0, REAR_WALL_T + 4.0,
                         Vector(fan_cx + 27.0, Y_UPPER_FLOOR + UPPER_H - 18.0, Z_PLEN_END - 2.0))
body = body.cut(sas_slot1).cut(sas_slot2)

# ------------------------------------------------------------------------------
# 11. Top Service Aperture & Drop-In Lid
# ------------------------------------------------------------------------------
print("11. Creating recessed stepped perimeter roof aperture and solid matching lid...", flush=True)

roof_shelf_y = OUT_H - ROOF_T + 1.7 # 175.2 mm

# Lower through-cut in roof (Z = 165.0 to 198.0 mm)
aperture = Part.makeBox(135.8, ROOF_T + 2.0, 33.0,
                        Vector(8.0, OUT_H - ROOF_T - 1.0, 165.0))

# Upper recessed rebate ledge in roof (Z = 162.0 to 199.5 mm)
rebate   = Part.makeBox(143.8, 2.0, 37.5,
                        Vector(4.0, roof_shelf_y, 162.0))

body = body.cut(aperture).cut(rebate)

# Create Matching Service Lid with 0.4 mm perimeter clearance
plug   = Part.makeBox(135.0, 1.7, 32.2, Vector(8.4, OUT_H - ROOF_T, 165.4))
flange = Part.makeBox(143.0, 1.8, 36.7, Vector(4.4, roof_shelf_y, 162.4))
lid = plug.fuse(flange)

# Blind tactile circular thumb dimple on top of lid (1.0 mm deep, completely solid bottom)
thumb = Part.makeCylinder(12.0, 1.2, Vector(OUT_W / 2.0, OUT_H - 1.0, 180.0), Vector(0, 1, 0))
lid = lid.cut(thumb)

# Tactile grip ridges flanking the thumb dimple for effortless removal
for dx in (-28.0, -22.0, -16.0, 16.0, 22.0, 28.0):
    ridge = Part.makeBox(2.0, 0.6, 12.0, Vector(OUT_W / 2.0 + dx - 1.0, OUT_H, 180.0 - 6.0))
    lid = lid.fuse(ridge)

print(f"Body Volume: {body.Volume:.2f} mm3, isClosed: {body.isClosed()}", flush=True)
print(f"Lid Volume:  {lid.Volume:.2f} mm3, isClosed: {lid.isClosed()}", flush=True)

assert body.isClosed(), "ERROR: Body solid is not closed/watertight!"
assert lid.isClosed(), "ERROR: Lid solid is not closed/watertight!"

# ==============================================================================
# 12. EXPORT DELIVERABLES
# ==============================================================================

step_body = os.path.join(OUT_DIR, "dl380_flex_case_body.step")
step_lid  = os.path.join(OUT_DIR, "dl380_flex_case_lid.step")
step_all  = os.path.join(OUT_DIR, "dl380_flex_case.step")

stl_body  = os.path.join(OUT_DIR, "dl380_flex_case_body.stl")
stl_lid   = os.path.join(OUT_DIR, "dl380_flex_case_lid.stl")
stl_print = os.path.join(PRINT_DIR, "dl380_flex_case_all-parts.stl")

print(f"12. Exporting STEP models...", flush=True)
body.exportStep(step_body)
lid.exportStep(step_lid)

# Compound for full assembly STEP
compound = Part.Compound([body, lid])
compound.exportStep(step_all)

print(f"13. Tessellating production STL meshes...", flush=True)
mesh_body = MeshPart.meshFromShape(Shape=body, LinearDeflection=0.08, AngularDeflection=0.35)
mesh_lid  = MeshPart.meshFromShape(Shape=lid,  LinearDeflection=0.08, AngularDeflection=0.35)

mesh_body.write(stl_body)
mesh_lid.write(stl_lid)

# Combine for single plate print STL
mesh_all = Mesh.Mesh()
mesh_all.addMesh(mesh_body)
mesh_all.addMesh(mesh_lid)
mesh_all.write(stl_print)

# Write report
report_path = os.path.join(OUT_DIR, "dl380_flex_case_report.txt")
with open(report_path, "w") as f:
    f.write("=" * 80 + "\n")
    f.write("DL380 DOUBLE-DECKER FLEX-ATX ENCLOSURE - BUILD REPORT\n")
    f.write("=" * 80 + "\n\n")
    f.write(f"Target Cage:      HP ProLiant DL380 G6/G7 8-bay 2.5\" SFF (145 x 87 x 165 mm)\n")
    f.write(f"Target PSU:       Enhance ENP-2320 (Flex-ATX 200W, 150 x 81.5 x 40.5 mm)\n")
    f.write(f"Target Fan:       120 mm Arctic P12 PWM PST / Noctua NF-A12 (120 x 120 x 25 mm)\n\n")
    f.write(f"Outer Dimensions: {OUT_W:.2f} mm (W) x {OUT_H:.2f} mm (H) x {OUT_D:.2f} mm (D)\n")
    f.write(f"Body Volume:      {body.Volume:.2f} mm3 (isClosed: {body.isClosed()})\n")
    f.write(f"Lid Volume:       {lid.Volume:.2f} mm3 (isClosed: {lid.isClosed()})\n")
    f.write(f"Body Facets:      {mesh_body.CountFacets:,}\n")
    f.write(f"Lid Facets:       {mesh_lid.CountFacets:,}\n\n")
    f.write(f"Print Bed Size:   Fits standard 256 x 256 mm build plates (Bambu Lab X1C/P1S/A1)\n")
    f.write(f"Bed Footprint:    {OUT_W:.2f} mm (W) x {OUT_D:.2f} mm (D), Margin X = {256.0 - OUT_W:.1f} mm, Margin Y = {256.0 - OUT_D:.1f} mm\n")
    f.write(f"Switch Port:      16.2 mm illuminated push-button switch in lower front bezel\n")
    f.write(f"Power Routing:    Vertical 32x24 mm mid-deck slot directly under backplane 10-pin port\n")
    f.write(f"Basement Wiring:  Dedicated 62.3 mm wide wiring corridor beside PSU\n")
    f.write(f"Fan Grille:       115.0 mm diameter hexagonal honeycomb rear exhaust\n")
    f.write(f"Service Lid:      Stepped perimeter drop-in lid, 100% solid top (no through-holes)\n")
    f.write("=" * 80 + "\n")

print("=" * 80)
print(f"SUCCESS: DL380 Double-Decker Flex-ATX Enclosure Generated Successfully!")
print(f"  STEP Body:   {step_body}")
print(f"  STEP Lid:    {step_lid}")
print(f"  Print STL:   {stl_print}")
print(f"  Report:      {report_path}")
print("=" * 80, flush=True)
