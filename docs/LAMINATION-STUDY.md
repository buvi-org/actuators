# Individual lamination study

The purpose is to inspect every steel sheet, see how two-sided coating consumes axial space, and choose a layer count under an explicit stack budget. This does not establish an OEM winding or magnetic design.

## Default assumptions

| Parameter | Default | Evidence |
|---|---:|---|
| Slots / teeth | 36 | CubeMars product specification |
| Outside diameter | 80 mm | Provisional study dimension |
| Bore | 52 mm | Provisional study dimension |
| Slot-root diameter | 62 mm | Provisional study dimension |
| Tooth body / tip width | 2.8 / 4.8 mm | Provisional study dimensions |
| Tooth-tip radial depth | 1.2 mm | Provisional study dimension |
| Bare steel thickness | 0.20 mm | Study assumption |
| Coating per face | 2 micrometres | Study assumption |
| Additional interface gap | 0 micrometres | Idealized packed stack |
| Available axial budget | 14 mm | Study assumption, not a measured motor stack |
| End allowance | 0 mm | Study assumption |
| Steel thickness tolerance | +/-0.005 mm | Illustrative tolerance, not a supplier guarantee |
| Coating tolerance | +/-0.5 micrometres per face | Illustrative tolerance |

The model has outward-facing teeth consistent with an outer-rotor study. The profile has no production fillets, interlocks, winding-specific slot opening, burr allowance, or validated flux path. Cutting it is not a released manufacturing instruction.

## Stack calculation

All equation terms use millimetres. Convert coating and gap inputs from micrometres by dividing by 1000.

Let `t` be bare steel thickness, `c` coating on one face, `g` additional gap/adhesive per interface, `N` the number of sheets, `B` the overall axial budget, and `a` the combined end allowance.

```text
Coated sheet thickness = t + 2c
Stack height H = N(t + 2c) + (N - 1)g
Overall height = H + a
Maximum whole-sheet count = floor((B - a + g) / (t + 2c + g))
Net axial steel = Nt
Axial steel fraction = Nt / H
Budget remaining = B - a - H
```

The outside coating faces count too: there are `2N` coated faces and `N-1` inter-sheet interfaces. For a single sheet there is no interface gap. End allowance is added once, not once per sheet. The zero-sheet case returns zero stack height.

For the default configuration: 68 sheets, 136 coated faces, 67 interfaces, 13.600 mm of steel, 0.272 mm of coating and 13.872 mm stack height. Nominal remaining budget is 0.128 mm. Geometric axial steel fraction is 98.04%.

| Coating per face | Whole sheets within 14 mm | Coated stack | Net steel |
|---:|---:|---:|---:|
| 0 micrometres | 70 | 14.000 mm | 14.000 mm |
| 1 micrometre | 69 | 13.938 mm | 13.800 mm |
| 2 micrometres | 68 | 13.872 mm | 13.600 mm |
| 3 micrometres | 67 | 13.802 mm | 13.400 mm |
| 5 micrometres | 66 | 13.860 mm | 13.200 mm |
| 10 micrometres | 63 | 13.860 mm | 12.600 mm |

Zero coating is a geometric comparison, not a recommended electrical-steel insulation system.

## Thickness tolerances

Worst-case stack height evaluates every steel/coating/gap thickness at its upper bound. Minimum coating and gap thicknesses are clamped to zero. The default 68-sheet stack spans 13.464–14.280 mm under the entered tolerances. Its upper bound exceeds the 14 mm budget.

Using maximum thicknesses in the count equation yields a conservative 66 sheets. This is a dimensional worst-case calculation, not a statistical capability estimate. The budget itself is treated as exact after subtracting the end allowance; use the minimum available budget if surrounding parts have axial tolerances.

Do not double-count coating if a steel supplier's quoted gauge already includes it. Obtain the bare-steel thickness, coating mass/thickness definition, per-face versus total coating convention, and the thickness under specified measurement pressure.

## Individual parts and exports

- Steel layers are individually selectable; each has a lower and upper coating layer.
- The display spread is an extra visual separation only. It never changes engineering quantities or exported assembled thickness.
- The selected-sheet view helps inspect one lamination's profile. It does not reduce the exported assembly to one sheet.
- Coating visibility is a display setting. Coating remains included in stack calculations and GLB export.
- STEP default assembly contains 204 solids: 68 steel sheets and 136 coatings. Zero-thickness coatings are omitted as solids.
- Browser GLB exports true assembly dimensions in metres. STEP and DXF use millimetres.
- DXF contains an external polyline and circular bore, labelled provisional. Its tessellated tooth tips and non-filleted roots are not production tooling geometry.
- Generated STEP default files are not updated by browser controls. Export the current study JSON and run the documented CAD script to create a changed STEP assembly.

## Measurements needed for a production stack

Get the actual OD, bore, full tooth/slot profile, active steel length, lamination gauge and coating specification. Also determine stack pressure, measured stacking factor, burr height/direction, insulation resistance, grade-specific iron loss at operating electrical frequencies, stack joining and end insulation. Then validate electromagnetic performance, winding insertion, thermal paths and mechanical retention.
