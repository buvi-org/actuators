# Ring-gear and stator mounting revision

The previous illustrative assembly lacked a load-bearing connection between the eight front countersunk screws and the ring gear, and did not define the stator mounting. This revision introduces a Primeform proposal: a fixed ring gear with an integral mounting flange, stator shoulder and bore sleeve. It is one component and one STEP solid. This integration is a design choice, not a confirmed OEM construction.

## Interfaces

- Eight source screws NAUO7 and NAUO22–28 pass through main housing M01 into ring/carrier G05. Their centres define a 54 mm bolt circle. Individual occurrence descriptions now identify this joint; the other sixteen F01 screws join the rear and main housings.
- Flange: OD 60 / ID 49.8 mm, z = 8.75 to 13.25 mm. Its front face meets the housing at z = 13.25 mm. Eight M2.5 x 0.45 through-thread positions use the actual source screw centres, compensating for the ring's tooth-phase rotation. STEP shows 2.05 mm pilot bores, not helical thread geometry.
- Source screw tips reach z = 9.95 mm: nominal penetration from the mounting face is 3.3 mm. This is geometric penetration, not a validated effective thread engagement, torque or pullout capacity.
- The stator remains z = -6.936 to +6.936 mm. Its front end seats on an integral shoulder at z = +6.936 mm, extending radially to 30 mm. The laminations have not been lengthened merely to fill space.
- Sleeve: OD 51.96 / ID 49.8 mm, z = -6.0 to +6.936 mm. It leaves 0.020 mm radial clearance inside the assumed 52 mm stator bore, proposed for retaining adhesive. The rear 0.936 mm of the stack overhangs the sleeve. The sleeve was shortened after detecting a rear-housing clash; the resulting nominal axial clearance is 0.25 mm.
- C03 now represents the retaining/thermal bondline over the actual sleeve length. There is no claimed press fit or additional invisible fastener. Adhesive selection, surface preparation, cure, bond fatigue and temperature capability remain unresolved.

The intended stator torque path is laminations → bondline → integral carrier/flange → eight-screw joint → main housing. Heat follows the same structural path; thermal resistance and joint contact conductance are not yet calculated. The ring reaction torque also enters the housing through the flange joint.

## Verification

`cad/build_gears.py` builds the integral part and records `public/design/stator-mount-validation.json`. Checks include:

- One valid ring/carrier solid, including STEP export/re-import.
- All eight source screw axes pass through the corresponding flange bores.
- No nominal solid overlap with source main housing, rear housing, output carrier, output bearings or input hub.
- No overlap with the stator and winding annular envelopes.

The original gear tooth geometry and phasing are unchanged. `cad/check_gear_mesh.py` checks the unchanged toothed profiles independently. The new flange/sleeve starts outside the gear tooth region; the mounting check is separate from loaded gear contact analysis. The existing rotor-yoke versus extended housing-boss conflict is not solved by this revision.

Use **Stator mount** in the viewer for a clipped assembled view with M01, G05, EM01, C03 and the eight front screws. Turn off Section to see the complete bodies. The G05 STEP download and gear-assembly STEP both include the integral support.

## Before manufacture

Resolve the integrated gear/carrier material and heat treatment, achievable thin sleeve tolerances, bonding process and retention strength, mounting-face flatness, shaft/gear concentricity, tapped-hole tolerances and torque, thermal expansion, heat flow, and gear/carrier stress. Confirm that this mounting approach is suitable for the required duty. No OEM stator dimensions, adhesive or mounting detail have been inferred as fact.
