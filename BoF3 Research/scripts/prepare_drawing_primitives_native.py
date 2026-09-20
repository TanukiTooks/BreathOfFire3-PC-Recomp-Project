from pathlib import Path
import base64,csv,hashlib,json,runpy,struct,zlib
R=Path(__file__).resolve().parents[1];O=R/'coverage/drawing-primitives-native';O.mkdir(parents=True,exist_ok=True)
runpy.run_path(str(R/'scripts/prepare_panel_border_native.py'),run_name='__main__')
inputs=json.loads((R/'startup-panel-border-inputs.json').read_text());manifest=[]
all_refs=[dict(row,source_section=sec) for sec in ('GAME','STATUS') for row in csv.DictReader((R/'coverage/identification'/sec/'references.tsv').open(),delimiter='\t')]
targets=[('GAME', 'GAME-section-00-80195800.bin', 2149144576, '1663ff2e78134fe15f3cae6fb4074acf14b68b79cfa02be0c7651eaf6a1728ff', 2149245936, 2149247364, 'bof3_draw_textured_panel'), ('GAME', 'GAME-section-00-80195800.bin', 2149144576, '1663ff2e78134fe15f3cae6fb4074acf14b68b79cfa02be0c7651eaf6a1728ff', 2149249268, 2149249548, 'bof3_draw_colored_line'), ('GAME', 'GAME-section-00-80195800.bin', 2149144576, '1663ff2e78134fe15f3cae6fb4074acf14b68b79cfa02be0c7651eaf6a1728ff', 2149249648, 2149249696, 'bof3_get_menu_tile_descriptor'), ('GAME', 'GAME-section-00-80195800.bin', 2149144576, '1663ff2e78134fe15f3cae6fb4074acf14b68b79cfa02be0c7651eaf6a1728ff', 2149249696, 2149249936, 'bof3_draw_menu_tile')]
for section,filename,base,sha,lo,hi,name in targets:
 b=(R/'coverage/ghidra-input'/filename).read_bytes();assert hashlib.sha256(b).hexdigest()==sha
 root=R/'coverage/identification'/section;funcs={int(x['address'],16):x for x in csv.DictReader((root/'functions.tsv').open(),delimiter='\t')};refs=list(csv.DictReader((root/'references.tsv').open(),delimiter='\t'));f=funcs[lo]
 assert int(f['body_bytes'])==hi-lo and int(f['max_address'],16)==hi-1
 assert struct.unpack_from('<I',b,lo-base-8)[0]==0x03e00008 and struct.unpack_from('<I',b,hi-base-8)[0]==0x03e00008
 expected_delay={0x801af270:0x00431021}.get(lo,0);assert struct.unpack_from('<I',b,hi-base-4)[0]==expected_delay
 code=b[lo-base:hi-base];first=struct.unpack_from('<I',code,0)[0]
 assert first==0x30a500ff if lo==0x801af270 else first>>16==0x27bd
 for i in range(0,len(code),4):
  word=struct.unpack_from('<I',code,i)[0]
  if word>>26 in (1,4,5,6,7):
   imm=word&65535;imm=imm if imm<32768 else imm-65536;assert lo<=lo+i+4+imm*4<hi
  if word>>26==2:
   target=((lo+i+4)&0xf0000000)|((word&0x03ffffff)<<2);assert lo<=target<hi
 deps=sorted({x['to'] for x in refs if x['function']==f'{lo:08x}' and 'CALL' in x['type']});callers=[{'section':x['source_section'],'pc':x['from']} for x in all_refs if x['to']==f'{lo:08x}' and 'CALL' in x['type']];assert callers
 inputs.append({'schema':'psxrecomp overlay capture v2','origin':f'Static recipe for {name} from verified {section} section; not a runtime capture.','load_addr':hex(lo),'size':len(code),'guard_bytes':0,'bytes_b64':base64.b64encode(code).decode(),'function_entry_pcs':[hex(lo)],'dispatch_entry_pcs':[hex(lo)],'static_dispatch_entry_pcs':[hex(lo)],'static_discovery_entry_pcs':[hex(lo)],'executed_pcs':[],'seeds':[hex(lo)],'producer_ranges':[{'start':hex(lo),'end':hex(hi)}],'strict_producer_ranges':True})
 manifest.append({'section':section,'input':filename,'image_base':f'0x{base:08X}','source_sha256':sha,'name':name,'entry':f'0x{lo:08X}','end_exclusive':f'0x{hi:08X}','bytes':len(code),'sha256':hashlib.sha256(code).hexdigest(),'crc32':f'0x{zlib.crc32(code):08X}','direct_dependencies':deps,'direct_call_sites':callers,'boundary_evidence':'Direct call targets; contiguous body immediately after previous return/delay slot; verified stack prologue or leaf argument mask; complete final return and exact delay-slot opcode; conditional branches and direct jumps remain within body.'})
(R/'startup-drawing-primitives-inputs.json').write_text(json.dumps(inputs,indent=2)+'\n');(O/'recipes.json').write_text(json.dumps({'routines':manifest,'total_new_instruction_bytes':sum(x['bytes'] for x in manifest)},indent=2)+'\n')
print('Prepared four original drawing primitives:',sum(x['bytes'] for x in manifest),'bytes')
