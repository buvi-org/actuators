# Validation record

## Reference geometry

- Imported the CubeMars STEP as an assembly and retained 43 unique leaf occurrence IDs.
- Reconciled all 43 occurrences to the 14 CAD-backed BOM rows.
- Counted 54 source solids, including 12 simplified solids inside the driver assembly.
- Measured a centred 98 x 98 x 38.5 mm bounding envelope and converted to metre-unit GLB.
- Parsed the exported GLB and checked for a mesh node for every source occurrence.

## Lamination geometry and calculations

- Default single-sheet solid validates in Open Cascade through CadQuery.
- Default STEP assembly contains 68 steel and 136 coating solids, 204 total.
- Axial stack height is 13.872 mm; single-sheet steel volume is approximately 377.700 mm3 for the provisional profile.
- Unit tests exercise two-sided coatings, N-1 gaps, end allowance, rounding at whole-sheet boundaries, fixed counts, worst-case tolerances, invalid inputs and monotonic layer counts as coating increases.
- Browser GLB export is checked for 204 individually named mesh nodes from the default assembly even when selected-sheet view and display spread are active.

## Browser and build checks

Automated Chromium/Edge checks exercise reference loading, selection/isolation, assembled/exploded/section modes, BOM search, lamination parameter updates, invalid-entry handling, JSON and GLB downloads, and desktop/mobile horizontal layout. Screenshots are inspected for the default stack, spread stack and actuator assembly.

`npm run build` creates a static bundle. The source uses relative asset paths for a subdirectory webview.

## Rotor hub joint audit

- `cad/check_hub_joint.py` asserts the manifest hash of the manufacturer STEP, then measures the input-shaft hub `NAUO45` and its neighbours. Results in `public/design/hub-joint-validation.json`, findings in [rotor hub joint audit](ROTOR-HUB-JOINT.md).
- Measured: the OEM hub is a body of revolution, Ø44.5 x 14.5 mm, with a 2 mm thick six-spoke flange at z -1.75 to +0.25 mm; it is coaxial with the sun shaft and carries both 6701-ZZ bearings and the encoder target magnet with zero interpenetration.
- Measured: the procedural `EM03/endbell` (46 mm opening, z -8.6 to -7.6 mm) does not touch the hub flange and has no surface that can receive it. Assembly step A06 was therefore an unsupported "attach" claim; it is now a blocked step with measured evidence.
- This is a measurement check. No fit, retention, torque capacity, runout or assembly process is qualified by it.

## Not validated

No physical dimensions were measured on hardware. No rotor/stator electromagnetic simulation, winding design, gear stress calculation, tolerance-stack release, bearing-life calculation, collision clearance of omitted internals, driver circuit verification, thermal test, load test or manufacturing release is implied. Visual clipping is uncapped; explosion offsets are inspection annotations, not a disassembly sequence.
