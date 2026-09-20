"""Actual OpenGL intro comparisons in isolated preferences and copied cards."""
from pathlib import Path
import argparse,shutil,subprocess,sys,os,socket,json,hashlib
import bof3_display_settings as settings
R=Path(__file__).resolve().parents[1];G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII';O=R/'coverage/mural'
p=argparse.ArgumentParser();p.add_argument('variant',choices=['baseline','native']);p.add_argument('aspect',choices=['plain','wide']);p.add_argument('--logo',action='store_true');a=p.parse_args();D=O/(a.variant+'-'+a.aspect+('-logo' if a.logo else ''));E=D/'runtime';E.mkdir(parents=True,exist_ok=True)
with socket.socket() as s:assert s.connect_ex(('127.0.0.1',4387))!=0,'Diagnostic port busy'
originals={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (G/'run-boot-baseline/saves').glob('card*.mcd')}
if (O/'original-cards.json').exists():assert originals==json.loads((O/'original-cards.json').read_text())
else:(O/'original-cards.json').write_text(json.dumps(originals,indent=2))
exe=O/'baseline.exe' if a.variant=='baseline' else G/'build-release/Breath_of_Fire_III___PSXRecomp.exe';shutil.copy2(exe,E/'game.exe')
for n in ['assets','bios','mods']:shutil.copytree(G/'build-release'/n,E/n,dirs_exist_ok=True)
for n in ['input.ini','keybinds.ini']:
 if (G/'build-release'/n).exists():shutil.copy2(G/'build-release'/n,E/n)
(E/'mods/state.toml').write_text('format_version = 2\n');settings.save(E/'settings.toml','windowed',1280 if a.aspect=='wide' else 960,1,'nearest','on',aspect='16:9' if a.aspect=='wide' else '4:3')
(D/'saves').mkdir(exist_ok=True)
for n in originals:shutil.copy2(n,D/'saves'/Path(n).name)
with (D/'stdout.log').open('w') as out,(D/'stderr.log').open('w') as err:
 game=subprocess.Popen([str(E/'game.exe'),'--game',str(G/'game.toml'),'--debug-port','4387','--memcard-dir',str(D/'saves')],cwd=D,stdout=out,stderr=err,env=dict(os.environ,BOF3_SKIP_CAPCOM_LOGO='0' if a.logo else '1',PSX_DISPLAY_RING='1'),creationflags=subprocess.CREATE_NO_WINDOW)
 try:
  r=subprocess.run([sys.executable,str(R/'scripts/probe_mural.py'),'--out',str(D)],capture_output=True,text=True,timeout=180);(D/'probe.log').write_text(r.stdout+r.stderr);print(r.stdout,flush=True);assert r.returncode==0,r.stderr
 finally:
  if game.poll() is None:game.terminate()
  game.wait(timeout=10)
  assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in originals.items());(D/'run.json').write_text(json.dumps({'variant':a.variant,'aspect':a.aspect,'logo_played':a.logo,'original_cards_unchanged':True,'exe_sha256':hashlib.sha256(exe.read_bytes()).hexdigest()},indent=2))
