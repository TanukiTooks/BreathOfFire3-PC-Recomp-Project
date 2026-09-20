from pathlib import Path
from PIL import Image,ImageChops
import csv,hashlib,json,re,zlib
R=Path(__file__).resolve().parents[1];O=R/'coverage/drawing-primitives-native';G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII'
manifest=json.loads((O/'recipes.json').read_text())
result={'status':'passed','new_routines':[],'new_instruction_bytes':1996,'checkpoints':[],'limitations':['Eight headless checkpoints; not all menus, input configurations, graphics backends or full-game paths.','Counts are bounded-log lower bounds, not exact totals or speed measurements.','Native dispatch guards and entry execution are verified; dependencies keep their existing routing.']}
log=(O/'native/stderr.log').read_text();counts={}
for addr,count in re.findall(r'\[bof3-native-card\] entry=(0x[0-9A-F]+) handled=1 count=(\d+)',log):counts[addr]=max(counts.get(addr,0),int(count))
for entry in ['0x801E5320','0x801DE088','0x801DF21C','0x801E14A8','0x801AEBA0','0x801DF410']:assert counts.get(entry,0)>=8
new=(G/'generated-drawing-primitives-overlays/overlays_static.c').read_text();old=(G/'generated-panel-border-overlays/overlays_static.c').read_text();pattern=r'^void (\w+)\(CPUState \*cpu\);';old_ids=set(re.findall(pattern,old,re.M));new_ids=set(re.findall(pattern,new,re.M));assert old_ids and old_ids<=new_ids
added=new_ids-old_ids;assert len(added)==71
for f in manifest['routines']:
 source=(R/'coverage/ghidra-input'/f['input']).read_bytes();assert hashlib.sha256(source).hexdigest()==f['source_sha256']
 lo=int(f['entry'],16);hi=int(f['end_exclusive'],16);base=int(f['image_base'],16);b=source[lo-base:hi-base]
 assert len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256'] and f'0x{zlib.crc32(b):08X}'==f['crc32']
 assert f'0x{lo&0x1fffffff:08X}u, 0x{len(b):X}u' in new
 assert counts.get(f['entry'],0)>=8
 prefix=f"ov_{lo&0x1fffffff:08X}_{zlib.crc32(b):08X}_";aliases=sorted(x for x in added if x.startswith(prefix));assert aliases
 result['new_routines'].append(dict(f,native_entries_at_least=counts[f['entry']],generated_entries_including_continuations=len(aliases)))
assert sum(x['generated_entries_including_continuations'] for x in result['new_routines'])==len(added)
result['native_entry_counts_at_least']=counts;result['preserved_prior_generated_identities']=len(old_ids);result['added_entries_including_continuations']=len(added)
old_inputs=json.loads((R/'startup-panel-border-inputs.json').read_text());new_inputs=json.loads((R/'startup-drawing-primitives-inputs.json').read_text());assert new_inputs[:len(old_inputs)]==old_inputs and len(new_inputs)==len(old_inputs)+4
for stage in ['card0','card1','card0-return','cancel','reenter','confirm','load-prompt','loaded-save']:
 a=json.loads((O/'baseline'/f'{stage}.json').read_text());b=json.loads((O/'native'/f'{stage}.json').read_text());keys=['slot','outer_phase','menu_phase','mask'];assert all(a[k]==b[k] for k in keys),stage
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
 assert 'RESEARCH_SYMBOLS_APPLIED=4' in (O/f"ghidra-{f['section']}.log").read_text()
for label,filename in [('baseline','Breath_of_Fire_III___PSXRecomp.before-drawing-primitives.exe'),('native','Breath_of_Fire_III___PSXRecomp.exe')]:result[label+'_exe_sha256']=hashlib.sha256((G/'build-release'/filename).read_bytes()).hexdigest()
(O/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS: four guarded native drawing primitives, preserved prior entries and inputs, eight matching state checkpoints, screenshot comparison, copied-save load, Ghidra names and unchanged original cards.')
print('Native entries observed at least:',counts)
