#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_print_kit.py - turn the built parts into files a print service can quote
from directly.

    freecadcmd export_print_kit.py

Writes into ./print:

    dl380-case_body.stl / .obj        body, oriented for printing
    dl380-case_lid.stl  / .obj        lid,  oriented for printing
    dl380-case_psu-strap.stl / .obj   PSU strap, oriented for printing
    dl380-case_all-parts.stl / .obj   all three laid out side by side, one file
    README.txt                        manifest to send with the files

WHY THE ORIENTATION MATTERS
    The CAD model uses Y as "up" (the body stands on Y = 0).  Every slicer uses Z
    as up.  Exported raw, the body arrives lying on its back - a 281 mm tall
    thing on the plate - and the lid arrives upside down with its locating lip
    printed in mid air.  So each part is rotated here until the face that should
    sit on the build plate is at Z = 0:

        body   stands on its base        -> rotate +90 deg about X
        lid    plate face down, skirt up -> rotate -90 deg about X
        strap  lies flat                 -> rotate +90 deg about X

    After the rotation each part is translated so its minimum corner is at the
    origin, which is what most slicers and marketplaces expect.
"""

import os
import sys

import FreeCAD as App
import Mesh
import Part
from FreeCAD import Vector

import Import

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "out")
DST = os.path.join(HERE, "print")

RATE = 750.0      # Rp per gram of filament
DENS = 1.27       # PETG, g/cm3
PROFILE = 0.75    # printed mass / solid mass at 3 perimeters and 15% infill

#        name          step file                        up   rot_z
PARTS = [("body",      "dl380_cage_case_body.step",      +1,    0.0),
         ("lid",       "dl380_cage_case_lid.step",       -1,   90.0),
         ("psu-strap", "dl380_cage_case_strap.step",     +1,    0.0)]

PLATE = (340.0, 320.0)   # Bambu Lab H2S; the combined file is laid out to fit it
GAP = 10.0

TITLE = "DL380 drive-cage enclosure - print kit"

NOTES = """\
WHAT THIS IS
  Three printed parts for an external enclosure that turns an HP ProLiant DL380
  G6/G7 8-bay 2.5" SFF drive cage (with backplane) into a standalone, fan-cooled
  JBOD box.  Fan, PicoPSU, grille, cable exits and DC jack all live in the body.
  Slide-and-click lid and snap-fit PSU strap mean 100% screwless enclosure assembly.

UNITS
  Millimetres.  STL and OBJ carry no units, so please import as mm.

FILES
  dl380-case_body.stl / .obj        x1   the main part
  dl380-case_lid.stl  / .obj        x1   toolless slide-and-click cover
  dl380-case_psu-strap.stl / .obj   x1   small snap-fit retaining strap
  dl380-case_all-parts.stl / .obj   x1   the same three solids in one file,
                                         already laid out side by side for the
                                         plate.  Use this if you prefer a single
                                         file for the whole job.

ORIENTATION
  Every file is already rotated so the face that should sit on the build plate
  is at Z = 0, and each part's minimum X and Y are at 0.  No reorientation and
  no re-arranging is needed - they can be sliced as they arrive.

SUPPORTS
  None required.  The parts are designed to print unsupported: the internal 45
  degree gussets carry the roof, and the exhaust grille is punched through a
  3 mm membrane rather than the full wall.

SUGGESTED SETTINGS
  Material          PETG (the plenum sees warm server air)
  Layer height      0.2 mm
  Perimeters        3
  Infill            15%
  Top/bottom        4-5 layers
  Nozzle            0.4 mm - do not go larger.  The grille webs are 1.2 mm, i.e.
                    three 0.4 mm lines, and a bigger nozzle would close them up.

WEIGHT AND COST  (PETG at 1.27 g/cm3)
  Solid (100% infill, upper bound)  : {SOLID}
  Printed (3 perimeters, 15% infill): {PRINTED}

  Please quote from your own slice of these files.  The solid figure is the CAD
  volume and is the absolute ceiling; the printed figure assumes 3 perimeters and
  15% infill, which is where this part actually lands because 71% of its volume
  is wall rather than infill.
"""


def load(step):
    before = set(o.Name for o in App.ActiveDocument.Objects) if App.ActiveDocument else set()
    Import.insert(step, os.path.basename(step))
    found = {}
    for o in App.ActiveDocument.Objects:
        sh = getattr(o, "Shape", None)
        if sh is None:
            continue
        for s in sh.Solids:
            if s.Volume > 0:
                found.setdefault(round(s.Volume), s)
    if not found:
        raise SystemExit("no solids in %s" % step)
    return max(found.values(), key=lambda s: s.Volume)


def orient(shape, up, rot_z=0.0):
    """Rotate so the print-up face points along +Z, then sit it on Z = 0."""
    rotated = shape.rotate(Vector(0, 0, 0), Vector(1, 0, 0), 90.0 if up > 0 else -90.0)
    if rot_z:
        rotated = rotated.rotate(Vector(0, 0, 0), Vector(0, 0, 1), rot_z)
    bb = rotated.BoundBox
    return rotated.translate(Vector(-bb.XMin, -bb.YMin, -bb.ZMin))


def place(shape, dx, dy):
    return shape.translate(Vector(dx, dy, 0.0))


def main():
    App.newDocument("printkit")
    os.makedirs(DST, exist_ok=True)

    # one document and one object, reused for every export - creating a fresh
    # document per file makes FreeCAD spew a recompute progress bar per export
    doc = App.newDocument("emit")
    ob = doc.addObject("Part::Feature", "part")

    def emit(shape, name):
        ob.Shape = shape
        written = []
        for ext in ("stl", "obj"):
            p = os.path.join(DST, "dl380-case_%s.%s" % (name, ext))
            Mesh.export([ob], p)
            written.append(p)
        return written

    oriented, rows, out = {}, [], []
    for name, step, up, rot_z in PARTS:
        shape = orient(load(os.path.join(SRC, step)), up, rot_z)
        oriented[name] = shape
        bb = shape.BoundBox
        v = shape.Volume / 1000.0
        tris = len(Mesh.Mesh(shape.tessellate(0.1)).Facets)
        rows.append((name, v, tris, bb))
        out.extend(emit(shape, name))

    # Everything in one file: the body down the left, the lid and the strap
    # stacked to its right.  The lid is rotated 90 deg so its long dimension (211.7 mm)
    # runs along Y, fitting alongside the body (208.4 mm X + 10 mm GAP + 92.2 mm X = 310.6 mm <= 340 mm).
    bw = oriented["body"].BoundBox.XLength
    lh = oriented["lid"].BoundBox.YLength
    offsets = {"body": (0.0, 0.0),
               "lid": (bw + GAP, 0.0),
               "psu-strap": (bw + GAP, lh + GAP)}
    combo = None
    for name, step, up, rot_z in PARTS:
        s = place(oriented[name], offsets[name][0], offsets[name][1])
        combo = s if combo is None else combo.fuse(s)
    out.extend(emit(combo, "all-parts"))

    # manifest
    def rp(v):
        return format(int(round(v)), ",").replace(",", ".")

    lines = []
    add = lines.append
    add(TITLE)
    add("=" * len(TITLE))
    add("")
    add("%-12s %10s %8s %9s %13s %24s %9s"
        % ("part", "volume", "solid", "printed", "cost @ 750/g", "bbox (mm)", "triangles"))
    add("-" * 92)
    for name, v, tris, bb in rows:
        add("%-12s %7.1f cm3 %6.0f g %7.0f g  Rp %10s  %6.1f x %6.1f x %5.1f %9d"
            % (name, v, v * DENS, v * DENS * PROFILE,
               rp(v * DENS * PROFILE * RATE),
               bb.XLength, bb.YLength, bb.ZLength, tris))
    add("-" * 92)
    total_solid = sum(r[1] for r in rows)
    add("%-12s %7.1f cm3 %6.0f g %7.0f g  Rp %10s"
        % ("TOTAL", total_solid, total_solid * DENS, total_solid * DENS * PROFILE,
           rp(total_solid * DENS * PROFILE * RATE)))
    add("")
    cb = combo.BoundBox
    fits = cb.XLength <= PLATE[0] and cb.YLength <= PLATE[1]
    add("The combined file lays all three out in %.1f x %.1f x %.1f mm - %s."
        % (cb.XLength, cb.YLength, cb.ZLength,
           "fits a %.0f x %.0f plate" % PLATE if fits
           else "CHECK THIS AGAINST YOUR BUILD VOLUME"))
    add("")
    add(NOTES.replace("{SOLID}", "%5.0f g   Rp %s" % (total_solid * DENS,
                                                      rp(total_solid * DENS * RATE)))
             .replace("{PRINTED}", "%5.0f g   Rp %s" % (total_solid * DENS * PROFILE,
                                                        rp(total_solid * DENS * PROFILE * RATE))))
    path = os.path.join(DST, "README.txt")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")

    print("wrote into %s:" % DST)
    for p in out + [path]:
        print("  %-34s %9d bytes" % (os.path.basename(p), os.path.getsize(p)))
    print("")
    print("\n".join(lines[:13]))


if __name__ in ("__main__",
                os.path.splitext(os.path.basename(__file__))[0]):
    main()
