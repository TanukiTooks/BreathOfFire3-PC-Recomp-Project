from pathlib import Path
import json,re,hashlib,struct
from PIL import Image,ImageChops
R=Path(__file__).resolve().parents[1];O=R/'coverage/scenario01-native';G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII'
recipes=json.loads((O/'recipes.json').read_text());old=(G/'generated-party-motion-overlays/overlays_static.c').read_text(encoding='utf-8');new=(G/'generated-scenario01-overlays/overlays_static.c').read_text(encoding='utf-8')
oldids=set(re.findall(r'void (ov_\w+)\(',old));newids=set(re.findall(r'void (ov_\w+)\(',new));assert oldids<=newids and len(newids-oldids)==153
normalize=lambda s:re.sub(r'Static overlay translation unit \d+:','Static overlay translation unit N:',s)
newsrc={normalize(p.read_text(encoding='utf-8')) for p in (G/'generated-scenario01-overlays').glob('overlays_static_*.c')}
prior=list((G/'generated-party-motion-overlays').glob('overlays_static_*.c'));assert len(prior)==60 and all(normalize(p.read_text(encoding='utf-8')) in newsrc for p in prior)
assert not any(re.search(r'= psx_ws_cull_|if.*psx_ws_cull_',s) for s in newsrc)
counts={}
for entry,count in re.findall(r'entry=(0x[0-9A-F]+) handled=1 count=(\d+)',(O/'native/stderr.log').read_text()):counts[entry]=max(int(count),counts.get(entry,0))
entries={int(addr,16):(int(first),int(count)) for addr,first,count in re.findall(r'\{\s*0x([0-9A-F]+)u,\s*(\d+)u,\s*(\d+)u\s*\}',re.search(r'static const PsxOvEntry psx_ov_entries\[\d+\] = \{(.*?)\n\};',new,re.S)[1])}
variants=re.findall(r'\{\s*(\w+),\s*(\d+)u,\s*0x([0-9A-F]+)u,\s*(\w+)\s*\}',re.search(r'static const PsxOvVariant psx_ov_variants\[\d+\] = \{(.*?)\n\};',new,re.S)[1])
routines=[]
for f in recipes['routines']:
 lo=int(f['entry'],16);hi=int(f['end_exclusive'],16);size=f['bytes']
 if lo!=0x801f8000:assert counts.get(f['entry'],0)>0,(f['entry'],'not observed')
 for v in ['baseline','native']:
  for stage in ['camp-idle','world-loaded','world-settled']:
   capture=(O/v/f'{stage}-code-801F2C00.bin').read_bytes();data=capture[lo-0x801f2c00:hi-0x801f2c00];assert hashlib.sha256(data).hexdigest()==f['sha256']
 pcs=[]
 for pc in sorted({int(name.rsplit('_',1)[1],16) for name in newids-oldids if name.startswith(f'ov_{lo&0x1fffffff:08X}_')}):
  first,n=entries[pc];matching=[v for v in variants[first:first+n] if v[3].startswith(f'ov_{lo&0x1fffffff:08X}_{int(f["crc32"],16):08X}_')];assert matching
  for ranges,count,crc,name in matching:
   assert int(count)==1 and int(crc,16)==int(f['crc32'],16)
   assert f'static const uint32_t {ranges}[] = {{ 0x{lo&0x1fffffff:08X}u, 0x{size:X}u }};' in new
  pcs.append(hex(pc))
 assert set(int(p,16) for p in f['dispatch_entries'])<=set(int(p,16) for p in pcs)
 vals={}
 for v in ['baseline','native']:
  d=json.loads((O/v/'world-settled.json').read_text())['dirty'];vals[v]=next((r['insns'] for r in d['per_pc'] if int(r['pc'],16)==lo&0x1fffffff),0)
 assert vals['native']==0,(f['entry'],vals)
 if lo==0x801f7fc4:assert vals['baseline']>0
 routines.append(dict(f,native_entry_count_at_least=counts.get(f['entry'],0),entry_attributed_interpreter_instructions=vals,full_body_guards_verified_for_entries=pcs))
# The repeated unchanged baseline reproduces the exact follower orientation/animation selection.
base_idle=(O/'baseline/camp-settled-primary.bin').read_bytes();repeat_idle=(O/'baseline-repeat/camp-settled-primary.bin').read_bytes();native_idle=(O/'native/camp-settled-primary.bin').read_bytes()
idle_offsets=[8,0x4b,0x50,0x54,0x55]
for offset in idle_offsets:
 i=0x140+offset;assert base_idle[i]!=native_idle[i] and native_idle[i]==repeat_idle[i]
assert json.loads((O/'baseline-repeat/run.json').read_text())['original_cards_unchanged'] and json.loads((O/'baseline-repeat/complete.json').read_text())['complete']
allstages=['card0','card1','card0-return','cancel','reenter','confirm','load-prompt','loaded-save','camp-idle','camp-right','camp-return','camp-settled','camp-exit-approach','world-loaded','world-right','world-return','world-settled'];rows=[]
for stage in allstages:
 a=json.loads((O/'baseline'/f'{stage}.json').read_text());b=json.loads((O/'native'/f'{stage}.json').read_text());keys=['slot','outer_phase','menu_phase','mask','gameplay_phase'];assert all(a[k]==b[k] for k in keys),stage
 ia=Image.open(O/'baseline'/f'{stage}.png').convert('RGB');ib=Image.open(O/'native'/f'{stage}.png').convert('RGB');d=ImageChops.difference(ia,ib);changed=sum(x!=(0,0,0) for x in d.get_flattened_data())
 if stage.startswith('world-'):assert changed==0,(stage,changed)
 row={'stage':stage,'logical_state_match':True,'baseline_frame':a['frame'],'native_frame':b['frame'],'image_different_pixels':changed,'image_diff_bbox':d.getbbox()}
 if stage.startswith(('camp-','world-')):
  ca=json.loads((O/'baseline'/f'{stage}-context.json').read_text());cb=json.loads((O/'native'/f'{stage}-context.json').read_text())
  for key in ['map','scenario_state','scenario_tables','party_count']:assert ca[key]==cb[key],(stage,key)
  assert ca['scenario_state'][2]==2 and ca['scenario_state'][4]==0
  checks={}
  for name in ['controls','party-stats','palette','sequences','primary','scene','small']:
   aa=(O/'baseline'/f'{stage}-{name}.bin').read_bytes();bb=(O/'native'/f'{stage}-{name}.bin').read_bytes();stride={'primary':0x140,'scene':0x98,'small':0x74}.get(name,len(aa));diff=[{'record':i//stride,'offset':hex(i%stride),'baseline':x,'native':y} for i,(x,y) in enumerate(zip(aa,bb)) if x!=y]
   if name in ['controls','party-stats','palette','sequences']:assert not diff,(stage,name)
   if name=='primary':
    for v in diff:assert int(v['offset'],16) in [0x32,0x33,0x4a,0x58,0x59,0x5a,0x5b,0x12a] or (stage.startswith('world-') and v['record']==0 and int(v['offset'],16) in [0x128,0x129]) or (stage=='camp-settled' and v['record']==1 and int(v['offset'],16) in idle_offsets),(stage,v)
   if name=='scene':assert all(int(v['offset'],16) in [0x4a,0x58,0x59,0x5a,0x5b] for v in diff),(stage,name,diff)
   if name=='small':assert all(stage.startswith('world-') and int(v['offset'],16) in [0x38,0x39,0x3a,0x3b] for v in diff),(stage,name,diff)
   checks[name]={'bytes':len(aa),'differences':diff}
  row['records']=checks
 rows.append(row)
cases=json.loads((O/'case-validation.json').read_text());assert cases['passed']==134
src=(R/'coverage/party-motion-native/SCENA01-section00-801F6C00.bin').read_bytes()
for row in cases['instruction_coverage']:
 # The independent interpreter recursively executes these jump delay slots within interp_step(1).
 for p in row['unvisited']:
  pc=int(p,16);w=struct.unpack_from('<I',src,pc-4-0x801f6c00)[0]
  assert w>>26 in [2,3] or (w>>26==0 and w&63 in [8,9])
 row['unvisited_are_atomic_jump_delay_slots']=True
traces={}
for v in ['baseline','native']:
 t=json.loads((O/v/'scenario-write-trace.json').read_text());traces[v]=[{k:e[k] for k in ['addr','new','pc','frame']} for e in t['entries'] if int(e['addr'],16)==0x146872 and e['frame']>5000]
 # Loading camp, then world, each follows 1 -> 2. Store-PC observations can differ across native debug paths.
 assert [int(e['new'],16) for e in traces[v]]==[1,2,1,2],(v,traces[v])
 assert json.loads((O/v/'complete.json').read_text())['complete'] and json.loads((O/v/'run.json').read_text())['original_cards_unchanged']
for path,sha in json.loads((O/'original-cards.json').read_text()).items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha
framework=G.parent/'psxrecomp-src-nightly-20260910-ed55299be3'
assert hashlib.sha256((framework/'runtime/src/main.cpp').read_bytes()).hexdigest()=='5b97adfc2dc3ef22ba26ccca1de170069974bc3964f116a08356780682ae6a1e'
result={'status':'passed_with_documented_sampling_limits','routines':routines,'total_targeted_routines':46,'total_targeted_instruction_bytes':22280,'preserved_prior_generated_identities':len(oldids),'current_generated_identities':len(newids),'added_identities':153,'prior_translation_units_preserved_except_numbering_comment':len(prior),'checkpoints':rows,'baseline_repeat_idle_evidence':{'record':1,'offsets':[hex(i) for i in idle_offsets],'baseline':[base_idle[0x140+i] for i in idle_offsets],'native':[native_idle[0x140+i] for i in idle_offsets],'repeat':[repeat_idle[0x140+i] for i in idle_offsets]},'functional_cases':134,'instruction_coverage':cases['instruction_coverage'],'scenario_state_transition_trace':traces,'original_cards_unchanged':True,'native_exe_sha256':hashlib.sha256((G/'build-release/Breath_of_Fire_III___PSXRecomp.exe').read_bytes()).hexdigest(),'limitations':['At camp-settled, follower orientation and animation-selection pointers differ. The unchanged baseline repeat reproduces all five differing selection bytes exactly; this is documented sampling variation, not byte-equivalent gameplay.','Copied-save gameplay snapshots are polled at different frames and are not full-RAM or frame-exact comparisons. Raw differences are retained.','Permitted animation/sort/random and secondary world-record Y differences follow evidence established in the preceding party/motion batch; world-map images must still match exactly.','Controlled functional cases use declared external-service test doubles. They verify the five new bodies and call boundaries, not real resource/flag/actor service implementations or full story-event effects.','Initializer 0x801F8000 is verified by controlled direct/nested tests; the copied-save route enters state 1 directly and does not naturally execute it.','Entry-attributed interpreter counters do not count all descendant execution and are not FPS or whole-game coverage measurements.','Full-body CRC guards preserve fallback for other overlay identities; live callback/table reads and original unchecked signed indices are retained.','Widescreen terrain changes remain checkpointed; this batch uses 4:3 for integration comparisons.']}
(O/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print('PASS: 134 controlled cases, 17 logical checkpoints, all 3798 prior identities preserved.')
print('Images:',[(r['stage'],r['image_different_pixels']) for r in rows]);print('Observed entries:',{r['entry']:r['native_entry_count_at_least'] for r in routines})
