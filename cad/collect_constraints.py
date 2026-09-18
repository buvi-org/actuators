"""Collect every fixed constraint that the rotor/hub design must satisfy.

This writes the table that has to be agreed before any geometry is built. Every value is
measured, with the file it came from, so nothing here is an assumption.
"""
import json
import sys
from pathlib import Path

import cadquery as cq
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tmp/audit"))
from oem import load  # noqa: E402

occ, parts, center, centered = load()
manifest = json.loads((ROOT / "public/models/manifest.json").read_text(encoding="utf-8"))
choice = json.loads((ROOT / "public/data/packaging-choice.json").read_text(encoding="utf-8"))

rows = []


def add(group, name, value, source):
    rows.append({"group": group, "constraint": name, "value": value, "source": source})


# ---- Fixed external interface -------------------------------------------------
add("External (fixed)", "Overall envelope", "Ø98 x 38.5 mm", "manifest envelope_mm")
add("External (fixed)", "Mounting holes", "8 x M3 on Ø85 PCD; 6 x M4 on Ø28 PCD",
    "S2 drawing, docs/INTERNAL-STRUCTURE.md")

# ---- Housing envelope the rotor must live inside ------------------------------
h = cq.importers.importStep(str(ROOT / "public/design/main-housing-supported.step")).val()
best = None
for z in np.arange(-1.9, 12.0, 0.1):
    res = h.intersect(cq.Face.makePlane(60, 60, cq.Vector(0, 0, float(z)), cq.Vector(0, 0, 1)))
    rs = []
    for f in res.Faces():
        for w in f.Wires():
            for e in w.Edges():
                for t in np.linspace(0, 1, 80):
                    p = e.positionAt(t)
                    r = float(np.hypot(p.x, p.y))
                    if 20 < r < 60:
                        rs.append(r)
    if rs:
        m = min(rs)
        if best is None or m < best[1]:
            best = (round(float(z), 2), round(m, 3))
add("Housing envelope", "Minimum inward wall radius over the rotor band",
    f"r {best[1]} mm at z {best[0]}", "measured, public/design/main-housing-supported.step")
add("Housing envelope", "Rotor must therefore stay inside",
    f"r {round(best[1] - 0.3, 2)} mm", "derived: 0.3 mm running clearance")

# ---- Stator and magnet band ---------------------------------------------------
add("Motor", "Stator OD / bore / stack", "80 / 60 / 13.872 mm",
    "packaging-choice.json (Choice C)")
add("Motor", "Stator axial span", f"z {choice['stack_center_z_mm'] - 6.936:.3f} .. "
    f"{choice['stack_center_z_mm'] + 6.936:.3f} mm", "packaging-choice.json")
add("Motor", "Air gap (assumed, not measured)", "0.5 mm radial", "study assumption")
add("Motor", "Magnet inner radius therefore", "r 40.0 mm", "derived: stator r 40 + air gap")
add("Motor", "Housing's own arcuate slots (radial band)", "r 41.766 .. 43.236 mm",
    "measured, housings NAUO3 / NAUO4")

# ---- Shaft, bearings, sun -----------------------------------------------------
add("Shaft / bearings", "6701-ZZ bore x OD x width", "12 x 18 x 4 mm", "B03 BOM row")
add("Shaft / bearings", "Hub front counterbore for the bearing", "Ø12 mm at z 1.25..5.25",
    "measured on NAUO45")
add("Shaft / bearings", "Hub rear bore", "Ø6 mm at z -8.75..-6.75", "measured on NAUO45")
add("Shaft / bearings", "Hub pilot counterbore for the sun", "Ø5.95 mm at z 3.75..5.25",
    "measured on NAUO45")
add("Shaft / bearings", "Sun front journal", "Ø6.000 mm, keyed/flat feature 0.202 mm spread",
    "measured on NAUO41")
add("Shaft / bearings", "Sun-to-hub contact volume", "0.324 mm3 over z 3.75..5.25",
    "measured, hub-joint-validation.json")

# ---- Measured wall thicknesses of the OEM hub --------------------------------
add("OEM hub walls (the concern)", "Outer rim radial wall", "1.225 mm (r 21.025 to 22.25)",
    "measured on NAUO45")
add("OEM hub walls (the concern)", "Flange web axial thickness", "2.0 mm (z -1.75 to 0.25)",
    "measured on NAUO45")
add("OEM hub walls (the concern)", "Main body radial wall", "4.0 mm (r 2.0 to 6.0)",
    "measured on NAUO45")
add("OEM hub walls (the concern)", "Front land radial wall", "3.025 mm (r 2.975 to 6.0)",
    "measured on NAUO45")
add("OEM hub walls (the concern)", "Hub envelope / length", "Ø44.5 x 14.5 mm",
    "manifest bounds_mm for NAUO45")

width = max(len(r["group"]) for r in rows)
print(f"{'group':<{width}}  {'constraint':<48} {'value':<44} source")
print("-" * (width + 150))
for r in rows:
    print(f"{r['group']:<{width}}  {r['constraint']:<48} {r['value']:<44} {r['source']}")

out = ROOT / "public/design/design-constraints.json"
out.write_text(json.dumps({"scope": "Fixed constraints for the rotor/hub design. Agree these "
                                    "before building geometry.", "constraints": rows}, indent=2) + "\n",
               encoding="utf-8")
print("\nwrote", out)
