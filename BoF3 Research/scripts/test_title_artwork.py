from pathlib import Path
import sys,subprocess,shutil,os,json,socket,time,hashlib,argparse
from record_runtime_coverage import request
import bof3_display_settings as settings
p=argparse.ArgumentParser();p.add_argument('mode',choices=['baseline','native','original','missing']);p.add_argument('--wide',action='store_true');p.add_argument('--scale',type=int,default=1);p.add_argument('--tag',default='');a=p.parse_args()
R=Path(__file__).resolve().parents[1];G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII';O=R/'coverage/title-artwork';D=O/(a.mode+('-wide' if a.wide else '-plain')+f'-{a.scale}x'+('-'+a.tag if a.tag else ''));E=D/'runtime';E.mkdir(parents=True,exist_ok=True)
with socket.socket() as s:assert s.connect_ex(('127.0.0.1',4387))!=0,'Port busy'
originals={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (G/'run-boot-baseline/saves').glob('card*.mcd')}
exe=O/'baseline.exe' if a.mode=='baseline' else G/'build-release/Breath_of_Fire_III___PSXRecomp.exe';shutil.copy2(exe,E/'game.exe')
for n in ['assets','bios','mods']:shutil.copytree(G/'build-release'/n,E/n,dirs_exist_ok=True)
if a.mode=='missing':(E/'assets/title/subtitle.png').rename(E/'assets/title/subtitle.png.unavailable')
for n in ['input.ini','keybinds.ini']:shutil.copy2(G/'build-release'/n,E/n)
(E/'mods/state.toml').write_text('format_version = 2\n',encoding='utf-8');settings.save(E/'settings.toml','windowed',1280 if a.wide else 960,a.scale,'nearest','on',aspect='16:9' if a.wide else '4:3')
(D/'saves').mkdir(exist_ok=True)
for p in originals:shutil.copy2(p,D/'saves'/Path(p).name)
def call(c,**kw):
 r=request(4387,c,**kw);assert r.get('ok',True),(c,r);return r
def frame():return call('get_registers')['frame']
def until(target):
 end=time.monotonic()+90
 while frame()<target:assert time.monotonic()<end,('timeout',frame(),target);time.sleep(.03)
def wait(n):until(frame()+n)
def ram(addr,n):return bytes.fromhex(call('read_ram',addr=hex(addr),len=n)['hex'])
def snap(label):
 now=frame();seq=call('present_shot_seq')['seq'];call('present_shot',path=(D/(label+'-present.png')).as_posix());end=time.monotonic()+10
 while call('present_shot_seq')['seq']==seq:assert time.monotonic()<end;time.sleep(.02)
 assert call('present_shot_seq')['wrote'];call('screenshot_file',path=(D/(label+'.png')).as_posix())
 now=frame();call('display_ring_aux',frame=now-2,path=(D/(label+'.vram')).as_posix())
 state={'frame':now,'outer':int.from_bytes(ram(0x80143b92,2),'little'),'intro_state':ram(0x80143c10,36).hex(),'gpu':[call('gpu_frame_dump',frame=f,count=512) for f in range(now-3,now)]}
 (D/(label+'.json')).write_text(json.dumps(state,indent=2),encoding='utf-8');print(label,state['frame'],state['outer'],flush=True)
with (D/'stdout.log').open('w') as out,(D/'stderr.log').open('w') as err:
 game=subprocess.Popen([str(E/'game.exe'),'--game',str(G/'game.toml'),'--debug-port','4387','--memcard-dir',str(D/'saves')],cwd=D,stdout=out,stderr=err,env=dict(os.environ,BOF3_SKIP_CAPCOM_LOGO='1',PSX_DISPLAY_RING='1',BOF3_TRACE_TITLE_ARTWORK='1',BOF3_TITLE_ARTWORK='original' if a.mode=='original' else 'enhanced'),creationflags=subprocess.CREATE_NO_WINDOW)
 try:
  end=time.monotonic()+25
  while True:
   try:frame();break
   except OSError:assert time.monotonic()<end;time.sleep(.1)
  for target in [1500,1750,1900,2200,2600]:
   until(target+2);call('display_ring_get',frame=target,path=(D/f'canonical-{target}.png').as_posix());snap(str(target))
  t=time.monotonic();start=frame();wait(120);speed=(frame()-start)/(time.monotonic()-t)
  until(3050);call('press',buttons=0xfff7,frames=5);start_frame=frame();until(start_frame+40);snap('after-start-40');until(start_frame+120);snap('after-start-120');until(start_frame+650);snap('start-menu')
  data=bytearray()
  for lo in range(0x801d0c00,0x801ef000,0x8000):data.extend(ram(lo,min(0x8000,0x801ef000-lo)))
  (D/'start-menu-801d0c00.bin').write_bytes(data)
  call('press',buttons=0xbfff,frames=5);wait(400);snap('card');assert ram(0x801ed860,1)[0]==5
  (D/'complete.json').write_text(json.dumps({'complete':True,'frames_per_second':speed,'mode':a.mode,'wide':a.wide,'scale':a.scale}),encoding='utf-8')
 finally:
  if game.poll() is None:game.terminate()
  game.wait(timeout=10);assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in originals.items())
  (D/'run.json').write_text(json.dumps({'original_cards_unchanged':True,'exe_sha256':hashlib.sha256((E/'game.exe').read_bytes()).hexdigest()}),encoding='utf-8')
print('Complete',D.name,flush=True)
