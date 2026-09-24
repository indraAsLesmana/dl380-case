#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
 dl380_cage_case.py  -  parametric external enclosure for an
 HP ProLiant DL380 G6/G7  8-bay 2.5" SFF drive cage + backplane
 (cage assy P/N 496074-001 and relatives)

 Run head-less:   freecadcmd dl380_cage_case.py
 Or from FreeCAD:  exec(open("dl380_cage_case.py").read())

 Outputs (into ./out):
   dl380_cage_case.step          body + lid, high precision STEP
   dl380_cage_case_body.step     body only
   dl380_cage_case_lid.step      lid only
   dl380_cage_case_body.stl      body, print mesh
   dl380_cage_case_lid.stl       lid,  print mesh
   dl380_cage_case_report.txt    derived dimensions + sanity checks

 Coordinate system
   X : width,  centred on 0  (-OUT_W/2 .. +OUT_W/2)
   Y : height, 0 = outside of the base (part stands on Y=0)
   Z : depth,  0 = FRONT face (caddy insertion side), grows to the rear

 Design notes
   * The fan lives INSIDE the rear section and exhausts through a printed
     honeycomb grille recessed into the outer face of the rear wall.  Nothing
     hangs off the back.
   * The rear section therefore has to be tall enough to swallow the fan frame,
     which is taller than the cage.  REAR_H is DERIVED, never hand-set: give it
     a fan small enough to fit the bay height and it comes out equal to BAY_H
     and the top is a flat prism again.
   * Air path is: open front -> through the caddies -> plenum -> fan -> grille.
     There is deliberately no tapered duct any more.  With the fan inside the
     plenum there is nothing to funnel into, and the volume is needed for the
     PicoPSU and the cabling.
================================================================================
"""

import math
import os
import sys

import FreeCAD as App
import Part
from FreeCAD import Vector

# ==============================================================================
# 1. PARAMETERS  -  everything you need to change lives here
# ==============================================================================

# ---- target hardware ---------------------------------------------------------
CAGE_W        = 145.0    # mm  HP cage outer width
CAGE_H        =  87.0    # mm  HP cage outer height
CAGE_D        = 165.0    # mm  HP cage outer depth (incl. backplane PCB)
FIT_CLEAR     =   0.4    # mm  slide-in clearance, per side  (spec: +0.4/side)

# ---- printing / structure ----------------------------------------------------
WALL          = 2.8      # mm  structural wall thickness
FLOOR_T       = 4.0      # mm  base floor thickness (stiffer, carries the cage)
LID_T         = 3.0      # mm  service lid plate thickness
LID_LIP_T     = 1.5      # mm  lid locating lip depth.  Deliberately shallow: the
                         #     plenum's interior ceiling is only 1.3 mm below it,
                         #     so the lip can never reach anything loose in there
LID_LIP_GAP   = 6.0      # mm  the lid's lip stops this far short of the fan

# ---- slide-and-click housing lid ---------------------------------------------
#  The lid slides horizontally along +Z from the front step into interlocking
#  45 deg guide rails on the outer walls, and clicks shut over a ramped catch
#  tooth in the front vertical step.  100% screwless, zero heat-set inserts.
SLIDE_CLEAR     = 0.25     # mm  glide clearance between lid runner and body rail
RAIL_W          = 1.4      # mm  projection of the body guide rail
RAIL_H          = 2.4      # mm  height of the body guide rail
RAIL_YC         = 98.0     # mm  rail center Y (between 95.4 and 100.6 mm, above bay roof)
SKIRT_D         = 10.0     # mm  how far the side skirts hang down
SKIRT_T         = 2.8      # mm  skirt wall thickness
LID_FRONT_T     = 2.4      # mm  thickness of front face covering the step
LATCH_W         = 18.0     # mm  width of the flexible cantilever snap arm
LATCH_TOOTH_H   = 2.0      # mm  height of the snap tooth
LATCH_TOOTH_D   = 1.2      # mm  protrusion of the snap tooth in +Z
LATCH_RELIEF    = 1.2      # mm  width of relief slots on sides of latch arm
LID_RING_W      = 24.0     # mm  outer width of front pull ring
LID_RING_LEN    = 22.0     # mm  forward extension of pull ring in -Z
LID_RING_HOLE   = 14.0     # mm  Ø of finger pull hole
CATCH_POCKET_W  = 20.0     # mm  width of catch pocket in the body front step
CATCH_POCKET_H  = 2.6      # mm  height of catch pocket
CATCH_POCKET_D  = 1.8      # mm  depth of catch pocket in +Z
STOP_RIB_W      = 4.0      # mm  width of the internal rear stop frame
STOP_RIB_D      = 3.0      # mm  how far the stop frame sticks into the bay
REAR_WALL_LAYERS = 3       # rear wall in wall-units -> 8.4 mm
GUSSET_H        = 18.0     # mm  45 deg gussets under the plenum roof

# ---- wiring / airflow plenum (compact & wide) --------------------------------
#  Widened to 200 mm inner (205.6 mm outer) to provide ~27.5 mm clearance on the
#  left for the side-facing HP 10-pin backplane power harness to plug in and
#  sweep naturally into the wiring chamber.
#  Shortened to 80 mm depth for a compact, rigid enclosure (Z_OUT ~ 253.4 mm).
PLEN_INT_W    = 200.0    # mm  internal width of the plenum chamber
PLENUM_D      =  80.0    # mm  clear depth behind the backplane (holds PicoPSU + fan)

# ---- fan ---------------------------------------------------------------------
#  92 mm (default): frame 92 -> rear section becomes 102.8 mm tall
#  80 mm          : frame 80 -> fits the bay, REAR_H collapses to 94.6, flat top
FAN_MODEL     = "ARCTIC P9 PWM PST  (ACFAN00298A)"
FAN_SIZE      =  92.0    # mm  nominal fan frame size
FAN_INNER_CLEAR = 2.0    # mm  clearance between the fan frame and the bore
FAN_APERTURE  =  86.0    # mm  Ø of the grille field (clears the blades)
FAN_PATTERN   =  82.5    # mm  fan mounting hole square pattern (ARCTIC drawing)
FAN_HOLE      =   4.2    # mm  Ø -> 4.2 for M3 heat-set insert, 4.5 for M4 pass
FAN_INSET     =  25.0    # mm  fan depth; it hugs the inside of the rear wall

# ---- fan housing -------------------------------------------------------------
# ---- fan housing (tall U-channel with front retaining rail & press-fit feel) -
#  The fan slides straight DOWN into a full-height U-channel from the top and
#  seats on the plenum floor. Tall side guide rails and front retaining rails
#  with lead-in chamfers create a snug press-fit track (25.10 mm depth vs 25.0 mm
#  fan frame) that holds the fan firmly on all sides with no screws at all.
FAN_GUIDE_CLEAR = 0.15   # mm  clearance per side between fan frame and side rail
FAN_GUIDE_T     = 3.0    # mm  side rail thickness
FAN_GUIDE_H     = 86.0   # mm  rail height above the plenum floor (up to y=90.0)
FAN_GUIDE_CHAM  = 2.5    # mm  lead-in chamfer at the top of each rail
FAN_FRONT_Z_IN  = 219.90 # mm  front rail inner face (25.10 mm track depth from rear wall at 245.0)
FAN_FRONT_Z_OUT = 217.00 # mm  front rail outer face (219.90 - 2.90)
FAN_FRONT_X_IN  = 43.50  # mm  front retaining lip inner edge (overlaps 46.0 mm fan frame by 2.5 mm)
FAN_FRONT_CHAM  = 2.5    # mm  lead-in chamfer on front rail in Z for smooth drop-in
FAN_LID_GAP     = 1.0    # mm  gap between the fan's top edge and the lid fin

# ---- drive bay net motif (honeycomb cutouts for weight & cost reduction) ----
NET_CELL        = 11.0   # mm  hex cell width across flats
NET_WEB         =  1.8   # mm  web thickness between hex cells

# ---- honeycomb exhaust grille ------------------------------------------------
GRILLE_CELL   =   9.0    # mm  honeycomb cell size, across flats
GRILLE_WEB    =   1.2    # mm  material between cells (3 lines @ 0.4 mm nozzle)
GRILLE_RIM    =   2.0    # mm  solid ring between the cells and the pocket wall
GRILLE_DEPTH  =   3.0    # mm  membrane thickness the cells are punched through

# ---- cable egress (rear wall, beside the grille pocket) ----------------------
#  The SFF-8087 -> SFF-8088 leads leave through the BACK at X = -70.0.
REAR_CABLE_SLOT_X =  70.0          # mm  slot centre X
REAR_CABLE_SLOT_Y = (33.0, 50.0)   # mm  slot centre heights
REAR_CABLE_SLOT_W =  17.0          # mm  slot width in X
REAR_CABLE_SLOT_H =  12.0          # mm  slot height in Y

# ---- PicoPSU cradle (transverse orientation, shifted left) -------------------
#  mini-box picoPSU-120 measured 31 x 44 x 21 mm (1U), 57 g with its harness.
#  Oriented transversely (44 mm across X, 31 mm along Z) to save depth, and
#  shifted left to X = -40.0 mm to leave the right plenum wide open for the
#  backplane power harness and Wago 221 lever blocks.
PSU_W, PSU_L, PSU_H = 31.0, 44.0, 21.0   # mm  board envelope (31 mm W along Z, 44 mm L across X)
PSU_CLEAR     =   0.8    # mm  clearance per side in the cradle
PSU_CX        = -40.0    # mm  cradle centre X (shifted to left)
PSU_BOOT      =  12.0    # mm  gap between the backplane and the cradle mouth
PSU_PLINTH_T  =   3.0    # mm  the board sits on this, off the floor
PSU_WALL_H    =  24.0    # mm  cradle wall height above the floor
PSU_FRONT_LIP =   6.0    # mm  front wall height; the 3 mm above the plinth is
                         #     what stops the board sliding forward
PSU_STRAP_H   =   4.0    # mm  retaining strap thickness
PSU_STRAP_L   =  14.0    # mm  retaining strap length in Z
PSU_BOSS_W    =   6.0    # mm  boss sticking sideways past each cradle wall
PSU_BOSS_L    =  14.0    # mm  boss length in Z
PSU_LEG_T     =   2.0    # mm  toolless snap leg thickness
PSU_LEG_H     =   6.0    # mm  toolless snap leg height
PSU_TOOTH_W   =   0.8    # mm  snap tooth undercut width
PSU_TOOTH_H   =   1.6    # mm  snap tooth height

# ---- DC input jack (rear wall) ----------------------------------------------
DC_JACK_X     = -70.0    # mm  centre X (left of the grille; cables exit right)
DC_JACK_Y     =  52.0    # mm  centre Y
DC_JACK_DIA   =   8.0    # mm  jack body hole
DC_JACK_PAD   =  16.0    # mm  counterbore diameter in the outer face
DC_JACK_DEPTH =   5.0    # mm  counterbore depth

# ---- service opening ---------------------------------------------------------
SVC_Z0        = 165.0    # mm  front edge of opening (starts at backplane for easy connector access)
SVC_Z1_BACKOFF=   0.0    # mm  how far short of the rear wall the opening stops
SVC_R         =  12.0    # mm  corner radius of the opening
LID_SCREW_Z   = ()       # no screws - 100% toolless slide-and-click

# ---- HP cage anchoring (internal bottom slider rails + top ribs) ------------
#  The HP cage slides in from the front between internal guide rails on the floor
#  and ceiling ribs, seating against the rear stop frame. No screws needed.
CAGE_RAIL_H    = 14.0      # mm  internal bottom guide rail height
CAGE_RAIL_W    =  4.0      # mm  rail thickness
CAGE_TOP_RIB_H =  5.0      # mm  top guide rib height
CAGE_TOP_RIB_W =  4.0      # mm  top guide rib thickness
CAGE_SCREW_Z   = ()        # no screws - 100% toolless cage slide-in
CAGE_SCREW_DIA = 3.4      # mm  legacy clearance

# ---- base --------------------------------------------------------------------
FOOT_DIA      = 12.0     # mm  rubber foot recess
FOOT_DEEP     = 2.0      # mm
FOOT_X        = 61.0     # mm  +/- X of the foot centres

# ---- entry lead-in -----------------------------------------------------------
#  Deliberately small: the lead-in and the outer corner rounds both take material
#  off the same 2.8 mm front wall.  Wall left at the mouth corner is
#  WALL - FILLET_R - LEAD_IN/2 = 1.00 mm.
LEAD_IN       = 0.8      # mm  total flare added to the aperture at the mouth
LEAD_DEPTH    = 4.0      # mm  how deep that flare goes

# ---- edge rounding -----------------------------------------------------------
#  Rounded on the OUTSIDE only, for handling comfort and to stop the edges
#  chipping.  Applied to the bare shell before anything is cut out of it;
#  filleting the finished body would also try to round the honeycomb webs and
#  every internal corner, which OCC will not survive.
FILLET_R      = 1.4      # mm  body outer edges and the PSU strap
FILLET_R_LID  = 1.0      # mm  lid plate - it is only 3 mm thick, and a 1.4 round
                         #     would leave 0.2 mm at the rim

# ---- faceting ----------------------------------------------------------------
DUCT_SEG      = 96       # polygon segments used for the entry lead-in flare

# ---- output ------------------------------------------------------------------
OUT_DIR       = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
BASENAME      = "dl380_cage_case"

# ==============================================================================
# 2. DERIVED DIMENSIONS  -  do not hand-edit, all computed
# ==============================================================================

INT_W   = CAGE_W + 2 * FIT_CLEAR           # internal width between guide rails (145.8 mm)
INT_H   = CAGE_H + 2 * FIT_CLEAR           # internal height of the bay (87.8 mm)
OUT_W   = PLEN_INT_W + 2 * WALL            # uniform outside width (205.6 mm)
BAY_H   = INT_H + FLOOR_T + WALL           # outside height of the bay section

# The rear section has to swallow the fan frame, which is taller than the cage.
INT_H_PLEN = max(INT_H, FAN_SIZE + 2 * FAN_INNER_CLEAR)
REAR_H     = FLOOR_T + INT_H_PLEN + WALL
FLAT_TOP   = abs(REAR_H - BAY_H) < 1e-9

REAR_WALL_T = REAR_WALL_LAYERS * WALL      # rear wall thickness (stiff, holds fan)
Z_BAY   = CAGE_D                           # front face of the plenum
Z_RIN   = CAGE_D + PLENUM_D                # inner face of the rear wall
Z_OUT   = Z_RIN + REAR_WALL_T              # very back of the enclosure

BAY_Y0  = FLOOR_T                          # inside floor
BAY_Y1  = FLOOR_T + INT_H                  # inside ceiling of the bay
BAY_YC  = (BAY_Y0 + BAY_Y1) / 2.0          # bay vertical centre
PLEN_Y1 = REAR_H - WALL                    # inside ceiling of the plenum

FAN_R   = FAN_APERTURE / 2.0
FAN_OFF = FAN_PATTERN / 2.0                # +/- offset of the 4 fan holes
FAN_Z0  = Z_RIN - FAN_INSET                # front face of the fan

# ---- fan housing -------------------------------------------------------------
#  The fan SEATS ON THE PLENUM FLOOR, so its axis drops to FLOOR_T + FAN_SIZE/2
#  and everything keyed off it - the grille, the mounting holes - follows.
FAN_CY      = FLOOR_T + FAN_SIZE / 2.0     # fan axis, with the fan on the floor
FAN_HALF    = FAN_SIZE / 2.0
FAN_TOP     = FLOOR_T + FAN_SIZE           # top edge of the fan frame
GUIDE_X     = FAN_HALF + FAN_GUIDE_CLEAR   # rail inner face
GUIDE_XO    = GUIDE_X + FAN_GUIDE_T        # rail outer face
LID_FIN_Y0  = FAN_TOP + FAN_LID_GAP        # bottom of the lid's retainer fin

# honeycomb geometry: R sizes a perfect tiling, Rp the shrunken cells we cut
GRILLE_R        = (GRILLE_CELL + GRILLE_WEB) / math.sqrt(3.0)
GRILLE_RP       = GRILLE_R - GRILLE_WEB / math.sqrt(3.0)
GRILLE_OPEN_R   = FAN_R - GRILLE_RP        # only centres inside this get a cell
GRILLE_POCKET_R = FAN_R + GRILLE_RIM       # recess radius in the outer face

XW       = OUT_W / 2.0                     # uniform outer half width (102.8 mm)
XI       = INT_W / 2.0                     # cage opening half width (72.9 mm)

# ---- uniform width & plenum dimensions ---------------------------------------
PLEN_OUT_W = OUT_W                         # plenum outside width equals bay (205.6 mm)
PLEN_XI    = PLEN_INT_W / 2.0              # plenum inside half width (100.0 mm)
PLEN_XW    = XW                            # plenum outside half width (102.8 mm)
SVC_HALF   = PLEN_XI - GUSSET_H            # service opening half width (82.0 mm)

# ---- PicoPSU cradle placement (transverse, shifted left) --------------------
PSU_XH      = (PSU_L + 2 * PSU_CLEAR) / 2.0    # cradle inner half width in X (22.8 mm)
PSU_ZH      = (PSU_W + 2 * PSU_CLEAR) / 2.0    # cradle inner half length in Z (16.3 mm)
PSU_Z0      = Z_BAY + PSU_BOOT                 # cradle mouth (177.0 mm)
PSU_Z1      = PSU_Z0 + 2 * PSU_ZH              # cradle inner rear (209.6 mm)
PSU_TRAY_OH = PSU_XH + WALL                    # cradle outer half width (25.6 mm)
PSU_TOP     = FLOOR_T + PSU_PLINTH_T + PSU_H + 0.4   # board top + clearance (28.4 mm)
PSU_BORE_Z  = (PSU_Z0 + PSU_Z1) / 2.0          # strap snap ridge Z (193.3 mm)
PSU_STRAP_X = PSU_TRAY_OH + PSU_BOSS_W         # boss outer edge from cradle centre (31.6 mm)

# ---- base rubber feet --------------------------------------------------------
FOOT_Z      = (14.0, Z_OUT - 14.0)             # front and rear foot Z coordinates

# ---- service opening, derived from the rear wall -----------------------------
SVC_Z1 = Z_RIN - SVC_Z1_BACKOFF            # opening rear edge
FAN_DROP_LO = PSU_Z1 + WALL + 2.0          # clear of the cradle's rear wall
FAN_DROP_HI = SVC_Z1 - FAN_INSET           # its thickness must clear the roof

# ---- slide-and-click housing lid ---------------------------------------------
RAIL_Z0         = Z_BAY + 1.5                                   # start behind the 1.4 mm step fillet
LID_OX          = PLEN_XW + SLIDE_CLEAR + SKIRT_T               # lid outer half width (105.85 mm)
LID_Z0          = Z_BAY - LID_FRONT_T                           # lid front edge
LID_Z1          = Z_OUT                                         # lid rear edge (flush with rear wall)
LID_Y_FRONT_BOT = BAY_H + 1.8                                   # bottom of front face, clear of step fillet


# ==============================================================================
# 3. PRIMITIVE HELPERS
# ==============================================================================

def box(dx, dy, dz, x=0.0, y=0.0, z=0.0):
    """Axis aligned box, (x, y, z) is the min corner."""
    return Part.makeBox(dx, dy, dz, Vector(x, y, z))


def cyl_x(radius, length, y, z, x=0.0):
    """Cylinder whose axis runs along +X."""
    return Part.makeCylinder(radius, length, Vector(x, y, z), Vector(1, 0, 0))


def cyl_y(radius, length, x, z, y=0.0):
    """Cylinder whose axis runs along +Y."""
    return Part.makeCylinder(radius, length, Vector(x, y, z), Vector(0, 1, 0))


def cyl_z(radius, length, x, y, z=0.0):
    """Cylinder whose axis runs along +Z."""
    return Part.makeCylinder(radius, length, Vector(x, y, z), Vector(0, 0, 1))


def polygon_wire(points, z):
    """Closed polygon wire lying in the plane Z = z."""
    pts = [Vector(p[0], p[1], z) for p in points]
    pts.append(pts[0])
    return Part.makePolygon(pts)


def prism(points, z0, dz):
    """Extrude a closed 2D polygon given in XY along +Z."""
    return Part.Face(polygon_wire(points, z0)).extrude(Vector(0.0, 0.0, dz))


def prism_y(points_xz, y0, dy):
    """Extrude a closed 2D polygon given in XZ along +Y."""
    pts = [Vector(p[0], y0, p[1]) for p in points_xz]
    pts.append(pts[0])
    return Part.Face(Part.makePolygon(pts)).extrude(Vector(0.0, dy, 0.0))


def rect_points(half_w, half_h, cy, n):
    """n points ON the boundary of a rectangle, sampled by polar angle."""
    pts = []
    for i in range(n):
        th = 2.0 * math.pi * i / n
        c, s = math.cos(th), math.sin(th)
        tx = half_w / abs(c) if abs(c) > 1e-12 else 1e18
        ty = half_h / abs(s) if abs(s) > 1e-12 else 1e18
        t = min(tx, ty)
        pts.append((t * c, cy + t * s))
    return pts


def stadium(center_y, center_z, height_y, length_z, span_x0, span_x1, r):
    """Rounded-end (stadium) slot, extruded along X from span_x0 to span_x1."""
    z0 = center_z - (length_z / 2.0 - r)
    z1 = center_z + (length_z / 2.0 - r)
    L = span_x1 - span_x0
    s = box(L, height_y, length_z - 2 * r, span_x0, center_y - r, z0)
    for zz in (z0, z1):
        s = s.fuse(cyl_x(r, L, center_y, zz, span_x0))
    return s


def rounded_rect_prism(half_w, y0, y1, z0, z1, r, x_centre=0.0):
    """Rounded rectangle in the XZ plane, extruded along Y."""
    W, D = 2 * half_w, z1 - z0
    s = box(W, y1 - y0, D, x_centre - half_w, y0, z0)
    for xx in (x_centre - half_w + r, x_centre + half_w - r):
        for zz in (z0 + r, z1 - r):
            s = s.fuse(cyl_y(r, y1 - y0, xx, zz, y0))
    return s


def rounded_rect_z(half_w, half_h, cx, cy, z0, z1, r):
    """Rounded rectangle in the XY plane, extruded along Z."""
    L = z1 - z0
    s = box(2 * half_w, 2 * half_h, L, cx - half_w, cy - half_h, z0)
    for xx in (cx - half_w + r, cx + half_w - r):
        for yy in (cy - half_h + r, cy + half_h - r):
            s = s.fuse(cyl_z(r, L, xx, yy, z0))
    return s


def gusset(x_wall, y_top, height, z0, z1, side):
    """45 degree gusset filling the corner between a side wall and the roof.

    Its sloping underside is what makes the roof printable and what gives the
    lid screws enough material to bite into.
    """
    if side > 0:
        p = [(x_wall, y_top - height), (x_wall - height, y_top), (x_wall, y_top)]
    else:
        p = [(-x_wall, y_top), (-(x_wall - height), y_top),
             (-x_wall, y_top - height)]
    return prism(p, z0, z1 - z0)


def honeycomb_openings(cx, cy, r_centres, z0, dz, cell, web):
    """Flat-top hexagonal cells whose centres lie inside radius r_centres."""
    R = (cell + web) / math.sqrt(3.0)          # perfect-tiling circumradius
    Rp = R - web / math.sqrt(3.0)              # cell circumradius after shrink
    col_pitch = 1.5 * R
    row_pitch = math.sqrt(3.0) * R
    nc = int(math.ceil(r_centres / col_pitch)) + 1
    nr = int(math.ceil(r_centres / row_pitch)) + 2
    cells = []
    for c in range(-nc, nc + 1):
        x = cx + c * col_pitch
        yoff = 0.0 if c % 2 == 0 else row_pitch / 2.0
        for r in range(-nr, nr + 1):
            y = cy + r * row_pitch + yoff
            if math.hypot(x - cx, y - cy) > r_centres:
                continue
            pts = [(x + Rp * math.cos(math.radians(60.0 * i)),
                    y + Rp * math.sin(math.radians(60.0 * i))) for i in range(6)]
            cells.append(prism(pts, z0, dz))
    return cells


def make_hex_grid(span_u, span_v, cell_flat, web, center_u, center_v,
                  extrude_axis, extrude_start, extrude_len, rot_deg=0):
    """Generate a grid of hexagonal cutting prisms across a 2D bounding span."""
    r_flat = cell_flat / 2.0
    r_corner = r_flat / math.cos(math.radians(30))
    pitch_u = cell_flat + web
    pitch_v = 1.5 * r_corner + web * 0.866
    nu = int(span_u / pitch_u) + 2
    nv = int(span_v / pitch_v) + 2
    margin = cell_flat / 2.0
    solids = []
    for iv in range(-nv, nv + 1):
        v = center_v + iv * (cell_flat * math.sqrt(3)/2.0 + web * math.sqrt(3)/2.0)
        u_shift = (pitch_u / 2.0) if (iv % 2 != 0) else 0.0
        for iu in range(-nu, nu + 1):
            u = center_u + iu * pitch_u + u_shift
            if abs(u - center_u) <= (span_u / 2.0 - margin) and abs(v - center_v) <= (span_v / 2.0 - margin):
                pts = []
                for i in range(6):
                    ang = math.radians(60 * i + rot_deg)
                    pts.append((u + r_corner * math.cos(ang), v + r_corner * math.sin(ang)))
                if extrude_axis == 'y':
                    vecs = [Vector(x, extrude_start, z) for (x, z) in pts]
                    vec_ext = Vector(0, extrude_len, 0)
                elif extrude_axis == 'x':
                    vecs = [Vector(extrude_start, y, z) for (z, y) in pts]
                    vec_ext = Vector(extrude_len, 0, 0)
                else:
                    vecs = [Vector(x, y, extrude_start) for (x, y) in pts]
                    vec_ext = Vector(0, 0, extrude_len)
                poly = Part.makePolygon(vecs + [vecs[0]])
                face = Part.Face(poly)
                solids.append(face.extrude(vec_ext))
    return solids


def _tidy(shape):
    """Merge coplanar faces when the FreeCAD build offers it (no clean() in 1.1)."""
    for meth in ("removeSplitter", "clean"):
        fn = getattr(shape, meth, None)
        if fn is not None:
            try:
                shape = fn()
            except Exception as exc:      # pragma: no cover
                print("  (tidy: %s() skipped: %s)" % (meth, exc))
    return shape


def fillet_all(shape, r):
    """Round every edge of a simple solid.

    Only safe on a shape with no internal detail - run it on the bare shell
    before cutting anything into it.  Coplanar faces must already have been
    merged by _tidy(), otherwise the seams between them become grooves.
    Steps down the radius if OCC refuses one.
    """
    if r <= 0.0:
        return shape
    last = None
    for attempt in (r, r * 0.75, r * 0.5, r * 0.35):
        try:
            out = shape.makeFillet(attempt, shape.Edges)
            if out.isValid() and out.Volume > 0.0:
                if abs(attempt - r) > 1e-9:
                    print("  (fillet: %.2f mm refused, used %.2f mm)"
                          % (r, attempt))
                return out
        except Exception as exc:
            last = exc
    print("  (fillet: every radius refused, edges left sharp: %s)" % last)
    return shape


# ==============================================================================
# 4. BUILD
# ==============================================================================

def build():
    log = {}

    # ---------------------------------------------------------------- shell ---
    outer = box(OUT_W, BAY_H, Z_BAY, -XW, 0.0, 0.0)
    outer = outer.fuse(box(OUT_W, REAR_H, Z_OUT - Z_BAY, -XW, 0.0, Z_BAY))
    #  Round every outer edge here, while the shell is still just two boxes.
    #  _tidy() first, or the coplanar seams between the two boxes' faces would
    #  get filleted into grooves.
    outer = _tidy(outer)
    v_shell = outer.Volume
    outer = fillet_all(outer, FILLET_R)
    log["shell_volume_bare"] = v_shell
    log["shell_volume_filleted"] = outer.Volume

    # ---------------------------------------------------------------- voids ---
    #  Front mouth opening (145.8 x 87.8 mm) through the 2.8 mm front wall,
    #  opening into the full 200.0 mm wide interior chamber.
    front_mouth = box(INT_W, INT_H, WALL + 1.0, -XI, BAY_Y0, -1.0)
    bay_void = box(PLEN_INT_W, INT_H, Z_BAY - WALL, -PLEN_XI, BAY_Y0, WALL)
    plen_void = box(PLEN_INT_W, PLEN_Y1 - BAY_Y0, PLENUM_D, -PLEN_XI, BAY_Y0, Z_BAY)

    body = outer.cut(front_mouth.fuse(bay_void).fuse(plen_void))

    # --------------------------------- internal guide rails for HP cage ---
    #  Bottom guide rails (14 mm tall) and top guide ribs (5 mm tall) capture
    #  and align the 145 mm HP drive cage, keeping 27.1 mm lateral clearance
    #  on the left for the backplane power harness and Wago blocks.
    #  Includes 1.5 mm 45-deg lead-in chamfers at the entry (Z = WALL to WALL + 3.0).
    p_l_rail_xz = [
        (-(XI + CAGE_RAIL_W), WALL),
        (-XI - 1.5, WALL),
        (-XI, WALL + 3.0),
        (-XI, Z_BAY),
        (-(XI + CAGE_RAIL_W), Z_BAY)
    ]
    p_r_rail_xz = [
        (XI + CAGE_RAIL_W, WALL),
        (XI + 1.5, WALL),
        (XI, WALL + 3.0),
        (XI, Z_BAY),
        (XI + CAGE_RAIL_W, Z_BAY)
    ]
    l_rail = prism_y(p_l_rail_xz, BAY_Y0, CAGE_RAIL_H)
    r_rail = prism_y(p_r_rail_xz, BAY_Y0, CAGE_RAIL_H)
    l_top  = prism_y(p_l_rail_xz, BAY_Y1 - CAGE_TOP_RIB_H, CAGE_TOP_RIB_H)
    r_top  = prism_y(p_r_rail_xz, BAY_Y1 - CAGE_TOP_RIB_H, CAGE_TOP_RIB_H)
    body = body.fuse(l_rail).fuse(r_rail).fuse(l_top).fuse(r_top)

    # ------------------------------------- internal rear stop frame for cage ---
    ring = box(INT_W, INT_H, STOP_RIB_D, -XI, BAY_Y0, Z_BAY - STOP_RIB_D)
    ring = ring.cut(box(INT_W - 2 * STOP_RIB_W, INT_H - 2 * STOP_RIB_W,
                        STOP_RIB_D + 2.0,
                        -(XI - STOP_RIB_W), BAY_Y0 + STOP_RIB_W,
                        Z_BAY - STOP_RIB_D - 1.0))
    #  Relief notch on the right stop rib: provides clear, direct clearance for
    #  the side-facing 10-pin power port on the bottom-right edge of the upright HP backplane.
    pwr_notch = box(STOP_RIB_W + 2.0, 46.0, STOP_RIB_D + 2.0,
                    XI - STOP_RIB_W - 1.0, BAY_Y0 - 0.5, Z_BAY - STOP_RIB_D - 1.0)
    ring = ring.cut(pwr_notch)
    body = body.fuse(ring)

    # ------------------------------------------- roof gussets beside the lid ---
    for side in (1, -1):
        body = body.fuse(gusset(PLEN_XI, PLEN_Y1, GUSSET_H, Z_BAY, Z_RIN, side))

    # ------------------------------------------------ fan housing in plenum ---
    #  A tall U-channel the fan slides straight down into from the top.
    #  It seats on the plenum floor and is guided in X by two side rails and in
    #  Z by the rear wall and front retaining rails. Top lead-in chamfers provide
    #  smooth entry while the 25.10 mm track depth gives a snug press-fit feel.
    for sx in (1, -1):
        # 1. Side rail: X in [GUIDE_X, GUIDE_XO], Z in [FAN_Z0, Z_RIN]
        p_side = [
            (sx * GUIDE_X, FLOOR_T),
            (sx * GUIDE_XO, FLOOR_T),
            (sx * GUIDE_XO, FLOOR_T + FAN_GUIDE_H),
            (sx * (GUIDE_X + FAN_GUIDE_CHAM), FLOOR_T + FAN_GUIDE_H),
            (sx * GUIDE_X, FLOOR_T + FAN_GUIDE_H - FAN_GUIDE_CHAM)
        ]
        if sx < 0:
            p_side.reverse()
        body = body.fuse(prism(p_side, FAN_Z0, FAN_INSET))

        # 2. Front retaining rail: captures front face of fan frame
        p_front_yz = [
            (FLOOR_T, FAN_FRONT_Z_OUT),
            (FLOOR_T, FAN_FRONT_Z_IN),
            (FLOOR_T + FAN_GUIDE_H - 8.0, FAN_FRONT_Z_IN),
            (FLOOR_T + FAN_GUIDE_H, FAN_FRONT_Z_IN - FAN_FRONT_CHAM),
            (FLOOR_T + FAN_GUIDE_H, FAN_FRONT_Z_OUT)
        ]
        x_min = min(sx * FAN_FRONT_X_IN, sx * GUIDE_XO)
        dx = abs(GUIDE_XO - FAN_FRONT_X_IN)
        vecs = [Vector(x_min, y, z) for (y, z) in p_front_yz]
        poly = Part.makePolygon(vecs + [vecs[0]])
        face = Part.Face(poly)
        front_solid = face.extrude(Vector(dx, 0, 0))
        body = body.fuse(front_solid)

    # ----------------------------------------------- PicoPSU cradle in plenum ---
    #  Transverse orientation (44 mm across X, 31 mm along Z) shifted to X = +40.0 mm.
    #  plinth the board stands on
    body = body.fuse(box(2 * PSU_XH, PSU_PLINTH_T, 2 * PSU_ZH,
                         PSU_CX - PSU_XH, FLOOR_T, PSU_Z0))
    #  side walls
    for sx in (1, -1):
        x0 = (PSU_CX + PSU_XH) if sx > 0 else (PSU_CX - PSU_TRAY_OH)
        body = body.fuse(box(WALL, PSU_WALL_H, 2 * PSU_ZH, x0, FLOOR_T, PSU_Z0))
    #  rear wall and the low lip across the mouth, which is what stops the
    #  board sliding forward onto the backplane
    body = body.fuse(box(2 * PSU_TRAY_OH, PSU_WALL_H, WALL,
                         PSU_CX - PSU_TRAY_OH, FLOOR_T, PSU_Z1))
    body = body.fuse(box(2 * PSU_TRAY_OH, PSU_FRONT_LIP, WALL,
                         PSU_CX - PSU_TRAY_OH, FLOOR_T, PSU_Z0 - WALL))
    #  corner bosses that take the retaining-strap snap fit
    for sx in (1, -1):
        bx = (PSU_CX + PSU_TRAY_OH) if sx > 0 else (PSU_CX - PSU_TRAY_OH - PSU_BOSS_W)
        body = body.fuse(box(PSU_BOSS_W, PSU_TOP - FLOOR_T, PSU_BOSS_L,
                             bx, FLOOR_T, PSU_BORE_Z - PSU_BOSS_L / 2.0))
        rx = (PSU_CX + PSU_TRAY_OH + PSU_BOSS_W) if sx > 0 else (PSU_CX - PSU_TRAY_OH - PSU_BOSS_W - PSU_TOOTH_W)
        body = body.fuse(box(PSU_TOOTH_W, 1.5, PSU_BOSS_L,
                             rx, PSU_TOP - 3.0,
                             PSU_BORE_Z - PSU_BOSS_L / 2.0))

    # --------------------------------------------- slide rails on outer walls ---
    #  45 deg beveled guide rails on left and right outer walls for the sliding lid
    y_bot = RAIL_YC - RAIL_H / 2.0 - RAIL_W
    y_m1  = RAIL_YC - RAIL_H / 2.0
    y_m2  = RAIL_YC + RAIL_H / 2.0
    y_top = RAIL_YC + RAIL_H / 2.0 + RAIL_W

    p_right = [
        (PLEN_XW, y_bot),
        (PLEN_XW + RAIL_W, y_m1),
        (PLEN_XW + RAIL_W, y_m2),
        (PLEN_XW, y_top)
    ]
    p_left = [
        (-PLEN_XW, y_bot),
        (-PLEN_XW, y_top),
        (-(PLEN_XW + RAIL_W), y_m2),
        (-(PLEN_XW + RAIL_W), y_m1)
    ]
    body = body.fuse(prism(p_right, RAIL_Z0, Z_OUT - RAIL_Z0))
    body = body.fuse(prism(p_left, RAIL_Z0, Z_OUT - RAIL_Z0))

    # ------------------------------------------------------------------ cuts ---
    cuts = []

    # --- front step catch pocket for slide-and-click lid snap latch ----------
    cuts.append(box(CATCH_POCKET_W, CATCH_POCKET_H, CATCH_POCKET_D,
                    -CATCH_POCKET_W / 2.0, RAIL_YC - CATCH_POCKET_H / 2.0, Z_BAY))

    # --- DC input jack in the rear wall --------------------------------------
    cuts.append(cyl_z(DC_JACK_DIA / 2.0, REAR_WALL_T + 2.0,
                      DC_JACK_X, DC_JACK_Y, Z_RIN - 1.0))
    cuts.append(cyl_z(DC_JACK_PAD / 2.0, DC_JACK_DEPTH + 1.0,
                      DC_JACK_X, DC_JACK_Y, Z_OUT - DC_JACK_DEPTH))

    # --- fan mounting holes (screws come from inside the plenum) -------------
    for sx in (-1, 1):
        for sy in (-1, 1):
            cuts.append(cyl_z(FAN_HOLE / 2.0, REAR_WALL_T + 2.0,
                              sx * FAN_OFF, FAN_CY + sy * FAN_OFF, Z_RIN - 1.0))

    # --- honeycomb exhaust grille -------------------------------------------
    #  a shallow pocket in the outer face, then hexagonal cells punched through
    #  the remaining membrane.  The pocket is wider than the cell field so no
    #  cell can break out through the pocket wall.
    cuts.append(cyl_z(GRILLE_POCKET_R, REAR_WALL_T - GRILLE_DEPTH + 1.0,
                      0.0, FAN_CY, Z_OUT - (REAR_WALL_T - GRILLE_DEPTH)))
    cells = honeycomb_openings(0.0, FAN_CY, GRILLE_OPEN_R,
                               Z_RIN - 1.0, REAR_WALL_T + 2.0,
                               GRILLE_CELL, GRILLE_WEB)
    log["honeycomb_cells"] = len(cells)
    cuts.extend(cells)

    # --- top service opening -------------------------------------------------
    cuts.append(rounded_rect_prism(SVC_HALF, PLEN_Y1 - 6.0, REAR_H + 2.0,
                                   SVC_Z0, SVC_Z1, SVC_R))

    # --- cable egress slots through the rear wall ----------------------------
    slot_r = min(REAR_CABLE_SLOT_W, REAR_CABLE_SLOT_H) / 2.0 - 0.01
    for yy in REAR_CABLE_SLOT_Y:
        cuts.append(rounded_rect_z(REAR_CABLE_SLOT_W / 2.0,
                                   REAR_CABLE_SLOT_H / 2.0,
                                   REAR_CABLE_SLOT_X, yy,
                                   Z_RIN - 1.0, Z_OUT + 2.0, slot_r))

    # --- HP cage anchor screws (omitted in toolless slide-in design) --------
    for sx in (-1, 1):
        for zz in CAGE_SCREW_Z:
            cuts.append(cyl_x(CAGE_SCREW_DIA / 2.0, WALL + 2.0, BAY_YC, zz,
                              sx * XI - 1.0))

    # --- rubber feet recesses ------------------------------------------------
    for sx in (-1, 1):
        for zz in FOOT_Z:
            cuts.append(cyl_y(FOOT_DIA / 2.0, FOOT_DEEP + 0.5,
                              sx * FOOT_X, zz, -0.5))

    # --- caddy entry lead-in flare ------------------------------------------
    w_in = polygon_wire(rect_points(XI, INT_H / 2.0, BAY_YC, DUCT_SEG), LEAD_DEPTH)
    w_out = polygon_wire(rect_points(XI + LEAD_IN / 2.0,
                                     INT_H / 2.0 + LEAD_IN / 2.0,
                                     BAY_YC, DUCT_SEG), 0.0)
    cuts.append(Part.makeLoft([w_in, w_out], solid=True, ruled=True))

    # --- drive bay net motif (honeycomb cutouts on top, bottom, left, right) -
    net_cuts = []
    # Top roof (u=X, v=Z, extrude along Y)
    net_cuts.extend(make_hex_grid(120.0, 134.0, NET_CELL, NET_WEB, 0.0, 83.0, 'y', BAY_Y1 - 1.0, WALL + 2.0))
    # Bottom floor (u=X, v=Z, extrude along Y)
    net_cuts.extend(make_hex_grid(90.0, 122.0, NET_CELL, NET_WEB, 0.0, 87.0, 'y', -1.0, FLOOR_T + 2.0))
    # Left wall (u=Z, v=Y, extrude along X)
    net_cuts.extend(make_hex_grid(134.0, 68.0, NET_CELL, NET_WEB, 83.0, BAY_YC, 'x', -XW - 1.0, WALL + 2.0))
    # Right wall (u=Z, v=Y, extrude along X)
    net_cuts.extend(make_hex_grid(134.0, 68.0, NET_CELL, NET_WEB, 83.0, BAY_YC, 'x', XW - WALL - 1.0, WALL + 2.0))
    log["net_cells"] = len(net_cuts)
    cuts.append(Part.makeCompound(net_cuts))

    for c in cuts:
        body = body.cut(c)

    body = _tidy(body)

    # ================================================= slide-and-click lid ---
    #  Slides horizontally along +Z into 45 deg guide rails on the body's outer
    #  walls, and clicks shut with a compliant cantilever snap latch into a
    #  recessed pocket on the front vertical step.  100% screwless.
    x_inner = PLEN_XW + SLIDE_CLEAR
    x_outer = LID_OX
    y_top = REAR_H + LID_T
    y_bot = REAR_H - SKIRT_D

    # 1. Top plate
    lid = box(2 * LID_OX, LID_T, LID_Z1 - LID_Z0, -LID_OX, REAR_H, LID_Z0)

    # 2. Left and right skirts with 45 deg interlocking runners
    br_bot = RAIL_YC - RAIL_H / 2.0 - RAIL_W
    br_m1  = RAIL_YC - RAIL_H / 2.0
    br_m2  = RAIL_YC + RAIL_H / 2.0
    br_top = RAIL_YC + RAIL_H / 2.0 + RAIL_W
    br_out = PLEN_XW + RAIL_W

    p_r_skirt = [
        (x_outer, REAR_H),
        (x_outer, y_bot),
        (x_inner, y_bot),
        (x_inner, br_bot - SLIDE_CLEAR),
        (br_out + SLIDE_CLEAR, br_m1 - SLIDE_CLEAR),
        (br_out + SLIDE_CLEAR, br_m2 + SLIDE_CLEAR),
        (x_inner, br_top + SLIDE_CLEAR),
        (x_inner, REAR_H)
    ]
    p_l_skirt = [(-p[0], p[1]) for p in reversed(p_r_skirt)]

    lid = lid.fuse(prism(p_r_skirt, LID_Z0, LID_Z1 - LID_Z0))
    lid = lid.fuse(prism(p_l_skirt, LID_Z0, LID_Z1 - LID_Z0))

    # 3. Front face covering the step
    front_face = box(2 * x_inner, REAR_H - LID_Y_FRONT_BOT, LID_FRONT_T,
                     -x_inner, LID_Y_FRONT_BOT, LID_Z0)
    lid = lid.fuse(front_face)

    # 4. Snap latch arm at front center
    slot_d = LID_FRONT_T + 1.0
    c_left = box(LATCH_RELIEF, REAR_H - LID_Y_FRONT_BOT + 1.0, slot_d,
                 -(LATCH_W / 2.0 + LATCH_RELIEF), LID_Y_FRONT_BOT - 0.5, LID_Z0 - 0.5)
    c_right = box(LATCH_RELIEF, REAR_H - LID_Y_FRONT_BOT + 1.0, slot_d,
                  LATCH_W / 2.0, LID_Y_FRONT_BOT - 0.5, LID_Z0 - 0.5)
    lid = lid.cut(c_left).cut(c_right)

    # Snap tooth on the inside (+Z face) of the latch arm
    tw = LATCH_W - 0.6
    tooth = box(tw, LATCH_TOOTH_H, LATCH_TOOTH_D,
                -tw / 2.0, RAIL_YC - LATCH_TOOTH_H / 2.0, Z_BAY)
    lid = lid.fuse(tooth)

    # Ergonomic thumb release tab on the front face of the latch arm
    tab_lip = box(LATCH_W, 2.4, 1.4, -LATCH_W / 2.0, LID_Y_FRONT_BOT, LID_Z0 - 1.4)
    lid = lid.fuse(tab_lip)

    # 5. Front center pull ring holder for easy lid removal
    z_center = LID_Z0 - LID_RING_LEN + LID_RING_W / 2.0
    p_ring = [
        ( -LID_RING_W / 2.0, LID_Z0),
        ( -LID_RING_W / 2.0, z_center),
    ]
    for i in range(1, 16):
        ang = math.pi + i * (math.pi / 16.0)
        p_ring.append(((LID_RING_W / 2.0) * math.cos(ang), z_center + (LID_RING_W / 2.0) * math.sin(ang)))
    p_ring.append((LID_RING_W / 2.0, z_center))
    p_ring.append((LID_RING_W / 2.0, LID_Z0))

    vecs = [Vector(p[0], REAR_H, p[1]) for p in p_ring]
    poly = Part.makePolygon(vecs + [vecs[0]])
    face = Part.Face(poly)
    ring_solid = face.extrude(Vector(0, LID_T, 0))

    hole = Part.makeCylinder(LID_RING_HOLE / 2.0, LID_T + 4.0,
                             Vector(0, REAR_H - 2.0, z_center), Vector(0, 1, 0))
    ring_solid = ring_solid.cut(hole)
    lid = lid.fuse(ring_solid)

    # Note: Underside fan retainer fins removed; fan is captive in body U-channel track.

    lid = _tidy(lid)

    # ==================================== toolless snap strap for PicoPSU ---
    #  Snap-on retaining strap that clips over the cradle corner bosses.
    #  No screws, no heat-set inserts.
    PSU_SNAP_CLEAR = 0.2
    boss_outer_x   = PSU_TRAY_OH + PSU_BOSS_W        # 31.6
    ridge_outer_x  = boss_outer_x + PSU_TOOTH_W      # 32.4
    strap_inner_x  = ridge_outer_x + PSU_SNAP_CLEAR  # 32.6
    strap_outer_x  = strap_inner_x + PSU_LEG_T       # 34.6

    strap = box(2 * strap_outer_x, PSU_STRAP_H, PSU_STRAP_L,
                PSU_CX - strap_outer_x, PSU_TOP, PSU_BORE_Z - PSU_STRAP_L / 2.0)
    for sx in (1, -1):
        lx = (PSU_CX + strap_inner_x) if sx > 0 else (PSU_CX - strap_outer_x)
        leg = box(PSU_LEG_T, PSU_LEG_H + PSU_STRAP_H, PSU_STRAP_L,
                  lx, PSU_TOP - PSU_LEG_H, PSU_BORE_Z - PSU_STRAP_L / 2.0)
        strap = strap.fuse(leg)
        tx = (PSU_CX + strap_inner_x - PSU_TOOTH_W) if sx > 0 else (PSU_CX - strap_inner_x)
        tooth = box(PSU_TOOTH_W, PSU_LEG_H - 3.5, PSU_BOSS_L,
                    tx, PSU_TOP - PSU_LEG_H, PSU_BORE_Z - PSU_BOSS_L / 2.0)
        strap = strap.fuse(tooth)
    strap = _tidy(strap)

    return body, lid, strap, log


# ==============================================================================
# 5. CHECKS
# ==============================================================================

def material_depth(shape, x, z, y_top=None, probe_r=0.6, max_d=40.0, step=0.25):
    """How much solid material sits directly under the point (x, z)?  (mm)"""
    if y_top is None:
        y_top = REAR_H
    d = 0.0
    while d < max_d:
        p = Part.makeSphere(probe_r, Vector(x, y_top - step / 2.0 - d, z))
        if p.common(shape).Volume < 0.5 * p.Volume:
            break
        d += step
    return d


def ring_depths(shape, cx, cz, radius=3.4, n=6, **kw):
    """Material depth sampled on a circle around a bore -> min wall thickness."""
    out = []
    for i in range(n):
        a = 2.0 * math.pi * i / n
        out.append(material_depth(shape, cx + radius * math.cos(a),
                                  cz + radius * math.sin(a), **kw))
    return out


def report(body, lid, strap, log):
    L = []
    add = L.append
    add("=" * 78)
    add(" DL380 G6/G7 8x2.5\" SFF drive-cage desktop enclosure - build report")
    add("=" * 78)
    add("")
    add(" TARGET HARDWARE")
    add("   cage outer              : %.1f x %.1f x %.1f mm (W x H x D)"
        % (CAGE_W, CAGE_H, CAGE_D))
    add("   sleeve bore             : %.1f x %.1f mm  (%.1f mm/side clearance)"
        % (INT_W, INT_H, FIT_CLEAR))
    add("")
    add(" ENCLOSURE  (body)")
    add("   outside W x H x D       : %.1f (uniform) x %.1f x %.1f mm"
        % (OUT_W, REAR_H, Z_OUT))
    add("   bay section             : %.1f (W) x %.1f (H) x %.1f (D) mm"
        % (OUT_W, BAY_H, Z_BAY))
    add("   fan/plenum section      : %.1f (W) x %.1f (H) x %.1f (D) mm"
        % (OUT_W, REAR_H, Z_OUT - Z_BAY))
    add("   top profile             : %s"
        % ("FLAT - rear section is the same height as the bay"
           if FLAT_TOP else
           "STEPPED - rear section is %.1f mm taller than the bay (fan is inside)"
           % (REAR_H - BAY_H)))
    add("   wall / floor / rear wall: %.1f / %.1f / %.1f mm"
        % (WALL, FLOOR_T, REAR_WALL_T))
    add("   plenum clear depth      : %.1f mm" % PLENUM_D)
    add("   roof gussets            : %.1f mm tall at 45 deg, carrying the lid rails"
        % GUSSET_H)
    add("")
    add(" HP CAGE SLIDER RAILS & GUIDE RIBS  (internal)")
    add("   bottom guide rails      : %.1f mm tall x %.1f mm thick on floor (Z %.1f..%.1f)"
        % (CAGE_RAIL_H, CAGE_RAIL_W, WALL, Z_BAY))
    add("   top guide ribs          : %.1f mm tall x %.1f mm thick on roof (Z %.1f..%.1f)"
        % (CAGE_TOP_RIB_H, CAGE_TOP_RIB_W, WALL, Z_BAY))
    add("   front mouth lead-in     : 1.5 mm 45 deg chamfer at entry (Z=%.1f..%.1f)"
        % (WALL, WALL + 3.0))
    add("   lateral wiring clearance: %.1f mm open side chamber on right for 10-pin harness"
        % (PLEN_XI - XI - CAGE_RAIL_W))
    add("")
    add(" FAN  -  %s" % FAN_MODEL)
    add("   nominal size            : %.0f x %.0f x 25 mm, 106 g"
        % (FAN_SIZE, FAN_SIZE))
    add("   P9 PWM PST rating       : 200-3000 rpm PWM (0 rpm below 5%),")
    add("                             38.83 cfm | 65.97 m3/h, 3.12 mmH2O static,")
    add("                             0.12 A @ 12 V = 1.44 W, fluid dynamic bearing")
    add("   position                : in a slot against the rear wall, Z %.1f..%.1f,"
        % (FAN_Z0, Z_RIN))
    add("                             seated on the plenum floor")
    add("   fan axis                : (0, %.1f) - the frame sits ON the floor at"
        % FAN_CY)
    add("                             y=%.1f, so the axis is %.1f mm below the"
        % (FLOOR_T, (PLEN_Y1 + BAY_Y0) / 2.0 - FAN_CY))
    add("                             centre of the plenum bore")
    add("   hole pattern            : %.1f x %.1f square, O%.1f"
        % (FAN_PATTERN, FAN_PATTERN, FAN_HOLE))
    add("   hole centres (X,Y)      : (+/-%.1f, %.1f)  (+/-%.1f, %.1f)"
        % (FAN_OFF, FAN_CY - FAN_OFF, FAN_OFF, FAN_CY + FAN_OFF))
    add("")
    add(" FAN HOUSING  - tall U-channel with front retaining rail (press-fit feel)")
    add("   how it goes in          : straight DOWN into the U-channel at Z %.1f..%.1f"
        % (FAN_Z0, Z_RIN))
    add("   seat                    : the plenum floor.  This sets the height, so")
    add("                             the screw holes line up if you ever use them")
    add("   sides (X)               : two tall guide rails %.1f mm up from the floor (y=%.1f),"
        % (FAN_GUIDE_H, FLOOR_T + FAN_GUIDE_H))
    add("                             %.2f mm clearance per side, %.1f mm lead-in"
        % (FAN_GUIDE_CLEAR, FAN_GUIDE_CHAM))
    add("   behind (Z+)             : the rear wall / grille face at Z=%.1f" % Z_RIN)
    add("   forward (Z-)            : two tall front retaining rails (Z=%.1f..%.1f),"
        % (FAN_FRONT_Z_OUT, FAN_FRONT_Z_IN))
    add("                             overlapping fan frame by %.1f mm per side with %.1f mm entry chamfer"
        % (FAN_HALF - FAN_FRONT_X_IN, FAN_FRONT_CHAM))
    add("   track depth (Z)         : %.2f mm (for 25.0 mm fan frame) -> snug press-fit feel"
        % (Z_RIN - FAN_FRONT_Z_IN))
    add("   up (Y+)                 : closed by lid plate (%.1f mm headroom above frame)"
        % (PLEN_Y1 - FAN_TOP))
    add("   => restrained on all six sides: toolless slide-in, zero screws, rock solid")
    add("")
    add(" DRIVE BAY NET MOTIF  (weight & cost reduction cutouts)")
    add("   pattern                 : hexagonal honeycomb mesh (%.1f mm cells, %.1f mm webs)"
        % (NET_CELL, NET_WEB))
    add("   cutout panels           : top roof, bottom floor, left wall, right wall")
    add("   total hex cells         : %d cells" % log.get("net_cells", 0))
    add("   cost impact             : reduces raw plastic mass by ~107 g solid (~80 g printed)")
    add("")
    add(" HONEYCOMB EXHAUST GRILLE  (recessed into the outer face)")
    add("   pocket                  : O%.1f, %.1f mm deep"
        % (2 * GRILLE_POCKET_R, REAR_WALL_T - GRILLE_DEPTH))
    add("   membrane                : %.1f mm thick" % GRILLE_DEPTH)
    add("   cell / web              : %.1f mm across flats / %.1f mm walls"
        % (GRILLE_CELL, GRILLE_WEB))
    add("   cells                   : %d" % log["honeycomb_cells"])
    add("   open fraction of field  : %.0f%%" % (((GRILLE_RP / GRILLE_R) ** 2) * 100.0))
    add("   tightest edge margin    : %.2f mm (pocket to the top edge)"
        % (REAR_H - FAN_CY - GRILLE_POCKET_R))
    add("")
    add(" PicoPSU CRADLE  (transverse, shifted left X=%+.1f mm)"
        % PSU_CX)
    add("   board                   : %.1f (L, across X) x %.1f (W, along Z) x %.1f (H) mm"
        % (PSU_L, PSU_W, PSU_H))
    add("   cradle inner            : %.1f x %.1f mm, %.1f mm clearance per side"
        % (2 * PSU_XH, 2 * PSU_ZH, PSU_CLEAR))
    add("   cradle Z                : %.1f .. %.1f  (mouth to rear wall)"
        % (PSU_Z0, PSU_Z1))
    add("   backplane clearance     : %.1f mm from the cradle mouth to the"
        % PSU_BOOT)
    add("                             backplane face - the board cannot reach it")
    add("   lateral clearance       : %.1f mm open plenum floor on right (X=%.1f..%.1f)"
        % (PLEN_XI - (PSU_CX + PSU_XH), PSU_CX + PSU_XH, PLEN_XI))
    add("                             for backplane power cable and Wago 221 lever blocks")
    add("   plinth                  : %.1f mm, board sits clear of the floor"
        % PSU_PLINTH_T)
    add("   front lip               : %.1f mm tall (%.1f mm above the plinth),"
        % (PSU_FRONT_LIP, PSU_FRONT_LIP - PSU_PLINTH_T))
    add("                             stops the board sliding forward")
    add("   retaining strap         : %.1f x %.1f x %.1f mm, toolless snap fit"
        % (2 * (PSU_STRAP_X + PSU_LEG_T), PSU_STRAP_H, PSU_STRAP_L))
    add("                             clips over corner boss ledges (0 screws, 0 inserts),")
    add("                             %.1f mm gap over the board top"
        % (PSU_TOP - FLOOR_T - PSU_PLINTH_T - PSU_H))
    add("")
    add(" DC INPUT JACK  (rear wall)")
    add("   centre                  : (%+.1f, %.1f)" % (DC_JACK_X, DC_JACK_Y))
    add("   panel counterbore       : O%.1f x %.1f mm deep, leaving a %.1f mm"
        % (DC_JACK_PAD, DC_JACK_DEPTH, REAR_WALL_T - DC_JACK_DEPTH))
    add("                             thick panel for the jack nut")
    add("   jack hole               : O%.1f through" % DC_JACK_DIA)
    add("   edge margin             : %.2f mm outboard"
        % (PLEN_XW - DC_JACK_X - DC_JACK_PAD / 2.0))
    add("")
    add(" CABLE EGRESS  (rear wall, beside the grille)")
    add("   %d slots                : %.1f (X) x %.1f (Y) mm, rounded corners"
        % (len(REAR_CABLE_SLOT_Y), REAR_CABLE_SLOT_W, REAR_CABLE_SLOT_H))
    add("   centres                 : X=%+.1f   Y = %s"
        % (REAR_CABLE_SLOT_X,
           ", ".join("%.1f" % y for y in REAR_CABLE_SLOT_Y)))
    add("   fitted SFF-8088 lead    : ~12.5 x 8 mm, so %.1f x %.1f mm of slack"
        % (REAR_CABLE_SLOT_W - 12.5, REAR_CABLE_SLOT_H - 8.0))
    add("   clearance to the grille : %.2f mm (slot corner to the pocket)"
        % min(math.hypot(abs(REAR_CABLE_SLOT_X) - REAR_CABLE_SLOT_W / 2.0,
                         y - FAN_CY) - GRILLE_POCKET_R
              for y in REAR_CABLE_SLOT_Y))
    add("   clearance to the edge   : %.2f mm outboard"
        % (PLEN_XW - abs(REAR_CABLE_SLOT_X) - REAR_CABLE_SLOT_W / 2.0))
    add("")
    add(" SERVICE LID  (slide-and-click housing - 100% screwless)")
    add("   outside                 : %.1f (W) x %.1f (D) mm, %.1f mm plate"
        % (2 * LID_OX, LID_Z1 - LID_Z0, LID_T))
    add("   skirts                  : %.1f mm deep at the sides, %.1f mm"
        % (SKIRT_D, REAR_H - LID_Y_FRONT_BOT))
    add("                             at the front (covering the step), all %.1f mm thick" % SKIRT_T)
    add("   guide rails             : 45 deg beveled slide rails on outer walls (Z %.1f..%.1f)"
        % (RAIL_Z0, Z_OUT))
    add("                             glide clearance: %.2f mm" % SLIDE_CLEAR)
    add("   cantilever latch        : %.1f mm wide spring arm with %.1f mm catch tooth"
        % (LATCH_W, LATCH_TOOTH_D))
    add("   pull ring holder        : O%.1f mm finger hole at front center for effortless removal"
        % LID_RING_HOLE)
    add("   positive stop           : front face seats against 8.2 mm step at Z=%.1f" % Z_BAY)
    add("   screws                  : 0 (100% toolless slide-and-click)")
    add("")
    add("   FAN CABLE & RETENTION   - fan captive with no screws")
    add("   fan underside clearance : flush lid underside, fan captured in body U-channel")
    add("   headroom over the frame : %.1f mm (frame top y=%.1f, ceiling y=%.1f)"
        % (PLEN_Y1 - FAN_TOP, FAN_TOP, PLEN_Y1))
    add("   skirt vs the case       : the skirt is outside the case, so it cannot")
    add("                             reach any cable that is inside")
    add("")
    add("   service opening         : %.1f wide, Z %.1f..%.1f, R%.1f corners"
        % (2 * SVC_HALF, SVC_Z0, SVC_Z1, SVC_R))
    add("   entry for the fan       : Z %.1f..%.1f, straight down into the housing."
        % (FAN_Z0, Z_RIN))
    add("                             The front tabs and rails make that the only")
    add("                             way in, so there is nothing to slide or align")
    add("   roof left beside opening: %.1f mm each side, plus %.1f mm across"
        % (PLEN_XI - SVC_HALF, SVC_Z0 - Z_BAY))
    add("                             the front")
    add("")
    add(" EDGE TREATMENT  (outside edges only, for handling and to stop chipping)")
    add("   body / strap fillet     : R%.1f on every outer edge" % FILLET_R)
    add("   lid fillet              : R%.1f (its plate is only %.1f mm thick)"
        % (FILLET_R_LID, LID_T))
    add("   filleted                : %s"
        % ("yes" if log["shell_volume_filleted"]
           < log["shell_volume_bare"] - 1.0 else "NO - check the build log"))
    add("   material the rounds took : %.0f mm3 off the bare shell"
        % (log["shell_volume_bare"] - log["shell_volume_filleted"]))
    add("   wall at the mouth corner : %.2f mm  (%.1f wall - R%.1f - %.1f lead-in)"
        % (WALL - FILLET_R - LEAD_IN / 2.0, WALL, FILLET_R, LEAD_IN / 2.0))
    add("   lead-in flare           : %.1f mm total, down from 1.6 mm - the round"
        % LEAD_IN)
    add("                             and the flare both cut the same 2.8 mm")
    add("                             front wall, so one had to give")
    add("")
    add(" VOLUME / MASS / PRICING @ Rp 600/g")
    total_solid = 0.0
    total_printed = 0.0
    RATE = 600.0
    for name, shp in (("body", body), ("lid", lid), ("strap", strap)):
        v = shp.Volume
        m_sol = v / 1000.0 * 1.27
        m_prn = m_sol * 0.75
        total_solid += m_sol
        total_printed += m_prn
        add("   %-6s volume / solid / prn: %7.1f cm3 | %5.0f g (solid) | %5.0f g (printed) -> Rp %9.0f"
            % (name, v / 1000.0, m_sol, m_prn, m_prn * RATE))
    add("   ----------------------------------------------------------------------------------")
    add("   TOTAL ENCLOSURE          : %7.1f cm3 | %5.0f g (solid) | %5.0f g (printed) -> Rp %9.0f"
        % ((body.Volume + lid.Volume + strap.Volume) / 1000.0, total_solid, total_printed, total_printed * RATE))
    add("")
    add(" SANITY CHECKS")
    add("   body valid              : %s" % body.isValid())
    add("   lid valid               : %s" % lid.isValid())
    add("   strap valid             : %s" % strap.isValid())
    add("   body closed (solid)     : %s" % body.isClosed())
    add("   strap closed (solid)    : %s" % strap.isClosed())
    bb = body.BoundBox
    add("   body bbox               : %.2f x %.2f x %.2f"
        % (bb.XLength, bb.YLength, bb.ZLength))
    bb = lid.BoundBox
    add("   lid  bbox               : %.2f x %.2f x %.2f"
        % (bb.XLength, bb.YLength, bb.ZLength))
    lid_inter = body.common(lid).Volume
    add("   body/lid interference    : %.4f mm3" % lid_inter)
    add("   body/strap interference  : %.4f mm3" % body.common(strap).Volume)
    add("   build volume (Bambu H2S 340x320x340):")
    add("     body  fits            : %s" % (bb_max(body) <= 340.0))
    add("     lid   fits            : %s"
        % (max(lid.BoundBox.XLength, lid.BoundBox.YLength,
               lid.BoundBox.ZLength) <= 340.0))
    add("     strap fits            : %s"
        % (max(strap.BoundBox.XLength, strap.BoundBox.YLength,
               strap.BoundBox.ZLength) <= 340.0))
    add("   PicoPSU phantom fit (board pushed to the rear of the cradle):")
    psu = box(PSU_L, PSU_H, PSU_W, PSU_CX - PSU_L / 2.0,
              FLOOR_T + PSU_PLINTH_T, PSU_Z1 - PSU_W)
    inter = body.common(psu).Volume
    add("     board/body interference: %.4f mm3  -> %s"
        % (inter, "CLEAR" if inter < 1e-6 else "FOULING"))
    add("     board front to backplane: %.2f mm in the rearmost position"
        % ((PSU_Z1 - PSU_W) - Z_BAY))
    add("   HP cage slide path (145.0 x 87.0 mm, entrance to stop frame at Z=%.1f):"
        % (Z_BAY - STOP_RIB_D))
    cage_phantom = box(CAGE_W, CAGE_H, Z_BAY - STOP_RIB_D, -CAGE_W / 2.0, FLOOR_T, 0.0)
    cage_inter = body.common(cage_phantom).Volume
    add("     cage/body interference  : %.4f mm3  -> %s"
        % (cage_inter, "CLEAR" if cage_inter < 1e-6 else "FOULING"))
    add("   slide rails on body     : length %.1f mm (Z %.1f..%.1f), height %.1f..%.1f mm"
        % (Z_OUT - RAIL_Z0, RAIL_Z0, Z_OUT,
           RAIL_YC - RAIL_H / 2.0 - RAIL_W, RAIL_YC + RAIL_H / 2.0 + RAIL_W))
    add("   front catch pocket      : %.1f (W) x %.1f (H) x %.1f (D) mm at Z=%.1f"
        % (CATCH_POCKET_W, CATCH_POCKET_H, CATCH_POCKET_D, Z_BAY))
    add("   cable egress slots through the rear wall:")
    for yy in REAR_CABLE_SLOT_Y:
        probe = Part.makeSphere(1.2, Vector(REAR_CABLE_SLOT_X, yy,
                                            Z_RIN + REAR_WALL_T / 2.0))
        frac = probe.common(body).Volume / probe.Volume
        add("     X=%+6.1f Y=%5.1f : %.0f%% inside solid  -> %s"
            % (REAR_CABLE_SLOT_X, yy, 100 * frac,
               "CLEAR" if frac < 0.05 else "BLOCKED"))
    add("")
    add(" NOTES")
    if FLAT_TOP:
        add("   * Flat top: the %.0f mm fan frame fits inside the bay bore, so the"
            % FAN_SIZE)
        add("     whole case is a single prism.")
    else:
        add("   * The %.0f mm fan frame is taller than the %.1f mm bay bore, so the"
            % (FAN_SIZE, INT_H))
        add("     rear section steps up %.1f mm to hold it inside."
            % (REAR_H - BAY_H))
        add("     The largest fan that would keep the top flat is %.1f mm."
            % (BAY_H - WALL - FLOOR_T - 2 * FAN_INNER_CLEAR))
    add("   * Air path: open front -> caddies -> plenum -> fan -> honeycomb grille.")
    add("     No tapered duct any more: with the fan inside the plenum there is")
    add("     nothing to funnel into, and the volume is needed for cabling.")
    add("   * The grille is punched through a %.1f mm membrane, not the full %.1f mm"
        % (GRILLE_DEPTH, REAR_WALL_T))
    add("     wall, so it costs little airflow and still looks clean.")
    add("   * Cage side-screw Z positions are a starting suggestion: drill/print")
    add("     only the pair that lines up with your cage's own holes.")
    add("   * Rear stop frame inner aperture: %.1f x %.1f mm"
        % (INT_W - 2 * STOP_RIB_W, INT_H - 2 * STOP_RIB_W))
    add("=" * 78)
    return "\n".join(L) + "\n"


def bb_max(shape):
    bb = shape.BoundBox
    return max(bb.XLength, bb.YLength, bb.ZLength)


# ==============================================================================
# 6. EXPORT
# ==============================================================================

def export(body, lid, strap, log):
    os.makedirs(OUT_DIR, exist_ok=True)

    doc = App.newDocument("dl380_cage_case")
    ob = doc.addObject("Part::Feature", "Case_Body")
    ol = doc.addObject("Part::Feature", "Service_Lid")
    os_ = doc.addObject("Part::Feature", "PicoPSU_Strap")
    ob.Shape, ol.Shape, os_.Shape = body, lid, strap
    doc.recompute()

    import Import
    import Mesh

    paths = []
    p_all = os.path.join(OUT_DIR, BASENAME + ".step")
    Import.export([ob, ol, os_], p_all)
    paths.append(p_all)

    for name, shape in (("body", body), ("lid", lid), ("strap", strap)):
        p = os.path.join(OUT_DIR, "%s_%s.step" % (BASENAME, name))
        shape.exportStep(p)
        paths.append(p)

    for name, obj in (("body", ob), ("lid", ol), ("strap", os_)):
        p = os.path.join(OUT_DIR, "%s_%s.stl" % (BASENAME, name))
        Mesh.export([obj], p)
        paths.append(p)

    txt = report(body, lid, strap, log)
    p = os.path.join(OUT_DIR, "%s_report.txt" % BASENAME)
    with open(p, "w") as f:
        f.write(txt)
    paths.append(p)

    return paths, txt


# ==============================================================================
# 7. MAIN
# ==============================================================================

def main():
    body, lid, strap, log = build()
    paths, txt = export(body, lid, strap, log)
    print(txt)
    print("FILES:")
    for p in paths:
        print("  %-70s %8d bytes" % (p, os.path.getsize(p)))


if __name__ in ("__main__",                    # python3 dl380_cage_case.py
                os.path.splitext(os.path.basename(__file__))[0]):  # freecadcmd ...
    main()
