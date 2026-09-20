from pathlib import Path
import json,hashlib
from PIL import Image
R=Path(__file__).resolve().parents[1];A=R.parent/'BoF3 PSXRecomp/BreathOfFireIII/assets/title';D=R/'coverage/title-footer'
D.mkdir(parents=True,exist_ok=True)
source=A/'start and licenses.png';raw=source.read_bytes();im=Image.open(source);assert im.mode=='RGB' and im.size==(1672,941)
rects={'press-start.png':(312,342,1370,411),'copyright-japan.png':(67,449,877,511),'copyright-usa.png':(67,521,1608,582)}
rows=[]
for name,box in rects.items():
 crop=im.crop(box);crop.save(A/name,optimize=True);loaded=Image.open(A/name);assert loaded.tobytes()==crop.tobytes()
 rows.append({'file':name,'box':box,'size':crop.size,'sha256':hashlib.sha256((A/name).read_bytes()).hexdigest(),'crop_rgb_exact':True})
assert source.read_bytes()==raw
(D/'asset-import.json').write_text(json.dumps({'source_sha256':hashlib.sha256(raw).hexdigest(),'source_size':im.size,'source_unchanged':True,'black_background':'retained in PNG crops; renderer keys near-black pixels and preserves RGB-on-black appearance','pieces':rows},indent=2),encoding='utf-8')
print('Imported 3 exact RGB crops, with original source sheet unchanged.')
