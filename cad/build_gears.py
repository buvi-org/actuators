"""Provisional gear topology: one connected solid per physical gear, mm units.
20/70/160 involute candidate, not an OEM reconstruction or production release.
"""
from pathlib import Path
import json, math
import cadquery as cq
import numpy as np
import trimesh
import hashlib
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'public/design'
from involute_geometry import profile,COUNTS,M,ALPHA,CENTER
geometry={name:profile(name) for name in COUNTS}

def external(outline,bore):
 face=cq.Face.makeFromWires(outline,[cq.Workplane('XY').circle(bore).wire().val()])
 return cq.Solid.extrudeLinear(face,cq.Vector(0,0,5)).translate((0,0,-2.5))
# Preserve source shaft ends and replace the entire central blank/spline region.
manifest=json.loads((ROOT/'public/models/manifest.json').read_text(encoding='utf-8'))
source=ROOT/'tmp/reference/reference.step'
assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest['source_sha256']
reference=cq.Assembly.importStep(str(source))
shaft=next(s.moved(loc) for s,name,loc,c in reference if name.split('/')[-1]=='NAUO41')
shaft=shaft.translate(-cq.Vector(*manifest['center_original_mm']))
ends=shaft.cut(cq.Solid.makeBox(20,20,7.5,cq.Vector(-10,-10,3.75)))
toothed=cq.Solid.extrudeLinear(geometry['sun'][0],[],cq.Vector(0,0,7.5)).translate((0,0,3.75))
sun=ends.fuse(toothed).clean().translate((0,0,-8.25))
assert sun.isValid() and len(sun.Solids())==1
vertices,faces=sun.tessellate(.015,.04)
mesh=trimesh.Trimesh(vertices=np.array([v.toTuple() for v in vertices])/1000,faces=np.array(faces),process=False)
scene=trimesh.Scene();scene.add_geometry(mesh,node_name='G02');scene.export(OUT/'provisional-sun-gear.glb')
planet=external(geometry['planet'][0],3)
face=cq.Face.makeFromWires(cq.Workplane('XY').circle(29.98).wire().val(),[geometry['ring'][0]])
ring=cq.Solid.extrudeLinear(face,cq.Vector(0,0,5)).translate((0,0,-2.5))
# Integral fixed-ring flange and stator carrier, in assembly coordinates.
# The gear local origin is z=8.25; rotate hole locations back by tooth phase.
phase=math.pi/160
stack_half=6.936

def annulus(ri,ro,z0,z1):
 return cq.Solid.makeCylinder(ro,z1-z0,cq.Vector(0,0,z0)).cut(cq.Solid.makeCylinder(ri,z1-z0,cq.Vector(0,0,z0)))
ring_world=ring.translate((0,0,8.25))
# Compact ring rim: no long sleeve and no stator axial shoulder.
flange=annulus(24.9,29.98,8.75,13.25)
ring_world=ring_world.fuse(flange).clean()
mount_ids=['NAUO7']+[f'NAUO{i}' for i in range(22,29)]
bolt_centres=[]
for part in manifest['parts']:
 if part['id'] not in mount_ids:continue
 bounds=part['bounds_mm'];x=(bounds[0]+bounds[3])/2;y=(bounds[1]+bounds[4])/2
 # Source bolt coordinates are already in the assembled world frame.
 lx=x*math.cos(phase)+y*math.sin(phase);ly=-x*math.sin(phase)+y*math.cos(phase)
 ring_world=ring_world.cut(cq.Solid.makeCylinder(1.025,4.52,cq.Vector(lx,ly,8.74)))
 bolt_centres.append({'instance':part['id'],'x_mm':x,'y_mm':y,'pcd_mm':2*math.hypot(x,y),'screw_tip_z_mm':bounds[2],'nominal_engagement_mm':13.25-bounds[2]})
assert len(bolt_centres)==8
ring=ring_world.clean().translate((0,0,-8.25))
mounted=ring_world.rotate((0,0,0),(0,0,1),math.degrees(phase))
# Compare against source stationary and rotating bodies plus stator/coil envelopes.
clashes={}
for shape,name,loc,color in reference:
 id=name.split('/')[-1]
 if id not in ['NAUO3','NAUO4','NAUO37','NAUO38','NAUO39','NAUO45']:continue
 body=shape.moved(loc).translate(-cq.Vector(*manifest['center_original_mm']))
 overlap=mounted.intersect(body,tol=1e-6).Volume()
 clashes[id]=round(abs(overlap),6)

 if abs(overlap)>=.01:
  bb=mounted.intersect(body,tol=1e-6).BoundingBox(); print('CLASH',id,overlap,[bb.xmin,bb.ymin,bb.zmin,bb.xmax,bb.ymax,bb.zmax],flush=True)
 assert abs(overlap)<.01,(id,overlap)
stator=annulus(30,40,-stack_half+4.5,stack_half+4.5)
coil=annulus(34.5,39,-3.3,12.3)
for name,body in [('stator_envelope',stator),('winding_envelope',coil)]:
 overlap=mounted.intersect(body,tol=1e-6).Volume();clashes[name]=round(abs(overlap),6)
 assert abs(overlap)<.01,(name,overlap)
# Every mounting bore must be clear through the flange on the actual screw axis.
for b in bolt_centres:
 probe=cq.Solid.makeCylinder(1,4.48,cq.Vector(b['x_mm'],b['y_mm'],8.76))
 assert mounted.intersect(probe).Volume()<.001
mounting={'design':'Choice C: compact ring OD locates stator radially; main housing shoulder locates it axially','bolt_circle_mm':54,'screws':bolt_centres,'thread_callout':'8 x M2.5 x 0.45; pilot cylinders only; thread capacity pending','ring_od_mm':59.96,'ring_z_mm':[5.75,13.25],'stator_bore_mm':60,'slot_root_diameter_mm':68,'stator_back_iron_mm':4,'stator_z_mm':[-2.436,11.436],'stator_seat_z_mm':11.436,'radial_bond_gap_mm':.02,'locating_overlap_z_mm':[5.75,11.436],'locating_length_mm':5.686,'thread_outer_edge_material_mm':1.73,'source_and_envelope_overlap_mm3':clashes,'scope':'Nominal ring fit only. Housing seat checked separately. Rotor axial alignment and existing housing clashes unresolved.'}
(OUT/'stator-mount-validation.json').write_text(json.dumps(mounting,indent=2)+'\n')
report={}
for name,solid in [('sun',sun),('planet',planet),('ring',ring)]:
 assert solid.isValid() and len(solid.Solids())==1
 path=OUT/f'provisional-{name}-gear.step';cq.exporters.export(solid,str(path))
 restored=cq.importers.importStep(str(path)).val()
 assert restored.isValid() and len(restored.Solids())==1
 assert abs(restored.Volume()-solid.Volume())<.001
 vertices,faces=solid.tessellate(.002,.025)
 mesh=trimesh.Trimesh(vertices=np.array([v.toTuple() for v in vertices])/1000,faces=np.array(faces),process=False)
 scene=trimesh.Scene();scene.add_geometry(mesh,node_name=name);scene.export(OUT/f'provisional-{name}-gear.glb')
 report[name]={**geometry[name][2],'solid_count':1,'step_roundtrip_valid':True,'volume_mm3':round(solid.Volume(),4)}
a=cq.Assembly(name='Provisional_planetary_gears')
a.add(sun,name='Sun_gear',loc=cq.Location(cq.Vector(0,0,8.25)))
a.add(ring.rotate((0,0,0),(0,0,1),180/160),name='Ring_gear',loc=cq.Location(cq.Vector(0,0,8.25)))
for i in range(3):
 angle=i*2*math.pi/3
 part=planet.rotate((0,0,0),(0,0,1),math.degrees(angle+math.pi+math.pi/70+20/70*angle))
 a.add(part,name=f'Planet_gear_{i+1}',loc=cq.Location(cq.Vector(13.5*math.cos(angle),13.5*math.sin(angle),8.25)))
a.export(str(OUT/'provisional-gear-train.step'))
restored=cq.Assembly.importStep(str(OUT/'provisional-gear-train.step'))
leaves=list(restored)
assert len(leaves)==5 and all(s.isValid() and len(s.Solids())==1 for s,_,_,_ in leaves)
report['assembly']={'components':5,'solids':5,'tooth_components':0,'status':'Analytic involute candidate; manufacturing release pending process, tolerances and strength checks'}
(OUT/'gear-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
