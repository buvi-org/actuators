# Sources and attribution

Checked 2026-09-17. Local downloads and PDF renderings are kept in ignored `tmp/reference/`; they are not republished here as original documents.

| ID | Primary source | Used for |
|---|---|---|
| S1 | [CubeMars AK80-9 V3.0 product page](https://www.cubemars.com/product/ak80-9-v3-0-robotic-actuator.html) | Performance, topology counts, winding, sensor and reference size |
| S2 | [V3.0 interface PDF](https://www.cubemars.com/data/cms/202602/ak80-9-v3-0-robotic-actuator-2d-drawing.pdf) | Current mounting geometry and envelope tolerance |
| S3 | [V3.0 actuator STEP ZIP](https://www.cubemars.com/data/cms/202602/ak80-9-v3-0-robotic-actuator-3d-drawing.zip) | 43 leaf CAD instances, 54 solids, 14 part types, part labels and geometry |
| S4 | [EZO 625ZZ specification](https://www.ezo-brg.co.jp/english/product/spec.php?eid=00545) | Standard 625-ZZ dimensions |
| S5 | [SMB thin-section bearing catalogue](https://www.smbbearings.com/products/thin-section-bearings.html) | Nominal 6701-ZZ and 6707-ZZ dimensions |
| S6 | [AK Series Module Manual V3.2.0](https://www.cubemars.com/data/cms/202602/ak-series-prodcut-manual-v3-2-0-for-ak-3-0-robotic-actuator.pdf) | pp.4, 7–13: encoder caveat, driver, connectors, pin functions, harness |
| S7 | [CubeMars exploded illustration](https://img.cubemars.com/products/AK70_80/images/AK80-9_02.jpg) | Visual inference: outer rotor, wound annular stator, three planets and separate internal ring |
| S8 | [Driver AK60-4820-1C-A2 without capacitor STEP ZIP](https://www.cubemars.com/data/cms/202604/driver-ak60-4820-1c-a2-without-capacitor.zip) | 205 reference designators and package-model labels |

Some links on the manufacturer page resolve incorrectly under `/product/data/`. The working downloads use `/data/` at the domain root. The actuator download listing date is 2026-02-05; the STEP header says 2025-03-05. These are different dates and are recorded separately.

## File integrity

- Source actuator STEP SHA-256: `f569faf5c38c6cc2af5a510b36160a316161feb9cad37f5d136abe22b7f1beaa`.
- Source separate driver STEP SHA-256: `3c6492221216ea4b7d1baa2194fdfcbbe4fb43ec9d795633e4d6ae964f858e0f`.
- The conversion script records source filenames/dates and hashes in generated manifests. Recheck references if a fresh download changes these hashes.

## Authorship boundaries

`public/models/ak80-9-reference.glb` is a tessellated conversion of CubeMars reference CAD. The conversion does not establish Primeform authorship or an open-hardware license for that manufacturer geometry. Source dimensions and names are attributed to CubeMars; colours, translated component labels, inspection offsets and explanatory notes were added for this workbench.

The provisional lamination profile, its parameterization, viewer code, stack calculations and engineering notes are newly authored project work. They are not representations of an inspected OEM lamination. No fabrication or performance validation has been completed. A license for Primeform's own contributions remains to be selected.

Three.js, Vite, CadQuery, Open Cascade and other dependencies retain their own licenses. Their use does not transfer a license to the reference manufacturer design.
