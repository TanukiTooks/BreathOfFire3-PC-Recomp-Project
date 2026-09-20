"""Reapply the opt-in logo skip at the verified LOGO-only Start-button test."""
from pathlib import Path
import argparse,hashlib,json,struct
R=Path(__file__).resolve().parents[1];G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII';O=R/'coverage/skip-capcom-logo';O.mkdir(parents=True,exist_ok=True)
p=argparse.ArgumentParser();p.add_argument('--generated-dir',type=Path,default=G/'generated-scenario01-events-overlays');a=p.parse_args()
b=(R/'coverage/ghidra-input/LOGO-payload-801CE000.bin').read_bytes();assert hashlib.sha256(b).hexdigest()=='7a2cbfa8b165f1aaa4c3f415c67d51c32c5aed6a2d0fa7c7d1cbe2744a37c87c'
assert struct.unpack_from('<III',b,0xe30)==(0x30420800,0x14400005,0)
old='cpu->gpr[2] = cpu->gpr[2] & 0x0800;  /* 0x801CEE30: 0x30420800 */'
new='cpu->gpr[2] = bof3_logo_skip_button(cpu->gpr[2]) & 0x0800;  /* 0x801CEE30: 0x30420800 */'
decl='\n/* Optional logo-only Start-button exit; guest instructions remain unchanged. */\nextern uint32_t bof3_logo_skip_button(uint32_t buttons);\n'
rows=[]
for path in a.generated_dir.glob('overlays_static_*.c'):
 s=path.read_text(encoding='utf-8');before=s;n=s.count('/* 0x801CEE30: 0x30420800 */');assert s.count(old)+s.count(new)==n,(path,'unknown instruction shape')
 if not n:continue
 assert '#include "psx_runtime.h"' in s
 s=s.replace(old,new)
 if decl not in s:s=s.replace('#include "psx_runtime.h"','#include "psx_runtime.h"'+decl,1)
 if before!=s:path.write_text(s,encoding='utf-8')
 rows.append({'file':path.name,'sites':n,'sha256':hashlib.sha256(s.encode()).hexdigest()})
assert rows,'No verified logo skip test found'
(O/'generated-adjustments.json').write_text(json.dumps(rows,indent=2)+'\n');print('Verified logo-only skip sites:',sum(r['sites'] for r in rows))
