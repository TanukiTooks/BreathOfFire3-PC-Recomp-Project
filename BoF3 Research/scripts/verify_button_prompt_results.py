"""Audit isolated prompt captures and preserve precise build provenance."""
from pathlib import Path
import json,hashlib,difflib
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];W=R.parent
D=R/'coverage/button-prompts/implementation'
G=W/'BoF3 PSXRecomp/BreathOfFireIII'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
report={'final_executable_sha256':sha(G/'build-release/Breath_of_Fire_III___PSXRecomp.exe'),'runs':{},'image_comparisons':{},'font_comparisons':{},'production_preferences':{},'notes':[]}
for run in sorted(D.glob('*/run.json')):
 data=json.loads(run.read_text(encoding='utf-8'));name=run.parent.name
 binary=run.parent/'runtime/game.exe'
 actual=sha(binary)
 entry={'actual_copied_executable_sha256':actual,'recorded_end_of_run_source_sha256':data['exe_sha256'],'original_cards_unchanged':data['original_cards_unchanged']}
 assert entry['original_cards_unchanged']
 completed=run.parent/'complete.json'
 if completed.exists():entry.update(json.loads(completed.read_text(encoding='utf-8')))
 else:entry['complete']=False
 report['runs'][name]=entry
 if actual!=data['exe_sha256']:report['notes'].append(name+': older harness hashed production executable at exit; use actual copied executable SHA above (a build overlapped this run).')
ref=np.fromfile(R/'coverage/button-prompts/discovery/naming.vram',dtype='<u2').reshape(512,1024)[:256,960:1024]
for f in sorted(D.glob('*/naming.vram')):
 a=np.fromfile(f,dtype='<u2').reshape(512,1024)[:256,960:1024]
 count=int(np.count_nonzero(a!=ref));assert count==0,(str(f),count)
 report['font_comparisons'][f.parent.name]={'original_font_words_different':count,'words_checked':16384}
base=D/'baseline-plain-1x';original=D/'original-plain-1x'
for label in ['mural','card','naming','naming-right']:
 a=np.array(Image.open(base/(label+'.png')).convert('RGB'));b=np.array(Image.open(original/(label+'.png')).convert('RGB'))
 diff=np.any(a!=b,axis=2);total=int(diff.sum())
 if label.startswith('naming'):diff[48:90,248:281]=False
 outside=int(diff.sum());assert outside==0,(label,total,outside)
 report['image_comparisons']['baseline_vs_original_'+label]={'different_pixels_total':total,'different_pixels_excluding_animated_Ryu_preview':outside}
# Common-font legend is the only intended change to the default keyboard naming screen.
f=D/'keyboard-plain-1x-release/naming.png'
if f.exists():
 a=np.array(Image.open(base/'naming.png').convert('RGB'));b=np.array(Image.open(f).convert('RGB'));diff=np.any(a!=b,axis=2)
 total=int(diff.sum());diff[48:90,248:281]=False;diff[49:89,178:198]=False
 outside=int(diff.sum());assert outside==0,('keyboard unexpected changes',outside)
 report['image_comparisons']['baseline_vs_release_keyboard_naming']={'different_pixels_total':total,'different_pixels_excluding_legend_and_animated_Ryu':outside}
backups=json.loads((D/'backups.json').read_text(encoding='utf-8'));patch=[]
for name,old in backups.items():
 current=W/name;before=D/old['backup'];assert sha(before)==old['sha256']
 if 'build-release' in name:
  assert sha(current)==old['sha256'],name
  report['production_preferences'][name]={'unchanged':True,'sha256':sha(current)}
 else:patch.extend(difflib.unified_diff(before.read_text(encoding='utf-8').splitlines(True),current.read_text(encoding='utf-8').splitlines(True),fromfile='before/'+name,tofile='after/'+name))
(D/'integration.patch').write_text(''.join(patch),encoding='utf-8')
main=W/'BoF3 PSXRecomp/psxrecomp-src-nightly-20260910-ed55299be3/runtime/src/main.cpp'
b=main.read_bytes().replace(b'#include "host_input_prompt.h"\n',b'').replace(b'    host_input_prompt_sample(s + 1);\n',b'')
# main.cpp uses LF, including the appended include.
b=b.removesuffix(b'\n#include "host_input_prompt_bridge.inc"\n')
old_main=backups[str(main.relative_to(W))]['sha256']
assert hashlib.sha256(b).hexdigest()==old_main,'Main bridge removal must recover the Turbo-pinned source exactly'
report['turbo_main_bridge_stripping_recovers_previous_pin']=True
for name in ['guard-test.log','host-bridge-test.log']:
 text=(D/name).read_text(encoding='utf-8-sig');assert 'PASS:' in text;report[name]=text.strip()
report['notes'] += ['xbox-wide-4x-final stalled at boot frame 550 before prompt replacement; retained as failed. The same copied build passed keyboard-plain-1x-final and keyboard-wide-4x-remap-final; later release runs also passed.', 'xbox-wide-4x-release-load loaded the save. Its historical party-menu capture is an indoor scene after input, not evidence of an opened party menu.', 'Diagnostic button injection validates navigation; SDL process-local virtual devices validate host classification/remaps/hotplug. Physical Bluetooth and keyboard handoff remains a user check.', 'Original/auto/Xbox initial routes predate small-font aliases/SELECT and keyboard styling refinements; exact executable versions are listed per run.']
report['source_hashes']={}
for folder,pattern in [(G/'native','button_prompt*'),(main.parent,'host_input_prompt*'),(main.parent.parent/'include','host_input_prompt*')]:
 for p in folder.glob(pattern):report['source_hashes'][str(p.relative_to(W))]=sha(p)
(D/'validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('PASS: evidence audit;',len(report['runs']),'recorded runs including retained failures,',len(report['font_comparisons']),'exact full-font checks, original fallback/image checks, production preferences and Turbo pin.')
print('Final executable:',report['final_executable_sha256'])
