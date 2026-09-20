from pathlib import Path
import json,hashlib,sys
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'coverage/widescreen'
result={'status':'passed','logical_states':[],'timers':{},'buffers':[],'presentation':[]}
variant=sys.argv[1] if len(sys.argv)>1 else 'legacy-16-9'
variants=['native-4-3',variant];stages=['card0','card1','card0-return','cancel','reenter','confirm','load-prompt','loaded-save','gameplay-idle','gameplay-right','gameplay-left','gameplay-settled']
for stage in stages:
 a,b=[json.loads((O/v/f'{stage}.json').read_text()) for v in variants]
 for key in ['slot','outer_phase','menu_phase','mask','gameplay_phase']:assert a[key]==b[key],(stage,key)
 result['logical_states'].append({'stage':stage,'matched':True})
for stage in stages[-4:]:
 for name in ['primary-records','small-records','palette-records','primary-controls','palette-tables','sequence-records']:
  a,b=[(O/v/f'{stage}-{name}.bin').read_bytes() for v in variants];assert len(a)==len(b)
  differences=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
  if name=='primary-records':assert all(i%320 in (0x4a,0x12a) for i in differences),(stage,name,differences)
  else:assert not differences,(stage,name)
  result['buffers'].append({'stage':stage,'name':name,'different_bytes':len(differences),'non_timing_bytes_match':True})
for v in variants:
 samples=[json.loads((O/v/f'{s}-timers.json').read_text()) for s in stages[-4:]]
 def ticks(c):return ((c[0]*60+c[1])*60+c[2])*30+c[3]
 for a,b in zip(samples,samples[1:]):
  delta=ticks(b['play_clock_bytes'])-ticks(a['play_clock_bytes']);low=b['before_frame']-a['after_frame'];high=b['after_frame']-a['before_frame'];assert delta>0 and low-1<=delta*2<=high+1
 assert all(s['phase']==0 and s['countdown_bytes']==[0]*8 for s in samples)
 result['timers'][v]={'clock_cadence_preserved':True,'samples':samples}
 palette=json.loads((O/v/'palette-active-cases.json').read_text())['cases'];assert len(palette)==4 and all(c['matches'] for c in palette)
 im=Image.open(O/v/'present.png');assert im.width>=640 and im.height>=480
 log=(O/v/'stdout.log').read_text(encoding='utf-8');assert 'OpenGL context created' in log
 assert f'internal scale {1}x' in log
 assert 'driver vsync' in log
 if v==variants[1]:assert 'mod selected fixed display aspect 16:9' in log and 'native-wide, present 1:1' in log
 result['presentation'].append({'variant':v,'size':list(im.size),'palette_cases_passed':4,'opengl_confirmed':True})
assert [p['size'] for p in result['presentation']]==[[960,720],[1280,720]]
assert json.loads((O/'runtime-validation.json').read_text())['original_cards_unchanged']
result['limitations']=['One indoor save route, boot and save menus only; no battle/world-map/general scene coverage yet.','Legacy textured-edge expansion is a renderer heuristic, not recovered game geometry.','Timing checks are guest-frame cadence; audio and subjective feel need human playtesting.']
result['central_crop_comparison']=[]
from PIL import ImageChops
for stage in stages:
 a=Image.open(O/variants[0]/(stage+'-present.png')).convert('RGB');b=Image.open(O/variants[1]/(stage+'-present.png')).convert('RGB');crop=b.crop((160,0,1120,720));diff=ImageChops.difference(a,crop)
 changed=sum(x!=(0,0,0) for x in diff.get_flattened_data());result['central_crop_comparison'].append({'stage':stage,'changed_pixels':changed,'total_pixels':a.width*a.height})
 for side,box in [('left',(0,0,160,720)),('right',(1120,0,1280,720))]:
  count=sum(x!=(0,0,0) for x in b.crop(box).get_flattened_data())
  result['central_crop_comparison'][-1][side+'_nonblack_pixels']=count
(O/(variant+'-validation.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('PASS: twelve state comparisons, gameplay buffers, palette outputs, clock cadence and native-wide activation.');print(json.dumps(result['central_crop_comparison'],indent=2))
