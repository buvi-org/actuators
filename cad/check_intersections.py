"""Pairwise intersection matrix for every modelled body, plus intended-contact checks.

This is the regression guard the project was missing: every time the geometry changes,
every pair of bodies is tested for interpenetration and for the contacts that are
supposed to exist. A step that claims a fit is only real if the test says so.

The part definitions mirror src/assembly-model.js and cad/build_*.py. If those change,
this must change with them, or the check silently stops describing the model.

Run:  python cad/check_intersections.py
Writes: public/design/intersection-matrix.json
"""
import json
import math
import sys
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cad"))
sys.path.insert(0, str(ROOT / "tmp/audit"))
from check_hub_joint import load_source  # noqa: E402

TOL = 1e-6


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


def magnet_set(count=42, ri=40.5, ro=42.4, z0=0.25, z1=11.5, coverage=0.85):
    """The 42 magnet segments exactly as the viewer builds them."""
    solids = []
    for i in range(count):
        a = (i * 2 * math.pi) / count
        width = ((2 * math.pi) / count) * coverage
        shape = cq.Workplane("XY").moveTo(0, 0)
        pts = []
        for t in range(24):
            ang = a - width / 2 + (width * t) / 23
            pts.append((ro * math.cos(ang), ro * math.sin(ang)))
        for t in range(24):
            ang = a + width / 2 - (width * t) / 23
            pts.append((ri * math.cos(ang), ri * math.sin(ang)))
        shape = shape.polyline(pts).close().extrude(z1 - z0).translate((0, 0, z0))
        solids.append(shape.val())
    return solids


def main():
    m, names, centred = load_source()
    hub = centred("NAUO45")
    sun = centred("NAUO41")
    rear_bearing = centred("NAUO42")
    front_bearing = centred("NAUO43")
    encoder = centred("NAUO44")
    main_h = cq.importers.importStep(str(ROOT / "public/design/main-housing-supported.step")).val()
    rear_h = centred("NAUO4")

    shell = cq.importers.importStep(str(ROOT / "public/design/rotor-shell.step")).val()

    bodies = {
        "M01 main housing": main_h,
        "M02 rear housing": rear_h,
        "G03 hub": hub,
        "G02 sun": sun,
        "B03 6701 rear": rear_bearing,
        "B03 6701 front": front_bearing,
        "E02 encoder magnet": encoder,
        "EM03 rotor end bell": shell,
    }
    magnets = magnet_set()
    for i, mag in enumerate(magnets):
        bodies[f"EM04 magnet {i + 1}"] = mag

    # Intended joints: a fit is real only if the test agrees.
    INTENDED = {
        ("G03 hub", "G02 sun"): "pilot fit",
        ("G03 hub", "B03 6701 rear"): "bearing seat",
        ("G03 hub", "B03 6701 front"): "bearing seat",
        ("G03 hub", "E02 encoder magnet"): "magnet seat",
        ("EM03 rotor end bell", "G03 hub"): "shell to hub (UNDEFINED joint)",
        ("M01 main housing", "M02 rear housing"): "housing joint face",
    }
    # Pairs that must never interpenetrate.
    MUST_CLEAR = {
        ("M01 main housing", "M02 rear housing"),
        ("M01 main housing", "EM03 rotor end bell"),
        ("M02 rear housing", "EM03 rotor end bell"),
        ("M01 main housing", "G03 hub"),
        ("M02 rear housing", "G03 hub"),
        ("M02 rear housing", "G02 sun"),
        ("EM03 rotor end bell", "G02 sun"),
        ("EM03 rotor end bell", "B03 6701 rear"),
        ("EM03 rotor end bell", "B03 6701 front"),
        ("EM03 rotor end bell", "E02 encoder magnet"),
    }

    keys = list(bodies)
    clashes = []
    contacts = []
    rows = []
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            va = bodies[a].intersect(bodies[b]).Volume()
            if va > TOL:
                clashes.append(
                    {
                        "a": a,
                        "b": b,
                        "interference_mm3": round(va, 6),
                        "intended": INTENDED.get((a, b)) or INTENDED.get((b, a)) or None,
                    }
                )
    for (a, b), label in INTENDED.items():
        if a not in bodies or b not in bodies:
            continue
        v = bodies[a].intersect(bodies[b]).Volume()
        d = bodies[a].distance(bodies[b])
        contacts.append(
            {
                "a": a,
                "b": b,
                "intent": label,
                "interference_mm3": round(v, 6),
                "min_distance_mm": round(d, 6),
                "result": "contact" if (v > TOL or d < 1e-4) else "FAIL - no contact",
            }
        )

    must_clear_fail = [
        c for c in clashes
        if (c["a"], c["b"]) in MUST_CLEAR or (c["b"], c["a"]) in MUST_CLEAR
    ]
    # Magnets are supposed to be bonded on the shell's bore, not inside the rim material.
    mag_clash = [c for c in clashes if c["a"].startswith("EM04") or c["b"].startswith("EM04")]

    report = {
        "scope": "Pairwise intersection matrix for every modelled body, plus intended-contact "
                 "checks. Re-run after every geometry change.",
        "frame": "assembled centred mm",
        "bodies": keys,
        "pair_count": len(keys) * (len(keys) - 1) // 2,
        "clashes": clashes,
        "intended_contacts": contacts,
        "must_clear_violations": must_clear_fail,
        "magnet_clashes": mag_clash[:12],
        "summary": {
            "bodies": len(keys),
            "pairs_tested": len(keys) * (len(keys) - 1) // 2,
            "clashing_pairs": len(clashes),
            "must_clear_violations": len(must_clear_fail),
            "magnet_clashing_pairs": len(mag_clash),
            "contacts_missing": sum(1 for c in contacts if c["result"].startswith("FAIL")),
        },
    }
    out = ROOT / "public/design/intersection-matrix.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report["summary"], indent=2))
    print("\n=== clashes ===")
    for c in clashes:
        tag = c["intended"] and f" (intended: {c['intended']})" or "  <-- UNINTENDED"
        print(f"  {c['a']:22} x {c['b']:22} {c['interference_mm3']:10.3f} mm3{tag}")
    if not clashes:
        print("  none")
    print("\n=== intended contacts ===")
    for c in contacts:
        print(f"  {c['a']:22} x {c['b']:22} {c['result']:18} "
              f"ov {c['interference_mm3']:9.4f} mm3  gap {c['min_distance_mm']:.4f} mm  [{c['intent']}]")
    print("\nwrote", out)


if __name__ == "__main__":
    main()
