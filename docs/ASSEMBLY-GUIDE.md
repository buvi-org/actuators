# Joint review: invalid animation withdrawn

Open **3D assembly → Joint review**. The previous animation was wrong: it applied one global axial offset to unrelated parts without validating insertion access, subassembly ownership or collisions. Its UI tests verified controls, not physical assembly. It has been removed.

All 30 records now provide a specific installation-path review. All geometry stays at its current model position. Amber marks the part under review, cyan marks its counterparts, and the entire remaining assembly is ghosted for context. Existing final-position interferences remain visible. Numbering is a review index, not an assembly order. No trajectory is currently validated or animated.

## What must change before assembly can be animated

- Build, insulate, wind, instrument and impregnate the stator in accessible tooling before evaluating installation of the resulting subassembly. Do not translate finished coils through steel teeth or send individual sheets through a closed housing.
- Prepare the rotor yoke, adhesive, magnets, hub and retention as a defined rotor subassembly. Resolve yoke/boss and end-bell/rear-housing interference before checking insertion.
- Define carrier pin bores and retention, choose planet supports, establish fits and phase the gears. Check installation of the retained carrier/planet group together rather than sliding the carrier through stationary pins and planets.
- Populate and test the PCB separately; move attached components with the board. Define mounting, lead termination, routing, strain relief and connector/cover access.
- Treat bonding, impregnation, lubrication and soldering as material processes, not rigid-body insertions.
- For each screw and bearing, define its own axis, receiving surface, shoulder, retention, insertion side and tool access. Do not infer a press fit or torque from visual overlap.

The ring/stator carrier installation order remains open. Its flange and sleeve must clear housing entrances and shoulders, while the selected stator bonding/winding process must retain access. The candidate forward motor shift also requires carrier and screw-tip redesign.

A future trajectory requires defined moving-subassembly membership, actual mating faces and assembly state, a collision-free final fit, swept-clearance verification and process/tool access checks. An analytic seat overlay or successful UI test is not that evidence.

The downloadable `public/data/assembly-sequence.json` retains all BOM coverage and identifies these gaps per joint. Two axial-seat annuli remain nominal annotations, not persistent CAD face selections. No OEM assembly procedure or manufacturing release is claimed.

Validation: `npm run test:assembly` checks all 30 reviews retain base poses, misleading playback controls are absent, joint references cover the BOM and selection/exit restore the ordinary viewer. Existing application checks are `npm test`, `npm run test:browser`, and `npm run build`.
