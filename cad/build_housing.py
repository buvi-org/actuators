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
# Choice C housing-owned axial seat contacts stator back iron, not winding ends.
# Rotor axial correction: the rotor's axial position is fixed by real OEM features (the
# measured hub at z -1.75..+0.25, both 6701-ZZ bearings and the encoder magnet), so the
# Choice C +4.5 mm stator shift was the error and the seat moves 4.5 mm rearward with the
# stator, winding and ring flange. See docs/ROTOR-HUB-JOINT.md.
SHIFT=-4.5
SEAT_Z=11.436+SHIFT
seat=cq.Solid.makeCylinder(33.5,15.25-SEAT_Z,cq.Vector(0,0,SEAT_Z)).cut(cq.Solid.makeCylinder(30.1,15.25-SEAT_Z,cq.Vector(0,0,SEAT_Z)))
modified=s.fuse(prism,seat,tol=1e-5)
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
# Seat-only checks: full annular steel/winding envelopes are conservative.
def annulus(ri,ro,z0,z1):
 return cq.Solid.makeCylinder(ro,z1-z0,cq.Vector(0,0,z0)).cut(cq.Solid.makeCylinder(ri,z1-z0,cq.Vector(0,0,z0)))
seat_checks={}
for name,body in [('stator',annulus(30,40,-2.436+SHIFT,11.436+SHIFT)),('windings',annulus(34.5,39,-3.3+SHIFT,12.3+SHIFT)),('ring_envelope',annulus(24.9,29.98,5.75+SHIFT,13.25+SHIFT))]:
 overlap=abs(seat.intersect(body).Volume());seat_checks[name]=overlap
 assert overlap<.01,(name,overlap)
assert abs(modified.BoundingBox().zmax-s.BoundingBox().zmax)<1e-5
report={'stator_seat_z_mm':SEAT_Z,'seat_radii_mm':[30.1,33.5],'seat_overlap_mm3':seat_checks,'revision':'Primeform housing study R3 / stator seat realigned 4.5 mm rearward with the rotor','source_sha256':manifest['source_sha256'],'source_occurrence':'NAUO3','rear_seat_z_mm':-4.75,'floor_target_z_mm':15.25,'screw_bores_preserved':16,'support_diameter_mm':5,'added_volume_mm3':round(added.Volume(),3),'modified_valid':modified.isValid(),'modified_solid_count':len(modified.Solids()),'original_material_removed_mm3':round(removed,6),'added_support_overlap_with_provisional_rotor_yoke_mm3':round(clash,3),'release':'Study only: rotor radial envelope and the hub-to-shell connection remain unresolved; cutter access, fillets and tolerances not released.'}
(out/'housing-study.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
