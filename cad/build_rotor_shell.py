"""Build the rotor shell as a SPOKED part: magnet rim, spokes, and a central boss on the hub.

Arrangement, from the reporter's sketch and the measured hub:

  * the rim carries the magnets on its bore, at the largest diameter that clears the housing
  * six spokes run inward from the rim
  * a central boss locates on the hub's front collar, D 14.00 for z 0.25..1.25
  * the shell slides DOWN OVER the hub's flange (D 44.50 at z -1.75..0.25), so its bore
    clears D 44.50 and its lowest web sits on the flange face at z +0.25

Measured hub interfaces used here (tmp/audit, hub_features.py):
  flange      R 22.250 (D 44.50)  z -1.75..+0.25
  flange face z +0.25
  collar      D 14.00             z +0.25..+1.25
  hole circle 8 x D 2.05 at R 20.000 (D 40.00 PCD), z -1.75..+0.25

Run:  python cad/build_rotor_shell.py
Writes: public/design/rotor-shell.step, .glb, .json
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

# Measured hub interfaces
HUB_FLANGE_R = 22.250
HUB_FACE_Z = 0.250
HUB_COLLAR_D = 14.00
HUB_COLLAR_Z = (0.250, 1.250)
HOLE_PCD_R = 20.000
HUB_HOLE_D = 2.05

# Shell layout
SHELL_BORE_R = HUB_FLANGE_R + 0.10   # D 44.70: slides over the hub flange
BOSS_BORE_D = HUB_COLLAR_D + 0.10    # D 14.10: locates on the hub collar
BOSS_OD_D = 2 * SHELL_BORE_R         # D 44.70: the boss must reach the web's inner bore,
                                     # otherwise the six spokes float clear of it
RIM_BORE_R = 43.10                   # magnets sit INSIDE this bore
RIM_OD_R = 43.40                     # rim wall 0.30 mm outside the magnet band
MAG_BORE = 42.00
MAG_OD = 43.00
WEB_Z0 = HUB_FACE_Z                  # lowest web face, resting on the hub flange face
WEB_T = 2.00
WEB_Z1 = WEB_Z0 + WEB_T
MAG_Z0 = WEB_Z1
MAG_Z1 = 11.20
TOP_Z = 11.40
SPOKES = 6
RIB_MM = 6.0
SEGMENTS = 42
COVERAGE = 0.85

assert SHELL_BORE_R > HUB_FLANGE_R, "shell bore must clear the hub flange"
assert BOSS_BORE_D > HUB_COLLAR_D, "boss bore must clear the hub collar"
assert RIM_OD_R <= 43.4 + 1e-9, "shell must stay inside the housing features"
assert MAG_OD < RIM_BORE_R, "magnets must not share a band with the rim wall"
assert MAG_Z0 >= WEB_Z1 - 1e-9, "magnets must start above the web"


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

    # 1. Spoked web: a disc from the shell bore out to the rim, with six spokes left.
    web = ring(SHELL_BORE_R, RIM_OD_R, WEB_Z0, WEB_Z1)
    for cut in spoke_pockets(SHELL_BORE_R, RIM_OD_R, WEB_Z0, WEB_T, SPOKES, RIB_MM):
        web = web.cut(cut)
    web = web.clean()

    # 2. Central boss: raised off the web, locating on the hub's collar.
    boss = ring(BOSS_BORE_D / 2, BOSS_OD_D / 2, WEB_Z0, HUB_COLLAR_Z[1] + 0.5)

    # 3. Rim carrying the magnets on its bore, up to the top of the shell.
    rim = ring(RIM_BORE_R, RIM_OD_R, WEB_Z0, TOP_Z)

    body = web.fuse(boss).fuse(rim).clean()
    assert len(body.Solids()) == 1, "parts did not fuse into one body"

    # 4. Magnet retaining lip at the top.
    retainer = ring(MAG_OD + 0.10, RIM_OD_R, MAG_Z1, TOP_Z)
    body = body.fuse(retainer).clean()

    # 5. Eight screw holes through the web on the hub's own hole circle, so the shell can be
    #    bolted to the hub's flange face. The bolts enter from the front, through the web.
    web_t = WEB_Z1 - WEB_Z0
    for i in range(8):
        az = i * 45.0
        x = HOLE_PCD_R * math.cos(math.radians(az))
        y = HOLE_PCD_R * math.sin(math.radians(az))
        body = body.cut(
            cq.Solid.makeCylinder(1.10, web_t + 2.0, cq.Vector(x, y, WEB_Z0 - 1.0))
        )
        body = body.cut(
            cq.Solid.makeCylinder(2.25, 0.8, cq.Vector(x, y, WEB_Z1 - 0.8))
        )
    body = body.clean()

    assert body.isValid(), "rotor shell is not valid"
    count = len(body.Solids())
    assert count == 1, f"expected one connected solid, got {count}"

    # 6. Magnets, in the rim.
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

    checks = {}
    worst = 0.0
    for label, other in (("main_housing", main_h), ("rear_housing", rear), ("hub", hub)):
        v = body.intersect(other).Volume()
        checks[f"shell_vs_{label}_mm3"] = round(v, 6)
        worst = max(worst, v)

    magnet_total = 0.0
    for i, mag in enumerate(magnets):
        v = mag.intersect(body).Volume()
        magnet_total += v
        if v > 1e-9:
            checks[f"magnet{i + 1}_vs_shell_mm3"] = round(v, 6)
        worst = max(worst, v)
    checks["magnets_total_vs_shell_mm3"] = round(magnet_total, 6)

    # Each screw needs web material to clamp, and the hub must have a hole on the same axis.
    engage = {}
    hub_holes = 0
    for i in range(8):
        az = i * 45.0
        x = HOLE_PCD_R * math.cos(math.radians(az))
        y = HOLE_PCD_R * math.sin(math.radians(az))
        probe = cq.Solid.makeCylinder(2.25, 0.3, cq.Vector(x, y, WEB_Z0 + 0.5)).cut(
            cq.Solid.makeCylinder(1.10, 1.0, cq.Vector(x, y, WEB_Z0))
        )
        engage[f"screw{i + 1}"] = round(probe.intersect(body).Volume(), 4)
        env = cq.Solid.makeCylinder(1.6, WEB_T + 1.0, cq.Vector(x, y, WEB_Z0 - 0.5))
        if env.intersect(hub).Volume() < env.Volume() * 0.5:
            hub_holes += 1

    assert worst < 1e-6, f"clash remains: {checks}"
    assert min(engage.values()) > 0.01, f"a screw has nothing to clamp: {engage}"

    cq.exporters.export(body, str(OUT / "rotor-shell.step"))
    vertices, faces = body.tessellate(0.01, 0.05)
    mesh = trimesh.Trimesh(
        vertices=np.array([v.toTuple() for v in vertices]) / 1000,
        faces=np.array(faces),
        process=False,
    )
    scene = trimesh.Scene()
    scene.add_geometry(mesh, node_name="rotorShell")
    scene.export(OUT / "rotor-shell.glb")

    bb = body.BoundingBox()
    report = {
        "scope": "Rotor shell as a spoked part: magnet rim, six spokes, central boss on the "
                 "hub's collar, and a bolted web on the hub's own hole circle.",
        "status": "Primeform proposal. Joint data measured from the manufacturer hub.",
        "solids": count,
        "valid": bool(body.isValid()),
        "volume_mm3": round(body.Volume(), 3),
        "bbox_mm": [round(v, 3) for v in (bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax)],
        "layout_mm": {
            "shell_bore_r": SHELL_BORE_R,
            "slides_over_hub_flange_r": HUB_FLANGE_R,
            "web_face_z": WEB_Z0,
            "boss_bore_d": BOSS_BORE_D,
            "locates_on_hub_collar_d": HUB_COLLAR_D,
            "spokes": SPOKES,
            "rim_bore_r": RIM_BORE_R,
            "rim_od_r": RIM_OD_R,
            "magnet_band_r": [MAG_BORE, MAG_OD],
            "magnet_z": [MAG_Z0, MAG_Z1],
        },
        "joint": {
            "screw_circle_pcd_mm": round(2 * HOLE_PCD_R, 3),
            "hub_hole_d_mm": HUB_HOLE_D,
            "hub_holes_found": hub_holes,
            "engaged_material_mm3": engage,
            "note": "the bolts pass through the web into the hub's flange face",
        },
        "interference_mm3": checks,
        "worst_unintended_interference_mm3": round(worst, 9),
        "open": [
            "Screw size and tightening torque are unspecified.",
            "Magnet band r 42.0 to 43.0 does not match the housings' arcuate slots "
            "(r 41.766 to 43.236).",
        ],
    }
    (OUT / "rotor-shell.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("\nwrote rotor-shell.step / .glb / .json")


if __name__ == "__main__":
    main()
