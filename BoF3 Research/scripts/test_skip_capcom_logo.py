from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,socket,sys,os
import bof3_display_settings as settings
R=Path(__file__).resolve().parents[1];G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII';O=R/'coverage/skip-capcom-logo'
p=argparse.ArgumentParser();p.add_argument('mode',choices=['baseline','off','on']);a=p.parse_args();D=O/a.mode;E=D/'runtime';E.mkdir(parents=True,exist_ok=True)
with socket.socket() as s:
 assert s.connect_ex(('127.0.0.1',4387))!=0,'Diagnostic port busy'
originals={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (G/'run-boot-baseline/saves').glob('card*.mcd')}
if (O/'original-cards.json').exists():assert originals==json.loads((O/'original-cards.json').read_text())
else:(O/'original-cards.json').write_text(json.dumps(originals,indent=2))
exe=O/'baseline.exe' if a.mode=='baseline' else G/'build-release/Breath_of_Fire_III___PSXRecomp.exe';shutil.copy2(exe,E/'game.exe')
for name in ['assets','bios','mods']:shutil.copytree(G/'build-release'/name,E/name,dirs_exist_ok=True)
for name in ['input.ini','keybinds.ini']:
 if (G/'build-release'/name).exists():shutil.copy2(G/'build-release'/name,E/name)
(E/'mods/state.toml').write_text('format_version = 2\n')
settings.save(E/'settings.toml','windowed',960,1,'nearest','on',aspect='4:3',skip_capcom_logo=a.mode=='on')
prefs=settings.show(E/'settings.toml');(D/'saves').mkdir(exist_ok=True)
for path in originals:shutil.copy2(path,D/'saves'/Path(path).name)
with (D/'stdout.log').open('w') as out,(D/'stderr.log').open('w') as err:
 game=subprocess.Popen([str(E/'game.exe'),'--headless','--game',str(G/'game.toml'),'--debug-port','4387','--memcard-dir',str(D/'saves')],cwd=D,stdout=out,stderr=err,env=dict(os.environ,PSX_DISPLAY_RING='1',BOF3_SKIP_CAPCOM_LOGO='1' if prefs['skip_capcom_logo'] else '0'),creationflags=subprocess.CREATE_NO_WINDOW)
 try:
  proc=subprocess.run([sys.executable,str(R/'scripts/probe_skip_capcom_logo.py'),'--out',str(D),'--load-save'],capture_output=True,text=True,timeout=240)
  (D/'probe.log').write_text(proc.stdout+proc.stderr);print(proc.stdout,flush=True);assert proc.returncode==0,proc.stderr
 finally:
  if game.poll() is None:game.terminate()
  game.wait(timeout=10)
  assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in originals.items())
  (D/'run.json').write_text(json.dumps({'original_cards_unchanged':True,'exe_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'mode':a.mode},indent=2))
