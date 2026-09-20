from pathlib import Path
import json,hashlib,struct
from PIL import Image
R=Path(__file__).resolve().parents[1];G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII';D=G/'assets/button-prompts/xbox';O=R/'coverage/button-prompts'
m=json.loads((D/'manifest.json').read_text(encoding='utf-8'));v=struct.unpack('<524288H',(O/'discovery/naming.vram').read_bytes())
lines=['/* Generated from the user-supplied PNG exports; do not edit. */','#pragma once','#include <stdint.h>','typedef struct Bof3PromptIcon { int w,h; const uint16_t *pixels; } Bof3PromptIcon;']
def array(name,values):
 lines.append(f'static const uint16_t {name}[{len(values)}] = {{')
 for i in range(0,len(values),16):lines.append('    '+','.join(f'0x{x:04x}' for x in values[i:i+16])+',')
 lines.append('};')
icons=[]
for name,item in m['icons'].items():
 p=D/item['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'];im=Image.open(p).convert('RGBA');data=[]
 for r,g,b,a in im.get_flattened_data():
  c=(r>>3)|((g>>3)<<5)|((b>>3)<<10)
  data.append((c or 0x8000) if a>=128 else 0)
 var='icon_'+name.replace('-','_');array(var,data);icons.append((name,*im.size,var))
lines.append('enum { '+', '.join('ICON_'+x[0].replace('-','_').upper() for x in icons)+' };')
lines.append('static const Bof3PromptIcon prompt_icons[] = {')
lines.extend(f'    {{{w},{h},{var}}},' for _,w,h,var in icons);lines.append('};')
array('prompt_scratch_original',[v[y*1024+960+x] for y in range(32) for x in range(32)])
array('prompt_palettes_original',list(v[480*1024:480*1024+256]))
# Face/shoulder buttons, START/SELECT split labels and exact small-text face aliases.
tiles=[(232,0,4),(224,0,7),(216,0,5),(240,0,6),(0,16,8),(8,16,10),(16,16,9),(24,16,11),(32,16,14),(40,16,14),(48,16,15),(56,16,15),(64,16,15),(152,136,4),(160,136,7),(144,136,5),(168,136,6)]
for i,(u,y,_) in enumerate(tiles):array(f'prompt_tile_{i}',[v[(y+dy)*1024+960+u//4+x] for dy in range(8) for x in range(2)])
lines+=['typedef struct Bof3PromptGlyph { int u,v,logical,part; const uint16_t *original; } Bof3PromptGlyph;','static const Bof3PromptGlyph prompt_glyphs[] = {']
lines.extend(f'    {{{u},{y},{logical},{i-8 if 8<=i<=9 else i-10 if 10<=i<=12 else 0},prompt_tile_{i}}},' for i,(u,y,logical) in enumerate(tiles));lines.append('};')
(G/'native/button_prompt_assets.h').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Compiled 39 source icons and exact font guards into the game asset header.')
