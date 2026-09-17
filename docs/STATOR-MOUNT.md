# Stator mounting — Choice C

The current model uses a compact ring gear as the stator radial locator and a main-housing shoulder as the axial stop. The previous Ø52 bore, long ring sleeve and ring-owned stator shoulder are superseded.

See [packaging choices and selection](PACKAGING-CHOICES.md) for the alternatives, dimensions, reasons, axial layout and unresolved issues. The selected dimensions are Ø60 stator bore, Ø68 slot root, Ø80 stator OD, Ø59.96 ring OD, and a housing stop at z 11.436 mm. The stator moves 4.5 mm forward. This is a packaging study, not an OEM reconstruction or validated electromagnetic design.

Rebuild with `python cad/build_gears.py`, `python cad/build_housing.py`, `python scripts/build_bom.py`, and `npm run lamination`. The ring and housing generators retain their respective nominal solid and overlap checks. The ring tooth design and 9:1 ratio are unchanged. Rotor alignment and existing rotor/housing clashes remain unresolved.
