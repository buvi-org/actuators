"""Audit rotating end-bell clearance in nominal assembled coordinates (mm)."""
from pathlib import Path
import cadquery as cq
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
m=json.loads((ROOT/'public/models/manifest.json').read_text(encoding='utf-8'))
source=ROOT/'tmp/reference/reference.step'
assert hashlib.sha256(source.read_bytes()).hexdigest()==m['source_sha256']
a=cq.Assembly.importStep(str(source))
rear=next(s.moved(l) for s,n,l,c in a if n.split('/')[-1]=='NAUO4').translate(-cq.Vector(*m['center_original_mm']))
def ring(ri,ro,z,h):return cq.Solid.makeCylinder(ro,h,cq.Vector(0,0,z)).cut(cq.Solid.makeCylinder(ri,h,cq.Vector(0,0,z)))
endbell=ring(23,45.5,-8.6,1)
volume=endbell.intersect(rear).Volume()
# Full annular bell already represents its 360-degree swept volume.
swept_rear=rear.intersect(ring(23,45.5,-20,30))
rear_limit=swept_rear.BoundingBox().zmax
clearance=.25
trial_shift=4.1
shifted=rear.translate((0,0,-trial_shift))
assert endbell.intersect(shifted).Volume()<1e-6
report={'source_sha256':m['source_sha256'],'rear_housing':'NAUO4','end_bell':'EM03/endbell','assembled_end_bell_z_mm':[-8.6,-7.6],'end_bell_radii_mm':[23,45.5],'overlap_mm3':round(volume,6),'rear_obstruction_forward_limit_mm':round(rear_limit,6),'candidate_running_clearance_mm':clearance,'forward_moved_bell_required_z_mm':[round(rear_limit+clearance,6),round(rear_limit+clearance+1,6)],'current_stator_rear_z_mm':-6.936,'current_winding_rear_z_mm':-7.8,'rearward_housing_translation_candidate_mm':trial_shift,'translated_housing_endbell_overlap_mm3':round(endbell.intersect(shifted).Volume(),6),'translated_housing_endbell_min_distance_mm':round(endbell.distance(shifted),6),'candidate_translation_scope':'Clearance study only. Not an implemented assembly: housing joint, bearings, hub and electronics alignment need coordinated redesign.','status':'Unresolved axial layout. Preserve motor stack or external envelope before choosing correction.'}
(ROOT/'public/design/rotor-clearance-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
