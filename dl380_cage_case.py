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

# ---- wiring / airflow plenum -------------------------------------------------
PLENUM_D      = 65.0     # mm  clear depth behind the backplane (spec: 65)
REAR_H        = 132.0    # mm  OUTER height of the fan/plenum section
REAR_WALL_T   = 5.6      # mm  rear wall thickness (2 x WALL, stiff, holds fan)

# ---- 120 mm fan --------------------------------------------------------------
FAN_APERTURE  = 115.0    # mm  Ø of the circular opening
FAN_PATTERN   = 105.0    # mm  fan mounting hole square pattern
FAN_HOLE      =   4.2    # mm  Ø  -> 4.2 for M3 heat-set insert, 4.5 for M4 pass
FAN_DUCT_GAP  =  16.0    # mm  how far the tapered duct starts ahead of rear wall
FAN_CABLE_SLOT= (12.0, 4.0)   # W x H fan-cable notch in the rear wall (centre, low)

# ---- cable egress ------------------------------------------------------------
CABLE_SLOT_C  = (20.0, 213.0)  # (Y centre, Z centre) on the LEFT (-X) wall
CABLE_SLOT_SZ = (16.0, 30.0)   # (height in Y, length in Z)   >= 14 x 28 per spec
CABLE_SLOT_MIRROR = False      # True -> also cut the same slot in the right wall

# ---- service opening + lid screws -------------------------------------------
SVC_W         = 96.0     # mm  service opening width  (X)
SVC_Z0, SVC_Z1= 172.0, 223.0   # mm  service opening extent in Z
SVC_R         = 10.0     # mm  corner radius of the opening
LID_SCREW_X   = 68.0     # mm  +/- X of the four lid screws
LID_SCREW_Z   = (180.0, 215.0) # mm  Z of the four lid screws
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
FOOT_Z        = (14.0, 221.6)

# ---- entry lead-in -----------------------------------------------------------
LEAD_IN       = 1.6      # mm  flare added to the aperture at the mouth
LEAD_DEPTH    = 4.0      # mm  how deep that flare goes

# ---- faceting ----------------------------------------------------------------
DUCT_SEG      = 96       # segments of the rect->circle airflow transition

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

Z_BAY   = CAGE_D                           # front face of the plenum
Z_RIN   = CAGE_D + PLENUM_D                # inner face of the rear wall
Z_OUT   = Z_RIN + REAR_WALL_T              # very back of the enclosure

BAY_Y0  = FLOOR_T                          # inside floor
BAY_Y1  = FLOOR_T + INT_H                  # inside ceiling of the bay
BAY_YC  = (BAY_Y0 + BAY_Y1) / 2.0          # bay vertical centre
PLEN_Y1 = REAR_H - WALL                    # inside ceiling of the plenum
FAN_CY  = REAR_H / 2.0                     # fan axis height

XW      = OUT_W / 2.0                      # outer half width
XI      = INT_W / 2.0                      # inner half width

FAN_R   = FAN_APERTURE / 2.0
FAN_OFF = FAN_PATTERN / 2.0                # +/- offset of the 4 fan holes


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


def circle_points(radius, cy, n, phase=0.0):
    """n points ON a circle, same angular ordering as rect_points()."""
    return [(radius * math.cos(2 * math.pi * i / n + phase),
             cy + radius * math.sin(2 * math.pi * i / n + phase))
            for i in range(n)]


def stadium(center_y, center_z, height_y, length_z, span_x0, span_x1, r):
    """Rounded-end (stadium) slot, extruded along X from span_x0 to span_x1."""
    z0 = center_z - (length_z / 2.0 - r)
    z1 = center_z + (length_z / 2.0 - r)
    L = span_x1 - span_x0
    s = box(L, height_y, length_z - 2 * r, span_x0, center_y - r, z0)
    for zz in (z0, z1):
        s = s.fuse(cyl_x(r, L, center_y, zz, span_x0))
    return s


def rounded_rect_prism(half_w, y0, y1, z0, z1, r):
    """Rounded rectangle in the XZ plane, extruded along Y."""
    W, D = 2 * half_w, z1 - z0
    s = box(W, y1 - y0, D, -half_w, y0, z0)
    for xx in (-half_w + r, half_w - r):
        for zz in (z0 + r, z1 - r):
            s = s.fuse(cyl_y(r, y1 - y0, xx, zz, y0))
    return s


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

    # drive-bay sleeve: open at the front (z = -1 so the cut really leaves)
    bay_void = box(INT_W, INT_H, Z_BAY + 1.0, -XI, BAY_Y0, -1.0)

    # ------------------------------------------- airflow transition (duct) ---
    #  rectangle 145.8 x 87.8  ->  circle Ø115, both as matched n-gons so the
    #  ruled loft cannot twist.  This is the "tapered bevel" of the spec.
    w_rect = polygon_wire(rect_points(XI, INT_H / 2.0, BAY_YC, DUCT_SEG), Z_BAY)
    w_circ = polygon_wire(circle_points(FAN_R, FAN_CY, DUCT_SEG), Z_RIN - FAN_DUCT_GAP)
    duct = Part.makeLoft([w_rect, w_circ], solid=True, ruled=False)
    duct = duct.fuse(cyl_z(FAN_R, FAN_DUCT_GAP + 1.0, 0.0, FAN_CY, Z_RIN - FAN_DUCT_GAP))
    log.append(("airflow duct volume", duct.Volume))

    # plenum upper cavity -> room for SFF-8087 boots, Wago 221 blocks, cables
    top_cav = box(2 * (XI - 14.9), PLEN_Y1 - BAY_Y1, PLENUM_D,
                  -(XI - 14.9), BAY_Y1, Z_BAY)
    plenum_void = duct.fuse(top_cav)

    body = outer.cut(bay_void.fuse(plenum_void))

    # ------------------------------------- internal rear stop frame for cage ---
    ring = box(INT_W, INT_H, STOP_RIB_D, -XI, BAY_Y0, Z_BAY - STOP_RIB_D)
    ring = ring.cut(box(INT_W - 2 * STOP_RIB_W, INT_H - 2 * STOP_RIB_W,
                        STOP_RIB_D + 2.0,
                        -(XI - STOP_RIB_W), BAY_Y0 + STOP_RIB_W,
                        Z_BAY - STOP_RIB_D - 1.0))
    body = body.fuse(ring)

    # ------------------------------------------------------------------ cuts ---
    cuts = []

    # --- 120 mm fan: aperture, 4 mounting holes, optional cable notch ---------
    cuts.append(cyl_z(FAN_R, REAR_WALL_T + 2.0, 0.0, FAN_CY, Z_RIN - 1.0))
    for sx in (-1, 1):
        for sy in (-1, 1):
            cuts.append(cyl_z(FAN_HOLE / 2.0, REAR_WALL_T + 2.0,
                              sx * FAN_OFF, FAN_CY + sy * FAN_OFF, Z_RIN - 1.0))
    fc_w, fc_h = FAN_CABLE_SLOT
    cuts.append(rounded_rect_prism(fc_w / 2.0, 2.0, 2.0 + fc_h,
                                   Z_RIN - 0.5, Z_OUT + 0.5, fc_h / 2.0 - 0.01))

    # --- tapered duct: final straight throat into the rear wall --------------
    #     (the loft already ends at the rear wall face, this just guarantees a
    #      clean cylindrical land for the fan to sit against)

    # --- top service opening -------------------------------------------------
    cuts.append(rounded_rect_prism(SVC_W / 2.0, PLEN_Y1 - 6.0, REAR_H + 2.0,
                                   SVC_Z0, SVC_Z1, SVC_R))

    # --- lid heat-set insert bores (4x, from the top face downwards) ---------
    for sx in (-1, 1):
        for zz in LID_SCREW_Z:
            cuts.append(cyl_y(LID_INSERT_DIA / 2.0, LID_INSERT_D,
                              sx * LID_SCREW_X, zz, REAR_H - LID_INSERT_D))

    # --- cable egress slots --------------------------------------------------
    cy, cz = CABLE_SLOT_C
    sh, sz = CABLE_SLOT_SZ
    sx_signs = (-1, 1) if CABLE_SLOT_MIRROR else (-1,)
    for sx in sx_signs:
        if sx < 0:
            cuts.append(stadium(cy, cz, sh, sz, -XW - 2.0, -20.0, sh / 2.0))
        else:
            cuts.append(stadium(cy, cz, sh, sz, 20.0, XW + 2.0, sh / 2.0))

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
    w_out = polygon_wire(rect_points(XI + LEAD_IN / 2.0, INT_H / 2.0 + LEAD_IN / 2.0,
                                     BAY_YC, DUCT_SEG), 0.0)
    cuts.append(Part.makeLoft([w_in, w_out], solid=True, ruled=True))

    for c in cuts:
        body = body.cut(c)

    body = _tidy(body)

    # ============================================================== service lid
    lid = box(OUT_W, LID_T, Z_OUT - Z_BAY, -XW, REAR_H, Z_BAY)
    lid = lid.fuse(rounded_rect_prism(SVC_W / 2.0 - 0.5, REAR_H - LID_LIP_T,
                                      REAR_H, SVC_Z0 + 0.5, SVC_Z1 - 0.5,
                                      SVC_R - 0.5))
    for sx in (-1, 1):
        for zz in LID_SCREW_Z:
            lid = lid.cut(cyl_y(LID_CLEAR_DIA / 2.0, LID_T + LID_LIP_T + 2.0,
                                sx * LID_SCREW_X, zz, REAR_H - LID_LIP_T - 1.0))
    lid = _tidy(lid)

    return body, lid, log


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


def ring_depths(shape, cx, cz, radius=3.4, n=8, **kw):
    """Material depth sampled on a circle around a bore -> min wall thickness."""
    out = []
    for i in range(n):
        a = 2.0 * math.pi * i / n
        out.append(material_depth(shape, cx + radius * math.cos(a),
                                  cz + radius * math.sin(a), **kw))
    return out


def report(body, lid, log):
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
    add("   wall / floor / rear wall: %.1f / %.1f / %.1f mm"
        % (WALL, FLOOR_T, REAR_WALL_T))
    add("   plenum clear depth      : %.1f mm" % PLENUM_D)
    add("")
    add(" 120 mm FAN")
    add("   aperture                : O%.1f at (0, %.1f) in the rear wall"
        % (FAN_APERTURE, FAN_CY))
    add("   hole pattern            : %.1f x %.1f square, O%.1f"
        % (FAN_PATTERN, FAN_PATTERN, FAN_HOLE))
    add("   hole centres (X,Y)      : (+/-%.1f, %.1f)  (+/-%.1f, %.1f)"
        % (FAN_OFF, FAN_CY - FAN_OFF, FAN_OFF, FAN_CY + FAN_OFF))
    add("   cable notch             : %.1f x %.1f mm, low centre"
        % FAN_CABLE_SLOT)
    add("")
    add(" CABLE EGRESS (left wall)")
    add("   stadium slot            : %.1f (Y) x %.1f (Z) mm at Y=%.1f Z=%.1f"
        % (CABLE_SLOT_SZ[0], CABLE_SLOT_SZ[1], CABLE_SLOT_C[0], CABLE_SLOT_C[1]))
    add("   mirrored to right wall  : %s" % ("YES" if CABLE_SLOT_MIRROR else "no"))
    add("")
    add(" SERVICE LID")
    add("   plate                   : %.1f x %.1f x %.1f mm"
        % (OUT_W, LID_T, Z_OUT - Z_BAY))
    add("   opening                 : %.1f wide, Z %.1f..%.1f, R%.1f corners"
        % (SVC_W, SVC_Z0, SVC_Z1, SVC_R))
    add("   4x M3 lid screws        : X=+/-%.1f  Z=%s  (O%.1f insert / O%.1f clear)"
        % (LID_SCREW_X, LID_SCREW_Z, LID_INSERT_DIA, LID_CLEAR_DIA))
    add("")
    add(" VOLUME / MASS")
    for name, shp, dens in (("body", body, 1.27), ("lid", lid, 1.27)):
        v = shp.Volume
        add("   %-6s volume            : %10.1f mm3  = %6.1f cm3"
            % (name, v, v / 1000.0))
        add("   %-6s mass @1.27 g/cm3  : %8.0f g  (PETG, 100%% infill equiv)"
            % (name, v / 1000.0 * dens))
    add("")
    add(" SANITY CHECKS")
    add("   body valid              : %s" % body.isValid())
    add("   lid valid               : %s" % lid.isValid())
    add("   body closed (solid)     : %s" % body.isClosed())
    bb = body.BoundBox
    add("   body bbox               : %.2f x %.2f x %.2f"
        % (bb.XLength, bb.YLength, bb.ZLength))
    bb = lid.BoundBox
    add("   lid  bbox               : %.2f x %.2f x %.2f"
        % (bb.XLength, bb.YLength, bb.ZLength))
    add("   body/lid interference    : %.4f mm3" % body.common(lid).Volume)
    add("   build volume (Bambu H2S 340x320x340):")
    add("     body  fits            : %s"
        % (bb_max(body) <= 340.0))
    add("     lid   fits            : %s"
        % (max(lid.BoundBox.XLength, lid.BoundBox.YLength, lid.BoundBox.ZLength) <= 340.0))
    add("   lid-screw insert bores - material around the O%.1f bore:"
        % LID_INSERT_DIA)
    for sx in (-1, 1):
        for zz in LID_SCREW_Z:
            ds = ring_depths(body, sx * LID_SCREW_X, zz, radius=3.4, n=6,
                             y_top=REAR_H, max_d=LID_INSERT_D + 3.0)
            ok = "OK" if min(ds) >= LID_INSERT_D else "TOO SHALLOW"
            add("     X=%+7.1f Z=%6.1f : min %.1f mm / max %.1f mm  -> %s"
                % (sx * LID_SCREW_X, zz, min(ds), max(ds), ok))
    add("   cable egress slot through the left wall:")
    cy, cz = CABLE_SLOT_C
    sh, sz = CABLE_SLOT_SZ
    for yy in (cy - sh / 2.0 + 2.0, cy, cy + sh / 2.0 - 2.0):
        probe = Part.makeSphere(1.2, Vector(-XW + WALL / 2.0, yy, cz))
        frac = probe.common(body).Volume / probe.Volume
        add("     Y=%5.1f Z=%6.1f : %.0f%% inside solid  -> %s"
            % (yy, cz, 100 * frac, "CLEAR" if frac < 0.05 else "BLOCKED"))
    for dz in (-0.5, 0.0, 0.5):
        zz = cz + dz * sz
        d = material_depth(body, -XW + 0.15, zz, y_top=REAR_H,
                           max_d=110.0, step=1.0)
        add("     Z=%6.1f : solid wall from the top face down to Y=%.1f"
            % (zz, REAR_H - d))
    add("")
    add(" NOTES")
    add("   * The 120 mm fan will NOT fit across an 87.8 mm tall cage aperture, so")
    add("     the rear section is taller (%.1f mm outside, %.1f mm inside) than the"
        % (REAR_H, PLEN_Y1))
    add("     bay (%.1f mm) - the extra height is the airflow plenum." % BAY_H)
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

def export(body, lid, log):
    os.makedirs(OUT_DIR, exist_ok=True)

    doc = App.newDocument("dl380_cage_case")
    ob, ol = doc.addObject("Part::Feature", "Case_Body"), \
             doc.addObject("Part::Feature", "Service_Lid")
    ob.Shape, ol.Shape = body, lid
    doc.recompute()

    import Import
    import Mesh

    paths = []
    p_all = os.path.join(OUT_DIR, BASENAME + ".step")
    Import.export([ob, ol], p_all)
    paths.append(p_all)

    for name, shape in (("body", body), ("lid", lid)):
        p = os.path.join(OUT_DIR, "%s_%s.step" % (BASENAME, name))
        shape.exportStep(p)
        paths.append(p)

    for name, obj in (("body", ob), ("lid", ol)):
        p = os.path.join(OUT_DIR, "%s_%s.stl" % (BASENAME, name))
        Mesh.export([obj], p)
        paths.append(p)

    txt = report(body, lid, log)
    p = os.path.join(OUT_DIR, "%s_report.txt" % BASENAME)
    with open(p, "w") as f:
        f.write(txt)
    paths.append(p)

    return paths, txt


# ==============================================================================
# 7. MAIN
# ==============================================================================

def main():
    body, lid, log = build()
    paths, txt = export(body, lid, log)
    print(txt)
    print("FILES:")
    for p in paths:
        print("  %-70s %8d bytes" % (p, os.path.getsize(p)))


if __name__ in ("__main__",                    # python3 dl380_cage_case.py
                os.path.splitext(os.path.basename(__file__))[0]):  # freecadcmd ...
    main()
