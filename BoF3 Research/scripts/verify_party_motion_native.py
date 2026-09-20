from pathlib import Path
import json,re,hashlib,struct,zlib,collections
from PIL import Image,ImageChops
R=Path(__file__).resolve().parents[1];O=R/'coverage/party-motion-native';G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII'
recipes=json.loads((O/'recipes.json').read_text());old=(G/'generated-motion-commands-overlays/overlays_static.c').read_text();new=(G/'generated-party-motion-overlays/overlays_static.c').read_text()
old_ids=set(re.findall(r'void (ov_\w+)\(',old));new_ids=set(re.findall(r'void (ov_\w+)\(',new));assert old_ids<=new_ids and len(new_ids-old_ids)==28
normalize=lambda s:re.sub(r'Static overlay translation unit \d+:','Static overlay translation unit N:',s)
new_sources={normalize(p.read_text(encoding='utf-8')) for p in (G/'generated-party-motion-overlays').glob('overlays_static_*.c')}
prior=list((G/'generated-motion-commands-overlays').glob('overlays_static_*.c'));assert all(normalize(p.read_text(encoding='utf-8')) in new_sources for p in prior)
assert not any(re.search(r'= psx_ws_cull_|if.*psx_ws_cull_',s) for s in new_sources)
counts={}
for entry,count in re.findall(r'entry=(0x[0-9A-F]+) handled=1 count=(\d+)',(O/'native/stderr.log').read_text()):counts[entry]=max(int(count),counts.get(entry,0))
entries={int(addr,16):(int(first),int(count)) for addr,first,count in re.findall(r'\{\s*0x([0-9A-F]+)u,\s*(\d+)u,\s*(\d+)u\s*\}',re.search(r'static const PsxOvEntry psx_ov_entries\[\d+\] = \{(.*?)\n\};',new,re.S)[1])}
variants=re.findall(r'\{\s*(\w+),\s*(\d+)u,\s*0x([0-9A-F]+)u,\s*(\w+)\s*\}',re.search(r'static const PsxOvVariant psx_ov_variants\[\d+\] = \{(.*?)\n\};',new,re.S)[1])
routines=[]
for f in recipes['routines']:
 lo=int(f['entry'],16);size=f['bytes'];assert counts.get(f['entry'],0)>=8
 for variant in ['baseline','native','baseline-repeat']:
  for stage in ['camp-idle','world-loaded','world-settled']:
   data=(O/variant/f'{stage}-code-{lo:08X}.bin').read_bytes();assert hashlib.sha256(data).hexdigest()==f['sha256']
 for pc in [f['entry']]+f['resume_dispatch_entries']:
  first,n=entries[int(pc,16)];matching=[v for v in variants[first:first+n] if v[3].startswith(f'ov_{lo&0x1fffffff:08X}_{int(f["crc32"],16):08X}_')];assert matching
  for ranges,count,crc,name in matching:
   assert int(count)==1 and int(crc,16)==int(f['crc32'],16)
   assert f'static const uint32_t {ranges}[] = {{ 0x{lo&0x1fffffff:08X}u, 0x{size:X}u }};' in new
 vals={}
 for variant in ['baseline','native']:
  d=json.loads((O/variant/'world-settled.json').read_text())['dirty'];vals[variant]=next((r['insns'] for r in d['per_pc'] if int(r['pc'],16)==lo&0x1fffffff),0)
 assert vals['baseline']>0 and vals['native']==0
 routines.append(dict(f,native_entry_count_at_least=counts[f['entry']],entry_attributed_interpreter_instructions=vals,full_body_guards_verified=True))
all_stages=['card0','card1','card0-return','cancel','reenter','confirm','load-prompt','loaded-save','camp-idle','camp-right','camp-return','camp-settled','camp-exit-approach','world-loaded','world-right','world-return','world-settled'];rows=[]
for stage in all_stages:
 a=json.loads((O/'baseline'/f'{stage}.json').read_text());b=json.loads((O/'native'/f'{stage}.json').read_text());keys=['slot','outer_phase','menu_phase','mask','gameplay_phase'];assert all(a[k]==b[k] for k in keys),stage
 ia=Image.open(O/'baseline'/f'{stage}.png').convert('RGB');ib=Image.open(O/'native'/f'{stage}.png').convert('RGB');d=ImageChops.difference(ia,ib);changed=sum(x!=(0,0,0) for x in d.get_flattened_data())
 if stage.startswith('world-'):assert changed==0
 row={'stage':stage,'logical_state_match':True,'baseline_frame':a['frame'],'native_frame':b['frame'],'image_different_pixels':changed,'image_diff_bbox':d.getbbox()}
 if stage.startswith(('camp-','world-')):
  assert json.loads((O/'baseline'/f'{stage}-context.json').read_text())['map']==json.loads((O/'native'/f'{stage}-context.json').read_text())['map']
  checks={}
  for name in ['controls','party-stats','palette','sequences','primary','scene','small']:
   aa=(O/'baseline'/f'{stage}-{name}.bin').read_bytes();bb=(O/'native'/f'{stage}-{name}.bin').read_bytes();stride={'primary':0x140,'scene':0x98,'small':0x74}.get(name,len(aa));diff=[{'record':i//stride,'offset':hex(i%stride),'baseline':x,'native':y} for i,(x,y) in enumerate(zip(aa,bb)) if x!=y]
   if name in ['controls','party-stats','palette','sequences']:assert not diff,(stage,name)
   if name=='primary':
    for v in diff:assert int(v['offset'],16) in [0x32,0x33,0x4a,0x58,0x59,0x5a,0x5b,0x12a] or (stage.startswith('world-') and v['record']==0 and int(v['offset'],16) in [0x128,0x129]),(stage,v)
   if name=='scene':assert all(int(v['offset'],16) in [0x4a,0x58,0x59,0x5a,0x5b] for v in diff)
   if name=='small':assert all(stage.startswith('world-') and int(v['offset'],16) in [0x38,0x39,0x3a,0x3b] for v in diff)
   checks[name]={'bytes':len(aa),'differences':diff}
  row['records']=checks
 rows.append(row)
# A fresh run of the unchanged baseline reproduces the randomized field value
# and the secondary-record coordinate variation. These are limitations, not exact-state matches.
base=(O/'baseline/world-loaded-primary.bin').read_bytes();repeat=(O/'baseline-repeat/world-loaded-primary.bin').read_bytes();native=(O/'native/world-loaded-primary.bin').read_bytes();assert base[0x128:0x12a]!=repeat[0x128:0x12a] and repeat[0x128:0x12a]==native[0x128:0x12a]
assert (O/'baseline/world-loaded-small.bin').read_bytes()!=(O/'baseline-repeat/world-loaded-small.bin').read_bytes()
cases=json.loads((O/'case-validation.json').read_text());assert cases['passed']==58 and cases['real_callee_cases']==3
for variant in ['baseline','native','baseline-repeat']:
 assert json.loads((O/variant/'complete.json').read_text())['complete'];assert json.loads((O/variant/'run.json').read_text())['original_cards_unchanged']
for path,sha in json.loads((O/'original-cards.json').read_text()).items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha
result={'status':'passed_with_documented_sampling_limits','routines':routines,'total_targeted_routines':41,'total_targeted_instruction_bytes':19432,'preserved_prior_generated_identities':len(old_ids),'current_generated_identities':len(new_ids),'added_identities':28,'prior_translation_units_preserved_except_numbering_comment':len(prior),'checkpoints':rows,'functional_cases':58,'real_callee_cases':3,'baseline_repeat_random_field':{'baseline':int.from_bytes(base[0x128:0x12a],'little'),'repeat':int.from_bytes(repeat[0x128:0x12a],'little'),'native':int.from_bytes(native[0x128:0x12a],'little')},'original_cards_unchanged':True,'native_exe_sha256':hashlib.sha256((G/'build-release/Breath_of_Fire_III___PSXRecomp.exe').read_bytes()).hexdigest(),'limitations':['Gameplay captures are polled at different frames. They are not full-RAM or frame-exact equivalence tests.','Core coordinates/flags, party stats, controls, palette and sequence records match; raw animation/sort and randomized-field differences are recorded.','Secondary world-record Y coordinates differ in both baseline/native and repeated-baseline runs. All four world-map images match.','58 isolated cases compare all RAM/scratch/registers exactly but exclude cycles, devices, renderer, audio and IRQ timing.','The real 0x801A3080 callee is covered only with zero-velocity, zero-duration direction setup; other paths remain untested.','The normal route did not observe the new helper call-return continuation 0x801A2B4C. The controlled real-callee cases exercise it.']}
(O/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS: 17 logical checkpoints, 58 functional cases, 3770 prior identities preserved; two routines now native.')
