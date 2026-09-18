# Assembly process audit — all 20 steps

Prepared 2026-09-17. Current status after the layout and rotor-shell corrections. Reproduce with:

```powershell
npm test                       # runs the geometry checks first, then the unit tests
npm run test:geometry          # intersections, contacts, hub joint, ring clamp
python cad/check_intersections.py   # pairwise matrix for every modelled body
python cad/check_assembly_contacts.py   # joint contact / gap, all claimed joints
python cad/check_ring_clamp.py          # the eight front screws vs the ring
node tmp/qa/audit-all-steps.mjs         # rendered state of every step
```

Rendered screenshots: `tmp/qa/steps/step-NN.png`.
Machine-readable findings: `public/design/intersection-matrix.json`,
`public/design/assembly-contact-validation.json`.

Step numbers below are the ones shown in the app (`step 1` … `step 20`). The
`A01`-style ids are the internal names for the same rows.

## Interpenetration is now a test, not an inspection

The project had no intersection test. Every geometry regression so far — a hub with no
attachment, a solid ring of 43,791 mm³, magnets cutting 137.7 mm³ into the shell — was
a body passing through another body, and no test caught any of it.

`cad/check_intersections.py` now tests **every pair of modelled bodies** (1,225 pairs
across 50 bodies) in the assembled state and reports two things separately:

- **interpenetration**: the volume of the boolean intersection
- **intended contact**: whether a claimed joint actually touches

It runs as the first step of `npm test`, so `npm test` fails if a body passes through
another. Current result:

| Check | Result |
|---|---|
| Bodies tested | 50 |
| Pairs tested | 1,225 |
| Interpenetrating pairs | **2, both intended fits** |
| Unintended interpenetration | **0** |
| Magnet clashes | **0** (was 42 pairs at 137.7 mm³ each) |
| Intended contacts present | **6 of 6** |

The two remaining overlaps are the fits that are supposed to interfere: hub ∩ sun =
0.324 mm³ (the measured pilot fit) and the housing joint faces at 0.000 mm³.

## The magnet defect that test found

The magnets were cutting **137.7 mm³ into the shell, 42 times over** — visible in the
render as segments buried in the rim. Two causes:

1. the magnets' outer radius (42.5 mm) exceeded the shell's bore band outer face
   (42.4 mm)
2. the spoked web and the magnet band shared the same axial band (web z 0.25…2.25,
   magnets z −2.5…11.5), so every spoke passed through every magnet

The web could not simply move: the hub is only r 22.25 over z −1.75…0.25 and r 6…7
elsewhere, so the web has to sit on the hub's Ø44.5 flange. The shell is now built the
way a real rotor shell is: **the rim is pocketed** — 42 pockets machined to the same
angular width as the segments — and the segments seat in them with zero interference.

| | Before | After |
|---|---|---|
| Shell material | 43,791 mm³ (solid ring) | **2,274 mm³ (pocketed, spoked)** |
| Shell bodies | 2 (invented joint) | **1 connected, valid solid** |
| Magnet interference | 42 pairs × 137.7 mm³ | **0** |
| Shell vs both housings and the hub | clashing | **0.000 mm³** |


## The correction that removed the defects

Two corrections were needed.

**First, the direction of the axial move.** An earlier revision moved the stator,
winding, ring mounting flange and housing seat 4.5 mm rearward. That moved
manufacturer hardware and broke two things:

- the eight front screws stayed at their fixed positions, so the ring clamp was
  destroyed (engagement measured **0.0000 mm³**)
- the ring flange is generated from `ring_z` while the ring teeth live in the gear
  GLB at the gear plane, so the flange and its teeth separated by **2.000 mm**

Moving the ring instead is not an option: it would leave only **0.500 mm** of axial
overlap with the planets where a full 5.000 mm face is needed.

**The fix reverses the direction.** The ring, stator, winding, housing seat and
gear train stay where the manufacturer put them, and the study's own invented rotor
shell moves forward 4.5 mm to meet the stator. Only invented geometry moves.

**Second, the rotor shell was split into two parts when the manufacturer makes it as
one.** The real part is a single spoked shell whose outer rim carries the magnets,
with the sun force-fitted into it. The study had modelled a separate disc plus a
separate rim, which invented a joint that does not exist and produced a 7.75 mm
thick solid ring of 43,791 mm³ — a solid-of-revolution shortcut, not a design.
The shell is now **one connected solid** of **7,482 mm³**: a six-spoke web on the
hub's Ø44.5 front face, an outer rim carrying the magnets on its Ø81 bore, and a
closing flange at the rear.

| Check | Before | After |
|---|---|---|
| Ring clamp (step 3) | 0.0000 mm³, **not clamped** | **8/8 screws engaged, 10.89 mm³** |
| Ring flange vs its teeth (step 2) | 2.000 mm short | overlaps the toothed band |
| Stator front face vs seat (step 4) | — | **contact at z 11.436 = 11.436** |
| Stator/magnet axial overlap | 13.872 mm | **13.872 mm of 13.872 (full)** |
| Rotor shell parts | 2 solids (invented joint) | **1 connected, valid solid** |
| Rotor shell material | 43,791 mm³ (solid ring) | **7,482 mm³ (spoked)** |
| Rotor shell vs rear housing | 194.333 mm³ clash | **0.000 mm³** |
| Rotor shell vs main housing / hub | 0.000 mm³ | **0.000 mm³** |
| Gear face overlap | 5.000 mm | **5.000 mm (full)** |

## The rotor is ONE machined body

The decisive evidence was the manufacturer photograph: the shell's web flows straight
into the central hub boss, and the sun is pressed into it. The hub and the shell are
**one machined part**, not two parts to be joined.

Everything before this had modelled them separately and then argued about how to join
them — which invented a joint the manufacturer does not have, and produced the whole
A06 blocker. `cad/build_rotor.py` now takes the **measured OEM hub** as the starting
point and machines the shell onto it as **one connected solid**:

| | Value |
|---|---|
| Bodies | **1** connected, valid solid |
| Volume | 5,388 mm³ |
| Envelope | Ø84.8 × 20.5 mm, z −9.25 … +11.25 |
| Hub portion | measured OEM NAUO45: six-spoke flange r 17.145…22.25, Ø6 / Ø12 / Ø5.95 bores |
| Shell portion | six-spoke web out of the hub flange; rim r 40.5…42.4 with 42 magnet pockets |
| Sun fit | measured 0.324 mm³ pilot contact, z 3.75…5.25 |
| Unintended interference | **0.000 mm³** against both housings |

**Blocked steps: none.** A06 was "hub retention — not defined"; it is now
"press the sun into the rotor", a real operation. A07 is "install the rotor over the
stator". Both remain `Proposed / requires validation` because fit classes, torque
capacity, press tooling and the insertion path are not defined — but they are no
longer structurally impossible.



## Dimensioned diagrams

Selecting any part in the tree shows a dimensioned axial section in the inspector,
generated from the mesh actually on screen (`src/part-diagram.js`). Every number is
measured from the displayed geometry, so a diagram cannot disagree with the model it
describes. Measured examples:

| Part | Axial | Max Ø | Bores |
|---|---|---|---|
| Rotor, one piece (G03) | 20.5 mm | Ø84.8 | Ø44.5, Ø34.3, Ø12 |
| Ring (G05) | 7.5 mm | Ø59.96 | Ø49.8, Ø47.45, Ø47.4 |
| Main housing (M01) | 24.2 mm | Ø98 | Ø95, Ø94.56, Ø93.78 |

## Where it stands

**No step is blocked. All 20 are geometrically consistent. Eight carry open
engineering items that are not geometric.**

| # | Step(s) | Status | Issue |
|---|---|---|---|
| 1 | step 6 | open | Sun-to-rotor press: fit class, retention, press tooling and torque capacity undefined |
| 2 | step 7 | open | Rotor insertion over the stator: 0.5 mm nominal air gap, path and lead-in not defined |
| 3 | step 11 | open | Both output bearings float: 6707-ZZ and 625-ZZ each 0.0000 mm³ against both claimed receivers |
| 4 | steps 9, 10 | open | Planet pin retention, pin bores and bearing/bushing selection undefined |
| 5 | step 13 | open | Lubricant and seal are placeholders: no groove, shim, preload or quantity |
| 6 | step 15 | open | Sixteen screw thread engagement and tightening torque unspecified |
| 7 | step 17 | open | 205 electronic designators are inventory records only; board positions unmapped |
| 8 | steps 19, 20 | open | Six screw thread engagement; output closure seal and preload undefined |

Steps 1, 2, 3, 4, 5, 8, 12, 14, 16 and 18 are internally consistent and measured.

## The joint that used to block, and why it no longer exists

A06 used to hinge on **how the magnet-carrying shell attaches to the hub**. The
measured answer was 0.000000 mm³ interference at 0.000000 mm distance: coincident
faces with no fit, key, screw or bond, so the rotor torque path was undefined.

That question is now dissolved rather than answered. The manufacturer photograph
shows the shell's web flowing straight into the central hub boss, with the sun
pressed into it: **the hub and the shell are one machined part.** Modelling them as
two bodies and then trying to join them invented a joint that does not exist.

`cad/build_rotor.py` takes the measured OEM hub and machines the shell onto it as one
connected solid, so there is nothing to join. A06 becomes a real operation — press the
sun into the rotor — and the fit it relies on is the measured 0.324 mm³ pilot contact
on the Ø5.95 counterbore.

## Step-by-step table

**vis/total** = meshes visible in that step / total in the model. "stray" = visible
meshes that are neither this step's parts nor its target — the retained
earlier-installed parts, which is intended.

| App step | parts (vis/total) | target (vis/total) | verdict |
|---|---|---|---|
| 1 | M01 2/2 | — | OK; fixture step |
| 2 | G05 1/1 | M01 2/2 | OK; flange now overlaps its toothed band |
| 3 | 8 × F01 1/1 each | M01 2/2, G05 1/1 | **OK; 8/8 engaged, 10.89 mm³** |
| 4 | EM01 204/204, EM05 36/36, EM02 36/36, E04, EM06, C03 | G05 1/1, M01 2/2 | OK; seat contact exact |
| 5 | EM04 42/42, C02 1/1 | EM03/web 1/1, EM03/rim 1/1 | OK geometry; carrier retention open |
| 6 | G03 2/2 | EM03/web 1/1 | **blocked**: carrier-to-hub joint undefined |
| 7 | EM03/web, EM03/rim, EM04 42/42, C02, G03 | M01 2/2, EM01 204/204 | **blocked** by step 6 |
| 8 | B03 2/2, G02 1/1 | G03 2/2, M02 1/1 | OK; hub ∩ sun 0.3241 mm³, bearings 0.0000 mm³ |
| 9 | G06 3/3 | G01 1/1 | pin retention undefined |
| 10 | G07 3/3, G04 3/3 | G06 3/3, G01 1/1 | bearing selection unresolved |
| 11 | B01 1/1, B02 1/1 | M01 2/2, G01 1/1 | **open**: both bearings float |
| 12 | G01, G06, G07, G04 | B01, B02, G02, G05 | insertion path unvalidated |
| 13 | C01 1/1, C04 1/1 | G02, G04, G05, M01 | placeholders only |
| 14 | M02 1/1 | M01 2/2, EM03 2/2, B03 2/2 | **unblocked**: 0.000 mm³ clash on all sides |
| 15 | 16 × F01 1/1 | M02, M01 | **unblocked**; torque unspecified |
| 16 | E02 1/1 | G03 2/2 | OK contact; retention undefined |
| 17 | E01 11/11, E03, E05, E06, E07 6/6, E08, E09 | M02, E02, EM02 36/36, E04 | positions unmapped |
| 18 | M03 1/1 | M02 1/1, E01 11/11 | clearance unverified |
| 19 | F02 6/6 | M03 1/1, M02 1/1 | torque unspecified |
| 20 | M04 1/1 | G01 1/1 | seal/preload undefined |

## Measurements that are sound

- Gear train: 20/70/160 teeth, module 0.3. Sun pitch r 3.0 + planet r 10.5 = 13.500 =
  declared centre distance; ring pitch r 24.0 − planet r 10.5 = 13.500. Face bands
  co-planar at z 8.25 with the full 5.000 mm overlap.
- Stator seat: stator front face z 11.436 = housing seat z 11.436.
- Hub: Ø44.5 × 14.5 mm revolution body, six-spoke flange r 17.145…22.25 at
  z −1.75…+0.25; carries both 6701-ZZ bearings and the encoder magnet at
  0.0000 mm³ interference.
- Hub ∩ sun = 0.3241 mm³ confined to z 3.750…5.250, with a keyed/flat feature
  (0.2022 mm azimuthal spread) on the sun journal.
- Rotor shell (web r 22.25…40.5 z −2.5…+5.25; rim r 40.5…42.4 z +5.25…+11.5):
  0.000 mm³ against both housings and the hub.
- M01 ∩ M02 = 0.000 mm³.

## Figures retired in this audit

- **"Rotor end bell vs NAUO4 = 2666.283 mm³"** referred to the deleted procedural
  `EM03/endbell`. It reproduces exactly against that deleted geometry, so the number
  was real but the part no longer exists. Removed from step 14.
- **"M02 overlaps M01 by 2666.283256 mm³"** (from the handoff) does not hold for the
  source solids: measured **M02 ∩ M01 = 0.000 mm³**. The same number had been
  attached to two different claims.
- **"Extended supports intersect the provisional yoke by 1134.581 mm³"** is still
  reported by `build_housing.py`, but the support bosses are at r 27 ± 2.5 mm while
  the yoke was at r 42.5…45.5 mm, so the two cannot overlap. This figure needs
  re-deriving or retiring.

## Known limits

Contact and clash are measured. Fit classes, torque capacity, preload, insertion
paths, tool access and electrical routing are not. "No clash" in this document means
no interpenetration in the modelled state — it does not mean the joint is designed.
