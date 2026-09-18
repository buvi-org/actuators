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

## 4. New evidence that changes the rotor problem

The magnetic rotor may not belong to `EM03` at all. The source **main housing**
`NAUO3` carries arcuate pockets measured at **r 41.766 … 43.236 mm for
z 13.001 … 16.250 mm**, which is a magnet-slot band, not a structural pocket. The
rear housing `NAUO4` has a matching band at z -8.250 … -6.001 mm. The exploded
illustration shows the same slotted plates in the rotating stack.

If the housings are the magnet carriers, then `EM03` (a separate yoke plus end
bell) is an invention that duplicates an OEM feature, and the "yoke versus
housing bosses" overlap of 1134.581 mm³ is a consequence of that invention rather
than a real interference.

This is a strong lead, not a released conclusion: confirming it needs either a
teardown or a dimensioned internal drawing. It is recorded as an open decision in
the validation JSON.

## 5. What is still unresolved

1. **Which feature drives the sun.** The hub carries both bearings coaxially with
   the sun, but the source CAD shows no key, spline, pin, clamp or press land
   between them beyond the 0.324 mm³ nominal contact. A friction-only path through
   two bearings cannot be assumed to transmit 9:1 gearbox torque. A physical sample
   or an internal drawing is required.
2. **Rotor form and carrier.** Resolve whether the rotor is the `NAUO3`/`NAUO4`
   housing pair (measurement suggests it is) or a separate shell, before drawing
   any replacement geometry.
3. **Axial layout.** The hub, both bearings and the encoder magnet fix the rotor
   module relative to the rear housing. The Choice C stator shift of +4.5 mm
   therefore has to be reconciled with the housing seat, not by translating the
   rotor. Moving the rotor also moves a real OEM part against real OEM seats.
4. **Fits and retention.** The two Ø6 locations, the Ø12 front counterbore, the
   Ø44.5 rim and the Ø2.546 through-bore need fit classes, retention and runout
   definition before any of them can be called a joint.

## 6. Next correction, in order

1. Confirm finding 4 (rotor carried by the housing) from evidence.
2. Replace the procedural rotor module with geometry derived from the measured
   OEM hub profile, and delete `EM03/endbell` and `EM03/yoke` if finding 4 holds.
3. Re-measure the rotor/housing/stator axial stack and produce a corrected axial
   layout that keeps the Ø98 × 38.5 mm external envelope and the real bearing and
   encoder positions.
4. Only then define the hub joint: receiving surface, fit class, retention and
   torque path, with a process step that names both parts and the surfaces.
