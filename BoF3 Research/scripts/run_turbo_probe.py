from pathlib import Path
import sys,os,json,shutil,socket,subprocess,time
R=Path(__file__).resolve().parents[1];G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII';O=R/'coverage/turbo';speed=int(sys.argv[1]);label=sys.argv[2];E=O/label;E.mkdir(exist_ok=True)
with socket.socket() as s:
 if s.connect_ex(('127.0.0.1',4387))==0:raise RuntimeError('Diagnostic port busy')
shutil.copy2(G/'build-release/Breath_of_Fire_III___PSXRecomp.exe',E/'game.exe')
for name in ['assets','bios','mods']:shutil.copytree(G/'build-release'/name,E/name,dirs_exist_ok=True)
for name in ['input.ini','keybinds.ini']:shutil.copy2(G/'build-release'/name,E/name)
(E/'saves').mkdir(exist_ok=True)
for p in (G/'run-boot-baseline/saves').glob('card*.mcd'):shutil.copy2(p,E/'saves'/p.name)
(E/'settings.toml').write_text('[video]\nrenderer="opengl"\nwindow_width=640\nsupersampling=1\nantialiasing=false\ntexture_filtering="nearest"\nvsync="on"\nfullscreen=0\n',encoding='utf-8')
env=dict(os.environ,PSX_FAST_FORWARD_SPEED=str(speed))
with (E/'stdout.log').open('w') as out,(E/'stderr.log').open('w') as err:
 game=subprocess.Popen([str(E/'game.exe'),'--game',str(G/'game.toml'),'--debug-port','4387','--memcard-dir',str(E/'saves')],cwd=E,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
 print('TEST PID',game.pid,flush=True)
 try:
  # Drive the known copied-save route, then keep the process for actual hotkeys.
  t=(R/'scripts/probe_display_settings.py').read_text(encoding='utf-8');t=t[:t.index('# Controlled active palette cases')]
  (E/'probe.py').write_text('import sys\nsys.path.insert(0,'+repr(str(R/'scripts'))+')\n'+t,encoding='utf-8')
  probe=subprocess.run([sys.executable,str(E/'probe.py'),'--out',str(E),'--load-save'],capture_output=True,text=True,timeout=240)
  (E/'probe.log').write_text(probe.stdout+probe.stderr,encoding='utf-8');assert probe.returncode==0,probe.stderr
  print('READY FOR TURBO HOTKEY TEST',flush=True)
  deadline=time.monotonic()+360
  while game.poll() is None and time.monotonic()<deadline:time.sleep(.25)
 finally:
  if game.poll() is None:game.terminate()
  game.wait(timeout=10)
