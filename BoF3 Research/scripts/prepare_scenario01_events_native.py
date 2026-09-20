from pathlib import Path
import base64,csv,hashlib,json,struct,zlib
R=Path(__file__).resolve().parents[1];O=R/'coverage/scenario01-events-native';O.mkdir(exist_ok=True)
inputs=json.loads((R/'startup-scenario01-inputs.json').read_text(encoding='utf-8'));manifest=[]
b=(R/'coverage/party-motion-native/SCENA01-section00-801F6C00.bin').read_bytes();base=0x801f6c00
sha='289b2b95706371c76f70e49226525ef995b33b57f4a2dd653eb5678801324b48';assert hashlib.sha256(b).hexdigest()==sha
funcs={int(x['address'],16):x for x in csv.DictReader((R/'coverage/scenario01-native/SCENA01/functions.tsv').open(),delimiter='\t')}
targets=[(0x801f8ae4,0x801f8c0c,'bof3_update_scenario01_event_01'),(0x801f8c0c,0x801f8f34,'bof3_update_scenario01_event_02')]
tables=[(0x801f6c7c,12,0x801f8c3c)]
for lo,hi,name in targets:
 f=funcs[lo];assert int(f['body_bytes'])==hi-lo and int(f['min_address'],16)==lo and int(f['max_address'],16)==hi-1
 code=b[lo-base:hi-base];assert struct.unpack_from('<I',b,lo-base-8)[0]==0x03e00008
 assert struct.unpack_from('<II',code,len(code)-8)==(0x03e00008,0)
 calls=[];resumes=[];switches=[]
 if lo==0x801f8c0c:
  for addr,count,jump in tables:
   values=list(struct.unpack_from('<'+'I'*count,b,addr-base));assert all(lo<=v<hi and v%4==0 for v in values)
   switches.append(dict(address=hex(addr),count=count,jump_pc=hex(jump),targets=[hex(v) for v in values]))
 for i in range(0,len(code),4):
  pc=lo+i;w=struct.unpack_from('<I',code,i)[0];op=w>>26
  if op in (1,4,5,6,7):
   imm=struct.unpack('<h',struct.pack('<H',w&65535))[0];assert lo<=pc+4+imm*4<hi
  if op==2:assert lo<=((pc+4)&0xf0000000)|((w&0x3ffffff)<<2)<hi
  if op==3:calls.append({'pc':hex(pc),'target':hex(((pc+4)&0xf0000000)|((w&0x3ffffff)<<2))});resumes.append(pc+8)
  if op==0 and (w&63)==9:
   raise AssertionError('Unexpected JALR')
  if op==0 and (w&63)==8 and w!=0x03e00008:assert pc in [t[2] for t in tables] and w==0x00400008
  assert not (op==0 and (w&63) in (12,13)),'Unexpected trap'
 for stage in ['camp-idle','world-loaded','world-settled']:
  live=(O/'baseline'/f'{stage}-code-801F2C00.bin').read_bytes();assert live[lo-0x801f2c00:hi-0x801f2c00]==code
  for t in switches:
   a=int(t['address'],16);assert live[a-0x801f2c00:a-0x801f2c00+4*t['count']]==b[a-base:a-base+4*t['count']]
 entries=sorted(set([lo]+resumes+[int(v,16) for t in switches for v in t['targets']]))
 entries=[hex(v) for v in entries]
 inputs.append({'schema':'psxrecomp overlay capture v2','origin':f'Static recipe for {name}; SCENA01 section 0, full-body live camp/world match. Tables remain runtime reads.','load_addr':hex(lo),'size':len(code),'guard_bytes':0,'bytes_b64':base64.b64encode(code).decode(),'function_entry_pcs':[hex(lo)],'dispatch_entry_pcs':entries,'static_dispatch_entry_pcs':entries,'static_discovery_entry_pcs':[hex(lo)],'executed_pcs':[],'seeds':[hex(lo)],'producer_ranges':[{'start':hex(lo),'end':hex(hi)}],'strict_producer_ranges':True})
 manifest.append({'section':'SCENA01.EMI section 0','entry':f'0x{lo:08X}','end_exclusive':f'0x{hi:08X}','name':name,'bytes':len(code),'sha256':hashlib.sha256(code).hexdigest(),'crc32':f'0x{zlib.crc32(code):08X}','source_sha256':sha,'calls':calls,'resume_dispatch_entries':[f'0x{x:08X}' for x in resumes],'switch_tables':switches,'dispatch_entries':entries,'boundary_evidence':'Exact contiguous Ghidra extent, preceding and final return/delay slot, all direct branches internal, indirect jump destinations explicitly seeded from the source event-substate table; full source and live body equality.'})
(R/'startup-scenario01-events-inputs.json').write_text(json.dumps(inputs,indent=2)+'\n',encoding='utf-8')
(O/'recipes.json').write_text(json.dumps({'routines':manifest,'total_new_instruction_bytes':sum(f['bytes'] for f in manifest)},indent=2)+'\n',encoding='utf-8')
print('Verified two SCENA01 event handlers, 1104 instruction bytes.')
