# Packaging decision: provisional Choice C

Status: selected for the current study, not approved for manufacture or rated performance. This supersedes the assumed Ø52 stator bore and long ring sleeve. Manufacturer exterior remains Ø98 × 38.5 mm with the existing mounting interfaces; internal dimensions below are Primeform choices.

## Alternatives considered

| Geometry (mm) | Previous assumption | A | B | C — selected |
|---|---:|---:|---:|---:|
| Stator OD | 80 | 80 | 80 | 80 |
| Stator bore / nominal ring location | 52 | 56 | 58 | 60 |
| Slot-root diameter | 62 | 64 | 66 | 68 |
| Radial stator back iron | 5 | 4 | 4 | 4 |
| Radial tooth region, including tip | 9 | 8 | 7 | 6 |
| Outer-edge material for M2.5 on Ø54 PCD, assuming ring OD equals bore | Not applicable to old flanged design | -0.25 | 0.75 | 1.75 |

Choice C retains useful back iron while accommodating the existing internal ring screw pattern. Choice B preserves more winding space but has only 0.75 mm outside the thread major diameter before fit allowances. Neither figure is a strength qualification. Actual selected ring OD 59.96 mm reduces C's edge material to approximately 1.73 mm.

The 4 mm back iron is a comparison choice, not a magnetic saturation calculation. The 6 mm tooth region is not usable copper area. Slot geometry, insulation, turns, conductor size, copper loss and iron loss must be evaluated together. A/B remain alternatives if C cannot meet winding requirements.

## Selected interfaces

- Stator: Ø80 OD, Ø60 bore, Ø68 slot roots, 36 teeth, 68 sheets with gross length 13.872 mm. Stack centre moves 4.5 mm forward, giving z -2.436 to 11.436 mm.
- Ring: Ø59.96 OD supplies radial location, with 0.020 mm nominal radial bond gap. Compact rim spans z 5.75 to 13.25 mm; gear teeth remain z 5.75 to 10.75 mm. The long sleeve and ring-owned stator shoulder are removed. Gear teeth, gear plane and 9:1 ratio are unchanged.
- Ring attachment: eight existing M2.5 × 6 screws on Ø54 PCD; mounting face remains z 13.25 mm, nominal screw penetration 3.3 mm. Thread capacity, tolerances and torque are not released.
- Housing: an integral annular shoulder at z 11.436 mm, radii 30.1 to 33.5 mm, stops the stator steel at its back-iron region. The annulus extends into the existing housing floor; it does not bridge the rotor swept region.
- Ring-to-stator overlap: z 5.75 to 11.436 mm, only 5.686 mm long. Adhesive is a provisional retention method. This short locating length needs tilt, runout, torque and thermal checks.
- Winding proxy: radii 34.5 to 39 mm, z -3.3 to 12.3 mm. End-turn projection beyond the steel remains 0.864 mm. Radial bundle depth is shortened; no winding capacity is claimed. The main floor at z 13.25 mm gives nominal 0.95 mm axial allowance at that winding envelope; local surface/tolerance checks remain necessary.

The complete ring lies radially within the stator bore. Its front mounting rim extends 1.814 mm beyond the steel stack axially. Full axial containment of every part of the ring is NOT achieved; that would require changing the mounting seat and screw engagement. The toothed band is axially contained by the shifted stack.

## Checks and outstanding issues

Generated ring and housing are each one valid solid. Ring STEP round-trips; gear assembly remains five solids. Nominal ring clearance is checked against source housing, rear housing, output carrier, output bearings, hub, and stator/winding envelopes. The new housing shoulder has zero calculated overlap with the selected stator, winding and ring envelopes. Source housing material is preserved, and external axial extent is unchanged.

This does not validate the full actuator. Rotor/magnets remain at their previous positions: magnet span -7 to 7 mm now overlaps the shifted steel by only 9.436 mm. Rotor axial packaging must be redesigned without sacrificing end-bell or bearing clearances. Existing boss/yoke and end-bell/rear-housing interferences remain. Short bond length, radial fit, winding capacity, structural strength, ring distortion, thermal expansion, housing machining fillets and installation paths remain open.

See `public/data/packaging-choice.json`, `public/design/stator-mount-validation.json` and `public/design/housing-study.json`. Lamination STEP/DXF exports use the selected radial profile; the standalone stack export is at its own local origin, while the assembly viewer applies the 4.5 mm offset.
