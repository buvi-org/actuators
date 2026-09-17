# Involute planetary candidate — 9:1

This replaces the polygonal placeholder teeth with an analytically defined involute candidate. It is an original Primeform gear design, not a recovered CubeMars tooth specification. Manufacturing release is pending; a CAD curve cannot establish 100% physical manufacturing accuracy.

| Parameter | Sun | Planet (three) | Internal ring |
|---|---:|---:|---:|
| Teeth | 20 | 70 | 160 |
| Module, mm | 0.3 | 0.3 | 0.3 |
| Pressure angle | 20° | 20° | 20° |
| Profile shift | 0 | 0 | 0 |
| Pitch diameter, mm | 6 | 21 | 48 |
| Tip diameter, mm | 6.6 | 21.6 | 47.4 |
| Root diameter, mm | 5.25 | 20.25 | 48.75 |
| Face width, mm | 7.5 | 5 | 5 |
| Circular tooth thinning, mm | 0.010 | 0.010 | 0.010 |

The candidate preserves the previous pitch diameters and 13.5 mm planet centre radius. The standard unshifted 20° undercut limit is 2/sin²(20°) ≈ 17.10 teeth; the 20-tooth sun clears it. The previous 12-tooth sun did not, and cannot simply be given an unshifted full-depth involute without addressing undercut.

With the ring fixed, sun input and carrier output, i = 1 + Zr/Zs = 1 + 160/20 = 9 exactly. Geometry closes because Zr = Zs + 2Zp = 160. Three equally spaced planets are possible because (Zs + Zr)/3 = 60 is an integer. Changing which member is fixed changes the ratio.

## Curves and STEP

`cad/involute_geometry.py` defines the flanks from the involute function, inv(alpha) = tan(alpha) - alpha, and the base radius. Each flank uses a parameterized interpolating B-spline with 49 analytic samples; 193 independent evaluation positions per representative flank check the fit. The enforced sampled position-error bound is 0.000001 mm. This is a numerical CAD check, not a manufacturing tolerance or a rigorous bound between every sample. STEP uses curved edges, not polygonal tooth flanks.

Root transitions use 0.060 mm circular fillets. The sun includes the below-base-circle radial transition; the planet and ring use tangent circular root blends. These fillets are explicitly designed geometry, not a claim about the trochoidal root left by a hob or shaper. A cutting process/tool definition may require different roots. Tip relief, lead correction and crowning are not yet specified.

Each gear is one valid solid. The sun preserves the source end journals, replacing the central section from z = 3.75 to 11.25 mm. The common mesh plane is z = 8.25 mm. STEP files are exported and re-imported to verify validity, solid count and volume. The browser loads tessellations of the same solids for all three gear types. The manufacturing surface is the STEP B-rep, not the GLB triangles.

## Checks and their limits

`public/design/gear-validation.json` records solid and spline-fit checks. `public/design/gear-mesh-validation.json` records:

- Exact 9:1 kinematic ratio and matching 13.5 mm centre distances.
- External transverse contact ratio ≈ 1.682; internal ≈ 1.947, from standard unmodified addendum geometry.
- Correct planet/ring phasing and zero detected overlap in 720 sampled positions across one full carrier revolution (nine sun revolutions), using sampled actual CAD boundaries.
- Nominal 0.020 mm circular backlash per mesh, obtained by thinning each mating tooth by 0.010 mm at its pitch circle. This is a candidate nominal allowance, not a backlash tolerance range or a verified output lost-motion figure.

The motion check is finite planar sampling, not proof at every continuous position, cutter simulation, or loaded contact analysis. It excludes carrier/pin deflection, runout, tolerance stacks, temperature, lubrication and torque-dependent elastic deformation. The existing housing/rotor conflict remains separately unresolved.

## Required before manufacturing release

Choose cutting process, tooling and root generation; material and heat treatment; tooth-thickness/space-width tolerances and measurement method; gear quality, profile/lead deviations and runout limits; bearing and shaft fits; chamfers and burr removal; lubricant; rated/peak duty and life. Complete tooth bending/contact fatigue, load sharing, shaft/root/fillet strength, cutter interference, and loaded contact checks. The original product's torque ratings do not validate this finer-module candidate.

Rebuild: `python cad/build_reference.py` if source cache is absent, then `python cad/build_gears.py` and `python cad/check_gear_mesh.py`.

Sources: [Drivetrain Hub — spur gear geometry](https://drivetrainhub.com/notebooks/gears/geometry/Chapter%202%20-%20Spur%20Gears.html), [planetary assembly conditions](https://drivetrainhub.com/notebooks/gears/geometry/Chapter%204%20-%20Planetary%20Gears.html), [KHK — internal gear interference](https://khkgears.net/pdf/internal-tech.pdf). Equations were checked against these references; the candidate values are Primeform assumptions.
