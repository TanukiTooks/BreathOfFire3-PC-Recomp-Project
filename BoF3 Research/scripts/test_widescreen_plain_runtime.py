from pathlib import Path
import hashlib,json,shutil,socket,subprocess,sys
import bof3_display_settings as settings
R=Path(__file__).resolve().parents[1];G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII';O=R/'coverage/widescreen';E=O/'runtime';E.mkdir(exist_ok=True)
with socket.socket() as s:
 if s.connect_ex(('127.0.0.1',4387))==0:raise RuntimeError('Diagnostic port is already in use.')
shutil.copy2(G/'build-release/Breath_of_Fire_III___PSXRecomp.exe',E/'game.exe')
for name in ['assets','bios','mods']:shutil.copytree(G/'build-release'/name,E/name,dirs_exist_ok=True)
for name in ['input.ini','keybinds.ini','game_options.toml']:shutil.copy2(G/'build-release'/name,E/name)
originals={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (G/'run-boot-baseline/saves').glob('card*.mcd')}
results=[]
for label,mode,width,scale,filtering,vsync in [('plain-16-9','windowed',1280,1,'nearest','on')]:
 out=O/label;out.mkdir(exist_ok=True);(out/'saves').mkdir(exist_ok=True)
 for p in (G/'run-boot-baseline/saves').glob('card*.mcd'):shutil.copy2(p,out/'saves'/p.name)
 state='format_version = 2\n\n[[package]]\nid = "bof3.presentation.widescreen"\nversion = "0.1.0"\n\n[[feature]]\npackage_id = "bof3.presentation.widescreen"\nid = "widescreen"\nenabled = '+str(label=='plain-16-9').lower()+'\n'
 (E/'mods/state.toml').write_text(state,encoding='utf-8')
 config=(G/'game.toml').read_text(encoding='utf-8').replace('exe = "disc/SLUS_004.22"','exe = "'+(G/'disc/SLUS_004.22').as_posix()+'"')
 config+='\n[widescreen]\nnative_wide = true\ngte_game_mode = true\nnw_full_mirror = true\nnw_textured_edges = false\nnw_textured_edge_scale = 160\n\n[widescreen.cull]\nauto_screen_x = true\nguard_pixels = 32\n'
 (out/'game.toml').write_text(config,encoding='utf-8')
 prefs=settings.save(E/'settings.toml',mode,width,scale,filtering,vsync);(out/'requested-settings.json').write_text(json.dumps(prefs,indent=2))
 with (out/'stdout.log').open('w') as stdout,(out/'stderr.log').open('w') as stderr:
  game=subprocess.Popen([str(E/'game.exe'),'--game',str(out/'game.toml'),'--debug-port','4387','--memcard-dir',str(out/'saves')],cwd=out,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
  try:
   probe=subprocess.run([sys.executable,str(R/'scripts/probe_widescreen.py'),'--out',str(out),'--load-save'],capture_output=True,text=True,timeout=240)
   (out/'probe.log').write_text(probe.stdout+probe.stderr,encoding='utf-8');assert probe.returncode==0,(label,probe.stdout,probe.stderr)
  finally:
   if game.poll() is None:game.terminate()
   game.wait(timeout=10)
 results.append({'label':label,'settings':prefs,'probe_complete':True,'presentation_capture':str(out/'present.png')});print('PASS',label,flush=True)
for path,sha in originals.items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha
(O/'plain-runtime-validation.json').write_text(json.dumps({'runs':results,'original_cards_unchanged':True,'scope':'Actual OpenGL native 4:3 and Legacy-configured 16:9 runs through copied-save load, movement, palette cases and final framebuffer capture.'},indent=2)+'\n')
