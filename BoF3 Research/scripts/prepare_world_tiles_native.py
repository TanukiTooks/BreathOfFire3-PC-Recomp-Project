"""Exact-image recipe for the observed AREA033 animated tile renderer."""
from pathlib import Path
import base64,csv,hashlib,json,struct,zlib
R=Path(__file__).resolve().parents[1];O=R/'coverage/world-native-investigation'
base=0x801f2c00;lo=0x801f469c;hi=0x801f4cb0
source=(O/'AREA033-section13-801F2C00.bin').read_bytes()
assert hashlib.sha256(source).hexdigest()=='2eda98a24d1638efb597d4ba3fb8dd3db65c4a7782e130d99b2cd58b2b1c07e1'
fn=next(f for f in csv.DictReader((O/'analysis-corrected/functions.tsv').open(),delimiter='\t') if int(f['address'],16)==lo)
assert int(fn['body_bytes'])==hi-lo and int(fn['min_address'],16)==lo and int(fn['max_address'],16)==hi-1
code=source[lo-base:hi-base]
assert struct.unpack_from('<II',source,lo-base-8)==(0x03e00008,0)
assert struct.unpack_from('<II',code,len(code)-8)==(0x03e00008,0)
for name in ('world-loaded','world-right','world-return','world-settled'):
 live=(O/'baseline'/f'{name}-code-801F2C00.bin').read_bytes()
 assert live[lo-base:hi-base]==code
calls=[];resumes=[];traps=[]
for i in range(0,len(code),4):
 pc=lo+i;w=struct.unpack_from('<I',code,i)[0];op=w>>26
 if op in (1,4,5,6,7):
  imm=struct.unpack('<h',struct.pack('<H',w&65535))[0];assert lo<=pc+4+imm*4<hi
 if op==2:assert lo<=((pc+4)&0xf0000000)|((w&0x3ffffff)<<2)<hi
 if op==3:
  calls.append(dict(pc=hex(pc),target=hex(((pc+4)&0xf0000000)|((w&0x3ffffff)<<2))));resumes.append(pc+8)
 if op==0 and w&63 in (8,9):assert w==0x03e00008
 if op==0 and w&63 in (12,13):traps.append(hex(pc))
entries=sorted(set([lo]+resumes))
recipe=dict(schema='psxrecomp overlay capture v2',origin='AREA033 section 13 animated map tile renderer; exact full body at four live world-map checkpoints',load_addr=hex(lo),size=len(code),guard_bytes=0,bytes_b64=base64.b64encode(code).decode(),function_entry_pcs=[hex(lo)],dispatch_entry_pcs=list(map(hex,entries)),static_dispatch_entry_pcs=list(map(hex,entries)),static_discovery_entry_pcs=[hex(lo)],executed_pcs=[],seeds=[hex(lo)],producer_ranges=[dict(start=hex(lo),end=hex(hi))],strict_producer_ranges=True)
(R/'world-tiles-native-inputs.json').write_text(json.dumps([recipe],indent=2)+'\n')
prior=json.loads((R/'startup-scenario01-events-inputs.json').read_text())
(R/'startup-world-tiles-inputs.json').write_text(json.dumps(prior+[recipe],indent=2)+'\n')
(O/'recipe.json').write_text(json.dumps(dict(entry=hex(lo),end=hex(hi),bytes=len(code),sha256=hashlib.sha256(code).hexdigest(),crc32=hex(zlib.crc32(code)),calls=calls,dispatch_entries=list(map(hex,entries)),trap_pcs=traps),indent=2))
print('Verified AREA033 tile renderer:',len(code),'bytes;',len(entries),'dispatch entries; traps',traps)
