from pathlib import Path
import base64,csv,hashlib,json,runpy,struct,zlib
R=Path(__file__).resolve().parents[1];O=R/'coverage/gameplay-loops-native';O.mkdir(parents=True,exist_ok=True)
runpy.run_path(str(R/'scripts/prepare_logo_decoder_native.py'),run_name='__main__')
inputs=json.loads((R/'startup-logo-decoder-inputs.json').read_text());manifest=[]
b=(R/'coverage/ghidra-input/GAME-section-00-80195800.bin').read_bytes();base=0x80195800;sha='1663ff2e78134fe15f3cae6fb4074acf14b68b79cfa02be0c7651eaf6a1728ff';assert hashlib.sha256(b).hexdigest()==sha
root=R/'coverage/identification/GAME';funcs={int(x['address'],16):x for x in csv.DictReader((root/'functions.tsv').open(),delimiter='\t')};refs=list(csv.DictReader((root/'references.tsv').open(),delimiter='\t'))
targets=[(0x80197068,0x801970d8,0x801970d0,'bof3_gameplay_state_loop'),(0x801a0514,0x801a061c,0x801a05f0,'bof3_process_active_scene_records'),(0x801a06d8,0x801a0ae4,0x801a0a44,'bof3_dispatch_scene_record_updates')]
for lo,hi,resume,name in targets:
 f=funcs[lo];assert int(f['body_bytes'])==hi-lo and int(f['min_address'],16)==lo and int(f['max_address'],16)==hi-1
 code=b[lo-base:hi-base];assert struct.unpack_from('<I',b,lo-base-8)[0]==0x03e00008
 if lo==0x801a06d8:assert struct.unpack_from('<III',code)==(0x3c028014,0x9442625a,0x27bdffd8)
 else:assert struct.unpack_from('<I',code)[0]>>16==0x27bd
 if lo==0x80197068:assert struct.unpack_from('<II',code,len(code)-8)==(0x08065c27,0)
 else:assert struct.unpack_from('<II',code,len(code)-8)==(0x03e00008,0)
 direct=[];indirect=[]
 for i in range(0,len(code),4):
  word=struct.unpack_from('<I',code,i)[0];op=word>>26
  if op in (1,4,5,6,7):
   imm=word&65535;imm=imm if imm<32768 else imm-65536;assert lo<=lo+i+4+imm*4<hi
  if op==2:assert lo<=(((lo+i+4)&0xf0000000)|((word&0x03ffffff)<<2))<hi
  if op==3:direct.append({'pc':f'0x{lo+i:08X}','target':f'0x{((lo+i+4)&0xf0000000)|((word&0x03ffffff)<<2):08X}'})
  if op==0 and word&63==9:indirect.append(f'0x{lo+i:08X}')
 # Each observed interior PC is exactly the continuation after a JAL and delay slot.
 assert struct.unpack_from('<I',b,resume-base-8)[0]>>26==3
 live=O/'baseline'/f'live-code-{lo:08X}.bin';assert live.read_bytes()==code
 callers=[{'section':'GAME','pc':x['from']} for x in refs if x['to']==f'{lo:08x}' and 'CALL' in x['type']]
 if lo!=0x80197068:assert callers
 else:
  snapshot=json.loads((O/'baseline/loaded-save.json').read_text());entry=next(x for x in snapshot['dirty']['per_pc'] if x['pc']=='0x00197068');assert entry['entries']>=1
 dispatch=[hex(lo),hex(resume)]
 inputs.append({'schema':'psxrecomp overlay capture v2','origin':f'Static recipe for {name} from verified GAME section and exact loaded-save RAM bytes; interior dispatch PC is a return continuation, not a separate function.','load_addr':hex(lo),'size':len(code),'guard_bytes':0,'bytes_b64':base64.b64encode(code).decode(),'function_entry_pcs':[hex(lo)],'dispatch_entry_pcs':dispatch,'static_dispatch_entry_pcs':dispatch,'static_discovery_entry_pcs':[hex(lo)],'executed_pcs':[],'seeds':[hex(lo)],'producer_ranges':[{'start':hex(lo),'end':hex(hi)}],'strict_producer_ranges':True})
 manifest.append({'section':'GAME','input':'GAME-section-00-80195800.bin','image_base':f'0x{base:08X}','source_sha256':sha,'name':name,'entry':f'0x{lo:08X}','end_exclusive':f'0x{hi:08X}','observed_resume':f'0x{resume:08X}','bytes':len(code),'sha256':hashlib.sha256(code).hexdigest(),'crc32':f'0x{zlib.crc32(code):08X}','direct_dependencies':sorted({x['target'] for x in direct}),'direct_calls':direct,'indirect_call_sites':indirect,'direct_call_sites':callers,'live_code_evidence':str(live.relative_to(R)),'boundary_evidence':'Exact loaded RAM match; complete original prefix and branch/delay slots; all direct internal transfers stay in body; observed interior continuation is JAL+8. Main loop intentionally does not return and excludes its unreachable trailing epilogue; update bodies end in complete returns.'})
(R/'startup-gameplay-loops-inputs.json').write_text(json.dumps(inputs,indent=2)+'\n');(O/'recipes.json').write_text(json.dumps({'routines':manifest,'total_new_instruction_bytes':sum(x['bytes'] for x in manifest)},indent=2)+'\n')
print('Prepared three loop bodies with explicit observed return continuations:',sum(x['bytes'] for x in manifest),'bytes')
