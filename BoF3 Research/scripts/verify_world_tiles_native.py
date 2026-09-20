from pathlib import Path
import hashlib,json,re
from PIL import Image,ImageChops
R=Path(__file__).resolve().parents[1];O=R/'coverage/world-native-investigation';G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII'
read=lambda p:p.read_text(encoding='utf-8')
norm=lambda p:re.sub(r'Static overlay translation unit \d+:','Static overlay translation unit N:',read(p))
old=O/'before-overlays';new=G/'generated-scenario01-events-overlays'
ids=lambda p:set(re.findall(r'void (ov_\w+)\(',read(p)))
oldids=ids(old/'overlays_static.c');newids=ids(new/'overlays_static.c');assert oldids<=newids and len(newids-oldids)==44
newsrc={norm(p) for p in new.glob('overlays_static_*.c')};prior=list(old.glob('overlays_static_*.c'));assert all(norm(p) in newsrc for p in prior)
assert norm(G/'generated-world-tiles-overlays/overlays_static_0000.c') in newsrc
dispatch=read(new/'overlays_static.c')
variants=re.findall(r'\{\s*(\w+),\s*(\d+)u,\s*0x([0-9A-F]+)u,\s*(ov_001F469C_\w+)\s*\}',dispatch)
assert len(variants)==44
for ranges,count,crc,name in variants:
 assert int(count)==1 and int(crc,16)==0xb755b17d
 assert f'static const uint32_t {ranges}[] = {{ 0x001F469Cu, 0x614u }};' in dispatch
stages=['card0','card1','card0-return','cancel','reenter','confirm','load-prompt','loaded-save','camp-idle','camp-right','camp-return','camp-settled','camp-exit-approach','world-loaded','world-right','world-return','world-settled'];rows=[]
for stage in stages:
 a=json.loads(read(O/'baseline'/f'{stage}.json'));b=json.loads(read(O/'native'/f'{stage}.json'))
 for k in ('slot','outer_phase','menu_phase','mask','gameplay_phase'):assert a[k]==b[k],(stage,k)
 assert b['dirty']['aborts']==0
 ia=Image.open(O/'baseline'/f'{stage}.png').convert('RGB');ib=Image.open(O/'native'/f'{stage}.png').convert('RGB');diff=ImageChops.difference(ia,ib)
 pixels=sum(p!=(0,0,0) for p in diff.getdata());row=dict(stage=stage,logical_state_match=True,baseline_frame=a['frame'],native_frame=b['frame'],image_changed_pixels=pixels,image_bbox=diff.getbbox())
 if stage.startswith(('camp-','world-')):
  ca=json.loads(read(O/'baseline'/f'{stage}-context.json'));cb=json.loads(read(O/'native'/f'{stage}-context.json'))
  for k in ('map','scenario_state','scenario_tables','party_count'):assert ca[k]==cb[k],(stage,k)
  for name in ('controls','party-stats','palette','sequences'):
   assert (O/'baseline'/f'{stage}-{name}.bin').read_bytes()==(O/'native'/f'{stage}-{name}.bin').read_bytes(),(stage,name)
 if stage.startswith('world-'):assert pixels==0,(stage,pixels)
 rows.append(row)
def delta(variant):
 a=json.loads(read(O/variant/'camp-settled.json'))['dirty'];b=json.loads(read(O/variant/'world-settled.json'))['dirty']
 old={r['pc']:r['insns'] for r in a['per_pc']}
 return dict(total=b['insns_run']-a['insns_run'],target=sum(r['insns']-old.get(r['pc'],0) for r in b['per_pc'] if 0x1f469c<=int(r['pc'],16)<0x1f4cb0))
before=delta('baseline');after=delta('native');assert before['target']>6000000 and after['target']==0
counts={}
for entry,count in re.findall(r'entry=(0x[0-9A-F]+) handled=1 count=(\d+)',read(O/'native/stderr.log')):counts[entry]=max(int(count),counts.get(entry,0))
assert counts.get('0x801F469C',0)>0 and counts.get('0x801F4968',0)>0
for v in ('baseline','native'):assert json.loads(read(O/v/'run.json'))['original_cards_unchanged'] and json.loads(read(O/v/'complete.json'))['complete']
for path,sha in json.loads(read(O/'original-cards.json')).items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha
assert json.loads(read(O/'case-validation.json'))['passed']==42
result=dict(status='passed_with_polled_animation_sampling_limits',old_bodies_preserved=len(prior),old_identities_preserved=len(oldids),new_identities=len(newids),new_body_bytes=1556,full_body_guarded_identities=44,controlled_cases=42,checkpoints=rows,interpreter_before=before,interpreter_after=after,native_counts={k:counts[k] for k in ('0x801F469C','0x801F4968')},original_cards_unchanged=True,exe_sha256=hashlib.sha256((G/'build-release/Breath_of_Fire_III___PSXRecomp.exe').read_bytes()).hexdigest(),limitations=['This is one AREA033 routine, not all world maps or all gameplay.','Runtime checkpoints are polled at different frames; animated character/menu images can differ.','Headless route tests do not measure presented FPS or audio.','Controlled external rendering services are test doubles; the saved-game route exercises real services.'])
(O/'validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
