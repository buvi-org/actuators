"""Audit every claimed joint in the assembly for contact, gap and clash.

The project's previous checks verified zero overlap, which cannot distinguish a
seated joint from a floating part. This check measures both directions: for each
claimed joint it reports interference volume and minimum distance, and it verifies
the axial cadence between parts that must be bolted, bonded or meshed together.

Run:  python cad/check_assembly_contacts.py
Writes: public/design/assembly-contact-validation.json
"""
import json
import sys
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cad"))
sys.path.insert(0, str(ROOT / "tmp/audit"))

from check_hub_joint import load_source  # noqa: E402

GEAR_Z = 8.25
GEAR_WIDTH = 5.0
RING_FACE_TOP = GEAR_Z + GEAR_WIDTH / 2
SCREW_TIP_Z = 9.95


def annulus(ri, ro, z0, z1):
    h = z1 - z0
    return cq.Solid.makeCylinder(ro, h, cq.Vector(0, 0, z0)).cut(
        cq.Solid.makeCylinder(ri, h + 1, cq.Vector(0, 0, z0 - 0.5))
    )


def main():
    m, names, centred = load_source()
    choice = json.loads((ROOT / "public/data/packaging-choice.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "public/models/manifest.json").read_text(encoding="utf-8"))

    stack = choice["stack_length_mm"]
    seat = choice["housing_seat_z_mm"]
    ring_z = choice["ring_z_mm"]

    findings = []
    joints = []

    def joint(step, a, b, a_shape, b_shape, expect_contact):
        ia = a_shape.intersect(b_shape).Volume()
        dist = a_shape.distance(b_shape)
        ok = (ia > 1e-6) if expect_contact == "overlap" else (dist < 1e-4)
        joints.append(
            {
                "step": step,
                "a": a,
                "b": b,
                "interference_mm3": round(ia, 6),
                "min_distance_mm": round(dist, 6),
                "expected": expect_contact,
                "result": "pass" if ok else "FAIL",
            }
        )

    # A02/A03: the ring must be clamped by the eight front screws.
    ring_flange = annulus(24.9, 29.98, ring_z[0] + 3.0, ring_z[1])
    screw_ids = ["NAUO7"] + [f"NAUO{i}" for i in range(22, 29)]
    engage = {}
    for p in manifest["parts"]:
        if p["id"] not in screw_ids:
            continue
        b = p["bounds_mm"]
        x, y = (b[0] + b[3]) / 2, (b[1] + b[4]) / 2
        bore = cq.Solid.makeCylinder(1.025, 6.0, cq.Vector(x, y, b[2]))
        engage[p["id"]] = round(ring_flange.intersect(bore).Volume(), 4)
    if max(engage.values()) < 0.01:
        findings.append(
            {
                "step": "A03",
                "severity": "critical",
                "issue": "Ring is not clamped by any front screw",
                "measured": f"eight screws engage {max(engage.values()):.4f} mm3 of ring material; "
                            f"ring flange top z {ring_z[1]:.3f}, screw tips z {SCREW_TIP_Z:.3f}, "
                            f"gap {SCREW_TIP_Z - ring_z[1]:.3f} mm",
                "consequence": "The ring and the stator it carries have no load path to the housing; "
                               "the eight screws hold nothing.",
            }
        )

    # A02/A04: ring flange must be co-located with the ring's toothed section.
    if ring_z[1] < RING_FACE_TOP:
        findings.append(
            {
                "step": "A02, A04",
                "severity": "major",
                "issue": "Ring mounting flange no longer overlaps the ring's toothed band",
                "measured": f"toothed band top z {RING_FACE_TOP:.3f}, flange top z {ring_z[1]:.3f}, "
                            f"shortfall {RING_FACE_TOP - ring_z[1]:.3f} mm",
                "consequence": "The flange is intended to be the ring's mounting rim; it now sits "
                               "below the teeth it is meant to carry.",
            }
        )

    # A04: stator must contact the housing seat.
    stator_front = stack / 2
    if abs(stator_front - seat) > 1e-6:
        findings.append(
            {
                "step": "A04",
                "severity": "critical",
                "issue": "Stator front face does not reach the housing seat",
                "measured": f"stator front z {stator_front:.3f}, seat z {seat:.3f}",
                "consequence": "No axial stop; the stator is located by adhesive alone.",
            }
        )

    # A04: stator/magnet axial overlap.
    overlap = min(7.0, stack / 2) - max(-7.0, -stack / 2)
    joints.append(
        {
            "step": "A04/A05",
            "a": "stator stack",
            "b": "magnet band",
            "interference_mm3": None,
            "min_distance_mm": None,
            "expected": "axial overlap",
            "result": "pass" if overlap > 13.0 else "FAIL",
            "note": f"axial overlap {overlap:.3f} mm",
        }
    )

    # A06: hub joints.
    hub = centred("NAUO45")
    joint("A06", "hub", "sun", hub, centred("NAUO41"), "overlap")
    joint("A08", "hub", "6701 rear", hub, centred("NAUO42"), "touch")
    joint("A08", "hub", "6701 front", hub, centred("NAUO43"), "touch")
    joint("A16", "hub", "encoder magnet", hub, centred("NAUO44"), "touch")

    # A05/A06: the carrier must contact the hub it is said to be anchored on.
    web = annulus(22.25, 40.5, -5.0, 5.0)
    ic = hub.intersect(web).Volume()
    dc = hub.distance(web)
    joints.append(
        {
            "step": "A06",
            "a": "carrier web",
            "b": "hub",
            "interference_mm3": round(ic, 6),
            "min_distance_mm": round(dc, 6),
            "expected": "contact",
            "result": "pass" if (ic > 1e-6 or dc < 1e-4) else "FAIL",
            "note": "coincident faces only: no fit, key, screw or bond is defined",
        }
    )
    if ic < 1e-6:
        findings.append(
            {
                "step": "A06",
                "severity": "major",
                "issue": "Carrier is retained on the hub by nothing",
                "measured": f"carrier web vs hub interference {ic:.6f} mm3, min distance {dc:.4f} mm",
                "consequence": "Coincident radii at r 22.25 mm with no fit class, key, screw or "
                               "bond. The rotor torque path from carrier to hub is undefined.",
            }
        )

    # A05/A14: carrier clash with the rear housing.
    main_h = cq.importers.importStep(str(ROOT / "public/design/main-housing-supported.step")).val()
    clash_main = web.intersect(main_h).Volume()
    clash_rear = web.intersect(centred("NAUO4")).Volume()
    if clash_rear > 1e-6:
        findings.append(
            {
                "step": "A05, A14",
                "severity": "major",
                "issue": "Carrier web intersects the rear housing",
                "measured": f"{clash_rear:.3f} mm3 against NAUO4 (inward wall only r 29 mm over "
                            f"z -5.25..-4.75); {clash_main:.3f} mm3 against the modified main housing",
                "consequence": "The rear housing cannot be seated while the carrier spans z -5..+5.",
            }
        )

    # A11: output bearings must seat in something.
    seats = {}
    for name, label in (("NAUO39", "6707-ZZ"), ("NAUO38", "625-ZZ")):
        s = centred(name)
        seats[label] = {
            "vs_main_housing_mm3": round(s.intersect(centred("NAUO3")).Volume(), 6),
            "vs_lower_carrier_mm3": round(s.intersect(centred("NAUO37")).Volume(), 6),
            "min_distance_main_mm": round(s.distance(centred("NAUO3")), 6),
            "min_distance_carrier_mm": round(s.distance(centred("NAUO37")), 6),
        }
    if all(v["min_distance_main_mm"] > 1e-3 and v["min_distance_carrier_mm"] > 1e-3 for v in seats.values()):
        findings.append(
            {
                "step": "A11",
                "severity": "major",
                "issue": "Output bearings have no identified seat in either claimed receiver",
                "measured": json.dumps(seats),
                "consequence": "A11 claims seats in M01 and G01, but both bearings clear both parts. "
                               "Race ownership, shoulders and preload remain undefined.",
            }
        )

    # A14: rear housing against the main housing.
    m01, m02 = centred("NAUO3"), centred("NAUO4")
    rear_inter = m02.intersect(m01).Volume()
    joints.append(
        {
            "step": "A14",
            "a": "rear housing",
            "b": "main housing",
            "interference_mm3": round(rear_inter, 6),
            "min_distance_mm": round(m02.distance(m01), 6),
            "expected": "contact",
            "result": "pass" if (rear_inter > 1e-6 or m02.distance(m01) < 1e-4) else "FAIL",
        }
    )

    report = {
        "scope": "Contact audit of every claimed joint. Measures interference and minimum "
                 "distance, because zero overlap alone cannot tell a seated joint from a floating part.",
        "frame": "assembled centred mm",
        "declared_axial_layout": {
            "stator_stack_z_mm": [-stack / 2, stack / 2],
            "housing_seat_z_mm": seat,
            "ring_flange_z_mm": ring_z,
            "gear_mesh_plane_z_mm": GEAR_Z,
            "magnet_band_z_mm": [-7.0, 7.0],
            "stator_magnet_overlap_mm": round(overlap, 3),
        },
        "joints": joints,
        "findings": findings,
        "summary": {
            "joints_checked": len(joints),
            "joints_failed": sum(1 for j in joints if j["result"] == "FAIL"),
            "findings": len(findings),
            "critical": sum(1 for f in findings if f["severity"] == "critical"),
            "major": sum(1 for f in findings if f["severity"] == "major"),
        },
    }
    out = ROOT / "public/design/assembly-contact-validation.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    for f in findings:
        print(f"\n[{f['severity'].upper()}] {f['step']}: {f['issue']}")
        print(f"   measured   : {f['measured']}")
        print(f"   consequence: {f['consequence']}")
    print("\nwrote", out)


if __name__ == "__main__":
    main()
