# Rotor hub / end bell joint audit — measurement record

Prepared 2026-09-17 against baseline `dd09154`. Reproduce with:

```powershell
python cad/check_hub_joint.py
```

Output: `public/design/hub-joint-validation.json`. Source geometry is the
manufacturer STEP revision recorded by `manifest.source_sha256`; the checker
asserts that hash before measuring, so these numbers cannot silently drift from
the reference model.

This replaces the arithmetic in the handoff. Everything below is a measurement of
the source CAD in the assembled, centred millimetre frame, or an explicit
statement that the measurement is impossible with the current modelled geometry.

## 1. What the OEM input-shaft hub actually is

Occurrence `NAUO45` (`AK80-9输入轴-2`), mapped in the BOM as `G03` "Input shaft
hub". Measured, it is **a body of revolution about the motor axis**, not a disc
with a bore. The X-Z material section is:

| z range (mm) | material radius (mm) | feature |
|---|---|---|
| -9.250 … -8.750 | 3.0, 5.55 … 5.95 | rear lead-in |
| -8.750 … -6.750 | 3.0, 6.0 | rear land, Ø6 bore |
| -6.750 … -3.250 | 2.0, 6.0 | Ø4 bore, Ø12 outer |
| -3.250 … -2.750 | 2.0, 7.0 | Ø14 shoulder |
| -2.750 … -1.750 | 2.0, 17.145 | flange back face, Ø34.29 |
| -1.750 … +0.250 | 2.0, 18.975, 21.025, 22.25 | spoked flange: Ø35.5 pocket, Ø42.05 rim, Ø44.5 outer |
| +0.250 … +1.250 | 2.0, 7.0 | Ø14 collar |
| +1.250 … +3.250 | 2.0, 6.0 | front land |
| +3.250 … +4.750 | 2.975, 6.0 | front counterbore Ø5.95 |
| +4.750 … +5.250 | 2.975, 5.55 … 5.95 | front lead-in |

Key numbers:

- Outer envelope Ø44.5, length 14.5 mm, volume 3114.2 mm³ (matches the manifest).
- Flange: r 17.145 → 22.25 mm (Ø34.29 → Ø44.5) over z -1.75 → +0.25 mm, so the
  web is **2 mm thick** with six spokes, a Ø35.5 annular pocket and a Ø42.05 rim.
- Bores: a 12 mm counterbore (see below), a Ø4 middle bore, a Ø6 rear bore and a
  Ø5.95 front counterbore.
- A Ø2.546 mm cylindrical face runs z -6.75 → +3.25 mm: the through-bore.

## 2. It is coaxial with the sun and carries both bearings

Boolean interference against the neighbouring occurrences (mm³):

| pair | interference | reading |
|---|---:|---|
| hub `NAUO45` ↔ sun `NAUO41` | 0.324 | coaxial, nominal line-to-line contact only |
| hub ↔ 6701-ZZ rear `NAUO42` | 0.000 | coaxial, no interpenetration |
| hub ↔ 6701-ZZ front `NAUO43` | 0.000 | coaxial, no interpenetration |
| hub ↔ encoder target magnet `NAUO44` | 0.000 | coaxial, no interpenetration |
| hub ↔ rear housing `NAUO4` | 0.000, min distance 0.500 | clears the housing |
| hub ↔ main housing `NAUO3` | 0.000 | clears the housing |

The STEP hierarchy confirms the grouping: one subassembly holds `NAUO41` (sun),
`NAUO42`/`NAUO43` (both 6701-ZZ), `NAUO44` (encoder magnet) and `NAUO45` (hub).
The hub is the bearing carrier of that coaxial module. It is **not** an outboard
end-bell disc that a hub bolts onto.

## 3. Why assembly step A06 attaches nothing

The viewer's rotor shell is procedural and does not share this form.

| | procedural `EM03/endbell` | measured OEM hub |
|---|---|---|
| form | plain annulus | body of revolution, six-spoke flange |
| opening / envelope | 46 mm opening (r 23) | Ø44.5 envelope (r 22.25) |
| z band | -8.6 … -7.6 mm | flange at -1.75 … +0.25 mm |

Three independent defects, each sufficient on its own:

1. **No contact.** The end-bell band and the hub flange band do not intersect in
   z at all — they are 6.85 mm apart at the nearest faces.
2. **No receiving surface.** Even if the two were brought into one plane, a 46 mm
   opening cannot receive a 44.5 mm body as a fit; the end bell has no bore, land,
   shoulder or counterbore sized for the hub.
3. **Wrong form.** The OEM part is a revolution body with a spoked flange; the
   procedural part is a flat annulus. Replacing one with the other is a geometry
   change, not a dimension tweak.

The rotor shell is not joined to itself either: `EM03/endbell` ends at z -7.6 mm
and `EM03/yoke` begins at z -7.5 mm, a modelled 0.1 mm axial gap. Sharing parent
`EM03` in the tree connects nothing.

**Conclusion.** A06 previously read "Attach input hub to rotor end bell" with
status "Proposed / requires validation". No attachment geometry, retention or
torque path existed. It is now marked `Blocked by known geometry`, and autoplay
stops on it instead of overshooting to A07.

## 4. The drive interface the CAD does encode

Sectioning the sun across the contact band and classifying each section (plain
loop vs azimuthal radius spread vs loop count) resolves the earlier open question:

| Measurement | Value |
|---|---|
| Contact volume | 0.324 mm³ |
| Contact axial band | z 3.750 … 5.250 mm |
| Fit at that band | sun front journal Ø6.000 into hub counterbore Ø5.950 |
| Sun section across the band | one loop, r 2.4185 … 3.000 |
| Azimuthal radius spread | **0.2022 mm** → a keyed or flat (D) drive feature |

So the hub does not merely retain the sun on bearings: its front counterbore
pilots the sun's keyed front journal over 1.5 mm of engagement. That is the
measured torque path from the rotor side into the sun, and it is why the earlier
"friction through two bearings" reading in this document was wrong.

**Caveat.** A 0.202 mm azimuthal spread measured from a CAD tessellation is
evidence of a drive feature, not a released key or spline specification. Confirm
it against hardware before designing to it.

No key, keyway, spline or cross-pin appears anywhere on the sun's rear Ø4.0
section.

## 5. What was implemented

1. **The real hub is in the model.** `cad/build_hub.py` re-exports occurrence
   `NAUO45` from the source STEP as `public/design/oem-rotor-hub.step` and
   `public/design/oem-rotor-hub.glb` (one valid solid, 3114.2 mm³, Ø44.5 × 14.5).
   The viewer shows it as assembly item `G03`, replacing the procedural
   `EM03/endbell` and `EM03/yoke` annuli, which have been deleted.
2. **The hub joint is described from measurement.** Assembly step A06 now names
   the actual surfaces: the Ø5.95 counterbore onto the sun's Ø6.0 keyed journal
   over z 3.75…5.25 mm, plus the Ø12 and Ø6 bearing bores and the encoder-magnet
   seat.
3. **The stator shift was reversed.** The rotor's axial position is fixed by real
   OEM features (the hub, both 6701-ZZ bearings, the encoder magnet), so the
   Choice C **+4.5 mm stator shift was the error**. The stator, winding, ring
   mounting flange and housing seat all moved 4.5 mm rearward, so the 13.872 mm
   steel stack now spans z −6.936…+6.936 mm and overlaps the full magnet span
   (−7…+7 mm) instead of 9.436 mm. The gear mesh itself is deliberately unchanged:
   the sun stays on the OEM shaft journals.
4. **Reports and data were regenerated**, not hand-edited: `build_gears.py` and
   `build_housing.py` now derive everything from a single `SHIFT` constant, and
   `stator-mount-validation.json`, `housing-study.json` and
   `packaging-choice.json` follow.

## 6. What is still blocked, and why

A06 remains `Blocked by known geometry`, for a different and better-understood
reason than before.

The hub's flange ends at **r 22.25 mm**. The nearest housing wall is at
**r 47.4 mm**. That is a **25.15 mm radial gap**, and the source CAD contains no
web, spider, bell or disc joining the hub to the rotor shell. So:

- The hub **is** measured, correctly shaped and correctly placed.
- The **hub-to-sun joint is real** and measured.
- The **hub-to-rotor-shell joint does not exist in the evidence**. Until it is
  designed, the hub has no rotor torque input and A07 has no rotor to install.

Two further open items:

1. **Rotor radial placement.** The study yoke (r 42.5…45.5) and magnet band
   (r 40.5…42.5) do not coincide with the arcuate slots in the source housings
   (r 41.766…43.236). The housings' slots do not match the study's 42-segment
   band either, so the source model does not settle where the magnets belong.
2. **The housing-boss clash.** The added supports still intersect the provisional
   yoke by 1134.581 mm³. It is unchanged by the axial realignment, because the
   yoke spans z −7.5…+7.5 and the supports run the housing floors.

## 7. Next correction, in order

1. Design and validate the hub-to-shell connection that closes the 25.15 mm gap,
   or establish from hardware that the OEM achieves it with a feature absent from
   the published STEP.
2. Resolve the rotor radial envelope so the yoke clears the housing bosses and the
   magnets sit on a justified radius.
3. Release the Ø5.95/Ø6.0 keyed pilot fit: fit class, retention, runout, balance
   and torque capacity against the 9:1 gearbox input.

