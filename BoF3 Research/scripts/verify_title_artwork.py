from pathlib import Path
import json,hashlib,difflib
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];W=R.parent;D=R/'coverage/title-artwork';G=W/'BoF3 PSXRecomp/BreathOfFireIII'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pixels(p):return np.array(Image.open(p).convert('RGB'))
def diff(a,b):return int(np.count_nonzero(np.any(a!=b,axis=2)))
report={'final_executable_sha256':sha(G/'build-release/Breath_of_Fire_III___PSXRecomp.exe'),'runs':{},'comparisons':{},'preserved':{},'visual_checks':{},'notes':[]}
for p in sorted(D.glob('*/run.json')):
 run=json.loads(p.read_text(encoding='utf-8'));assert run['original_cards_unchanged'];assert run['exe_sha256']==sha(p.parent/'runtime/game.exe')
 if (p.parent/'complete.json').exists():run.update(json.loads((p.parent/'complete.json').read_text(encoding='utf-8')))
 if p.parent.name in ['native-plain-1x-first','native-plain-1x-trace']:run['visual_result']='failed: freshness window too short; retained development evidence'
 report['runs'][p.parent.name]=run
required=['native-plain-1x-overlap','native-wide-4x-overlap','missing-plain-1x']
for name in required:
 assert report['runs'][name]['complete'],name
 assert report['runs'][name]['exe_sha256']==report['final_executable_sha256'],name
base=D/'baseline-plain-1x'
for name in ['original-plain-1x','missing-plain-1x']:
 for frame in [1500,1750,1900,2200,2600]:
  filename=f'canonical-{frame}.png';n=diff(pixels(base/filename),pixels(D/name/filename));assert n==0,(name,frame,n)
  report['comparisons'][f'{name}:baseline:{frame}']={'changed_pixels':n}
for name in ['native-plain-1x-overlap','native-wide-4x-overlap']:
 for frame in [1500,1750,1900,2200,2600]:
  a=pixels(base/f'canonical-{frame}.png');b=pixels(D/name/f'canonical-{frame}.png')
  n=diff(a if frame<1800 else a[184:],b if frame<1800 else b[184:]);assert n==0,(name,frame,n)
  report['comparisons'][f'{name}:{frame}']={'region':'whole mural' if frame<1800 else 'original footer y184:240','changed_pixels':n}
 # The canonical frame excludes the host artwork; the present capture must contain it.
 im=pixels(D/name/'2600-present.png');h,w=im.shape[:2];scale=min(w/320,h/240);ox=(w-320*scale)/2;oy=(h-240*scale)/2
 x0,x1=round(ox+24*scale),round(ox+296*scale);y0,y1=round(oy+28*scale),round(oy+151*scale)
 region=im[y0:y1,x0:x1];colored=int(np.count_nonzero(region.max(axis=2)>40));assert colored>10000,(name,colored)
 x0,x1=round(ox+96*scale),round(ox+224*scale);y0,y1=round(oy+106*scale),round(oy+150*scale)
 sub=im[y0:y1,x0:x1].astype(np.int32);red=int(np.count_nonzero((sub[:,:,0]>sub[:,:,1]*1.3)&(sub[:,:,0]>sub[:,:,2]*1.3)&(sub[:,:,0]>60)));assert red>1000,(name,red)
 report['visual_checks'][name]={'colored_title_pixels':colored,'red_subtitle_pixels':red,'manual_review':'overlapping PNGs, original footer clear; menu labels in front; card selection clear'}
 # Title changes must not alter the original texture pages or CLUTs.
 a=np.fromfile(base/'2600.vram',dtype='<u2').reshape(512,1024);b=np.fromfile(D/name/'2600.vram',dtype='<u2').reshape(512,1024)
 n=diff(a[:,576:,None],b[:,576:,None]);assert n==0,(name,'texture VRAM',n)
 report['comparisons'][name+':texture-vram']={'words_checked':512*448,'changed_words':n}
backups=json.loads((D/'backups.json').read_text(encoding='utf-8'));patch=[]
for name,old in backups.items():
 current=W/name;before=D/old['backup'];assert sha(before)==old['sha256']
 if 'build-release' in name:
  assert sha(current)==old['sha256'];report['preserved'][name]=sha(current)
 else:patch.extend(difflib.unified_diff(before.read_text(encoding='utf-8').splitlines(True),current.read_text(encoding='utf-8').splitlines(True),fromfile='before/'+name,tofile='after/'+name))
(D/'integration.patch').write_text(''.join(patch),encoding='utf-8')
for name in ['bofiii_upscaled.png','subtitle.png']:
 source=W/'Future Assets To Use'/name;assert source.read_bytes()==(G/'assets/title'/name).read_bytes()==(G/'build-release/assets/title'/name).read_bytes();report['preserved'][name]=sha(source)
main=W/'BoF3 PSXRecomp/psxrecomp-src-nightly-20260910-ed55299be3/runtime/src/main.cpp';assert sha(main)=='0cc3dda225dc9bc723cf6b1732fe6af58060271d6e83a8898dbeaff5063ef818';report['preserved']['Turbo-pinned main.cpp']=sha(main)
for name in ['guard-test.log','prompt-guard-test.log']:
 text=(D/name).read_text(encoding='utf-8-sig');assert 'PASS:' in text;report[name]=text.strip()
report['notes']=['Physical Xbox/keyboard glyph visibility and switching confirmed by the user before title changes.', 'Original/footer labels are image sprites and remain unchanged. New Game/Load Game image labels are re-presented in front of the dimmed host logo.', 'Canonical VRAM frames intentionally exclude host PNG layers; final composition is verified in present captures.', 'Widescreen terrain acceptance bounds remain at their original values. The previous +54 pixel fix remains a separate investigation checkpoint.', 'native-plain-1x-menu and native-wide-4x-release validate the earlier separated layout; final overlap runs use the final executable.']
report['sources']={}
for p in [G/'native/title_artwork.c',G/'native/title_artwork_guard.h',main.parent/'gpu_gl_artwork.inc']:
 report['sources'][str(p.relative_to(W))]=sha(p)
(D/'validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('PASS:',len(report['comparisons']),'image/texture comparisons; final 4:3/wide overlap captures; footer/source/settings/save preservation; title and prompt guards.')
print('Final executable:',report['final_executable_sha256'])
