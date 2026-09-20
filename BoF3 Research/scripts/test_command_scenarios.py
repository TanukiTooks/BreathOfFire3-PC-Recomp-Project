"""Functional differential fixtures: original MIPS vs actual generated bodies.
External callees are explicit MIPS test doubles, not claims about game subsystems.
"""
from pathlib import Path
import json,struct,subprocess,hashlib
R=Path(__file__).resolve().parents[1];O=R/'coverage/command-scenarios';E=O/'build/command_scenarios.exe';O.joinpath('cases').mkdir(exist_ok=True)
GAME=(R/'coverage/ghidra-input/GAME-section-00-80195800.bin').read_bytes();assert hashlib.sha256(GAME).hexdigest()=='1663ff2e78134fe15f3cae6fb4074acf14b68b79cfa02be0c7651eaf6a1728ff'
REC=0x80010000;SCRIPT=0x80011000;CURRENT=0x80012000;CONTROL=0x801a8f94;EXTENDED=0x801a9de8
cases=[]
def case(name,entry,script,cursor=0,offset=None,result=17,patches=(),stubs=(),checks=(),trap=0):cases.append(dict(name=name,entry=entry,script=script,cursor=cursor,offset=offset,result=result,patches=patches,stubs=stubs,checks=checks,trap=trap))
def u8(a,v):return (a,bytes([v&255]))
def u16(a,v):return (a,struct.pack('<H',v&65535))
def u32(a,v):return (a,struct.pack('<I',v&0xffffffff))
def stub(a,value=0):return (a,[0x03e00008,0x24020000|(value&65535)])
case('control_early_exit',CONTROL,[255],offset=0)
case('relative_forward',CONTROL,[1,0,3,255],offset=3)
case('relative_backward',CONTROL,[255,0,0,1,255,253],cursor=3,offset=0)
case('counted_loop',CONTROL,[2,0,3,255],offset=3,checks=[u8(REC+2,0)])
case('skip_two',CONTROL,[10,99,255],offset=2)
case('reset_cursor',CONTROL,[255,0,11],cursor=2,offset=0)
case('ext_ff_wrap',EXTENDED,[255],offset=65535)
case('ext_f2_zero_count',EXTENDED,[242,5,0],offset=2,result=5)
case('ext_f3_zero_count',EXTENDED,[243,7,0,0,20],offset=4,result=7)
case('ext_f4_positive',EXTENDED,[244,0,40,4],offset=3,patches=[u16(CURRENT+0x3e,20)],checks=[u32(CURRENT+0x14,5),u8(REC,128)])
case('ext_f4_negative',EXTENDED,[244,0,20,4],offset=3,patches=[u16(CURRENT+0x3e,40)],checks=[u32(CURRENT+0x14,-5)])
case('ext_f4_zero_duration',EXTENDED,[244,0,30,0],offset=3,patches=[u16(CURRENT+0x3e,20)],checks=[u8(CURRENT+9,1),u32(CURRENT+0x14,10)])
case('ext_f5_clear_flag',EXTENDED,[245],offset=0,patches=[u8(REC,255)],checks=[u8(REC,127)])
case('ext_f6_global',EXTENDED,[246,42],offset=1,checks=[u8(0x80146874,42)])
case('ext_fa_zero_count',EXTENDED,[250,5,0,0x12,0x34],offset=4,result=5,checks=[u16(CURRENT+0x3e,0x1234),u32(CURRENT+0x14,0)])

# Callback bodies are minimal MIPS test doubles; underlying subsystems are not tested.
identity=(0x8015b870,[0x03e00008,0x00801021])
resolve=(0x801ac8f0,[0x9482000a,0x03e00008,0])
case('indirect_offset_resolver',CONTROL,[1,0x40,3,255],offset=3,stubs=[stub(0x801ac8f0,3)])
for opcode,label,x,y in [(4,'equal',7,7),(4,'unequal',7,8),(5,'vars_equal',9,9),(5,'vars_unequal',9,8),(6,'less',8,7),(6,'not_less',7,8),(7,'vars_less',9,8),(7,'vars_not_less',8,9),(8,'mask_set',1,3),(8,'mask_clear',1,2),(9,'vars_mask_set',2,3),(9,'vars_mask_clear',2,1)]:
 selected=7 if ((x==y) if opcode in (4,5) else (y<x) if opcode in (6,7) else bool(x&y)) else 8
 case('condition_'+label,CONTROL,[opcode,x,y,0,7,0,8,255,255],offset=selected,stubs=[identity,resolve])
case('script_callback',CONTROL,[3,2,255],offset=2,result=0x5a,patches=[u16(0x80143f00,0),u32(0x8017f974,0x80014000),u32(0x8001403c,0x80014100),u32(0x80014108,0x80015000),u8(CURRENT+8,0x5a)],stubs=[stub(0x80015000,3)])
for value in [0,1]:case('control_toggle_'+str(value),CONTROL,[12,value,255],offset=2,stubs=[stub(0x8015c100 if value==0 else 0x8015c0b8)])
for kind in [1,2]:
 case('coordinate_setup_kind'+str(kind),CONTROL,[13,1,1,2,0,255],offset=5,result=255 if kind==2 else 17,stubs=[stub(0x8015c148,kind),(0x8015477c,[0x03e00008,0x00801021])],checks=[u32(0x80143f7c if kind==2 else CURRENT+0x34,0x18000),u32(0x80143f80 if kind==2 else CURRENT+0x38,0x20000)])
for opcode in [14,15]:
 for flags in [0,1,2,3]:
  special=bool(flags&2);script=[opcode,3,5,flags]+([7] if special else [])+[255]
  case(f'animation_{opcode:02x}_{flags}',CONTROL,script,offset=5 if special else 4,patches=[u32(0x80146250,0x80013000),u8(0x80013079,2),u8(0x801c87d8+3*11+2,0x24)],stubs=[stub(0x8014d6dc if special else 0x8014d6b8)],checks=[u8(REC,0x40),u8(CURRENT+7,8),u8(CURRENT,16 if flags&1 else 0),u8(CURRENT+0x2a,5)])
for val in [-1,1]:case('a0_callback_'+str(val),CONTROL,[0xa2,0,255],offset=0 if val<0 else 2,patches=[u32(0x801821c8,0x80015000)],stubs=[stub(0x80015000,val)])
case('b0_delegate',CONTROL,[0xb0,255],offset=1,stubs=[stub(0x801a96e4)])
for opcode,callee in [(240,0x8015c058),(241,0x8015c088)]:case(f'ext_{opcode:02x}_callback',EXTENDED,[opcode],offset=0,stubs=[stub(callee)])
for kind in [1,2]:case('ext_f2_kind'+str(kind),EXTENDED,[242,5,3],offset=2,result=5,stubs=[stub(0x8015c148,kind),stub(0x801abba8 if kind==1 else 0x801c5dfc)],checks=[u8(REC+7,3)])
case('ext_f3_signed_division',EXTENDED,[243,5,2,0,20],offset=4,result=5,patches=[u8(CURRENT+9,2),u16(CURRENT+0x3e,40)],stubs=[stub(0x8015c148,1),stub(0x801abba8)],checks=[u32(CURRENT+0x14,-5)])
case('ext_f3_zero_divisor_trap',EXTENDED,[243,5,2,0,20],patches=[u8(CURRENT+9,0),u16(CURRENT+0x3e,40)],stubs=[stub(0x8015c148,1),stub(0x801abba8)],trap=0x801a9f48)
case('ext_f7_motion_callback',EXTENDED,[247,1,2,3,4,5,6],offset=6,result=6,stubs=[stub(0x801abd68),stub(0x8015c148,1)],checks=[u8(REC+7,1)])
case('ext_f8_callback',EXTENDED,[248,1,2,3,4],offset=1,stubs=[stub(0x801ac768)])
for val in [0,1]:case('ext_f9_wait_'+str(val),EXTENDED,[249,1,2],offset=2 if val==0 else 65535,result=5 if val==0 else 255,patches=[u8(CURRENT+8,13)],stubs=[stub(0x801ac33c,val)])
for opcode,callee in [(251,0x8015507c),(252,0x80155218)]:
 for val in [0,1]:case(f'ext_{opcode:02x}_predicate_{val}',EXTENDED,[opcode],offset=0,stubs=[stub(callee,val)]+([stub(0x8015df18)] if val else []))
for val in [0,1]:case('ext_fd_wait_'+str(val),EXTENDED,[253],offset=65535 if val==0 else 0,stubs=[stub(0x8014daec,val)],checks=[u8(CURRENT+7,32 if val==0 else 0)])
case('ext_fe_phase_skip',EXTENDED,[254,2,9],offset=2,patches=[u8(0x80143bb0,3)])
for val in [8,9]:case('ext_fe_match_'+str(val),EXTENDED,[254,2,9],offset=2,stubs=[stub(0x8015ca9c,val)]+([stub(0x8015df18)] if val==9 else []))

case('ext_f3_global_signed_division',EXTENDED,[243,5,2,0,20],offset=4,result=5,patches=[u16(CURRENT+0x3e,40),u16(0x8014932e,16),u8(0x80143fc3,4)],stubs=[stub(0x8015c148,2),stub(0x801c5dfc)],checks=[u32(0x80143f5c,-40960),u8(REC,64)])
case('ext_f3_global_zero_scale_trap',EXTENDED,[243,5,2,0,20],patches=[u16(CURRENT+0x3e,40),u16(0x8014932e,0),u8(0x80143fc3,4)],stubs=[stub(0x8015c148,2),stub(0x801c5dfc)],trap=0x801a9fdc)
case('ext_f3_global_zero_product_trap',EXTENDED,[243,5,2,0,20],patches=[u16(CURRENT+0x3e,40),u16(0x8014932e,256),u8(0x80143fc3,4)],stubs=[stub(0x8015c148,2),stub(0x801c5dfc)],trap=0x801aa030)
for kind in [1,2]:case('ext_fa_kind'+str(kind),EXTENDED,[250,5,2,0x12,0x34],offset=4,result=5,patches=[u16(0x80149330,123)],stubs=[stub(0x8015c148,kind),stub(0x801abba8 if kind==1 else 0x801c5dfc)],checks=[u8(REC,128 if kind==1 else 64),u16(CURRENT+0x3e,0x1234),u32(CURRENT+0x14,0)]+([u16(0x80149330,0)] if kind==2 else []))
results=[]
for c in cases:
 memory=bytearray(0x200400);memory[0x195800:0x195800+len(GAME)]=GAME
 def ix(a):
  p=a&0x1fffffff
  assert p<0x200000 or 0x1f800000<=p<0x1f800400
  return p if p<0x200000 else 0x200000+p-0x1f800000
 def put(a,b):memory[ix(a):ix(a)+len(b)]=b
 put(0x1f800044,struct.pack('<I',CURRENT));put(SCRIPT,bytes(c['script']));put(REC+10,struct.pack('<H',c['cursor']))
 for a,b in c['patches']:put(a,b)
 for a,words in c['stubs']:put(a,struct.pack('<'+'I'*len(words),*words))
 regs=[0]+[0x11000000+i for i in range(1,32)];regs[4:7]=[REC,SCRIPT,17];regs[29]=0x80180000;regs[31]=0x80008000
 directory=O/'cases'/c['name'];directory.mkdir(exist_ok=True);input_file=directory/'input.bin';input_file.write_bytes(struct.pack('<32I',*regs)+memory+struct.pack('<I',len(c['stubs']))+b''.join(struct.pack('<II',address,len(words)*4) for address,words in c['stubs']))
 outputs={}
 for variant in ['oracle','native']:
  p=subprocess.run([str(E),variant,hex(c['entry']),str(input_file),str(directory/variant)],capture_output=True,text=True,timeout=5)
  (directory/f'{variant}.log').write_text(p.stdout+p.stderr,encoding='utf-8');assert p.returncode==0,(c['name'],variant,p.returncode,p.stderr)
  outputs[variant]=(json.loads((directory/f'{variant}.json').read_text()),(directory/f'{variant}.ram').read_bytes())
 a,am=outputs['oracle'];b,bm=outputs['native']
 diffs=[i for i,(x,y) in enumerate(zip(am,bm)) if x!=y];assert not diffs,(c['name'],'RAM',[(hex(i),am[i],bm[i]) for i in diffs[:10]])
 for key in ['gpr','hi','lo','trap_pc','trap_code','stub_calls','calls']:assert a[key]==b[key],(c['name'],key,a[key],b[key])
 assert b['trap_pc']==c['trap']
 if c['trap']:assert a['exception_code']==9 and a['exception_epc']==c['trap']+4, 'Known upstream oracle EPC advance recorded explicitly'
 if not c['trap']:
  assert b['gpr'][2]==c['result'],(c['name'],'return',b['gpr'][2],c['result'])
  if c['offset'] is not None:assert struct.unpack_from('<H',bm,ix(REC)+10)[0]==c['offset'],(c['name'],'offset')
  for address,expected in c['checks']:assert bm[ix(address):ix(address)+len(expected)]==expected,(c['name'],hex(address),'expected state')
 results.append({'name':c['name'],'entry':hex(c['entry']),'ram_and_scratch_identical':True,'all_gprs_hi_lo_identical':True,'expected_state_passed':True,'stubbed_callees':[hex(x[0]) for x in c['stubs']],'native_visited':b['visited'],'oracle_visited':a['visited'],'trap_pc':hex(b['trap_pc']),'oracle_exception_epc':hex(a['exception_epc']),'oracle_exception_code':a['exception_code'],'observed_stub_calls':[hex(x) for x in b['stub_calls']],'callback_arguments_identical':True,'calls':b['calls']})
 print('PASS',c['name'],flush=True)
(O/'validation.json').write_text(json.dumps({'status':'passed','cases':results,'limitations':['Standalone functional execution; timing, graphics, audio, interrupts and PGXP are excluded.','External callees are fixture MIPS test doubles; their actual game behavior is not validated.','Original source instructions and actual generated C share the framework but use separate execution paths; this is not an independent hardware oracle.']},indent=2)+'\n',encoding='utf-8')
print('PASS',len(results),'command scenarios')
