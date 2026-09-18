"""Extract the OEM rotor hub from the manufacturer STEP as a viewer/STEP asset.

The hub is occurrence NAUO45 of the source assembly. Earlier study geometry
replaced it with a flat annulus (EM03/endbell), which is a different form in a
different place with a larger opening, so assembly step A06 had nothing to
attach. This script exports the real part instead. It is a re-export of
manufacturer geometry, not a Primeform design.

Coordinates are the assembled, centred millimetre frame used by the manifest:
source coordinates minus center_original_mm. The GLB is written in metres.

Run:  python cad/build_hub.py
Writes: public/design/oem-rotor-hub.step, public/design/oem-rotor-hub.glb
"""
from pathlib import Path
import hashlib
import json
import sys

import cadquery as cq
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public/design"
sys.path.insert(0, str(ROOT / "cad"))

from check_hub_joint import material_bands, load_source, bbox_of  # noqa: E402


def main():
    m, names, centred = load_source()
    hub = centred("NAUO45")
    assert hub.isValid(), "extracted hub solid is not valid"
    assert len(hub.Solids()) == 1, f"expected one hub solid, got {len(hub.Solids())}"

    OUT.mkdir(parents=True, exist_ok=True)
    step_path = OUT / "oem-rotor-hub.step"
    cq.exporters.export(hub, str(step_path))

    vertices, faces = hub.tessellate(0.01, 0.05)
    mesh = trimesh.Trimesh(
        vertices=np.array([v.toTuple() for v in vertices]) / 1000,
        faces=np.array(faces),
        process=False,
    )
    scene = trimesh.Scene()
    scene.add_geometry(mesh, node_name="G03")
    glb_path = OUT / "oem-rotor-hub.glb"
    scene.export(glb_path)

    bands = material_bands(hub)
    report = {
        "source_sha256": m["source_sha256"],
        "occurrence": "NAUO45",
        "product": names["NAUO45"],
        "asset_step": "public/design/oem-rotor-hub.step",
        "asset_glb": "public/design/oem-rotor-hub.glb",
        "units": {"step": "mm", "glb": "m", "frame": "assembled centred mm"},
        "bbox_mm": bbox_of(hub),
        "volume_mm3": round(hub.Volume(), 3),
        "solids": len(hub.Solids()),
        "valid": bool(hub.isValid()),
        "triangles": int(len(faces)),
        "profile_bands": [{"z_mm": [z0, z1], "material_r_mm": runs} for z0, z1, runs in bands],
        "note": (
            "Re-export of manufacturer geometry. Replaces the procedural EM03/endbell + "
            "EM03/yoke pair, which did not match the measured hub form, opening diameter or "
            "axial position. See hub-joint-validation.json."
        ),
    }
    (OUT / "oem-rotor-hub.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in report.items() if k != "profile_bands"}, indent=2))
    print("wrote", step_path, step_path.stat().st_size, "bytes")
    print("wrote", glb_path, glb_path.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
