# Main housing R1: supported screw bosses

Current R2 adds the Choice C stator axial seat at z 11.436 mm, radii 30.1–33.5 mm. See [packaging decision](PACKAGING-CHOICES.md). Original R1 boss discussion follows; its rotor interference remains unresolved.

The CubeMars NAUO3 housing remains the reference. Primeform R1 extends sixteen 5 mm diameter screw supports toward the housing floor, centred on the source screw axes. Gold support bodies in the tree show the added material; hiding them restores the reference view. They are integral housing material, not additional purchased parts.

`cad/build_housing.py` generates the modified solid STEP, the added-material GLB, and `public/design/housing-study.json`. Run `python cad/build_reference.py` first if the cached source STEP is absent, then `python cad/build_housing.py`. Coordinates are centred assembly millimetres. The rear seating face is z = -4.75 mm and the extrusion terminates at z = 15.25 mm, reaching the existing pocket floors. Existing source screw bores are retained; this does not specify or extend thread engagement. Original material is not removed. Reference GLB and STEP attribution remain unchanged.

## Clearance finding

The extended supports overlap the current illustrative rotor yoke (ID 85 / OD 91 / length 15 mm). This is a known geometry conflict, not just an unperformed check. The modified housing is a design study; the provisional motor envelope must be reconciled before a functional assembly or machining release. Reducing the rotor diameter would affect magnets, air gap, stator dimensions and performance, so that change is not made silently. See the generated report for overlap volume.

The constant-diameter supports fill beneath the tapered rear pads. Their 5 mm diameter is a Primeform choice, not a recovered OEM dimension. This is not a complete CAM validation: root fillets, tool radii, remaining source pockets, wall thickness, fits and workholding still need review.

## Side holes

The STEP has a pair of 2.1 mm diameter radial bores on the +Y side and a pair of 3.2 mm diameter radial bores on the opposite side. Their centres are x = ±6 mm and z = 3.25 mm. These are geometric measurements, not thread callouts. The published external drawing does not label their functions. A small fixing/access interface is plausible, but mounting, retention, tooling and wiring functions are not established. Retain the holes pending confirmation; do not designate them as ventilation or cable exits.

## Spaces between bosses

The scalloped peripheral cavity leaves room around the motor envelope while retaining local material at fasteners. Compared with a continuous thick ring, it also removes material and mass. These are geometric/engineering interpretations, not an OEM statement of purpose. The shallow pockets in the housing floor are a separate feature and appear consistent with material removal while retaining ribs. Neither region is validated spare space: rotor runout, assembly insertion, thermal expansion, insulation, and any routing must be accounted for. The collision above demonstrates why filling peripheral space needs a motor-envelope check.

Sources: [CubeMars STEP](https://www.cubemars.com/data/cms/202602/ak80-9-v3-0-robotic-actuator-3d-drawing.zip), [external drawing](https://www.cubemars.com/data/cms/202602/ak80-9-v3-0-robotic-actuator-2d-drawing.pdf). No inspected source establishes the OEM manufacturing process or side-hole purpose.
