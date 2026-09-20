"""Apply guarded terrain bounds and the earlier grid decision to compiled copies."""
from pathlib import Path
import struct,hashlib,json
R=Path(__file__).resolve().parents[1];G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII';O=R/'coverage/widescreen-terrain-release'
O.mkdir(parents=True,exist_ok=True)
b=(G/'disc/SLUS_004.22').read_bytes();base=struct.unpack_from('<I',b,0x18)[0]
for pc,word in [(0x801533ec,0x24420032),(0x801533f0,0x3042ffff),(0x801533f4,0x2c4201a5),(0x801533f8,0x10400009)]:assert struct.unpack_from('<I',b,0x800+pc-base)[0]==word
old1='{ uint32_t _pgx1 = cpu->gpr[2]; cpu->gpr[2] = cpu->gpr[2] + 50;\n    PGXP_ALU(0x24420032u, cpu->gpr[2], _pgx1, 0x00000032u); }  /* 0x801533EC: 0x24420032 */'
new1='{ uint32_t _pgx1 = cpu->gpr[2]; uint32_t _bof3_imm = (uint32_t)bof3_terrain_immediate(0x801533ECu,0x24420032u); cpu->gpr[2] = cpu->gpr[2] + _bof3_imm;\n    PGXP_ALU(0x24420032u, cpu->gpr[2], _pgx1, _bof3_imm); }  /* 0x801533EC: 0x24420032 */'
old2='cpu->gpr[2] = (cpu->gpr[2] < (uint32_t)421) ? 1 : 0;  /* 0x801533F4: 0x2C4201A5 */'
new2='cpu->gpr[2] = (cpu->gpr[2] < (uint32_t)bof3_terrain_immediate(0x801533F4u,0x2C4201A5u)) ? 1 : 0;  /* 0x801533F4: 0x2C4201A5 */'
old3='int _bc_80153224 = (cpu->gpr[3] != cpu->gpr[2]);  /* save branch cond before delay slot */'
new3='int _bc_80153224 = bof3_terrain_grid_branch(0x80153224u,0x14620003u,(cpu->gpr[3] != cpu->gpr[2]));  /* save branch cond before delay slot */'
grid_decl='extern int bof3_terrain_grid_branch(uint32_t pc,uint32_t insn,int taken);\n'
assert struct.unpack_from('<I',b,0x800+0x80153224-base)[0]==0x14620003
# Verify the read-only native guards against the original executable too.
import re
guard=(G/'native/terrain_widescreen.c').read_text(encoding='utf-8').split('grid_guard[]={',1)[1].split('};',1)[0]
pairs=[(int(a,16),int(w,16)) for a,w in re.findall(r'\{0x([0-9a-f]+)u,0x([0-9a-f]+)u\}',guard)]
assert len(pairs)==13
for pc,word in pairs:assert struct.unpack_from('<I',b,0x800+pc-base)[0]==word
rows=[];decl='\nextern int32_t bof3_terrain_immediate(uint32_t pc,uint32_t insn);\n'
for folder,pattern in [(G/'generated','*_full_*.c'),(G/'generated-scenario01-events-overlays','overlays_static_*.c')]:
 for p in folder.glob(pattern):
  text=p.read_text(encoding='utf-8');before=text;counts=[]
  for old,new,marker in [(old1,new1,'/* 0x801533EC: 0x24420032 */'),(old2,new2,'/* 0x801533F4: 0x2C4201A5 */'),(old3,new3,'int _bc_80153224 =')]:
   n=text.count(marker);assert text.count(old)+text.count(new)==n,(p,marker,'source shape changed');counts.append(n);text=text.replace(old,new)
  if any(counts):
   include=next(line for line in text.splitlines() if line.startswith('#include '))
   if decl not in text:text=text.replace(include,include+decl,1)
   if counts[2] and grid_decl not in text:text=text.replace(include,include+'\n'+grid_decl,1)
   if text!=before:p.write_text(text,encoding='utf-8')
   rows.append({'file':str(p.relative_to(G)),'bias_sites':counts[0],'bound_sites':counts[1],'grid_sites':counts[2],'sha256':hashlib.sha256(text.encode()).hexdigest()})
assert sum(x['grid_sites'] for x in rows)==1
assert rows and sum(x['bias_sites'] for x in rows)==sum(x['bound_sites'] for x in rows)
(O/'generated-adjustments.json').write_text(json.dumps({'files':rows,'source_sha256':hashlib.sha256(b).hexdigest(),'guest_code_unchanged':True},indent=2),encoding='utf-8')
print('Verified terrain native bias/bound pairs:',sum(x['bias_sites'] for x in rows),'in',len(rows),'units.')
