# Installation guide

How to assemble the DL380 case. Read the **Order of work** section first — several
steps are only possible in one sequence.

Run `freecadcmd dl380_cage_case.py` first if `out/` is empty; the numbers below come
from [`out/dl380_cage_case_report.txt`](out/dl380_cage_case_report.txt).

---

## Conventions

The model uses these axes, and this guide uses them throughout:

| Direction | Meaning |
|---|---|
| **front** | the big open rectangular mouth — where caddies are inserted |
| **back / rear** | the face with the honeycomb grille, cable slots and DC jack |
| **top** | the face with the long service opening and the screwed-on lid |
| **inside** | the plenum behind the backplane — reached through the top opening |

There is **no way in from the back**. Everything except the cage goes in through the
top service opening or the front mouth.

---

## What you need

**Printed**

| Part | File | Notes |
|---|---|---|
| Body | `out/dl380_cage_case_body.stl` | the big one; prints flat on its base, front opening up, **no supports** |
| Service lid | `out/dl380_cage_case_lid.stl` | prints flat |
| PSU strap | `out/dl380_cage_case_strap.stl` | prints flat |

**Hardware**

| Item | Qty | Where |
|---|---|---|
| M3 heat-set insert, 5.7 mm long | **12** | 4 fan, 2 PSU strap, 6 lid |
| M3 × 30 screw | 4 | through the fan frame |
| M3 × 10–12 screw | 8 | 6 lid, 2 PSU strap |
| M3 × 6–8 screw + nut | 2–6 | cage anchoring |
| Rubber feet Ø12 × 2 mm | 4 | base |
| Panel-mount 5.5 × 2.5 mm DC jack | 1 | rear wall |
| ARCTIC P9 PWM PST 92 mm | 1 | 106 g |
| PicoPSU-120 (31 × 44 × 21 mm) | 1 | cradle |
| SFF-8087 → SFF-8088 cables | 2 | rear slots |
| Wago 221 lever terminals | 3 | plenum |

**Tools**: 2.5 mm hex or the driver your screws need, a soldering iron with a
heat-set insert tip, flush cutters, and a small scraper or deburring tool.

![the assembled layout, cut open](out/body_cut.png)

---

## Order of work

```
 1  print + clean up
 2  dry-fit the cage                 (checks the slide before anything is captive)
 3  12 x heat-set inserts            (all of them, while the box is empty)
 4  fan                              <- goes to the very back, do it first
 5  cage, in from the FRONT          <- straight slide, no tilt
 6  cage anchor screws
 7  DC jack in the rear wall
 8  SFF-8087 cables in from the back, onto the backplane
 9  wiring: PicoPSU -> Wagos -> backplane, ground PS_ON#
10  PicoPSU into the cradle + strap
11  service lid
12  rubber feet
13  first power-up
```

Steps 4 and 5 can be swapped. Everything else has to be in this order: the cables
want the cradle empty, the PSU wants the cables already routed, and the lid closes
the only way in.

---

## Step 1 — print and clean up

Print the body flat on its base with the front opening pointing up. **No supports
are needed and none should be used** — the internal 45° roof gussets and the 3 mm
grille membrane are designed to print unsupported.

Check these before you go further:

- the four Ø4.2 fan insert holes in the **outside** of the rear wall are clear
- the honeycomb grille is open. The webs are 1.2 mm — **three 0.4 mm lines** — so
  don't use a nozzle bigger than 0.4 mm, and don't jab them with a scraper
- the two rear cable slots and the Ø8 DC jack hole are clear
- the 12 insert bores are open: 4 in the rear wall (outside face), 2 in the PSU
  strap bosses, 6 in the roof gussets

---

## Step 2 — dry-fit the cage

Do this now, while the box is completely empty and you can still see what you're
doing.

**Yes, the cage just slides in from the front — straight, not tilted, no clips and
no flexing.** It goes in backplane-end first, and travels 165 mm until it stops.

![the target cage](docs/reference/cage-front-bezel.png)

| | |
|---|---|
| Cage | 145.0 × 87.0 × 165.0 mm |
| Bore in the case | 145.8 × 87.8 mm |
| Clearance | **0.4 mm per side** — a slide fit |

0.4 mm per side is a proper slide fit but it is not loose. It will jam if you
corkscrew it, so:

1. Set the case on its base on the bench.
2. Pick the cage up by both sides, backplane away from you.
3. Line the cage up square in the mouth and push it in **straight** — both hands,
   equal pressure, no rocking.
4. It should slide freely and stop with a firm, definite feel when it meets the
   internal stop frame at the back of the bay.

That stop frame is a 4 mm-wide ledge with a 137.8 × 79.8 mm aperture in it. The
cage's rear butts against it and that sets the depth — the cage's front bezel ends
up flush with the case's front face.

**If it fights you**: don't force it. Find the tight corner, lift it out, look for
print elephant-footing or blobs on the inside of the sleeve, scrape them off, and
try again. The mouth has a 1.6 mm lead-in flare to help you start it square.

Pull it back out for now — you want the box empty for the inserts.

---

## Step 3 — the 12 heat-set inserts

The bore is Ø4.2 × 10 mm everywhere. Set your iron to the insert maker's
temperature, insert squarely, and stop when the insert is flush with the surface.
**Do not push past flush** — you'll punch through into the cavity on the thin ones.

| Qty | Location | Insert from | Bore centre |
|---|---|---|---|
| 4 | rear wall, fan mounting | **outside** face | (±41.25, 10.75) and (±41.25, 93.25) |
| 2 | PSU strap bosses | top, through the service opening | (±20.7, Z 192) |
| 6 | roof gussets, lid | top, on the outer top face | (±70, Z 185 / 215 / 245) |

Three things worth knowing:

- **The fan inserts go in from the outside.** They are the only ones you fit from
  the outside face. Fit them now, before the cage is in, so you can sit the part
  flat on the bench.
- **The 2 PSU strap inserts** are down inside the plenum, on the two bosses either
  side of the PSU cradle at Z 192. Reach in through the top opening.
- **The 6 lid inserts** are in the 45° roof gussets, so the bore is in the flat top
  face either side of the long opening, 5.7 mm inboard of the side walls.

---

## Step 4 — the fan (do this before the cage)

The fan is the deepest thing in the case: it ends up hard against the **inside** of
the rear wall at Z 248–273, so it goes in first while the plenum is empty.

**Where it lands**

| | |
|---|---|
| Position | Z 248 → 273, flat against the rear wall |
| Frame | X ±46, Y 6 → 98 (2 mm clear of the bore on every side) |
| Screws | 4 × M3 × 30 through the frame, from inside, into the outside-face inserts |

**How to get it in.** The service opening in the top runs Z 172 → 273, and the PSU
cradle occupies Z 182 → 233 on the floor. That leaves a drop-in window of
**Z 235.4 → 248** — 12.6 mm of slack, and the report prints this number so you can
check it for yourself.

1. Hold the fan flat (frame horizontal, hub up) over the **rear end** of the
   opening, somewhere in Z 235–248. Anywhere in that band works.
2. Lower it straight down until it rests on the floor of the plenum.
3. **Slide it back** the last 12.6 mm until its frame touches the inside of the
   rear wall.
4. Check the airflow arrow points **out of the back** — this fan exhausts. Also
   check its cable is trailing out of the front of the fan, toward the cradle end,
   not pinched behind it.
5. Start all four M3 × 30 screws by hand, then nip them up. The inserts are in
   PETG: **snug, not tight.**

If it will not drop in, you are too far forward and standing it on the PSU cradle.
Move it back.

---

## Step 5 — the cage, in from the front

Same slide as step 2, but now you know it fits. Push it in square and straight until
it stops on the frame. Nothing else changes — the fan is behind it and out of the
way, at Z 248+, and the cage stops at Z 165.

---

## Step 6 — anchor the cage

The side walls have **six candidate Ø3.4 holes per side** at Z 15 / 45 / 75 / 105 /
135 / 155, all on the bay's mid-height. These are a *menu*, not a measurement — the
real cage's own holes were never measured, so:

1. Look through the wall holes from outside and see which one lines up with a hole
   in the cage's sheet metal.
2. Fit a screw in that one. Two per side, front and rear, is plenty.
3. If none line up, stop here — the rear stop frame already holds the cage in
   depth, and the lid holds it from above. Add a screw only where it's real.

The hole is a clearance hole straight through 2.8 mm of wall, so a small M3 screw and
nut works, as does a self-tapper. **Do not overtighten** — it's a 2.8 mm wall.

---

## Step 7 — the DC jack

The rear wall takes a panel-mount 5.5 × 2.5 mm barrel jack at **(+60, 52)**:

| | |
|---|---|
| Jack body hole | Ø8.0 through |
| Counterbore | Ø16.0 × 5 mm deep, in the **outside** face |
| Panel the jack sees | **3.4 mm** |

The counterbore is there on purpose: the wall is 8.4 mm thick and most panel-mount
jacks won't clamp a panel that thick. Feed the jack through from **outside**, body
first, and the nut lands on the 3.4 mm floor of the counterbore. Solder your leads
to the tags on the inside before you tighten it down.

If your jack's neck is a different length, change `DC_JACK_PAD` / `DC_JACK_DEPTH`
and rebuild.

---

## Step 8 — the SFF-8087 cables

There are two slots in the rear wall, both at **X = −60**, at **Y = 33** and
**Y = 50**, each 17 × 12 mm with rounded corners. Do these before the PicoPSU goes
in — you need the cradle empty to get your hand in.

1. From **outside**, feed each SFF-8088 overmould through its own slot, in to the
   plenum. One cable per slot.
2. Reach in through the top opening and pull the tail forward to the backplane.
3. Plug both SFF-8087 ends into the backplane, reaching forward past the front edge
   of the opening to Z 165.
4. Pull the slack back so the cables lie along the **left-hand side** of the plenum
   and leave the middle clear for the PSU.

Keep the two cables in separate slots — that's what gives each one its own strain
relief, and two cables sawing against each other in one hole is how you get a
fractured pair after a year.

---

## Step 9 — wiring

This part is yours, not the model's: no wire routing or Wago mounts are modelled,
because your backplane's power connector is whatever it is.

**Room you have**: about 47 mm of clear floor either side of the PSU cradle, plus a
17 mm strip right behind the backplane. The Wagos sit on the floor there; cable-tie
them to the harness if you want them fixed.

**Two things that will catch you out**

1. **There is no motherboard in this box**, so a PicoPSU will not start on its own.
   Its **PS_ON# pin must be tied to ground** for it to run as a standalone
   12 V → 5 V / 3.3 V supply. Without that jumper you get nothing on the rails.
2. The PicoPSU's output harness is 24-pin ATX plus a SATA/Molex string, and none of
   that mates with an HP backplane. You're cutting it down and landing 12 V / 5 V /
   3.3 V / ground on the Wagos, then out to the backplane's own power input.

Rough current budget: the ARCTIC P9 draws 0.12 A at 12 V = **1.44 W**, which is
nothing for a Wago 221, so the fan can share terminals with the drives.

---

## Step 10 — the PicoPSU into the cradle

The cradle is sized for the **bare picoPSU-120 board, 31 × 44 × 21 mm**.

| | |
|---|---|
| Cradle bore | 32.6 × 45.6 mm (0.8 mm clearance per side) |
| Cradle Z | 185 → 230.6 |
| Board sits on | a 3 mm plinth, so the solder side never touches the floor |
| Front lip | 6 mm tall — 3 mm above the plinth |
| Backplane gap | the mouth is 20 mm behind the backplane; the board stops 21.6 mm short of it |

1. Route the output harness and the DC input leads **out of the cradle toward the
   front** before you drop the board in, or you will not get them past the lip.
2. Lower the board into the cradle, connectors facing whichever way leaves the
   harness room.
3. The 6 mm front lip holds it from sliding forward onto the backplane. Nothing you
   do here can make the board touch the backplane — that is what the 20 mm gap and
   the lip are for.
4. Set the strap across the top and fit **2 × M3 × 10–12** into the two boss
   inserts. Snug only.

**Watch the 24-pin connector.** If it faces up, it stands taller than the 21 mm
board and the strap lands on it. Either lay the strap over the connector or move it
along the cradle by changing `PSU_BORE_Z`.

---

## Step 11 — the service lid

1. Check nothing is proud of the top face: no cable or Wago sticking up into where
   the lid sits.
2. Drop the lid on. Its 2 mm lip should settle into the opening with no force.
3. Start all **6 × M3 × 10–12** by hand — three down each side at Z 185 / 215 / 245
   — then tighten in a cross pattern, snug not tight.

The lid is what closes the plenum and makes the case rigid, so fit all six.

---

## Step 12 — rubber feet

Four Ø12 × 2 mm recesses in the base at (±61, Z 14) and (±61, Z 260). Push-fit; a
dab of cyanoacrylate if they're loose.

---

## Step 13 — first power-up

1. Before applying power: **no screw tips protruding into the plenum**, no wire
   trapped between the lid and the body, no bare conductor touching the backplane.
2. Power up and confirm the fan spins and pushes air **out of the back**. Hold a
   tissue near the grille — it should be pushed away, not sucked in.
3. If the fan doesn't run, check the PS_ON# jumper first (step 9).
4. Run it for ten minutes and feel the rear wall and the grille. If the plenum is
   uncomfortably hot, the fan is restricted or running too slow — the P9 is PWM and
   idles quietly, so give it some duty cycle.

---

## Troubleshooting

| Symptom | Cause |
|---|---|
| Cage won't start into the mouth | printing blobs or elephant-footing inside the sleeve; scrape and retry. Don't force it — 0.4 mm/side is not a clearance you can bully |
| Cage stops short of the front face | something in the bay behind it, or it's wedged; lift out and look |
| Fan won't drop into the plenum | you're forward of Z 248 and standing it on the PSU cradle — move it back to the Z 235–248 band |
| Fan won't sit flat on the rear wall | its cable is trapped behind it, or a cable is in the way along the side |
| PicoPSU won't start | PS_ON# isn't grounded (step 9) |
| Strap won't sit down | the 24-pin ATX connector is standing up under it — move the strap along the cradle |
| DC jack won't clamp | your jack's neck is shorter than 3.4 mm; reduce `DC_JACK_DEPTH` and rebuild |
| Lid won't settle | a cable or Wago is proud of the top face, or the lip is catching on the grille side |

---

## If you change anything, re-check these

Two numbers in this guide are *derived* and both are printed in the build report, so
you don't have to work them out again:

- **`fan drop-in window : Z …`** — the band the fan must be lowered into. If
  `PLENUM_D`, `PSU_*` or `FAN_INSET` change and this band goes empty, the report
  prints `*** FAN CANNOT BE FITTED ***` instead of a number.
- **`opening size`** and the roof margins — the lid needs the side strips, the front
  band and the rear wall top to sit on.

Run `freecadcmd verify_step.py` after any rebuild; it probes the exported STEP and
exits non-zero if any opening is blocked or any wall is missing.
