# Assembly process audit — all 20 steps

Prepared 2026-09-17 against `0ced663` plus the contact checker added here.
Reproduce with:

```powershell
python cad/check_assembly_contacts.py     # joint contact / clash, all claimed joints
python tmp/audit/step_audit.py            # sequence data integrity
node tmp/qa/audit-all-steps.mjs           # rendered state of every step
```

Rendered screenshots: `tmp/qa/steps/step-NN.png`. Data: `tmp/qa/steps/report.json`.
Machine-readable findings: `public/design/assembly-contact-validation.json`.

This is the audit the handoff said had never been done: every stage inspected for
receiving parts, real contact, undefined joints, penetration and access — not just
zero-overlap checks.

## Headline

**1 critical and 3 major defects, 4 steps blocked, 6 steps with an undefined
joint.** The gear train itself is sound. The worst defect is one I introduced in
the previous commit: **the ring is no longer clamped by any screw.**

| # | Step(s) | Severity | Defect |
|---|---|---|---|
| 1 | A03 | **critical** | Ring is not clamped: screws engage 0.0000 mm³ |
| 2 | A02, A04 | major | Ring flange no longer overlaps its own toothed band (2.000 mm short) |
| 3 | A06 | major | Carrier retained on the hub by nothing |
| 4 | A05, A14 | major | Carrier web intersects rear housing by 194.333 mm³ |
| 5 | A11 | major | Output bearings seat in neither claimed receiver |
| 6 | A14, A15 | block | Rear housing cannot seat (carrier clash) |
| 7 | A07 | block | Rotor subassembly not buildable (A06 undefined) |
| 8 | A17 | gap | 205 electronic designators are inventory only, positions unmapped |
| 9 | A01, A20 | minor | No receiving part declared (clean alone, but nothing to measure against) |

## Defect 1 — critical: the ring is not clamped (A02/A03)

Measured: the eight front screws engage **0.0000 mm³** of ring material. The ring
flange tops out at z 8.750 mm; the screw tips are at z 9.950 mm. **Gap 1.200 mm.**

Cause: when I moved the stator, winding, ring flange and housing seat 4.5 mm
rearward, I moved the ring's mounting flange but the eight screws are OEM parts
at their fixed positions (they are the Z=9.95..15.95 occurrences in the source
CAD). The clamp no longer exists.

Consequence: the ring and the stator it carries have **no load path to the
housing**. A03 currently renders as "fasten ring to main housing" with eight
screws that hold nothing — exactly the class of false step the handoff warned
about.

## Defect 2 — major: ring flange misplaced relative to its own teeth (A02/A04)

Measured: the ring's toothed band tops out at z 10.750 mm; the flange tops out at
z 8.750 mm. **2.000 mm shortfall.**

Cause: the ring gear's teeth are baked into `provisional-ring-gear.glb` at the gear
mesh plane z 8.25, but the flange is generated procedurally in `build_gears.py`
from the shifted `ring_z`. So the flange and the teeth it is supposed to carry are
now in different places.

Good news: the **gear meshes themselves are intact.** The sun (face z 4.500..12.000),
planets and ring teeth (both z 5.750..10.750) are all co-planar at z 8.25, and the
radial mesh is exact: sun pitch r 3.0 + planet pitch r 10.5 = 13.500 = declared
centre distance, and ring pitch r 24.0 − planet pitch r 10.5 = 13.500.

## Defect 3 — major: the carrier is retained by nothing (A06)

Measured: carrier web vs hub interference **0.000000 mm³**, minimum distance
**0.0000 mm** — i.e. coincident faces at r 22.25 mm and nothing else.

There is no fit class, key, screw, pin or bond defined between the carrier and the
hub. I created this part last commit to fix the empty magnet-bond step; it is
correctly *shaped* and it clears the main housing, but it is not *attached*. The
rotor torque path from carrier to hub is undefined, which is the same class of
failure as the original A06.

## Defect 4 — major: carrier web penetrates the rear housing (A05/A14)

Measured: **194.333 mm³** against NAUO4. The rear housing's inward wall is only
r 29 mm over z −5.25…−4.75 mm, while the carrier spans r 22.25…40.5 mm over
z −5…+5 mm. No axial translation fixes it: the carrier is bounded forward by the
main housing's conical bore and aft by the rear housing shoulder.

Also corrected here: the recurring **"rotor end bell vs NAUO4 = 2666.283 mm³"**
figure referred to the deleted `EM03/endbell`. I verified it reproduces exactly
against that deleted geometry, and it is now retired from A14. Separately, the
**"M02 overlaps M01 by 2666.283256 mm³"** claim in `docs/HANDOFF-DEEPSEEK.md` does
not hold for the source solids: measured **M02 ∩ M01 = 0.000 mm³**. The two
figures were the same number attached to two different claims.

## Defect 5 — major: output bearings have no seat (A11)

Measured, and reported honestly by the step's own panel ("Identify each bearing
seat owner and shoulder"):

| Bearing | vs main housing | vs lower carrier | vs 6707/625 claims |
|---|---:|---:|---|
| 6707-ZZ (B02) | 0.0000 mm³ | 0.0000 mm³ | neither |
| EZO 625-ZZ (B01) | 0.0000 mm³ | 0.0000 mm³ | neither |

Both bearings float. A11 claims seats in M01 and G01 that do not exist in the
geometry. Race ownership, shoulders and preload are undefined.

## Blocked steps

- **A06** — hub-to-carrier joint undefined (defect 3).
- **A07** — rotor subassembly not buildable, because A06 has no joint.
- **A14** — rear housing cannot seat (defect 4).
- **A15** — follows A14; also lacks thread engagement and torque values.

## Step-by-step table

Legend: **vis/total** = meshes visible in that step / total in the model.
"stray" = visible meshes that are neither this step's parts nor its target — these
are the retained earlier-installed parts, which is intended.

| Step | Title | parts (vis/total) | target (vis/total) | verdict |
|---|---|---|---|---|
| A01 | Start with the main housing | M01 2/2 | — | OK; fixture step, no receiving part needed |
| A02 | Seat ring / radial locator | G05 1/1 | M01 2/2 | **defect 2**: flange below its teeth |
| A03 | Fasten ring — eight front screws | 8 × F01 1/1 each | M01 2/2, G05 1/1 | **defect 1, critical**: 0.0000 mm³ engagement |
| A04 | Seat prepared stator | EM01 204/204, EM05 36/36, EM02 36/36, E04 1/1, EM06 1/1, C03 1/1 | G05 1/1, M01 2/2 | seat contact OK (6.936 = 6.936); 8 stray meshes unexplained |
| A05 | Rotor bench: hub and carrier, then bond magnets | EM04 42/42, C02 1/1 | EM03/web 1/1, EM03/rim 1/1 | renders correctly; **defect 4** |
| A06 | Rotor bench: hub joint — measured, not released | G03 2/2 | EM03/web 1/1 | **defect 3**, blocked |
| A07 | Install rotor subassembly | EM03/web, EM03/rim, EM04 42/42, C02 1/1, G03 | M01 2/2, EM01 204/204 | blocked; 84 stray |
| A08 | Locate input bearings and couple sun | B03 2/2, G02 1/1 | G03 2/2, M02 1/1 | hub ∩ sun = 0.324 mm³ works; **335 stray** |
| A09 | Prepare carrier: locate and retain pins | G06 3/3 | G01 1/1 | pin retention undefined (5 mm pins, no bores modelled) |
| A10 | Fit planet supports and gears | G07 3/3, G04 3/3 | G06 3/3, G01 1/1 | bearing/bushing selection unresolved |
| A11 | Seat output support bearings | B01 1/1, B02 1/1 | M01 2/2, G01 1/1 | **defect 5** |
| A12 | Install carrier and retained planets | G01, G06, G07, G04 | B01, B02, G02, G05 | 338 stray; insertion path unvalidated |
| A13 | Lubricant and closure materials | C01 1/1, C04 1/1 | G02, G04, G05, M01 | placeholders only; no quantity or groove design |
| A14 | Seat rear housing | M02 1/1 | M01 2/2, EM03 2/2, B03 2/2 | **defect 4**, blocked |
| A15 | Fasten rear housing — sixteen screws | 16 × F01 1/1 | M02 1/1, M01 2/2 | blocked by A14 |
| A16 | Attach encoder target magnet to input hub | E02 1/1 | G03 2/2 | hub ∩ magnet = 0.0000 mm³; retention undefined |
| A17 | Mount populated driver assembly | E01 11/11, E03, E05, E06, E07 6/6, E08, E09 | M02, E02, EM02 36/36, E04 | **205 designators are inventory only**; positions unmapped |
| A18 | Fit driver cover | M03 1/1 | M02 1/1, E01 11/11 | board-to-cover clearance unverified |
| A19 | Fasten driver cover — six screws | F02 6/6 | M03 1/1, M02 1/1 | thread engagement unspecified |
| A20 | Fit output closure cover | M04 1/1 | G01 1/1 | seal/preload undefined |

## What "stray" means, and one thing to check

The stray counts rise from 84 (A07) to 390 (A20) because every earlier installed
part stays visible, which is user requirement 10 and is intended. It is listed so
the behaviour is on record.

One item does deserve a look: **A04 shows 8 stray meshes** while A07 shows 84.
A04's strays are the eight front screws it does not declare in `context` — the
screws are correctly retained from A03, but the step data does not say so.

## Root cause of defects 1 and 2

Both come from my previous commit's axial change. I moved the stator, winding,
ring flange and housing seat 4.5 mm rearward but did not follow the consequences:

- the eight OEM front screws stayed where they are, so the clamp broke
- the ring flange is generated from `ring_z` while the ring teeth live in the GLB
  at the gear plane, so the flange and teeth separated

The correct fix is a decision about the ring: either the whole ring (teeth *and*
flange *and* the screws) stays with the gear train and the stator is aligned some
other way, or the ring genuinely moves and the screws, housing counterbores and the
gear train all move with it. Half-moving it is what produced both defects.

## Not defects, recorded for completeness

- Gear train geometry is exact and unchanged: 20/70/160 teeth, module 0.3, radial
  mesh centres 13.500 mm, face bands co-planar at z 8.25.
- Stator seat contact is correct: stator front face z 6.936 = housing seat z 6.936.
- Stator/magnet axial overlap is now the full 13.872 mm, up from 9.436 mm.
- Hub joints measure as designed: hub ∩ sun 0.324 mm³, hub ∩ both bearings and the
  encoder magnet 0.0000 mm³.
- The carrier clears the modified main housing by 0.000 mm³.
- M01 ∩ M02 = 0.000 mm³ and sun ∩ M02 = 0.000 mm³.
