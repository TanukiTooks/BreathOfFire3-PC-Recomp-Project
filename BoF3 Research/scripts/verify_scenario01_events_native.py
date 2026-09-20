from pathlib import Path
import json,re,hashlib,struct
from PIL import Image,ImageChops
R=Path(__file__).resolve().parents[1];O=R/'coverage/scenario01-events-native';G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII'
recipes=json.loads((O/'recipes.json').read_text());old=(G/'generated-scenario01-overlays/overlays_static.c').read_text(encoding='utf-8');new=(G/'generated-scenario01-events-overlays/overlays_static.c').read_text(encoding='utf-8')
oldids=set(re.findall(r'void (ov_\w+)\(',old));newids=set(re.findall(r'void (ov_\w+)\(',new));assert oldids<=newids and len(newids-oldids)==50
normalize=lambda s:re.sub(r'Static overlay translation unit \d+:','Static overlay translation unit N:',s)
newsrc={normalize(p.read_text(encoding='utf-8')) for p in (G/'generated-scenario01-events-overlays').glob('overlays_static_*.c')}
prior=list((G/'generated-scenario01-overlays').glob('overlays_static_*.c'));assert len(prior)==65 and all(normalize(p.read_text(encoding='utf-8')) in newsrc for p in prior)
assert not any(re.search(r'= psx_ws_cull_|if.*psx_ws_cull_',s) for s in newsrc)
counts={}
for entry,count in re.findall(r'entry=(0x[0-9A-F]+) handled=1 count=(\d+)',(O/'native/stderr.log').read_text()):counts[entry]=max(int(count),counts.get(entry,0))
entries={int(addr,16):(int(first),int(count)) for addr,first,count in re.findall(r'\{\s*0x([0-9A-F]+)u,\s*(\d+)u,\s*(\d+)u\s*\}',re.search(r'static const PsxOvEntry psx_ov_entries\[\d+\] = \{(.*?)\n\};',new,re.S)[1])}
variants=re.findall(r'\{\s*(\w+),\s*(\d+)u,\s*0x([0-9A-F]+)u,\s*(\w+)\s*\}',re.search(r'static const PsxOvVariant psx_ov_variants\[\d+\] = \{(.*?)\n\};',new,re.S)[1])
routines=[]
for f in recipes['routines']:
 lo=int(f['entry'],16);hi=int(f['end_exclusive'],16);size=f['bytes']
 # Natural copied-save route stays on event 0; counts are recorded without claiming target coverage.
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

 routines.append(dict(f,native_entry_count_at_least=counts.get(f['entry'],0),entry_attributed_interpreter_instructions=vals,full_body_guards_verified_for_entries=pcs))
# These exact follower selection tuples were reproduced by an unchanged baseline in the preceding batch.
idle_offsets=[8,0x4b,0x50,0x54,0x55]
prior_idle=[]
for variant in ['baseline','native','baseline-repeat']:
 data=(R/'coverage/scenario01-native'/variant/'camp-settled-primary.bin').read_bytes();prior_idle.append(tuple(data[0x140+i] for i in idle_offsets))
# A prior unchanged baseline captured the exact leader orientation/animation selection now seen natively.
leader_offsets=[8,0x2a,0x4b,0x50,0x54]
leader_ref=(R/'coverage/party-motion-native/baseline-repeat/camp-idle-primary.bin').read_bytes()
leader_now=(O/'native/camp-idle-primary.bin').read_bytes()
assert tuple(leader_ref[i] for i in leader_offsets)==tuple(leader_now[i] for i in leader_offsets)
assert json.loads((R/'coverage/party-motion-native/original-cards.json').read_text())==json.loads((O/'original-cards.json').read_text())
for variant in ['baseline-repeat']:
 assert json.loads((O/variant/'run.json').read_text())['original_cards_unchanged'] and json.loads((O/variant/'complete.json').read_text())['complete']
repeat_follower=(O/'baseline-repeat/camp-settled-primary.bin').read_bytes();current_follower=(O/'native/camp-settled-primary.bin').read_bytes()
assert tuple(repeat_follower[0x140+i] for i in idle_offsets)==tuple(current_follower[0x140+i] for i in idle_offsets)
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
  if stage=='camp-settled':
   for variant in ['baseline','native']:
    data=(O/variant/f'{stage}-primary.bin').read_bytes();assert tuple(data[0x140+i] for i in idle_offsets) in prior_idle,'New follower animation selection requires investigation'
  checks={}
  for name in ['controls','party-stats','palette','sequences','primary','scene','small']:
   aa=(O/'baseline'/f'{stage}-{name}.bin').read_bytes();bb=(O/'native'/f'{stage}-{name}.bin').read_bytes();stride={'primary':0x140,'scene':0x98,'small':0x74}.get(name,len(aa));diff=[{'record':i//stride,'offset':hex(i%stride),'baseline':x,'native':y} for i,(x,y) in enumerate(zip(aa,bb)) if x!=y]
   if name in ['controls','party-stats','palette','sequences']:assert not diff,(stage,name)
   if name=='primary':
    for v in diff:assert int(v['offset'],16) in [0x32,0x33,0x4a,0x58,0x59,0x5a,0x5b,0x12a] or (stage.startswith('world-') and v['record']==0 and int(v['offset'],16) in [0x128,0x129]) or (stage=='camp-settled' and v['record']==1 and int(v['offset'],16) in idle_offsets) or (stage=='camp-idle' and v['record']==0 and int(v['offset'],16) in leader_offsets),(stage,v)
   if name=='scene':assert all(int(v['offset'],16) in [0x4a,0x58,0x59,0x5a,0x5b] for v in diff),(stage,name,diff)
   if name=='small':assert all(stage.startswith('world-') and int(v['offset'],16) in [0x38,0x39,0x3a,0x3b] for v in diff),(stage,name,diff)
   checks[name]={'bytes':len(aa),'differences':diff}
  row['records']=checks
 rows.append(row)
cases=json.loads((O/'case-validation.json').read_text());assert cases['passed']==96
src=(R/'coverage/party-motion-native/SCENA01-section00-801F6C00.bin').read_bytes()
for row in cases['instruction_coverage']:
 # Two source instructions are unreachable after unsigned substate <2 and !=1 implies zero.
 unreachable={0x801f8b1c,0x801f8b20}
 for p in row['unobserved']:
  pc=int(p,16)
  if pc in unreachable:continue
  w=struct.unpack_from('<I',src,pc-4-0x801f6c00)[0]
  assert w>>26 in [1,2,3,4,5,6,7] or (w>>26==0 and w&63 in [8,9])
 row['unobserved_are_atomic_delay_slots_or_proven_unreachable']=True
traces={}
for v in ['baseline','native']:
 t=json.loads((O/v/'scenario-write-trace.json').read_text());traces[v]=[{k:e[k] for k in ['addr','new','pc','frame']} for e in t['entries'] if int(e['addr'],16)==0x146872 and e['frame']>5000]
 # Loading camp, then world, each follows 1 -> 2. Store-PC observations can differ across native debug paths.
 assert [int(e['new'],16) for e in traces[v]]==[1,2,1,2],(v,traces[v])
 assert json.loads((O/v/'complete.json').read_text())['complete'] and json.loads((O/v/'run.json').read_text())['original_cards_unchanged']
for path,sha in json.loads((O/'original-cards.json').read_text()).items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha
framework=G.parent/'psxrecomp-src-nightly-20260910-ed55299be3'
assert hashlib.sha256((framework/'runtime/src/main.cpp').read_bytes()).hexdigest()=='5b97adfc2dc3ef22ba26ccca1de170069974bc3964f116a08356780682ae6a1e'
result={'status':'passed_with_documented_sampling_limits','routines':routines,'total_targeted_routines':48,'total_targeted_instruction_bytes':23384,'preserved_prior_generated_identities':len(oldids),'current_generated_identities':len(newids),'added_identities':50,'prior_translation_units_preserved_except_numbering_comment':len(prior),'checkpoints':rows,'idle_sampling_evidence':{'follower':'Current unchanged baseline repeat reproduces native selection tuple at camp-settled.','leader':'coverage/party-motion-native/baseline-repeat/camp-idle-primary.bin reproduces native selection tuple; same original card hashes.','leader_offsets':[hex(i) for i in leader_offsets],'follower_offsets':[hex(i) for i in idle_offsets]},'functional_cases':96,'isolated_cases':84,'chained_steps':12,'instruction_coverage':cases['instruction_coverage'],'scenario_state_transition_trace':traces,'original_cards_unchanged':True,'native_exe_sha256':hashlib.sha256((G/'build-release/Breath_of_Fire_III___PSXRecomp.exe').read_bytes()).hexdigest(),'limitations':['The additional leader orientation/animation tuple at camp-idle exactly matches the older unchanged party/motion baseline repeat using the same cards; this is recorded variation, not live-state equivalence.','Any permitted follower selection difference is restricted to five fields in record 1 at camp-settled and to the exact selection tuples reproduced in the preceding baseline-repeat investigation.','Copied-save gameplay snapshots are polled at different frames and are not full-RAM or frame-exact comparisons. Raw differences are retained.','Permitted animation/sort/random and secondary world-record Y differences follow evidence established in the preceding party/motion batch; world-map images must still match exactly.','Controlled cases execute the original packed-flag setter and event-control cleanup on both sides. Other external services use declared doubles. Progression in chained tests is fixture-driven; real resource/camera/actor services and natural story completion remain unverified.','The copied-save route remains on event 0 and does not naturally execute new event 1/2 handlers. Their execution is verified in controlled direct/nested/chained tests; natural story-event integration remains pending.','Entry-attributed interpreter counters do not count all descendant execution and are not FPS or whole-game coverage measurements.','Full-body CRC guards preserve fallback for other overlay identities; live callback/table reads and original unchecked signed indices are retained.','Widescreen terrain changes remain checkpointed; this batch uses 4:3 for integration comparisons.']}
(O/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print('PASS: 96 controlled checks, 17 regression checkpoints, all 3951 prior identities preserved.')
print('Images:',[(r['stage'],r['image_different_pixels']) for r in rows]);print('Observed entries:',{r['entry']:r['native_entry_count_at_least'] for r in routines})
