"""Build a traceable engineering BOM; null means unknown, never zero."""
from pathlib import Path
from collections import Counter
import json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'public/data'
OUT.mkdir(parents=True,exist_ok=True)
manifest=json.loads((ROOT/'public/models/manifest.json').read_text(encoding='utf-8'))
counts=Counter(p['bomId'] for p in manifest['parts'])
S1='https://www.cubemars.com/product/ak80-9-v3-0-robotic-actuator.html'
S2='https://www.cubemars.com/data/cms/202602/ak80-9-v3-0-robotic-actuator-2d-drawing.pdf'
S3=manifest['source']
sources=[dict(id='S1',name='CubeMars V3.0 product specification',url=S1),
 dict(id='S2',name='CubeMars V3.0 interface drawing',url=S2),
 dict(id='S3',name='CubeMars V3.0 STEP assembly',url=S3),
 dict(id='S4',name='EZO 625ZZ bearing specification',url='https://www.ezo-brg.co.jp/english/product/spec.php?eid=00545'),
 dict(id='S5',name='SMB thin section bearing dimensions',url='https://www.smbbearings.com/products/thin-section-bearings.html'),
 dict(id='S6',name='CubeMars AK V3.2.0 manual, pp. 7–13',url='https://www.cubemars.com/data/cms/202602/ak-series-prodcut-manual-v3-2-0-for-ak-3-0-robotic-actuator.pdf'),
 dict(id='S7',name='CubeMars AK80-9 exploded illustration',url='https://img.cubemars.com/products/AK70_80/images/AK80-9_02.jpg'),
 dict(id='S8',name='CubeMars separate driver STEP',url='https://www.cubemars.com/data/cms/202604/driver-ak60-4820-1c-a2-without-capacitor.zip')]

rows=[]
def row(id,name,group,qty,spec,material,process,unknown,sources,*,status='Reference CAD',unit='ea',parent=None):
    instances=[p['id'] for p in manifest['parts'] if p['bomId']==id]
    rows.append(dict(id=id,name=name,group=group,quantity=qty,unit=unit,status=status,
        specifications=spec,material=material,process=process,unresolved=unknown,
        sources=sources,instances=instances,parent=parent,unitCost=None,currency='USD',
        procurementReady=False))

row('M01','Main housing','Structure',counts['M01'],
 {'CAD envelope':'Ø98 x 24.2 mm','Assembly envelope':'Ø98 x 38.5 mm','Mounting':'8 x M3 on Ø85 PCD (drawing)'},
 'OEM grade unspecified; aluminium alloy is a proposed material family only',
 'Proposed: CNC turning + milling; finish and datums to be specified',
 'Alloy, heat treatment, wall tolerances, bearing fits, surface finish and ring-gear attachment are unverified.', ['S2','S3'])
row('M02','Rear housing','Structure',counts['M02'],{'CAD envelope':'Ø98 x 9 mm'},
 'OEM grade unspecified','Proposed: CNC turning + milling',
 'Verify locating pilot, concentricity, thermal contact, fastener engagement and finish.', ['S3'])
row('M03','Driver cover','Structure',counts['M03'],{'CAD envelope':'Ø71 x 11 mm','OEM drawing code':'BJJ02040285'},
 'OEM grade unspecified','Proposed: CNC machining',
 'Material, insulation clearances, sealing and thermal path need definition.', ['S3'])
row('M04','Closure cover','Transmission',counts['M04'],{'CAD envelope':'Ø14 x 2 mm'},
 'OEM grade unspecified','Proposed: turned disc',
 'Retention method, tolerance and functional purpose require teardown confirmation.', ['S3'])
row('G01','Output carrier','Transmission',counts['G01'],{'CAD envelope':'Ø37 x 7.5 mm','Output interface':'6 x M4 on Ø28 PCD (drawing)'},
 'OEM grade unspecified','Proposed: machined carrier',
 'Pin attachment, torque path, material, fits and fatigue margin need validation.', ['S2','S3'])
row('G02','Sun gear / input shaft','Transmission',counts['G02'],{'CAD bounding box':'6.717 x 6.717 x 21.5 mm','Assembly ratio':'9:1 (not a tooth-count specification)'},
 'OEM steel and hardness unspecified','Proposed: gear cutting, heat treatment, finish grinding',
 'Tooth count, module, pressure angle, profile shift, hardness, case depth and spline/shaft fits remain unresolved.', ['S1','S3'])
row('G03','Input shaft hub','Transmission',counts['G03'],{'CAD envelope':'Ø44.5 x 14.5 mm'},
 'OEM material unspecified','Proposed: precision machining',
 'This is a hub within the rotor assembly, not a complete electromagnetic rotor. Magnet/yoke integration is absent.', ['S3'])
row('B01','625-ZZ bearing','Bearings',counts['B01'],{'Bore x OD x width':'5 x 16 x 5 mm','Shielding':'ZZ, two metal shields','CAD OEM code':'C0105000059 / EZO'},
 'Verify supplier steel, cage and lubricant','Buy: EZO 625ZZ or qualified equivalent',
 'Select clearance, fit, grease and life from actual radial/axial/moment loads. Do not assign actuator load ratings to this bearing.', ['S3','S4'])
row('B02','6707-ZZ bearing','Bearings',counts['B02'],{'Bore x OD x width':'35 x 44 x 5 mm','Shielding':'ZZ','CAD OEM code':'C0105000031'},
 'Verify supplier steel, cage and lubricant','Buy: qualified 6707ZZ',
 'OEM supplier, clearance, load ratings, preload and fit are unspecified.', ['S3','S5'])
row('B03','6701-ZZ bearing','Bearings',counts['B03'],{'Bore x OD x width':'12 x 18 x 4 mm','Shielding':'ZZ','CAD OEM code':'C0105000046'},
 'Verify supplier steel, cage and lubricant','Buy: qualified 6701ZZ',
 'OEM supplier, clearance, speed rating, bearing fits and grease need selection.', ['S3','S5'])
row('F01','M2.5 x 6 countersunk screw','Fasteners',counts['F01'],{'Thread / nominal length':'M2.5 x 6 mm','Head':'Countersunk internal hex','CAD OEM code':'C0203000297'},
 'Strength class / coating unspecified','Buy after fastener specification release',
 'Verify head standard, torque, locking method, material and thread engagement. CAD count is 24, not a count of interface holes.', ['S3'])
row('F02','M2 x 12 screw','Fasteners',counts['F02'],{'Thread / under-head length':'M2 x 12 mm','CAD overall length':'14 mm','CAD OEM code':'C0203000308'},
 'Strength class / coating unspecified','Buy after fastener specification release',
 'Verify head style/standard, tightening torque, locking and engagement.', ['S3'])
row('E01','Driver board assembly','Electronics',counts['E01'],{'CAD board identifier':'BZD02010008 / C-AK-DRV-12S_V3.00_L','CAD envelope':'62.282 x 62.479 x 6.850 mm','Control':'FOC; servo and MIT modes','Supply reference':'48 V nominal'},
 'PCBA; substrate and copper weight unspecified','Buy a compatible complete driver, or design a new PCBA',
 'Current download listing names AK60-4820-1C-A2; CAD names another revision. Resolve revision before purchasing. The 12 CAD solids are packaging geometry, not an electronic BOM. Voltage/current limits, firmware and schematic are missing.', ['S1','S3'])
row('E02','Encoder target magnet','Electronics',counts['E02'],{'CAD size':'Ø6 x 2.5 mm','OEM code':'C0103000453'},
 'Magnet grade and magnetization unspecified','Buy after sensor pairing',
 'Magnetization direction, sensor air gap, concentricity and field range must match selected encoder.', ['S3'])

row('EM01','Stator lamination stack','Motor',1,{'Slot count':'36 (published)','OD / ID / active length':'Unpublished','Lamination thickness':'0.20 mm proposed starting point'},
 'Proposed: low-loss non-oriented electrical steel; grade unselected',
 'Prototype profile cutting + insulated stack; production stamping after validation',
 'Requires magnetic geometry, B-H/loss curves, stack factor, burr limit, stack retention and FEA. Quantity is one proposed stack; individual lamination count unknown.', ['S1'],status='Not in reference CAD')
row('EM02','Three-phase winding','Motor',1,{'Connection':'Delta (published)','KV target':'100 rpm/V','Terminal-to-terminal resistance':'160 mΩ published','Terminal-to-terminal inductance':'116 µH published'},
 'Enamelled copper; wire grade unselected','Wind, terminate, impregnate and test',
 'Turns, wire diameter, parallel strands, coil pitch, winding diagram, fill factor and test temperature/frequency unknown. Do not treat terminal resistance as phase-branch resistance in delta.', ['S1'],status='Not in reference CAD',unit='set')
row('EM03','Rotor magnetic yoke','Motor',1,{'Architecture':'Outer rotor study','Envelope / wall thickness':'To be designed'},
 'Proposed: magnetic steel yoke with separate structural carrier as required','Machine and dynamically balance',
 'OEM yoke geometry, magnetic saturation margin, magnet retention and rotor balance specification absent.', [],status='Not in reference CAD')
row('EM04','Rotor permanent magnet set','Motor',1,{'Pole pairs':'21 (published)','Magnetic poles':'42 (derived)','Physical segment count':'Unknown; 42 poles does not establish 42 pieces'},
 'Proposed: high-coercivity NdFeB; grade to follow thermal/demagnetization analysis','Buy custom segments; bond and retain',
 'Arc, thickness, pole coverage, segment count, coating, grade and magnetization are unknown.', ['S1'],status='Not in reference CAD',unit='set')
row('EM05','Slot insulation and end insulation','Motor',None,{'Insulation system':'Published class C is an assembly claim; component system not specified'},
 'Film / paper / sleeves to match validated winding system','Cut/form and install',
 'Material, thickness, dielectric rating, creepage and quantity require winding design.', ['S1'],status='Unresolved',unit='set')
row('EM06','Winding impregnation compound','Motor',None,{'Function':'Electrical insulation and winding retention'},
 'Varnish or resin compatible with winding insulation','Controlled impregnation / cure',
 'Chemistry, cured thermal rating, application mass and cure schedule unknown.', [],status='Unresolved',unit='g')
row('G04','Planet gear set','Transmission',None,{'Reduction target':'9:1','Tooth counts / module / number of planets':'Not disclosed'},
 'Gear steel and heat treatment to be selected','Gear cutting / heat treatment / inspection',
 'Planet gears are omitted from STEP. Do not infer OEM tooth counts from ratio alone. Need interference, tooth-root/contact fatigue and efficiency calculations.', ['S1','S3'],status='Not in reference CAD',unit='set')
row('G05','Internal ring gear','Transmission',None,{'Reduction target':'9:1','Separate or integral construction':'Unresolved'},
 'Material and hardness to be selected','Internal gear machining or validated alternative',
 'Ring tooth profile absent; carrier architecture and ring retention unresolved.', ['S1','S3'],status='Not in reference CAD')
row('G06','Planet pins and retention','Transmission',None,{'Diameter / length / number':'Unresolved'},
 'Hardened pin steel to be selected','Ground pins + retention',
 'Pin bending, shear, fit, surface hardness and carrier thickness need load-based sizing.', [],status='Not in reference CAD',unit='set')
row('G07','Planet bearings or bushings','Bearings',None,{'Type / size / number':'Unresolved'},
 'To be selected','Buy after pin and gear geometry release',
 'Determine bearing versus bushing architecture, life, lubrication and clearance.', [],status='Not in reference CAD',unit='set')
row('E03','Rotor position encoder','Electronics',1,{'Technology':'Magnetic','Resolution':'16 bit','Encoder count':'1; no output encoder published'},
 'IC / sensor module not identified','Part of E01 purchased PCBA or custom board',
 'Exact IC, accuracy, latency, interface, position convention and magnet pairing unresolved. Resolution is not accuracy.', ['S1'],status='Published function',parent='E01')
row('E04','Winding temperature sensor','Electronics',1,{'Published identifier':'NTC MF51B 103F3950','Nominal notation':'10 kΩ / B3950; tolerance to be verified'},
 'NTC assembly','Buy matched part and embed in winding',
 'Sensor count is a design allowance; verify package, tolerance, placement and calibration.', ['S1'],status='Published function')
row('E05','Power and CAN connector','Electronics',None,{'Description on product page':'XT30 2+2','Specification table':'XT30PW-M; CAN connector field is blank'},
 'Connector assembly','Buy only after footprint/pinout verification',
 'Manufacturer page conflicts internally. Verify exact connector SKU, quantity, rated current and pin assignment against delivered driver.', ['S1'],status='Unresolved',parent='E01')
row('E06','UART connector','Electronics',1,{'Published part':'A1257WR-S-3P','Product description':'CJT 3-pin'},
 'Connector assembly','Part of E01; verify mating harness',
 'Confirm pitch, mating part, orientation and voltage levels with driver documentation.', ['S1'],status='Published function',parent='E01')
row('E07','Power stage, gate drive and sensing','Electronics',None,{'Architecture requirement':'Three-phase inverter, current sensing, protection','Exact electronic BOM':'Not public in inspected sources'},
 'MOSFETs, gate driver, shunts and passives unselected','Included in purchased E01; custom schematic required to make locally',
 'Need actual phase-current convention, transient bus rating, MOSFET SOA, shunt design, switching losses and thermal analysis.', [],status='Unresolved',unit='set',parent='E01')
row('E08','Control, communications and power supplies','Electronics',None,{'Architecture requirement':'MCU, CAN transceiver, regulation, decoupling and protection'},
 'ICs and passives unselected','Included in purchased E01; custom schematic required to make locally',
 'MCU, encoder IC, CAN IC, regulator, capacitor and passive part numbers/quantities missing. This parent-level BOM is not a PCB placement BOM.', [],status='Unresolved',unit='set',parent='E01')
row('E09','Bulk DC-link capacitor assembly','Electronics',None,{'Reference download':'Driver STEP is labelled without capacitor','Capacitance / voltage / ESR / ripple rating':'Unknown'},
 'Capacitor technology and specification unselected','Confirm driver configuration before selecting',
 'The driver file still includes small C-designators; the bulk capacitor configuration cannot be established from the filename. Need circuit, mounting, transient and ripple-current requirements. Verify whether included in purchased E01.', ['S8'],status='Unresolved',unit='set')
row('A01','Power/CAN harness','Harness',1,{'Included pack':'One power/CAN cable (published)'},
 'Copper wire and matching connectors','Buy or crimp after current/pinout validation',
 'Wire gauge, length, insulation, pinout and contact parts unresolved.', ['S1'],status='Published accessory')
row('A02','Serial harness','Harness',1,{'Included pack':'One serial cable (published)'},
 'Signal wire and matching connector','Buy or crimp after pinout validation',
 'Length, wire gauge, pinout and mating connector unresolved.', ['S1'],status='Published accessory')
row('C01','Gear lubricant','Consumables',None,{'Selection basis':'Speed, contact loads, materials and operating temperature'},
 'Grease grade unselected','Metered fill after compatibility validation',
 'OEM type, fill mass, service interval and compatibility unknown.', [],status='Unresolved',unit='g')
row('C02','Magnet adhesive and retention','Consumables',None,{'Selection basis':'Peak rotor speed and temperature'},
 'Structural adhesive / retention method unselected','Controlled surface preparation, bond and cure',
 'Bondline thickness, cure, adhesive mass and overspeed proof required.', [],status='Unresolved',unit='set')
row('C03','Thermal interface material','Consumables',None,{'Selection basis':'Stator-to-housing and PCBA thermal paths'},
 'Compound or pad unselected','Controlled application',
 'Thickness, conductivity, electrical insulation and quantity unresolved.', [],status='Unresolved',unit='set')
row('C04','Shims, seals, spacers and thread locking','Consumables',None,{'Contents':'Determine from tolerance stack and teardown'},
 'Unselected','Select after assembly tolerancing',
 'No seal rating is established. Identify every retained item during physical teardown; do not assume this list is exhaustive.', [],status='Unresolved',unit='set')

# Additional facts from the current manual and marketing exploded view. These
# sources are kept distinct from the older embedded PCBA in the assembly STEP.
by_id={r['id']:r for r in rows}
by_id['E01']['specifications'].update({'Current compatible driver':'AK60-4820-1C-A2 (manual p.7)',
 'Driver input range':'18–52 V; 48 V nominal','Driver rated output current':'20 A RMS (driver rating, not motor continuous rating)',
 'Driver maximum output current':'60 A peak (driver rating, duration not given)',
 'Driver outline':'63 x 57 mm (manual; different from legacy CAD envelope)',
 'CAN bitrate':'1 Mbit/s','Standby consumption':'≤1 W','Driver ambient':'−20 to +65 °C','Driver maximum board temperature':'100 °C'})
by_id['E01']['sources'].append('S6')
by_id['E01']['sources'].append('S8')
by_id['E01']['specifications']['Separate driver inventory']='205 reference designators extracted; see driver-inventory.json, values and MPNs unknown'
by_id['E01']['unresolved']='Assembly STEP identifies C-AK-DRV-12S_V3.00_L, while the current manual/download names AK60-4820-1C-A2. Resolve hardware/firmware revision before procurement. Twelve CAD solids describe packaging, not the IC/passive BOM. Peak duration and thermal derating remain unspecified.'
by_id['E03']['specifications']['Firmware-dependent resolution']='Product page: 16 bit; manual p.4: up to 21 bit with custom firmware; p.8 table lists 21 bit'
by_id['E03']['sources'].append('S6')
by_id['E05'].update(quantity=1,status='Published manual',unresolved='Manual resolves the combined connector naming for AK60-4820-1C-A2. Confirm board revision and physical pin orientation before wiring.',sources=['S1','S6'])
by_id['E05']['specifications'].update({'Onboard connector':'AMASS XT30PW(2+2)-M','Cable mate':'AMASS XT30(2+2)-F',
 'Pin functions, manual p.10':'1: supply + (red); 2: supply − (black); 3: CAN_H (white); 4: CAN_L (blue)'})
by_id['E06']['specifications'].update({'Cable mate':'CJT A1257H-3P','Pin functions, manual p.10':'1: GND (black); 2: RX (yellow); 3: TX (green)'})
by_id['E06']['sources'].append('S6')
by_id['A01']['specifications'].update({'Power conductors':'16 AWG silicone, red/black','CAN conductors':'30 AWG PTFE, white/blue, OD 0.64 mm',
 'Nominal length':'100 ±10 mm (manual p.12; remarks also say ±2 mm)','Termination':'XT30(2+2)-F; opposite end stripped/tinned 3 ±1 mm'})
by_id['A01']['unresolved']='Confirm drawing revision and length tolerance; the manual remarks conflict with its detailed length specification. Verify connector orientation and actual current duty.'
by_id['A01']['sources'].append('S6')
by_id['A02']['specifications'].update({'Conductors':'30 AWG PTFE; OD 0.64 mm','Nominal length':'200 ±10 mm (manual p.13; remarks also say ±2 mm)',
 'Termination':'GH1.25 3-pin to FC 2 x 4 crimp connector, as described in manual'})
by_id['A02']['unresolved']='Verify actual mating housing, terminal part numbers and conflicting cable length tolerance against supplied harness.'
by_id['A02']['sources'].append('S6')
by_id['G04'].update(quantity=3,unit='ea',status='Illustration inference',sources=['S1','S3','S7'])
by_id['G04']['specifications']['Planet count']='Three visible in manufacturer exploded illustration; verify physical assembly'
by_id['G04']['unresolved']='Three planets are inferred from the exploded illustration; their teeth and dimensions are omitted from STEP. Need tooth count, module, profile shift, face width, material, hardness and fatigue analysis.'
by_id['G05'].update(quantity=1,status='Illustration inference',sources=['S1','S3','S7'])
by_id['G05']['specifications']['Separate or integral construction']='Separate annular ring is shown in exploded illustration; exact mounting unverified'
by_id['EM01']['specifications']['Individual-sheet model']='See Lamination lab: provisional profile, coating and thickness tolerance; live study BOM L01–L03'

by_id['G02']['status']='Source journals + provisional toothed section'
by_id['G02']['specifications'].update({'Current study solid':'One gear-and-shaft solid. Source journals retained; z 3.75 to 11.25 mm replaced by a 20-tooth involute candidate, module 0.3, pressure angle 20 degrees, face width 7.5 mm. Current tip diameter 6.6 mm; original source envelope listed separately.', 'Representation':'Viewer GLB tessellated from the same solid as provisional-sun-gear.step; source blank excluded from combined study.'})
by_id['G02']['unresolved'] += ' Study tooth profile is not a manufacturing design. Verify involute geometry, profile shift, root strength, mating gears and axial fits.'

for gear_id, teeth in [('G02',20),('G04',70),('G05',160)]:
    by_id[gear_id]['specifications'].update({'Primeform matched gear candidate':f'{teeth} teeth; module 0.3; pressure angle 20 degrees; zero profile shift', 'Candidate backlash':'0.020 mm circular per mesh at nominal centres, from 0.010 mm tooth thinning per gear; not a manufacturing tolerance', 'Root transition':'0.060 mm circular fillets; not a hob/shaper-generated trochoid', 'Ratio and assembly':'20 / 70 / 160 teeth; ring fixed, sun input, carrier output: exactly 9:1; three planets at 120 degrees; centres 13.5 mm', 'Release blockers':'Cutting process, steel grade, heat treatment, gear quality, tooth-thickness tolerances, strength, fatigue, lubrication and loaded contact checks'})

by_id['G05']['name']='Internal ring gear with integral stator carrier'
by_id['G05']['status']='Primeform mounting proposal'
by_id['G05']['specifications'].update({'Housing joint':'Eight M2.5 x 6 countersunk screws, NAUO7 and NAUO22–28, through M01 into this flange; 54 mm PCD', 'Mounting flange':'OD 60 / ID 49.8 mm; z 8.75 to 13.25 mm; 8 x M2.5 x 0.45 through. STEP uses 2.05 mm pilot bores, no thread helices.', 'Nominal screw penetration':'3.3 mm from housing contact face to screw tip; thread engagement strength and torque not released', 'Stator carrier':'Integral sleeve OD 51.96 / ID 49.8 mm, z -6.0 to 6.936 mm; axial shoulder at z 6.936 mm, OD 60 mm', 'Rear clearance':'0.25 mm nominal sleeve-to-rear-housing axial clearance', 'Support rationale':'Primeform proposed integral stationary ring/carrier; OEM flange inferred from illustration, support integration not established by OEM sources'})
by_id['G05']['unresolved'] += ' Integral carrier needs material/heat-treatment, adhesive, thermal path, shaft alignment and thread-strength review. New nominal interfaces are not manufacture-released.'
by_id['EM01']['specifications'].update({'Mounting in current study':'Bore 52 mm seats on G05 shoulder at z 6.936 mm; sleeve OD 51.96 mm gives 0.020 mm radial bond gap', 'Axial location':'Stack -6.936 to +6.936 mm; sleeve -6.0 to +6.936 mm leaves 0.936 mm stack overhang at rear', 'Retention':'Proposed retaining adhesive on carrier sleeve, with front axial seating shoulder; no assumed press fit'})
by_id['F01']['specifications'].update({'Front joint, 8 screws':'NAUO7 and NAUO22–28: M01 main housing to G05 integral ring gear / stator carrier, 54 mm PCD', 'Rear joint, 16 screws':'Remaining F01 instances: M02 rear housing to M01 main housing'})
by_id['C03']['name']='Stator retaining and thermal bondline'
by_id['C03']['specifications'].update({'Proposed bondline':'0.020 mm radial, sleeve radius 25.98 to stator bore radius 26.00 mm; length 12.936 mm', 'Function':'Stator torque retention and heat transfer to integral G05 carrier and housing'})
by_id['C03']['material']='Retaining adhesive grade unselected; validate electrical insulation, temperature and thermal performance'
by_id['C03']['unresolved']='Bond shear/fatigue, thermal cycles, cure, surface preparation, disassembly, tolerances and compatibility with gear heat treatment remain unresolved.'

by_id['M01']['status']='Reference CAD + Primeform modification'
by_id['M01']['specifications'].update({
 'Primeform housing R1':'Sixteen 5 mm diameter screw supports extended to housing floors; 16 source screw bores preserved. Gold supports can be hidden to compare source geometry.',
 'Known clearance conflict':'Extended supports intersect the provisional rotor yoke. Rotor diameter and housing clearance must be reconciled.',
 'Side holes measured from STEP':'One pair has diameter 2.1 mm on +Y side; opposite pair has diameter 3.2 mm. Pair centres x = ±6 mm, z = 3.25 mm in viewer coordinates. Functions and thread specifications unconfirmed.',
 'Radial spaces':'Clearance and unfilled material between screw bosses; no OEM functional designation established. Do not treat as validated spare volume.'})
by_id['M01']['unresolved'] += ' R1 needs rotor-clearance redesign and cutter-access/fillet validation. Side-hole purpose needs OEM confirmation; retain existing holes.'

# External mating cables are interface documentation, not internal actuator BOM items.
for connector_id, accessory_id in [('E05', 'A01'), ('E06', 'A02')]:
    connector, accessory = by_id[connector_id], by_id[accessory_id]
    connector['specifications']['External cable scope'] = 'Supplied mating accessory; excluded from the internal actuator assembly and BOM quantity'
    for key, value in accessory['specifications'].items():
        connector['specifications']['External cable / ' + key] = value
    connector['unresolved'] += ' External cable: ' + accessory['unresolved']
    connector['sources'] = list(dict.fromkeys(connector['sources'] + accessory['sources']))
rows = [r for r in rows if r['id'] not in ('A01', 'A02')]

specs={
 'identity':'AK80-9 V3.0 KV100','referenceManufacturer':'CubeMars','projectOwner':'Primeform Robotics',
 'revision':'Reference study R0','release':'Not released for manufacture','sourceDate':'2026-09-17',
 'published':{'Voltage':'48 V nominal','Rated output torque':'9 Nm','Peak output torque':'22 Nm',
 'Rated output speed':'390 rpm','No-load output speed':'570 rpm','Rated output power':'368 W',
 'Rated current':'12 A DC (manufacturer label)','Peak current':'28 A DC (manufacturer label)',
 'Reduction':'9:1','Mass':'490 g','Envelope':'Ø98 x 38.5 mm','Length tolerance':'±0.5 mm (V3 drawing)',
 'KV':'100 rpm/V','Kt':'0.095 Nm/A','Ke':'10 V/krpm','Winding':'Delta','Stator slots':'36','Pole pairs':'21',
 'Resistance':'160 mΩ, terminal-to-terminal','Inductance':'116 µH, terminal-to-terminal',
 'Backlash':'15 arcmin (0.25°)','Backdrive torque':'0.51 Nm','Rotor inertia':'1118.3238 g·cm²',
 'Ambient temperature':'−20 to +50 °C','Encoder':'One magnetic, 16 bit','Winding sensor':'NTC MF51B 103F3950',
 'Insulation class':'C (manufacturer designation)','Dynamic load rating':'2760 N (manufacturer assembly table)',
 'Static load rating':'2810 N (manufacturer assembly table)'},
 'interfaces':{'Housing mounting':'8 x M3 on Ø85 PCD, each indicated face; depth unspecified',
 'Output mounting':'6 x M4 on Ø28 PCD; depth unspecified','Pilot dimensions':'Ø48 and Ø37; see drawing for axial shoulders',
 'Locator':'Ø3, depth 3 indicated; count/angles to verify from CAD and physical part',
 'Connector warning':'Product prose and table disagree on power/CAN connector; verify driver revision'},
 'derived':{'Rated mechanical power':'9 × 390 × 2π / 60 = 367.6 W',
 'Rated motor speed':'390 × 9 = 3510 rpm','No-load motor speed':'570 × 9 = 5130 rpm',
 'Electrical frequency at rated speed':'3510 / 60 × 21 = 1228.5 Hz',
 'Magnetic poles':'2 × 21 = 42; physical magnet segment count is unknown'},
 'cautions':['Published ratings describe CubeMars hardware, not a validated Primeform build.',
 'Peak torque duration and simultaneous torque-speed capability are not established here.',
 'Do not use listed DC current as phase RMS current in copper-loss or inverter sizing calculations.',
 '100 KV × 48 V / 9 gives 533 rpm, not the listed 570 rpm; retain both source values until test conditions are known.',
 'CAD lacks several working internals and contains simplified bearings and board packaging. Mesh volume is not a mass prediction.'],
 'sources':sources}
specs['interfaces']['Connector warning']='Manual p.11 specifies XT30PW(2+2)-M + XT30(2+2)-F; the product table abbreviates it. Confirm hardware revision.'
specs['driver']={k:v for k,v in by_id['E01']['specifications'].items() if k not in ['CAD board identifier','CAD envelope']}
specs['cautions'].append('Encoder resolution varies by source/firmware: retain 16-bit product specification until hardware and firmware are identified; manual says up to 21-bit with custom firmware.')
(OUT/'bom.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding='utf-8')
(OUT/'specifications.json').write_text(json.dumps(specs,indent=2,ensure_ascii=False),encoding='utf-8')
docs=ROOT/'docs'; docs.mkdir(exist_ok=True)
lines=['# AK80-9 V3.0 KV100 engineering BOM','',
 'Reference study R0. Counts in the reference CAD cover every one of its 43 leaf instances, not every physical item in a working actuator. Missing quantities remain unknown. Board children are included in E01 and must not be ordered or costed twice. No line is released for procurement.','',
 '| ID | Component | Qty | Evidence | Specification | Open items |', '|---|---|---:|---|---|---|']
for r in rows:
    sp='; '.join(f'{k}: {v}' for k,v in r['specifications'].items())
    lines.append(f"| {r['id']} | {r['name']} | {r['quantity'] if r['quantity'] is not None else 'TBD'} {r['unit']} | {r['status']} | {sp} | {r['unresolved']} |")
lines += ['', '## Sources','']+[f"- {s['id']}: [{s['name']}]({s['url']})" for s in sources]
(docs/'BOM.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
lines=['# Component specifications','']
for r in rows:
    lines += [f"## {r['id']} — {r['name']}",'',f"Quantity: {r['quantity'] if r['quantity'] is not None else 'TBD'} {r['unit']}. Evidence: {r['status']}.",
        '',*[f'- **{k}:** {v}' for k,v in r['specifications'].items()],f"- **Material:** {r['material']}",
        f"- **Make/buy:** {r['process']}",f"- **Unresolved:** {r['unresolved']}",
        f"- **Source references:** {', '.join(r['sources']) or 'Engineering requirement; not an OEM specification'}",'']
(docs/'COMPONENT-SPECS.md').write_text('\n'.join(lines),encoding='utf-8')
print(f'Wrote {len(rows)} BOM rows; {sum(counts.values())} CAD instances; {len(counts)} CAD part types.')
