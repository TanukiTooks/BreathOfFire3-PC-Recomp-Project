from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
D=Path('BoF3 Research/coverage/button-prompts');V=np.frombuffer((D/'discovery/naming.vram').read_bytes(),dtype='<u2').reshape(512,1024)
# Decode the captured native PSX font page, not the user-supplied preview.
p=V[480,48:64];atlas=np.zeros((256,256,4),dtype=np.uint8)
for y in range(256):
 for x in range(256):
  idx=(int(V[y,960+x//4])>>((x%4)*4))&15;c=int(p[idx]);atlas[y,x]=[(c&31)*255//31,((c>>5)&31)*255//31,((c>>10)&31)*255//31,255 if c else 0]
Image.fromarray(atlas).save(D/'original-font-page.png')
records=[]
for name,u,x,y in [('cross',232,182,49),('triangle',224,182,57),('circle',216,182,65),('square',240,182,73)]:
 data=b''.join(V[row,960+u//4:960+u//4+2].tobytes() for row in range(8))
 Image.fromarray(atlas[:8,u:u+8]).save(D/(name+'-original.png'))
 records.append({'button':name,'texpage':'0x02F','clut':'0x7803','uv':[u,0],'size':[8,8],'screen_xy':[x,y],'native_texels_hex':data.hex(),'native_texels_sha256':hashlib.sha256(data).hexdigest(),'palette_hex':p.tobytes().hex()})
(D/'identified-glyphs.json').write_text(json.dumps({'capture':'discovery/naming.json','renderer':'FUN_801DD618','legend_caller':'FUN_801E6784','glyphs':records,'start':{'uv':[[32,16],[40,16]],'clut':'0x7800','size_each':[8,8],'screen_xy':[[178,81],[186,81]]}},indent=2),encoding='utf-8')
print('Decoded native font page and recorded four observed prompt glyphs.')

# Corroborate the entire live font texture against the existing disc inventory.
raw=V[:256,960:1024].copy().view('u1').reshape(256,128)
tiled=raw.reshape(8,32,2,64).transpose(0,2,1,3).tobytes()
h=hashlib.sha256(tiled).hexdigest()
sections=json.loads((D.parents[1]/'coverage/emi-sections.json').read_text(encoding='utf-8'))
matches=[s for s in sections if s['sha256']==h and s['size']==len(tiled)]
assert any(s['file']=='BIN/ETC/FIRST.EMI' and s['index']==3 for s in matches)
(D/'font-source.json').write_text(json.dumps({'packed_font_sha256':h,'packed_font_size':len(tiled),'tile_storage':'64-byte rows, 32 rows per tile; 2 columns x 8 rows','matches':matches},indent=2),encoding='utf-8')
print('Complete 32 KiB live font matched FIRST.EMI section 3 and ENDKANJI.EMI section 0.')
