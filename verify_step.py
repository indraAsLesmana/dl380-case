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
_DEFAULT = os.path.join(HERE, "out", "dl380_cage_case_body.step")
# NB: under freecadcmd sys.argv[1] is the script name itself, so only accept an
# argument that actually looks like a STEP file.
_arg = sys.argv[1] if len(sys.argv) > 1 else ""
STEP = _arg if _arg.lower().endswith((".step", ".stp")) else _DEFAULT

# ---- geometry constants, mirrored from dl380_cage_case.py -------------------
INT_H, INT_W = 87.8, 145.8
FLOOR_T, WALL = 4.0, 2.8
CAGE_D, PLENUM_D, REAR_WALL_T = 165.0, 100.0, 8.4

FAN_SIZE, FAN_APERTURE, FAN_PATTERN, FAN_INNER_CLEAR = 92.0, 86.0, 82.5, 2.0
INT_H_PLEN = max(INT_H, FAN_SIZE + 2 * FAN_INNER_CLEAR)
REAR_H = FLOOR_T + INT_H_PLEN + WALL                      # 102.8
PLEN_Y1 = REAR_H - WALL                                   # 100.0
FAN_R = FAN_APERTURE / 2.0                                # 43.0
FAN_OFF = FAN_PATTERN / 2.0                               # 41.25
FAN_CY = (FLOOR_T + PLEN_Y1) / 2.0                        # 52.0

XW = (INT_W + 2 * WALL) / 2.0                             # 75.7
XI = INT_W / 2.0                                          # 72.9
Z_BAY = CAGE_D                                            # 165.0
Z_RIN = CAGE_D + PLENUM_D                                 # 265.0
ZW = Z_RIN + REAR_WALL_T / 2.0                            # mid rear-wall

GRILLE_CELL, GRILLE_WEB, GRILLE_RIM = 9.0, 1.2, 2.0
GRILLE_POCKET_R = FAN_R + GRILLE_RIM                      # 45.0
GUSSET_H = 18.0
SVC_HALF = XI - GUSSET_H                                  # 54.9
LID_SCREW_X, LID_SCREW_Z = 70.0, 185.0
REAR_CABLE_SLOT_X, REAR_CABLE_SLOT_Y = -60.0, (33.0, 50.0)
REAR_CABLE_SLOT_W, REAR_CABLE_SLOT_H = 17.0, 12.0

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
    ("plenum  fan bay",           (0.0, FAN_CY, 200.0),             "void"),
    ("plenum  clear volume",      (0.0, 30.0, 200.0),               "void"),
    ("roof material  (gusset)",   (71.5, PLEN_Y1 + 1.5, 200.0),     "solid"),
    ("top service opening",       (0.0, REAR_H - 1.0, 215.0),       "void"),
    ("lid insert bore",           (LID_SCREW_X, REAR_H - 4.6, LID_SCREW_Z), "void"),
    ("bay interior",              (0.0, FLOOR_T + INT_H / 2.0, 100.0), "void"),
    ("bay side wall",             (XI + WALL / 2.0, FLOOR_T + INT_H / 2.0, 100.0),
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
]


def load(path):
    Import = __import__("Import")
    Import.insert(path, "verify")
    shapes = [o.Shape for o in App.ActiveDocument.Objects
              if hasattr(o, "Shape") and o.Shape.Volume > 0]
    if not shapes:
        raise SystemExit("no solids found in %s" % path)
    return max(shapes, key=lambda s: s.Volume)


def main():
    if not os.path.exists(STEP):
        raise SystemExit("missing %s - run dl380_cage_case.py first" % STEP)

    body = load(STEP)
    print("probing %s" % STEP)
    print("  solid: valid=%s closed=%s volume=%.0f mm3"
          % (body.isValid(), body.isClosed(), body.Volume))
    print("")
    print("  %-26s %-7s %8s  %s" % ("feature", "expect", "inside", "verdict"))
    print("  " + "-" * 62)

    failures = 0
    for name, (x, y, z), want in CASES:
        s = Part.makeSphere(1.0, Vector(x, y, z))
        frac = s.common(body).Volume / s.Volume
        ok = frac < 0.05 if want == "void" else frac > 0.95
        failures += 0 if ok else 1
        print("  %-26s %-7s %7.0f%%  %s"
              % (name, want, frac * 100, "OK" if ok else "*** FAIL ***"))

    print("  " + "-" * 62)
    print("  %d probes, %d failures" % (len(CASES), failures))
    return 1 if failures else 0


if __name__ in ("__main__",                    # python3 verify_step.py
                os.path.splitext(os.path.basename(__file__))[0]):  # freecadcmd ...
    _rc = main()
    if _rc:
        raise SystemExit(_rc)
