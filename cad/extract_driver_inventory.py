"""Extract only evidence actually encoded in the manufacturer's driver STEP."""
from pathlib import Path
from collections import Counter,defaultdict
import hashlib,json,re,urllib.request,zipfile
ROOT=Path(__file__).resolve().parents[1]
URL='https://www.cubemars.com/data/cms/202604/driver-ak60-4820-1c-a2-without-capacitor.zip'
cache=ROOT/'tmp/reference';cache.mkdir(parents=True,exist_ok=True)
archive=cache/'driver.zip'
if not archive.exists():urllib.request.urlretrieve(URL,archive)
with zipfile.ZipFile(archive) as z:raw=z.read(next(n for n in z.namelist() if n.lower().endswith(('.step','.stp'))))
text=raw.decode('gb18030',errors='replace')
entities={int(k):v for k,v in re.findall(r'#(\d+)\s*=\s*(.*?);',text,re.S)}
def name(eid):
    e=entities[eid]
    if re.match(r'PRODUCT\s*\(',e):return re.search(r"'([^']*)'",e)[1]
    for n in map(int,re.findall(r'#(\d+)',e)):
        if re.match(r'PRODUCT_DEFINITION_FORMATION|PRODUCT\s*\(',entities[n]):return name(n)
    raise ValueError(f'No product name: {eid}')
children=defaultdict(list);occurrences=Counter()
for e in entities.values():
    if e.startswith('NEXT_ASSEMBLY_USAGE_OCCURRENCE'):
        refs=list(map(int,re.findall(r'#(\d+)',e)));parent,child=map(name,refs[:2]);children[parent].append(child);occurrences[child]+=1
def descendants(n,visited=None):
    visited=set() if visited is None else visited
    if n in visited:return []
    visited.add(n);result=[]
    for c in children[n]:result.append(c);result+=descendants(c,visited)
    return result
types={'R':'Resistor','C':'Capacitor','L':'Inductor','Q':'Transistor','U':'Integrated circuit','D':'Diode / LED','P':'Connector','X':'Crystal / oscillator','T':'Transformer / coupled device','TVS':'Transient suppressor','E':'Electromechanical / unresolved'}
rows=[]
for product,count in occurrences.items():
    m=re.fullmatch(r'(TVS|R|C|L|Q|U|D|P|X|T|E)(\d+)\.step',product)
    if not m:continue
    packages=sorted(set(n for n in descendants(product) if not n.startswith(('LOGO','Pad'))))
    rows.append(dict(reference=m[1]+m[2],category=types[m[1]],quantity=count,packageModels=packages,
        value=None,manufacturerPartNumber=None,tolerance=None,rating=None,
        evidence='Driver STEP reference designator and model label; package labels are not verified device identities',parent='E01',source=URL))
rows.sort(key=lambda r:(re.match(r'[A-Z]+',r['reference'])[0],int(re.search(r'\d+',r['reference'])[0])))
data=dict(source=URL,source_sha256=hashlib.sha256(raw).hexdigest(),retrieved='2026-09-17',
    sourceAssemblyNames=[n for n in children if 'AK-DRV' in n],referenceDesignators=len(rows),
    categoryCounts=dict(Counter(r['category'] for r in rows)),
    notes=['Package models may be generic library placeholders. No netlist, values or IC identities are established.',
      'Source filename says without capacitor; absent bulk/DC-link capacitors must be investigated separately.',
      'All items are children of purchased PCBA E01, not additional items to order with a complete board.'],components=rows)
out=ROOT/'public/data/driver-inventory.json';out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=['# Driver component inventory','',f"{len(rows)} reference designators extracted from [manufacturer driver STEP]({URL}).",'',*data['notes'],'',
 '| Ref | Category | CAD occurrences | Package model labels | Value / MPN |','|---|---|---:|---|---|']
for r in rows:lines.append(f"| {r['reference']} | {r['category']} | {r['quantity']} | {', '.join(r['packageModels']) or 'No package label recovered'} | Unknown |")
(ROOT/'docs/DRIVER-INVENTORY.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in data.items() if k!='components'},ensure_ascii=True,indent=2))
print(json.dumps(rows[:4],ensure_ascii=True))
