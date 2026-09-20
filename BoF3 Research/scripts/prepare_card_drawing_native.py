from pathlib import Path
import base64,csv,hashlib,json,runpy,struct,zlib
R=Path(__file__).resolve().parents[1];O=R/'coverage/card-drawing-native';O.mkdir(parents=True,exist_ok=True)
runpy.run_path(str(R/'scripts/prepare_card_native.py'),run_name='__main__')
b=(R/'coverage/ghidra-input/STATUS-section-00-801D0C00.bin').read_bytes();base=0x801d0c00
assert hashlib.sha256(b).hexdigest()=='a47d32865283a01ce87b2f2f8cb19d3305525659b95a8feb4f307eddf63a8cb1'
funcs={int(x['address'],16):x for x in csv.DictReader((R/'coverage/identification/STATUS/functions.tsv').open(),delimiter='\t')};refs=list(csv.DictReader((R/'coverage/identification/STATUS/references.tsv').open(),delimiter='\t'))
inputs=json.loads((R/'startup-card-native-inputs.json').read_text());manifest=[]
for lo,hi,name in [(0x801de088,0x801de5d4,'bof3_draw_framed_panel'),(0x801df21c,0x801df410,'bof3_draw_tiled_menu_background'),(0x801e14a8,0x801e1680,'bof3_draw_card_slot_choices')]:
 f=funcs[lo];assert int(f['body_bytes'])==hi-lo and int(f['max_address'],16)==hi-1
 assert struct.unpack_from('<II',b,lo-base-8)==(0x03e00008,0) and struct.unpack_from('<II',b,hi-base-8)==(0x03e00008,0)
 code=b[lo-base:hi-base];assert struct.unpack_from('<I',code,0)[0]>>16==0x27bd
 for i in range(0,len(code),4):
  word=struct.unpack_from('<I',code,i)[0];op=word>>26
  if op in (1,4,5,6,7):
   imm=word&65535;imm=imm if imm<32768 else imm-65536;target=lo+i+4+imm*4;assert lo<=target<hi,(name,hex(target))
 deps=sorted({x['to'] for x in refs if x['function']==f'{lo:08x}' and 'CALL' in x['type']})
 callers=[x['from'] for x in refs if x['to']==f'{lo:08x}' and 'CALL' in x['type']];assert callers
 inputs.append({'schema':'psxrecomp overlay capture v2','origin':f'Static recipe for {name} from verified shared START/STATUS section; not a runtime capture.','load_addr':hex(lo),'size':len(code),'guard_bytes':0,'bytes_b64':base64.b64encode(code).decode(),'function_entry_pcs':[hex(lo)],'dispatch_entry_pcs':[hex(lo)],'static_dispatch_entry_pcs':[hex(lo)],'static_discovery_entry_pcs':[hex(lo)],'executed_pcs':[],'seeds':[hex(lo)],'producer_ranges':[{'start':hex(lo),'end':hex(hi)}],'strict_producer_ranges':True})
 manifest.append({'name':name,'entry':f'0x{lo:08X}','end_exclusive':f'0x{hi:08X}','bytes':len(code),'sha256':hashlib.sha256(code).hexdigest(),'crc32':f'0x{zlib.crc32(code):08X}','direct_dependencies':deps,'direct_call_sites':callers,'boundary_evidence':'Direct callers, contiguous Ghidra body, stack entry immediately after previous return/delay slot, own final return/delay slot; conditional branches stay within the extracted body.'})
(R/'startup-card-drawing-inputs.json').write_text(json.dumps(inputs,indent=2)+'\n');(O/'recipes.json').write_text(json.dumps({'source_sha256':hashlib.sha256(b).hexdigest(),'routines':manifest,'total_new_instruction_bytes':sum(x['bytes'] for x in manifest)},indent=2)+'\n')
print('Prepared three bounded drawing routines:',sum(x['bytes'] for x in manifest),'bytes')
