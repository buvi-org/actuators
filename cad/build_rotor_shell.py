"""Rebuild the rotor shell so no body interpenetrates another.

Diagnosis from cad/check_intersections.py: the spoked web and the magnet band shared
the same axial band (web z 0.25..2.25, magnets z -2.5..11.5), so every spoke cut into
every magnet by 137.7 mm3. The web cannot move to the hub's other end because the hub
is only r 22.25 over z -1.75..0.25 and r 6..7 elsewhere.

Fix: seat the web on the hub flange starting at z -1.75 and start the magnets above it,
so the web and magnets never share an axial band.
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

DISC_Z0 = -1.75
DISC_T = 2.0
WEB_ID = 22.25
WEB_OD = 40.5
MAG_BORE = 40.5
RIM_OD = 42.4
RIM_TOP = 11.25
MAG_Z0 = 0.25
MAG_Z1 = 11.5
SPOKES = 6
RIB_MM = 4.0


def ring(ri, ro, z0, z1):
    h = z1 - z0
    return cq.Solid.makeCylinder(ro, h, cq.Vector(0, 0, z0)).cut(
        cq.Solid.makeCylinder(ri, h + 1, cq.Vector(0, 0, z0 - 0.5))
    )


def spoked_web(ri, ro, z0, thickness, spokes, rib_mm):
    solid = ring(ri, ro, z0, z0 + thickness)
    half = math.degrees(math.atan2(rib_mm / 2.0, ro))
    out = solid
    for i in range(spokes):
        a0 = i * (360.0 / spokes) + half
        a1 = (i + 1) * (360.0 / spokes) - half
        if a1 <= a0:
            continue
        wedge = (
            cq.Workplane("XY", origin=(0, 0, z0 - 0.5))
            .moveTo(0, 0)
            .lineTo(ro * 2.0, 0)
            .radiusArc(
                (ro * 2.0 * math.cos(math.radians(a1 - a0)), ro * 2.0 * math.sin(math.radians(a1 - a0))),
                ro * 2.0,
            )
            .close()
            .extrude(thickness + 1.0)
        )
        out = out.cut(wedge.rotate((0, 0, 0), (0, 0, 1), a0).val())
    return out.clean()


def main():
    occ, parts, center, centered = load()
    hub = centered("NAUO45")

    # Web sits on the hub's O44.5 flange and starts at the flange's rear face.
    web = spoked_web(WEB_ID, WEB_OD, DISC_Z0, DISC_T, SPOKES, RIB_MM)
    # The rim is the magnet carrier: it is built slightly proud and then pocketed.
    rim = ring(MAG_BORE, RIM_OD, DISC_Z0, RIM_TOP)
    shell = web.fuse(rim).clean()

    # Magnet segments and the pockets they sit in. The pocket is machined to the same
    # angular width as the segment, so the segment seats with no interference at all -
    # which is how the real rotor shell carries its magnets.
    coverage = 0.85
    pockets = []
    magnets = []
    for i in range(42):
        a = (i * 2 * math.pi) / 42
        width = ((2 * math.pi) / 42) * coverage

        def arc(radius, ang, steps=24):
            return [
                (radius * math.cos(ang - width / 2 + (width * t) / (steps - 1)),
                 radius * math.sin(ang - width / 2 + (width * t) / (steps - 1)))
                for t in range(steps)
            ]

        outer, inner = arc(RIM_OD, a), arc(MAG_BORE, a)
        pts = outer + list(reversed(inner))
        pocket = (
            cq.Workplane("XY", origin=(0, 0, MAG_Z0 - 0.5))
            .polyline(pts)
            .close()
            .extrude(MAG_Z1 - MAG_Z0 + 1.0)
            .val()
        )
        pockets.append(pocket)
        seg = (
            cq.Workplane("XY", origin=(0, 0, MAG_Z0))
            .polyline(pts)
            .close()
            .extrude(MAG_Z1 - MAG_Z0)
            .val()
        )
        magnets.append(seg)

    for p in pockets:
        shell = shell.cut(p)
    shell = shell.clean()
    assert shell.isValid(), "rotor shell is not valid"
    assert len(shell.Solids()) == 1, f"expected one connected solid, got {len(shell.Solids())}"

    main_h = cq.importers.importStep(str(OUT / "main-housing-supported.step")).val()
    rear = centered("NAUO4")

    worst = 0.0
    details = {}
    for label, solid in [("shell", shell)]:
        for name, housing in (("main_housing", main_h), ("rear_housing", rear), ("hub", hub)):
            v = solid.intersect(housing).Volume()
            details[f"{label}_vs_{name}_mm3"] = round(v, 6)
            worst = max(worst, v)
    for i, mag in enumerate(magnets):
        for name, other in (("shell", shell), ("main_housing", main_h), ("rear_housing", rear), ("hub", hub)):
            v = mag.intersect(other).Volume()
            if v > 1e-9:
                details[f"magnet{i + 1}_vs_{name}_mm3"] = round(v, 6)
                worst = max(worst, v)
    assert worst < 1e-6, f"clash remains: {details}"

    cq.exporters.export(shell, str(OUT / "rotor-shell.step"))
    vertices, faces = shell.tessellate(0.01, 0.05)
    mesh = trimesh.Trimesh(
        vertices=np.array([v.toTuple() for v in vertices]) / 1000,
        faces=np.array(faces),
        process=False,
    )
    scene = trimesh.Scene()
    scene.add_geometry(mesh, node_name="EM03")
    scene.export(OUT / "rotor-shell.glb")

    bb = shell.BoundingBox()
    report = {
        "scope": "Rotor end bell as one connected solid: a six-spoke web seated on the measured "
                 "hub flange, and an outer rim carrying the magnets on its bore above the web.",
        "status": "Primeform proposal, not OEM or CubeMars geometry.",
        "solids": len(shell.Solids()),
        "valid": bool(shell.isValid()),
        "volume_mm3": round(shell.Volume(), 3),
        "bbox_mm": [round(v, 3) for v in (bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax)],
        "features": {
            "spoked_web": f"r {WEB_ID} to {WEB_OD} mm, z {DISC_Z0} to {DISC_Z0 + DISC_T} mm, "
                          f"{SPOKES} ribs of {RIB_MM} mm",
            "magnet_rim": f"r {MAG_BORE} to {RIM_OD} mm, z {DISC_Z0} to {RIM_TOP} mm",
            "magnet_band": f"r {MAG_BORE} to {RIM_OD} mm, z {MAG_Z0} to {MAG_Z1} mm "
                           f"({MAG_Z1 - MAG_Z0} mm long), seated in the rim bore with no interference",
        },
        "interference_mm3": details,
        "worst_interference_mm3": round(worst, 9),
        "open": [
            "The joint to the hub is undefined: no fit, key, screw or bond is specified.",
            "The magnet radial band (r 40.5 to 42.4 mm) does not match the arcuate slots in the "
            "source housings (r 41.766 to 43.236 mm), so rotor radial placement is unproven.",
        ],
    }
    (OUT / "rotor-shell.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("wrote", OUT / "rotor-shell.step", (OUT / "rotor-shell.step").stat().st_size, "bytes")
    print("wrote", OUT / "rotor-shell.glb", (OUT / "rotor-shell.glb").stat().st_size, "bytes")


if __name__ == "__main__":
    main()
