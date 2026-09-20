"""Game-owned correction for eight BREAK no-ops emitted in the extended command body.
Uses the same psx_break helper as dirty_ram_interp and the strict translator.
Fails closed on a source or generated-code mismatch; idempotent after regeneration.
"""
from pathlib import Path
import argparse,hashlib,json,re,struct
R=Path(__file__).resolve().parents[1];G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII';O=R/'coverage/motion-commands-native'
parser=argparse.ArgumentParser();parser.add_argument('--generated-dir',type=Path,default=G/'generated-motion-commands-overlays');args=parser.parse_args()
source=(R/'coverage/ghidra-input/GAME-section-00-80195800.bin').read_bytes()
assert hashlib.sha256(source).hexdigest()=='1663ff2e78134fe15f3cae6fb4074acf14b68b79cfa02be0c7651eaf6a1728ff'
expected={0x801a9f48:0x0007000d,0x801a9f60:0x0006000d,0x801a9fdc:0x0007000d,0x801a9ff4:0x0006000d,0x801aa030:0x0007000d,0x801aa048:0x0006000d,0x801aa0f8:0x0007000d,0x801aa110:0x0006000d}
candidates=[]
for p in args.generated_dir.glob('overlays_static_*.c'):
 s=p.read_text(encoding='utf-8')
 if 'Static overlay translation unit' in s and 'ov_001A9DE8_7DB51C2D_' in s:candidates.append((p,s))
assert len(candidates)==1
p,s=candidates[0];original=s;evidence=[]
for pc,opcode in expected.items():
 assert struct.unpack_from('<I',source,pc-0x80195800)[0]==opcode
 code=(opcode>>6)&0xfffff
 suffix=f'/* 0x{pc:08X}: 0x{opcode:08X} */'
 replacement=f'psx_break(cpu, 0x{code:05X}u, 0x{pc:08X}u); return;  {suffix}'
 pattern=r'/\* break\('+str(code)+r'\) [^\n]*?trap, no-op in recompiler \*/  '+re.escape(suffix)
 matches=list(re.finditer(pattern,s))
 if matches:
  assert len(matches)==1;s=re.sub(pattern,lambda _:replacement,s)
 else:assert s.count(replacement)==1,(hex(pc),'missing or changed BREAK translation')
 evidence.append({'pc':f'0x{pc:08X}','opcode':f'0x{opcode:08X}','break_code':f'0x{code:05X}','generated_statement':replacement})
assert 'trap, no-op in recompiler' not in s
if s!=original:p.write_text(s,encoding='utf-8')
(O/'break-translation-fix.json').write_text(json.dumps({'generated_file':str(p.relative_to(G)),'sites':evidence,'behavior':'Matches dirty-RAM baseline psx_break: report guest PC/code and terminate on BREAK; this is not full hardware exception emulation.'},indent=2)+'\n',encoding='utf-8')
print('Verified eight command BREAK sites use the baseline runtime trap handler.')
