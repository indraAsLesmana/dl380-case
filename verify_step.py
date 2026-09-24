#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_step.py - probe the EXPORTED STEP file and confirm every feature is
open where it should be open and solid where it should be solid.

This deliberately re-reads the exported geometry rather than the in-memory
shape, so it also proves the STEP round-trip did not lose or merge features.

    freecadcmd verify_step.py [path/to/part.step]

Exits non-zero if any probe fails, so it is usable as a commit gate.
"""

import math
import os
import sys

import FreeCAD as App
import Part
from FreeCAD import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
_DEFAULT = os.path.join(HERE, "out", "dl380_cage_case.step")
# NB: under freecadcmd sys.argv[1] is the script name itself, so only accept an
# argument that actually looks like a STEP file.
_arg = sys.argv[1] if len(sys.argv) > 1 else ""
STEP = _arg if _arg.lower().endswith((".step", ".stp")) else _DEFAULT

# ---- geometry constants, mirrored from dl380_cage_case.py -------------------
INT_H, INT_W = 87.8, 145.8
FLOOR_T, WALL = 4.0, 2.8
CAGE_D, PLENUM_D, REAR_WALL_T = 165.0, 80.0, 8.4

FAN_SIZE, FAN_APERTURE, FAN_PATTERN, FAN_INNER_CLEAR = 92.0, 86.0, 82.5, 2.0
INT_H_PLEN = max(INT_H, FAN_SIZE + 2 * FAN_INNER_CLEAR)
REAR_H = FLOOR_T + INT_H_PLEN + WALL                      # 102.8
PLEN_Y1 = REAR_H - WALL                                   # 100.0
FAN_R = FAN_APERTURE / 2.0                                # 43.0
FAN_OFF = FAN_PATTERN / 2.0                               # 41.25
FAN_TOP = FLOOR_T + FAN_SIZE                              # 96.0
FAN_CY = FLOOR_T + FAN_SIZE / 2.0                         # 50.0 - seats on floor

# fan housing
FAN_GUIDE_CLEAR, FAN_GUIDE_T, FAN_GUIDE_H = 0.2, 3.0, 42.0
FAN_LID_GAP = 1.0
GUIDE_X = FAN_SIZE / 2.0 + FAN_GUIDE_CLEAR                # 46.2 rail inner face
GUIDE_XC = GUIDE_X + FAN_GUIDE_T / 2.0                    # rail mid-thickness
LID_FIN_Y0 = FAN_TOP + FAN_LID_GAP                        # 97.0 fin bottom
PLEN_INT_W = 200.0
PLEN_OUT_W = PLEN_INT_W + 2 * WALL                        # 205.6
PLEN_XI = PLEN_INT_W / 2.0                                # 100.0
PLEN_XW = PLEN_OUT_W / 2.0                                # 102.8
XW = PLEN_XW                                              # 102.8 (uniform outer half width)
XI = INT_W / 2.0                                          # 72.9
CAGE_RAIL_H, CAGE_RAIL_W = 14.0, 4.0
CAGE_TOP_RIB_H, CAGE_TOP_RIB_W = 5.0, 4.0

Z_BAY = CAGE_D                                            # 165.0
Z_RIN = CAGE_D + PLENUM_D                                 # 245.0
Z_OUT = Z_RIN + REAR_WALL_T                               # 253.4
ZW = Z_RIN + REAR_WALL_T / 2.0                            # mid rear-wall

GRILLE_CELL, GRILLE_WEB, GRILLE_RIM = 9.0, 1.2, 2.0
GRILLE_POCKET_R = FAN_R + GRILLE_RIM                      # 45.0
FILLET_R = 1.4
GUSSET_H = 18.0
SVC_HALF = PLEN_XI - GUSSET_H                             # 82.0
REAR_CABLE_SLOT_X, REAR_CABLE_SLOT_Y = -70.0, (33.0, 50.0)
REAR_CABLE_SLOT_W, REAR_CABLE_SLOT_H = 17.0, 12.0

# PicoPSU cradle (transverse orientation, shifted right)
PSU_W, PSU_L, PSU_H = 31.0, 44.0, 21.0
PSU_CLEAR, PSU_BOOT, PSU_PLINTH_T = 0.8, 12.0, 3.0
PSU_WALL_H, PSU_FRONT_LIP = 24.0, 6.0
PSU_BOSS_W, PSU_BOSS_L = 6.0, 14.0
PSU_TOOTH_W = 0.8
PSU_CX = 40.0
PSU_XH = (PSU_L + 2 * PSU_CLEAR) / 2.0                    # 22.8
PSU_ZH = (PSU_W + 2 * PSU_CLEAR) / 2.0                    # 16.3
PSU_Z0 = Z_BAY + PSU_BOOT                                 # 177.0
PSU_Z1 = PSU_Z0 + 2 * PSU_ZH                              # 209.6
PSU_TRAY_OH = PSU_XH + WALL                               # 25.6
PSU_TOP = FLOOR_T + PSU_PLINTH_T + PSU_H + 0.4            # 28.4
PSU_BOSS_X = PSU_XH + (WALL + PSU_BOSS_W) / 2.0           # 27.2
PSU_BORE_Z = (PSU_Z0 + PSU_Z1) / 2.0                      # 193.3

# DC input jack
DC_JACK_X, DC_JACK_Y = 70.0, 52.0
DC_JACK_DIA, DC_JACK_PAD, DC_JACK_DEPTH = 8.0, 16.0, 5.0

# slide-and-click housing lid
SLIDE_CLEAR = 0.25
RAIL_W, RAIL_H, RAIL_YC = 1.4, 2.4, 98.0
SKIRT_T, SKIRT_D = 2.8, 10.0
LID_T = 3.0
FAN_INSET = 25.0
FAN_Z0 = Z_RIN - FAN_INSET                                # 220.0
FAN_TOP = FAN_CY + FAN_SIZE / 2.0                         # 96.0
LID_FRONT_T = 2.4
LID_Z0 = Z_BAY - LID_FRONT_T                              # 162.6
LID_Z1 = Z_OUT                                            # 253.4
LID_OX = PLEN_XW + SLIDE_CLEAR + SKIRT_T                  # 105.85
RAIL_Z0 = Z_BAY + 1.5

# the first honeycomb cell sits on the fan axis; the next column is offset
_GR = (GRILLE_CELL + GRILLE_WEB) / math.sqrt(3.0)
CELL2 = (1.5 * _GR, FAN_CY + math.sqrt(3.0) * _GR / 2.0)

CASES = [
    # name                        (x,   y,    z)                     expect
    ("grille cell centre",        (0.0, FAN_CY, ZW),                "void"),
    ("grille cell next column",   (CELL2[0], CELL2[1], ZW),         "void"),
    ("rear wall above pocket",    (0.0, FAN_CY + 47.0, ZW),         "solid"),
    ("rear wall below pocket",    (0.0, FAN_CY - 47.0, ZW),         "solid"),
    ("fan hole  top-right",       (FAN_OFF, FAN_CY + FAN_OFF, ZW),  "void"),
    ("fan hole  bottom-right",    (FAN_OFF, FAN_CY - FAN_OFF, ZW),  "void"),
    ("fan hole  top-left",        (-FAN_OFF, FAN_CY + FAN_OFF, ZW), "void"),
    ("fan hole  bottom-left",     (-FAN_OFF, FAN_CY - FAN_OFF, ZW), "void"),
    ("plenum  fan bay",           (0.0, FAN_CY, 230.0),             "void"),
    ("plenum  clear volume",      (0.0, 60.0, 200.0),               "void"),
    ("fan housing, rail right",   (GUIDE_XC, 20.0, FAN_Z0 + 12.0),  "solid"),
    ("fan housing, rail left",    (-GUIDE_XC, 20.0, FAN_Z0 + 12.0), "solid"),
    ("fan housing, front rail right low", (GUIDE_XC, 10.0, FAN_Z0 - 1.5), "solid"),
    ("fan housing, front rail right tall", (GUIDE_XC, 70.0, FAN_Z0 - 1.5), "solid"),
    ("fan housing, front rail left low", (-GUIDE_XC, 10.0, FAN_Z0 - 1.5), "solid"),
    ("fan housing, front rail left tall", (-GUIDE_XC, 70.0, FAN_Z0 - 1.5), "solid"),
    ("fan housing, slot is clear", (0.0, FAN_CY, FAN_Z0 + 12.0),    "void"),
    ("in front of the housing",   (0.0, FAN_CY, FAN_Z0 - 5.0),      "void"),
    ("cradle interior",           (PSU_CX, FLOOR_T + 11.0, PSU_BORE_Z), "void"),
    ("cradle interior  corner",   (PSU_CX + PSU_XH - 3.0, PSU_TOP - 2.0, PSU_Z1 - 2.0), "void"),
    ("cradle plinth",             (PSU_CX, FLOOR_T + 1.5, PSU_BORE_Z), "solid"),
    ("cradle side wall",          (PSU_CX + PSU_XH + WALL / 2.0, 15.0, PSU_BORE_Z), "solid"),
    ("cradle rear wall",          (PSU_CX, 15.0, PSU_Z1 + WALL / 2.0), "solid"),
    ("cradle front lip",          (PSU_CX, FLOOR_T + 1.0, PSU_Z0 - WALL / 2.0),
                                                                     "solid"),
    ("strap boss ridge",          (PSU_CX + PSU_TRAY_OH + PSU_BOSS_W + PSU_TOOTH_W / 2.0,
                                   PSU_TOP - 1.8, PSU_BORE_Z),       "solid", 0.3),
    ("strap boss material",       (PSU_CX + PSU_BOSS_X, FLOOR_T + 2.0, PSU_BORE_Z),
                                                                     "solid"),
    ("DC jack hole",              (DC_JACK_X, DC_JACK_Y, ZW),       "void"),
    ("DC jack counterbore",       (DC_JACK_X, DC_JACK_Y, Z_OUT - DC_JACK_DEPTH / 2.0),
                                                                     "void"),
    ("rear wall beside jack",     (GRILLE_POCKET_R + 3.0, FAN_CY, ZW), "solid"),
    ("roof material  (gusset)",   (PLEN_XI - 1.5, PLEN_Y1 + 1.5, 200.0), "solid"),
    ("top service opening",       (0.0, REAR_H - 1.0, 200.0),       "void"),
    ("slide rail right",          (PLEN_XW + RAIL_W / 2.0, RAIL_YC, 200.0), "solid", 0.4),
    ("slide rail left",           (-(PLEN_XW + RAIL_W / 2.0), RAIL_YC, 200.0), "solid", 0.4),
    ("catch pocket",              (0.0, RAIL_YC, Z_BAY + 0.5),      "void"),
    ("bay interior",              (0.0, FLOOR_T + INT_H / 2.0, 100.0), "void"),
    ("bay outer wall (front frame)", (XW - WALL / 2.0, FLOOR_T + INT_H / 2.0, 10.0),
                                                                     "solid"),
    ("bay right wall net opening", (XW - WALL / 2.0, 47.9, 83.0),   "void"),
    ("bay left wall net opening",  (-(XW - WALL / 2.0), 47.9, 83.0), "void"),
    ("bay roof net opening",       (0.0, FLOOR_T + INT_H + WALL / 2.0, 83.0), "void"),
    ("cage bottom rail right",    (XI + CAGE_RAIL_W / 2.0, FLOOR_T + 5.0, 100.0),
                                                                     "solid"),
    ("cage bottom rail left",     (-(XI + CAGE_RAIL_W / 2.0), FLOOR_T + 5.0, 100.0),
                                                                     "solid"),
    ("cage top rib right",        (XI + CAGE_TOP_RIB_W / 2.0, FLOOR_T + INT_H - 2.5, 100.0),
                                                                     "solid"),
    ("cage top rib left",         (-(XI + CAGE_TOP_RIB_W / 2.0), FLOOR_T + INT_H - 2.5, 100.0),
                                                                     "solid"),
    ("bay side chamber left",     (-(XI + 12.0), FLOOR_T + INT_H / 2.0, 100.0),
                                                                     "void"),
    ("bay front cheek left",      (-(XI + 12.0), FLOOR_T + INT_H / 2.0, WALL / 2.0),
                                                                     "solid"),
    ("bay front cheek right",     (XI + 12.0, FLOOR_T + INT_H / 2.0, WALL / 2.0),
                                                                     "solid"),
    ("rear cable slot  1",        (REAR_CABLE_SLOT_X, REAR_CABLE_SLOT_Y[0], ZW),
                                                                     "void"),
    ("rear cable slot  2",        (REAR_CABLE_SLOT_X, REAR_CABLE_SLOT_Y[1], ZW),
                                                                     "void"),
    ("web between slots",         (REAR_CABLE_SLOT_X,
                                   (REAR_CABLE_SLOT_Y[0] + REAR_CABLE_SLOT_Y[1]) / 2.0,
                                   ZW),                              "solid"),
    ("web slot <-> grille",       (-(GRILLE_POCKET_R + 3.0), FAN_CY, ZW), "solid"),
    ("rear stop frame rib",       (0.0, FLOOR_T + 2.0, Z_BAY - 1.5), "solid"),
    ("floor material",            (0.0, 2.0, 100.0),                 "solid"),
    ("rubber foot recess",        (61.0, 1.0, 14.0),                 "void"),
    # edge rounding: a point 0.35 mm in from the sharp corner along the diagonal
    # is removed by a R1.4 round, and would be solid without one
    ("fillets  corner removed",   (PLEN_XW - 0.35 / math.sqrt(2.0),
                                   FAN_CY, Z_OUT - 0.35 / math.sqrt(2.0)),
                                                                     "void", 0.15),
    ("fillets  wall kept",        (PLEN_XW - 1.7, FAN_CY, Z_OUT - 2.4), "solid"),
]

# ---- probes against the LID (loaded as the second-largest solid) -------------
#  Probe radii matter here: the lip is only 1.5 mm deep and the skirt 2.8 mm
#  thick, so the default 1.0 mm sphere will not fit in either.
LID_CASES = [
    ("plate material",            (0.0, REAR_H + LID_T / 2.0, 200.0), "solid"),
    ("skirt, right wall",         (PLEN_XW + SLIDE_CLEAR + SKIRT_T / 2.0, 95.0, 200.0),
                                                                     "solid"),
    ("skirt, left wall",          (-(PLEN_XW + SLIDE_CLEAR + SKIRT_T / 2.0), 95.0, 200.0),
                                                                     "solid"),
    ("runner, right skirt",       (PLEN_XW + SLIDE_CLEAR + 0.6, 94.2, 200.0), "solid", 0.4),
    ("runner, left skirt",        (-(PLEN_XW + SLIDE_CLEAR + 0.6), 94.2, 200.0), "solid", 0.4),
    ("skirt, front wall",         (0.0, 98.0, LID_Z0 + 1.0),         "solid"),
    ("lid clear of the case wall", (PLEN_XW - 1.2, 95.0, 200.0),    "void"),
    ("front skirt stops at roof", (0.0, 92.0, LID_Z0 + 1.0),         "void"),
    ("front cantilever latch",    (0.0, RAIL_YC, Z_BAY - 1.0),       "solid"),
    ("lip ends before the fan",   (0.0, REAR_H - 1.0, 230.0),        "void", 0.5),
    ("open over the fan",         (0.0, REAR_H - 1.0, FAN_Z0 + 10.0),
                                                                     "void", 0.5),
    ("fan retainer fin",          (GUIDE_XC, LID_FIN_Y0 + 2.0, FAN_Z0 + 12.0),
                                                                     "solid"),
    ("clearance under the fin",   (GUIDE_XC, FAN_TOP - 1.0, FAN_Z0 + 12.0), "void"),
    ("latch snap tooth",          (0.0, RAIL_YC, Z_BAY + 0.6),       "solid", 0.4),
]


def load_all(path):
    """Every distinct solid in the file, largest first.

    Import.insert() can hand back both a compound holding all the solids and the
    individual solids, which double-counts them - so flatten to solids and dedupe
    by volume rather than trusting the document's object list.
    """
    Import = __import__("Import")
    Import.insert(path, "verify")
    found = {}
    for o in App.ActiveDocument.Objects:
        sh = getattr(o, "Shape", None)
        if sh is None:
            continue
        for s in sh.Solids:
            if s.Volume > 0.0:
                found.setdefault(round(s.Volume), s)
    if not found:
        raise SystemExit("no solids found in %s" % path)
    return sorted(found.values(), key=lambda s: -s.Volume)


def run_table(title, solid, cases):
    print("  %s" % title)
    print("  %-26s %-7s %8s  %s" % ("feature", "expect", "inside", "verdict"))
    print("  " + "-" * 62)
    failures = 0
    for case in cases:
        name, (x, y, z), want = case[0], case[1], case[2]
        probe_r = case[3] if len(case) > 3 else 1.0
        s = Part.makeSphere(probe_r, Vector(x, y, z))
        frac = s.common(solid).Volume / s.Volume
        ok = frac < 0.05 if want == "void" else frac > 0.95
        failures += 0 if ok else 1
        print("  %-26s %-7s %7.0f%%  %s"
              % (name, want, frac * 100, "OK" if ok else "*** FAIL ***"))
    return failures


def main():
    if not os.path.exists(STEP):
        raise SystemExit("missing %s - run dl380_cage_case.py first" % STEP)

    solids = load_all(STEP)
    print("probing %s" % STEP)
    for i, s in enumerate(solids):
        bb = s.BoundBox
        print("  solid %d: valid=%s closed=%s volume=%8.0f mm3  bbox %.1f x %.1f x %.1f"
              % (i, s.isValid(), s.isClosed(), s.Volume,
                 bb.XLength, bb.YLength, bb.ZLength))
    if len(solids) < 2:
        print("  (only one solid found - the lid probes are being skipped)")
    print("")

    total = len(CASES)
    failures = run_table("BODY", solids[0], CASES)
    if len(solids) > 1:
        print("  " + "-" * 62)
        total += len(LID_CASES)
        failures += run_table("LID", solids[1], LID_CASES)
    print("  " + "-" * 62)
    print("  %d probes, %d failures" % (total, failures))
    return 1 if failures else 0


if __name__ in ("__main__",                    # python3 verify_step.py
                os.path.splitext(os.path.basename(__file__))[0]):  # freecadcmd ...
    _rc = main()
    # flush BEFORE raising: an uncaught SystemExit tears the process down and
    # discards whatever is still sitting in the stdout buffer, so a failing run
    # would exit non-zero with no output at all - exactly when you need it.
    sys.stdout.flush()
    sys.stderr.flush()
    if _rc:
        raise SystemExit(_rc)
