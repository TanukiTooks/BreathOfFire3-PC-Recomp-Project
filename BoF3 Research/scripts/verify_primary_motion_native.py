from pathlib import Path
from PIL import Image,ImageChops
import csv,hashlib,json,re,zlib,struct
R=Path(__file__).resolve().parents[1];O=R/'coverage/primary-motion-native';G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII'
manifest=json.loads((O/'recipes.json').read_text())
result={'status':'passed','new_routines':[],'new_instruction_bytes':820,'checkpoints':[],'limitations':['Twelve headless checkpoints; not all menus, input configurations, graphics backends or full-game paths.','Counts are bounded-log lower bounds, not exact totals or speed measurements.','Native dispatch guards and entry execution are verified; dependencies keep their existing routing.']}
log=(O/'native/stderr.log').read_text();counts={}
for addr,count in re.findall(r'\[bof3-native-card\] entry=(0x[0-9A-F]+) handled=1 count=(\d+)',log):counts[addr]=max(counts.get(addr,0),int(count))
for entry in ['0x801E5320','0x801DE088','0x801DF21C','0x801E14A8','0x801AEBA0','0x801DF410','0x801AE3F0','0x801AF0F4','0x801AF270','0x801AF2A0','0x801D7578','0x801A0514','0x801A06D8','0x801970D0','0x801A05F0','0x801A0A44']:assert counts.get(entry,0)>=8
new=(G/'generated-primary-motion-overlays/overlays_static.c').read_text();old=(G/'generated-frame-helpers-overlays/overlays_static.c').read_text();pattern=r'^void (\w+)\(CPUState \*cpu\);';old_ids=set(re.findall(pattern,old,re.M));new_ids=set(re.findall(pattern,new,re.M));assert old_ids and old_ids<=new_ids
added=new_ids-old_ids;assert len(added)==60
for f in manifest['routines']:
 source=(R/'coverage/ghidra-input'/f['input']).read_bytes();assert hashlib.sha256(source).hexdigest()==f['source_sha256']
 lo=int(f['entry'],16);hi=int(f['end_exclusive'],16);base=int(f['image_base'],16);b=source[lo-base:hi-base]
 assert len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256'] and f'0x{zlib.crc32(b):08X}'==f['crc32']
 assert f'0x{lo&0x1fffffff:08X}u, 0x{len(b):X}u' in new
 assert counts.get(f['entry'],0)>=8
 for pc in f['observed_hotspots']:assert counts.get(pc,0)>=8
 assert (O/'baseline'/f"live-code-{lo:08X}.bin").read_bytes()==b
 assert (O/'native'/f"live-code-{lo:08X}.bin").read_bytes()==b
 prefix=f"ov_{lo&0x1fffffff:08X}_{zlib.crc32(b):08X}_";aliases=sorted(x for x in added if x.startswith(prefix));assert aliases
 result['new_routines'].append(dict(f,native_entries_at_least=counts[f['entry']],generated_entries_including_continuations=len(aliases)))
assert sum(x['generated_entries_including_continuations'] for x in result['new_routines'])==len(added)
result['native_entry_counts_at_least']=counts;result['preserved_prior_generated_identities']=len(old_ids);result['added_entries_including_continuations']=len(added)
old_inputs=json.loads((R/'startup-frame-helpers-inputs.json').read_text());new_inputs=json.loads((R/'startup-primary-motion-inputs.json').read_text());assert new_inputs[:len(old_inputs)]==old_inputs and len(new_inputs)==len(old_inputs)+3
for stage in ['card0','card1','card0-return','cancel','reenter','confirm','load-prompt','loaded-save','gameplay-idle','gameplay-right','gameplay-left','gameplay-settled']:
 a=json.loads((O/'baseline'/f'{stage}.json').read_text());b=json.loads((O/'native'/f'{stage}.json').read_text());keys=['slot','outer_phase','menu_phase','mask','gameplay_phase'];assert all(a[k]==b[k] for k in keys),stage
 ia=Image.open(O/'baseline'/f'{stage}.png').convert('RGB');ib=Image.open(O/'native'/f'{stage}.png').convert('RGB');assert ia.size==ib.size
 diff=ImageChops.difference(ia,ib);points=[(i%ia.width,i//ia.width) for i,pixel in enumerate(diff.get_flattened_data()) if pixel!=(0,0,0)]
 # The selection outline has a one-pixel beveled upper-left corner at (50,56).
 border=all(48<=x<=256 and 54<=y<=105 and (x<=49 or x>=255 or y<=55 or y>=104 or (x,y)==(50,56)) for x,y in points)
 assert not points or (stage=='confirm' and border),(stage,diff.getbbox(),len(points))
 result['checkpoints'].append({'stage':stage,'state':{k:b[k] for k in keys},'state_match':True,'identical_image':not points,'different_pixels':len(points),'difference_bbox':diff.getbbox(),'save_outline_only':bool(points) and border})
for run in ['baseline','native']:
 assert json.loads((O/run/'probe-result.json').read_text())['status']=='complete'
 loaded=json.loads((O/run/'loaded-save.json').read_text());assert loaded['outer_phase']==0
assert json.loads((O/'original-card-hashes.json').read_text(encoding='utf-8-sig'))
for card in json.loads((O/'original-card-hashes.json').read_text(encoding='utf-8-sig')):assert hashlib.sha256(Path(card['Path']).read_bytes()).hexdigest().upper()==card['Hash']
result['original_card_hashes_unchanged']=True
for f in manifest['routines']:
 functions={x['address'].upper():x for x in csv.DictReader((R/'coverage/identification'/f['section']/'functions.tsv').open(),delimiter='\t')}
 assert functions[f['entry'][2:]]['name']==f['name']
 assert 'RESEARCH_SYMBOLS_APPLIED=3' in (O/f"ghidra-{f['section']}.log").read_text()
for label,filename in [('baseline','Breath_of_Fire_III___PSXRecomp.before-primary-motion.exe'),('native','Breath_of_Fire_III___PSXRecomp.exe')]:result[label+'_exe_sha256']=hashlib.sha256((G/'build-release'/filename).read_bytes()).hexdigest()
prior_validation=json.loads((R/'coverage/frame-helpers-native/validation.json').read_text())
for entry,count in prior_validation['native_entry_counts_at_least'].items():assert counts.get(entry,0)>=min(8,count),entry
result['hotspots']={}
for f in manifest['routines']:
 for hotspot in f['observed_hotspots']:
  pc=f"0x{int(hotspot,16)&0x1fffffff:08X}";values={}
  for variant in ['baseline','native']:
   stats=json.loads((O/variant/'gameplay-settled.json').read_text())['dirty'];values[variant]=next((x['insns'] for x in stats['per_pc'] if x['pc']==pc),0)
  assert values['baseline']>0 and values['native']==0,(pc,values)
  result['hotspots'][hotspot]=values
# Match canonical guest dispatch keys to their variant records, not physical guard-range addresses.
entry_body=re.search(r'static const PsxOvEntry psx_ov_entries\[\d+\] = \{(.*?)\n\};',new,re.S).group(1)
entries={int(addr,16):(int(first),int(count)) for addr,first,count in re.findall(r'\{\s*0x([0-9A-F]+)u,\s*(\d+)u,\s*(\d+)u\s*\}',entry_body)}
variant_body=re.search(r'static const PsxOvVariant psx_ov_variants\[\d+\] = \{(.*?)\n\};',new,re.S).group(1)
variants=re.findall(r'\{\s*(\w+),\s*(\d+)u,\s*0x([0-9A-F]+)u,\s*(\w+)\s*\}',variant_body)
case_checks=[]
for f in manifest['routines']:
 prefix=f"ov_{int(f['entry'],16)&0x1fffffff:08X}_{int(f['crc32'],16):08X}_"
 for target in [f['entry']]+f['observed_hotspots']+f['resume_dispatch_entries']:
  first,n=entries[int(target,16)];matches=[x for x in variants[first:first+n] if x[3].startswith(prefix) and x[3].endswith('_func_'+target[2:])]
  assert matches,(target,prefix)
  for ranges,count,crc,name in matches:
   assert int(crc,16)==int(f['crc32'],16) and int(count)==1
   expected=f"static const uint32_t {ranges}[] = {{ 0x{int(f['entry'],16)&0x1fffffff:08X}u, 0x{f['bytes']:X}u }};"
   assert expected in new
  if target in f['case_dispatch_entries']:case_checks.append({'pc':target,'matching_guarded_variant':True,'native_entries_at_least':counts.get(target,0)})
result['native_resume_counts_at_least']={pc:counts.get(pc,0) for f in manifest['routines'] for pc in f['resume_dispatch_entries']}
assert counts.get('0x80197068',0)>=1
baseline_records=(O/'baseline/gameplay-settled-records.bin').read_bytes();native_records=(O/'native/gameplay-settled-records.bin').read_bytes()
assert len(baseline_records)==30*0x98 and len(native_records)==len(baseline_records)
field_evidence=json.loads((O/'animation-field-evidence.json').read_text());boot=(R/'input/SLUS_004.22').read_bytes();assert hashlib.sha256(boot).hexdigest()==field_evidence['boot_sha256'];boot_base=struct.unpack_from('<I',boot,0x18)[0]
for evidence in field_evidence['original_opcodes_verified']:assert struct.unpack_from('<I',boot,2048+int(evidence['pc'],16)-boot_base)[0]==int(evidence['opcode'],16)
allowed_offsets={int(f['offset'],16)+i for f in field_evidence['fields'] for i in range(f['bytes'])}
differences=[{'record':i//0x98,'offset':f'0x{i%0x98:02X}','baseline':a,'native':b} for i,(a,b) in enumerate(zip(baseline_records,native_records)) if a!=b]
assert all(int(x['offset'],16) in allowed_offsets for x in differences),differences
result['settled_scene_records']={'bytes':len(native_records),'identical':not differences,'non_animation_bytes_identical':True,'different_bytes':len(differences),'differences':differences,'field_evidence':'animation-field-evidence.json','baseline_frame':json.loads((O/'baseline/gameplay-settled.json').read_text())['frame'],'native_frame':json.loads((O/'native/gameplay-settled.json').read_text())['frame']}
result['interpreted_instructions_at_loaded_save']={v:json.loads((O/v/'loaded-save.json').read_text())['dirty']['insns_run'] for v in ['baseline','native']}
result['interpreted_instructions_at_settled_gameplay']={v:json.loads((O/v/'gameplay-settled.json').read_text())['dirty']['insns_run'] for v in ['baseline','native']}
# Active palette output tests supplement the naturally inactive pool in this save.
result['active_palette_cases']=[]
for variant in ['baseline','native']:
 cases=json.loads((O/variant/'palette-active-cases.json').read_text())['cases'];assert len(cases)==4 and all(c['matches'] and c['actual']==c['expected'] for c in cases)
 if variant=='baseline':baseline_cases=cases
 else:assert cases==baseline_cases
result['active_palette_cases']=baseline_cases
primary_evidence=json.loads((O/'primary-timing-field-evidence.json').read_text());game=(R/'coverage/ghidra-input/GAME-section-00-80195800.bin').read_bytes();assert hashlib.sha256(game).hexdigest()==primary_evidence['game_sha256']
for e in primary_evidence['original_opcodes_verified']:assert struct.unpack_from('<I',game,int(e['pc'],16)-0x80195800)[0]==int(e['opcode'],16)
result['additional_record_checks']=[]
for stage in ['gameplay-idle','gameplay-right','gameplay-left','gameplay-settled']:
 record={}
 for name in ['small-records','palette-records','primary-controls','palette-tables','primary-records','sequence-records']:
  a=(O/'baseline'/f'{stage}-{name}.bin').read_bytes();b=(O/'native'/f'{stage}-{name}.bin').read_bytes();assert len(a)==len(b)
  record[name]={'bytes':len(a),'identical':a==b,'different_bytes':sum(x!=y for x,y in zip(a,b))}
  if name!='primary-records':assert a==b,(stage,name)
  else:
   differences=[{'record':i//320,'offset':hex(i%320),'baseline':x,'native':y} for i,(x,y) in enumerate(zip(a,b)) if x!=y]
   assert all(int(d['offset'],16) in (0x4a,0x12a) for d in differences),(stage,differences)
   record[name].update(differences=differences,non_timing_bytes_identical=True,field_evidence='primary-timing-field-evidence.json')
  if name=='sequence-records':assert not any(a[i*16]&1 for i in range(8))
  if name=='small-records':assert not any(a[i*0x74] for i in range(20))
  if name=='palette-records':assert not any(a[i*12]&1 for i in range(32))
 result['additional_record_checks'].append({'stage':stage,'buffers':record})
result['limitations']+=['The natural route has one primary record and inactive palette/small-record pools; active small-record callbacks and secondary primary-record branches remain untested.','Four synthetic palette cases test type 0 color and bit15 paths; completion flags, invalid divisors and other descriptor types are not runtime validated.','Primary-record differences are confined to verified countdown/counter fields 0x4A and 0x12A; all other bytes match. Different frame timings prevent a full byte-equivalence assertion.']
result['observed_primary_callbacks']=[]
for stage in ['gameplay-idle','gameplay-right','gameplay-left','gameplay-settled']:
 a=json.loads((O/'baseline'/f'{stage}-primary-callback.json').read_text());b=json.loads((O/'native'/f'{stage}-primary-callback.json').read_text());assert a==b,(stage,a,b)
 assert struct.unpack_from('<I',game,int(a['table_entry'],16)-0x80195800)[0]==int(a['target'],16)
 result['observed_primary_callbacks'].append(dict(stage=stage,**a))
result['limitations']+=['The eight sequence records are inactive on this route; active sequence updates remain untested.','The motion-command dispatcher is exercised but not every command class or helper branch is runtime validated.']
(O/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS: three guarded native primary/motion helpers, prior entries and inputs retained, twelve state checkpoints, screenshot comparison, copied-save load, four active palette cases, Ghidra names and unchanged original cards.')
print('Native entries observed at least:',counts)
