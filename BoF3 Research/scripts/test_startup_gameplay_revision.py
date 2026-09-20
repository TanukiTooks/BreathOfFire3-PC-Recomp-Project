"""Load a copied memory card, compare precision gates, then allow F1 UI testing."""
from pathlib import Path
import os, time, json, shutil, subprocess, hashlib
from record_runtime_coverage import request
import bof3_display_settings as settings
G=settings.ROOT/'BoF3 PSXRecomp/BreathOfFireIII'
D=settings.ROOT/'BoF3 Research/coverage/startup-revision/gameplay'
E=D/'runtime'; E.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
originals={p:sha(p) for p in (G/'run-boot-baseline/saves').glob('card*.mcd')}
for name in ('assets','bios','mods'):shutil.copytree(G/'build-release'/name,E/name,dirs_exist_ok=True)
for name in ('input.ini','keybinds.ini'):shutil.copy2(G/'build-release'/name,E/name)
shutil.copy2(G/'build-release/Breath_of_Fire_III___PSXRecomp.exe',E/'game.exe')
settings.save(E/'settings.toml','windowed',960,4,'nearest','on',aspect='16:9',psx_wobble=False)
(D/'saves').mkdir(exist_ok=True)
for p in originals:shutil.copy2(p,D/'saves'/p.name)
def call(cmd,**kw):
    r=request(4387,cmd,**kw)
    assert r.get('ok',True),(cmd,r)
    return r
def frame():return call('get_registers')['frame']
def wait(n):
    target=frame()+n;end=time.monotonic()+60
    while frame()<target:
        assert time.monotonic()<end,'Frame timeout'
        time.sleep(.04)
rows=[]
with (D/'stdout.log').open('w') as out,(D/'stderr.log').open('w') as err:
    game=subprocess.Popen([str(E/'game.exe'),'--game',str(G/'game.toml'),'--debug-port','4387','--memcard-dir',str(D/'saves')],cwd=D,stdout=out,stderr=err,env=dict(os.environ,BOF3_SKIP_CAPCOM_LOGO='1'),creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        end=time.monotonic()+25
        while True:
            try:frame();break
            except OSError:assert time.monotonic()<end;time.sleep(.1)
        while frame()<3050:time.sleep(.1)
        for mask,delay in [(0xfff7,650),(0xbfff,400),(0xbfff,350),(0xbfff,100),(0xbfff,1000)]:
            call('press',buttons=mask,frames=5);wait(delay)
        assert int.from_bytes(bytes.fromhex(call('read_ram',addr='0x80143b92',len=2)['hex']),'little')==0
        for tolerance in (.5,1.0):
            call('pgxp',tolerance=tolerance);wait(60)
            before=call('geom_correction');f=frame();start=time.monotonic();wait(120)
            after=call('geom_correction')
            seq=call('present_shot_seq')['seq'];call('present_shot',path=(D/f'camp-{tolerance}.png').as_posix())
            while call('present_shot_seq')['seq']==seq:time.sleep(.03)
            rows.append(dict(tolerance=tolerance,before=before,after=after,fps=(frame()-f)/(time.monotonic()-start)))
        assert rows[1]['after']['pgxp']['tolerance_reject']==rows[1]['before']['pgxp']['tolerance_reject']
        (D/'precision.json').write_text(json.dumps(rows,indent=2))
        print('READY FOR F1 TEST',game.pid,flush=True)
        end=time.monotonic()+600
        while game.poll() is None and time.monotonic()<end:time.sleep(.2)
    finally:
        if game.poll() is None:game.terminate()
        game.wait(timeout=10)
        assert all(sha(p)==h for p,h in originals.items())
        (D/'result.json').write_text(json.dumps(dict(exit_code=game.returncode,original_cards_unchanged=True,exe_sha256=sha(E/'game.exe')),indent=2))
