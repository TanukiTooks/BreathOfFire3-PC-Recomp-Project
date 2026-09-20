from pathlib import Path
import argparse,sys,os,shutil,subprocess,socket,json,hashlib
R=Path(__file__).resolve().parents[1];G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII';O=R/'coverage/scenario01-events-native'
p=argparse.ArgumentParser();p.add_argument('variant',choices=['baseline','native']);p.add_argument('--repeat-baseline',action='store_true');p.add_argument('--out',type=Path,default=O);a=p.parse_args();O=a.out.resolve();assert not a.repeat_baseline or a.variant=='baseline';D=O/('baseline-repeat' if a.repeat_baseline else a.variant);E=D/'runtime';E.mkdir(parents=True,exist_ok=True)
with socket.socket() as s:
 if s.connect_ex(('127.0.0.1',4387))==0:raise RuntimeError('Diagnostic port busy')
originals={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (G/'run-boot-baseline/saves').glob('card*.mcd')}
if a.variant=='baseline' and not a.repeat_baseline:
 if not (O/'baseline.exe').exists():shutil.copy2(G/'build-release/Breath_of_Fire_III___PSXRecomp.exe',O/'baseline.exe')
 if (O/'original-cards.json').exists():assert originals==json.loads((O/'original-cards.json').read_text()),'Save changed since baseline'
 else:(O/'original-cards.json').write_text(json.dumps(originals,indent=2))
else:assert originals==json.loads((O/'original-cards.json').read_text()),'Original save changed since baseline'
exe=O/'baseline.exe' if a.variant=='baseline' else G/'build-release/Breath_of_Fire_III___PSXRecomp.exe'
shutil.copy2(exe,E/'game.exe')
for name in ['assets','bios','mods']:shutil.copytree(G/'build-release'/name,E/name,dirs_exist_ok=True)
(E/'mods/state.toml').write_text('format_version = 2\n',encoding='utf-8')
(E/'settings.toml').write_text('[video]\nrenderer="opengl"\nwindow_width=640\nsupersampling=1\ntexture_filtering="nearest"\nvsync="on"\nfullscreen=0\n',encoding='utf-8')
(D/'saves').mkdir(exist_ok=True)
for path in originals:shutil.copy2(path,D/'saves'/Path(path).name)
with (D/'stdout.log').open('w') as out,(D/'stderr.log').open('w') as err:
 game=subprocess.Popen([str(E/'game.exe'),'--headless','--game',str(G/'game.toml'),'--debug-port','4387','--memcard-dir',str(D/'saves')],cwd=D,stdout=out,stderr=err,env=dict(os.environ,BOF3_TRACE_NATIVE_CARD='1'),creationflags=subprocess.CREATE_NO_WINDOW)
 try:
  probe=subprocess.run([sys.executable,str(R/'scripts/probe_scenario01.py'),'--out',str(D),'--load-save'],capture_output=True,text=True,timeout=300)
  (D/'probe.log').write_text(probe.stdout+probe.stderr,encoding='utf-8');print(probe.stdout,flush=True);assert probe.returncode==0,probe.stderr
 finally:
  if game.poll() is None:game.terminate()
  game.wait(timeout=10)
  unchanged=all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha for path,sha in originals.items())
  (D/'run.json').write_text(json.dumps({'original_cards_unchanged':unchanged,'exe_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'exit_code':game.returncode},indent=2));assert unchanged
