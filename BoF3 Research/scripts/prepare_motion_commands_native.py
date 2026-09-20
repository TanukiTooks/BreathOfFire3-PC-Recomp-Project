from pathlib import Path
import base64,csv,hashlib,json,runpy,struct,zlib
R=Path(__file__).resolve().parents[1];O=R/'coverage/motion-commands-native';O.mkdir(parents=True,exist_ok=True)
runpy.run_path(str(R/'scripts/prepare_position_records_native.py'),run_name='__main__')
inputs=json.loads((R/'startup-position-records-inputs.json').read_text());manifest=[]
b=(R/'coverage/ghidra-input/GAME-section-00-80195800.bin').read_bytes();base=0x80195800;sha='1663ff2e78134fe15f3cae6fb4074acf14b68b79cfa02be0c7651eaf6a1728ff';assert hashlib.sha256(b).hexdigest()==sha
root=R/'coverage/identification/GAME';funcs={int(x['address'],16):x for x in csv.DictReader((root/'functions.tsv').open(),delimiter='\t')};refs=list(csv.DictReader((root/'references.tsv').open(),delimiter='\t'))
tables={0x801a8f94:(0x80195cc0,[0x801a900c,0x801a9068,0x801a92d8,0x801a90d8,0x801a90f0,0x801a9180,0x801a9198,0x801a922c,0x801a9244,0x801a9330,0x801a933c,0x801a9344,0x801a9384,0x801a94d0,0x801a94e8]),0x801a9de8:(0x80195d80,[0x801a9e44,0x801a9e54,0x801a9e64,0x801a9eb8,0x801aa06c,0x801aa138,0x801aa308,0x801aa328,0x801aa3a0,0x801aa14c,0x801aa1a0,0x801aa3dc,0x801aa400,0x801aa24c,0x801aa290,0x801aa438])}
# Original subtract/bounds, scaled table load and JR; all instructions are retained.
expected={0x801a8fe4:0x2443ffff,0x801a8fe8:0x2c62000f,0x801a8fec:0x104001a5,0x801a8ff0:0x00031080,0x801a8ff4:0x3c018019,0x801a8ff8:0x00220821,0x801a8ffc:0x8c225cc0,0x801a9004:0x00400008,0x801a9e18:0x2443ff10,0x801a9e1c:0x2c620010,0x801a9e20:0x1040018a,0x801a9e28:0x00031080,0x801a9e2c:0x3c018019,0x801a9e30:0x00220821,0x801a9e34:0x8c225d80,0x801a9e3c:0x00400008}
for pc,word in expected.items():assert struct.unpack_from('<I',b,pc-base)[0]==word
jump_tables=[]
for entry,(address,cases) in tables.items():
 data=b[address-base:address-base+len(cases)*4];assert list(struct.unpack('<'+'I'*len(cases),data))==cases
 assert (O/'baseline'/f'live-command-table-{address:08X}.bin').read_bytes()==data
 jump_tables.append({'entry':f'0x{entry:08X}','address':f'0x{address:08X}','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'first_command':1 if entry==0x801a8f94 else 240,'targets':[f'0x{x:08X}' for x in cases],'note':'Original runtime table read retained; case labels are dispatch entries, not semantic functions.'})
targets=[(0x801a8f94,0x801a96e4,'bof3_execute_scene_control_commands'),(0x801a9de8,0x801aa470,'bof3_execute_extended_motion_command')]
for lo,hi,name in targets:
 f=funcs[lo];assert int(f['body_bytes'])==hi-lo and int(f['min_address'],16)==lo and int(f['max_address'],16)==hi-1
 code=b[lo-base:hi-base];assert struct.unpack_from('<I',b,lo-base-8)[0]==0x03e00008
 assert struct.unpack_from('<III',code)==((0x27bdffd8,0xafb00010,0x00808021) if lo==0x801a8f94 else (0x27bdffd0,0xafb1001c,0x00808821))
 assert struct.unpack_from('<II',code,len(code)-8)==(0x03e00008,0)
 direct=[];indirect=[];resumes=[];jumps=[]
 for i in range(0,len(code),4):
  word=struct.unpack_from('<I',code,i)[0];op=word>>26
  if op in (1,4,5,6,7):
   imm=word&65535;imm=imm if imm<32768 else imm-65536;assert lo<=lo+i+4+imm*4<hi
  if op==2:assert lo<=(((lo+i+4)&0xf0000000)|((word&0x03ffffff)<<2))<hi
  if op==3:
   direct.append({'pc':f'0x{lo+i:08X}','target':f'0x{((lo+i+4)&0xf0000000)|((word&0x03ffffff)<<2):08X}'})
   resumes.append(lo+i+8)
  if op==0 and word&63==9:indirect.append(f'0x{lo+i:08X}');resumes.append(lo+i+8)
  if op==0 and word&63==8 and word!=0x03e00008:jumps.append(lo+i)
 assert indirect==(['0x801A9310','0x801A9648'] if lo==0x801a8f94 else [])
 assert jumps==([0x801a9004] if lo==0x801a8f94 else [0x801a9e3c])
 cases=tables[lo][1];assert all(lo<=pc<hi and pc%4==0 for pc in cases)
 live=O/'baseline'/f'live-code-{lo:08X}.bin';assert live.read_bytes()==code
 callers=[{'section':'GAME','pc':x['from']} for x in refs if x['to']==f'{lo:08x}' and 'CALL' in x['type']]
 pointers=[f'0x{base+i:08X}' for i in range(0,len(b)-3,4) if struct.unpack_from('<I',b,i)[0]==lo]
 assert callers or pointers

 dispatch=[hex(pc) for pc in sorted(set([lo]+resumes+cases))]
 inputs.append({'schema':'psxrecomp overlay capture v2','origin':f'Static recipe for {name} from exact loaded GAME bytes. Call-return PCs are dispatch entries, not semantic function starts.','load_addr':hex(lo),'size':len(code),'guard_bytes':0,'bytes_b64':base64.b64encode(code).decode(),'function_entry_pcs':[hex(lo)],'dispatch_entry_pcs':dispatch,'static_dispatch_entry_pcs':dispatch,'static_discovery_entry_pcs':[hex(lo)],'executed_pcs':[],'seeds':[hex(lo)],'producer_ranges':[{'start':hex(lo),'end':hex(hi)}],'strict_producer_ranges':True})
 manifest.append({'section':'GAME','input':'GAME-section-00-80195800.bin','image_base':f'0x{base:08X}','source_sha256':sha,'name':name,'entry':f'0x{lo:08X}','end_exclusive':f'0x{hi:08X}','observed_hotspots':[f'0x{lo:08X}'],'resume_dispatch_entries':[f'0x{pc:08X}' for pc in resumes],'case_dispatch_entries':[f'0x{pc:08X}' for pc in cases],'bytes':len(code),'sha256':hashlib.sha256(code).hexdigest(),'crc32':f'0x{zlib.crc32(code):08X}','direct_dependencies':sorted({x['target'] for x in direct}),'direct_calls':direct,'indirect_call_sites':indirect,'direct_call_sites':callers,'aligned_pointer_locations':pointers,'live_code_evidence':str(live.relative_to(R)),'boundary_evidence':'Complete Ghidra body and exact loaded RAM match; preceding return/delay slot; verified stack setup; complete return/delay slot; internal direct branches and all bounded switch targets. Runtime jump tables, callbacks and original division traps retained.'})
(R/'startup-motion-commands-inputs.json').write_text(json.dumps(inputs,indent=2)+'\n');(O/'recipes.json').write_text(json.dumps({'routines':manifest,'total_new_instruction_bytes':sum(x['bytes'] for x in manifest),'command_jump_tables':jump_tables,'verified_switch_opcodes':{f'0x{k:08X}':f'0x{v:08X}' for k,v in expected.items()}},indent=2)+'\n')
print('Prepared two motion-command interpreters:',sum(x['bytes'] for x in manifest),'instruction bytes')
