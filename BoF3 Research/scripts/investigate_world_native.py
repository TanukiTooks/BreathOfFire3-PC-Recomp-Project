"""Rank current world-route fallback and identify its disc section by live bytes."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];O=R/'coverage/world-native-investigation';D=O/'baseline'
sections=json.loads((R/'coverage/emi-sections.json').read_text())
files={f['path']:f for f in json.loads((R/'coverage/disc-inventory.json').read_text())}
def snapshot(name):return json.loads((D/(name+'.json')).read_text())
a=snapshot('camp-settled');b=snapshot('world-settled')
old={r['pc']:r['insns'] for r in a['dirty']['per_pc']}
rank=sorted([dict(r,delta_insns=r['insns']-old.get(r['pc'],0)) for r in b['dirty']['per_pc']],key=lambda r:-r['delta_insns'])
live=(D/'world-settled-code-801F2C00.bin').read_bytes();pc=int(rank[0]['pc'],16)|0x80000000
matches=[]
with (R.parent/'iso/Breath of Fire III (USA)/Breath of Fire III (USA) (Track 1).bin').open('rb') as disc:
 def read_at(file,offset,size):
  data=bytearray()
  while size:
   sector,within=divmod(offset,2048);count=min(size,2048-within)
   disc.seek((file['lba']+sector)*2352+24+within);data.extend(disc.read(count));offset+=count;size-=count
  return bytes(data)
 for s in sections:
  base=int(s['destination_field'],16)
  if s['type_low16']!=0 or not(base<=pc and pc+64<=base+s['size']):continue
  data=read_at(files[s['file']],s['file_offset']+pc-base,64)
  if data!=live[pc-0x801f2c00:pc-0x801f2c00+64]:continue
  full=read_at(files[s['file']],s['file_offset'],s['size']);assert hashlib.sha256(full).hexdigest()==s['sha256']
  lo=max(base,0x801f2c00);hi=min(base+len(full),0x80200000)
  match=dict(s,overlap_bytes=hi-lo,overlap_exact=full[lo-base:hi-base]==live[lo-0x801f2c00:hi-0x801f2c00])
  name=f"{Path(s['file']).stem}-section{s['index']:02}-{base:08X}.bin";(O/name).write_bytes(full);match['extracted']=name;matches.append(match)
result=dict(camp_frame=a['frame'],world_frame=b['frame'],total_delta=b['dirty']['insns_run']-a['dirty']['insns_run'],top=rank[:25],matches=matches)
(O/'selection.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
