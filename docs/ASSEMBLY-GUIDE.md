# Assembly and mating study

Open **3D assembly → Assembly guide**. Thirty operations cover all 35 BOM records and distinguish the eight front M2.5 screws from the sixteen rear screws. Play/pause, previous/next, operation selection, progress scrubbing and speed control support inspection. Autoplay stops before a known blocked operation; explicitly playing that operation previews its illustrative motion.

The right panel identifies installed parts, mating counterparts, contact or clearance surfaces, joining method, process assumptions and outstanding release checks. Click a part link for the existing full component record below. Amber identifies the current parts, cyan the counterparts, and earlier operations are ghosted. Two nominal axial seats have analytic annular overlays. These are annotations, not CAD face selections. Other mating surfaces are described in text: the tessellated model does not currently have a persistent CAD face/mate topology map.

The JSON register is `public/data/assembly-sequence.json` and can be downloaded from the guide. It records a proposed Primeform assembly study, not an OEM procedure. All steps remain unvalidated. Source CAD supplies component positions and identities, not proof of thread ownership, interference fit, adhesive specification or installation order. Electrical subcomponents include data-only designators whose positions are not mapped.

Motion is a separated layout illustration ending at existing model positions. It is not collision-checked, does not simulate screw rotation or press loads, and does not prove installation access. Operations include subassembly preparation; future mating counterparts may be shown ghosted to explain their relationships. Individual lamination and coating meshes move in a staggered sequence. The finished frame retains known geometry errors; this change does not resolve them.

## Release blockers

- Extended main-housing bosses interfere with the provisional rotor yoke.
- Rotor end bell intersects the reference rear housing by approximately 2666.28 mm³.
- The proposed forward motor shift has not been implemented; it needs carrier and screw-tip redesign.
- Rotor/hub/sun torque connections, planet pin retention, bearing fits and race seat ownership need detailed definition.
- Fastener torque, engagement verification, insulation, bond qualification, PCB mounting, lead routing and sealing are open.

The guide intentionally records unresolved connections so the design can be reviewed joint by joint. A complete, validated assembly instruction requires closing these issues, selecting real fits/processes, attaching persistent surface references and validating both final interference and insertion paths.

Validation: `npm run test:assembly` checks BOM coverage, referenced nodes, individual laminations, playback pause at blocked joints, scrubbing, navigation and restoration of normal viewing. `npm test`, `npm run test:browser` and `npm run build` check the existing application.
