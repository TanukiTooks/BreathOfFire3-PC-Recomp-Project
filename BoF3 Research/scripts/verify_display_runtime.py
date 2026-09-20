from pathlib import Path
import json,hashlib
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'coverage/display-settings'
result={'status':'passed','logical_states':[],'timers':{},'buffers':[],'presentation':[]}
variants=['crisp-windowed','higher-borderless'];stages=['card0','card1','card0-return','cancel','reenter','confirm','load-prompt','loaded-save','gameplay-idle','gameplay-right','gameplay-left','gameplay-settled']
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
 assert f'internal scale {1 if v==variants[0] else 2}x' in log
 assert ('driver vsync' if v==variants[0] else 'wall-clock pacer') in log
 result['presentation'].append({'variant':v,'size':list(im.size),'palette_cases_passed':4,'opengl_confirmed':True})
assert result['presentation'][0]['size']==[640,480]
assert json.loads((O/'runtime-validation.json').read_text())['original_cards_unchanged']
result['limitations']=['Two actual render configurations; 3x/4x are exposed within runtime limits but not separately playtested.','Window sizing and fullscreen retain 4:3; strict integer fullscreen scaling is not implemented.','Timer checks use debug-frame counts, not display FPS; no new simulation frame rate is enabled.','Audio and controller feel require human playtesting.']
(O/'display-validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('PASS: twelve logical-state comparisons, gameplay buffers, palette outputs, clock cadence and both actual OpenGL configurations.')
