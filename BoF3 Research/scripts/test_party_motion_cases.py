from pathlib import Path
import json,struct,subprocess,hashlib
R=Path(__file__).resolve().parents[1];O=R/'coverage/party-motion-native';E=O/'case-build/party_motion_cases.exe';GAME=(R/'coverage/ghidra-input/GAME-section-00-80195800.bin').read_bytes()
assert hashlib.sha256(GAME).hexdigest()=='1663ff2e78134fe15f3cae6fb4074acf14b68b79cfa02be0c7651eaf6a1728ff'
REC=0x80147a58;CUR=0x80148000;ACT=0x80146888;cases=[]
def b(a,v):return a,bytes([v&255])
def h(a,v):return a,struct.pack('<H',v&65535)
def w(a,v):return a,struct.pack('<I',v&0xffffffff)
def add(name,entry,patches,checks,match=3,real=False):cases.append(dict(name=name,entry=entry,patches=patches,checks=checks,match=match,real=real))
# Exercise bit movement individually, including discarded bits, plus mixed masks.
for mask in [0,65535,0xa55a]+[1<<i for i in range(16)]:
 for flag in [False,True]:
  expected=mask if not flag else (mask&0x9ff)|((mask&0x3000)<<2)|((mask&0xc000)>>2)
  add(f'control_mask_{mask:04x}_flag{int(flag)}',0x801bdbc4,[b(0x80143f02,0),b(0x80145fcc,2),h(0x80144974+2*0xa4,0x20 if flag else 0),h(0x80145aa4,mask)],[h(0x8014625c,expected)])
for name,mode,count,flagged,expected in [('leader_only_ignores_follower',0,3,4,0xffff),('party_uses_follower',1,3,4,0xf9ff),('party_uses_last',1,3,1,0xf9ff),('party_none_flagged',1,3,7,0xffff),('party_zero_count',1,0,2,0xffff)]:
 patches=[b(0x80143f02,mode),b(0x80146254,count),h(0x80145aa4,0xffff),h(0x80144974+flagged*0xa4,0x20)]+[b(0x80145fcc+i*0x140,index) for i,index in enumerate([2,4,1])]
 add(name,0x801bdbc4,patches,[h(0x8014625c,expected)])
# All local branch outcomes, flag preservation and byte truncation.
for state in [0,1]:
 for sentinel in [0,255]:
  for equal in [False,True]:
   value=3|(8 if state else 0);match=value if equal else value+1
   final=0xa5 if sentinel!=255 and equal else 0xad
   add(f'flag_state{state}_sentinel{sentinel}_equal{int(equal)}',0x801a2ae4,[b(CUR+6,1),b(CUR+7,0),b(CUR+8,0x83),b(CUR+9,state),b(0x1f800003,sentinel),b(REC+0x74,0xa5)],[b(CUR+8,(0x83|8) if state else 3),b(REC+0x74,final if not state else 0xad),b(0x1f800003,0)],match=match)
# High bits are retained by the state-nonzero OR path; matching is against that full byte.
add('flag_full_byte_match',0x801a2ae4,[b(CUR+6,1),b(CUR+8,0x83),b(CUR+9,1),b(REC+0x74,0xa5)],[b(CUR+8,0x8b),b(REC+0x74,0xa5)],match=0x12348b)
add('flag_existing_descriptor_bit',0x801a2ae4,[b(CUR+6,1),b(CUR+7,8),b(CUR+8,0xe3),b(REC+0x74,0xad)],[b(CUR+8,0xe3),b(REC+0x74,0xa5)])
add('type10_inactive',0x801a2ae4,[b(CUR+6,10),b(CUR+9,0),b(REC+0x74,0xad)],[b(REC+0x74,0xad)])
add('type10_actor_flag_clear',0x801a2ae4,[b(CUR+6,10),b(CUR+9,1),b(ACT+0x74,0),b(REC+0x74,0xad)],[b(REC+0x74,0xad)])
for direction in [0,3,5]:
 angle=struct.unpack_from('<H',GAME,0x801c8424-0x80195800+2*direction)[0]
 add('type10_real_callee_direction'+str(direction),0x801a2ae4,[b(CUR+6,10),b(CUR+9,1),b(CUR+8,0xf8|direction),b(ACT+0x74,8),b(REC+0x74,0xad),w(CUR+0x6c,0xdeadbeef)],[b(REC+0x74,0xa5),w(CUR+0x6c,angle)],real=True)
results=[]
for case in cases:
 memory=bytearray(0x200400);memory[0x195800:0x195800+len(GAME)]=GAME
 def ix(a):
  p=a&0x1fffffff
  assert p<0x200000 or 0x1f800000<=p<0x1f800400
  return p if p<0x200000 else 0x200000+p-0x1f800000
 def put(a,data):memory[ix(a):ix(a)+len(data)]=data
 for a,data in [w(0x1f800044,CUR),w(0x80146884,ACT)]+case['patches']:put(a,data)
 regs=[0]+[0x11000000+i for i in range(1,32)];regs[4]=REC;regs[5]=case['match'];regs[29]=0x80180000;regs[31]=0x80008000
 # Actual original GAME callee is retained, not replaced by a test double.
 ranges=[(0x801a3080,0x390)] if case['real'] else []
 D=O/'cases'/case['name'];D.mkdir(parents=True,exist_ok=True);inp=D/'input.bin';inp.write_bytes(struct.pack('<32I',*regs)+memory+struct.pack('<I',len(ranges))+b''.join(struct.pack('<II',*r) for r in ranges))
 out={}
 for variant in ['oracle','native']:
  proc=subprocess.run([str(E),variant,hex(case['entry']),str(inp),str(D/variant)],capture_output=True,text=True,timeout=5);(D/(variant+'.log')).write_text(proc.stdout+proc.stderr,encoding='utf-8');assert proc.returncode==0,(case['name'],variant,proc.stderr)
  out[variant]=(json.loads((D/(variant+'.json')).read_text()),(D/(variant+'.ram')).read_bytes())
 a,am=out['oracle'];z,zm=out['native'];assert am==zm,(case['name'],'RAM differences',[(hex(i),x,y) for i,(x,y) in enumerate(zip(am,zm)) if x!=y][:12])
 for key in ['gpr','hi','lo','trap_pc','trap_code','calls','stub_calls']:assert a[key]==z[key],(case['name'],key,a[key],z[key])
 assert z['trap_pc']==0
 for addr,data in case['checks']:assert zm[ix(addr):ix(addr)+len(data)]==data,(case['name'],hex(addr),zm[ix(addr):ix(addr)+len(data)].hex(),data.hex())
 assert bool(z['calls'])==case['real']
 results.append({'name':case['name'],'entry':hex(case['entry']),'full_memory_and_register_match':True,'expected_outputs_pass':True,'real_callee':case['real'],'calls':z['calls'],'native_visited':z['visited']})
result={'passed':len(results),'real_callee_cases':sum(c['real'] for c in cases),'cases':results,'exe_sha256':hashlib.sha256(E.read_bytes()).hexdigest(),'scope':'Actual generated C versus independent original MIPS; complete RAM/scratch/GPR/HI/LO comparisons. Three type-10 cases execute original 0x801A3080 in the interpreter on both sides with zero-velocity inputs, not a stub. Timing, rendering, IRQs and other callee paths excluded.'}
(O/'case-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(results),'cases, including',result['real_callee_cases'],'real-callee cases')
