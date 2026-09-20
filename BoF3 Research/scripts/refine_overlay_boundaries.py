from pathlib import Path
import struct,csv,json
R=Path(__file__).resolve().parents[1]
for name,base,file in [('GAME',0x80195800,'GAME-section-00-80195800.bin'),('STATUS',0x801d0c00,'STATUS-section-00-801D0C00.bin')]:
 r=R/'coverage/identification'/name;b=(R/'coverage/ghidra-input'/file).read_bytes();w=struct.unpack('<'+str(len(b)//4)+'I',b[:len(b)//4*4]);pointers={}
 for i,x in enumerate(w):pointers.setdefault(x,[]).append(base+i*4)
 refs=list(csv.DictReader((r/'references.tsv').open(),delimiter='\t'));calls={int(x['to'],16) for x in refs if 'CALL' in x['type'] and x['to'].isalnum()};fixes=[]
 for f in csv.DictReader((r/'functions.tsv').open(),delimiter='\t'):
  a=int(f['address'],16);o=(a-base)//4
  if not(0<=o<len(w)) or w[o]>>16!=0x27bd:continue
  for k in range(o-1,max(-1,o-9),-1):
   x=w[k]
   if x==0x03e00008:
    start=k+2
    while start<o and w[start]==0:start+=1
    pc=base+start*4
    if start<o and (pc in pointers or pc in calls):fixes.append({'old':f'{a:08X}','new':f'{pc:08X}','evidence':'Prefix follows previous jr ra plus delay slot, has no intervening control transfer, and is a pointer/call target.','direct_call_target':pc in calls,'pointer_locations':[f'0x{p:08X}' for p in pointers.get(pc,[])]})
    break
   if x>>26 in (1,2,3,4,5,6,7) or (x>>26==0 and x&63 in (8,9)):break
 (r/'boundary-refinements.json').write_text(json.dumps(fixes,indent=2)+'\n')
 (r/'boundary-refinements.tsv').write_text(''.join(x['old']+'\t'+x['new']+'\n' for x in fixes))
 print(name,len(fixes),'supported prefix corrections')
