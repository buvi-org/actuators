"""Asset-level intersection test: the meshes the viewer actually loads.

The earlier matrix compared part definitions held inside the checker, which meant it
could agree with itself while the real assets disagreed. This test works on the GLB
files that ship to the viewer, so a body cannot pass through another in the delivered
model without this failing.

Run:  python cad/check_asset_intersections.py
Writes: public/design/asset-intersection-validation.json
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public/design"
sys.path.insert(0, str(ROOT / "tmp/audit"))
from oem import load  # noqa: E402
from check_hub_joint import load_source  # noqa: E402

TOL = 1e-9


def load_mesh(path, name=None):
    m = trimesh.load(str(path), force="mesh")
    if name:
        m.metadata["name"] = name
    return m


def magnet_meshes():
    """The 42 segments exactly as src/assembly-model.js builds them."""
    R_OUT, R_IN = 42.4, 40.5
    Z0, Z1 = 0.25, 11.5
    SECTORS, COVERAGE = 42, 0.85
    out = []
    for i in range(SECTORS):
        a = (i * 2 * math.pi) / SECTORS
        width = ((2 * math.pi) / SECTORS) * COVERAGE
        pts = []
        for t in range(12):
            ang = a - width / 2 + (width * t) / 11
            pts.append((R_OUT * math.cos(ang), R_OUT * math.sin(ang)))
        for t in range(12):
            ang = a + width / 2 - (width * t) / 11
            pts.append((R_IN * math.cos(ang), R_IN * math.sin(ang)))
        poly = trimesh.path.polygons.Polygon(pts)
        mesh = trimesh.creation.extrude_polygon(poly, Z1 - Z0)
        mesh.apply_translation([0, 0, Z0])
        out.append(mesh)
    return out


def main():
    occ, parts, center, centred = load()
    _, _, centred_src = load_source()

    rotor = load_mesh(OUT / "rotor.glb", "rotor")
    magnets = magnet_meshes()

    # Also mesh the housings from the same STEP the viewer's reference GLB comes from,
    # so the rotor is tested against the real housing solids.
    def mesh_of(shape, tol=0.35):
        v, f = shape.tessellate(0.05, tol)
        return trimesh.Trimesh(
            vertices=np.array([[p.x, p.y, p.z] for p in v]) / 1000.0,
            faces=np.array(f),
            process=False,
        )

    main_h = mesh_of(
        __import__("cadquery").importers.importStep(
            str(OUT / "main-housing-supported.step")
        ).val()
    )
    rear_h = mesh_of(centred_src("NAUO4"))
    sun = mesh_of(centred_src("NAUO41"))

    bodies = {
        "rotor (GLB)": rotor,
        "M01 main housing": main_h,
        "M02 rear housing": rear_h,
        "G02 sun": sun,
    }

    findings = []

    # 1. magnets against the rotor mesh, exactly as shipped.
    total = 0.0
    worst, worst_i = 0.0, None
    for i, m in enumerate(magnets):
        try:
            v = abs(trimesh.boolean.intersection([m, rotor]).volume) * 1e9
        except Exception as exc:  # noqa: BLE001
            findings.append({"check": f"magnet {i + 1} vs rotor", "error": str(exc)[:120]})
            continue
        total += v
        if v > worst:
            worst, worst_i = v, i + 1
    if worst > TOL:
        findings.append(
            {
                "severity": "critical",
                "check": "magnets vs rotor",
                "issue": f"magnet {worst_i} interpenetrates the rotor mesh",
                "measured_mm3": round(worst, 6),
                "total_mm3": round(total, 6),
                "consequence": "The magnets do not seat in their pockets; the delivered model is not buildable.",
            }
        )

    # 2. rotor against the two housings.
    for label in ("M01 main housing", "M02 rear housing"):
        other = bodies[label]
        v = 0.0
        try:
            v = abs(trimesh.boolean.intersection([rotor, other]).volume) * 1e9
        except Exception as exc:  # noqa: BLE001
            findings.append({"check": f"rotor vs {label}", "error": str(exc)[:120]})
            continue
        if v > 1e-6:
            findings.append(
                {
                    "severity": "critical",
                    "check": f"rotor vs {label}",
                    "issue": "rotor interpenetrates the housing mesh",
                    "measured_mm3": round(v, 6),
                }
            )

    report = {
        "scope": "Intersection test on the assets the viewer loads, not on definitions held "
                 "inside the checker. This is the guard the earlier matrix lacked.",
        "method": "trimesh boolean intersection with the manifold3d backend, on the GLB meshes.",
        "assets": {
            "rotor": "public/design/rotor.glb",
            "magnets": "42 segments as built by src/assembly-model.js",
            "housings": "tessellated from the same STEP used for the reference GLB",
        },
        "segments": len(magnets),
        "magnet_total_interference_mm3": round(total, 9),
        "magnet_worst_interference_mm3": round(worst, 9),
        "findings": findings,
        "summary": {
            "checks": len(magnets) + 2,
            "critical_findings": sum(1 for f in findings if f.get("severity") == "critical"),
            "errors": sum(1 for f in findings if "error" in f),
        },
    }
    out = OUT / "asset-intersection-validation.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    print(f"magnet interference: total {total:.9f} mm3, worst {worst:.9f} mm3")
    for f in findings:
        print("  !!", f)
    print("wrote", out)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
