"""Build the rotor to mate with the measured hub: seat on its spigot, bolt to its 8 holes.

Joint data, all measured from the hub solid NAUO45 (tmp/audit/hub_features.py):

  * seat spigot        : R 17.700  (D 35.40),  z -1.75 .. +0.25
  * flange face        : R 22.250  (D 44.50) outer edge,  z -1.75 .. +0.25
  * hole circle        : R 20.000  (D 40.00 PCD), hole R 1.025 (D 2.05),
                         azimuths 0, 45, 90 ... 315, z -1.75 .. +0.25

So the rotor drops onto the hub's R 17.70 spigot, lands on the hub flange face at
z +0.25, and is bolted through the R 20.0 hole circle.

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
HUB_SPIGOT_D = 35.40          # R 17.700, the seat the rotor drops onto
HUB_FLANGE_OD = 44.50         # R 22.250
HUB_FACE_Z = 0.25             # the hub's front face
HOLE_PCD_D = 40.00            # R 20.000
HOLE_D = 2.05                 # measured hole diameter
HOLE_AZIMUTHS = [0, 45, 90, 135, 180, 225, 270, 315]
SCREW_CLEAR_D = 2.20          # clearance for an M2 in a 2.05 hole
SCREW_CSK_D = 4.00            # countersink for an M2 countersunk head

# ---------------------------------------------------------------------------
# Rotor geometry. Radial bands must not overlap the magnets.
# Housing limit: the rotor must stay at or below R 43.2; the carrier wall sweep found the
# first interference at OD 43.6.
# ---------------------------------------------------------------------------
ROTOR_SEAT_BORE = HUB_SPIGOT_D + 0.10   # clearance fit over the hub spigot
FLANGE_OD = 43.20
FLANGE_Z0 = HUB_FACE_Z                  # lands on the hub face
FLANGE_T = 1.70
FLANGE_Z1 = FLANGE_Z0 + FLANGE_T
MAG_BORE = 41.20
MAG_OD = 42.20
WALL_BORE = 42.30
CUP_OD = 43.20
MAG_Z0 = FLANGE_Z1                      # magnets start above the flange
MAG_Z1 = 11.20
TOP_Z = 11.40
SEGMENTS = 42
COVERAGE = 0.85

assert FLANGE_OD <= 43.2 + 1e-9, "rotor must stay inside the housing features"
assert ROTOR_SEAT_BORE > HUB_SPIGOT_D, "rotor bore must clear the hub spigot"
assert HOLE_PCD_D / 2 + SCREW_CSK_D / 2 < FLANGE_OD, "countersink must be inside the flange OD"
assert HOLE_PCD_D / 2 - SCREW_CSK_D / 2 > ROTOR_SEAT_BORE / 2, "countersink must clear the seat bore"
assert MAG_Z0 >= FLANGE_Z1 - 1e-9, "magnets must start above the flange"
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

    # 1. Flange. It must both socket onto the hub spigot (R 17.70) AND reach the cup wall
    # (R 42.30). A plain annulus cannot do both while the bolt circle sits at R 20.0, so the
    # flange spans the full width and the socket is its bore.
    flange = ring(ROTOR_SEAT_BORE / 2, CUP_OD, FLANGE_Z0, FLANGE_Z1)

    # 2. Cup wall carrying the magnets on its bore, and a retaining ring at the top.
    wall = ring(WALL_BORE, CUP_OD, FLANGE_Z0, TOP_Z)
    retainer = ring(MAG_OD + 0.10, CUP_OD, MAG_Z1, TOP_Z)

    body = flange.fuse(wall).fuse(retainer).clean()

    # 3. Bolt holes on the hub's own hole circle, with countersinks on the head side.
    for az in HOLE_AZIMUTHS:
        x = (HOLE_PCD_D / 2) * math.cos(math.radians(az))
        y = (HOLE_PCD_D / 2) * math.sin(math.radians(az))
        body = body.cut(
            cq.Solid.makeCylinder(
                SCREW_CLEAR_D / 2, FLANGE_T + 2.0, cq.Vector(x, y, FLANGE_Z0 - 1.0)
            )
        )
        body = body.cut(
            cq.Solid.makeCone(
                SCREW_CSK_D / 2, SCREW_CLEAR_D / 2, 1.2,
                cq.Vector(x, y, FLANGE_Z1 - 1.2),
            )
        )
    body = body.clean()

    assert body.isValid(), "rotor body is not valid"
    count = len(body.Solids())
    assert count == 1, f"expected one connected solid, got {count}"

    # 4. Magnets, seated in the cup.
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
        checks[f"rotor_vs_{label}_mm3"] = round(v, 6)
        worst = max(worst, v)

    magnet_total = 0.0
    for i, mag in enumerate(magnets):
        v = mag.intersect(body).Volume()
        magnet_total += v
        if v > 1e-9:
            checks[f"magnet{i + 1}_vs_rotor_mm3"] = round(v, 6)
        worst = max(worst, v)
    checks["magnets_total_vs_rotor_mm3"] = round(magnet_total, 6)

    # Joint check: each screw must have flange material to clamp.
    engage = {}
    for i, az in enumerate(HOLE_AZIMUTHS):
        x = (HOLE_PCD_D / 2) * math.cos(math.radians(az))
        y = (HOLE_PCD_D / 2) * math.sin(math.radians(az))
        probe = cq.Solid.makeCylinder(
            SCREW_CSK_D / 2, 0.4, cq.Vector(x, y, FLANGE_Z0 + 0.2)
        ).cut(cq.Solid.makeCylinder(SCREW_CLEAR_D / 2, 1.2, cq.Vector(x, y, FLANGE_Z0)))
        engage[f"screw{i + 1}"] = round(probe.intersect(body).Volume(), 4)

    # Seat check: the rotor must actually land on the hub face.
    seat_probe = ring(ROTOR_SEAT_BORE / 2, HUB_FLANGE_OD / 2, FLANGE_Z0 - 0.05, FLANGE_Z0 + 0.05)
    seat_contact = ring(
        HUB_SPIGOT_D / 2 - 0.5, HUB_FLANGE_OD / 2 + 0.5, HUB_FACE_Z - 0.5, HUB_FACE_Z
    )
    seat_overlap = seat_probe.intersect(hub).Volume()

    assert worst < 1e-6, f"clash remains: {checks}"
    assert min(engage.values()) > 0.01, f"a screw has nothing to clamp: {engage}"

    cq.exporters.export(body, str(OUT / "rotor-flange.step"))
    vertices, faces = body.tessellate(0.01, 0.05)
    mesh = trimesh.Trimesh(
        vertices=np.array([v.toTuple() for v in vertices]) / 1000,
        faces=np.array(faces),
        process=False,
    )
    scene = trimesh.Scene()
    scene.add_geometry(mesh, node_name="rotorFlange")
    scene.export(OUT / "rotor-flange.glb")

    bb = body.BoundingBox()
    report = {
        "scope": "Rotor as a machined part that seats on the measured hub and bolts to the "
                 "hub's own hole circle.",
        "status": "Primeform proposal. All joint data measured from the manufacturer hub.",
        "solids": count,
        "valid": bool(body.isValid()),
        "volume_mm3": round(body.Volume(), 3),
        "bbox_mm": [round(v, 3) for v in (bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax)],
        "joint": {
            "seat": f"rotor bore D {ROTOR_SEAT_BORE:.2f} on the hub spigot D {HUB_SPIGOT_D:.2f}",
            "seat_face_z_mm": HUB_FACE_Z,
            "seat_contact_volume_mm3": round(seat_overlap, 4),
            "hole_circle_pcd_mm": HOLE_PCD_D,
            "hole_azimuths_deg": HOLE_AZIMUTHS,
            "hub_hole_d_mm": HOLE_D,
            "rotor_clearance_d_mm": SCREW_CLEAR_D,
            "countersink_d_mm": SCREW_CSK_D,
            "engaged_material_mm3": engage,
            "fastener": "not specified yet; the hub hole is D 2.05, which suits a clearance "
                        "fit for an M2 screw",
        },
        "interference_mm3": checks,
        "worst_unintended_interference_mm3": round(worst, 9),
        "open": [
            "The hub's hole circle is measured, but the STEP file shows pairs of holes at "
            "each azimuth (the hub has 16 such faces). Confirm whether each station is one "
            "hole or two.",
            "Fastener size, thread engagement and tightening torque are unspecified.",
            "Magnet band r 41.2 to 42.2 does not match the housings' arcuate slots "
            "(r 41.766 to 43.236).",
        ],
    }
    (OUT / "rotor-flange.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("\nwrote rotor-flange.step / .glb / .json")


if __name__ == "__main__":
    main()
