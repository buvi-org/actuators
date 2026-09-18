"""Build the rotor as ONE machined body: hub features + shell in a single solid.

The manufacturer part is one piece. The image shows the shell's web flowing straight
into the central hub boss, with the sun pressed into it. The study had modelled the
hub (measured OEM NAUO45) and the shell separately and then argued about how to join
them, which invented a joint that does not exist.

This takes the measured OEM hub profile as the starting point and fuses the shell onto
it as one connected solid, so there is nothing to join.

Run:  python cad/build_rotor.py
Writes: public/design/rotor.step, public/design/rotor.glb, public/design/rotor.json
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
sys.path.insert(0, str(ROOT / "cad"))
from oem import load  # noqa: E402

# Shell geometry, seated on the measured hub so the two are one body.
DISC_Z0 = -1.75          # hub flange rear face
DISC_T = 2.0
WEB_ID = 22.25           # = hub flange outer radius: the web continues out of the flange
WEB_OD = 40.5
RIM_OD = 42.4
RIM_TOP = 11.25
MAG_BORE = 40.5
MAG_Z0 = 0.25
MAG_Z1 = 11.5
SPOKES = 6
RIB_MM = 4.0
COVERAGE = 0.85
SEGMENTS = 42


def ring(ri, ro, z0, z1):
    h = z1 - z0
    return cq.Solid.makeCylinder(ro, h, cq.Vector(0, 0, z0)).cut(
        cq.Solid.makeCylinder(ri, h + 1, cq.Vector(0, 0, z0 - 0.5))
    )


def spoke_pockets(ri, ro, z0, thickness, spokes, rib_mm):
    """Wedge cutters that leave `spokes` ribs between them."""
    half = math.degrees(math.atan2(rib_mm / 2.0, ro))
    out = []
    for i in range(spokes):
        a0 = i * (360.0 / spokes) + half
        a1 = (i + 1) * (360.0 / spokes) - half
        if a1 <= a0:
            continue
        out.append(
            cq.Workplane("XY", origin=(0, 0, z0 - 0.5))
            .moveTo(0, 0)
            .lineTo(ro * 2.0, 0)
            .radiusArc(
                (ro * 2.0 * math.cos(math.radians(a1 - a0)), ro * 2.0 * math.sin(math.radians(a1 - a0))),
                ro * 2.0,
            )
            .close()
            .extrude(thickness + 1.0)
            .rotate((0, 0, 0), (0, 0, 1), a0)
            .val()
        )
    return out


def segment_polys(a, width):
    def arc(radius, steps=24):
        return [
            (
                radius * math.cos(a - width / 2 + (width * t) / (steps - 1)),
                radius * math.sin(a - width / 2 + (width * t) / (steps - 1)),
            )
            for t in range(steps)
        ]

    return arc(RIM_OD) + list(reversed(arc(MAG_BORE)))


def main():
    occ, parts, center, centered = load()
    hub = centered("NAUO45")

    # Start from the measured hub so its bores, shoulders and bore steps are preserved
    # exactly. Everything else is added to it as one body.
    body = hub

    # Shell web: same radius range as the hub flange, so it grows straight out of it.
    web = ring(WEB_ID, WEB_OD, DISC_Z0, DISC_Z0 + DISC_T)
    for cut in spoke_pockets(WEB_ID, WEB_OD, DISC_Z0, DISC_T, SPOKES, RIB_MM):
        web = web.cut(cut)
    web = web.clean()

    # Outer rim, then the 42 magnet pockets machined into it.
    rim = ring(MAG_BORE, RIM_OD, DISC_Z0, RIM_TOP)
    for i in range(SEGMENTS):
        a = (i * 2 * math.pi) / SEGMENTS
        width = ((2 * math.pi) / SEGMENTS) * COVERAGE
        pts = segment_polys(a, width)
        pocket = (
            cq.Workplane("XY", origin=(0, 0, MAG_Z0 - 0.5))
            .polyline(pts)
            .close()
            .extrude(MAG_Z1 - MAG_Z0 + 1.0)
            .val()
        )
        rim = rim.cut(pocket)
    rim = rim.clean()

    body = body.fuse(web).fuse(rim).clean()
    assert body.isValid(), "rotor body is not valid"
    count = len(body.Solids())
    assert count == 1, f"rotor must be one connected solid, got {count}"

    # The magnets, to confirm they seat with no interference in this body.
    magnets = []
    for i in range(SEGMENTS):
        a = (i * 2 * math.pi) / SEGMENTS
        width = ((2 * math.pi) / SEGMENTS) * COVERAGE
        magnets.append(
            cq.Workplane("XY", origin=(0, 0, MAG_Z0))
            .polyline(segment_polys(a, width))
            .close()
            .extrude(MAG_Z1 - MAG_Z0)
            .val()
        )

    main_h = cq.importers.importStep(str(OUT / "main-housing-supported.step")).val()
    rear = centered("NAUO4")
    sun = centered("NAUO41")

    checks = {}
    worst = 0.0
    for label, other in (("main_housing", main_h), ("rear_housing", rear), ("sun", sun)):
        v = body.intersect(other).Volume()
        checks[f"rotor_vs_{label}_mm3"] = round(v, 6)
        # The sun is a measured pilot fit (0.324 mm3) and is allowed to interfere.
        if label != "sun":
            worst = max(worst, v)
    for i, mag in enumerate(magnets):
        v = mag.intersect(body).Volume()
        if v > 1e-9:
            checks[f"magnet{i + 1}_vs_rotor_mm3"] = round(v, 6)
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
        "scope": "Rotor as ONE machined body: the measured OEM hub plus the shell (six-spoke "
                 "web and pocketed magnet rim) fused into a single connected solid. The sun is "
                 "pressed into it; there is no hub-to-shell joint to define.",
        "status": "Primeform proposal for the shell portion. The hub portion is measured "
                  "manufacturer geometry (occurrence NAUO45).",
        "solids": count,
        "valid": bool(body.isValid()),
        "volume_mm3": round(body.Volume(), 3),
        "bbox_mm": [round(v, 3) for v in (bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax)],
        "features": {
            "hub": "measured OEM profile: O44.5 x 14.5 mm, six-spoke flange r 17.145 to 22.25, "
                   "rear O6 bore, front O12 counterbore, O5.95 pilot counterbore for the sun",
            "web": f"six-spoke web r {WEB_ID} to {WEB_OD} mm, z {DISC_Z0} to {DISC_Z0 + DISC_T} mm, "
                   f"growing out of the hub flange",
            "rim": f"r {MAG_BORE} to {RIM_OD} mm, z {DISC_Z0} to {RIM_TOP} mm, with {SEGMENTS} "
                   f"magnet pockets at {COVERAGE * 100:.0f}% arc coverage",
            "magnets": f"{SEGMENTS} segments r {MAG_BORE} to {RIM_OD} mm, z {MAG_Z0} to {MAG_Z1} mm",
        },
        "interference_mm3": checks,
        "worst_unintended_interference_mm3": round(worst, 9),
        "open": [
            "The sun-to-rotor fit class, retention and torque capacity are not qualified. The "
            "measured contact is 0.324 mm3 on the O5.95 counterbore over z 3.75 to 5.25 mm.",
            "The magnet radial band (r 40.5 to 42.4 mm) does not match the arcuate slots in the "
            "source housings (r 41.766 to 43.236 mm), so rotor radial placement is unproven.",
        ],
    }
    (OUT / "rotor.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("wrote", OUT / "rotor.step", (OUT / "rotor.step").stat().st_size, "bytes")
    print("wrote", OUT / "rotor.glb", (OUT / "rotor.glb").stat().st_size, "bytes")


if __name__ == "__main__":
    main()
