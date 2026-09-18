"""Build the rotor as ONE machined body, with every radial band stated once.

Layout rule: NO TWO BODIES SHARE A RADIAL BAND, and every band is asserted, because an
earlier revision let the magnets and the carrier occupy the same radii and "fixed" it by
cutting pockets, which is a comb rather than a carrier.

The magnet channel is open at the top so the segments can be inserted axially, and closed
by a retaining ring whose bore is larger than the magnet outer radius, so it retains the
magnets without blocking their insertion.

Run:  python cad/build_rotor.py
Writes: public/design/rotor.step, .glb, .json  (and viewer/rotor-params.json)
"""
import json
import math
import sys
from pathlib import Path

import cadquery as cq
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public/design"
sys.path.insert(0, str(ROOT / "tmp/audit"))
from oem import load  # noqa: E402

# ---------------------------------------------------------------------------
# Radial bands, mm.
#
# Two measured limits bracket the rotor:
#   * the housing's inward wall is r 47.400 over the rotor band, but it carries inward
#     features above r 43.4 (swept in tmp/audit/clash_by_z.py). A carrier wall sweep shows
#     the first interference at OD 43.6, so the rotor must stay at or below r 43.2.
#   * the stator OD is r 40, so the magnets must start outside it.
# ---------------------------------------------------------------------------
HUB_FLANGE_R = 22.25     # measured OEM hub flange outer radius
MAG_BORE = 41.20         # magnets sit on this bore (carrier bore)
MAG_OD = 42.20           # magnet outer face, 0.9 mm radial thickness
WALL_BORE = 42.30        # carrier wall bore, 0.1 mm clear of the magnets
CARRIER_OD = 43.20        # carrier outer wall, 0.8 mm radial thickness
# Axial. The housing's stator seat starts at z 11.436 and occupies r 30.100 to 33.500, so
# nothing may sit at r > 30 above that height. The rotor therefore ends at z 11.400.
WEB_Z0 = -1.75           # hub flange rear face
WEB_Z1 = 0.25            # hub flange front face
MAG_Z0 = 0.25            # magnets start above the base plate
MAG_Z1 = 10.40           # magnet top
BASE_T = 2.0             # base plate under the magnets
RETAIN_T = 1.0           # retaining ring above the magnets
TOP_Z = 11.40            # rotor top, just below the housing stator seat at z 11.436
SPOKES = 6
RIB_MM = 4.0
SEGMENTS = 42
COVERAGE = 0.85
# Clearance between the retaining ring bore and the magnet outer face.
RING_BORE = MAG_OD + 0.10

assert HUB_FLANGE_R < MAG_BORE, "web must grow outward from the flange"
assert MAG_BORE < MAG_OD < WALL_BORE < CARRIER_OD, "radial bands must not overlap"
assert CARRIER_OD <= 43.2 + 1e-9, "rotor must stay at or below r 43.2 (housing inward features)"
assert RING_BORE > MAG_OD, "retaining ring must not block magnet insertion"


def ring(ri, ro, z0, z1):
    h = z1 - z0
    return cq.Solid.makeCylinder(ro, h, cq.Vector(0, 0, z0)).cut(
        cq.Solid.makeCylinder(ri, h + 1, cq.Vector(0, 0, z0 - 0.5))
    )


def spoke_pockets(ri, ro, z0, thickness, spokes, rib_mm):
    half = math.degrees(math.atan2(rib_mm / 2.0, ro))
    out = []
    for i in range(spokes):
        a0 = i * (360.0 / spokes) + half
        a1 = (i + 1) * (360.0 / spokes) - half
        if a1 <= a0:
            continue
        out.append(
            cq.Workplane("XY", origin=(0, 0, z0 - 1.0))
            .moveTo(0, 0)
            .lineTo(ro * 2.0, 0)
            .radiusArc(
                (ro * 2.0 * math.cos(math.radians(a1 - a0)),
                 ro * 2.0 * math.sin(math.radians(a1 - a0))),
                ro * 2.0,
            )
            .close()
            .extrude(thickness + 2.0)
            .rotate((0, 0, 0), (0, 0, 1), a0)
            .val()
        )
    return out


def arc_points(radius, a, width, steps=32):
    return [
        (radius * math.cos(a - width / 2 + (width * t) / (steps - 1)),
         radius * math.sin(a - width / 2 + (width * t) / (steps - 1)))
        for t in range(steps)
    ]


def segment_poly(a, width, ri, ro):
    return arc_points(ro, a, width) + list(reversed(arc_points(ri, a, width)))


def main():
    occ, parts, center, centered = load()
    hub = centered("NAUO45")

    # 1. Spoked web from the hub flange out to the base plate's inner edge.
    web = ring(HUB_FLANGE_R, MAG_BORE, WEB_Z0, WEB_Z1)
    for cut in spoke_pockets(HUB_FLANGE_R, MAG_BORE, WEB_Z0, WEB_Z1 - WEB_Z0, SPOKES, RIB_MM):
        web = web.cut(cut)
    web = web.clean()

    # 2. Base plate under the magnets, spanning web to carrier outer wall so it connects.
    base = ring(HUB_FLANGE_R, CARRIER_OD, WEB_Z0, MAG_Z0)

    # 3. Carrier outer wall.
    wall = ring(WALL_BORE, CARRIER_OD, WEB_Z0, TOP_Z)

    # 4. Retaining ring above the magnets. Its bore clears the magnets radially, so it
    #    captures them axially without blocking axial insertion.
    retainer = ring(RING_BORE, CARRIER_OD, MAG_Z1, TOP_Z)

    body = hub.fuse(web).fuse(base).fuse(wall).fuse(retainer).clean()
    assert body.isValid(), "rotor body is not valid"
    count = len(body.Solids())
    assert count == 1, f"rotor must be one connected solid, got {count}"

    # 5. Magnet segments, seated in the channel.
    magnets = []
    for i in range(SEGMENTS):
        a = (i * 2 * math.pi) / SEGMENTS
        width = ((2 * math.pi) / SEGMENTS) * COVERAGE
        magnets.append(
            cq.Workplane("XY", origin=(0, 0, MAG_Z0))
            .polyline(segment_poly(a, width, MAG_BORE, MAG_OD))
            .close()
            .extrude(MAG_Z1 - MAG_Z0)
            .val()
        )

    main_h = cq.importers.importStep(str(OUT / "main-housing-supported.step")).val()
    rear = centered("NAUO4")
    sun = centered("NAUO41")

    checks = {}
    worst = 0.0
    for label, other in (("main_housing", main_h), ("rear_housing", rear)):
        v = body.intersect(other).Volume()
        checks[f"rotor_vs_{label}_mm3"] = round(v, 6)
        worst = max(worst, v)
    sun_v = body.intersect(sun).Volume()
    checks["rotor_vs_sun_mm3"] = round(sun_v, 6)  # measured, intended pilot fit

    magnet_vs_body = 0.0
    for i, mag in enumerate(magnets):
        v = mag.intersect(body).Volume()
        magnet_vs_body += v
        if v > 1e-9:
            checks[f"magnet{i + 1}_vs_rotor_mm3"] = round(v, 6)
        worst = max(worst, v)
    magnet_vs_magnet = 0.0
    for i in range(SEGMENTS):
        j = (i + 1) % SEGMENTS
        v = magnets[i].intersect(magnets[j]).Volume()
        magnet_vs_magnet += v
        worst = max(worst, v)

    assert worst < 1e-6, f"clash remains: {checks}"

    cq.exporters.export(body, str(OUT / "rotor.step"))
    vertices, faces = body.tessellate(0.01, 0.05)
    mesh = trimesh.Trimesh(
        vertices=np.array([v.toTuple() for v in vertices]) / 1000,
        faces=np.array(faces),
        process=False,
    )
    scene = trimesh.Scene()
    scene.add_geometry(mesh, node_name="rotor")
    scene.export(OUT / "rotor.glb")

    bb = body.BoundingBox()
    report = {
        "scope": "Rotor as ONE machined body: the measured OEM hub plus a shell (spoked web, "
                 "magnet carrier and retaining ring) fused into a single connected solid.",
        "status": "Primeform proposal for the shell. The hub portion is measured manufacturer "
                  "geometry (occurrence NAUO45).",
        "solids": count,
        "valid": bool(body.isValid()),
        "volume_mm3": round(body.Volume(), 3),
        "bbox_mm": [round(v, 3) for v in (bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax)],
        "radial_bands_mm": {
            "hub_flange": [17.145, HUB_FLANGE_R],
            "web": [HUB_FLANGE_R, MAG_BORE],
            "magnet_band": [MAG_BORE, MAG_OD],
            "carrier_wall": [WALL_BORE, CARRIER_OD],
            "retaining_ring_bore": RING_BORE,
            "assertion": "bands are strictly increasing and non-overlapping; asserted in the builder",
        },
        "axial_bands_mm": {
            "web": [WEB_Z0, WEB_Z1],
            "base_plate": [WEB_Z0, MAG_Z0],
            "magnet_band": [MAG_Z0, MAG_Z1],
            "retaining_ring": [MAG_Z1, TOP_Z],
            "top": TOP_Z,
            "magnet_insertion": "the channel is open at the top before the retainer is fitted; "
                                "the retainer bore clears the magnets radially by 0.1 mm",
        },
        "magnet_seating": {
            "segments": SEGMENTS,
            "arc_coverage": COVERAGE,
            "magnet_vs_rotor_interference_mm3": round(magnet_vs_body, 9),
            "magnet_vs_magnet_interference_mm3": round(magnet_vs_magnet, 9),
        },
        "interference_mm3": checks,
        "worst_unintended_interference_mm3": round(worst, 9),
        "open": [
            "The sun-to-rotor fit class, retention and torque capacity are not qualified. "
            f"Measured contact {sun_v:.6f} mm3 over z 3.75 to 5.25 mm.",
            "Rotor radial placement is still unproven: this band (r 42.0 to 43.0) does not match "
            "the arcuate slots in the source housings (r 41.766 to 43.236).",
            "The measured OEM hub has a 1.225 mm rim wall and a 2.0 mm flange web, which are not "
            "structural. This body re-uses that hub as-is; the wall thicknesses are not resolved.",
        ],
    }
    (OUT / "rotor.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    # Single source of truth for the viewer's rotor-derived geometry.
    params = {
        "source": "public/design/rotor.json",
        "magnet_band_mm": [MAG_BORE, MAG_OD],
        "magnet_z_mm": [MAG_Z0, MAG_Z1],
        "segments": SEGMENTS,
        "coverage": COVERAGE,
        "bondline_mm": [round(MAG_OD, 3), round(WALL_BORE, 3)],
        "retaining_ring_mm": {"bore": RING_BORE, "outer": CARRIER_OD, "z": [MAG_Z1, TOP_Z]},
        "note": "Generated by cad/build_rotor.py. src/assembly-model.js reads these so viewer "
                "geometry cannot drift from the built rotor.",
    }
    (OUT / "viewer-rotor-params.json").write_text(json.dumps(params, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2))
    print("wrote rotor.step, rotor.glb, rotor.json, viewer-rotor-params.json")


if __name__ == "__main__":
    main()
