# Component specifications

## M01 — Main housing

Quantity: 1 ea. Evidence: Reference CAD + Primeform modification.

- **CAD envelope:** Ø98 x 24.2 mm
- **Assembly envelope:** Ø98 x 38.5 mm
- **Mounting:** 8 x M3 on Ø85 PCD (drawing)
- **Primeform housing R1:** Sixteen 5 mm diameter screw supports extended to housing floors; 16 source screw bores preserved. Gold supports can be hidden to compare source geometry.
- **Known clearance conflict:** Extended supports intersect the provisional rotor yoke. Rotor diameter and housing clearance must be reconciled.
- **Side holes measured from STEP:** One pair has diameter 2.1 mm on +Y side; opposite pair has diameter 3.2 mm. Pair centres x = ±6 mm, z = 3.25 mm in viewer coordinates. Functions and thread specifications unconfirmed.
- **Radial spaces:** Clearance and unfilled material between screw bosses; no OEM functional designation established. Do not treat as validated spare volume.
- **Material:** OEM grade unspecified; aluminium alloy is a proposed material family only
- **Make/buy:** Proposed: CNC turning + milling; finish and datums to be specified
- **Unresolved:** Alloy, heat treatment, wall tolerances, bearing fits, surface finish and ring-gear attachment are unverified. R1 needs rotor-clearance redesign and cutter-access/fillet validation. Side-hole purpose needs OEM confirmation; retain existing holes.
- **Source references:** S2, S3

## M02 — Rear housing

Quantity: 1 ea. Evidence: Reference CAD.

- **CAD envelope:** Ø98 x 9 mm
- **Known interference:** Source rear housing intersects the provisional rotor end bell; see rotor-clearance-validation.json. This is not an exploded-view artifact.
- **Material:** OEM grade unspecified
- **Make/buy:** Proposed: CNC turning + milling
- **Unresolved:** Verify locating pilot, concentricity, thermal contact, fastener engagement and finish.
- **Source references:** S3

## M03 — Driver cover

Quantity: 1 ea. Evidence: Reference CAD.

- **CAD envelope:** Ø71 x 11 mm
- **OEM drawing code:** BJJ02040285
- **Material:** OEM grade unspecified
- **Make/buy:** Proposed: CNC machining
- **Unresolved:** Material, insulation clearances, sealing and thermal path need definition.
- **Source references:** S3

## M04 — Closure cover

Quantity: 1 ea. Evidence: Reference CAD.

- **CAD envelope:** Ø14 x 2 mm
- **Material:** OEM grade unspecified
- **Make/buy:** Proposed: turned disc
- **Unresolved:** Retention method, tolerance and functional purpose require teardown confirmation.
- **Source references:** S3

## G01 — Output carrier

Quantity: 1 ea. Evidence: Reference CAD.

- **CAD envelope:** Ø37 x 7.5 mm
- **Output interface:** 6 x M4 on Ø28 PCD (drawing)
- **Material:** OEM grade unspecified
- **Make/buy:** Proposed: machined carrier
- **Unresolved:** Pin attachment, torque path, material, fits and fatigue margin need validation.
- **Source references:** S2, S3

## G02 — Sun gear / input shaft

Quantity: 1 ea. Evidence: Source journals + provisional toothed section.

- **CAD bounding box:** 6.717 x 6.717 x 21.5 mm
- **Assembly ratio:** 9:1 (not a tooth-count specification)
- **Current study solid:** One gear-and-shaft solid. Source journals retained; z 3.75 to 11.25 mm replaced by a 20-tooth involute candidate, module 0.3, pressure angle 20 degrees, face width 7.5 mm. Current tip diameter 6.6 mm; original source envelope listed separately.
- **Representation:** Viewer GLB tessellated from the same solid as provisional-sun-gear.step; source blank excluded from combined study.
- **Primeform matched gear candidate:** 20 teeth; module 0.3; pressure angle 20 degrees; zero profile shift
- **Candidate backlash:** 0.020 mm circular per mesh at nominal centres, from 0.010 mm tooth thinning per gear; not a manufacturing tolerance
- **Root transition:** 0.060 mm circular fillets; not a hob/shaper-generated trochoid
- **Ratio and assembly:** 20 / 70 / 160 teeth; ring fixed, sun input, carrier output: exactly 9:1; three planets at 120 degrees; centres 13.5 mm
- **Release blockers:** Cutting process, steel grade, heat treatment, gear quality, tooth-thickness tolerances, strength, fatigue, lubrication and loaded contact checks
- **Material:** OEM steel and hardness unspecified
- **Make/buy:** Proposed: gear cutting, heat treatment, finish grinding
- **Unresolved:** Tooth count, module, pressure angle, profile shift, hardness, case depth and spline/shaft fits remain unresolved. Study tooth profile is not a manufacturing design. Verify involute geometry, profile shift, root strength, mating gears and axial fits.
- **Source references:** S1, S3

## G03 — Input shaft hub

Quantity: 1 ea. Evidence: Reference CAD.

- **CAD envelope:** Ø44.5 x 14.5 mm
- **Material:** OEM material unspecified
- **Make/buy:** Proposed: precision machining
- **Unresolved:** This is a hub within the rotor assembly, not a complete electromagnetic rotor. Magnet/yoke integration is absent.
- **Source references:** S3

## B01 — 625-ZZ bearing

Quantity: 1 ea. Evidence: Reference CAD.

- **Bore x OD x width:** 5 x 16 x 5 mm
- **Shielding:** ZZ, two metal shields
- **CAD OEM code:** C0105000059 / EZO
- **Material:** Verify supplier steel, cage and lubricant
- **Make/buy:** Buy: EZO 625ZZ or qualified equivalent
- **Unresolved:** Select clearance, fit, grease and life from actual radial/axial/moment loads. Do not assign actuator load ratings to this bearing.
- **Source references:** S3, S4

## B02 — 6707-ZZ bearing

Quantity: 1 ea. Evidence: Reference CAD.

- **Bore x OD x width:** 35 x 44 x 5 mm
- **Shielding:** ZZ
- **CAD OEM code:** C0105000031
- **Material:** Verify supplier steel, cage and lubricant
- **Make/buy:** Buy: qualified 6707ZZ
- **Unresolved:** OEM supplier, clearance, load ratings, preload and fit are unspecified.
- **Source references:** S3, S5

## B03 — 6701-ZZ bearing

Quantity: 2 ea. Evidence: Reference CAD.

- **Bore x OD x width:** 12 x 18 x 4 mm
- **Shielding:** ZZ
- **CAD OEM code:** C0105000046
- **Material:** Verify supplier steel, cage and lubricant
- **Make/buy:** Buy: qualified 6701ZZ
- **Unresolved:** OEM supplier, clearance, speed rating, bearing fits and grease need selection.
- **Source references:** S3, S5

## F01 — M2.5 x 6 countersunk screw

Quantity: 24 ea. Evidence: Reference CAD.

- **Thread / nominal length:** M2.5 x 6 mm
- **Head:** Countersunk internal hex
- **CAD OEM code:** C0203000297
- **Front joint, 8 screws:** NAUO7 and NAUO22–28: M01 main housing to G05 integral ring gear / stator carrier, 54 mm PCD
- **Rear joint, 16 screws:** Remaining F01 instances: M02 rear housing to M01 main housing
- **Material:** Strength class / coating unspecified
- **Make/buy:** Buy after fastener specification release
- **Unresolved:** Verify head standard, torque, locking method, material and thread engagement. CAD count is 24, not a count of interface holes.
- **Source references:** S3

## F02 — M2 x 12 screw

Quantity: 6 ea. Evidence: Reference CAD.

- **Thread / under-head length:** M2 x 12 mm
- **CAD overall length:** 14 mm
- **CAD OEM code:** C0203000308
- **Material:** Strength class / coating unspecified
- **Make/buy:** Buy after fastener specification release
- **Unresolved:** Verify head style/standard, tightening torque, locking and engagement.
- **Source references:** S3

## E01 — Driver board assembly

Quantity: 1 ea. Evidence: Reference CAD.

- **CAD board identifier:** BZD02010008 / C-AK-DRV-12S_V3.00_L
- **CAD envelope:** 62.282 x 62.479 x 6.850 mm
- **Control:** FOC; servo and MIT modes
- **Supply reference:** 48 V nominal
- **Current compatible driver:** AK60-4820-1C-A2 (manual p.7)
- **Driver input range:** 18–52 V; 48 V nominal
- **Driver rated output current:** 20 A RMS (driver rating, not motor continuous rating)
- **Driver maximum output current:** 60 A peak (driver rating, duration not given)
- **Driver outline:** 63 x 57 mm (manual; different from legacy CAD envelope)
- **CAN bitrate:** 1 Mbit/s
- **Standby consumption:** ≤1 W
- **Driver ambient:** −20 to +65 °C
- **Driver maximum board temperature:** 100 °C
- **Separate driver inventory:** 205 reference designators extracted; see driver-inventory.json, values and MPNs unknown
- **Material:** PCBA; substrate and copper weight unspecified
- **Make/buy:** Buy a compatible complete driver, or design a new PCBA
- **Unresolved:** Assembly STEP identifies C-AK-DRV-12S_V3.00_L, while the current manual/download names AK60-4820-1C-A2. Resolve hardware/firmware revision before procurement. Twelve CAD solids describe packaging, not the IC/passive BOM. Peak duration and thermal derating remain unspecified.
- **Source references:** S1, S3, S6, S8

## E02 — Encoder target magnet

Quantity: 1 ea. Evidence: Reference CAD.

- **CAD size:** Ø6 x 2.5 mm
- **OEM code:** C0103000453
- **Material:** Magnet grade and magnetization unspecified
- **Make/buy:** Buy after sensor pairing
- **Unresolved:** Magnetization direction, sensor air gap, concentricity and field range must match selected encoder.
- **Source references:** S3

## EM01 — Stator lamination stack

Quantity: 1 ea. Evidence: Not in reference CAD.

- **Slot count:** 36 (published)
- **OD / ID / active length:** Unpublished
- **Lamination thickness:** 0.20 mm proposed starting point
- **Individual-sheet model:** See Lamination lab: provisional profile, coating and thickness tolerance; live study BOM L01–L03
- **Mounting in current study:** Bore 52 mm seats on G05 shoulder at z 6.936 mm; sleeve OD 51.96 mm gives 0.020 mm radial bond gap
- **Axial location:** Stack -6.936 to +6.936 mm; sleeve -6.0 to +6.936 mm leaves 0.936 mm stack overhang at rear
- **Retention:** Proposed retaining adhesive on carrier sleeve, with front axial seating shoulder; no assumed press fit
- **Material:** Proposed: low-loss non-oriented electrical steel; grade unselected
- **Make/buy:** Prototype profile cutting + insulated stack; production stamping after validation
- **Unresolved:** Requires magnetic geometry, B-H/loss curves, stack factor, burr limit, stack retention and FEA. Quantity is one proposed stack; individual lamination count unknown.
- **Source references:** S1

## EM02 — Three-phase winding

Quantity: 1 set. Evidence: Not in reference CAD.

- **Connection:** Delta (published)
- **KV target:** 100 rpm/V
- **Terminal-to-terminal resistance:** 160 mΩ published
- **Terminal-to-terminal inductance:** 116 µH published
- **Material:** Enamelled copper; wire grade unselected
- **Make/buy:** Wind, terminate, impregnate and test
- **Unresolved:** Turns, wire diameter, parallel strands, coil pitch, winding diagram, fill factor and test temperature/frequency unknown. Do not treat terminal resistance as phase-branch resistance in delta.
- **Source references:** S1

## EM03 — Rotor magnetic yoke

Quantity: 1 ea. Evidence: Not in reference CAD.

- **Architecture:** Outer rotor study
- **Envelope / wall thickness:** To be designed
- **Known end-bell interference:** EM03/endbell at z -8.6 to -7.6 mm intersects rear housing NAUO4 by approximately 2666.283 mm3 in assembled coordinates. Axial layout correction pending.
- **Material:** Proposed: magnetic steel yoke with separate structural carrier as required
- **Make/buy:** Machine and dynamically balance
- **Unresolved:** OEM yoke geometry, magnetic saturation margin, magnet retention and rotor balance specification absent. Rear end bell collides with M02. Moving it forward conflicts with the current stator/winding axial envelope. Housing depth versus motor stack must be resolved.
- **Source references:** Engineering requirement; not an OEM specification

## EM04 — Rotor permanent magnet set

Quantity: 1 set. Evidence: Not in reference CAD.

- **Pole pairs:** 21 (published)
- **Magnetic poles:** 42 (derived)
- **Physical segment count:** Unknown; 42 poles does not establish 42 pieces
- **Material:** Proposed: high-coercivity NdFeB; grade to follow thermal/demagnetization analysis
- **Make/buy:** Buy custom segments; bond and retain
- **Unresolved:** Arc, thickness, pole coverage, segment count, coating, grade and magnetization are unknown.
- **Source references:** S1

## EM05 — Slot insulation and end insulation

Quantity: TBD set. Evidence: Unresolved.

- **Insulation system:** Published class C is an assembly claim; component system not specified
- **Material:** Film / paper / sleeves to match validated winding system
- **Make/buy:** Cut/form and install
- **Unresolved:** Material, thickness, dielectric rating, creepage and quantity require winding design.
- **Source references:** S1

## EM06 — Winding impregnation compound

Quantity: TBD g. Evidence: Unresolved.

- **Function:** Electrical insulation and winding retention
- **Material:** Varnish or resin compatible with winding insulation
- **Make/buy:** Controlled impregnation / cure
- **Unresolved:** Chemistry, cured thermal rating, application mass and cure schedule unknown.
- **Source references:** Engineering requirement; not an OEM specification

## G04 — Planet gear set

Quantity: 3 ea. Evidence: Illustration inference.

- **Reduction target:** 9:1
- **Tooth counts / module / number of planets:** Not disclosed
- **Planet count:** Three visible in manufacturer exploded illustration; verify physical assembly
- **Primeform matched gear candidate:** 70 teeth; module 0.3; pressure angle 20 degrees; zero profile shift
- **Candidate backlash:** 0.020 mm circular per mesh at nominal centres, from 0.010 mm tooth thinning per gear; not a manufacturing tolerance
- **Root transition:** 0.060 mm circular fillets; not a hob/shaper-generated trochoid
- **Ratio and assembly:** 20 / 70 / 160 teeth; ring fixed, sun input, carrier output: exactly 9:1; three planets at 120 degrees; centres 13.5 mm
- **Release blockers:** Cutting process, steel grade, heat treatment, gear quality, tooth-thickness tolerances, strength, fatigue, lubrication and loaded contact checks
- **Material:** Gear steel and heat treatment to be selected
- **Make/buy:** Gear cutting / heat treatment / inspection
- **Unresolved:** Three planets are inferred from the exploded illustration; their teeth and dimensions are omitted from STEP. Need tooth count, module, profile shift, face width, material, hardness and fatigue analysis.
- **Source references:** S1, S3, S7

## G05 — Internal ring gear with integral stator carrier

Quantity: 1 ea. Evidence: Primeform mounting proposal.

- **Reduction target:** 9:1
- **Separate or integral construction:** Separate annular ring is shown in exploded illustration; exact mounting unverified
- **Primeform matched gear candidate:** 160 teeth; module 0.3; pressure angle 20 degrees; zero profile shift
- **Candidate backlash:** 0.020 mm circular per mesh at nominal centres, from 0.010 mm tooth thinning per gear; not a manufacturing tolerance
- **Root transition:** 0.060 mm circular fillets; not a hob/shaper-generated trochoid
- **Ratio and assembly:** 20 / 70 / 160 teeth; ring fixed, sun input, carrier output: exactly 9:1; three planets at 120 degrees; centres 13.5 mm
- **Release blockers:** Cutting process, steel grade, heat treatment, gear quality, tooth-thickness tolerances, strength, fatigue, lubrication and loaded contact checks
- **Housing joint:** Eight M2.5 x 6 countersunk screws, NAUO7 and NAUO22–28, through M01 into this flange; 54 mm PCD
- **Mounting flange:** OD 60 / ID 49.8 mm; z 8.75 to 13.25 mm; 8 x M2.5 x 0.45 through. STEP uses 2.05 mm pilot bores, no thread helices.
- **Nominal screw penetration:** 3.3 mm from housing contact face to screw tip; thread engagement strength and torque not released
- **Stator carrier:** Integral sleeve OD 51.96 / ID 49.8 mm, z -6.0 to 6.936 mm; axial shoulder at z 6.936 mm, OD 60 mm
- **Rear clearance:** 0.25 mm nominal sleeve-to-rear-housing axial clearance
- **Support rationale:** Primeform proposed integral stationary ring/carrier; OEM flange inferred from illustration, support integration not established by OEM sources
- **Material:** Material and hardness to be selected
- **Make/buy:** Internal gear machining or validated alternative
- **Unresolved:** Ring tooth profile absent; carrier architecture and ring retention unresolved. Integral carrier needs material/heat-treatment, adhesive, thermal path, shaft alignment and thread-strength review. New nominal interfaces are not manufacture-released.
- **Source references:** S1, S3, S7

## G06 — Planet pins and retention

Quantity: TBD set. Evidence: Not in reference CAD.

- **Diameter / length / number:** Unresolved
- **Material:** Hardened pin steel to be selected
- **Make/buy:** Ground pins + retention
- **Unresolved:** Pin bending, shear, fit, surface hardness and carrier thickness need load-based sizing.
- **Source references:** Engineering requirement; not an OEM specification

## G07 — Planet bearings or bushings

Quantity: TBD set. Evidence: Not in reference CAD.

- **Type / size / number:** Unresolved
- **Material:** To be selected
- **Make/buy:** Buy after pin and gear geometry release
- **Unresolved:** Determine bearing versus bushing architecture, life, lubrication and clearance.
- **Source references:** Engineering requirement; not an OEM specification

## E03 — Rotor position encoder

Quantity: 1 ea. Evidence: Published function.

- **Technology:** Magnetic
- **Resolution:** 16 bit
- **Encoder count:** 1; no output encoder published
- **Firmware-dependent resolution:** Product page: 16 bit; manual p.4: up to 21 bit with custom firmware; p.8 table lists 21 bit
- **Material:** IC / sensor module not identified
- **Make/buy:** Part of E01 purchased PCBA or custom board
- **Unresolved:** Exact IC, accuracy, latency, interface, position convention and magnet pairing unresolved. Resolution is not accuracy.
- **Source references:** S1, S6

## E04 — Winding temperature sensor

Quantity: 1 ea. Evidence: Published function.

- **Published identifier:** NTC MF51B 103F3950
- **Nominal notation:** 10 kΩ / B3950; tolerance to be verified
- **Material:** NTC assembly
- **Make/buy:** Buy matched part and embed in winding
- **Unresolved:** Sensor count is a design allowance; verify package, tolerance, placement and calibration.
- **Source references:** S1

## E05 — Power and CAN connector

Quantity: 1 ea. Evidence: Published manual.

- **Description on product page:** XT30 2+2
- **Specification table:** XT30PW-M; CAN connector field is blank
- **Onboard connector:** AMASS XT30PW(2+2)-M
- **Cable mate:** AMASS XT30(2+2)-F
- **Pin functions, manual p.10:** 1: supply + (red); 2: supply − (black); 3: CAN_H (white); 4: CAN_L (blue)
- **External cable scope:** Supplied mating accessory; excluded from the internal actuator assembly and BOM quantity
- **External cable / Included pack:** One power/CAN cable (published)
- **External cable / Power conductors:** 16 AWG silicone, red/black
- **External cable / CAN conductors:** 30 AWG PTFE, white/blue, OD 0.64 mm
- **External cable / Nominal length:** 100 ±10 mm (manual p.12; remarks also say ±2 mm)
- **External cable / Termination:** XT30(2+2)-F; opposite end stripped/tinned 3 ±1 mm
- **Material:** Connector assembly
- **Make/buy:** Buy only after footprint/pinout verification
- **Unresolved:** Manual resolves the combined connector naming for AK60-4820-1C-A2. Confirm board revision and physical pin orientation before wiring. External cable: Confirm drawing revision and length tolerance; the manual remarks conflict with its detailed length specification. Verify connector orientation and actual current duty.
- **Source references:** S1, S6

## E06 — UART connector

Quantity: 1 ea. Evidence: Published function.

- **Published part:** A1257WR-S-3P
- **Product description:** CJT 3-pin
- **Cable mate:** CJT A1257H-3P
- **Pin functions, manual p.10:** 1: GND (black); 2: RX (yellow); 3: TX (green)
- **External cable scope:** Supplied mating accessory; excluded from the internal actuator assembly and BOM quantity
- **External cable / Included pack:** One serial cable (published)
- **External cable / Conductors:** 30 AWG PTFE; OD 0.64 mm
- **External cable / Nominal length:** 200 ±10 mm (manual p.13; remarks also say ±2 mm)
- **External cable / Termination:** GH1.25 3-pin to FC 2 x 4 crimp connector, as described in manual
- **Material:** Connector assembly
- **Make/buy:** Part of E01; verify mating harness
- **Unresolved:** Confirm pitch, mating part, orientation and voltage levels with driver documentation. External cable: Verify actual mating housing, terminal part numbers and conflicting cable length tolerance against supplied harness.
- **Source references:** S1, S6

## E07 — Power stage, gate drive and sensing

Quantity: TBD set. Evidence: Unresolved.

- **Architecture requirement:** Three-phase inverter, current sensing, protection
- **Exact electronic BOM:** Not public in inspected sources
- **Material:** MOSFETs, gate driver, shunts and passives unselected
- **Make/buy:** Included in purchased E01; custom schematic required to make locally
- **Unresolved:** Need actual phase-current convention, transient bus rating, MOSFET SOA, shunt design, switching losses and thermal analysis.
- **Source references:** Engineering requirement; not an OEM specification

## E08 — Control, communications and power supplies

Quantity: TBD set. Evidence: Unresolved.

- **Architecture requirement:** MCU, CAN transceiver, regulation, decoupling and protection
- **Material:** ICs and passives unselected
- **Make/buy:** Included in purchased E01; custom schematic required to make locally
- **Unresolved:** MCU, encoder IC, CAN IC, regulator, capacitor and passive part numbers/quantities missing. This parent-level BOM is not a PCB placement BOM.
- **Source references:** Engineering requirement; not an OEM specification

## E09 — Bulk DC-link capacitor assembly

Quantity: TBD set. Evidence: Unresolved.

- **Reference download:** Driver STEP is labelled without capacitor
- **Capacitance / voltage / ESR / ripple rating:** Unknown
- **Material:** Capacitor technology and specification unselected
- **Make/buy:** Confirm driver configuration before selecting
- **Unresolved:** The driver file still includes small C-designators; the bulk capacitor configuration cannot be established from the filename. Need circuit, mounting, transient and ripple-current requirements. Verify whether included in purchased E01.
- **Source references:** S8

## C01 — Gear lubricant

Quantity: TBD g. Evidence: Unresolved.

- **Selection basis:** Speed, contact loads, materials and operating temperature
- **Material:** Grease grade unselected
- **Make/buy:** Metered fill after compatibility validation
- **Unresolved:** OEM type, fill mass, service interval and compatibility unknown.
- **Source references:** Engineering requirement; not an OEM specification

## C02 — Magnet adhesive and retention

Quantity: TBD set. Evidence: Unresolved.

- **Selection basis:** Peak rotor speed and temperature
- **Material:** Structural adhesive / retention method unselected
- **Make/buy:** Controlled surface preparation, bond and cure
- **Unresolved:** Bondline thickness, cure, adhesive mass and overspeed proof required.
- **Source references:** Engineering requirement; not an OEM specification

## C03 — Stator retaining and thermal bondline

Quantity: TBD set. Evidence: Unresolved.

- **Selection basis:** Stator-to-housing and PCBA thermal paths
- **Proposed bondline:** 0.020 mm radial, sleeve radius 25.98 to stator bore radius 26.00 mm; length 12.936 mm
- **Function:** Stator torque retention and heat transfer to integral G05 carrier and housing
- **Material:** Retaining adhesive grade unselected; validate electrical insulation, temperature and thermal performance
- **Make/buy:** Controlled application
- **Unresolved:** Bond shear/fatigue, thermal cycles, cure, surface preparation, disassembly, tolerances and compatibility with gear heat treatment remain unresolved.
- **Source references:** Engineering requirement; not an OEM specification

## C04 — Shims, seals, spacers and thread locking

Quantity: TBD set. Evidence: Unresolved.

- **Contents:** Determine from tolerance stack and teardown
- **Material:** Unselected
- **Make/buy:** Select after assembly tolerancing
- **Unresolved:** No seal rating is established. Identify every retained item during physical teardown; do not assume this list is exhaustive.
- **Source references:** Engineering requirement; not an OEM specification
