from pathlib import Path
import base64,csv,hashlib,json,runpy,struct,zlib
R=Path(__file__).resolve().parents[1];O=R/'coverage/state-boundaries-native';O.mkdir(parents=True,exist_ok=True)
runpy.run_path(str(R/'scripts/prepare_primary_motion_native.py'),run_name='__main__')
inputs=json.loads((R/'startup-primary-motion-inputs.json').read_text());manifest=[]
b=(R/'coverage/ghidra-input/GAME-section-00-80195800.bin').read_bytes();base=0x80195800;sha='1663ff2e78134fe15f3cae6fb4074acf14b68b79cfa02be0c7651eaf6a1728ff';assert hashlib.sha256(b).hexdigest()==sha
root=R/'coverage/identification/GAME';funcs={int(x['address'],16):x for x in csv.DictReader((root/'functions.tsv').open(),delimiter='\t')};refs=list(csv.DictReader((root/'references.tsv').open(),delimiter='\t'))
targets=[(0x801b0320,0x801b036c,'bof3_update_primary_state1_substate'),(0x801a782c,0x801a7878,'bof3_dispatch_scene_mode'),(0x801a1a24,0x801a1a58,'bof3_mark_record_flag10_unless_type8')]
for lo,hi,name in targets:
 f=funcs[lo];assert int(f['body_bytes'])==hi-lo and int(f['min_address'],16)==lo and int(f['max_address'],16)==hi-1
 code=b[lo-base:hi-base];assert struct.unpack_from('<I',b,lo-base-8)[0]==0x03e00008
 expected_prefix={0x801b0320:(0x3c021f80,0x8c420044,0x27bdffe8),0x801a782c:(0x3c028014,0x80426870,0x27bdffe8),0x801a1a24:(0x3c021f80,0x8c420044,0)}
 assert struct.unpack_from('<III',code)==expected_prefix[lo]
 assert struct.unpack_from('<II',code,len(code)-8)==(0x03e00008,0)
 direct=[];indirect=[];resumes=[]
 for i in range(0,len(code),4):
  word=struct.unpack_from('<I',code,i)[0];op=word>>26
  if op in (1,4,5,6,7):
   imm=word&65535;imm=imm if imm<32768 else imm-65536;assert lo<=lo+i+4+imm*4<hi
  if op==2:assert lo<=(((lo+i+4)&0xf0000000)|((word&0x03ffffff)<<2))<hi
  if op==3:
   direct.append({'pc':f'0x{lo+i:08X}','target':f'0x{((lo+i+4)&0xf0000000)|((word&0x03ffffff)<<2):08X}'})
   resumes.append(lo+i+8)
  if op==0 and word&63==9:indirect.append(f'0x{lo+i:08X}');resumes.append(lo+i+8)
  if op==0 and word&63==8:assert word==0x03e00008
 assert indirect==({0x801b0320:['0x801B034C'],0x801a782c:['0x801A7858'],0x801a1a24:[]}[lo])
 live=O/'baseline'/f'live-code-{lo:08X}.bin';assert live.read_bytes()==code
 callers=[{'section':'GAME','pc':x['from']} for x in refs if x['to']==f'{lo:08x}' and 'CALL' in x['type']]
 pointers=[f'0x{base+i:08X}' for i in range(0,len(b)-3,4) if struct.unpack_from('<I',b,i)[0]==lo]
 assert callers or pointers
 if lo==0x801b0320:assert '0x801CD0B0' in pointers
 if lo==0x801a1a24:assert '0x801C83F0' in pointers
 dispatch=[hex(pc) for pc in sorted(set([lo]+resumes))]
 inputs.append({'schema':'psxrecomp overlay capture v2','origin':f'Static recipe for {name} from exact loaded GAME bytes. Call-return PCs are dispatch entries, not semantic function starts.','load_addr':hex(lo),'size':len(code),'guard_bytes':0,'bytes_b64':base64.b64encode(code).decode(),'function_entry_pcs':[hex(lo)],'dispatch_entry_pcs':dispatch,'static_dispatch_entry_pcs':dispatch,'static_discovery_entry_pcs':[hex(lo)],'executed_pcs':[],'seeds':[hex(lo)],'producer_ranges':[{'start':hex(lo),'end':hex(hi)}],'strict_producer_ranges':True})
 manifest.append({'section':'GAME','input':'GAME-section-00-80195800.bin','image_base':f'0x{base:08X}','source_sha256':sha,'name':name,'entry':f'0x{lo:08X}','end_exclusive':f'0x{hi:08X}','observed_hotspots':[f'0x{lo:08X}'],'resume_dispatch_entries':[f'0x{pc:08X}' for pc in resumes],'case_dispatch_entries':[],'bytes':len(code),'sha256':hashlib.sha256(code).hexdigest(),'crc32':f'0x{zlib.crc32(code):08X}','direct_dependencies':sorted({x['target'] for x in direct}),'direct_calls':direct,'indirect_call_sites':indirect,'direct_call_sites':callers,'aligned_pointer_locations':pointers,'live_code_evidence':str(live.relative_to(R)),'boundary_evidence':'Complete Ghidra body and exact loaded RAM match; preceding return/delay slot; verified setup prefix or complete leaf; complete own return/delay slot; internal branch targets. Indirect callback table reads retained.'})
(R/'startup-state-boundaries-inputs.json').write_text(json.dumps(inputs,indent=2)+'\n');(O/'recipes.json').write_text(json.dumps({'routines':manifest,'total_new_instruction_bytes':sum(x['bytes'] for x in manifest)},indent=2)+'\n')
print('Prepared state boundary helpers:',sum(x['bytes'] for x in manifest),'instruction bytes')
