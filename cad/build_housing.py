"""Extend sixteen screw supports to the housing pocket floor.
Original reference remains unchanged. Units: STEP mm, GLB m.
"""
from pathlib import Path
import json, hashlib
import cadquery as cq
import numpy as np
import trimesh
from OCP.BRepAdaptor import BRepAdaptor_Surface
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'public/models/manifest.json').read_text(encoding='utf-8'))
source=ROOT/'tmp/reference/reference.step'
assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest['source_sha256']
a=cq.Assembly.importStep(str(source))
s=next(shape.moved(loc) for shape,name,loc,color in a if name.split('/')[-1]=='NAUO3')
s=s.translate(-cq.Vector(*manifest['center_original_mm']))
# Locate the sixteen source screw axes. Extend 5 mm diameter pads to the floor.
bores={}
for face in s.Faces():
 if face.geomType()!='CYLINDER':continue
 c=BRepAdaptor_Surface(face.wrapped).Cylinder();p=c.Axis().Location();d=c.Axis().Direction()
 if abs(c.Radius()-1.025)<1e-5 and abs(d.Z())>.99:
  bores[(round(p.X(),5),round(p.Y(),5))]=True
assert len(bores)==16
supports=[]
for x,y in bores:
 support=cq.Solid.makeCylinder(2.5,20,cq.Vector(x,y,-4.75))
 # Clearance mask only affects added material; original blind bores remain intact.
 support=support.cut(cq.Solid.makeCylinder(1.05,7.51,cq.Vector(x,y,-4.76)))
 supports.append(support)
prism=supports[0].fuse(*supports[1:])
modified=s.fuse(prism,tol=1e-5)
added=modified.cut(s,tol=1e-5)
assert modified.isValid() and len(modified.Solids())==1
assert added.isValid() and added.Volume()>0
assert abs(modified.Volume()-s.Volume()-added.Volume())<.1
removed=s.cut(modified,tol=1e-5).Volume()
assert abs(removed)<.01
# Collision check against current illustrative yoke: radii 42.5..45.5, z -7.5..7.5 mm.
yoke=cq.Solid.makeCylinder(45.5,15,cq.Vector(0,0,-7.5)).cut(cq.Solid.makeCylinder(42.5,15,cq.Vector(0,0,-7.5)))
clash=added.intersect(yoke).Volume()
out=ROOT/'public/design';out.mkdir(exist_ok=True)
cq.exporters.export(modified,str(out/'main-housing-supported.step'))
verts,faces=added.tessellate(.025,.06)
mesh=trimesh.Trimesh(vertices=np.array([v.toTuple() for v in verts])/1000,faces=np.array(faces),process=False)
scene=trimesh.Scene();scene.add_geometry(mesh,node_name='M01/boss-extensions');scene.export(out/'housing-boss-extensions.glb')
report={'revision':'Primeform housing study R1','source_sha256':manifest['source_sha256'],'source_occurrence':'NAUO3','rear_seat_z_mm':-4.75,'floor_target_z_mm':15.25,'screw_bores_preserved':16,'support_diameter_mm':5,'added_volume_mm3':round(added.Volume(),3),'modified_valid':modified.isValid(),'modified_solid_count':len(modified.Solids()),'original_material_removed_mm3':round(removed,6),'added_support_overlap_with_provisional_rotor_yoke_mm3':round(clash,3),'release':'Study only: rotor envelope interference must be resolved; cutter access, fillets and tolerances not released.'}
(out/'housing-study.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
