from pathlib import Path
import base64,csv,hashlib,json,struct,zlib
R=Path(__file__).resolve().parents[1];O=R/'coverage/party-motion-native';O.mkdir(exist_ok=True)
inputs=json.loads((R/'startup-motion-commands-inputs.json').read_text());manifest=[]
b=(R/'coverage/ghidra-input/GAME-section-00-80195800.bin').read_bytes();base=0x80195800;sha='1663ff2e78134fe15f3cae6fb4074acf14b68b79cfa02be0c7651eaf6a1728ff';assert hashlib.sha256(b).hexdigest()==sha
funcs={int(x['address'],16):x for x in csv.DictReader((R/'coverage/identification/GAME/functions.tsv').open(),delimiter='\t')}
targets=[(0x801bdbc4,0x801bdcf8,'bof3_prepare_party_control_mask'),(0x801a2ae4,0x801a2c10,'bof3_update_motion_record_flag_08')]
for lo,hi,name in targets:
 f=funcs[lo];assert int(f['body_bytes'])==hi-lo and int(f['min_address'],16)==lo and int(f['max_address'],16)==hi-1
 code=b[lo-base:hi-base];assert struct.unpack_from('<I',b,lo-base-8)[0]==0x03e00008
 assert struct.unpack_from('<I',code)[0]==(0x27bdfff8 if lo==0x801bdbc4 else 0x27bdffe8)
 assert struct.unpack_from('<II',code,len(code)-8)==(0x03e00008,0)
 calls=[];resumes=[]
 for i in range(0,len(code),4):
  w=struct.unpack_from('<I',code,i)[0];op=w>>26
  if op in (1,4,5,6,7):
   imm=struct.unpack('<h',struct.pack('<H',w&65535))[0];assert lo<=lo+i+4+imm*4<hi
  if op==2:assert lo<=((lo+i+4)&0xf0000000)|((w&0x3ffffff)<<2)<hi
  if op==3:calls.append({'pc':hex(lo+i),'target':hex(((lo+i+4)&0xf0000000)|((w&0x3ffffff)<<2))});resumes.append(lo+i+8)
  if op==0 and w&63 in (8,9):assert w==0x03e00008,'Unexpected indirect transfer'
 assert calls==([] if lo==0x801bdbc4 else [{'pc':'0x801a2b44','target':'0x801a3080'}])
 for stage in ['camp-idle','world-loaded','world-settled']:assert (O/'baseline'/f'{stage}-code-{lo:08X}.bin').read_bytes()==code
 entries=[hex(lo)]+[hex(x) for x in resumes]
 inputs.append({'schema':'psxrecomp overlay capture v2','origin':f'Static recipe for {name}, exact full-party camp and world-map GAME code.','load_addr':hex(lo),'size':len(code),'guard_bytes':0,'bytes_b64':base64.b64encode(code).decode(),'function_entry_pcs':[hex(lo)],'dispatch_entry_pcs':entries,'static_dispatch_entry_pcs':entries,'static_discovery_entry_pcs':[hex(lo)],'executed_pcs':[],'seeds':[hex(lo)],'producer_ranges':[{'start':hex(lo),'end':hex(hi)}],'strict_producer_ranges':True})
 manifest.append({'section':'GAME','entry':f'0x{lo:08X}','end_exclusive':f'0x{hi:08X}','name':name,'bytes':len(code),'sha256':hashlib.sha256(code).hexdigest(),'crc32':f'0x{zlib.crc32(code):08X}','source_sha256':sha,'calls':calls,'resume_dispatch_entries':[f'0x{x:08X}' for x in resumes],'boundary_evidence':'Exact complete Ghidra extent, preceding return and delay slot, stack allocation, final return and delay slot; all direct branches internal; all live camp/world samples equal source.'})
(R/'startup-party-motion-inputs.json').write_text(json.dumps(inputs,indent=2)+'\n');(O/'recipes.json').write_text(json.dumps({'routines':manifest,'total_new_instruction_bytes':sum(f['bytes'] for f in manifest)},indent=2)+'\n')
print('Verified two party/motion helpers, 608 instruction bytes.')
