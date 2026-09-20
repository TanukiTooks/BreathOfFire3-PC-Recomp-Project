from pathlib import Path
import sys,subprocess,shutil,os,json,socket,time,hashlib
sys.path.insert(0,str(Path('BoF3 Research/scripts').resolve()));from record_runtime_coverage import request
R=Path('BoF3 Research').resolve();G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII';O=R/'coverage/mural';D=O/'discovery';E=D/'runtime';E.mkdir(parents=True,exist_ok=True)
with socket.socket() as s:assert s.connect_ex(('127.0.0.1',4387))!=0
shutil.copy2(G/'build-release/Breath_of_Fire_III___PSXRecomp.exe',E/'game.exe')
for n in ['assets','bios','mods']:shutil.copytree(G/'build-release'/n,E/n,dirs_exist_ok=True)
(E/'mods/state.toml').write_text('format_version = 2\n');(E/'settings.toml').write_text('[video]\nrenderer="opengl"\nwindow_width=960\nfullscreen=0\nsupersampling=1\nvsync="on"\n')
(D/'saves').mkdir(exist_ok=True)
for p in (G/'run-boot-baseline/saves').glob('card*.mcd'):shutil.copy2(p,D/'saves'/p.name)
def call(c,**kw):
 r=request(4387,c,**kw);assert r.get('ok',True),(c,r);return r
with (D/'stdout.log').open('w') as out,(D/'stderr.log').open('w') as err:
 game=subprocess.Popen([str(E/'game.exe'),'--game',str(G/'game.toml'),'--debug-port','4387','--memcard-dir',str(D/'saves')],cwd=D,stdout=out,stderr=err,env=dict(os.environ,BOF3_SKIP_CAPCOM_LOGO='1',PSX_DISPLAY_RING='1',PSX_FN_FILTER='0x80090000:0x80200000'),creationflags=subprocess.CREATE_NO_WINDOW)
 try:
  end=time.monotonic()+25
  while True:
   try:call('get_registers');break
   except OSError:
    assert time.monotonic()<end;time.sleep(.1)
  for target in [1200,1500,1800,2200]:
   while call('get_registers')['frame']<target:time.sleep(.07)
   now=call('get_registers')['frame'];data={'frame':now,'functions':call('fn_entry_tail',count=2048),'phase':call('phase_profile',window=1),'overlays':call('overlay_loader_status'),'dirty':call('dirty_ram_stats')}
   data['gpu']=[call('gpu_frame_dump',frame=f,count=2048) for f in range(now-3,now)]
   (D/f'{target}.json').write_text(json.dumps(data,indent=2));call('screenshot_file',path=(D/f'{target}.png').as_posix())
   (D/f'{target}-state.bin').write_bytes(bytes.fromhex(call('read_ram',addr='0x80143b00',len=0x2200)['hex']))
   print(target,now,flush=True)
   if target==1500:
    b=bytearray()
    for lo in range(0x80195800,0x80200000,0x8000):b.extend(bytes.fromhex(call('read_ram',addr=hex(lo),len=min(0x8000,0x80200000-lo))['hex']))
    (D/'live-80195800.bin').write_bytes(b)
    call('display_ring_aux',frame=now,path=(D/'mural.vram').as_posix())
 finally:
  if game.poll() is None:game.terminate()
  game.wait(timeout=10)
