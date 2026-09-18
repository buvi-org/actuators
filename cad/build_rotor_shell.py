"""Build the rotor shell as ONE connected solid, following the manufacturer arrangement.

The manufacturer part is a single spoked shell whose outer rim carries the magnets; the
sun is force-fitted into it. The earlier study split that into a disc plus a separate
rim, which invented a joint that does not exist. This builds it as one body.

Form follows the measured hub: a six-spoke web on the hub's O44.5 front face, a solid
outer rim carrying the magnets, and a thin closing flange at the far end.

Run:  python cad/build_rotor_shell.py
Writes: public/design/rotor-shell.step, public/design/rotor-shell.glb, rotor-shell.json
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

# Layout (assembled mm). The shell sits 4.5 mm forward of the original magnet band so the
# stator at its manufacturer position is fully covered.
HUB_FACE_Z = 0.25
DISC_T = 2.0
WEB_ID = 22.25
WEB_OD = 40.5
RIM_OD = 42.4
RIM_TOP = 11.25
MAG_BORE = 40.5
SPOKES = 6
RIB_MM = 4.0
MAG_Z0 = -2.5          # magnet band rear face; the shell closes here
CLOSE_T = 1.5


def ring(ri, ro, z0, z1):
    h = z1 - z0
    return cq.Solid.makeCylinder(ro, h, cq.Vector(0, 0, z0)).cut(
        cq.Solid.makeCylinder(ri, h + 1, cq.Vector(0, 0, z0 - 0.5))
    )


def spoked_web(ri, ro, z0, thickness, spokes, rib_mm):
    """Thin disc with pie-slice pockets, leaving `spokes` ribs of width rib_mm."""
    solid = ring(ri, ro, z0, z0 + thickness)
    half = math.degrees(math.atan2(rib_mm / 2.0, ro))
    pockets = []
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
        pockets.append(wedge.rotate((0, 0, 0), (0, 0, 1), a0).val())
    out = solid
    for p in pockets:
        out = out.cut(p)
    return out.clean()


def main():
    occ, parts, center, centered = load()
    hub = centered("NAUO45")

    web = spoked_web(WEB_ID, WEB_OD, HUB_FACE_Z, DISC_T, SPOKES, RIB_MM)
    # The rim starts 0.25 mm below the web's top face so the two bodies overlap in volume
    # and fuse into one connected solid rather than merely touching.
    rim = ring(MAG_BORE, RIM_OD, HUB_FACE_Z - 0.25, RIM_TOP)
    # Close the back of the magnet band. It must stay inside the main housing's conical
    # bore, which narrows to r 44.050 mm over z -4.31..3.08, so the closing flange sits
    # at the rear of the band where the wall is still wide.
    close = ring(MAG_BORE, RIM_OD, MAG_Z0, MAG_Z0 + CLOSE_T)
    # Overlap the closing flange into the rim so the body is connected, not just touching.
    rim = ring(MAG_BORE, RIM_OD, MAG_Z0, RIM_TOP)
    shell = web.fuse(rim).fuse(close).clean()

    assert shell.isValid(), "rotor shell is not valid"
    solids = len(shell.Solids())
    assert solids == 1, f"rotor shell must be one connected solid, got {solids}"

    main_h = cq.importers.importStep(str(OUT / "main-housing-supported.step")).val()
    rear = centered("NAUO4")
    clash = {
        "main_housing_mm3": round(shell.intersect(main_h).Volume(), 6),
        "rear_housing_mm3": round(shell.intersect(rear).Volume(), 6),
        "hub_mm3": round(shell.intersect(hub).Volume(), 6),
    }
    assert max(clash.values()) < 1e-6, f"rotor shell clashes: {clash}"

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
        "scope": "Rotor shell as one connected solid, following the manufacturer arrangement "
                 "(spoked shell carrying the magnets on its rim, sun force-fitted into the hub).",
        "status": "Primeform proposal: not OEM or CubeMars geometry. Sizing is measured from the "
                  "source housing bore, the hub flange and the stator position.",
        "solids": solids,
        "valid": bool(shell.isValid()),
        "volume_mm3": round(shell.Volume(), 3),
        "bbox_mm": [round(v, 3) for v in (bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax)],
        "features": {
            "spoked_web": f"r {WEB_ID} to {WEB_OD} mm, z {HUB_FACE_Z} to {HUB_FACE_Z + DISC_T} mm, "
                          f"{SPOKES} ribs of {RIB_MM} mm",
            "magnet_rim": f"r {MAG_BORE} to {RIM_OD} mm, z {MAG_Z0} to {RIM_TOP} mm, "
                          f"magnets bonded on the {MAG_BORE * 2} mm bore",
            "closing_flange": f"r {MAG_BORE} to {RIM_OD} mm, z {MAG_Z0} to {MAG_Z0 + CLOSE_T} mm, "
                              f"closing the rear of the magnet band",
        },
        "clash_mm3": clash,
        "open": [
            "The joint to the hub is undefined: no fit, key, screw or bond is specified.",
            "The magnet radial band (r 40.5 to 42.5 mm) does not match the arcuate slots in the "
            "source housings (r 41.766 to 43.236 mm), so rotor radial placement is unproven.",
        ],
    }
    (OUT / "rotor-shell.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("wrote", OUT / "rotor-shell.step", (OUT / "rotor-shell.step").stat().st_size, "bytes")
    print("wrote", OUT / "rotor-shell.glb", (OUT / "rotor-shell.glb").stat().st_size, "bytes")


if __name__ == "__main__":
    main()
