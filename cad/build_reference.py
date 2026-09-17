"""Fetch CubeMars' reference assembly and generate a named, metre-unit GLB.

This is a reference conversion, not a new manufacturing design. Vendor geometry
and names remain CubeMars material. Internal omissions are documented separately.
"""
from pathlib import Path
import hashlib, io, json, re, urllib.request, zipfile
import cadquery as cq
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://www.cubemars.com/data/cms/202602/ak80-9-v3-0-robotic-actuator-3d-drawing.zip'
CACHE = ROOT / 'tmp/reference'
OUT = ROOT / 'public/models'
CACHE.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
archive = CACHE / 'ak80-9.zip'
if not archive.exists():
    urllib.request.urlretrieve(URL, archive)
with zipfile.ZipFile(archive) as z:
    step_name = next(n for n in z.namelist() if n.lower().endswith(('.step', '.stp')))
    raw = z.read(step_name)
step = CACHE / 'reference.step'
step.write_bytes(raw)

# Recover original GB18030 product labels via the STEP entity graph. OCC's
# automatic text decoding corrupts these legacy labels; occurrence IDs survive.
text = raw.decode('gb18030', errors='replace')
entities = {int(k): v for k, v in re.findall(r'#(\d+)\s*=\s*(.*?);', text, re.S)}
def product_name(entity_id):
    e = entities[entity_id]
    if e.startswith('PRODUCT '):
        return re.search(r"'([^']*)'", e)[1]
    refs = [int(n) for n in re.findall(r'#(\d+)', e)]
    for n in refs:
        if entities[n].startswith(('PRODUCT_DEFINITION_FORMATION', 'PRODUCT ')):
            return product_name(n)
    raise ValueError(f'No product name for #{entity_id}')

occurrences = {}
for eid, e in entities.items():
    if e.startswith('NEXT_ASSEMBLY_USAGE_OCCURRENCE'):
        name = re.search(r"'(NAUO\d+)'", e)[1]
        refs = [int(n) for n in re.findall(r'#(\d+)', e)]
        occurrences[name] = product_name(refs[1])

assembly = cq.Assembly.importStep(str(step))
parts = []
for shape, path, loc, color in assembly:
    name = path.split('/')[-1]
    world = shape.moved(loc)
    b = world.BoundingBox()
    parts.append((name, world, [b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]))
mins = np.min([p[2][:3] for p in parts], axis=0)
maxs = np.max([p[2][3:] for p in parts], axis=0)
center = (mins + maxs) / 2

def classify(name):
    n=int(name.replace('NAUO',''))
    if n==3: return 'M01', 'Main housing', '#303b49', 'Structure', 0
    if n==4: return 'M02', 'Rear housing', '#465363', 'Structure', -0.035
    if 5<=n<=28: return 'F01', 'M2.5 x 6 countersunk screw', '#a9b4c2', 'Fasteners', (0.05 if n==7 or n>=22 else -0.065)
    if 29<=n<=34: return 'F02', 'M2 x 12 screw', '#a9b4c2', 'Fasteners', -0.095
    return {
        35:('E01','Driver board assembly','#276f63','Electronics',-0.075),
        36:('M03','Driver cover','#303b49','Structure',-0.11),
        37:('G01','Output carrier','#c0c9d4','Transmission',0.055),
        38:('B01','625-ZZ bearing','#94a3b8','Bearings',0.034),
        39:('B02','6707-ZZ bearing','#94a3b8','Bearings',0.035),
        40:('M04','Closure cover','#68798b','Transmission',0.075),
        41:('G02','Sun gear / input shaft','#d6a75e','Transmission',0.013),
        42:('B03','6701-ZZ bearing','#94a3b8','Bearings',-0.025),
        43:('B03','6701-ZZ bearing','#94a3b8','Bearings',0.022),
        44:('E02','Encoder target magnet','#bc7860','Electronics',-0.045),
        45:('G03','Input shaft hub','#b7c2ce','Transmission',0.03),
    }[n]

scene = trimesh.Scene()
manifest=[]
for name, shape, box in parts:
    bom_id, label, color, group, explode = classify(name)
    vertices, faces = shape.tessellate(0.025, 0.06)
    verts = (np.array([v.toTuple() for v in vertices]) - center) / 1000
    mesh = trimesh.Trimesh(vertices=verts, faces=np.array(faces), process=False)
    rgb=[int(color[i:i+2],16) for i in (1,3,5)]
    mesh.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
        name=bom_id, baseColorFactor=rgb+[255], metallicFactor=0.7 if group!='Electronics' else 0.15,
        roughnessFactor=0.36))
    mesh.metadata={'bomId':bom_id, 'occurrence':name, 'source':'CubeMars STEP', 'status':'reference'}
    scene.add_geometry(mesh, node_name=name, geom_name=name)
    lo=(np.array(box[:3])-center); hi=np.array(box[3:])-center
    manifest.append(dict(id=name,bomId=bom_id,name=label,sourceName=occurrences[name],
        group=group,color=color,explode=explode,dimensions_mm=[round(v,4) for v in hi-lo],
        bounds_mm=[*[round(v,4) for v in lo],*[round(v,4) for v in hi]],
        volume_mm3=round(shape.Volume(),4),solids=len(shape.Solids())))
scene.export(OUT/'ak80-9-reference.glb')
result=dict(model='AK80-9 V3.0 KV100',kind='manufacturer-reference',units='m',
    source=URL,source_sha256=hashlib.sha256(raw).hexdigest(),source_step_date='2025-03-05',
    source_download_listing_date='2026-02-05',retrieved='2026-09-17',
    envelope_mm=[round(v,4) for v in maxs-mins],center_original_mm=center.tolist(),
    mesh_count=len(manifest),solid_count=sum(p['solids'] for p in manifest),parts=manifest)
(OUT/'manifest.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='parts'},indent=2))
print(json.dumps([dict(id=p['id'],bom=p['bomId'],source=p['sourceName'],size=p['dimensions_mm'])
    for p in manifest if p['id'] not in [f'NAUO{i}' for i in range(6,35)]],ensure_ascii=True))
