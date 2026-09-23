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
CAGE_D, PLENUM_D, REAR_WALL_T = 165.0, 65.0, 8.4
REAR_H = INT_H + FLOOR_T + WALL                  # 94.6
BAY_YC = FLOOR_T + INT_H / 2.0                   # 47.9
FAN_APERTURE, FAN_PATTERN = 86.0, 82.5
FAN_CY = REAR_H / 2.0                            # 47.3
FAN_OFF = FAN_PATTERN / 2.0                      # 41.25
XW = (INT_W + 2 * WALL) / 2.0                    # 75.7
XI = INT_W / 2.0                                 # 72.9
Z_BAY = CAGE_D
Z_RIN = CAGE_D + PLENUM_D                        # 230.0
ZW = Z_RIN + REAR_WALL_T / 2.0                   # mid rear-wall thickness
FAN_CABLE_SLOT = (55.0, 14.0)                    # X, Y
SVC_Z = (174.0 + 222.0) / 2.0                    # service opening, mid Z
LID_SCREW_X, LID_SCREW_Z = 68.0, 185.0
CABLE_SLOT = (-XW + WALL / 2.0, 20.0, 213.0)     # left wall, mid thickness

CASES = [
    # name                       (x,   y,    z)                expect
    ("fan cable notch",           (FAN_CABLE_SLOT[0], FAN_CABLE_SLOT[1], ZW), "void"),
    ("fan aperture",              (0.0, FAN_CY, ZW),                          "void"),
    ("fan hole  top-right",       (FAN_OFF, FAN_CY + FAN_OFF, ZW),            "void"),
    ("fan hole  bottom-right",    (FAN_OFF, FAN_CY - FAN_OFF, ZW),            "void"),
    ("fan hole  top-left",        (-FAN_OFF, FAN_CY + FAN_OFF, ZW),           "void"),
    ("fan hole  bottom-left",     (-FAN_OFF, FAN_CY - FAN_OFF, ZW),           "void"),
    ("web  notch <-> aperture",   (40.0, 14.0, ZW),                           "solid"),
    ("rear wall  outboard",       (70.0, 70.0, ZW),                           "solid"),
    ("rear wall  above the vent", (0.0, REAR_H - 2.6, ZW),                    "solid"),
    ("rear wall  below the vent", (0.0, 2.6, ZW),                             "solid"),
    ("top service opening",       (0.0, REAR_H - 1.1, SVC_Z),                 "void"),
    ("lid insert bore",           (LID_SCREW_X, REAR_H - 4.6, LID_SCREW_Z),   "void"),
    ("bay interior",              (0.0, BAY_YC, 100.0),                       "void"),
    ("bay side wall",             (XI + WALL / 2.0, BAY_YC, 100.0),           "solid"),
    ("side wall cable slot",      CABLE_SLOT,                                 "void"),
    ("rear stop frame rib",       (0.0, FLOOR_T + 2.0, Z_BAY - 1.5),          "solid"),
    ("floor material",            (0.0, 2.0, 100.0),                          "solid"),
    ("rubber foot recess",        (61.0, 1.0, 14.0),                          "void"),
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
    print("  %-24s %-7s %8s  %s" % ("feature", "expect", "inside", "verdict"))
    print("  " + "-" * 60)

    failures = 0
    for name, (x, y, z), want in CASES:
        s = Part.makeSphere(1.0, Vector(x, y, z))
        frac = s.common(body).Volume / s.Volume
        ok = frac < 0.05 if want == "void" else frac > 0.95
        failures += 0 if ok else 1
        print("  %-24s %-7s %7.0f%%  %s"
              % (name, want, frac * 100, "OK" if ok else "*** FAIL ***"))

    print("  " + "-" * 60)
    print("  %d probes, %d failures" % (len(CASES), failures))
    return 1 if failures else 0


if __name__ in ("__main__",                    # python3 verify_step.py
                os.path.splitext(os.path.basename(__file__))[0]):  # freecadcmd ...
    _rc = main()
    if _rc:
        raise SystemExit(_rc)
