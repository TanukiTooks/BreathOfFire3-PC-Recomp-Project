from pathlib import Path
import hashlib,json,base64,csv
R=Path(__file__).resolve().parents[1];workspace=R.parent;G=workspace/'BoF3 PSXRecomp/BreathOfFireIII';O=R/'coverage/card-native'
b=(R/'coverage/ghidra-input/STATUS-section-00-801D0C00.bin').read_bytes()
assert hashlib.sha256(b).hexdigest()=='a47d32865283a01ce87b2f2f8cb19d3305525659b95a8feb4f307eddf63a8cb1'
start,end,base=0x801e5320,0x801e54a4,0x801d0c00
f=next(x for x in csv.DictReader((R/'coverage/identification/STATUS/functions.tsv').open(),delimiter='\t') if int(x['address'],16)==start)
assert int(f['body_bytes'])==end-start and int(f['max_address'],16)==end-1
code=b[start-base:end-base];assert len(code)==388
inputs=json.loads((R/'startup-card-overlay-captures.json').read_text())
recipe={'schema':'psxrecomp overlay capture v2','origin':'Static recipe extracted from verified START.EMI section 8 / STATUS.EMI section 0; not a new runtime capture.','load_addr':hex(start),'size':len(code),'guard_bytes':0,'bytes_b64':base64.b64encode(code).decode(),'function_entry_pcs':[hex(start)],'dispatch_entry_pcs':[hex(start)],'static_dispatch_entry_pcs':[hex(start)],'static_discovery_entry_pcs':[hex(start)],'executed_pcs':[],'seeds':[hex(start)],'producer_ranges':[{'start':hex(start),'end':hex(end)}],'strict_producer_ranges':True}
inputs.append(recipe);(R/'startup-card-native-inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
refs=list(csv.DictReader((R/'coverage/identification/STATUS/references.tsv').open(),delimiter='\t'))
deps=sorted({x['to'] for x in refs if x['function']=='801e5320' and 'CALL' in x['type']})
(O/'recipe.json').write_text(json.dumps({'source_sha256':hashlib.sha256(b).hexdigest(),'routine_sha256':hashlib.sha256(code).hexdigest(),'entry':hex(start),'end_exclusive':hex(end),'bytes':len(code),'direct_dependencies':deps,'strategy':'Compile only this original routine using stock static CPS generation; preserve runtime dispatch for dependencies; byte guards select the resident image.'},indent=2)+'\n')
print('Prepared one verified 388-byte routine; direct dependencies:',deps)
