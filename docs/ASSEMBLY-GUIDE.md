# Assembly process

Open **3D assembly → Assembly process**. The process has 20 proposed stages starting with main housing M01, ring/support G05, eight front screws, and the complete prepared stator located radially by G05 and stopped axially by the M01 shoulder. Separate rotor and carrier preparation stages identify work performed outside the actuator. Each stage explicitly names the fitted parts, receiving parts, mating surfaces and joining method.

Previous/Next navigate assembly stages. Before fitting hides the incoming group; Proposed seated state shows it at its modeled destination. Play stages alternates these states and proceeds through the proposal, pausing before known interference steps. This is state-based playback, not a validated insertion animation: no geometry is translated through another part. A user may inspect the proposed seated state of a blocked step without implying it is physically achievable.

Parts are opaque, with normal depth writes. Each physical part instance has a stable distinct color across all stages; multiple meshes belonging to the main housing share its color. Inspector swatches identify the corresponding part colors. Incoming and receiving roles are listed explicitly instead of recoloring all parts by role.

Earlier installed parts always remain visible during actuator installation. Bench preparation shows its local rotor or carrier participants until that subassembly is installed. Future parts stay hidden except explicit receiving-part references needed to explain unresolved connections, such as rear housing bearing-seat ownership in step 8.

Section cuts and the earlier-parts toggle are removed from Assembly process. All process geometry is unclipped; the ordinary viewer's Section control is hidden while the process is active and restored on exit. Nominal seat annotation remains optional and is not a persistent CAD face selection. Fit step frames the visible assembly and the incoming parts. The inspector retains component links and complete mating/process details.

## Open mechanical work

The interface does not resolve physical design problems. Yoke/boss and end-bell/rear-housing clashes remain. Stator insertion onto the integral support, shaft/hub torque transfer, bearing seats and fits, carrier pin retention, PCB mounting and sealing still require definition. Choice C shifts the stator forward 4.5 mm; rotor realignment is not implemented. See PACKAGING-CHOICES.md. A valid insertion animation requires a defined moving subassembly, assembly state, final fit, swept clearance and tool access for that operation.

The earlier generic axial translation was removed because it did not represent assembly. Adhesive, resin and lubricant are process representations, not independently translated solids. Step order remains proposed; advancing past a blocker does not establish successful physical completion.

The downloadable register is `public/data/assembly-sequence.json`. It covers all 35 BOM records, with eight front and sixteen rear F01 screws treated separately. No OEM assembly procedure or manufacturing release is claimed.

Validation: `npm run test:assembly` checks the 20 stages, housing-first order, front screw count, before/after visibility, persistent earlier-part context, stable distinct colors, opaque rendering, no clipping, static transforms, blocking behavior, BOM references, exit restoration and mobile layout. `npm test`, `npm run test:browser`, and `npm run build` check the existing application. These checks do not certify mechanical feasibility.
