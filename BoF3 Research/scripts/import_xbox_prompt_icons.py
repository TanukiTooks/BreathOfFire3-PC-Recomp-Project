"""Lossless sprite-sheet import for the six owner-supplied Figma exports.
No artwork generation, repainting, filtering or source-file modification.
"""
from pathlib import Path
import hashlib,json,html
from PIL import Image
R=Path(__file__).resolve().parents[1]
D=R.parent/'BoF3 PSXRecomp/BreathOfFireIII/assets/button-prompts/xbox'
O=D/'icons';O.mkdir(parents=True,exist_ok=True)
E=R/'coverage/button-prompts';E.mkdir(parents=True,exist_ok=True)
SHEETS={
13:([f'{b}-{style}' for style in ['color','solid','outline'] for b in ['a','b','x','y']],(464,24)),
14:(['lb','rb','lt','rt'],(156,24)),
15:(['dpad','dpad-left','dpad-up','dpad-right','dpad-down'],(184,24)),
16:(['right-stick-all','left-stick-all','left-stick-round','right-stick-round','left-stick-up','right-stick-up','left-stick-down','right-stick-down','left-stick-right','right-stick-right','left-stick-left','right-stick-left'],(467,26)),
17:(['left-stick','right-stick','left-stick-press','right-stick-press'],(150,26)),
18:(['menu','view'],(64,24)),
}
def sha(b):return hashlib.sha256(b).hexdigest()
manifest={'format_version':1,'family':'xbox','source_url':'https://www.figma.com/community/file/1271153059120916114/xbox-controller-icons-free','source_kind':'user-supplied transparent PNG exports','default_face_style':'color','sheets':[],'icons':{},'sdl_sources':{}}
validation=[]
for num,(names,size) in SHEETS.items():
 p=D/f'Frame {num}.png';before=p.read_bytes();im=Image.open(p);assert im.mode=='RGBA' and im.size==size,(p,im.mode,im.size)
 alpha=im.getchannel('A');assert alpha.getextrema()==(0,255)
 occupied=[alpha.crop((x,0,x+1,im.height)).getbbox() is not None for x in range(im.width)]
 runs=[];start=None
 for x,v in enumerate(occupied+[False]):
  if v and start is None:start=x
  if not v and start is not None:runs.append((start,x));start=None
 assert len(runs)==len(names),(p,runs)
 restored=Image.new('RGBA',im.size,(0,0,0,0))
 for name,(x0,x1) in zip(names,runs):
  region=im.crop((x0,0,x1,im.height));bbox=region.getchannel('A').getbbox();assert bbox
  y0,y1=bbox[1],bbox[3];icon=im.crop((x0,y0,x1,y1));dest=O/(name+'.png')
  icon.save(dest,optimize=True)
  loaded=Image.open(dest).convert('RGBA');assert loaded.tobytes()==icon.tobytes()
  restored.paste(loaded,(x0,y0))
  manifest['icons'][name]={'file':'icons/'+dest.name,'source_sheet':p.name,'source_rect':[x0,y0,x1-x0,y1-y0],'size':list(icon.size),'sha256':sha(dest.read_bytes()),'rgba_sha256':sha(icon.tobytes())}
 assert restored.tobytes()==im.tobytes(),f'Lossless reconstruction failed: {p}'
 assert p.read_bytes()==before
 manifest['sheets'].append({'file':p.name,'size':list(im.size),'sha256':sha(before),'icon_count':len(names)})
 validation.append({'file':p.name,'icons':len(names),'source_unchanged':True,'decoded_rgba_reconstruction_exact':True})
# These keys describe physical SDL controller sources, not fixed PSX actions.
# The runtime resolves input.ini/per-GUID remaps before lookup.
manifest['sdl_sources']={
 'a':'a-color','b':'b-color','x':'x-color','y':'y-color',
 'leftshoulder':'lb','rightshoulder':'rb','lefttrigger+':'lt','righttrigger+':'rt',
 'leftstick':'left-stick-press','rightstick':'right-stick-press','start':'menu','back':'view',
 'dpup':'dpad-up','dpdown':'dpad-down','dpleft':'dpad-left','dpright':'dpad-right',
 'leftx-':'left-stick-left','leftx+':'left-stick-right','lefty-':'left-stick-up','lefty+':'left-stick-down',
 'rightx-':'right-stick-left','rightx+':'right-stick-right','righty-':'right-stick-up','righty+':'right-stick-down'}
assert len(manifest['icons'])==39
assert all(v in manifest['icons'] for v in manifest['sdl_sources'].values())
(D/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
(E/'icon-import-validation.json').write_text(json.dumps({'icons':39,'physical_source_mappings':len(manifest['sdl_sources']),'source_pngs_modified':False,'checks':validation},indent=2)+'\n',encoding='utf-8')
# A local contact sheet references the exact exported assets; CSS sets display
# sizes without altering the PNG files or creating new versions of the art.
rows=[]
for name,icon in manifest['icons'].items():
 cells=''.join(f'<td><img src="{html.escape(icon["file"])}" height="{size}" alt="{html.escape(name)}"></td>' for size in [8,12,16,24])
 rows.append(f'<tr><th scope="row">{html.escape(name)}</th>{cells}</tr>')
(D/'preview.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Xbox prompt assets</title><style>body{font:16px system-ui;background:#202329;color:#e6e9ed;margin:32px;max-width:900px}h1{font-size:24px}p{line-height:1.5;color:#bdc6d3}table{border-collapse:collapse;width:100%}th,td{padding:12px;border-bottom:1px solid #3b414b;text-align:center}th:first-child{text-align:left;font-weight:500}td{width:15%;background:#292b2a}img{width:auto;vertical-align:middle}a{color:#96c6ff}</style><h1>Xbox button prompts</h1><p>39 icons extracted losslessly from the six supplied frames. Columns show possible display heights. These are asset previews. The game uses the colored face buttons for supported Xbox prompts; see the button-prompts research report for runtime screenshots.</p><table><thead><tr><th>Icon</th><th>8 px</th><th>12 px</th><th>16 px</th><th>24 px</th></tr></thead><tbody>'''+''.join(rows)+'''</tbody></table><p><a href="https://www.figma.com/community/file/1271153059120916114/xbox-controller-icons-free">Original Figma source</a></p></html>''',encoding='utf-8')
print('Imported 39 icons from 6 sheets; all reconstructed pixel-for-pixel. 24 physical input mappings resolve.')
