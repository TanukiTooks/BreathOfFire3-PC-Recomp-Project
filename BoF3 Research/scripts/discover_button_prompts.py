from pathlib import Path
import sys,subprocess,shutil,os,json,socket,time,hashlib
sys.path.insert(0,str(Path('BoF3 Research/scripts').resolve()))
from record_runtime_coverage import request
R=Path('BoF3 Research').resolve();G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII';D=R/'coverage/button-prompts/discovery';E=D/'runtime';E.mkdir(parents=True,exist_ok=True)
with socket.socket() as s:assert s.connect_ex(('127.0.0.1',4387))!=0,'Diagnostic port busy'
originals={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (G/'run-boot-baseline/saves').glob('card*.mcd')}
shutil.copy2(G/'build-release/Breath_of_Fire_III___PSXRecomp.exe',E/'game.exe')
for n in ['assets','bios','mods']:shutil.copytree(G/'build-release'/n,E/n,dirs_exist_ok=True)
for n in ['input.ini','keybinds.ini']:shutil.copy2(G/'build-release'/n,E/n)
(E/'mods/state.toml').write_text('format_version = 2\n',encoding='utf-8')
(E/'settings.toml').write_text('[video]\nrenderer="opengl"\nwindow_width=960\nfullscreen=0\nsupersampling=1\nvsync="on"\n',encoding='utf-8')
(D/'saves').mkdir(exist_ok=True)
for p in originals:shutil.copy2(p,D/'saves'/Path(p).name)
def call(c,**kw):
 r=request(4387,c,**kw);assert r.get('ok',True),(c,r);return r
def frame():return call('get_registers')['frame']
def wait(n):
 goal=frame()+n;end=time.monotonic()+60
 while frame()<goal:
  assert time.monotonic()<end,'Timeout';time.sleep(.05)
def ram(addr,n):return bytes.fromhex(call('read_ram',addr=hex(addr),len=n)['hex'])
def press(mask,n=150):call('press',buttons=mask,frames=5);wait(n)
def capture(label):
 now=frame();data={'frame':now,'functions':call('fn_entry_tail',count=2048),'gpu':[call('gpu_frame_dump',frame=f,count=2048) for f in range(now-3,now)]}
 (D/(label+'.json')).write_text(json.dumps(data,indent=2),encoding='utf-8')
 call('screenshot_file',path=(D/(label+'.png')).as_posix())
 call('display_ring_aux',frame=now-1,path=(D/(label+'.vram')).as_posix())
 b=bytearray()
 for lo in range(0x80195800,0x80200000,0x8000):b.extend(ram(lo,min(0x8000,0x80200000-lo)))
 (D/(label+'-80195800.bin')).write_bytes(b)
 print(label,now,flush=True)
with (D/'stdout.log').open('w') as out,(D/'stderr.log').open('w') as err:
 game=subprocess.Popen([str(E/'game.exe'),'--game',str(G/'game.toml'),'--debug-port','4387','--memcard-dir',str(D/'saves')],cwd=D,stdout=out,stderr=err,env=dict(os.environ,BOF3_SKIP_CAPCOM_LOGO='1',PSX_DISPLAY_RING='1',PSX_FN_FILTER='0x80090000:0x80200000'),creationflags=subprocess.CREATE_NO_WINDOW)
 try:
  end=time.monotonic()+25
  while True:
   try:frame();break
   except OSError:assert time.monotonic()<end;time.sleep(.1)
  while frame()<3050:time.sleep(.1)
  press(0xfff7,650);press(0xbfff,400);capture('card')
  button=int.from_bytes(ram(0x80145ac4,2),'little');cancel=0xffff^(((button&255)<<8)|(button>>8))
  press(cancel,450);press(0xffef,80);press(0xbfff,350);capture('naming')
 finally:
  if game.poll() is None:game.terminate()
  game.wait(timeout=10)
  unchanged=all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in originals.items());assert unchanged
  (D/'run.json').write_text(json.dumps({'original_cards_unchanged':unchanged,'exe_sha256':hashlib.sha256((E/'game.exe').read_bytes()).hexdigest()},indent=2),encoding='utf-8')
