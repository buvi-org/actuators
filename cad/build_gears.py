"""Provisional gear topology: one connected solid per physical gear, mm units.
Tooth counts and polygonal, non-involute flanks are illustrative, not OEM geometry.
"""
from pathlib import Path
import json, math
import cadquery as cq
import numpy as np
import trimesh
import hashlib
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'public/design'
def points(teeth,pitch_radius,internal=False):
 result=[]
 for i in range(teeth*4):
  angle=2*math.pi*i/(teeth*4)
  radius=(23.4 if i%4 in (1,2) else 24.6) if internal else pitch_radius+(2*pitch_radius/teeth)*(1 if i%4 in (1,2) else -1.15)
  result.append([radius*math.cos(angle),radius*math.sin(angle)])
 return result
profiles={'sun':points(12,3),'planet':points(42,10.5),'ring':points(96,24,True)}
(ROOT/'src/gear-profiles.json').write_text(json.dumps(profiles,separators=(',',':'))+'\n')
def wire(pts):return cq.Workplane('XY').polyline(pts).close().wire().val()
def external(pts,bore):
 face=cq.Face.makeFromWires(wire(pts),[cq.Workplane('XY').circle(bore).wire().val()])
 return cq.Solid.extrudeLinear(face,cq.Vector(0,0,5)).translate((0,0,-2.5))
# Preserve source shaft ends and replace the entire central blank/spline region.
manifest=json.loads((ROOT/'public/models/manifest.json').read_text(encoding='utf-8'))
source=ROOT/'tmp/reference/reference.step'
assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest['source_sha256']
reference=cq.Assembly.importStep(str(source))
shaft=next(s.moved(loc) for s,name,loc,c in reference if name.split('/')[-1]=='NAUO41')
shaft=shaft.translate(-cq.Vector(*manifest['center_original_mm']))
ends=shaft.cut(cq.Solid.makeBox(20,20,7.5,cq.Vector(-10,-10,3.75)))
toothed=cq.Solid.extrudeLinear(wire(profiles['sun']),[],cq.Vector(0,0,7.5)).translate((0,0,3.75))
sun=ends.fuse(toothed).clean().translate((0,0,-8.25))
assert sun.isValid() and len(sun.Solids())==1
vertices,faces=sun.tessellate(.015,.04)
mesh=trimesh.Trimesh(vertices=np.array([v.toTuple() for v in vertices])/1000,faces=np.array(faces),process=False)
scene=trimesh.Scene();scene.add_geometry(mesh,node_name='G02');scene.export(OUT/'provisional-sun-gear.glb')
planet=external(profiles['planet'],3)
face=cq.Face.makeFromWires(cq.Workplane('XY').circle(26).wire().val(),[wire(profiles['ring'])])
ring=cq.Solid.extrudeLinear(face,cq.Vector(0,0,5)).translate((0,0,-2.5))
report={}
for name,solid in [('sun',sun),('planet',planet),('ring',ring)]:
 assert solid.isValid() and len(solid.Solids())==1
 path=OUT/f'provisional-{name}-gear.step';cq.exporters.export(solid,str(path))
 restored=cq.importers.importStep(str(path)).val()
 assert restored.isValid() and len(restored.Solids())==1
 assert abs(restored.Volume()-solid.Volume())<.001
 report[name]={'solid_count':1,'step_roundtrip_valid':True,'volume_mm3':round(solid.Volume(),4)}
a=cq.Assembly(name='Provisional_planetary_gears')
a.add(sun,name='Sun_gear',loc=cq.Location(cq.Vector(0,0,8.25)))
a.add(ring,name='Ring_gear',loc=cq.Location(cq.Vector(0,0,8.25)))
for i in range(3):
 angle=i*2*math.pi/3
 part=planet.rotate((0,0,0),(0,0,1),math.degrees(angle+math.pi-.375*2*math.pi/42))
 a.add(part,name=f'Planet_gear_{i+1}',loc=cq.Location(cq.Vector(13.5*math.cos(angle),13.5*math.sin(angle),8.25)))
a.export(str(OUT/'provisional-gear-train.step'))
restored=cq.Assembly.importStep(str(OUT/'provisional-gear-train.step'))
leaves=list(restored)
assert len(leaves)==5 and all(s.isValid() and len(s.Solids())==1 for s,_,_,_ in leaves)
report['assembly']={'components':5,'solids':5,'tooth_components':0,'status':'Illustrative non-involute geometry; not production-ready'}
(OUT/'gear-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
