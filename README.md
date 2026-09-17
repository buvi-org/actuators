# Primeform Robotics Actuators

We are designing and building actuators for the Primeform Robotics division, and we are doing the work in public.

This repository will hold our actuator designs and the work behind them so they are useful to our team and to others building robotics systems. As each design develops, we plan to share design files, engineering calculations, bills of materials, assembly instructions, and test results.

## Development approach

- Share work as it develops, including early designs and experiments.
- Document design decisions, tradeoffs, and lessons from testing.
- Distinguish proposed designs from built and tested hardware.
- Welcome questions, feedback, and contributions through GitHub issues and pull requests.

## AK80-9 V3.0 KV100 reference study

Our first actuator study uses the CubeMars AK80-9 V3.0 KV100 as a reference. It is an outer-rotor motor with a 9:1 planetary reducer and integrated electronics. Published CubeMars performance is a reference target, not validated performance of a Primeform build.

The Three.js workbench includes:

- A full BOM tree with selection, hierarchical visibility, isolation, focus, and a details inspector showing specifications, sources, and unresolved information.
- The manufacturer reference contains 43 CAD instances. The combined study replaces its sun blank with one gear-and-shaft solid and adds provisional stator laminations, coating faces, winding bundles, rotor yoke, magnets, gears, pins and electronics. Manufacturer bearings and fasteners remain selectable.
- An **Internals** preset and a **Gear train** preset that exposes a toothed sun, three planets and the internal ring. The 20/70/160 tooth counts produce exactly 9:1 with the ring fixed; all three gear types use involute flanks from the STEP solids. The candidate module is 0.3 and pressure angle 20°. Manufacturing release still requires process, tolerances and strength validation.
- A Primeform housing variant with screw bosses extended to the floor, a downloadable solid STEP, and a visible warning for the measured clash with the provisional rotor yoke. Toggle the gold support material to compare the source housing. See [housing study](docs/HOUSING-STUDY.md).
- Choice C: a compact ring OD locates a Ø60-bore stator radially; a housing shoulder stops it axially. [Alternatives and decision](docs/PACKAGING-CHOICES.md). **Stator mount** exposes the joint; see [mounting design and checks](docs/STATOR-MOUNT.md).
- Single-solid sun, planet and ring gear STEP files; a gear-train STEP with five gear components (one sun, three planets, one ring). Teeth are integral geometry, never assembly components. The sun preserves source end journals and replaces its middle section; its viewer mesh is tessellated from that same solid. Rebuild with `python cad/build_gears.py`; the viewer uses meshes tessellated from the same solids.
- Full assembly GLB export, including reference geometry and annotated provisional bodies. The separate Lamination lab remains independently configurable; its settings do not currently change the assembly study.
- A 35-line engineering BOM distinguishing source CAD, published data, illustration inferences and unresolved items. External mating cables are documented under the power/CAN and UART connectors, without separate internal BOM quantities or cable geometry.
- An inventory of 205 driver-board reference designators and package-model labels. Component values and exact IC part numbers remain unknown. These inventory entries are selectable data records; individual PCB positions are not mapped to the actuator assembly, so their visibility controls are disabled.
- An original, provisional lamination study with individually selectable steel sheets and two coating layers per sheet, editable profile dimensions, coating/gap/tolerance calculations, and live study quantities.
- GLB, DXF, JSON and default solid STEP deliverables.

**This is a reference and design study, not a manufacture-ready AK80-9 clone.** The manufacturer STEP omits the working motor stack and planetary internals. The lamination profile is an independently authored placeholder; only its default 36-slot count comes from the manufacturer specification.

### Run the workbench

Requires Node.js 22.12+ or a compatible newer release (tested with Node 24).

```sh
npm ci
npm run dev
```

Open `http://127.0.0.1:5173/`. Use `#lamination` to open the individual-sheet study directly. The viewer uses local Three.js/model assets; Google Fonts is optional and falls back to system fonts.

```sh
npm test
npm run build
npm run preview
```

Browser interaction checks: run the dev server, then `npm run test:browser`. The default browser is installed Microsoft Edge; set `BROWSER_CHANNEL=chrome` to use Chrome. Test outputs stay in ignored `tmp/qa/`.

### Design and evidence files

| Item | Location |
|---|---|
| Engineering BOM | [docs/BOM.md](docs/BOM.md) |
| Per-component specifications | [docs/COMPONENT-SPECS.md](docs/COMPONENT-SPECS.md) |
| Internal structure findings and questions | [docs/INTERNAL-STRUCTURE.md](docs/INTERNAL-STRUCTURE.md) |
| Electronic reference-designator inventory | [docs/DRIVER-INVENTORY.md](docs/DRIVER-INVENTORY.md) |
| Lamination equations and manufacturing limits | [docs/LAMINATION-STUDY.md](docs/LAMINATION-STUDY.md) |
| Source register and attribution | [docs/SOURCES.md](docs/SOURCES.md) |
| Reference GLB and part manifest | [public/models/](public/models/) |
| Original provisional sheet and stack STEP/DXF | [public/design/](public/design/) |
| Machine-readable BOM and specifications | [public/data/](public/data/) |

### Rebuild CAD and engineering data

Python 3.11 is tested. Install CAD dependencies in your chosen environment:

```sh
python -m pip install -r cad/requirements.txt
python cad/build_reference.py
python cad/extract_driver_inventory.py
python scripts/build_bom.py
npm run lamination
```

The first two commands download the manufacturer's ZIP files into ignored `tmp/reference/`. The conversion preserves source occurrence IDs, records the STEP hash, transforms the assembly to a centred coordinate system and converts millimetres to metres for GLB. Visual colours and explosion offsets are our annotations.

To make solid CAD for a changed lamination configuration, export **Study JSON** from the webview, then run:

```sh
python cad/build_lamination.py path/to/lamination-study.json
```

This updates the generated STEP files in `public/design/`. Browser **Stack GLB** always exports the current full assembly at true thickness, independent of display spread or the selected-sheet view. It uses metres; STEP and DXF use millimetres.

See [involute gear design and manufacturing release requirements](docs/GEAR-DESIGN.md) for the matched candidate, equations, checks and unresolved inputs.

## Licensing

The repository is public. Licenses for Primeform's hardware studies, software and documentation have not yet been selected; public access alone does not grant a license to reuse those materials. Manufacturer reference geometry remains attributed to CubeMars. It is not an original Primeform design or covered by a Primeform open-hardware license. See [source attribution](docs/SOURCES.md).
