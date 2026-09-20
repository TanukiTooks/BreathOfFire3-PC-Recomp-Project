"""Repeatable, opt-in BoF3 tiled-background adjustment at two verified guest PCs.
All native copies/continuations are patched; original guest code and dispatch guards stay intact.
"""
from pathlib import Path
import argparse,hashlib,json,struct
R=Path(__file__).resolve().parents[1];G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII';O=R/'coverage/widescreen-menu-background'
p=argparse.ArgumentParser();p.add_argument('--generated-dir',type=Path,default=G/'generated-scenario01-events-overlays');a=p.parse_args()
source=(R/'coverage/ghidra-input/STATUS-section-00-801D0C00.bin').read_bytes()
assert hashlib.sha256(source).hexdigest()=='a47d32865283a01ce87b2f2f8cb19d3305525659b95a8feb4f307eddf63a8cb1'
for pc,w in [(0x801df328,0xa6360008),(0x801df3d0,0x2c420005)]:assert struct.unpack_from('<I',source,pc-0x801d0c00)[0]==w
old1='{ uint32_t _pgxa = cpu->gpr[17] + 8; g_debug_last_store_pc = 0x801DF328u; psx_store_cycle_barrier(); cpu->write_half(cpu->gpr[17] + 8, (uint16_t)cpu->gpr[22]);\n    PGXP_STORE(0xA6360008u, _pgxa, cpu->gpr[22]); }  /* 0x801DF328: 0xA6360008 */'
new1='{ uint32_t _pgxa = cpu->gpr[17] + 8;\n    uint32_t _bof3_x = cpu->gpr[22] - (uint32_t)bof3_menu_background_padding();\n    g_debug_last_store_pc = 0x801DF328u; psx_store_cycle_barrier(); cpu->write_half(cpu->gpr[17] + 8, (uint16_t)_bof3_x);\n    PGXP_STORE(0xA6360008u, _pgxa, _bof3_x); }  /* 0x801DF328: 0xA6360008 */'
old2='cpu->gpr[2] = (cpu->gpr[2] < (uint32_t)5) ? 1 : 0;  /* 0x801DF3D0: 0x2C420005 */'
new2='cpu->gpr[2] = (cpu->gpr[2] < bof3_menu_background_pairs()) ? 1 : 0;  /* 0x801DF3D0: 0x2C420005 */'
decls='\n/* BoF3 widescreen-only background tiling; preserves texture/palette and UI coordinates. */\nextern int32_t bof3_menu_background_padding(void);\nextern uint32_t bof3_menu_background_pairs(void);\n'
rows=[]
for path in a.generated_dir.glob('overlays_static_*.c'):
 text=path.read_text(encoding='utf-8');before=text;counts=[]
 for old,new,marker in [(old1,new1,'/* 0x801DF328: 0xA6360008 */'),(old2,new2,'/* 0x801DF3D0: 0x2C420005 */')]:
  n=text.count(marker);assert text.count(old)+text.count(new)==n,(path.name,marker,'changed source shape');counts.append(n);text=text.replace(old,new)
 if any(counts):
  assert '#include "psx_runtime.h"' in text
  if decls not in text:text=text.replace('#include "psx_runtime.h"','#include "psx_runtime.h"'+decls,1)
  if text!=before:path.write_text(text,encoding='utf-8')
  rows.append({'file':path.name,'x_store_sites':counts[0],'pair_limit_sites':counts[1],'patched_sha256':hashlib.sha256(text.encode()).hexdigest()})
assert rows and any(r['file']=='overlays_static_0009.c' for r in rows)
(O/'generated-adjustments.json').write_text(json.dumps({'files':rows,'source_sha256':hashlib.sha256(source).hexdigest(),'guest_code_and_dispatch_guards_unchanged':True},indent=2)+'\n',encoding='utf-8')
print('Verified widescreen background sites:',sum(r['x_store_sites'] for r in rows),'X stores and',sum(r['pair_limit_sites'] for r in rows),'loop limits in',len(rows),'units.')
