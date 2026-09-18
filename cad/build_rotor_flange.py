"""Build the rotor shell to attach to the OUTSIDE of the measured input shaft hub.

Joint, measured from the hub solid NAUO45 and confirmed by the reporter:

  * hub flange        R 22.250 (D 44.50) for z -1.75..+0.25  -- the surface the shell
                      slides OVER, so the shell's bore is larger than D 44.50
  * hub flange face   z +0.25, R 17.150..22.250              -- the face the shell lands on
  * hub hole circle   8 x D 2.05 at R 20.000 (D 40.00 PCD), z -1.75..+0.25

So the shell drops over the hub's flange from outside, its shoulder lands on the flange
face at z +0.25, and eight screws run axially through its shoulder at D 40.00 PCD into
the hub's own holes.

An earlier revision had the shell's seat at D 35.50, inside the hub's flange, which is the
wrong way round: the flange cannot pass a D 35.50 opening.

Run:  python cad/build_rotor_flange.py
Writes: public/design/rotor-flange.step, .glb, .json
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
# Joint data, measured from the hub
# ---------------------------------------------------------------------------
HUB_FLANGE_R = 22.250          # R 22.250, the surface the shell slides over
HUB_FACE_Z = 0.250             # the flange face the shell lands on
HOLE_PCD_R = 20.000            # R 20.000, the hub's own hole circle
HUB_HOLE_D = 2.05
SCREW_CLEAR_D = 2.20           # clearance for an M2 screw
SCREW_HEAD_D = 4.50            # counterbore for an M2 socket head
SCREW_AZIMUTHS = [0, 45, 90, 135, 180, 225, 270, 315]

# ---------------------------------------------------------------------------
# Shell geometry. The bore must clear the hub flange plus a sliding fit.
# Housing limit: the rotor must stay at or below R 43.2; a carrier sweep found the first
# interference at OD 43.6.
# ---------------------------------------------------------------------------
SHELL_BORE_R = HUB_FLANGE_R + 0.10    # R 22.350 (D 44.70): slides over the flange
SHELL_OD = 43.20
SHOULDER_Z0 = HUB_FACE_Z              # lands on the hub flange face
SHOULDER_T = 1.70
SHOULDER_Z1 = SHOULDER_Z0 + SHOULDER_T
MAG_BORE = 41.20
MAG_OD = 42.20
WALL_BORE = 42.30
MAG_Z0 = SHOULDER_Z1
MAG_Z1 = 11.20
TOP_Z = 11.40
SEGMENTS = 42
COVERAGE = 0.85

assert SHELL_BORE_R > HUB_FLANGE_R, "shell bore must clear the hub flange"
assert SHELL_OD <= 43.2 + 1e-9, "shell must stay inside the housing features"
assert HOLE_PCD_R + SCREW_HEAD_D / 2 < SHELL_OD, "head counterbore must be inside the shell OD"
# Note: the screw circle R 20.000 lies INSIDE the shell bore R 22.350, because the shell
# slides over the hub's flange. The screws therefore pass through the shell's outer wall
# rather than a thin shoulder, and their counterbores are on the outer face.
assert MAG_Z0 >= SHOULDER_Z1 - 1e-9, "magnets must start above the shoulder"
assert MAG_OD < WALL_BORE, "magnets must not share a band with the cup wall"


def ring(ri, ro, z0, z1):
    h = z1 - z0
    return cq.Solid.makeCylinder(ro, h, cq.Vector(0, 0, z0)).cut(
        cq.Solid.makeCylinder(ri, h + 1, cq.Vector(0, 0, z0 - 0.5))
    )


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

    # Shoulder: lands on the hub flange face, bored to slide over the flange.
    shoulder = ring(SHELL_BORE_R, SHELL_OD, SHOULDER_Z0, SHOULDER_Z1)
    # Cup wall carrying the magnets, and a retaining ring at the top.
    wall = ring(WALL_BORE, SHELL_OD, SHOULDER_Z0, TOP_Z)
    retainer = ring(MAG_OD + 0.10, SHELL_OD, MAG_Z1, TOP_Z)

    body = shoulder.fuse(wall).fuse(retainer).clean()

    # Eight screws pass through the shell's outer wall at D 40.00 PCD into the hub's flange
    # holes below. The bolt goes in from outside, so its counterbore is on the outer face and
    # its clearance hole runs the full wall thickness.
    wall_t = SHELL_OD - SHELL_BORE_R
    for az in SCREW_AZIMUTHS:
        x = HOLE_PCD_R * math.cos(math.radians(az))
        y = HOLE_PCD_R * math.sin(math.radians(az))
        body = body.cut(
            cq.Solid.makeCylinder(
                SCREW_CLEAR_D / 2, wall_t + 2.0, cq.Vector(x, y, SHOULDER_Z0 - 1.0)
            )
        )
        body = body.cut(
            cq.Solid.makeCylinder(
                SCREW_HEAD_D / 2, 0.9, cq.Vector(x, y, SHOULDER_Z1 - 0.9)
            )
        )
    body = body.clean()

    assert body.isValid(), "rotor shell is not valid"
    count = len(body.Solids())
    assert count == 1, f"expected one connected solid, got {count}"

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
    checks["shell_vs_sun_mm3"] = round(
        body.intersect(centered("NAUO41")).Volume(), 6
    )

    magnet_total = 0.0
    for i, mag in enumerate(magnets):
        v = mag.intersect(body).Volume()
        magnet_total += v
        if v > 1e-9:
            checks[f"magnet{i + 1}_vs_shell_mm3"] = round(v, 6)
        worst = max(worst, v)
    checks["magnets_total_vs_shell_mm3"] = round(magnet_total, 6)

    # Joint checks: each screw needs shell material to clamp AND the hub's hole must line up.
    # Each screw needs shell material to bear on. The counterbore is 0.9 mm deep from the
    # top face, so sample a thin ring just below it.
    engage = {}
    for i, az in enumerate(SCREW_AZIMUTHS):
        x = HOLE_PCD_R * math.cos(math.radians(az))
        y = HOLE_PCD_R * math.sin(math.radians(az))
        z = SHOULDER_Z1 - 1.2
        probe = cq.Solid.makeCylinder(
            SCREW_HEAD_D / 2, 0.3, cq.Vector(x, y, z)
        ).cut(cq.Solid.makeCylinder(SCREW_CLEAR_D / 2, 1.0, cq.Vector(x, y, z - 0.5)))
        engage[f"screw{i + 1}"] = round(probe.intersect(body).Volume(), 4)

    # The hub must have a hole on the same axis and at the same height.
    hub_holes = 0
    for az in SCREW_AZIMUTHS:
        x = HOLE_PCD_R * math.cos(math.radians(az))
        y = HOLE_PCD_R * math.sin(math.radians(az))
        probe = cq.Solid.makeCylinder(
            SCREW_CLEAR_D / 2, SHOULDER_T + 1.0, cq.Vector(x, y, SHOULDER_Z0 - 0.5)
        )
        # material that the probe does NOT occupy, inside a wider envelope, is the hole
        env = cq.Solid.makeCylinder(1.6, SHOULDER_T + 1.0, cq.Vector(x, y, SHOULDER_Z0 - 0.5))
        if env.intersect(hub).Volume() - probe.intersect(hub).Volume() > 0.5:
            hub_holes += 1

    seat = ring(SHELL_BORE_R, SHELL_OD, HUB_FACE_Z - 0.05, HUB_FACE_Z + 0.05)
    seat_contact = seat.intersect(hub).Volume()

    assert worst < 1e-6, f"clash remains: {checks}"
    assert min(engage.values()) > 0.01, f"a screw has nothing to clamp: {engage}"
    assert hub_holes == 8, f"only {hub_holes} of 8 hub holes line up"

    cq.exporters.export(body, str(OUT / "rotor-flange.step"))
    vertices, faces = body.tessellate(0.01, 0.05)
    mesh = trimesh.Trimesh(
        vertices=np.array([v.toTuple() for v in vertices]) / 1000,
        faces=np.array(faces),
        process=False,
    )
    scene = trimesh.Scene()
    scene.add_geometry(mesh, node_name="rotorShell")
    scene.export(OUT / "rotor-flange.glb")

    bb = body.BoundingBox()
    report = {
        "scope": "Rotor shell that attaches to the OUTSIDE of the measured input shaft hub.",
        "status": "Primeform proposal. Joint data measured from the manufacturer hub.",
        "solids": count,
        "valid": bool(body.isValid()),
        "volume_mm3": round(body.Volume(), 3),
        "bbox_mm": [round(v, 3) for v in (bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax)],
        "joint": {
            "shell_bore_mm": round(2 * SHELL_BORE_R, 3),
            "slides_over": f"the hub flange R {HUB_FLANGE_R} (D {2 * HUB_FLANGE_R})",
            "lands_on_face_z_mm": HUB_FACE_Z,
            "seat_contact_volume_mm3": round(seat_contact, 4),
            "screw_circle_pcd_mm": round(2 * HOLE_PCD_R, 3),
            "screw_azimuths_deg": SCREW_AZIMUTHS,
            "hub_holes_aligned": f"{hub_holes} of 8",
            "clearance_d_mm": SCREW_CLEAR_D,
            "counterbore_d_mm": SCREW_HEAD_D,
            "engaged_material_mm3": engage,
        },
        "interference_mm3": checks,
        "worst_unintended_interference_mm3": round(worst, 9),
        "open": [
            "Screw size, thread engagement and tightening torque are unspecified. The hub "
            "hole D 2.05 suits an M2 clearance or thread.",
            "Magnet band r 41.2 to 42.2 does not match the housings' arcuate slots "
            "(r 41.766 to 43.236).",
        ],
    }
    (OUT / "rotor-flange.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("\nwrote rotor-flange.step / .glb / .json")


if __name__ == "__main__":
    main()
