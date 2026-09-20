from pathlib import Path
from PIL import Image,ImageChops
import hashlib,json,re,zlib
R=Path(__file__).resolve().parents[1];O=R/'coverage/card-native';G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII'
result={'status':'passed','routine':'bof3_card_selection_update','entry':'0x801E5320','bytes':388,'checks':[],'limitations':['Headless targeted regression, not a full playthrough or audio/controller presentation test.','Checks confirm the native entry is dispatched; the six dependency calls retain the existing runtime routing.','Aggregate native percentages and whole-game completeness are not inferred.']}
for stage in ['card0','card1','card0-return','cancel','reenter','confirm']:
 a=json.loads((O/'baseline'/f'{stage}.json').read_text());b=json.loads((O/'native'/f'{stage}.json').read_text());keys=['slot','outer_phase','menu_phase','mask'];assert all(a[k]==b[k] for k in keys),(stage,a,b)
 ia=Image.open(O/'baseline'/f'{stage}.png').convert('RGB');ib=Image.open(O/'native'/f'{stage}.png').convert('RGB');assert ia.size==ib.size
 diff=ImageChops.difference(ia,ib);bbox=diff.getbbox();pixels=[(x,y) for y in range(ia.height) for x in range(ia.width) if ia.getpixel((x,y))!=ib.getpixel((x,y))]
 border_only=all(48<=x<=256 and 54<=y<=105 and (x<=49 or x>=255 or y<=55 or y>=104) for x,y in pixels)
 assert not pixels or (stage=='confirm' and border_only),(stage,bbox,len(pixels))
 result['checks'].append({'stage':stage,'state':{k:b[k] for k in keys},'state_matches_baseline':True,'identical_pixels':not pixels,'different_pixels':len(pixels),'difference_bbox':bbox,'save_outline_only':bool(pixels) and border_only})
log=(O/'native/stderr.log').read_text();hits=[int(x) for x in re.findall(r'\[bof3-native-card\] entry=0x801E5320 handled=1 count=(\d+)',log)];assert hits and max(hits)>=8
result['native_entry_observations_at_least']=max(hits)
old=(G/'generated-startup-card-overlays/overlays_static.c').read_text();new=(G/'generated-identified-card-overlays/overlays_static.c').read_text();pattern=r'^void (\w+)\(CPUState \*cpu\);'
oldf=set(re.findall(pattern,old,re.M));newf=set(re.findall(pattern,new,re.M));assert oldf and oldf<=newf
added=sorted(newf-oldf);assert len(added)==17 and all('_001E5320_' in x for x in added)
result['preserved_old_generated_identities']=len(oldf);result['added_generated_entries_and_continuations']=added
assert '0x001E5320u, 0x184u' in new
recipe=json.loads((O/'recipe.json').read_text());source=(R/'coverage/ghidra-input/STATUS-section-00-801D0C00.bin').read_bytes();code=source[0x801e5320-0x801d0c00:0x801e54a4-0x801d0c00]
assert hashlib.sha256(code).hexdigest()==recipe['routine_sha256'] and zlib.crc32(code)==0xdc06d5a7
result['guard_crc32']='0xDC06D5A7';result['routine_sha256']=recipe['routine_sha256'];result['direct_dependencies']=recipe['direct_dependencies']
original=json.loads((O/'baseline/original-card-hashes.json').read_text(encoding='utf-8-sig'))
for card in original:assert hashlib.sha256(Path(card['Path']).read_bytes()).hexdigest().upper()==card['Hash']
result['original_memory_card_hashes_unchanged']=True
assert json.loads((O/'native/probe-result.json').read_text())['status']=='complete'
assert (O/'native/loaded-save.png').exists()
loaded=json.loads((O/'native/loaded-save.json').read_text());assert loaded['outer_phase']==0 and loaded['frame']>json.loads((O/'native/confirm.json').read_text())['frame']
result['loaded_save_checkpoint']=loaded['frame']
result['baseline_exe_sha256']=hashlib.sha256((G/'build-release/Breath_of_Fire_III___PSXRecomp.before-card-native.exe').read_bytes()).hexdigest();result['native_exe_sha256']=hashlib.sha256((G/'build-release/Breath_of_Fire_III___PSXRecomp.exe').read_bytes()).hexdigest()
(O/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS: six state checkpoints, screenshot checks, native-entry trace, guarded source bytes, retained prior overlay identities and original card hashes.')
print('Native entries observed at least:',max(hits))
