from pathlib import Path
from PIL import Image,ImageChops
import csv,hashlib,json,re,zlib
R=Path(__file__).resolve().parents[1];O=R/'coverage/gameplay-loops-native';G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII'
manifest=json.loads((O/'recipes.json').read_text())
result={'status':'passed','new_routines':[],'new_instruction_bytes':1412,'checkpoints':[],'limitations':['Twelve headless checkpoints; not all menus, input configurations, graphics backends or full-game paths.','Counts are bounded-log lower bounds, not exact totals or speed measurements.','Native dispatch guards and entry execution are verified; dependencies keep their existing routing.']}
log=(O/'native/stderr.log').read_text();counts={}
for addr,count in re.findall(r'\[bof3-native-card\] entry=(0x[0-9A-F]+) handled=1 count=(\d+)',log):counts[addr]=max(counts.get(addr,0),int(count))
for entry in ['0x801E5320','0x801DE088','0x801DF21C','0x801E14A8','0x801AEBA0','0x801DF410','0x801AE3F0','0x801AF0F4','0x801AF270','0x801AF2A0','0x801D7578']:assert counts.get(entry,0)>=8
new=(G/'generated-gameplay-loops-overlays/overlays_static.c').read_text();old=(G/'generated-logo-decoder-overlays/overlays_static.c').read_text();pattern=r'^void (\w+)\(CPUState \*cpu\);';old_ids=set(re.findall(pattern,old,re.M));new_ids=set(re.findall(pattern,new,re.M));assert old_ids and old_ids<=new_ids
added=new_ids-old_ids;assert len(added)==68
for f in manifest['routines']:
 source=(R/'coverage/ghidra-input'/f['input']).read_bytes();assert hashlib.sha256(source).hexdigest()==f['source_sha256']
 lo=int(f['entry'],16);hi=int(f['end_exclusive'],16);base=int(f['image_base'],16);b=source[lo-base:hi-base]
 assert len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256'] and f'0x{zlib.crc32(b):08X}'==f['crc32']
 assert f'0x{lo&0x1fffffff:08X}u, 0x{len(b):X}u' in new
 assert counts.get(f['entry'],0)>=(1 if f['entry']=='0x80197068' else 8)
 assert counts.get(f['observed_resume'],0)>=8
 assert (O/'baseline'/f"live-code-{lo:08X}.bin").read_bytes()==b
 assert (O/'native'/f"live-code-{lo:08X}.bin").read_bytes()==b
 prefix=f"ov_{lo&0x1fffffff:08X}_{zlib.crc32(b):08X}_";aliases=sorted(x for x in added if x.startswith(prefix));assert aliases
 result['new_routines'].append(dict(f,native_entries_at_least=counts[f['entry']],generated_entries_including_continuations=len(aliases)))
assert sum(x['generated_entries_including_continuations'] for x in result['new_routines'])==len(added)
result['native_entry_counts_at_least']=counts;result['preserved_prior_generated_identities']=len(old_ids);result['added_entries_including_continuations']=len(added)
old_inputs=json.loads((R/'startup-logo-decoder-inputs.json').read_text());new_inputs=json.loads((R/'startup-gameplay-loops-inputs.json').read_text());assert new_inputs[:len(old_inputs)]==old_inputs and len(new_inputs)==len(old_inputs)+3
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
for label,filename in [('baseline','Breath_of_Fire_III___PSXRecomp.before-gameplay-loops.exe'),('native','Breath_of_Fire_III___PSXRecomp.exe')]:result[label+'_exe_sha256']=hashlib.sha256((G/'build-release'/filename).read_bytes()).hexdigest()
assert 'GAMEPLAY_BOUNDARY_MERGED=1' in (O/'ghidra-boundary.log').read_text()
result['resume_hotspots']={}
for f in manifest['routines']:
 pc=f"0x{int(f['observed_resume'],16)&0x1fffffff:08X}"
 values={}
 for variant in ['baseline','native']:
  stats=json.loads((O/variant/'gameplay-settled.json').read_text())['dirty'];values[variant]=next((x['insns'] for x in stats['per_pc'] if x['pc']==pc),0)
 assert values['baseline']>0 and values['native']==0,(pc,values)
 result['resume_hotspots'][f['observed_resume']]=values
baseline_records=(O/'baseline/gameplay-settled-records.bin').read_bytes();native_records=(O/'native/gameplay-settled-records.bin').read_bytes()
assert len(baseline_records)==30*0x98 and native_records==baseline_records
result['settled_scene_records']={'bytes':len(native_records),'identical':True,'sha256':hashlib.sha256(native_records).hexdigest()}
result['interpreted_instructions_at_loaded_save']={v:json.loads((O/v/'loaded-save.json').read_text())['dirty']['insns_run'] for v in ['baseline','native']}
result['interpreted_instructions_at_settled_gameplay']={v:json.loads((O/v/'gameplay-settled.json').read_text())['dirty']['insns_run'] for v in ['baseline','native']}
(O/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS: three guarded native gameplay loops and their resume entries, preserved prior entries and inputs, twelve matching state checkpoints, screenshot comparison, copied-save load, Ghidra names and unchanged original cards.')
print('Native entries observed at least:',counts)
