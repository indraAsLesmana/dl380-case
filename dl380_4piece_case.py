#!/usr/bin/env python3
"""
dl380_4piece_case.py - Parametric FreeCAD Model of the DL380 4-Piece Modular Enclosure
with Internal Corner Snap-Fit Latches and Side-Wall Alignment Tongue-and-Groove.

4-Piece Architecture:
  1. Part 01A: Lower Front Case (PSU Basement Front, Z=0 to 138 mm, Y=0 to 48.5 mm)
  2. Part 01B: Upper Front Case (DL380 Drive Cage Bay, Z=0 to 138 mm, Y=48.5 to 151.5 mm)
  3. Part 02A: Lower Back Case  (PSU Rear Bay & Guide, Z=138 to 215 mm, Y=0 to 48.5 mm)
  4. Part 02B: Upper Back Case  (92mm Fan Chamber & Latch Arms, Z=138 to 215 mm, Y=48.5 to 151.5 mm)
  5. Part 03:  Service Lid      (Drop-in Plenum Roof Lid, Z=165 to 209.5 mm)

Key Mechanical & DfAM Features:
  - 100% Support-Free Printing for Parts 01A, 01B, 02A, and 03!
  - Part 02B requires only minimal build-plate support (~8g) for horizontal latch arms.
  - Grounded internal vertical snap pillars rise from the basement floor with 45-degree self-supporting chamfers.
  - Smooth, flush outer side walls with zero snagging and clean tool-free snap assembly.
  - Mating side-wall alignment tongue-and-groove joint absorbs lateral shear and drive vibration.
  - Standard Z-split push-release snap-fit arms (l_arm, r_arm) lock upper front and back cases securely.
"""

import os, sys
for p in ['/usr/lib/freecad/lib', '/usr/lib/freecad-python3/lib', '/usr/lib/freecad/Ext']:
    if os.path.exists(p) and p not in sys.path:
        sys.path.append(p)

import math, time
import FreeCAD as App
import Part, Mesh, MeshPart
from FreeCAD import Vector, Rotation, Placement

# ------------------------------------------------------------------------------
# 1. PARAMETERS & CONFIGURATION (Calibrated)
# ------------------------------------------------------------------------------
WALL            =   3.0    # mm outer wall thickness
FLOOR_T         =   3.5    # mm bottom floor thickness
MID_DECK_T      =   5.5    # mm mid-deck floor thickness
ROOF_T          =   3.5    # mm top roof thickness
REAR_WALL_T     =   5.0    # mm rear wall thickness

BEZEL_W         = 180.0
BEZEL_H         =  86.0
BEZEL_D         =  11.5

CAGE_W          = 145.0
CAGE_H          =  75.52
CAGE_D          = 137.25
FIT_CLEAR       =   0.5
INT_W           = CAGE_W + 2 * FIT_CLEAR   # 146.0 mm internal guide bay

RUNNER_H        =   1.5
RUNNER_W        =   6.0
RAMP_L          =   6.0

PSU_W           =  82.32
PSU_H           =  42.58
PSU_L           = 150.07
BASEMENT_H      =  45.0

SWITCH_DIA      =  16.2

FAN_SIZE        =  92.0
FAN_D           =  25.0
FAN_APERTURE    =  86.0
FAN_PITCH       =  82.5
UPPER_H         = FAN_SIZE + 2.0  # 94.0 mm

Z_SPLIT         = 138.0    # mm split plane between Front Case and Backcase
Y_SPLIT         = FLOOR_T + BASEMENT_H # 48.5 mm horizontal split plane

OUT_W           = WALL + BEZEL_W + WALL # 186.0 mm
OUT_D           = 215.00                # 215.0 mm
OUT_H           = FLOOR_T + BASEMENT_H + MID_DECK_T + UPPER_H + ROOF_T # 151.5 mm

X_CAGE_0        = (OUT_W - INT_W) / 2.0 # 20.0 mm
X_CAGE_1        = X_CAGE_0 + INT_W      # 166.0 mm
X_BEZEL_0       = (OUT_W - BEZEL_W) / 2.0 # 3.0 mm
X_BEZEL_1       = X_BEZEL_0 + BEZEL_W     # 183.0 mm

Z_BEZEL_STOP    = BEZEL_D               # 11.5 mm
Z_CAGE_STOP     = CAGE_D                # 137.25 mm
Z_PLEN_END      = 210.0                 # 210.0 mm

fan_cx          = OUT_W / 2.0           # 93.0 mm
fan_cy          = Y_SPLIT + MID_DECK_T + UPPER_H / 2.0 # 101.0 mm
psu_cx          = (WALL + 87.5) / 2.0   # 45.25 mm

REPO_DIR        = os.path.dirname(os.path.abspath(__file__))
OUT_DIR         = os.path.join(REPO_DIR, "out", "4piece")
PKG_DIR         = os.path.join(REPO_DIR, "print_service_package", "4piece")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(PKG_DIR, exist_ok=True)

# ------------------------------------------------------------------------------
# 2. GEOMETRY HELPER FUNCTIONS
# ------------------------------------------------------------------------------
def make_hex_prism(cell_w, depth, center_x, center_y, z_start):
    r = cell_w / (2.0 * math.cos(math.radians(30)))
    pts = []
    for i in range(6):
        ang = math.radians(30 + i * 60)
        px = center_x + r * math.cos(ang)
        py = center_y + r * math.sin(ang)
        pts.append(Vector(px, py, z_start))
    pts.append(pts[0])
    w = Part.makePolygon(pts)
    f = Part.Face(w)
    return f.extrude(Vector(0, 0, depth))

def make_diamond_y(wx, wz, depth, cx, cz, y_start):
    p1 = Vector(cx,          y_start, cz - wz / 2.0)
    p2 = Vector(cx + wx / 2, y_start, cz)
    p3 = Vector(cx,          y_start, cz + wz / 2.0)
    p4 = Vector(cx - wx / 2, y_start, cz)
    poly = Part.makePolygon([p1, p2, p3, p4, p1])
    face = Part.Face(poly)
    return face.extrude(Vector(0, depth, 0))

def make_diamond_x(wz, wy, depth, cz, cy, x_start):
    p1 = Vector(x_start, cy - wy / 2.0, cz)
    p2 = Vector(x_start, cy,             cz + wz / 2.0)
    p3 = Vector(x_start, cy + wy / 2.0, cz)
    p4 = Vector(x_start, cy,             cz - wz / 2.0)
    poly = Part.makePolygon([p1, p2, p3, p4, p1])
    face = Part.Face(poly)
    return face.extrude(Vector(depth, 0, 0))

def make_diamond_z(wx, wy, depth, cx, cy, z_start):
    """Diamond prism cutting horizontally through the rear wall (Z axis).
    When printed vertically (Y-up), 45-degree struts require ZERO supports."""
    p1 = Vector(cx, cy + wy / 2.0, z_start)
    p2 = Vector(cx + wx / 2.0, cy, z_start)
    p3 = Vector(cx, cy - wy / 2.0, z_start)
    p4 = Vector(cx - wx / 2.0, cy, z_start)
    poly = Part.makePolygon([p1, p2, p3, p4, p1])
    face = Part.Face(poly)
    return face.extrude(Vector(0, 0, depth))

def make_left_latch():
    pts = [
        Vector(0.0, 0, 142.0),
        Vector(5.7, 0, 142.0),
        Vector(5.7, 0, 138.0),
        Vector(5.1, 0, 115.0),
        Vector(3.3, 0, 115.0),
        Vector(0.4, 0, 121.0),
        Vector(0.4, 0, 127.0),
        Vector(3.3, 0, 127.0),
        Vector(3.3, 0, 138.0),
        Vector(0.0, 0, 138.0),
        Vector(0.0, 0, 142.0),
    ]
    poly = Part.makePolygon(pts)
    face = Part.Face(poly)
    arm = face.extrude(Vector(0, 11.0, 0)).translate(Vector(0, 94.5, 0))
    for rz in [122.5, 124.0, 125.5]:
        rib = Part.makeBox(0.4, 9.0, 0.8, Vector(0.0, 95.5, rz - 0.4))
        arm = arm.fuse(rib)
    return arm

def make_right_latch():
    pts = [
        Vector(OUT_W - 0.0, 0, 142.0),
        Vector(OUT_W - 5.7, 0, 142.0),
        Vector(OUT_W - 5.7, 0, 138.0),
        Vector(OUT_W - 5.1, 0, 115.0),
        Vector(OUT_W - 3.3, 0, 115.0),
        Vector(OUT_W - 0.4, 0, 121.0),
        Vector(OUT_W - 0.4, 0, 127.0),
        Vector(OUT_W - 3.3, 0, 127.0),
        Vector(OUT_W - 3.3, 0, 138.0),
        Vector(OUT_W - 0.0, 0, 138.0),
        Vector(OUT_W - 0.0, 0, 142.0),
    ]
    poly = Part.makePolygon(pts)
    face = Part.Face(poly)
    arm = face.extrude(Vector(0, 11.0, 0)).translate(Vector(0, 94.5, 0))
    for rz in [122.5, 124.0, 125.5]:
        rib = Part.makeBox(0.4, 9.0, 0.8, Vector(OUT_W - 0.4, 95.5, rz - 0.4))
        arm = arm.fuse(rib)
    return arm

def make_vert_snap_pillar(z, length=8.0, is_right=False):
    """
    Vertical cantilever snap latch rising from Lower Case floor into Upper Case socket.
    Includes a solid grounded base pillar bonded to side wall and floor,
    and a 45-degree self-supporting retention tooth.
    """
    if not is_right:
        x_base = WALL
        x_arm  = WALL + 0.6
        pillar = Part.makeBox(2.4, Y_SPLIT - FLOOR_T, length, Vector(x_base, FLOOR_T, z))
        arm_box = Part.makeBox(1.8, 12.0, length, Vector(x_arm, Y_SPLIT, z))
        # Tooth extends towards -X (into left side wall socket)
        p1 = Vector(x_arm,       Y_SPLIT + 5.0, z)
        p2 = Vector(x_arm - 1.2, Y_SPLIT + 6.5, z)
        p3 = Vector(x_arm - 1.2, Y_SPLIT + 9.0, z)
        p4 = Vector(x_arm,       Y_SPLIT + 11.0, z)
        poly = Part.makePolygon([p1, p2, p3, p4, p1])
        tooth = Part.Face(poly).extrude(Vector(0, 0, length))
        return pillar.fuse(arm_box).fuse(tooth)
    else:
        x_base = OUT_W - WALL - 2.4
        x_arm  = OUT_W - WALL - 2.4
        pillar = Part.makeBox(2.4, Y_SPLIT - FLOOR_T, length, Vector(x_base, FLOOR_T, z))
        arm_box = Part.makeBox(1.8, 12.0, length, Vector(x_arm, Y_SPLIT, z))
        # Tooth extends towards +X (into right side wall socket)
        p1 = Vector(x_arm + 1.8,       Y_SPLIT + 5.0, z)
        p2 = Vector(x_arm + 1.8 + 1.2, Y_SPLIT + 6.5, z)
        p3 = Vector(x_arm + 1.8 + 1.2, Y_SPLIT + 9.0, z)
        p4 = Vector(x_arm + 1.8,       Y_SPLIT + 11.0, z)
        poly = Part.makePolygon([p1, p2, p3, p4, p1])
        tooth = Part.Face(poly).extrude(Vector(0, 0, length))
        return pillar.fuse(arm_box).fuse(tooth)

def make_vert_snap_socket(z, length=8.0, is_right=False):
    """Internal socket cut into Upper Case side wall to receive lower case snap arm and tooth."""
    if not is_right:
        slot   = Part.makeBox(2.5, 13.5, length + 1.0, Vector(WALL + 0.3, Y_SPLIT - 0.5, z - 0.5))
        pocket = Part.makeBox(1.8, 5.5,  length + 1.0, Vector(WALL - 1.0, Y_SPLIT + 5.0, z - 0.5))
        return slot.fuse(pocket)
    else:
        slot   = Part.makeBox(2.5, 13.5, length + 1.0, Vector(OUT_W - WALL - 2.8, Y_SPLIT - 0.5, z - 0.5))
        pocket = Part.makeBox(1.8, 5.5,  length + 1.0, Vector(OUT_W - WALL - 0.8, Y_SPLIT + 5.0, z - 0.5))
        return slot.fuse(pocket)

# ------------------------------------------------------------------------------
# 3. BUILD 4-PIECE MODULAR PARTS
# ------------------------------------------------------------------------------
def build_4piece_system():
    print("1. Modeling Lower Front Case (PSU Basement Front)...", flush=True)
    lf_shell = Part.makeBox(OUT_W, Y_SPLIT, Z_SPLIT, Vector(0, 0, 0))
    lf_void  = Part.makeBox(OUT_W - 2 * WALL, BASEMENT_H + 2.0, Z_SPLIT - FLOOR_T + 1.0,
                            Vector(WALL, FLOOR_T, FLOOR_T))
    lower_front = lf_shell.cut(lf_void)

    # Switch hole & intake vents
    sw_cx = OUT_W - WALL - 38.0
    sw_cy = FLOOR_T + BASEMENT_H / 2.0
    sw_hole = Part.makeCylinder(SWITCH_DIA / 2.0, WALL + 4.0, Vector(sw_cx, sw_cy, -2.0), Vector(0, 0, 1))
    lower_front = lower_front.cut(sw_hole)

    for row in range(-1, 3):
        cy = FLOOR_T + 22.0 + row * 8.0
        row_off = 4.0 if (row % 2 != 0) else 0.0
        for col in range(-3, 4):
            cx = psu_cx + col * 9.0 + row_off
            if abs(cx - psu_cx) < 32.0:
                vent = make_hex_prism(6.5, WALL + 4.0, cx, cy, -2.0)
                lower_front = lower_front.cut(vent)

    # Permanent central vertical divider rib
    f_divider = Part.makeBox(2.0, BASEMENT_H, Z_SPLIT - 20.0, Vector(87.5, FLOOR_T, 20.0))
    lower_front = lower_front.fuse(f_divider)

    # PSU pusher stops and lateral guide rails
    f_push_l = Part.makeBox(11.0, BASEMENT_H, 4.0, Vector(3.0, FLOOR_T, 55.60))
    f_push_r = Part.makeBox(11.0, BASEMENT_H, 4.0, Vector(76.5, FLOOR_T, 55.60))
    f_rail_l = Part.makeBox(0.80, 16.5, 132.0 - 59.60, Vector(3.0, FLOOR_T, 59.60))
    f_rail_r = Part.makeBox(0.80, 16.5, 132.0 - 59.60, Vector(86.70, FLOOR_T, 59.60))

    p1_fl = Vector(3.80, 0, 132.0)
    p2_fl = Vector(3.00, 0, 138.0)
    p3_fl = Vector(3.00, 0, 132.0)
    poly_fl = Part.makePolygon([p1_fl, p2_fl, p3_fl, p1_fl])
    wedge_fl = Part.Face(poly_fl).extrude(Vector(0, 16.5, 0)).translate(Vector(0, FLOOR_T, 0))

    p1_fr = Vector(86.70, 0, 132.0)
    p2_fr = Vector(87.50, 0, 138.0)
    p3_fr = Vector(87.50, 0, 132.0)
    poly_fr = Part.makePolygon([p1_fr, p2_fr, p3_fr, p1_fr])
    wedge_fr = Part.Face(poly_fr).extrude(Vector(0, 16.5, 0)).translate(Vector(0, FLOOR_T, 0))

    lower_front = (lower_front
                   .fuse(f_push_l).fuse(f_push_r)
                   .fuse(f_rail_l).fuse(wedge_fl)
                   .fuse(f_rail_r).fuse(wedge_fr))

    # Rear female lap-joint rebate on lower front SIDE WALLS ONLY (Z = 133.2 to 138.0 mm)
    # Keeping floor 100% solid and flat on build plate
    rebate_l = Part.makeBox(2.4, Y_SPLIT + 1.0, 4.8, Vector(-0.5, 0, Z_SPLIT - 4.8))
    rebate_r = Part.makeBox(2.4, Y_SPLIT + 1.0, 4.8, Vector(OUT_W - 1.9, 0, Z_SPLIT - 4.8))
    lower_front = lower_front.cut(rebate_l).cut(rebate_r)

    # Top alignment tongue along side walls
    lip_fl = Part.makeBox(1.5, 2.0, Z_SPLIT - 4.8 - 1.5, Vector(1.5, Y_SPLIT, 1.5))
    lip_fr = Part.makeBox(1.5, 2.0, Z_SPLIT - 4.8 - 1.5, Vector(OUT_W - 3.0, Y_SPLIT, 1.5))
    lower_front = lower_front.fuse(lip_fl).fuse(lip_fr)

    # 4 vertical cantilever snap pillars grounded to floor and side walls
    p_fl = make_vert_snap_pillar(16.0,  8.0, is_right=False)
    p_fr = make_vert_snap_pillar(16.0,  8.0, is_right=True)
    p_ml = make_vert_snap_pillar(101.0, 8.0, is_right=False)
    p_mr = make_vert_snap_pillar(101.0, 8.0, is_right=True)
    lower_front = lower_front.fuse(p_fl).fuse(p_fr).fuse(p_ml).fuse(p_mr)

    print(f"Lower Front complete: Vol = {lower_front.Volume:.2f} mm3, isClosed: {lower_front.isClosed()}", flush=True)

    print("2. Modeling Upper Front Case (DL380 Cage Bay)...", flush=True)
    uf_shell = Part.makeBox(OUT_W, OUT_H - Y_SPLIT, Z_SPLIT, Vector(0, Y_SPLIT, 0))
    uf_void  = Part.makeBox(INT_W, UPPER_H + 2.0, Z_SPLIT + 1.0 - BEZEL_D,
                            Vector(X_CAGE_0, Y_SPLIT + MID_DECK_T, BEZEL_D))
    uf_bezel = Part.makeBox(BEZEL_W, BEZEL_H, BEZEL_D + 2.0,
                            Vector(X_BEZEL_0, 50.5, -2.0))
    upper_front = uf_shell.cut(uf_void).cut(uf_bezel)

    # Runner rails on mid-deck
    p1 = Vector(0, 0, 0)
    p2 = Vector(0, 0, RAMP_L)
    p3 = Vector(0, RUNNER_H, RAMP_L)
    ramp_wire = Part.Wire([Part.makeLine(p1, p2), Part.makeLine(p2, p3), Part.makeLine(p3, p1)])
    ramp_face = Part.Face(ramp_wire)

    ramp_l = ramp_face.extrude(Vector(RUNNER_W, 0, 0)).translate(Vector(X_CAGE_0, Y_SPLIT + MID_DECK_T, BEZEL_D))
    ramp_r = ramp_face.extrude(Vector(RUNNER_W, 0, 0)).translate(Vector(X_CAGE_1 - RUNNER_W, Y_SPLIT + MID_DECK_T, BEZEL_D))

    track_l = Part.makeBox(RUNNER_W, RUNNER_H, Z_SPLIT - (BEZEL_D + RAMP_L),
                           Vector(X_CAGE_0, Y_SPLIT + MID_DECK_T, BEZEL_D + RAMP_L))
    track_r = Part.makeBox(RUNNER_W, RUNNER_H, Z_SPLIT - (BEZEL_D + RAMP_L),
                           Vector(X_CAGE_1 - RUNNER_W, Y_SPLIT + MID_DECK_T, BEZEL_D + RAMP_L))

    upper_front = upper_front.fuse(ramp_l).fuse(ramp_r).fuse(track_l).fuse(track_r)

    # Floor relief channels for bottom 5.0 mm shoulder studs
    for sx in (45.25, 45.25 + 54.25):
        cx = X_CAGE_0 + sx
        chan = Part.makeBox(16.0, 4.0, Z_SPLIT - BEZEL_D + 2.0,
                             Vector(cx - 8.0, Y_SPLIT + MID_DECK_T - 2.5, BEZEL_D - 1.0))
        upper_front = upper_front.cut(chan)

    # Top roof diamond mesh (self-supporting at 45 degrees)
    step_dx = 22.5
    step_dz = 22.5
    cuts_top = []
    for row in range(-2, 4):
        cz = 73.0 + row * step_dz
        offset_x = (step_dx * 0.5) if (row % 2 != 0) else 0.0
        for col in range(-2, 3):
            cx = fan_cx + col * step_dx + offset_x
            if 32.0 < cx < 154.0 and 18.0 < cz < 128.0:
                d = make_diamond_y(19.0, 19.0, ROOF_T + 4.0, cx, cz, OUT_H - ROOF_T - 2.0)
                cuts_top.append(d)

    if cuts_top:
        all_top = cuts_top[0]
        for c in cuts_top[1:]:
            all_top = all_top.fuse(c)
        upper_front = upper_front.cut(all_top)

    # Side wall diamond mesh
    cuts_side = []
    for row in range(-1, 3):
        cy = 100.0 + row * 22.0
        row_off = (step_dz * 0.5) if (row % 2 != 0) else 0.0
        for col in range(-2, 3):
            cz = 73.0 + col * step_dz + row_off
            if 22.0 < cz < 125.0:
                dl = make_diamond_x(18.0, 18.0, WALL + 4.0, cz, cy, -2.0)
                dr = make_diamond_x(18.0, 18.0, WALL + 4.0, cz, cy, OUT_W - WALL - 2.0)
                cuts_side.extend([dl, dr])

    if cuts_side:
        all_side = cuts_side[0]
        for c in cuts_side[1:]:
            all_side = all_side.fuse(c)
        upper_front = upper_front.cut(all_side)

    # Detent catch windows for rear latch arms
    chan_l = Part.makeBox(12.0, 16.0, 24.5, Vector(3.0, 92.0, 114.0))
    chan_r = Part.makeBox(12.0, 16.0, 24.5, Vector(OUT_W - 15.0, 92.0, 114.0))
    win_l  = Part.makeBox(5.5, 12.4, 12.9, Vector(-1.0, 93.8, 114.5))
    win_r  = Part.makeBox(5.5, 12.4, 12.9, Vector(OUT_W - 4.5, 93.8, 114.5))
    bevel_l = Part.makeBox(2.0, 14.0, 2.5, Vector(2.0, 93.0, 135.5))
    bevel_r = Part.makeBox(2.0, 14.0, 2.5, Vector(OUT_W - 4.0, 93.0, 135.5))
    upper_front = upper_front.cut(chan_l).cut(chan_r).cut(win_l).cut(win_r).cut(bevel_l).cut(bevel_r)

    # Rear female lap-joint rebate on upper front side walls & roof
    reb_uf_l = Part.makeBox(2.4, OUT_H - Y_SPLIT + 1.0, 4.8, Vector(-0.5, Y_SPLIT - 0.5, Z_SPLIT - 4.8))
    reb_uf_r = Part.makeBox(2.4, OUT_H - Y_SPLIT + 1.0, 4.8, Vector(OUT_W - 1.9, Y_SPLIT - 0.5, Z_SPLIT - 4.8))
    reb_uf_t = Part.makeBox(OUT_W + 1.0, 2.4, 4.8, Vector(-0.5, OUT_H - 1.9, Z_SPLIT - 4.8))
    upper_front = upper_front.cut(reb_uf_l).cut(reb_uf_r).cut(reb_uf_t)

    # Bottom mating grooves receiving lower front side tongues
    grv_l = Part.makeBox(1.8, 2.3, Z_SPLIT - 4.8 - 1.2, Vector(1.35, Y_SPLIT - 0.1, 1.35))
    grv_r = Part.makeBox(1.8, 2.3, Z_SPLIT - 4.8 - 1.2, Vector(OUT_W - 3.15, Y_SPLIT - 0.1, 1.35))
    upper_front = upper_front.cut(grv_l).cut(grv_r)

    # 4 recessed corner snap sockets inside side walls
    s_fl = make_vert_snap_socket(16.0,  8.0, is_right=False)
    s_fr = make_vert_snap_socket(16.0,  8.0, is_right=True)
    s_ml = make_vert_snap_socket(101.0, 8.0, is_right=False)
    s_mr = make_vert_snap_socket(101.0, 8.0, is_right=True)
    upper_front = upper_front.cut(s_fl).cut(s_fr).cut(s_ml).cut(s_mr)

    print(f"Upper Front complete: Vol = {upper_front.Volume:.2f} mm3, isClosed: {upper_front.isClosed()}", flush=True)

    print("3. Modeling Lower Back Case (PSU Rear Mount)...", flush=True)
    lb_shell = Part.makeBox(OUT_W, Y_SPLIT, OUT_D - Z_SPLIT, Vector(0, 0, Z_SPLIT))
    lb_void  = Part.makeBox(OUT_W - 2 * WALL, BASEMENT_H + 2.0, Z_PLEN_END - (Z_SPLIT - 1.0),
                            Vector(WALL, FLOOR_T, Z_SPLIT - 1.0))
    lower_back = lb_shell.cut(lb_void)

    # PSU guide rails and lead-in wedges
    b_rail_l = Part.makeBox(0.80, 16.5, Z_PLEN_END - 144.0, Vector(3.0, FLOOR_T, 144.0))
    b_rail_r = Part.makeBox(0.80, 16.5, Z_PLEN_END - 144.0, Vector(86.70, FLOOR_T, 144.0))

    p1_l = Vector(3.00, 0, 138.0)
    p2_l = Vector(3.00, 0, 144.0)
    p3_l = Vector(3.80, 0, 144.0)
    poly_bl = Part.makePolygon([p1_l, p2_l, p3_l, p1_l])
    wedge_bl = Part.Face(poly_bl).extrude(Vector(0, 16.5, 0)).translate(Vector(0, FLOOR_T, 0))

    p1_r = Vector(87.50, 0, 138.0)
    p2_r = Vector(86.70, 0, 144.0)
    p3_r = Vector(87.50, 0, 144.0)
    poly_br = Part.makePolygon([p1_r, p2_r, p3_r, p1_r])
    wedge_br = Part.Face(poly_br).extrude(Vector(0, 16.5, 0)).translate(Vector(0, FLOOR_T, 0))

    lower_back = lower_back.fuse(b_rail_l).fuse(wedge_bl).fuse(b_rail_r).fuse(wedge_br)

    # Rear PSU cutout (open U-channel to top of basement for 100% support-free print)
    psu_window = Part.makeBox(74.0, BASEMENT_H + 5.0, REAR_WALL_T + 4.0, Vector(6.0, 5.5, Z_PLEN_END - 2.0))
    lower_back = lower_back.cut(psu_window)

    # Front male tongue flange on side walls only
    t_box_l = Part.makeBox(2.1, Y_SPLIT, 4.5, Vector(0, 0, Z_SPLIT - 4.5))
    t_box_r = Part.makeBox(2.1, Y_SPLIT, 4.5, Vector(OUT_W - 2.1, 0, Z_SPLIT - 4.5))
    lower_back = lower_back.fuse(t_box_l).fuse(t_box_r)

    # 2 vertical cantilever snap pillars grounded to floor and side walls
    p_rl = make_vert_snap_pillar(181.0, 8.0, is_right=False)
    p_rr = make_vert_snap_pillar(181.0, 8.0, is_right=True)
    lower_back = lower_back.fuse(p_rl).fuse(p_rr)

    # Top alignment tongue on lower back side walls
    lip_bl = Part.makeBox(1.5, 2.0, OUT_D - Z_SPLIT - 1.5, Vector(1.5, Y_SPLIT, Z_SPLIT))
    lip_br = Part.makeBox(1.5, 2.0, OUT_D - Z_SPLIT - 1.5, Vector(OUT_W - 3.0, Y_SPLIT, Z_SPLIT))
    lower_back = lower_back.fuse(lip_bl).fuse(lip_br)

    print(f"Lower Back complete: Vol = {lower_back.Volume:.2f} mm3, isClosed: {lower_back.isClosed()}", flush=True)

    print("4. Modeling Upper Back Case (92mm Fan Plenum & Service Bay)...", flush=True)
    ub_shell = Part.makeBox(OUT_W, OUT_H - Y_SPLIT, OUT_D - Z_SPLIT, Vector(0, Y_SPLIT, Z_SPLIT))
    ub_void  = Part.makeBox(INT_W, UPPER_H + 2.0, Z_PLEN_END + 2.0 - (Z_SPLIT - 1.0),
                            Vector(WALL, Y_SPLIT + MID_DECK_T, Z_SPLIT - 1.0))
    upper_back = ub_shell.cut(ub_void)

    # Front male tongue flange on upper back side walls & roof
    t_u_l = Part.makeBox(2.1, OUT_H - Y_SPLIT, 4.5, Vector(0, Y_SPLIT, Z_SPLIT - 4.5))
    t_u_r = Part.makeBox(2.1, OUT_H - Y_SPLIT, 4.5, Vector(OUT_W - 2.1, Y_SPLIT, Z_SPLIT - 4.5))
    t_u_t = Part.makeBox(OUT_W, 2.1, 4.5, Vector(0, OUT_H - 2.1, Z_SPLIT - 4.5))
    upper_back = upper_back.fuse(t_u_l).fuse(t_u_r).fuse(t_u_t)

    # Rear stop frame with tab windows
    stop_box = Part.makeBox(INT_W, UPPER_H, 3.0, Vector(X_CAGE_0, Y_SPLIT + MID_DECK_T, Z_SPLIT))
    stop_hole = Part.makeBox(INT_W - 20.0, UPPER_H - 16.0, 5.0,
                             Vector(X_CAGE_0 + 10.0, Y_SPLIT + MID_DECK_T + 8.0, Z_SPLIT - 1.0))
    stop_frame = stop_box.cut(stop_hole)
    tab_win1 = Part.makeBox(34.0, 8.0, 5.0, Vector(X_CAGE_0 + 33.0, Y_SPLIT + MID_DECK_T, Z_SPLIT - 1.0))
    tab_win2 = Part.makeBox(34.0, 8.0, 5.0, Vector(X_CAGE_0 + 78.5, Y_SPLIT + MID_DECK_T, Z_SPLIT - 1.0))
    stop_frame = stop_frame.cut(tab_win1).cut(tab_win2)
    upper_back = upper_back.fuse(stop_frame)

    # 10-pin power pass-through slot
    power_slot = Part.makeBox(30.0, MID_DECK_T + 4.0, 26.0,
                              Vector(X_CAGE_0 + 114.0, Y_SPLIT - 2.0, 140.0))
    upper_back = upper_back.cut(power_slot)

    # Dual horizontal snap-fit latch arms
    l_arm = make_left_latch()
    r_arm = make_right_latch()
    upper_back = upper_back.fuse(l_arm).fuse(r_arm)

    # Rear 45° Diamond Mesh Fan Grille & M4 screw holes (100% Self-Supporting, Zero Sagging)
    # Directly applies DfAM principles: 45° struts require ZERO support material when printed vertically (Y-up)
    # Matches the Diamond Mesh pattern on the top roof and both side walls
    for dx in (-FAN_PITCH / 2.0, FAN_PITCH / 2.0):
        for dy in (-FAN_PITCH / 2.0, FAN_PITCH / 2.0):
            hole = Part.makeCylinder(4.2 / 2.0, REAR_WALL_T + 4.0,
                                     Vector(fan_cx + dx, fan_cy + dy, Z_PLEN_END - 2.0), Vector(0, 0, 1))
            upper_back = upper_back.cut(hole)

    d_cell  = 12.0
    d_pitch = 15.0
    r_max   = (FAN_APERTURE / 2.0) - 1.5

    diamond_cuts = []
    for row in range(-6, 7):
        cy = fan_cy + row * (d_pitch / 2.0)
        row_offset = (d_pitch / 2.0) if (row % 2 != 0) else 0.0
        for col in range(-6, 7):
            cx = fan_cx + col * d_pitch + row_offset
            dist = math.hypot(cx - fan_cx, cy - fan_cy)
            if dist + d_cell / 2.0 < r_max + 1.0 and dist < r_max:
                diamond_cuts.append(make_diamond_z(d_cell, d_cell, REAR_WALL_T + 4.0, cx, cy, Z_PLEN_END - 2.0))

    if diamond_cuts:
        all_diamonds = diamond_cuts[0]
        for d in diamond_cuts[1:]:
            all_diamonds = all_diamonds.fuse(d)
        upper_back = upper_back.cut(all_diamonds)

    # Top service lid aperture
    roof_shelf_y = OUT_H - ROOF_T + 1.7
    rebate   = Part.makeBox(143.8, 2.0, 44.5, Vector(fan_cx - 71.9, roof_shelf_y, 165.0))
    through  = Part.makeBox(135.0, ROOF_T + 4.0, 39.5, Vector(fan_cx - 67.5, OUT_H - ROOF_T - 2.0, 167.5))
    upper_back = upper_back.cut(rebate).cut(through)

    # Bottom grooves receiving lower back side tongues
    grv_bl = Part.makeBox(1.8, 2.3, OUT_D - Z_SPLIT - 1.2, Vector(1.35, Y_SPLIT - 0.1, Z_SPLIT))
    grv_br = Part.makeBox(1.8, 2.3, OUT_D - Z_SPLIT - 1.2, Vector(OUT_W - 3.15, Y_SPLIT - 0.1, Z_SPLIT))
    upper_back = upper_back.cut(grv_bl).cut(grv_br)

    # 2 recessed rear corner snap sockets
    s_rl = make_vert_snap_socket(181.0, 8.0, is_right=False)
    s_rr = make_vert_snap_socket(181.0, 8.0, is_right=True)
    upper_back = upper_back.cut(s_rl).cut(s_rr)

    print(f"Upper Back complete: Vol = {upper_back.Volume:.2f} mm3, isClosed: {upper_back.isClosed()}", flush=True)

    print("5. Modeling Snap-Fit Service Lid...", flush=True)
    plug   = Part.makeBox(134.4, 2.0, 38.9, Vector(fan_cx - 67.2, roof_shelf_y - 2.0, 167.8))
    flange = Part.makeBox(143.0, 1.8, 43.7, Vector(fan_cx - 71.5, roof_shelf_y, 165.4))
    lid = plug.fuse(flange)

    tab_l = Part.makeBox(18.0, 1.5, 3.5, Vector(fan_cx - 50.0, roof_shelf_y - 1.5, 161.9))
    tab_r = Part.makeBox(18.0, 1.5, 3.5, Vector(fan_cx + 32.0, roof_shelf_y - 1.5, 161.9))
    lid = lid.fuse(tab_l).fuse(tab_r)

    hook = Part.makeBox(14.0, 2.2, 1.8, Vector(fan_cx - 7.0, roof_shelf_y - 1.0, 209.1))
    lid = lid.fuse(hook)

    # Recessed grip grooves (debossed -0.6mm into surface for 100% support-free bed placement)
    for dx in (-45.0, -38.0, 38.0, 45.0):
        g_cut = Part.makeBox(2.0, 0.6, 12.0, Vector(fan_cx + dx - 1.0, OUT_H - 0.6, 186.0 - 6.0))
        lid = lid.cut(g_cut)

    print(f"Service Lid complete: Vol = {lid.Volume:.2f} mm3, isClosed: {lid.isClosed()}", flush=True)

    assert lower_front.isClosed(), "ERROR: Lower Front is not closed!"
    assert upper_front.isClosed(), "ERROR: Upper Front is not closed!"
    assert lower_back.isClosed(),  "ERROR: Lower Back is not closed!"
    assert upper_back.isClosed(),  "ERROR: Upper Back is not closed!"
    assert lid.isClosed(),         "ERROR: Service Lid is not closed!"

    return lower_front, upper_front, lower_back, upper_back, lid

# ------------------------------------------------------------------------------
# 4. EXPORT DELIVERABLES
# ------------------------------------------------------------------------------
def export_4piece_deliverables(lf, uf, lb, ub, lid):
    print("\n--- Exporting 4-Piece STEP & STL Models ---", flush=True)
    
    parts = [
        ("01A_lower_front", lf),
        ("01B_upper_front", uf),
        ("02A_lower_back",  lb),
        ("02B_upper_back",  ub),
        ("03_service_lid",  lid)
    ]
    
    # 1. Export STEP models
    for name, shape in parts:
        step_path = os.path.join(OUT_DIR, f"{name}.step")
        shape.exportStep(step_path)
        print(f"   - Exported STEP: {step_path}")
        
    compound = Part.Compound([lf, uf, lb, ub, lid])
    comp_step = os.path.join(OUT_DIR, "dl380_4piece_assembly.step")
    compound.exportStep(comp_step)
    print(f"   - Exported Assembly STEP: {comp_step}")

    # 2. Export Bed-Oriented STLs
    print("\n--- Tessellating Bed-Oriented STLs ---", flush=True)
    # 01A and 02A: Floor Y=0 flat on bed (Rotation around X by +90)
    # 01B: Rear face Z=138 flat on bed (Rotation around X by 180) -> 100% Support-Free!
    # 02B: Mid-deck Y=48.5 flat on bed (Rotation around X by +90) -> Only minor support under latch arms
    # 03:  Roof top flat on bed (Rotation around X by -90) -> 100% Support-Free!
    rot_floor_down = Rotation(Vector(1, 0, 0), 90.0)
    rot_rear_down  = Rotation(Vector(1, 0, 0), 180.0)
    rot_lid_down   = Rotation(Vector(1, 0, 0), -90.0)

    orientations = {
        "01A_lower_front": rot_floor_down,
        "01B_upper_front": rot_rear_down,
        "02A_lower_back":  rot_floor_down,
        "02B_upper_back":  rot_floor_down,
        "03_service_lid":  rot_lid_down,
    }

    for name, shape in parts:
        rot = orientations[name]
        p = shape.copy()
        p.Placement = Placement(Vector(0, 0, 0), rot)
        p.translate(Vector(-p.BoundBox.XMin, -p.BoundBox.YMin, -p.BoundBox.ZMin))
        
        mesh = MeshPart.meshFromShape(p, LinearDeflection=0.08, AngularDeflection=0.35)
        stl_out = os.path.join(OUT_DIR, f"{name}_bed.stl")
        stl_pkg = os.path.join(PKG_DIR, f"{name}_bed.stl")
        mesh.write(stl_out)
        mesh.write(stl_pkg)
        print(f"   - Bed STL: {stl_pkg} ({mesh.CountFacets:,} facets | Height: {p.BoundBox.ZLength:.1f} mm)")

    # 3. Write Report
    report_file = os.path.join(OUT_DIR, "dl380_4piece_report.txt")
    total_vol = lf.Volume + uf.Volume + lb.Volume + ub.Volume + lid.Volume
    with open(report_file, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("DL380 4-PIECE MODULAR ENCLOSURE - BUILD REPORT\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Part 01A (Lower Front): {lf.Volume:,.2f} mm3 (isClosed: {lf.isClosed()})\n")
        f.write(f"Part 01B (Upper Front): {uf.Volume:,.2f} mm3 (isClosed: {uf.isClosed()})\n")
        f.write(f"Part 02A (Lower Back):  {lb.Volume:,.2f} mm3 (isClosed: {lb.isClosed()})\n")
        f.write(f"Part 02B (Upper Back):  {ub.Volume:,.2f} mm3 (isClosed: {ub.isClosed()})\n")
        f.write(f"Part 03  (Service Lid): {lid.Volume:,.2f} mm3 (isClosed: {lid.isClosed()})\n")
        f.write(f"Total Volume:           {total_vol:,.2f} mm3 ({total_vol/1000:,.1f} cm3, ~{total_vol*1.26/1000:,.1f} g PETG)\n")
        f.write("=" * 80 + "\n")
    print(f"\nReport written to {report_file}", flush=True)

if __name__ == "__main__":
    t0 = time.time()
    lf, uf, lb, ub, lid = build_4piece_system()
    export_4piece_deliverables(lf, uf, lb, ub, lid)
    print(f"\nSUCCESS: 4-Piece Modular System Generated in {time.time() - t0:.2f} s!", flush=True)
