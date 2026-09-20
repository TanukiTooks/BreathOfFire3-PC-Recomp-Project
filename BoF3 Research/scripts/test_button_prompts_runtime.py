from pathlib import Path
import sys,subprocess,shutil,os,json,socket,time,hashlib,argparse
from record_runtime_coverage import request
import bof3_display_settings as settings
p=argparse.ArgumentParser();p.add_argument('mode',choices=['baseline','original','xbox','keyboard','auto']);p.add_argument('--wide',action='store_true');p.add_argument('--scale',type=int,default=1);p.add_argument('--remap',action='store_true');p.add_argument('--tag',default='');p.add_argument('--load',action='store_true');a=p.parse_args()
R=Path(__file__).resolve().parents[1];G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII';O=R/'coverage/button-prompts/implementation';D=O/(a.mode+('-wide' if a.wide else '-plain')+f'-{a.scale}x'+('-remap' if a.remap else '')+('-'+a.tag if a.tag else '')+('-load' if a.load else ''));E=D/'runtime';E.mkdir(parents=True,exist_ok=True)
with socket.socket() as s:assert s.connect_ex(('127.0.0.1',4387))!=0,'Diagnostic port busy'
originals={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (G/'run-boot-baseline/saves').glob('card*.mcd')}
exe=O/'baseline.exe' if a.mode=='baseline' else G/'build-release/Breath_of_Fire_III___PSXRecomp.exe';shutil.copy2(exe,E/'game.exe')
for n in ['assets','bios','mods']:shutil.copytree(G/'build-release'/n,E/n,dirs_exist_ok=True)
for n in ['input.ini','keybinds.ini']:shutil.copy2(G/'build-release'/n,E/n)
if a.remap:
 p=E/('keybinds.ini' if a.mode=='keyboard' else 'input.ini');s=p.read_text(encoding='utf-8')
 import re
 s,n=re.subn(r'(?m)^(cross\s*=\s*)[^\r\n]*',lambda m:m[1]+('K' if a.mode=='keyboard' else 'y'),s,count=1);assert n==1;p.write_text(s,encoding='utf-8')
(E/'mods/state.toml').write_text('format_version = 2\n',encoding='utf-8');settings.save(E/'settings.toml','windowed',1280 if a.wide else 960,a.scale,'nearest','on',aspect='16:9' if a.wide else '4:3')
(D/'saves').mkdir(exist_ok=True)
for p in originals:shutil.copy2(p,D/'saves'/Path(p).name)
def call(c,**kw):
 r=request(4387,c,**kw);assert r.get('ok',True),(c,r);return r
def frame():return call('get_registers')['frame']
def until(target):
 end=time.monotonic()+90
 while frame()<target:
  assert time.monotonic()<end,('timeout',frame(),target);time.sleep(.025)
def wait(n):until(frame()+n)
def ram(addr,n):return bytes.fromhex(call('read_ram',addr=hex(addr),len=n)['hex'])
def press(mask,n):call('press',buttons=mask,frames=5);wait(n)
def snap(label):
 now=frame();seq=call('present_shot_seq')['seq'];call('present_shot',path=(D/(label+'-present.png')).as_posix());end=time.monotonic()+10
 while call('present_shot_seq')['seq']==seq:assert time.monotonic()<end;time.sleep(.03)
 assert call('present_shot_seq')['wrote'];call('screenshot_file',path=(D/(label+'.png')).as_posix())
 call('display_ring_aux',frame=frame()-2,path=(D/(label+'.vram')).as_posix())
 state={'frame':now,'outer':int.from_bytes(ram(0x80143b92,2),'little'),'menu':ram(0x801ed860,1)[0]}
 (D/(label+'.json')).write_text(json.dumps(state,indent=2),encoding='utf-8');print(label,state,flush=True);return state
with (D/'stdout.log').open('w') as out,(D/'stderr.log').open('w') as err:
 game=subprocess.Popen([str(E/'game.exe'),'--game',str(G/'game.toml'),'--debug-port','4387','--memcard-dir',str(D/'saves')],cwd=D,stdout=out,stderr=err,env=dict(os.environ,BOF3_SKIP_CAPCOM_LOGO='1',PSX_DISPLAY_RING='1',BOF3_BUTTON_PROMPTS=a.mode,BOF3_TRACE_BUTTON_PROMPTS='1'),creationflags=subprocess.CREATE_NO_WINDOW)
 try:
  end=time.monotonic()+25
  while True:
   try:frame();break
   except OSError:assert time.monotonic()<end;time.sleep(.1)
  until(1502);call('display_ring_get',frame=1500,path=(D/'mural.png').as_posix());until(3050)
  press(0xfff7,650);press(0xbfff,400);assert snap('card')['menu']==5
  if a.load:
   press(0xbfff,350);press(0xbfff,100);assert snap('load-confirm')['menu']==10
   press(0xbfff,1000);assert snap('loaded-save')['outer']==0
   press(0xefff,350);snap('post-load-input')
   start=frame();t=time.monotonic();wait(120);speed=(frame()-start)/(time.monotonic()-t)
  else:
   button=int.from_bytes(ram(0x80145ac4,2),'little');cancel=0xffff^(((button&255)<<8)|(button>>8))
   press(cancel,450);press(0xffef,80);press(0xbfff,350);assert snap('naming')['outer']==2
   start=frame();t=time.monotonic();wait(120);speed=(frame()-start)/(time.monotonic()-t)
   # Verify the edited glyph renderer did not damage menu input/navigation.
   press(0xffdf,30);snap('naming-right')
  (D/'complete.json').write_text(json.dumps({'complete':True,'frames_per_second':speed,'mode':a.mode,'wide':a.wide,'scale':a.scale,'remap':a.remap,'load':a.load},indent=2),encoding='utf-8')
 finally:
  if game.poll() is None:game.terminate()
  game.wait(timeout=10)
  assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in originals.items())
  (D/'run.json').write_text(json.dumps({'original_cards_unchanged':True,'exe_sha256':hashlib.sha256((E/'game.exe').read_bytes()).hexdigest()},indent=2),encoding='utf-8')
print('Complete',D.name,flush=True)
