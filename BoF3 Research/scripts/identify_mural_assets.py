"""Reconstruct and verify mural assets from the original disc archive."""
from pathlib import Path
import json,hashlib,numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'coverage/mural';rows=json.loads((R/'coverage/emi-sections.json').read_text());source=json.loads((O/'asset-source.json').read_text());b=(O/'DEMO.EMI').read_bytes();assert hashlib.sha256(b).hexdigest()==source['file']['sha256']
texrow=next(r for r in rows if r['file']=='BIN/ETC/DEMO.EMI' and r['index']==6);palrow=next(r for r in rows if r['file']=='BIN/ETC/DEMO.EMI' and r['index']==7)
raw=b[texrow['file_offset']:texrow['file_offset']+texrow['size']];assert hashlib.sha256(raw).hexdigest()==texrow['sha256'];atlas=np.frombuffer(raw,dtype='uint8').reshape(8,16,32,64).transpose(0,2,1,3).reshape(256,1024)
v=np.frombuffer((O/'discovery/mural.vram').read_bytes(),dtype='<u2').reshape(512,1024);assert atlas.tobytes()==v[:256,320:832].copy().tobytes()
canvas=Image.new('RGB',(1021,192));matches=[]
for i in range(4):
 paloff=894464+i*512;assert palrow['file_offset']<=paloff<palrow['file_offset']+palrow['size'];pal=np.frombuffer(b[paloff:paloff+512],dtype='<u2');assert pal.tobytes()==v[487+i,:256].tobytes();pixels=atlas[:192,i*256:(i+1)*256];assert pixels.tobytes()==v[:192,320+i*128:448+i*128].copy().tobytes();rgb=np.stack([(pal&31)*255//31,((pal>>5)&31)*255//31,((pal>>10)&31)*255//31],axis=1).astype('uint8');pic=Image.fromarray(rgb[pixels]);pic.save(O/f'mural-strip-{i}.png');canvas.paste(pic,(255*i,0));matches.append({'strip':i,'texture_sha256':hashlib.sha256(pixels.tobytes()).hexdigest(),'clut_sha256':hashlib.sha256(pal.tobytes()).hexdigest(),'clut_archive_offset':paloff})
canvas.save(O/'mural-artwork.png');(O/'artwork-hashes.json').write_text(json.dumps(matches,indent=2)+'\n');print('PASS: complete source atlas and all four palettes exactly match captured VRAM; reconstructed 1021x192 mural.')
