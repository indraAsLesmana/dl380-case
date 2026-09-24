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
| **Mandatory screws / inserts** | **0** | **100% toolless assembly** |
| ARCTIC P9 PWM PST 92 mm | 1 | rear fan housing |
| PicoPSU-120 (31 × 44 × 21 mm) | 1 | cradle with snap-fit strap |
| Panel-mount 5.5 × 2.5 mm DC jack | 1 | rear wall counterbore |
| Rubber feet Ø12 × 2 mm | 4 | base |
| SFF-8087 → SFF-8088 cables | 2 | rear slots |
| Wago 221 lever terminals | 3 | plenum |
| *Optional: M3 heat-set inserts* | *4* | *fan mounting (only if bolting for transport)* |
| *Optional: M3 × 30 screws* | *4* | *fan mounting (only if bolting for transport)* |
| *Optional: M3 × 6–8 screw + nut* | *2–4* | *cage anchoring (only if bolting through side holes)* |

**Tools**: Flush cutters and a small scraper or deburring tool. (No soldering iron or hex drivers needed for mandatory assembly!).

![the assembled layout, cut open](out/body_cut.png)

---

## Order of work

```
 1  print + clean up
 2  dry-fit the cage                 (checks the slide before anything is captive)
 3  fan                              <- slides straight down into rear housing slot
 4  cage, in from the FRONT          <- straight slide, no tilt
 5  (optional) cage anchor screws
 6  DC jack in the rear wall
 7  SFF-8087 cables in from the back, onto the backplane
 8  wiring: PicoPSU -> Wagos -> backplane, ground PS_ON#
 9  PicoPSU into the cradle + snap-fit strap
10  slide-and-click service lid      <- slides +Z and clicks shut
11  rubber feet
12  first power-up
```

Steps 3 and 4 can be swapped. Everything else has to be in this order: the cables
want the cradle empty, the PSU wants the cables already routed, and the lid closes
the only way in.

---

## Step 1 — print and clean up

Print the body flat on its base with the front opening pointing up. **No supports
are needed and none should be used** — the internal 45° roof gussets, 45° slide rails,
and the 3 mm grille membrane are designed to print unsupported.

The lid prints top-plate face down on the bed with skirts pointing up (45° runner grooves
are self-supporting). The strap prints flat on the bed.

Check these before you go further:

- **every outer edge is rounded** — R1.4 on the body, R1.0 on the lid, R1.4 on the
  strap.
- the 45° slide rails on the body's outer plenum walls are clean and free of z-blobs.
- the recessed catch pocket on the front vertical step ($Z = 165\text{ mm}$) is clear.
- the lid's runner grooves and cantilever latch tooth are cleanly resolved.
- the honeycomb grille is open. The webs are 1.2 mm — **three 0.4 mm lines** — so
  don't use a nozzle bigger than 0.4 mm, and don't jab them with a scraper.
- the two rear cable slots and the Ø8 DC jack hole are clear.

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
try again.

**One thing to expect**: the mouth's lead-in flare is only **0.8 mm** (0.4 mm per
side) — half what it would be without the rounded outer corners, because the round
and the flare both come out of the same 2.8 mm front wall. So the mouth is closer to
a straight-edged hole than a funnel, and the cage has to go in **square** rather than
being guided in by the taper. Start it gently and correct the angle rather than
pushing; once it's started it slides freely.

Pull it back out for now — you want the box empty for the fan.

---

## Step 3 — the fan (do this before the cage)

The fan is the deepest thing in the case. It has **its own housing**: it slides
straight down into a slot and seats on the plenum floor, and **no screws are needed**.

**Where it lands**

| | |
|---|---|
| Slot | Z 248 → 273, straight down from above |
| Seat | the plenum floor — the frame's bottom edge rests on it |
| Frame | X ±46, guided by two rails with 0.2 mm clearance per side |
| Up | two fins on the lid later come down to 1 mm above its top edge |

**How to get it in.** The service opening in the top runs Z 172 → 273. Lower the
frame flat (hub up) into the **rear end** of that opening, over Z 248–273, and let
it drop.

1. Line the frame up over the **rear end** of the opening. The two guide rails below
   have a 1.8 mm chamfer at their tops to help you find the slot.
2. Lower it straight down. It slides between the rails and lands on the plenum
   floor.
3. It is seated when the frame's bottom edge is flat on the floor and its rear face
   is against the inside of the rear wall. There is 0.2 mm of play, so it feels snug
   rather than loose.
4. Check the airflow arrow points **out of the back** — this fan exhausts. Also
   check its lead trails out of the front of the frame, not trapped behind it.
5. **Route the lead now, while there is room.** Run it forward along one side of
   the plenum, tucked down low against the floor, and leave it long enough to reach
   the Wagos.
6. That is it — no screws. Close the lid at step 10: its two underside fins come
   down to just above the fan's top edge, and that is what stops the fan lifting
   out. With the lid on, the case holds the fan on **four** sides and the lid holds
   it on the **fifth**.

*(Optional: If you plan on tossing the case into a backpack and want the fan permanently bolted, you can press 4× M3 inserts into the rear face from the outside and run 4× M3 × 30 screws from inside).*

---

## Step 4 — the cage, in from the front

Same slide as step 2, but now you know it fits. Push it in square and straight until
it stops on the frame. Nothing else changes — the fan is behind it and out of the
way, at Z 248+, and the cage stops at Z 165.

---

## Step 5 — anchor the cage (optional)

The side walls have **six candidate Ø3.4 holes per side** at Z 15 / 45 / 75 / 105 /
135 / 155, all on the bay's mid-height. These are optional — the internal stop frame
and lid hold the cage in place. If you wish to pin it:

1. Look through the wall holes from outside and see which one lines up with a hole
   in the cage's sheet metal.
2. Fit a small screw in that one. Two per side, front and rear, is plenty.
3. If none line up, stop here — the rear stop frame already holds the cage in
   depth.

---

## Step 6 — the DC jack

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

---

## Step 7 — the SFF-8087 cables

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

---

## Step 8 — wiring

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

---

## Step 9 — the PicoPSU into the cradle + snap-fit strap

The cradle is sized for the **bare picoPSU-120 board, 31 × 44 × 21 mm**.

| | |
|---|---|
| Cradle bore | 32.6 × 45.6 mm (0.8 mm clearance per side) |
| Cradle Z | 185 → 230.6 |
| Board sits on | a 3 mm plinth, so the solder side never touches the floor |
| Front lip | 6 mm tall — 3 mm above the plinth |
| Backplane gap | the mouth is 20 mm behind the backplane; the board stops 21.6 mm short of it |
| Snap strap | 56.2 × 10 × 20 mm snap-fit clip with 0.8 mm undercut catch teeth |

1. Route the output harness and the DC input leads **out of the cradle toward the
   front** before you drop the board in, or you will not get them past the lip.
2. Lower the board into the cradle, connectors facing whichever way leaves the
   harness room.
3. The 6 mm front lip holds it from sliding forward onto the backplane.
4. Take the **snap-fit strap** and press it down over the cradle corner bosses.
   The compliant legs will flex outward over the retention ledges and click
   firmly into place. **No screws, no tools.**

---

## Step 10 — the slide-and-click lid

The service lid uses a **slide-and-click mechanism**: it slides forward horizontally
into 45° beveled rails on the outer plenum walls and clicks shut with an integrated
cantilever latch. **100% screwless.**

1. Check nothing is proud of the top: no cable or Wago sticking up into the opening.
2. Position the lid over the rear of the plenum, aligning the skirt runner grooves
   with the 45° slide rails on the case's outer walls.
3. Push the lid **forward (+Z)** along the rails. It slides smoothly toward the front.
4. As it reaches the front step ($Z = 165\text{ mm}$), the cantilever snap latch
   tooth will ride up over the step bevel and **click audibly** into the recessed
   catch pocket.
5. The lid is now locked in all 6 degrees of freedom:
   - X and Y restrained by the 45° interlocking rails.
   - -Z restrained by the front vertical step.
   - +Z restrained by the snap latch tooth.

**To remove the lid:** Press the ergonomic thumb-release tab on the front face
forward/up slightly to disengage the tooth from the catch pocket, and slide the
lid backward (-Z).

**The lid is also the fan's fifth restraint.** Its two underside fins come down to
1 mm above the fan's top edge — that is why the fan needs no screws.

---

## Step 11 — rubber feet

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
| Cage won't start into the mouth | the lead-in is only 0.8 mm and printing blobs or elephant-footing make it worse; scrape the sleeve and start it squarer. Don't force it — 0.4 mm/side is not a clearance you can bully |
| Something on the outside feels sharp | a print defect, not the design — every outer edge is R1.4 / R1.0. Deburr it |
| Cage stops short of the front face | something in the bay behind it, or it's wedged; lift out and look |
| Fan won't drop into the plenum | you're forward of the housing — the two front corner tabs at Z 244.7–247.7 will stop the frame. Lower it over Z 248–273 |
| Fan fits but rattles | the housing fit is 0.2 mm per side; lower `FAN_GUIDE_CLEAR` and rebuild |
| Fan won't go into the housing | raise `FAN_GUIDE_CLEAR`, or scrape the two rails |
| Fan lifts when I turn the case over | the lid is what holds it down — its two fins sit 1 mm above the frame. With the lid off, the fan is only held by gravity. Reduce `FAN_LID_GAP` if you want it clamped tighter |
| PicoPSU won't start | PS_ON# isn't grounded (step 9) |
| Strap won't sit down | the 24-pin ATX connector is standing up under it — move the strap along the cradle |
| DC jack won't clamp | your jack's neck is shorter than 3.4 mm; reduce `DC_JACK_DEPTH` and rebuild |
| Lid won't settle | a cable or Wago is proud of the top face, or the skirt is catching on the case's outer wall — check the bead is not snagging on a proud fan insert |
| Lid won't go on at all | the skirt bead is too proud for your printer; scrape the bead or rebuild with `SKIRT_BEAD = SKIRT_CLEAR` |
| Lid drops on but is loose | raise `SKIRT_BEAD` above `SKIRT_CLEAR` and rebuild |
| Lid pulls the fan cable | it can't — the lip stops 6 mm short of the fan and the skirt is outside the case. If you feel resistance, it's the bead on a fan insert, not a cable |

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
