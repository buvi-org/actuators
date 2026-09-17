# AK80-9 V3.0 internal structure findings

Reference study R0, checked 2026-09-17. See [source register](SOURCES.md) for links. Facts below distinguish a numerical specification, a CAD object and a marketing illustration; these provide different levels of evidence.

## Motor

S1 specifies 36 stator slots, 21 pole pairs, delta winding, 100 KV, Kt 0.095 Nm/A, 160 mOhm terminal-to-terminal resistance and 116 microhenry terminal-to-terminal inductance. Forty-two magnetic poles follow from 21 pole pairs; this does **not** establish the number of physical magnet segments.

S7 shows an annular outward-tooth wound stator, surrounded by an outer rotor with magnets on its inside circumference. It supports the outer-rotor architecture. The image does not establish steel grade, stack dimensions, magnet arc/thickness, magnetization, winding turns, conductor size or the insulation system.

The source assembly has a parent named rotor, but its leaf geometry comprises the sun/input shaft, two 6701-ZZ bearings, encoder target magnet and a hub. It does not contain a complete electromagnetic rotor. Neither the stator laminations nor coils appear as manufacturing geometry. Do not mistake a named subassembly for a complete parts list.

At the published rated output speed, motor speed is 390 × 9 = 3510 rpm and electrical frequency is 3510 / 60 × 21 = 1228.5 Hz. At the stated no-load speed, those values are 5130 rpm and 1795.5 Hz. These are derived kinematic values, not verified loss-test conditions. Steel selection needs relevant loss data and electromagnetic analysis.

## Gear train

The product specifies 9:1 planetary reduction. The exploded illustration S7 shows three planet gears and a separate annular internal ring. This is recorded as an illustration inference. STEP does not contain the full planet/ring/pin set; a complete gear drawing cannot be recovered from it.

For a conventional simple planetary set with fixed ring, sun input and carrier output, the relation would be `i = 1 + Zr/Zs`. A 9:1 ratio would require `Zr = 8 Zs`; common module and unshifted reference geometry imply `Zp = (Zr - Zs)/2`. These equations do not choose unique tooth counts, establish profile shifts, or prove the exact OEM construction. Verify architecture, tooth counts, pressure angle, face width and clearances before using them to design a replacement.

Material, hardness/case depth, gear precision, planet bearing type, pin retention, lubricant and backlash-setting method remain unresolved. The published backlash is 15 arcmin (0.25 degrees); do not substitute older-generation values.

## Bearings and interfaces recovered from CAD

| Part | CAD qty | Dimension or feature | Limit |
|---|---:|---|---|
| 6701-ZZ | 2 | 12 x 18 x 4 mm nominal bearing size | OEM maker, clearance and grease unknown |
| 6707-ZZ | 1 | 35 x 44 x 5 mm nominal bearing size | Load case, fit and preload unresolved |
| EZO 625-ZZ | 1 | 5 x 16 x 5 mm nominal size | Exact supplier option must be matched |
| Target magnet | 1 | Diameter 6 x 2.5 mm in CAD | Magnet grade and magnetization unknown |
| Output carrier | 1 | Diameter 37 x 7.5 mm CAD bounding envelope | Not a tolerance drawing |
| Main housing | 1 | Diameter 98 x 24.2 mm CAD bounding envelope | Alloy, fits and finish unspecified |
| Rear housing | 1 | Diameter 98 x 9 mm CAD envelope | Same caveat |
| Driver cover | 1 | Diameter 71 x 11 mm CAD envelope | Same caveat |
| M2.5 x 6 countersunk screws | 24 | Explicit STEP product name and occurrences | Strength class and tightening torque unknown |
| M2 x 12 screws | 6 | Explicit STEP product name and occurrences | 14 mm total model length includes head |

S2 gives the V3.0 external envelope diameter 98 x 38.5 +/-0.5 mm, 8 x M3 housing holes on diameter 85 PCD at the indicated faces, and 6 x M4 output holes on diameter 28 PCD. Thread depth and usable engagement are not specified. Diameter 48 and 37 shoulder callouts and a diameter 3 depth-3 locating feature also appear. Consult the complete drawing for orientation; do not mix these interfaces with an older AK80-9 drawing.

The manufacturer's assembly-table dynamic/static ratings (2760/2810 N) do not specify permissible arbitrary joint bending moments and must not be assigned to each bearing individually.

## Driver and harness

S6 pp.7–13 identifies AK60-4820-1C-A2 as compatible with AK80-9. It specifies 48 V nominal, 18–52 V operating range, 20 A RMS rated driver output, 60 A peak driver output, 63 x 57 mm outline, 1 Mbit/s CAN and up to 100 degrees C board temperature. These are driver ratings, not authorization to drive the motor at those currents continuously.

The actuator STEP calls the embedded driver C-AK-DRV-12S_V3.00_L. The separately downloaded current driver STEP still contains AK-DRV-12S_V3.00 labels. Confirm board revision and firmware with the actual unit; names and date listings alone do not prove an identical assembly.

The separate driver file yields **205 electronic reference designators**: 78 capacitors, 73 resistors, 12 transistors, 11 ICs, 18 diode/LED positions, 6 inductors, 3 connectors, and one each of a transformer/coupled device, TVS, oscillator and E-designated unresolved item. Prefixes determine these categories; they are not circuit identifications. Some C-designators use R-package geometry, demonstrating that STEP library labels cannot establish actual parts. See [complete inventory](DRIVER-INVENTORY.md).

The file name says without capacitor while small capacitor designators remain. We cannot establish the bulk/DC-link capacitor assembly, capacitance, voltage, ESR or ripple rating from that label. The schematic/netlist and electronic purchase BOM remain missing.

The manual resolves connector detail beyond the abbreviated product table:

- Power/CAN: AMASS XT30PW(2+2)-M on the board; XT30(2+2)-F cable mate. Pin functions are supply +, supply -, CAN_H and CAN_L in manual order. Verify the connector drawing's viewing direction before wiring.
- UART: CJT A1257WR-S-3P with A1257H-3P cable mate. Functions: GND, RX and TX in manual order.
- Power leads: 16 AWG silicone; CAN leads: 30 AWG PTFE, OD 0.64 mm. Detailed cable length says 100 +/-10 mm, while the remarks also say +/-2 mm. Confirm the harness drawing.
- Serial harness: 30 AWG, OD 0.64 mm, detailed length 200 +/-10 mm. Mate and tolerance still need matching to the actual cable.

## Source discrepancies to resolve

1. **Encoder:** S1 says one 16-bit magnetic encoder. S6 p.4 says 16-bit with up to 21-bit requiring custom firmware; its p.8 table says 21-bit. Do not silently advertise 21-bit for the reference actuator.
2. **Driver:** legacy CAD names/outline differ from current manual/download naming. Keep both sources until the actual board is identified.
3. **Current:** the motor product page labels current ADC; the driver manual explicitly uses RMS and peak current. These are not interchangeable in copper-loss, torque-constant or MOSFET calculations.
4. **Speed:** 100 KV x 48 V / 9 = 533 rpm differs from the listed 570 rpm no-load output. Preserve the published value and obtain test conditions instead of forcing consistency.
5. **Cable dimensions:** length tolerances disagree within the manual; get the harness drawing before ordering.

## Discussion before selecting manufacturing geometry

The highest-value next input is a physical AK80-9 V3.0 reference sample or a dimensioned lamination drawing. Measure stator OD/bore/active length, a cleaned single sheet and the assembled stack under a stated pressure, plus rotor air gap and magnet arc. Confirm coating thickness per face with the steel/coating supplier.

If a sample is unavailable, decide explicitly to design an original Primeform electromagnetic stack against the reference performance targets. In that route the interactive lamination study provides a starting parameterization, but its current dimensions require electromagnetic, thermal and mechanical design before fabrication. Exact OEM reproduction and an independently designed derivative are different deliverables.
