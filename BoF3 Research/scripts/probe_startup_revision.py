"""Isolated, paced startup measurement; never opens the player's memory cards."""
from pathlib import Path
import sys, os, time, json, shutil, subprocess, argparse
from PIL import Image, ImageStat
from record_runtime_coverage import request
import bof3_display_settings as settings

G = settings.ROOT / 'BoF3 PSXRecomp/BreathOfFireIII'
P = argparse.ArgumentParser()
P.add_argument('label')
P.add_argument('--skip', action='store_true')
P.add_argument('--seconds', type=int, default=20)
A = P.parse_args()
D = settings.ROOT / 'BoF3 Research/coverage/startup-revision' / A.label
E = D / 'runtime'
E.mkdir(parents=True, exist_ok=True)
for name in ('assets', 'bios', 'mods'):
    shutil.copytree(G/'build-release'/name, E/name, dirs_exist_ok=True)
for name in ('input.ini', 'keybinds.ini'):
    shutil.copy2(G/'build-release'/name, E/name)
shutil.copy2(G/'build-release/Breath_of_Fire_III___PSXRecomp.exe', E/'game.exe')
settings.save(E/'settings.toml', 'windowed', 640, 2, 'nearest', 'on', aspect='4:3', psx_wobble=False)
(D/'saves').mkdir(exist_ok=True)
rows=[]
with (D/'stdout.log').open('w') as out, (D/'stderr.log').open('w') as err:
    start=time.monotonic()
    game=subprocess.Popen([str(E/'game.exe'), '--game', str(G/'game.toml'), '--debug-port', '4387', '--memcard-dir', str(D/'saves')], cwd=D, stdout=out, stderr=err, env=dict(os.environ, BOF3_SKIP_CAPCOM_LOGO=str(int(A.skip))), creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        while time.monotonic()-start < A.seconds:
            if game.poll() is not None: raise RuntimeError('Runtime exited early')
            try:
                r=request(4387, 'get_registers')
                elapsed=round(time.monotonic()-start, 3)
                path=D/f'{len(rows):03}.png'
                shot=request(4387, 'screenshot_file', path=path.as_posix())
                brightness=max(ImageStat.Stat(Image.open(path).convert('RGB')).mean) if path.exists() else 0
                rows.append(dict(seconds=elapsed, frame=r.get('frame'), brightness=brightness, screenshot=shot))
            except OSError: pass
            time.sleep(.25)
        geometry=request(4387,'geom_correction')
    finally:
        if game.poll() is None: game.terminate()
        game.wait(timeout=10)
(D/'result.json').write_text(json.dumps(dict(rows=rows,geometry=geometry),indent=2))
print(json.dumps(dict(label=A.label,first_visible=next((r for r in rows if r['brightness']>2),None),geometry=geometry)),flush=True)
