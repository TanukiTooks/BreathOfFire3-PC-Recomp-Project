from pathlib import Path
import json,hashlib
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parents[1];G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII';T=R/'coverage/title-footer';D=R/'coverage/widescreen-terrain-release'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(name,value):assert value,name;checks.append(name)
base=T/'baseline-wide-4x-release';new=T/'native-wide-4x-release';missing=T/'missing-wide-4x-release'
for frame in [1500,1750,1900,2200,2600]:
 a=np.array(Image.open(base/f'canonical-{frame}.png'));b=np.array(Image.open(new/f'canonical-{frame}.png'));m=np.array(Image.open(missing/f'canonical-{frame}.png'))
 check(f'missing-image original canonical frame {frame}',np.array_equal(a,m))
 check(f'only footer affects canonical frame {frame}',np.array_equal(a[:184],b[:184]))
for label in ['1900','2200','2600','start-menu','card']:
 a=np.frombuffer((base/f'{label}.vram').read_bytes(),dtype='<u2').reshape(512,1024);b=np.frombuffer((new/f'{label}.vram').read_bytes(),dtype='<u2').reshape(512,1024)
 check(f'texture VRAM unchanged {label}',np.array_equal(a[:,512:],b[:,512:]))
for name in ['native-plain-1x-release','native-wide-4x-release','baseline-wide-4x-release','missing-wide-4x-release','original-plain-1x-release']:
 p=T/name;info=json.loads((p/'complete.json').read_text());run=json.loads((p/'run.json').read_text());check(name+' completed',info['complete']);check(name+' original cards preserved',run['original_cards_unchanged'])
 if not name.startswith('baseline'):check(name+' tested final executable',run['exe_sha256']==sha(G/'build-release/Breath_of_Fire_III___PSXRecomp.exe'))
check('missing footer asset isolated from production',not (missing/'runtime/assets/title/press-start.png').exists() and (G/'build-release/assets/title/press-start.png').exists())
(T/'validation.json').write_text(json.dumps({'status':'passed','checks':checks,'runtime_scope':'OpenGL 4:3 at 1x and 16:9 at 4x; title fade, Start pulse, Start menu and card screen; missing one footer PNG and explicit original-footer override. Canonical captures exclude host artwork; presentation captures visually inspected.', 'exe_sha256':sha(G/'build-release/Breath_of_Fire_III___PSXRecomp.exe')},indent=2),encoding='utf-8')
rows=json.loads((D/'scene-measurements.json').read_text());stationary={r['label']:r for r in rows}
assert [(stationary[n]['active_tiles'],stationary[n]['terrain_wall_quads'],stationary[n]['edge_black_pixels']) for n in ['wide-baseline','wide-native','wide-interpreted','wide-restored']]==[(630,646,9114),(791,813,0),(791,813,0),(791,813,0)]
a=(D/'wide-baseline-camera.bin').read_bytes();b=(D/'wide-native-camera.bin').read_bytes();diff=[hex(0x801492d8+i) for i,(x,y) in enumerate(zip(a,b)) if x!=y];assert set(diff)<=set(['0x80149334','0x80149335'])
assert all(r['aborts']==0 and r['original_cull_words']=='32004224ffff4230a501422c09004010' for r in rows)
plain=json.loads((D/'plain-native-metrics.json').read_text());assert plain['active_tiles']==630 and plain['aborts']==0
(D/'validation.json').write_text(json.dumps({'status':'passed','stationary_original_new_agreement':True,'camera_changes_only_allocator_index':diff,'rows':rows,'plain_native':plain,'interpreter':json.loads((D/'interpreter-agreement.json').read_text()),'preserved':json.loads((D/'preserved-files.json').read_text()),'scope':'Camp interior to Yrall map; stationary A/B, forced interpreter A/B/A and short movement checks. Shoulder-button attempts did not rotate this map camera. Not a whole-game culling/allocator audit; oracle source compile-checked only.'},indent=2),encoding='utf-8')
print('PASS:',len(checks),'title checks; terrain baseline/native/fallback comparison; 4:3 terrain identity.')
