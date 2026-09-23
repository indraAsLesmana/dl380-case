# DL380 Case — desktop enclosure for an HP ProLiant DL380 G6/G7 8-bay 2.5" SFF drive cage

Parametric [FreeCAD](https://www.freecad.org/) Python model of an external desktop
enclosure that turns a salvaged **HP ProLiant DL380 G6/G7 8-bay 2.5" SFF drive cage
with backplane** (cage assy P/N 496074-001 and relatives) into a standalone,
fan-cooled JBOD-style box with its own internal **PicoPSU**.

Everything — body, lid and PicoPSU strap — is generated from one script. Change a
number at the top, re-run, get a new STEP file. The rear section height is derived
from the fan, so swapping fan size re-shapes the enclosure by itself.

![front](out/body_front.png)
![cutaway](out/body_cut.png)
![rear](out/body_rear.png)

**Building it? → [INSTALL.md](INSTALL.md)** — step-by-step assembly, including how
the drive cage goes in and the order the internals have to be fitted.

---

## Status

| | |
|---|---|
| Shell | `freecadcmd dl380_cage_case.py` builds and exports clean, no errors |
| Body solid | valid ✓ closed ✓ **151.40 × 102.80 × 281.40 mm** |
| Lid solid | valid ✓ closed ✓ **157.40 × 17.00 × 122.00 mm** — a skirted housing |
| Strap solid | valid ✓ closed ✓ 50.20 × 4.00 × 20.00 mm |
| **Lid retention** | **drop-on housing — it stays on with no screws at all** |
| Body ↔ lid interference | 283 mm³ — the skirt bead's deliberate 0.15 mm press fit |
| Body ↔ strap interference | 0.0000 mm³ |
| PicoPSU phantom fit in the cradle | 0.0000 mm³ interference → CLEAR |
| Build volume (Bambu Lab H2S, 340×320×340) | all three fit ✓ |
| Edge treatment | **every outer edge rounded** — body R1.4, lid R1.0, strap R1.4 |
| **Fan housing** | **slides in from the top and needs no screws** — held 4 sides by the case, 5th by the lid |
| All three STL watertight | 34 092 / 31 876 / 10 468 triangles, 0 non-manifold edges ✓ |
| **Re-probed on the exported STEP** | `freecadcmd verify_step.py` → **53 probes, 0 failures** ✓ |

Reports: [`out/dl380_cage_case_report.txt`](out/dl380_cage_case_report.txt) is
written by the build; `verify_step.py` re-reads the exported STEP and probes the
body and the lid separately, so its 53 probes also prove the STEP round-trip lost
nothing.

---

## Target hardware

The cage this was designed around, photographed on the bench:

| Photo | What it shows |
|---|---|
| ![side](docs/reference/cage-side-mounting.png) | Stamped steel cage, side/top mounting holes |
| ![front](docs/reference/cage-front-bezel.png) | Black plastic front bezel, 8 × 2.5" caddy slots |
| ![backplane](docs/reference/cage-rear-backplane.png) | Backplane PCBs and the top mounting rail |

Nominal cage envelope used for the model: **145.0 × 87.0 × 165.0 mm (W × H × D)**.

---

## Design

```
 z=0                                                        z=281.4
 | <---------- 165 bay ---------->|<-20->|<--- cradle --->|<-25 fan->|<-8.4->|
 +================================+======+=================+==========+=======+ y=102.8
 | ^                              | boot |  PicoPSU cradle |   fan    |grille | STEP
 | |                              |      |  strap over it  |  INSIDE  | O90   | UP
 | | HP cage sleeve, wide open    |      |                 |   92     | honey |
 | | 145.8 x 87.8 (+0.4/side)     |      | [] |--board--|  |   frame  | comb  |
 | |                              |      | [] |         |  |          |       |
 | | ### rear stop frame ###       |      |    |         |  |  O86     |       |
 | v                              |      |    |-cables->|  |  field   |       | y=0
 +================================+======+=================+==========+=======+ y=94.6
                                  <--------- 108 plenum ----------> (rear face)
   [] = strap bosses          all of the cradle and fan sits INSIDE the case
```

### Sections

**Bay (z 0 → 165)** — a plain sleeve, internal **145.8 × 87.8 mm**, outer height
94.6 mm. The front is fully open so standard HP 2.5" SFF caddies and their
latch/eject levers slide straight in and out. A **3 mm deep internal stop frame**
around the rear seats the cage; its inner aperture is 137.8 × 79.8 mm, so it stops
the cage without choking the airflow path through the backplane.

**Plenum (z 165 → 273)** — 108 mm deep, laid out front to back:

| Z | What |
|---|---|
| 165 → 185 | 20 mm of cable boot space behind the backplane |
| 185 → 233.4 | the PicoPSU cradle |
| 233.4 → 248 | cable routing |
| 248 → 273 | the fan, against the inside of the rear wall |

**Fan — its own housing, and it needs no screws.** The ARCTIC P9 **slides straight
down into a slot** from the top and seats on the plenum floor, exhausting straight
through the grille. Nothing hangs off the back of the enclosure and the blades are
protected.

| | |
|---|---|
| Slot | Z 248 → 273, straight down from above |
| Seat | the plenum floor — this sets the height, so the screw holes still line up |
| Sides | two guide rails, 42 mm up from the floor, 0.2 mm clearance per side, 1.8 mm lead-in chamfer at the top |
| Behind | the rear wall / grille face |
| Forward | two 16 mm front corner tabs — it cannot tip out |
| Up | **two fins on the lid's underside** reach down to 1 mm above the frame's top edge |

That last row is what makes "no screws" honest: the case holds the fan on four sides
and **the lid holds it on the fifth**. There is nothing to line up and nothing to
drop. The four M3 positions are still cut if you would rather bolt it.

**One thing the rails are not.** They are a *snug* fit, not a press fit — and a press
fit is geometrically impossible here. A rigid slot narrower than the fan frame cannot
be inserted into: the fan just jams at the top. Both cases checked before building
it: at 0.00 mm clearance the fan touches and grips nothing, and at −0.15 mm it cannot
go in at all. So the clearance is what stops it rattling, and it is the tabs plus the
lid fins that hold it. Tune with `FAN_GUIDE_CLEAR` and `FAN_LID_GAP`.

Because the fan seats on the floor, its axis sits at **y = 50** rather than the
plenum's centre at 52, and the grille pocket and all four mounting holes moved down
2 mm with it.

**Honeycomb exhaust grille** — punched through a **3 mm membrane** at the bottom of
a Ø90 × 5.4 mm counterbore in the outer face, not through the full 8.4 mm wall, so
it costs little airflow and the wall stays stiff enough to carry the fan inserts.
55 flat-top hexagonal cells, 9 mm across flats with 1.2 mm webs, **78 % open** across
the field. The cell field is inset from the pocket wall so no cell can break out of
it; the tightest edge margin, pocket to case edge, is **5.8 mm**.

**Rear wall (z 273 → 281.4)** — **8.4 mm** thick (3 × wall). Carries the grille, the
four fan mounting holes, two cable slots and the DC jack.

**Cable egress — out of the back.** Two 17 × 12 mm rounded slots at X = −60,
Y = 33 and 50 take the two SFF-8087 → SFF-8088 leads. Separate slots so each cable
keeps its own strain relief instead of two cables sawing against each other in one
hole. 6.54 mm from the slot corners to the grille pocket, 7.20 mm outboard.

**DC input jack** — Ø8 through, counterbored Ø16 × 5 mm on the outer face at
(+60, 52). The counterbore matters: it leaves a **3.4 mm panel** for the jack's nut
instead of the full 8.4 mm wall, which is thicker than most panel-mount 5.5 × 2.5 mm
barrel jacks will clamp.

**PicoPSU cradle** — see below.

**Lid — a drop-on housing that needs no screws.** The body is one cohesive print
with a closed top over the bay; the plenum gets a separable lid that **slides
straight down over the top of the case** and stays there.

You fit it by dropping it on. Nothing to thread, nothing to line up:

| | |
|---|---|
| Skirt | 2.8 mm thick, **14 mm deep** down the two sides and the back |
| Front skirt | only **8 mm** — the drive bay's roof is 8.2 mm below the top of the rear section, and a full-depth skirt would land on it |
| Fit | 0.2 mm slip clearance + a 0.35 mm friction bead = a light **0.15 mm press fit** |
| Located by | the skirt in X and Z, the top rim in Y |
| Removed by | lifting it — it cannot slide off in any direction |

The bead is a deliberate interference, so `body ∩ lid` is no longer zero: the report
prints it (283 mm³) and checks it against the ~231 mm³ that a 0.15 mm band should
account for, rather than asserting zero. **Set `SKIRT_BEAD = SKIRT_CLEAR` for a free
slip fit** if you would rather have that, and the six M3 screw positions are still
cut in case you want it bolted for transport.

**The fan cable is clear of the lid, three ways over** — all three numbers are
printed in the build report:

1. The locating lip is **1.5 mm** deep, so it bottoms out at y = 101.3, which is
   **1.3 mm above** the plenum's interior ceiling at y = 100. It never enters the
   plenum at all, so nothing loose in there can be snagged on it.
2. The lip is cut short at **Z 242**, i.e. 6 mm before the fan starts at Z 248 —
   there is no lip over the fan whatsoever.
3. The skirt is entirely **outside** the case, so it cannot reach a cable that is
   inside it.

**Roof gussets** — because the plenum is a plain box, its roof would otherwise have
bridged 145.8 mm in mid air. Two **18 mm 45° gussets** run the length of the roof/wall
corners. They make the roof printable and give the lid screws their material.

**Base** — four Ø12 × 2 mm recesses for rubber feet, in a 4 mm floor.

**Edge treatment** — every outer edge is rounded: **R1.4** on the body and the PSU
strap, **R1.0** on the lid. Nothing on the outside is a sharp edge.

The rounds are applied to the **bare shell**, before anything is cut into it.
Filleting the finished body would also try to round the 1.2 mm honeycomb webs and
every internal corner, which OCC will not survive; and the coplanar faces have to be
merged first, or the seams between the two shell boxes get filleted into grooves.

R1.4 is close to the ceiling here: every outer edge sits on either a 2.8 mm wall or
a 3 mm lid plate, and the round has to leave a printable rim behind it.

**The cost, stated plainly**: the outer corner round and the cage lead-in flare both
remove material from the same 2.8 mm front wall, and at the mouth corner they add
up. Keeping the original 1.6 mm flare would have left **0.5 mm** there, so the flare
is reduced to 0.8 mm, which leaves exactly **1.00 mm**. So the cage's lead-in is
half what it was — see [INSTALL.md](INSTALL.md) step 2 for what that means in
practice.

### Why the rear section steps up 8.2 mm

A **92 mm fan frame is taller than the 87.8 mm cage bore**, so it cannot sit inside a
case only as tall as the bay. The rear section therefore steps from 94.6 mm to
102.8 mm — an 8.2 mm step, not the 37 mm tower an earlier revision had.

This is derived, not hand-set:

```python
INT_H_PLEN = max(INT_H, FAN_SIZE + 2*FAN_INNER_CLEAR)
REAR_H     = FLOOR_T + INT_H_PLEN + WALL     # 102.8 with a 92 mm fan
```

Give it a fan of **83.8 mm or less** and `REAR_H` collapses back to `BAY_H` and the
top becomes a flat prism. `FAN_SIZE` and `FAN_INNER_CLEAR` are the only numbers you
touch.

---

## Fitted fan — ARCTIC P9 PWM PST (ACFAN00298A)

Figures from ARCTIC's own spec sheet (`Spec_Sheet_P9_PWM_PST_EN.pdf`), not from a
reseller listing.

| | |
|---|---|
| Frame | 92 × 92 × 25 mm, 106 g |
| Mounting hole pattern | **82.5 × 82.5 mm** — matches `FAN_PATTERN` |
| Speed | 200–3000 rpm, PWM controlled (0 rpm below 5 % duty) |
| Airflow | 38.83 cfm / 65.97 m³/h |
| Static pressure | 3.12 mmH₂O — a high-pressure fan, which is what a caddy-stacked backplane wants |
| Bearing | fluid dynamic |
| Electrical | 12 V DC, 0.12 A = **1.44 W**, starts at 5 V |
| Lead | 400 mm + 80 mm PST daisy-chain, 4-pin plug **and** 4-pin socket |
| Ambient | 0–40 °C, 6 year warranty |

**Fit inside the enclosure**

| | |
|---|---|
| Bore it sits in | 145.8 × 96.0 × 108 mm |
| Frame clearance | 2.0 mm on every side |
| Fan position | Z 248 → 273, flat against the rear wall |
| Grille field | Ø90 pocket, Ø~86 of actual honeycomb |
| Mounting holes | Ø4.2 at (±41.25, 50 ± 41.25) — optional, the housing holds it |
| Housing | slot at Z 248→273, 0.2 mm per side, lid fins 1 mm above the frame top |

**Mounting** — with the housing, mounting is just "lower it in". The four M3 × 30
positions are still cut into the rear wall (heat-set inserts pressed in from the
**outside** face) if you would rather bolt it, in which case the screws go in from
inside the plenum. Point the fan so it exhausts outward and check the moulded
airflow arrow.

**Fan lead** — the 4-pin plug never leaves the case now, so no wall notch is needed.
Route the lead forward along the plenum and tuck it down before the lid goes on.

---

## PicoPSU cradle

Sized from mini-box's own figures for the **picoPSU-120: 31 × 44 × 21 mm (1U)**,
57 g with its harness, DC input a 5.5 × 2.5 × 10 mm barrel.

The board sits on the plenum floor behind the backplane, and the whole point of the
cradle is that it **cannot reach the backplane**:

| | |
|---|---|
| Cradle bore | 32.6 × 45.6 mm (0.8 mm clearance per side) |
| Cradle Z | 185 → 230.6 mm |
| Mouth to backplane face | **20 mm** — board stops 21.6 mm short even fully forward |
| Plinth | 3 mm, so the solder side never touches the floor |
| Front lip | 6 mm tall (3 mm above the plinth) — stops it sliding forward |
| Retaining strap | 50.2 × 4 × 20 mm, 2 × M3 into corner bosses, 0.4 mm over the board top |
| Corner bosses | Ø4.2 heat-set inserts, 10 mm deep |

The build runs a **phantom PicoPSU box** through the cradle and reports the
interference. That check earned its place immediately — it caught the left strap
boss being modelled 6 mm the wrong side of its wall, straight through the board's
footprint (625 mm³ of interference) which nothing visual had flagged.

**Two things to check on your own wiring**

1. The cradle holds the *bare board*. If you mount the 24-pin ATX connector facing
   up, it stands taller than the 21 mm board and the strap will be in the way. Either
   fit the strap around it, or change `PSU_BORE_Z` to move the strap along the cradle.
2. There is no motherboard here, so a PicoPSU will not start on its own — **PS_ON#
   must be tied to ground** for it to run as a standalone 12 V → 5 V/3.3 V supply.
   The fan's 1.44 W is nothing for the Wago 221 terminals, so it can share them.

---

## BOM

| Item | Qty | Notes |
|---|---|---|
| Printed body | 1 | ≈ 524 cm³ / ≈ 665 g at 1.27 g/cm³ |
| Printed lid (drop-on housing) | 1 | ≈ 88 cm³ / ≈ 112 g |
| Printed PSU strap | 1 | ≈ 3.8 cm³ / ≈ 5 g |
| **ARCTIC P9 PWM PST 92 mm** | 1 | inside the plenum, exhaust; 106 g |
| **PicoPSU-120** (or similar) | 1 | 31 × 44 × 21 mm; add a 12 V brick + panel DC jack |
| Panel-mount 5.5 × 2.5 mm DC jack | 1 | Ø8 body, ≤ 3.4 mm panel |
| M3 × 6 heat-set insert | **12** | 6 lid, 4 fan, 2 PSU strap |
| M3 × 10–12 screw | 8 | 6 lid, 2 strap |
| M3 × 30 screw | 4 | through the fan frame into the rear-wall inserts |
| M3 screw + nut | 2–6 | cage anchoring (see caveats) |
| Rubber feet Ø12 × 2 mm | 4 | |
| SFF-8087 → SFF-8088 cables | 2 | exit through the rear slots |
| Wago 221 lever terminals | 3 | in the plenum |

### Print settings

PETG or ASA suggested (the plenum sees warm server air). 0.2 mm layers, 3–4 walls,
4–5 top/bottom layers. **No supports needed** — the body prints flat on its base with
the front opening up. The grille webs are 1.2 mm, i.e. three 0.4 mm lines; don't go
below a 0.4 mm nozzle for those.

---

## Rebuilding and verifying

```bash
# generate STEP + STL + report into ./out
freecadcmd dl380_cage_case.py

# re-probe the exported STEP: every opening open, every wall solid
freecadcmd verify_step.py

# optional: dependency-free preview renders (SVG -> PNG via rsvg-convert)
python3 render_stl.py out/dl380_cage_case_body.stl out/body.png
```

Tested with FreeCAD 1.1.3 (`freecadcmd`). The scripts also run from the FreeCAD GUI
Python console via `exec(open("dl380_cage_case.py").read())`.

`render_stl.py` is a self-contained painter's-algorithm shaded renderer — it needs
only `rsvg-convert` (or any SVG rasteriser) and no Python packages at all. It draws
front, rear, side, top and half-section cutaway views.

---

## Parameters

All at the top of `dl380_cage_case.py`. Nothing derived is hand-edited.

| Parameter | Default | Meaning |
|---|---|---|
| `CAGE_W` / `CAGE_H` / `CAGE_D` | 145.0 / 87.0 / 165.0 | HP cage envelope |
| `FIT_CLEAR` | 0.4 | slide-in clearance, per side |
| `WALL` / `FLOOR_T` | 2.8 / 4.0 | wall and floor thickness |
| `FILLET_R` / `FILLET_R_LID` | 1.4 / 1.0 | outer edge rounds, body+strap / lid |
| `LEAD_IN` / `LEAD_DEPTH` | 0.8 / 4.0 | cage lead-in flare — capped by the rounds |
| `SKIRT_T` / `SKIRT_D` / `SKIRT_FRONT_D` | 2.8 / 14.0 / 8.0 | lid skirt thickness and depth |
| `SKIRT_CLEAR` / `SKIRT_BEAD` | 0.2 / 0.35 | slip clearance / bead; bead > clearance = press fit |
| `LID_LIP_T` / `LID_LIP_GAP` | 1.5 / 6.0 | locating lip depth, and its gap to the fan |
| `REAR_WALL_LAYERS` | 3 | rear wall in wall-units → 8.4 mm |
| `GUSSET_H` | 18.0 | 45° roof gusset size (sets the service opening width) |
| `PLENUM_D` | 108.0 | clear depth behind the backplane |
| `FAN_SIZE` / `FAN_INNER_CLEAR` | 92.0 / 2.0 | frame size and bore clearance |
| `FAN_APERTURE` / `FAN_PATTERN` / `FAN_HOLE` | 86.0 / 82.5 / 4.2 | grille field and mounting pattern |
| `FAN_INSET` | 25.0 | fan depth against the rear wall |
| `FAN_GUIDE_CLEAR` | 0.2 | clearance per side in the fan housing — the fit to tune |
| `FAN_GUIDE_T` / `FAN_GUIDE_H` / `FAN_GUIDE_CHAM` | 3.0 / 42.0 / 1.8 | rail thickness, height, lead-in |
| `FAN_TAB_H` / `FAN_TAB_Z` | 16.0 / 3.0 | front corner tabs that stop the fan tipping |
| `FAN_LID_GAP` | 1.0 | how far the lid's fin sits above the fan — how much it can lift |
| `GRILLE_CELL` / `GRILLE_WEB` | 9.0 / 1.2 | honeycomb cell and web size |
| `GRILLE_RIM` / `GRILLE_DEPTH` | 2.0 / 3.0 | solid rim, membrane thickness |
| `PSU_W` / `PSU_L` / `PSU_H` | 31 / 44 / 21 | the board envelope |
| `PSU_CLEAR` / `PSU_BOOT` / `PSU_PLINTH_T` | 0.8 / 20.0 / 3.0 | fit, backplane gap, plinth |
| `PSU_WALL_H` / `PSU_FRONT_LIP` | 24.0 / 6.0 | cradle wall and lip heights |
| `PSU_BORE_Z` | 192.0 | where the strap screws sit along the cradle |
| `REAR_CABLE_SLOT_*` | X −60, Y 33/50, 17 × 12 | rear cable egress |
| `DC_JACK_X` / `DC_JACK_Y` | 60.0 / 52.0 | DC jack position |
| `DC_JACK_DIA` / `DC_JACK_PAD` / `DC_JACK_DEPTH` | 8.0 / 16.0 / 5.0 | jack hole and counterbore |
| `CAGE_SCREW_Z` | 15…155 | candidate cage anchor positions |
| `LID_SCREW_X` / `LID_SCREW_Z` | 70.0 / (185, 215, 245) | lid screw positions |
| `REAR_H` | *derived* | follows the fan automatically |

---

## Caveats — read before printing

1. **Cage side-screw positions are unverified.** `CAGE_SCREW_Z` places six Ø3.4 holes
   per side wall as a *menu*, not a measurement — the real cage's own holes were not
   measured. Check which position lines up with your cage and drop the rest from the
   list before you print. The rear stop frame holds the cage regardless.
2. **The PicoPSU cradle is sized for the bare picoPSU-120 (31 × 44 × 21 mm).** Check
   your board before printing; other PicoPSU models differ, and `PSU_W/L/H` and
   `PSU_BORE_Z` are the numbers to change.
3. **The DC jack counterbore leaves a 3.4 mm panel.** Measure your jack's neck and
   change `DC_JACK_PAD` / `DC_JACK_DEPTH` if it wants something different.
4. **Rear section is 8.2 mm taller than the bay.** That is what an internal 92 mm fan
   costs. Use an 83.8 mm-or-smaller fan and the top is flat again.
5. **The lid is a 0.15 mm press fit on its skirt bead.** If it will not go on, take
   the bead down with a scraper, or set `SKIRT_BEAD = SKIRT_CLEAR` (0.2) for a free
   slip fit. If it is too loose, raise `SKIRT_BEAD`. Printed dimensions vary; this is
   the one number to trim to your machine.
6. **Dimensions are from the brief, not from calipers.** If your cage measures
   differently, change `CAGE_W` / `CAGE_H` / `CAGE_D` and rebuild.
7. **Nothing here has been printed yet.** The geometry is verified as valid, closed,
   non-interfering, phantom-fitted and feature-by-feature against the exported STEP,
   but that is not the same as a successful print.

---

## Repository layout

```
dl380_cage_case.py            parametric model -> STEP/STL (the thing to edit)
verify_step.py                re-probes the exported STEP; non-zero exit on failure
render_stl.py                 standalone STL -> shaded PNG renderer
docs/reference/               photos of the target hardware
out/
  dl380_cage_case.step        body + lid + strap, high precision  <- deliverable
  dl380_cage_case_body.step   body only
  dl380_cage_case_lid.step    lid only
  dl380_cage_case_strap.step  PicoPSU strap only
  dl380_cage_case_*.stl       print meshes
  dl380_cage_case_report.txt  derived dimensions + sanity checks
  *.png                       preview renders
```

---

## License

MIT — see [LICENSE](LICENSE).
