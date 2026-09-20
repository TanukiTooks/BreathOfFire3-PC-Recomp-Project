from pathlib import Path
import base64,csv,hashlib,json,runpy,struct,zlib
R=Path(__file__).resolve().parents[1];O=R/'coverage/scene-callbacks-native';O.mkdir(parents=True,exist_ok=True)
runpy.run_path(str(R/'scripts/prepare_gameplay_loops_native.py'),run_name='__main__')
inputs=json.loads((R/'startup-gameplay-loops-inputs.json').read_text());manifest=[]
b=(R/'coverage/ghidra-input/GAME-section-00-80195800.bin').read_bytes();base=0x80195800;sha='1663ff2e78134fe15f3cae6fb4074acf14b68b79cfa02be0c7651eaf6a1728ff';assert hashlib.sha256(b).hexdigest()==sha
root=R/'coverage/identification/GAME';funcs={int(x['address'],16):x for x in csv.DictReader((root/'functions.tsv').open(),delimiter='\t')};refs=list(csv.DictReader((root/'references.tsv').open(),delimiter='\t'))
table=b[0x30:0x58];cases=list(struct.unpack('<10I',table));assert all(0x80197378<=pc<0x801975e4 and pc%4==0 for pc in cases)
assert (O/'baseline/live-state-jump-table.bin').read_bytes()==table
assert struct.unpack_from('<I',b,0x801c7b1c-base)[0]==0x80197378
# Preserve the original bounded switch: index < 10, load table[index], JR through v0.
assert struct.unpack_from('<I',b,0x8019739c-base)[0]==0x2c62000a
assert struct.unpack_from('<I',b,0x801973b0-base)[0]==0x8c225830
assert struct.unpack_from('<I',b,0x801973b8-base)[0]==0x00400008
targets=[(0x801991b8,0x80199230,[0x80199200,0x801991e8,0x80199220],'bof3_run_scene_frame_pipeline'),(0x80197378,0x801975e4,[],'bof3_handle_active_gameplay_state'),(0x801a1384,0x801a17a0,[],'bof3_update_scene_record_motion_state')]
for lo,hi,resumes,name in targets:
 f=funcs[lo];assert int(f['body_bytes'])==hi-lo and int(f['min_address'],16)==lo and int(f['max_address'],16)==hi-1
 code=b[lo-base:hi-base];assert struct.unpack_from('<I',b,lo-base-8)[0]==0x03e00008
 if lo==0x801a1384:assert struct.unpack_from('<III',code)==(0x3c031f80,0x8c630044,0x27bdffd0)
 else:assert struct.unpack_from('<I',code)[0]>>16==0x27bd
 assert struct.unpack_from('<II',code,len(code)-8)==(0x03e00008,0)
 direct=[];indirect=[];indirect_jumps=[]
 for i in range(0,len(code),4):
  word=struct.unpack_from('<I',code,i)[0];op=word>>26
  if op in (1,4,5,6,7):
   imm=word&65535;imm=imm if imm<32768 else imm-65536;assert lo<=lo+i+4+imm*4<hi
  if op==2:assert lo<=(((lo+i+4)&0xf0000000)|((word&0x03ffffff)<<2))<hi
  if op==3:direct.append({'pc':f'0x{lo+i:08X}','target':f'0x{((lo+i+4)&0xf0000000)|((word&0x03ffffff)<<2):08X}'})
  if op==0 and word&63==9:indirect.append(f'0x{lo+i:08X}')
  if op==0 and word&63==8 and word!=0x03e00008:indirect_jumps.append(lo+i)
 assert indirect_jumps==([0x801973b8] if lo==0x80197378 else [])
 for resume in resumes:assert struct.unpack_from('<I',b,resume-base-8)[0]>>26==3
 live=O/'baseline'/f'live-code-{lo:08X}.bin';assert live.read_bytes()==code
 callers=[{'section':'GAME','pc':x['from']} for x in refs if x['to']==f'{lo:08x}' and 'CALL' in x['type']]
 if lo!=0x80197378:assert callers
 case_entries=cases if lo==0x80197378 else []
 dispatch=[hex(pc) for pc in sorted(set([lo]+resumes+case_entries))]
 inputs.append({'schema':'psxrecomp overlay capture v2','origin':f'Static recipe for {name} from exact loaded GAME bytes. Declared case labels and call-return PCs are dispatch entries, not semantic function starts.','load_addr':hex(lo),'size':len(code),'guard_bytes':0,'bytes_b64':base64.b64encode(code).decode(),'function_entry_pcs':[hex(lo)],'dispatch_entry_pcs':dispatch,'static_dispatch_entry_pcs':dispatch,'static_discovery_entry_pcs':[hex(lo)],'executed_pcs':[],'seeds':[hex(lo)],'producer_ranges':[{'start':hex(lo),'end':hex(hi)}],'strict_producer_ranges':True})
 manifest.append({'section':'GAME','input':'GAME-section-00-80195800.bin','image_base':f'0x{base:08X}','source_sha256':sha,'name':name,'entry':f'0x{lo:08X}','end_exclusive':f'0x{hi:08X}','observed_hotspots':[f'0x{pc:08X}' for pc in (resumes if resumes else [lo])],'case_dispatch_entries':[f'0x{pc:08X}' for pc in case_entries],'bytes':len(code),'sha256':hashlib.sha256(code).hexdigest(),'crc32':f'0x{zlib.crc32(code):08X}','direct_dependencies':sorted({x['target'] for x in direct}),'direct_calls':direct,'indirect_call_sites':indirect,'direct_call_sites':callers,'live_code_evidence':str(live.relative_to(R)),'boundary_evidence':'Exact loaded RAM match; corrected setup prefix where needed; complete return/delay slot; internal direct branches; original switch bounds and all ten table targets verified separately. Runtime jump-table loads and indirect dispatch are retained.'})
(R/'startup-scene-callbacks-inputs.json').write_text(json.dumps(inputs,indent=2)+'\n');(O/'recipes.json').write_text(json.dumps({'routines':manifest,'total_new_instruction_bytes':sum(x['bytes'] for x in manifest),'state_jump_table':{'address':'0x80195830','bytes':40,'sha256':hashlib.sha256(table).hexdigest(),'targets':[f'0x{pc:08X}' for pc in cases],'note':'Verified as data; not compiled into code or substituted for runtime table reads.'}},indent=2)+'\n')
print('Prepared three callbacks:',sum(x['bytes'] for x in manifest),'instruction bytes, ten verified state-case dispatch labels')
