"""Compare real renderer captures and preservation evidence for the menu feature."""
from pathlib import Path
from PIL import Image
import numpy as np
import hashlib,json,difflib
R=Path(__file__).resolve().parents[1];O=R/'coverage/widescreen-menu-background';G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII';F=R.parent/'BoF3 PSXRecomp/psxrecomp-src-nightly-20260910-ed55299be3'
rows=[]
def arr(p):return np.array(Image.open(p).convert('RGB'))
for aspect in ['plain','wide']:
 run=json.loads((O/('native-'+aspect)/'run.json').read_text());assert run['exe_sha256']==hashlib.sha256((G/'build-release/Breath_of_Fire_III___PSXRecomp.exe').read_bytes()).hexdigest()
 assert json.loads((O/('native-'+aspect)/'complete.json').read_text())['complete']
 for label in [*['card-pattern'+str(i) for i in range(4)],'new-game-entry','title-return']:
  base=O/('baseline-'+aspect);native=O/('native-'+aspect)
  a=arr(base/(label+'.png'));b=arr(native/(label+'.png'));changed=np.any(a!=b,axis=2);total=int(changed.sum())
  if label=='new-game-entry':changed[50:90,250:285]=False # animated Ryu preview, frame not synchronised between runs
  assert not changed.any(),(aspect,label,int(changed.sum()))
  if label!='title-return':assert json.loads((base/(label+'.json')).read_text())['code']==json.loads((native/(label+'.json')).read_text())['code']
  rows.append({'aspect':aspect,'label':label,'canonical_changed_pixels':total,'outside_animated_preview_changed_pixels':int(changed.sum())})
wide=[]
for label in [*['card-pattern'+str(i) for i in range(4)],*['name-pattern'+str(i) for i in range(4)]]:
 a=arr(O/'native-wide'/(label+'-present.png'));assert a.shape==(720,1280,3)
 black=[int(np.all(a[:,:150]==0,axis=2).sum()),int(np.all(a[:,1130:]==0,axis=2).sum())];assert black==[0,0],(label,black)
 state=json.loads((O/'native-wide'/(label+'.json')).read_text());assert state['sampled_draw_bytes']<state['draw_arena_capacity']//2
 wide.append({'label':label,'black_side_pixels':black,'sampled_draw_bytes':state['sampled_draw_bytes'],'capacity':state['draw_arena_capacity']})
for label in ['title-return','title-new-game']:
 a=arr(O/'native-wide'/(label+'-present.png'));assert not a[:,:150].any() and not a[:,1130:].any()
originals=json.loads((O/'original-cards.json').read_text());assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in originals.items())
main_sha=hashlib.sha256((F/'runtime/src/main.cpp').read_bytes()).hexdigest();assert main_sha=='5b97adfc2dc3ef22ba26ccca1de170069974bc3964f116a08356780682ae6a1e'
patch=''
for rel in ['runtime/src/gpu.c','runtime/src/mod_runtime.cpp','runtime/include/gpu.h','runtime/include/mod_plugins.h']:
 p=F/rel;patch+=''.join(difflib.unified_diff((O/(p.name+'.before')).read_text(encoding='utf-8').splitlines(True),p.read_text(encoding='utf-8').splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
(O/'framework-menu-frame.patch').write_text(patch,encoding='utf-8')
report={'passed':True,'canonical_comparisons':rows,'wide_backgrounds':wide,'title_pillarbox_restored':True,'live_background_guest_code_unchanged':True,'original_cards_unchanged':True,'turbo_main_cpp_unchanged':True,'exe_sha256':hashlib.sha256((G/'build-release/Breath_of_Fire_III___PSXRecomp.exe').read_bytes()).hexdigest(),'limitations':'1x OpenGL windowed nearest at 1280x720 wide / 960x720 original. Draw usage is sampled, not exhaustive peak allocation. Naming animated preview can differ by frame; other pixels must match.'}
(O/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
