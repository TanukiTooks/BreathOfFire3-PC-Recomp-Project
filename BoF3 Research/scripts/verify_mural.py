"""Validate the mural reveal against unchanged original-frame output."""
from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'coverage/mural';G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII';F=R.parent/'BoF3 PSXRecomp/psxrecomp-src-nightly-20260910-ed55299be3'
def pixels(p):return np.array(Image.open(p).convert('RGB'))
comparisons=[]
code=(O/'GAME-section-01-801D0C00.bin').read_bytes()[0xcf8:0xf00]
for mode in ['native-plain','native-wide']:
 rows=json.loads((O/mode/'samples.json').read_text())
 for row in rows:
  t=row['target'];a=pixels(O/'baseline-plain'/f'frame-{t}.png');b=pixels(O/mode/f'frame-{t}.png');n=int(np.any(a!=b,axis=2).sum());assert n==0,(mode,t,n);comparisons.append({'mode':mode,'frame':t,'changed_pixels':n})
  if row['mural_phase']:assert bytes.fromhex(row['code'])==code
sides=[]
for t in [1300,1400,1500,1600,1700]:
 a=pixels(O/'native-wide'/f'present-{t}.png');assert a.shape==(720,1280,3)
 left=int(np.any(a[120:600,:150]!=0,axis=2).sum());right=int(np.any(a[120:600,1130:]!=0,axis=2).sum());assert min(left,right)>30000,(t,left,right);sides.append({'frame':t,'left_art_pixels':left,'right_art_pixels':right})
for t in [2000,2200,2600]:
 a=pixels(O/'native-wide'/f'present-{t}.png');assert not a[:,:150].any() and not a[:,1130:].any()
for mode in ['baseline-plain','native-plain','native-wide','native-wide-logo']:
 d=O/mode;complete=json.loads((d/'complete.json').read_text());assert complete['complete'] and complete['card_selection_reached'];assert complete['fmv']['mdec_decode_count']==(220 if mode.endswith('-logo') else 0)
 if mode.startswith('native'):assert json.loads((d/'run.json').read_text())['exe_sha256']==hashlib.sha256((G/'build-release/Breath_of_Fire_III___PSXRecomp.exe').read_bytes()).hexdigest()
logo_rows=json.loads((O/'native-wide-logo/samples.json').read_text());assert any(r['mural_phase'] in (1,2,3) for r in logo_rows);assert logo_rows[-1]['mural_phase']==0
for row in logo_rows:
 if row['mural_phase']==2:
  a=pixels(O/'native-wide-logo'/f"present-{row['target']}.png")
  if row['scroll']>450 and row['scroll']<900:assert a[:,0:150].any() and a[:,1130:].any()
originals=json.loads((O/'original-cards.json').read_text());assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in originals.items())
assert hashlib.sha256((F/'runtime/src/main.cpp').read_bytes()).hexdigest()=='5b97adfc2dc3ef22ba26ccca1de170069974bc3964f116a08356780682ae6a1e'
# Verify earlier game enhancements against their normalized generated-source fingerprints.
for row in json.loads((R/'coverage/widescreen-menu-background/generated-adjustments.json').read_text())['files']:
 assert hashlib.sha256((G/'generated-scenario01-events-overlays'/row['file']).read_text(encoding='utf-8').encode()).hexdigest()==row['patched_sha256']
for row in json.loads((R/'coverage/skip-capcom-logo/generated-adjustments.json').read_text()):
 assert hashlib.sha256((G/'generated-scenario01-events-overlays'/row['file']).read_text(encoding='utf-8').encode()).hexdigest()==row['sha256']
assert json.loads((O/'guard-test.json').read_text())['passed']
result={'passed':True,'original_frame_comparisons':comparisons,'wide_side_content':sides,'title_returns_to_original_framing':True,'logo_on_and_off_passed':True,'card_selection_reached_all_four_runs':True,'original_cards_unchanged':True,'live_mural_body_unchanged':True,'prior_menu_and_logo_generated_changes_preserved':True,'exe_sha256':hashlib.sha256((G/'build-release/Breath_of_Fire_III___PSXRecomp.exe').read_bytes()).hexdigest(),'limits':'Actual OpenGL at 1x internal scale, nearest filtering, windowed. Finite artwork retains black surroundings as it enters/exits. Higher scales and fullscreen not separately tested for this feature; fishing/fairy village deferred.'}
(O/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':True,'exact_original_frame_matches':len(comparisons),'side_checks':len(sides),'exe_sha256':result['exe_sha256']},indent=2))
