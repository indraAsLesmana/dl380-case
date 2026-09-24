DL380 drive-cage enclosure - print kit
======================================

part             volume    solid   printed  cost @ 750/g                bbox (mm) triangles
--------------------------------------------------------------------------------------------
body           532.6 cm3    676 g     507 g  Rp    380.508   154.2 x  281.4 x 102.8     30116
lid             64.6 cm3     82 g      62 g  Rp     46.151   157.5 x  120.2 x  13.0       176
psu-strap        5.0 cm3      6 g       5 g  Rp      3.595    56.2 x   20.0 x  10.0        60
--------------------------------------------------------------------------------------------
TOTAL          602.3 cm3    765 g     574 g  Rp    430.254

The combined file lays all three out in 321.7 x 281.4 x 102.8 mm - fits a 340 x 320 plate.

WHAT THIS IS
  Three printed parts for an external enclosure that turns an HP ProLiant DL380
  G6/G7 8-bay 2.5" SFF drive cage (with backplane) into a standalone, fan-cooled
  JBOD box.  Fan, PicoPSU, grille, cable exits and DC jack all live in the body.

UNITS
  Millimetres.  STL and OBJ carry no units, so please import as mm.

FILES
  dl380-case_body.stl / .obj        x1   the main part
  dl380-case_lid.stl  / .obj        x1   drop-on cover for the body
  dl380-case_psu-strap.stl / .obj   x1   small retaining strap
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
  Solid (100% infill, upper bound)  :   765 g   Rp 573.672
  Printed (3 perimeters, 15% infill):   574 g   Rp 430.254

  Please quote from your own slice of these files.  The solid figure is the CAD
  volume and is the absolute ceiling; the printed figure assumes 3 perimeters and
  15% infill, which is where this part actually lands because 71% of its volume
  is wall rather than infill.

