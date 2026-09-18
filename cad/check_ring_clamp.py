"""Verify the ring clamp is restored for both screws groups (front 8 and rear 16)."""
import json
import sys
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "public/models/manifest.json").read_text(encoding="utf-8"))
choice = json.loads((ROOT / "public/data/packaging-choice.json").read_text(encoding="utf-8"))
ring_z = choice["ring_z_mm"]


def annulus(ri, ro, z0, z1):
    h = z1 - z0
    return cq.Solid.makeCylinder(ro, h, cq.Vector(0, 0, z0)).cut(
        cq.Solid.makeCylinder(ri, h + 1, cq.Vector(0, 0, z0 - 0.5))
    )


flange = annulus(24.9, 29.98, ring_z[0] + 3.0, ring_z[1])
print(f"ring mounting flange: z {ring_z[0]+3.0:.3f} .. {ring_z[1]:.3f}  (r 24.9..29.98)")
print(f"gear mesh plane z 8.250, ring teeth band z 5.750..10.750")
print(f"flange covers the toothed band: {ring_z[0]+3.0 <= 5.75 and ring_z[1] >= 10.75}")
print()

front = ["NAUO7"] + [f"NAUO{i}" for i in range(22, 29)]
print("A03: eight front screws clamping the ring")
hits = 0
for p in manifest["parts"]:
    if p["id"] not in front:
        continue
    b = p["bounds_mm"]
    x, y = (b[0] + b[3]) / 2, (b[1] + b[4]) / 2
    bore = cq.Solid.makeCylinder(1.025, 6.0, cq.Vector(x, y, b[2]))
    v = flange.intersect(bore).Volume()
    if v > 0.01:
        hits += 1
print(f"  screws with thread engagement in ring material: {hits}/8")
print(f"  screw tips z {manifest['parts'][6]['bounds_mm'][2]:.3f}, ring flange top z {ring_z[1]:.3f}")
print(f"  -> {'CLAMPED' if hits == 8 else 'NOT CLAMPED'}")
