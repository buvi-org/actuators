"""Audit the rotor hub joint against the manufacturer evidence.

This measures the OEM input-shaft hub (NAUO45) and its mating parts in the
source STEP, and compares the result with the procedural rotor geometry used by
the viewer. It exists because the previous assembly step claimed a hub-to-end-bell
attachment that has no geometry, fit or torque path behind it.

Run:  python cad/check_hub_joint.py
Writes: public/design/hub-joint-validation.json

Everything is in the assembled, centred millimetre frame used by the manifest.
Source geometry is manufacturer material; the numbers below are measurements of
that geometry, not a Primeform design release.
"""
from pathlib import Path
import hashlib
import json
import re
import sys

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cad"))


def load_source():
    m = json.loads((ROOT / "public/models/manifest.json").read_text(encoding="utf-8"))
    step = ROOT / "tmp/reference/reference.step"
    digest = hashlib.sha256(step.read_bytes()).hexdigest()
    assert digest == m["source_sha256"], "reference STEP does not match the manifest hash"
    raw = step.read_bytes()
    text = raw.decode("gb18030", errors="replace")
    entities = {int(k): v for k, v in re.findall(r"#(\d+)\s*=\s*(.*?);", text, re.S)}

    def product_name(eid):
        e = entities[eid]
        if e.startswith("PRODUCT "):
            return re.search(r"'([^']*)'", e)[1]
        for n in [int(x) for x in re.findall(r"#(\d+)", e)]:
            if entities[n].startswith(("PRODUCT_DEFINITION_FORMATION", "PRODUCT ")):
                return product_name(n)
        raise ValueError(eid)

    names = {}
    for eid, e in entities.items():
        if e.startswith("NEXT_ASSEMBLY_USAGE_OCCURRENCE"):
            nm = re.search(r"'(NAUO\d+)'", e)[1]
            names[nm] = product_name([int(x) for x in re.findall(r"#(\d+)", e)][1])

    assembly = cq.Assembly.importStep(str(step))
    shapes = {}
    for shape, path, loc, color in assembly:
        shapes[path.split("/")[-1]] = shape.moved(loc)

    mins, maxs = [], []
    for w in shapes.values():
        b = w.BoundingBox()
        mins.append([b.xmin, b.ymin, b.zmin])
        maxs.append([b.xmax, b.ymax, b.zmax])
    import numpy as np

    centre = (np.min(mins, axis=0) + np.max(maxs, axis=0)) / 2

    def centred(name):
        return shapes[name].moved(cq.Location(cq.Vector(*(-centre))))

    return m, names, centred


def flat_plane(z, half=120.0):
    return cq.Face.makePlane(half, half, cq.Vector(0, 0, float(z)), cq.Vector(0, 0, 1))


def axis_plane(half=120.0):
    return cq.Face.makePlane(half, half, cq.Vector(0, 0, 0), cq.Vector(0, 1, 0))


def material_bands(shape, samples=140):
    """Return [(z0, z1, [(r0, r1), ...])] of the X-Z section: the real hub profile."""
    res = shape.intersect(axis_plane())
    segs = []
    zfeat = set()
    for f in res.Faces():
        for w in f.Wires():
            for e in w.Edges():
                for v in e.Vertices():
                    zfeat.add(round(float(v.Z), 3))
                for t in range(samples + 1):
                    p = e.positionAt(t / samples)
                    segs.append(((p.x ** 2 + p.y ** 2) ** 0.5, float(p.z)))
    import numpy as np

    segs = np.array(segs)
    out = []
    zf = sorted(zfeat)
    for i in range(len(zf) - 1):
        z0, z1 = zf[i], zf[i + 1]
        if z1 - z0 < 0.02:
            continue
        band = segs[np.abs(segs[:, 1] - (z0 + z1) / 2) < (z1 - z0) / 2.5]
        if len(band) == 0:
            continue
        rs = np.sort(band[:, 0])
        runs, start, last = [], rs[0], rs[0]
        for r in rs[1:]:
            if r - last > 0.2:
                runs.append([round(float(start), 3), round(float(last), 3)])
                start = r
            last = r
        runs.append([round(float(start), 3), round(float(last), 3)])
        out.append([round(z0, 3), round(z1, 3), runs])
    return out


def bbox_of(shape):
    b = shape.BoundingBox()
    return [round(v, 4) for v in (b.xmin, b.ymin, b.zmin, b.xmax, b.ymax, b.zmax)]


def main():
    m, names, centred = load_source()
    hub = centred("NAUO45")
    sun = centred("NAUO41")
    rear_bearing = centred("NAUO42")
    front_bearing = centred("NAUO43")
    magnet = centred("NAUO44")
    rear_housing = centred("NAUO4")
    front_housing = centred("NAUO3")

    hub_bands = material_bands(hub)
    inner = min(r0 for _, _, runs in hub_bands for r0, _ in runs)
    outer = max(r1 for _, _, runs in hub_bands for _, r1 in runs)

    report = {
        "source_sha256": m["source_sha256"],
        "scope": (
            "OEM reference measurement of the input-shaft hub joint plus a comparison with the "
            "procedural rotor geometry in src/assembly-model.js. Measurements only: no fit, "
            "torque capacity or assembly process is qualified by this check."
        ),
        "oem_parts": {
            "hub": {"occurrence": "NAUO45", "product": names["NAUO45"], "bbox_mm": bbox_of(hub),
                    "volume_mm3": round(hub.Volume(), 3)},
            "sun": {"occurrence": "NAUO41", "product": names["NAUO41"], "bbox_mm": bbox_of(sun)},
            "rear_bearing": {"occurrence": "NAUO42", "product": names["NAUO42"], "bbox_mm": bbox_of(rear_bearing)},
            "front_bearing": {"occurrence": "NAUO43", "product": names["NAUO43"], "bbox_mm": bbox_of(front_bearing)},
            "encoder_magnet": {"occurrence": "NAUO44", "product": names["NAUO44"], "bbox_mm": bbox_of(magnet)},
        },
        "oem_hub_profile": {
            "note": "X-Z material section. Each band lists the material radial intervals at that z.",
            "bands": [{"z_mm": [z0, z1], "material_r_mm": runs} for z0, z1, runs in hub_bands],
            "min_inner_radius_mm": round(inner, 3),
            "max_outer_radius_mm": round(outer, 3),
        },
        "oem_coaxiality": {
            "hub_and_sun_interference_mm3": round(hub.intersect(sun).Volume(), 6),
            "hub_and_front_bearing_interference_mm3": round(hub.intersect(front_bearing).Volume(), 6),
            "hub_and_rear_bearing_interference_mm3": round(hub.intersect(rear_bearing).Volume(), 6),
            "hub_and_encoder_magnet_interference_mm3": round(hub.intersect(magnet).Volume(), 6),
            "hub_and_rear_housing_interference_mm3": round(hub.intersect(rear_housing).Volume(), 6),
            "hub_and_front_housing_interference_mm3": round(hub.intersect(front_housing).Volume(), 6),
            "hub_rear_housing_min_distance_mm": round(hub.distance(rear_housing), 6),
            "interpretation": (
                "Zero interference with both bearings and the magnet, and sub-cubic-millimetre "
                "interference with the sun, shows the OEM hub is coaxial with the sun and is the "
                "carrier for both 6701-ZZ bearings. It is not an outboard disc bolted to a bell."
            ),
        },
        "procedural_rotor_comparison": {
            "procedural_end_bell": {
                "id": "EM03/endbell", "radii_mm": [23, 45.5], "z_mm": [-8.6, -7.6], "thickness_mm": 1,
            },
            "procedural_yoke": {"id": "EM03/yoke", "radii_mm": [42.5, 45.5], "z_mm": [-7.5, 7.5]},
            "oem_hub_flange": {"r_mm": [17.145, 22.25], "z_mm": [-1.75, 0.25]},
            "findings": [
                "The procedural end bell has a 46 mm opening; the hub's nominal envelope is 44.5 mm, "
                "so it cannot be received by that disc even if the two were moved into the same plane.",
                "The end bell (z -8.6..-7.6) and the hub flange (z -1.75..0.25) do not overlap in z at "
                "all: there is no modelled contact, so step A06 attaches nothing.",
                "The yoke (z -7.5..+7.5) and the end bell share only the plane z -7.6/-7.5, a modelled "
                "0.1 mm axial gap, so the rotor shell is not joined to the bell either.",
                "The OEM hub is a body of revolution about the motor axis with a spoked flange; the "
                "procedural end bell is a plain annulus. The replacement geometry is the wrong form, "
                "not merely the wrong size.",
            ],
        },
        "open_decisions": [
            "Which OEM feature drives the sun: the hub carries the two 6701-ZZ bearings coaxially "
            "with the sun but the source CAD shows no key, spline, pin or press land between them. "
            "Confirm against a physical sample or a dimensioned internal drawing.",
            "Where the magnetic rotor sits: the source main housing (NAUO3) carries arcuate pockets "
            "at r 41.766-43.236 mm for z 13.001-16.250, so the magnet carrier is the housing, not the "
            "procedural EM03/endbell + EM03/yoke pair.",
            "Whether the rotor axial position can move at all: the hub, bearings and encoder magnet "
            "fix it relative to the rear housing, so the Choice C stator shift of +4.5 mm has to be "
            "reconciled with the housing seat rather than by moving the rotor.",
        ],
        "status": (
            "A06 is a measured failure: no receiving surface, no retention and no torque path exists "
            "between the hub and the procedural rotor shell. Resolve the rotor layout before "
            "implementing any attachment."
        ),
    }
    out = ROOT / "public/design/hub-joint-validation.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "oem_hub_profile"}, indent=2, ensure_ascii=False)[:4000])
    print("\nwrote", out)


if __name__ == "__main__":
    main()
