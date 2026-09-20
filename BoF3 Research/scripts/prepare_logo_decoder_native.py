from pathlib import Path
import base64,csv,hashlib,json,runpy,struct,zlib
R=Path(__file__).resolve().parents[1];O=R/'coverage/logo-decoder-native';O.mkdir(parents=True,exist_ok=True)
runpy.run_path(str(R/'scripts/prepare_drawing_primitives_native.py'),run_name='__main__')
inputs=json.loads((R/'startup-drawing-primitives-inputs.json').read_text())
exe=(R/'input/LOGO/LOGO.EXE').read_bytes()
assert hashlib.sha256(exe).hexdigest()=='21b3f791e450ff308a874e3691d0c0c88df428464f9ad08ea2c7a680a6c0dd2c'
assert exe[:8]==b'PS-X EXE'
base,size=struct.unpack_from('<II',exe,0x18);assert base==0x801ce000 and len(exe)==2048+size
b=exe[2048:];assert b==(R/'coverage/ghidra-input/LOGO-payload-801CE000.bin').read_bytes()
lo=0x801d7578;hi=0x801d78b8;name='bof3_logo_decode_video_bitstream';code=b[lo-base:hi-base]
f=next(x for x in csv.DictReader((R/'coverage/identification/LOGO/functions.tsv').open(),delimiter='\t') if x['address']==f'{lo:08x}')
assert int(f['body_bytes'])==hi-lo and int(f['min_address'],16)==lo and int(f['max_address'],16)==hi-1
assert struct.unpack_from('<III',b,lo-base-8)==(0x03e00008,0xad010000,0x3c08801d)
returns=[];cop0=[]
for i in range(0,len(code),4):
 word=struct.unpack_from('<I',code,i)[0];op=word>>26
 if op in (1,4,5,6,7):
  imm=word&65535;imm=imm if imm<32768 else imm-65536;assert lo<=lo+i+4+imm*4<hi
 if op==2:assert lo<=((lo+i+4)&0xf0000000)|((word&0x03ffffff)<<2)<hi
 assert op!=3,'Unexpected direct call'
 if op==0 and word&63 in (8,9):assert word==0x03e00008;returns.append(lo+i)
 if op==16:cop0.append(lo+i)
assert returns==[0x801d787c,0x801d78b0] and cop0==[0x801d7868,0x801d7878]
assert struct.unpack_from('<I',b,0x801d7880-base)[0]==0x00001020
assert struct.unpack_from('<I',b,hi-base-4)[0]==0x20020001
caller=0x801ceb98;word=struct.unpack_from('<I',b,caller-base)[0]
assert word>>26==3 and ((caller+4)&0xf0000000)|((word&0x03ffffff)<<2)==lo
capture_path=R/'coverage/runs/20260911-083320-410/overlay_captures.json';captures=json.loads(capture_path.read_text());matches=[]
for i,c in enumerate(captures):
 start=int(c['load_addr'],0);start=(start&0x1fffffff)|0x80000000;raw=base64.b64decode(c['bytes_b64'])
 if start<=lo and start+len(raw)>=hi and raw[lo-start:hi-start]==code and any((int(pc,0)&0x1fffffff)==(lo&0x1fffffff) for pc in c.get('executed_pcs',[])):matches.append(i)
assert matches
inputs.append({'schema':'psxrecomp overlay capture v2','origin':f'Static recipe for {name} from verified LOGO executable payload; corroborated by full-range live capture, not itself a runtime capture.','load_addr':hex(lo),'size':len(code),'guard_bytes':0,'bytes_b64':base64.b64encode(code).decode(),'function_entry_pcs':[hex(lo)],'dispatch_entry_pcs':[hex(lo)],'static_dispatch_entry_pcs':[hex(lo)],'static_discovery_entry_pcs':[hex(lo)],'executed_pcs':[],'seeds':[hex(lo)],'producer_ranges':[{'start':hex(lo),'end':hex(hi)}],'strict_producer_ranges':True})
manifest={'section':'LOGO','input':'LOGO-payload-801CE000.bin','image_base':f'0x{base:08X}','source_sha256':hashlib.sha256(b).hexdigest(),'name':name,'entry':f'0x{lo:08X}','end_exclusive':f'0x{hi:08X}','bytes':len(code),'sha256':hashlib.sha256(code).hexdigest(),'crc32':f'0x{zlib.crc32(code):08X}','direct_dependencies':[],'direct_call_sites':[{'section':'LOGO','pc':f'{caller:08x}'}],'boundary_evidence':'Direct JAL opcode at 0x801CEB98; contiguous Ghidra body; prior return and store delay slot; internal conditional branches; two complete returns; COP0 operations retained. Writable decoder state begins at the exclusive end and is not compiled.','live_capture_evidence':{'path':str(capture_path.relative_to(R)),'file_sha256':hashlib.sha256(capture_path.read_bytes()).hexdigest(),'full_range_match_indices':matches}}
(R/'startup-logo-decoder-inputs.json').write_text(json.dumps(inputs,indent=2)+'\n');(O/'recipes.json').write_text(json.dumps({'routines':[manifest],'total_new_instruction_bytes':len(code)},indent=2)+'\n')
print('Prepared full-capture-verified 832-byte logo decoder; both return delay slots and COP0 operations retained.')
