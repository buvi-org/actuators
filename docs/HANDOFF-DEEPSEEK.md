# Handoff to DeepSeek — Primeform actuator CAD and assembly viewer

Prepared 2026-09-17. Technical baseline commit: `332871a` on `main`.

## Read this first

The user is dissatisfied with the mechanical reasoning and validation. They are handing this work over, not asking for more cosmetic changes from the previous agent. The latest concrete failure is **Assembly process step 6: the input shaft hub is suspended inside the rotor end bell with no modeled connection**. The previous agent had just begun investigating it when the user requested this handoff. No corrective geometry, contact measurement, or full visual audit was completed after that complaint.

The project is **not a mechanically complete actuator**, despite having a substantial viewer, BOM, generated STEP files, and passing software tests. Several parts are illustrative proxies. “Proposed / requires validation” labels do not excuse physically meaningless assembly operations. Do not treat the current sequence, zero-overlap checks, or valid STEP solids as proof of assemblability.

Working tree was clean at handoff start. This handoff is the only intended new change after baseline `332871a`.

## Project and environment

- User: Rajesh. Organization: Primeform Robotics; public engineering repository under buvi-org.
- Repository: https://github.com/buvi-org/actuators
- Windows workspace: `C:\Users\Rajesh\Documents\ChatGPT\actuators`
- Branch: `main`; previous work committed and pushed directly there with the user's prior authorization.
- Viewer: http://127.0.0.1:5173/#model (Vite server has been running locally; check before starting another).
- Frontend: Vite 8.3.0, Three.js 0.186.0, plain JavaScript.
- Node 24 was used. Python 3.11 with CadQuery 2.7.0, trimesh 4.11.2, shapely 2.1.2, scipy and numpy; see `cad/requirements.txt`.
- Playwright 1.58.2 tests use installed Microsoft Edge (`channel: msedge`).
- `tmp/`, `node_modules/`, `dist/`, Python caches and `.venv/` are ignored. Local diagnostic files in `tmp/` are not portable repository dependencies.

## User's objective and requirements

Create an open AK80-9 V3.0 KV100 actuator design for Primeform Robotics: complete physical assembly, individual laminations/coatings, gears, rotor, stator, windings, magnets, bearings, fastening, BOM/specifications and Three.js visualization. Internal assumptions must be distinguished from manufacturer evidence.

Persistent user requirements:

1. Preserve CubeMars external dimensions and mounting interfaces. Do not solve internal problems by arbitrarily enlarging the exterior or drastically thinning one feature.
2. Every physical part must be selectable and visibility-controlled through the BOM tree, with all known details in the inspector.
3. Each gear is one physical part and one STEP solid. Teeth are not separate tree items or separate manufactured parts.
4. Individual laminations must be represented; allow steel/coating/stack-count studies.
5. Do not add duplicate external harnesses when connectors already represent the interface.
6. Assembly steps must say exactly which part is fitted to which receiving part, on which surfaces, and by what process.
7. Parts must not pass through other solid parts. Treat subassemblies as retained groups once their connections exist.
8. Call the mode **Assembly process**, not Joint review.
9. Parts are opaque and have distinct, stable colors. No section cuts inside Assembly process.
10. Earlier installed parts stay visible; separate bench preparation retains earlier members of that subassembly.
11. Step navigation/playback must preserve camera orbit, pan and zoom. Only explicit Fit step (or ordinary viewer Fit) reframes.
12. Inspect actual rendered outputs and mechanical interfaces, not only code and UI assertions.

## Immediate failure: step A06, hub to rotor end bell

Current A06 says “Attach input hub to rotor end bell,” but no attachment geometry or method is implemented.

- G03 is OEM reference occurrence `NAUO45`, one source solid. Manifest bounding box in assembly mm: x/y ±22.25; z -9.25 to +5.25. Envelope Ø44.5 × 14.5 mm. Bounding dimensions do not identify the actual contact surfaces or usable cylindrical lands.
- EM03/endbell is a procedural annulus: inner radius 23 mm, outer radius 45.5 mm, thickness 1 mm, center z -8.1 mm; axial span -8.6 to -7.6 mm.
- Therefore the displayed bell opening is Ø46 mm, larger than the hub's Ø44.5 nominal envelope. A nominal 0.75 mm radial mismatch is suggested for circular envelopes, but **no exact CAD minimum-distance/contact-face measurement was performed**. Inspect the real hub profile.
- EM03/yoke is a separate procedural annulus, radii 42.5–45.5 mm, z -7.5 to +7.5 mm. The bell ends at -7.6 mm, suggesting an additional **0.1 mm axial disconnection** between bell and yoke. This is arithmetic from the modeled extents, not an executed CAD audit.
- Sharing parent `EM03` in the tree does not join those solids mechanically.
- A06 is still incorrectly treated as an ordinary proposed stage; autoplay does not stop there. It first stops at A07, which is marked blocked.
- The hub is not proven to transfer torque to either the bell or sun shaft. Do not “fix” it merely by enlarging overlapping geometry, changing colors, or attaching a warning. Define actual receiving surfaces, retention and torque transfer, then check fit and access.

Recommended first investigation: render A06 from multiple sides, inspect source hub faces in STEP, measure separations, identify intended torque path and feasible connections within the fixed envelope, and check any proposed correction against the rear housing, bearings and stator winding space. Coordinate with the rotor axial-layout problem below.

## Current selected packaging: Choice C

The user asked to document options and provisionally choose one. Implemented in baseline `332871a`. Read `docs/PACKAGING-CHOICES.md` and `docs/STATOR-MOUNT.md`.

| Parameter | Current study value |
|---|---:|
| External reference envelope | Ø98 × 38.5 mm |
| Stator OD / bore / slot-root diameter | 80 / 60 / 68 mm |
| Radial stator back iron | 4 mm |
| Radial tooth region, including tip | 6 mm |
| Steel sheets | 68 × 0.20 mm |
| Coating | 2 micrometres per face |
| Gross stator stack | 13.872 mm |
| Stack center / ends | z 4.5 / -2.436 to +11.436 mm |
| Ring locating OD | 59.96 mm |
| Nominal radial bond gap | 0.020 mm |
| Ring full axial span | z 5.75 to 13.25 mm |
| Ring toothed band | z 5.75 to 10.75 mm |
| Ring/stator axial overlap | 5.686 mm |
| Main housing stator shoulder | z 11.436 mm, radii 30.1–33.5 mm |
| Winding proxy | radii 34.5–39 mm; z -3.3 to +12.3 mm |
| Eight front screws | M2.5 × 6, Ø54 PCD, tips z 9.95 mm |
| Nominal penetration from ring mounting face | 3.3 mm, not qualified thread engagement |
| Ring material beyond screw thread major diameter | approximately 1.73 mm |

User-approved locating concept: **ring OD provides stator radial location; housing shoulder provides axial stop**. Adhesive retention is only an unqualified proposal, not an approved fit/process.

The old Ø52 stator bore and Ø62 slot-root diameter were arbitrary initial defaults, not CubeMars measurements. They were mistakenly treated as fixed constraints in earlier reasoning. Choice comparisons retain Ø80 stator OD:

- A: bore 56, root 64 → 4 mm back iron, 8 mm radial tooth region; existing Ø54/M2.5 screw pattern breaks through a nominal Ø56 rim.
- B: bore 58, root 66 → 4 mm back iron, 7 mm tooth region; only 0.75 mm nominal outer screw-edge material before fit allowance.
- C: bore 60, root 68 → 4 mm back iron, 6 mm tooth region; selected for better existing screw packaging.

These are packaging comparisons, not electromagnetic optimization. Slot area, wire/turn count, saturation, iron/copper loss, strength and temperature have not been validated.

Choice C removed the long ring sleeve and its stator shoulder. The ring still has a front mounting rim extending **1.814 mm beyond the steel stack axially**. The entire ring fits radially inside the bore, but complete axial containment of the ring was NOT achieved. The tooth band is axially contained. This deviation is documented, not solved.

## Known mechanical problems and missing design

1. **Hub/end-bell and bell/yoke disconnections:** latest complaint, described above; not yet fixed.
2. **Rotor yoke vs housing bosses:** sixteen added Ø5 screw supports intersect the provisional yoke. Reported overlap approximately 1134.581 mm³. `cad/build_housing.py` and `public/design/housing-study.json`.
3. **Rear housing vs end bell:** reported overlap 2666.283256 mm³ with OEM NAUO4. `cad/check_rotor_clearance.py`, `public/design/rotor-clearance-validation.json`. The script/report contain OLD stator/winding positions (-6.936 and -7.8) and must be updated before drawing coordinated-layout conclusions. Bell and rear geometry remain unchanged, so the old collision remains relevant.
4. **Rotor axial alignment after Choice C:** stator moved +4.5 mm; rotor/magnets did not. Magnet span remains -7 to +7 mm, giving only 9.436 mm axial overlap with the shifted steel. Do not claim motor ratings from this arrangement.
5. **Stator retention:** ring overlap is only 5.686 mm, radial nominal gap 0.020 mm. Adhesive, tilt/runout control, torque capacity, cure, thermal path and sheet-stack retention remain unresolved.
6. **Windings and insulation:** coil bundles, solid liner envelopes and resin extent are illustrations. Shortening the radial coil bundle to fit the new roots does not prove windability, slot fill or electrical performance. Liner proxies may overlap parts and cannot be treated as detailed manufactured insulation.
7. **Planet carrier/pins/supports:** carrier is source geometry, but pin bores, retention and actual bearing/bushing selection are unresolved. Simply positioning pins and planets does not create a load-bearing carrier.
8. **Bearing ownership and retention:** exact inner/outer race mating seats, shoulders, fits, preload/endplay and assembly order need to be established for B01/B02/B03.
9. **Sun/hub connection:** torque-transfer and axial retention undefined.
10. **Electronics:** board mounts, thermal path, lead termination, capacitor placement/retention, encoder gap and routing are not released. 205 driver designators are inventory data; most physical positions are unmapped.
11. **Seals, shims and grease:** placeholder geometry; no completed groove, shim/preload, quantity or lubrication design.
12. **All insertion paths:** no full swept-volume and tool-access validation exists. The current 20-stage order is proposed, not established.

## What is actually checked

Last completed work before handoff:

- Generated ring and modified main housing each valid as one CAD solid.
- Ring STEP export/re-import valid; five-gear STEP assembly has five solids, not individual tooth solids.
- Ring nominal overlap checks against selected source bodies and stator/winding annular envelopes returned zero. See `public/design/stator-mount-validation.json` for the exact limited pair list.
- New housing shoulder vs stator/winding/ring annular envelopes returned zero overlap.
- A local check in ignored `tmp/check-choice-c.py` found modified housing vs compact ring overlap zero and unchanged housing bounding box in all six limits. This check is not yet a durable committed regression script.
- Existing gear profile study includes analytic involute generation and a sampled planar mesh-interference audit; it does not qualify gear strength, tolerances, root manufacturing process or installation paths.
- `npm test` (13 tests), `npm run test:assembly`, `npm run test:browser`, and `npm run build` passed after Choice C updates.

**Limits:** software tests check controls, visibility, color identity, unchanging positions, camera behavior, BOM references, exports and layout. They do not verify that each component is attached, that subassemblies transmit loads, or that a plausible rendered step is mechanically meaningful. Prior green tests did not catch the unsupported hub.

Prior visual QA viewed selected screenshots, not a systematic inspection of every stage from suitable angles. A full visual/contact audit has not happened. Do not repeat that omission.

## Viewer and assembly process implementation

- `src/main.js`: scene/loading, tree, inspector, selection, visibility, tabs, exports, render loop. `window.__actuator` exposes model, meshes, assembly nodes, camera, selection and assemblyGuide for browser inspection.
- `src/assembly-model.js`: procedural internals and source-node mapping. Most dimensions are hardcoded. Mesh `userData.nodeId`, `basePosition` and `explode` drive identity and placement.
- `src/assembly-guide.js`: Assembly process stage display, stable part colors, local bench context and prior installed context. No physical insertion trajectory is animated.
- `public/data/assembly-sequence.json`: 20 proposed stages, moving/receiving IDs, contexts, surfaces, process, checks and path-review text.
- Playback alternates before/after visibility states. It does not interpolate part positions. Known blocked steps stop automatic progression. Manual later previews remain possible.
- No section cuts in process mode; global Section control is hidden while active. Earlier parts remain opaque. Fit step is explicit; step changes must not reset the camera.
- Main housing source mesh and added geometry share a physical color identity. Other physical node IDs get stable distinct colors. Data-only descendants have no geometry.
- Full assembly GLB export uses base positions, not the currently displayed stage or exploded state.

Current stage order:

1. Main housing.
2. Ring/radial locator into housing.
3. Eight front screws.
4. Prepared stator onto ring OD and housing stop.
5. Rotor bench: magnets and adhesive into yoke.
6. Rotor bench: hub into end bell — **invalid attachment, latest complaint**.
7. Rotor subassembly into actuator — known clash/blocker.
8. Input bearings and sun — receiving seats unresolved.
9. Carrier bench: pins to carrier.
10. Carrier bench: supports and planets.
11. Output bearings.
12. Carrier/planet group installation.
13. Lubricant and closure materials.
14. Rear housing — known clash/blocker.
15. Sixteen rear screws — blocked by closure.
16. Encoder target magnet.
17. Populated driver board.
18. Driver cover.
19. Six driver-cover screws.
20. Output closure cover.

## CAD, data and source map

- `public/models/manifest.json`: source identity, BOM mapping, normalized mm bounding boxes, original center and source SHA. Source CAD has 43 leaf instances; original sun blank is excluded/replaced in viewer, leaving 42 source meshes plus added geometry.
- `public/models/ak80-9-reference.glb`: unchanged manufacturer reference conversion.
- `cad/build_reference.py`: obtains/converts OEM source; local source cache `tmp/reference/reference.step` is ignored.
- `cad/build_gears.py`: compact ring, eight mounting bores, source-journal sun with replaced teeth, planets, STEP and GLB exports, limited mounting validation.
- `cad/involute_geometry.py`: 20/70/160 teeth, module 0.3, 20° pressure angle, no profile shift, 0.01 mm tooth thinning per gear, 0.06 mm circular root fillets. Those fillets are not generated hob/shaper trochoids.
- `cad/check_gear_mesh.py`: sampled planar mesh audit. Ring fixed / sun input / carrier output gives 9:1. Three planet centers radius 13.5 mm, gear plane z 8.25 mm.
- `cad/build_housing.py`: preserves source main housing, adds sixteen long screw bosses and Choice C stator shoulder; exports whole modified STEP and added-material GLB for overlay on source mesh.
- `src/lamination-math.js`: default 60 mm bore / 68 mm roots and profile/stack mathematics. `src/lamination-view.js`: independent lab. Lab edits do not automatically update the full assembly.
- `scripts/export-lamination.mjs`, `cad/build_lamination.py`: default profile/DXF/STEP stack. Standalone stack is at local origin; assembly applies +4.5 mm.
- `scripts/build_bom.py`: generator for `public/data/bom.json`, `docs/BOM.md`, `docs/COMPONENT-SPECS.md`. Update generator as well as outputs.
- `public/data/packaging-choice.json`: chosen dimensions, but **not yet a single source driving all CAD/JS**. Values are duplicated across generators, JS, reports and process data. Synchronize explicitly or refactor carefully.
- `docs/PACKAGING-CHOICES.md`: current decision, alternatives, trade-offs, partial checks.
- `docs/STATOR-MOUNT.md`, `docs/HOUSING-STUDY.md`, `docs/GEAR-DESIGN.md`, `docs/INTERNAL-STRUCTURE.md`, `docs/LAMINATION-STUDY.md`: design context. Historical sections and scripts can contain superseded assumptions; current geometry takes precedence for measurement, not for validation.

Units: CAD and documented coordinates are mm; GLB/Three.js positions are metres. Procedural helpers in assembly-model generally accept mm and convert. Source positions are centered using manifest `center_original_mm`. Gear assets use local z=0 corresponding to assembly z=8.25 mm. Ring phase is π/160; its bolt holes are compensated in generator coordinates. Preserve these transforms when comparing solids or replacing geometry.

## Source evidence

- Product: https://www.cubemars.com/product/ak80-9-v3-0-robotic-actuator.html
- Drawing: https://www.cubemars.com/data/cms/202602/ak80-9-v3-0-robotic-actuator-2d-drawing.pdf
- STEP: https://www.cubemars.com/data/cms/202602/ak80-9-v3-0-robotic-actuator-3d-drawing.zip
- Manual: https://www.cubemars.com/data/cms/202602/ak-series-prodcut-manual-v3-2-0-for-ak-3-0-robotic-actuator.pdf
- Exploded illustration: https://img.cubemars.com/products/AK70_80/images/AK80-9_02.jpg
- Source register: `docs/SOURCES.md`.

Published 36 slots, 21 pole pairs, 9:1 ratio, 100 KV and exterior dimensions do not establish internal lamination dimensions, tooth counts, magnet piece count or assembly joints. Current 42 separate magnet pieces are an assumption: 42 poles does not prove 42 pieces. Published torque/current/thermal ratings belong to CubeMars hardware, not this study.

## Running and rebuilding

```powershell
npm install
python -m pip install -r cad/requirements.txt
npm run dev
```

If source STEP is absent, inspect/run `python cad/build_reference.py`. Preserve the manufacturer reference when rebuilding study geometry.

```powershell
python cad/build_gears.py
python cad/build_housing.py
python scripts/build_bom.py
npm run lamination
python cad/check_gear_mesh.py
npm test
npm run test:assembly
npm run test:browser
npm run build
```

Update `cad/check_rotor_clearance.py` for the current layout before using its coordinated-placement conclusions. Keep stdout/results from mechanical checks. Source STEP import/generation can take tens of seconds.

## Suggested continuation and acceptance criteria

1. Reproduce A06 visually, rotate to see the actual separation, and inspect hub/bell/yoke CAD surfaces. Record exact measurements and the missing torque path.
2. Audit **every stage**, not just A06: receiving parts present, correct physical subassembly membership, actual contact where intended, no accidental penetration, defined retention and access. Save labeled views and a finding table. Add connection checks, not only collision checks: zero overlap can mean a part is floating.
3. Resolve rotor/hub/end-bell design together with the shifted stator, magnets, bearings and housing bosses. Keep the external interfaces fixed. Present concrete joint proposals rather than silently assuming a press fit, weld or screw joint.
4. For each proposal, synchronize procedural viewer geometry, STEP, BOM/specifications, process steps and validation reports. Missing features must remain clear failures, not successful “attach” steps.
5. Check both static assembly and installation path/tool access. Only enable physical motion after defining and testing the moving group and stationary assembly state.
6. Render the actual changed output from multiple useful viewpoints. Re-run mechanical checks and UI tests for their distinct purposes. Report remaining failures honestly.

The prior agent's key errors were generic through-solid motion, treating proximity or shared tree parenting as assembly, assuming a bore without evidence, and claiming useful completeness from UI/build checks. The handoff should help replace those shortcuts with demonstrable mechanical connections and observed results.
