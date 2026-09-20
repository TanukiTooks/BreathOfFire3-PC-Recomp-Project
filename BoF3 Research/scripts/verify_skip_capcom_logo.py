from pathlib import Path
from PIL import Image
import json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'coverage/skip-capcom-logo';G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII';F=R.parent/'BoF3 PSXRecomp/psxrecomp-src-nightly-20260910-ed55299be3';runs={k:json.loads((O/k/'startup.json').read_text()) for k in ['baseline','off','on']}
compared=[]
for a,b in zip(runs['baseline'],runs['off']):
 assert a['target']==b['target']
 if 'capture_method' in a['frame'] or 'capture_method' in b['frame']:continue
 target=a['target'];pa=O/'baseline'/f'frame-{target}.png';pb=O/'off'/f'frame-{target}.png'
 with Image.open(pa) as ia,Image.open(pb) as ib:assert ia.size==ib.size and ia.tobytes()==ib.tobytes(),('frame mismatch',target)
 compared.append(target)
assert len([t for t in compared if 650<=t<=950])>=3
assert runs['baseline'][-1]['fmv']['mdec_decode_count']==220
assert runs['off'][-1]['fmv']['mdec_decode_count']==220
assert all(x['fmv']['mdec_decode_count']==0 for x in runs['on'])
for mode in runs:
 d=O/mode;assert json.loads((d/'probe-result.json').read_text())['status']=='complete';assert json.loads((d/'loaded-save.json').read_text())['outer_phase']==0
 assert json.loads((d/'run.json').read_text())['original_cards_unchanged']
for label in ['initial','cancel','confirm']:
 values=[json.loads((O/m/'probe-result.json').read_text())[label] for m in runs];assert all(x==values[0] for x in values)
for label in ['card0','card1','card0-return','cancel','reenter','confirm','load-prompt']:
 states=[json.loads((O/m/(label+'.json')).read_text()) for m in runs]
 for key in ['slot','outer_phase','menu_phase','mask']:assert len({x[key] for x in states})==1,(label,key)
originals=json.loads((O/'original-cards.json').read_text());assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==sha for p,sha in originals.items())
assert hashlib.sha256((F/'runtime/src/main.cpp').read_bytes()).hexdigest()=='5b97adfc2dc3ef22ba26ccca1de170069974bc3964f116a08356780682ae6a1e'
for row in json.loads((R/'coverage/widescreen-menu-background/generated-adjustments.json').read_text())['files']:
 # That report hashes normalized text, as does the regeneration patcher.
 s=(G/'generated-scenario01-events-overlays'/row['file']).read_text(encoding='utf-8');assert hashlib.sha256(s.encode()).hexdigest()==row['patched_sha256']
result={'passed':True,'off_matches_baseline_frames':compared,'logo_mdec_decodes':{'baseline':220,'off':220,'on':0},'copied_save_load_passed':['baseline','off','on'],'card_states_match':True,'original_cards_unchanged':True,'turbo_main_and_widescreen_menu_units_unchanged':True,'on_mural_visual_evidence':'on/frame-1500.png','on_title_visual_evidence':'on/frame-2500.png','exe_sha256':hashlib.sha256((G/'build-release/Breath_of_Fire_III___PSXRecomp.exe').read_bytes()).hexdigest(),'scope':'Headless startup and copied-save regression; actual WinForms persistence and visual layout checked separately. Transition frames with disabled display are recorded but not used for image equality.'}
(O/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
