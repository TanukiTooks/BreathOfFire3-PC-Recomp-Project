from pathlib import Path
import struct,json,re,base64
R=Path(__file__).resolve().parents[1]; O=R/'coverage/identification'
captures=json.loads((R/'startup-card-overlay-captures.json').read_text())
for name,base,filename in [('GAME',0x80195800,'GAME-section-00-80195800.bin'),('STATUS',0x801d0c00,'STATUS-section-00-801D0C00.bin')]:
 b=(R/'coverage/ghidra-input'/filename).read_bytes();seeds={};executed=set();dispatch=set()
 def add(pc,why):seeds.setdefault(pc,set()).add(why)
 for o in range(0,len(b)-32,4):
  w=struct.unpack_from('<I',b,o)[0]
  if w>>16==0x27bd and w&0x8000 and any(struct.unpack_from('<I',b,o+j)[0]>>16==0xafbf for j in range(4,32,4)):add(base+o,'stack-frame and saved return-address pattern; candidate')
 for c in captures:
  cb=base64.b64decode(c['bytes_b64']); ca=int(c['load_addr'],16)
  for field,dest in [('executed_pcs',executed),('dispatch_entry_pcs',dispatch)]:
   for p in c.get(field,[]):
    pc=int(p,16);so=pc-base;co=pc-ca
    if so>=0 and co>=0 and so+64<=len(b) and co+64<=len(cb) and b[so:so+64]==cb[co:co+64]:dest.add(pc)
 (O/name/'seeds.tsv').write_text('\n'.join(f'{pc:08X}\t'+ '; '.join(sorted(why)) for pc,why in sorted(seeds.items()))+'\n')
 (O/name/'seed-evidence.json').write_text(json.dumps({'input':filename,'base':f'0x{base:08X}','seed_count':len(seeds),'runtime_executed_matching_64_bytes':[f'0x{x:08X}' for x in sorted(executed)],'runtime_dispatch_matching_64_bytes':[f'0x{x:08X}' for x in sorted(dispatch)],'warning':'Dispatch and executed addresses are corroboration, not automatic function seeds. Prologue/table seeds remain candidates.'},indent=2)+'\n')
 print(name,len(seeds),'seeds;',len(executed),'runtime instruction PCs matched;',len(dispatch),'dispatch PCs matched')
