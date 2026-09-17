"""Original provisional sheet/stack CAD. Input: downloaded study JSON or defaults.

Run: python cad/build_lamination.py [path/to/lamination-study.json]
Uses polygon profile points shared with the browser, never an invented OEM profile.
"""
from pathlib import Path
import json, sys
import cadquery as cq

ROOT=Path(__file__).resolve().parents[1]
source=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'public/design/lamination-study.json'
d=json.loads(source.read_text(encoding='utf-8'))
if d.get('kind')!='provisional-lamination-study': raise ValueError('Expected lamination study JSON')
p=d['parameters'];n=d['results']['count'];t=p['steel'];c=p['coating']/1000;g=p['gap']/1000
if not isinstance(n,int) or not 1<=n<=500 or t<=0 or c<0 or g<0: raise ValueError('Invalid sheet count/thickness')
gross=n*(t+2*c)+(n-1)*g
if abs(gross-d['results']['gross'])>1e-8: raise ValueError('Derived stack height inconsistent with inputs')
outer=cq.Workplane('XY').polyline([tuple(v) for v in d['profile']['outer']]).close().wire().val()
hole=cq.Workplane('XY').circle(p['bore']/2).wire().val()
face=cq.Face.makeFromWires(outer,[hole])
sheet=cq.Solid.extrudeLinear(face,cq.Vector(0,0,t))
if not sheet.isValid(): raise ValueError('Invalid lamination solid')
out=ROOT/'public/design';out.mkdir(parents=True,exist_ok=True)
cq.exporters.export(sheet,str(out/'provisional-single-lamination.step'))
assembly=cq.Assembly(name='Primeform_provisional_lamination_stack')
coating=cq.Solid.extrudeLinear(face,cq.Vector(0,0,c)) if c else None
for i in range(n):
    z=i*(t+2*c+g)-gross/2
    assembly.add(sheet,name=f'L{i+1:03d}_steel',loc=cq.Location(cq.Vector(0,0,z+c)),color=cq.Color(.45,.52,.6))
    if coating:
        for side,offset in [('lower',0),('upper',c+t)]:
            assembly.add(coating,name=f'L{i+1:03d}_coating_{side}',loc=cq.Location(cq.Vector(0,0,z+offset)),color=cq.Color(.32,.68,.54))
assembly.export(str(out/'provisional-lamination-stack.step'))
report=dict(sheetCount=n,coatingFaceCount=2*n if c else 0,sheetValid=sheet.isValid(),
    sheetVolume_mm3=sheet.Volume(),profileArea_mm2=face.Area(),grossStack_mm=gross,
    solidCount=len(assembly.toCompound().Solids()),source=str(source.name))
(out/'cad-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
