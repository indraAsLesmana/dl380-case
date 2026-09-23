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
LID_LIP_T     = 2.0      # mm  lid locating lip depth (drops into the opening)
STOP_RIB_W    = 4.0      # mm  width of the internal rear stop frame
STOP_RIB_D    = 3.0      # mm  how far the stop frame sticks into the bay
REAR_WALL_LAYERS = 3     # rear wall in wall-units -> 8.4 mm, enough for a
                         # standard 5.7 mm M3 heat-set insert to seat fully
GUSSET_H      = 18.0     # mm  45 deg gussets under the plenum roof.  They carry
                         # the lid screws and stop the roof bridging in mid air

# ---- wiring / airflow plenum -------------------------------------------------
PLENUM_D      = 108.0    # mm  clear depth behind the backplane.  Holds, front to
                         #     back: 20 mm of cable boot space, a 55 mm PicoPSU
                         #     cradle and the 25 mm fan against the rear wall.

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

# ---- honeycomb exhaust grille ------------------------------------------------
GRILLE_CELL   =   9.0    # mm  honeycomb cell size, across flats
GRILLE_WEB    =   1.2    # mm  material between cells (3 lines @ 0.4 mm nozzle)
GRILLE_RIM    =   2.0    # mm  solid ring between the cells and the pocket wall
GRILLE_DEPTH  =   3.0    # mm  membrane thickness the cells are punched through

# ---- cable egress (rear wall, beside the grille pocket) ----------------------
#  The SFF-8087 -> SFF-8088 leads now leave through the BACK, in two separate
#  slots so each cable keeps its own strain relief and they stay clear of the
#  fan.  X is negative - they exit on the left, where the cabling already runs.
REAR_CABLE_SLOT_X = -60.0          # mm  slot centre X
REAR_CABLE_SLOT_Y = (33.0, 50.0)   # mm  slot centre heights
REAR_CABLE_SLOT_W =  17.0          # mm  slot width in X
REAR_CABLE_SLOT_H =  12.0          # mm  slot height in Y

# ---- PicoPSU cradle ----------------------------------------------------------
#  mini-box picoPSU-120 measured 31 x 44 x 21 mm (1U), 57 g with its harness.
#  It sits in a cradle on the plenum floor 20 mm behind the backplane so it can
#  never be pushed back onto the backplane PCB, and a strap over the top stops
#  it lifting out.
PSU_W, PSU_L, PSU_H = 31.0, 44.0, 21.0   # mm  board envelope
PSU_CLEAR     =   0.8    # mm  clearance per side in the cradle
PSU_BOOT      =  20.0    # mm  gap between the backplane and the cradle mouth
PSU_PLINTH_T  =   3.0    # mm  the board sits on this, off the floor
PSU_WALL_H    =  24.0    # mm  cradle wall height above the floor
PSU_FRONT_LIP =   6.0    # mm  front wall height; the 3 mm above the plinth is
                         #     what stops the board sliding forward
PSU_STRAP_H   =   4.0    # mm  retaining strap thickness
PSU_STRAP_L   =  20.0    # mm  retaining strap length in Z
PSU_BOSS_W    =   6.0    # mm  boss sticking sideways past each cradle wall
PSU_BOSS_L    =  14.0    # mm  boss length in Z
PSU_INSERT_D  =  10.0    # mm  M3 heat-set insert depth into the boss
PSU_SCREW_DIA =   3.4    # mm  M3 clearance through the strap

# ---- DC input jack (rear wall) ----------------------------------------------
#  For a panel-mount 5.5 x 2.5 mm barrel jack, matching the picoPSU-120's DC
#  input.  The outer face is counterbored so the jack sees a 3.4 mm panel
#  rather than the full 8.4 mm wall, which is thicker than most jacks accept.
DC_JACK_X     =  60.0    # mm  centre X (right of the grille; cables exit left)
DC_JACK_Y     =  52.0    # mm  centre Y
DC_JACK_DIA   =   8.0    # mm  jack body hole
DC_JACK_PAD   =  16.0    # mm  counterbore diameter in the outer face
DC_JACK_DEPTH =   5.0    # mm  counterbore depth

# ---- service opening + lid screws -------------------------------------------
SVC_Z0        = 172.0    # mm  front edge of the service opening
SVC_Z1_BACKOFF=   0.0    # mm  how far short of the rear wall the opening stops.
                         #     Keep it <= FAN_INSET - 2 or the fan can no longer
                         #     be lowered into place behind the PSU cradle; the
                         #     report prints the resulting drop-in window.
SVC_R         =  12.0    # mm  corner radius of the opening
LID_SCREW_X   = 70.0     # mm  +/- X of the lid screws
LID_SCREW_Z   = (185.0, 215.0, 245.0)   # mm  Z of the lid screws (both sides)
LID_INSERT_D  = 10.0     # mm  depth of the heat-set insert bore from the top face
LID_INSERT_DIA= 4.2      # mm  bore for M3 heat-set insert
LID_CLEAR_DIA = 3.4      # mm  M3 clearance hole through the lid

# ---- HP cage anchoring -------------------------------------------------------
CAGE_SCREW_Z  = (15.0, 45.0, 75.0, 105.0, 135.0, 155.0)  # suggested Z of side holes
CAGE_SCREW_DIA= 3.4      # mm  M3 clearance through the 2.8 side wall

# ---- base --------------------------------------------------------------------
FOOT_DIA      = 12.0     # mm  rubber foot recess
FOOT_DEEP     = 2.0      # mm
FOOT_X        = 61.0     # mm  +/- X of the foot centres
FOOT_Z        = (14.0, 260.0)

# ---- entry lead-in -----------------------------------------------------------
LEAD_IN       = 1.6      # mm  flare added to the aperture at the mouth
LEAD_DEPTH    = 4.0      # mm  how deep that flare goes

# ---- faceting ----------------------------------------------------------------
DUCT_SEG      = 96       # polygon segments used for the entry lead-in flare

# ---- output ------------------------------------------------------------------
OUT_DIR       = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
BASENAME      = "dl380_cage_case"

# ==============================================================================
# 2. DERIVED DIMENSIONS  -  do not hand-edit, all computed
# ==============================================================================

INT_W   = CAGE_W + 2 * FIT_CLEAR           # internal width  of the bay sleeve
INT_H   = CAGE_H + 2 * FIT_CLEAR           # internal height of the bay sleeve
OUT_W   = INT_W + 2 * WALL                 # outside width
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
FAN_CY  = (BAY_Y0 + PLEN_Y1) / 2.0         # fan axis, centred in the plenum bore
FAN_Z0  = Z_RIN - FAN_INSET                # front face of the fan

# honeycomb geometry: R sizes a perfect tiling, Rp the shrunken cells we cut
GRILLE_R        = (GRILLE_CELL + GRILLE_WEB) / math.sqrt(3.0)
GRILLE_RP       = GRILLE_R - GRILLE_WEB / math.sqrt(3.0)
GRILLE_OPEN_R   = FAN_R - GRILLE_RP        # only centres inside this get a cell
GRILLE_POCKET_R = FAN_R + GRILLE_RIM       # recess radius in the outer face

XW       = OUT_W / 2.0                     # outer half width
XI       = INT_W / 2.0                     # inner half width
SVC_HALF = XI - GUSSET_H                   # service opening half width

# ---- PicoPSU cradle placement ------------------------------------------------
PSU_XH      = (PSU_W + 2 * PSU_CLEAR) / 2.0    # cradle inner half width  16.3
PSU_ZH      = (PSU_L + 2 * PSU_CLEAR) / 2.0    # cradle inner half length 22.8
PSU_Z0      = Z_BAY + PSU_BOOT                 # cradle mouth            185.0
PSU_Z1      = PSU_Z0 + 2 * PSU_ZH              # cradle inner rear       230.6
PSU_TRAY_OH = PSU_XH + WALL                    # cradle outer half width  19.1
PSU_TOP     = FLOOR_T + PSU_PLINTH_T + PSU_H + 0.4   # board top + clearance 28.4
PSU_BOSS_X  = PSU_XH + (WALL + PSU_BOSS_W) / 2.0     # insert centre        20.7
PSU_BORE_Z  = PSU_Z0 + PSU_BOSS_L / 2.0 + 0.0        # strap screw Z        192.0
PSU_STRAP_X = PSU_TRAY_OH + PSU_BOSS_W               # strap half width     25.1

# ---- service opening, derived from the rear wall -----------------------------
SVC_Z1 = Z_RIN - SVC_Z1_BACKOFF            # opening rear edge
# The fan is inserted through this opening and can only descend BEHIND the
# cradle, so these two numbers bound where it can drop in before being pushed
# back against the rear wall.  If FAN_LO > FAN_HI the fan cannot be fitted.
FAN_DROP_LO = PSU_Z1 + WALL + 2.0          # clear of the cradle's rear wall
FAN_DROP_HI = SVC_Z1 - FAN_INSET           # its thickness must clear the roof


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


# ==============================================================================
# 4. BUILD
# ==============================================================================

def build():
    log = []

    # ---------------------------------------------------------------- shell ---
    outer = box(OUT_W, BAY_H, Z_BAY, -XW, 0.0, 0.0)
    outer = outer.fuse(box(OUT_W, REAR_H, Z_OUT - Z_BAY, -XW, 0.0, Z_BAY))

    # ---------------------------------------------------------------- voids ---
    bay_void = box(INT_W, INT_H, Z_BAY + 1.0, -XI, BAY_Y0, -1.0)
    plen_void = box(INT_W, PLEN_Y1 - BAY_Y0, PLENUM_D, -XI, BAY_Y0, Z_BAY)

    body = outer.cut(bay_void.fuse(plen_void))

    # ------------------------------------- internal rear stop frame for cage ---
    ring = box(INT_W, INT_H, STOP_RIB_D, -XI, BAY_Y0, Z_BAY - STOP_RIB_D)
    ring = ring.cut(box(INT_W - 2 * STOP_RIB_W, INT_H - 2 * STOP_RIB_W,
                        STOP_RIB_D + 2.0,
                        -(XI - STOP_RIB_W), BAY_Y0 + STOP_RIB_W,
                        Z_BAY - STOP_RIB_D - 1.0))
    body = body.fuse(ring)

    # ------------------------------------------- roof gussets beside the lid ---
    for side in (1, -1):
        body = body.fuse(gusset(XI, PLEN_Y1, GUSSET_H, Z_BAY, Z_RIN, side))

    # ----------------------------------------------- PicoPSU cradle in plenum ---
    #  plinth the board stands on
    body = body.fuse(box(2 * PSU_XH, PSU_PLINTH_T, 2 * PSU_ZH,
                         -PSU_XH, FLOOR_T, PSU_Z0))
    #  side walls
    for sx in (1, -1):
        x0 = PSU_XH if sx > 0 else -PSU_TRAY_OH
        body = body.fuse(box(WALL, PSU_WALL_H, 2 * PSU_ZH, x0, FLOOR_T, PSU_Z0))
    #  rear wall and the low lip across the mouth, which is what stops the
    #  board sliding forward onto the backplane
    body = body.fuse(box(2 * PSU_TRAY_OH, PSU_WALL_H, WALL,
                         -PSU_TRAY_OH, FLOOR_T, PSU_Z1))
    body = body.fuse(box(2 * PSU_TRAY_OH, PSU_FRONT_LIP, WALL,
                         -PSU_TRAY_OH, FLOOR_T, PSU_Z0 - WALL))
    #  corner bosses that take the retaining-strap inserts
    for sx in (1, -1):
        bx = PSU_TRAY_OH if sx > 0 else -(PSU_TRAY_OH + PSU_BOSS_W)
        body = body.fuse(box(PSU_BOSS_W, PSU_TOP - FLOOR_T, PSU_BOSS_L,
                             bx, FLOOR_T, PSU_BORE_Z - PSU_BOSS_L / 2.0))

    # ------------------------------------------------------------------ cuts ---
    cuts = []

    # --- retaining-strap inserts in the two corner bosses --------------------
    for sx in (1, -1):
        cuts.append(cyl_y(LID_INSERT_DIA / 2.0, PSU_INSERT_D,
                          sx * PSU_BOSS_X, PSU_BORE_Z,
                          PSU_TOP - PSU_INSERT_D))

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
    log.append(("honeycomb cells", len(cells)))
    cuts.extend(cells)

    # --- top service opening -------------------------------------------------
    cuts.append(rounded_rect_prism(SVC_HALF, PLEN_Y1 - 6.0, REAR_H + 2.0,
                                   SVC_Z0, SVC_Z1, SVC_R))

    # --- lid heat-set insert bores (from the top face downwards) -------------
    for sx in (-1, 1):
        for zz in LID_SCREW_Z:
            cuts.append(cyl_y(LID_INSERT_DIA / 2.0, LID_INSERT_D,
                              sx * LID_SCREW_X, zz, REAR_H - LID_INSERT_D))

    # --- cable egress slots through the rear wall ----------------------------
    slot_r = min(REAR_CABLE_SLOT_W, REAR_CABLE_SLOT_H) / 2.0 - 0.01
    for yy in REAR_CABLE_SLOT_Y:
        cuts.append(rounded_rect_z(REAR_CABLE_SLOT_W / 2.0,
                                   REAR_CABLE_SLOT_H / 2.0,
                                   REAR_CABLE_SLOT_X, yy,
                                   Z_RIN - 1.0, Z_OUT + 2.0, slot_r))

    # --- HP cage anchor screws ----------------------------------------------
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

    for c in cuts:
        body = body.cut(c)

    body = _tidy(body)

    # ============================================================== service lid
    lid = box(OUT_W, LID_T, Z_OUT - Z_BAY, -XW, REAR_H, Z_BAY)
    lid = lid.fuse(rounded_rect_prism(SVC_HALF - 0.5, REAR_H - LID_LIP_T,
                                      REAR_H, SVC_Z0 + 0.5, SVC_Z1 - 0.5,
                                      SVC_R - 0.5))
    for sx in (-1, 1):
        for zz in LID_SCREW_Z:
            lid = lid.cut(cyl_y(LID_CLEAR_DIA / 2.0, LID_T + LID_LIP_T + 2.0,
                                sx * LID_SCREW_X, zz, REAR_H - LID_LIP_T - 1.0))
    lid = _tidy(lid)

    # ============================================== PicoPSU retaining strap ---
    strap = box(2 * PSU_STRAP_X, PSU_STRAP_H, PSU_STRAP_L,
                -PSU_STRAP_X, PSU_TOP, PSU_BORE_Z - PSU_STRAP_L / 2.0)
    for sx in (1, -1):
        strap = strap.cut(cyl_y(PSU_SCREW_DIA / 2.0, PSU_STRAP_H + 2.0,
                                sx * PSU_BOSS_X, PSU_BORE_Z, PSU_TOP - 1.0))
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
    add("   outside W x H x D       : %.1f x %.1f x %.1f mm"
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
    add("   roof gussets            : %.1f mm tall at 45 deg, carrying the lid screws"
        % GUSSET_H)
    add("")
    add(" FAN  -  %s" % FAN_MODEL)
    add("   nominal size            : %.0f x %.0f x 25 mm, 106 g"
        % (FAN_SIZE, FAN_SIZE))
    add("   P9 PWM PST rating       : 200-3000 rpm PWM (0 rpm below 5%),")
    add("                             38.83 cfm | 65.97 m3/h, 3.12 mmH2O static,")
    add("                             0.12 A @ 12 V = 1.44 W, fluid dynamic bearing")
    add("   position                : INSIDE, against the rear wall, Z %.1f..%.1f"
        % (FAN_Z0, Z_RIN))
    add("   bore it sits in         : %.1f (W) x %.1f (H) x %.1f (D) mm"
        % (INT_W, PLEN_Y1 - BAY_Y0, PLENUM_D))
    add("   frame clearance         : %.1f mm on every side of the frame"
        % FAN_INNER_CLEAR)
    add("   hole pattern            : %.1f x %.1f square, O%.1f"
        % (FAN_PATTERN, FAN_PATTERN, FAN_HOLE))
    add("   hole centres (X,Y)      : (+/-%.1f, %.1f)  (+/-%.1f, %.1f)"
        % (FAN_OFF, FAN_CY - FAN_OFF, FAN_OFF, FAN_CY + FAN_OFF))
    add("   mounting                : M3 heat-set inserts pressed into the rear")
    add("                             wall from OUTSIDE, M3 x 30 screws through")
    add("                             the fan frame from inside the plenum")
    add("")
    add(" HONEYCOMB EXHAUST GRILLE  (recessed into the outer face)")
    add("   pocket                  : O%.1f, %.1f mm deep"
        % (2 * GRILLE_POCKET_R, REAR_WALL_T - GRILLE_DEPTH))
    add("   membrane                : %.1f mm thick" % GRILLE_DEPTH)
    add("   cell / web              : %.1f mm across flats / %.1f mm walls"
        % (GRILLE_CELL, GRILLE_WEB))
    add("   cells                   : %d" % log[0][1])
    add("   open fraction of field  : %.0f%%" % (((GRILLE_RP / GRILLE_R) ** 2) * 100.0))
    add("   tightest edge margin    : %.2f mm (pocket to the top edge)"
        % (REAR_H - FAN_CY - GRILLE_POCKET_R))
    add("")
    add(" PicoPSU CRADLE  (plenum floor, %.1f mm behind the backplane)"
        % PSU_BOOT)
    add("   board                   : %.1f (W) x %.1f (L) x %.1f (H) mm"
        % (PSU_W, PSU_L, PSU_H))
    add("   cradle inner            : %.1f x %.1f mm, %.1f mm clearance per side"
        % (2 * PSU_XH, 2 * PSU_ZH, PSU_CLEAR))
    add("   cradle Z                : %.1f .. %.1f  (mouth to rear wall)"
        % (PSU_Z0, PSU_Z1))
    add("   backplane clearance     : %.1f mm from the cradle mouth to the"
        % PSU_BOOT)
    add("                             backplane face - the board cannot reach it")
    add("   plinth                  : %.1f mm, board sits clear of the floor"
        % PSU_PLINTH_T)
    add("   front lip               : %.1f mm tall (%.1f mm above the plinth),"
        % (PSU_FRONT_LIP, PSU_FRONT_LIP - PSU_PLINTH_T))
    add("                             stops the board sliding forward")
    add("   retaining strap         : %.1f x %.1f x %.1f mm, 2 x M3 into corner"
        % (2 * PSU_STRAP_X, PSU_STRAP_H, PSU_STRAP_L))
    add("                             bosses with O%.1f heat-set inserts,"
        % LID_INSERT_DIA)
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
        % (XW - DC_JACK_X - DC_JACK_PAD / 2.0))
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
        % (XW - abs(REAR_CABLE_SLOT_X) - REAR_CABLE_SLOT_W / 2.0))
    add("")
    add(" SERVICE LID")
    add("   plate                   : %.1f x %.1f x %.1f mm"
        % (OUT_W, LID_T, Z_OUT - Z_BAY))
    add("   opening                 : %.1f wide, Z %.1f..%.1f, R%.1f corners"
        % (2 * SVC_HALF, SVC_Z0, SVC_Z1, SVC_R))
    add("   fan drop-in window      : Z %.1f .. %.1f  (%s)"
        % (FAN_DROP_LO, FAN_DROP_HI,
           "%.1f mm of slack, then push it back against the rear wall"
           % (FAN_DROP_HI - FAN_DROP_LO) if FAN_DROP_HI >= FAN_DROP_LO
           else "*** FAN CANNOT BE FITTED ***"))
    add("   roof left beside opening: %.1f mm each side, plus %.1f mm across"
        % (XI - SVC_HALF, SVC_Z0 - Z_BAY))
    add("                             the front")
    add("   %d x M3 lid screws       : X=+/-%.1f  Z=%s"
        % (2 * len(LID_SCREW_Z), LID_SCREW_X, LID_SCREW_Z))
    add("                             O%.1f insert bore / O%.1f clearance"
        % (LID_INSERT_DIA, LID_CLEAR_DIA))
    add("")
    add(" VOLUME / MASS")
    for name, shp in (("body", body), ("lid", lid), ("strap", strap)):
        v = shp.Volume
        add("   %-6s volume            : %10.1f mm3  = %6.1f cm3"
            % (name, v, v / 1000.0))
        add("   %-6s mass @1.27 g/cm3  : %8.0f g  (PETG, 100%% infill equiv)"
            % (name, v / 1000.0 * 1.27))
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
    add("   body/lid interference    : %.4f mm3" % body.common(lid).Volume)
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
    psu = box(PSU_W, PSU_H, PSU_L, -PSU_W / 2.0,
              FLOOR_T + PSU_PLINTH_T, PSU_Z1 - PSU_L)
    inter = body.common(psu).Volume
    add("     board/body interference: %.4f mm3  -> %s"
        % (inter, "CLEAR" if inter < 1e-6 else "FOULING"))
    add("     board front to backplane: %.2f mm in the rearmost position"
        % ((PSU_Z1 - PSU_L) - Z_BAY))
    add("   lid-screw insert bores - material around the O%.1f bore:"
        % LID_INSERT_DIA)
    for sx in (-1, 1):
        for zz in LID_SCREW_Z:
            ds = ring_depths(body, sx * LID_SCREW_X, zz, radius=3.4, n=6,
                             y_top=REAR_H, max_d=LID_INSERT_D + 3.0)
            add("     X=%+7.1f Z=%6.1f : min %.1f mm / max %.1f mm  -> %s"
                % (sx * LID_SCREW_X, zz, min(ds), max(ds),
                   "OK" if min(ds) >= LID_INSERT_D else "TOO SHALLOW"))
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
