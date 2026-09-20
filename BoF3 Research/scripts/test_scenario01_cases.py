"""SCENA01 generated C versus original MIPS, with explicit external-service test doubles."""
from pathlib import Path
import json,struct,subprocess,hashlib
R=Path(__file__).resolve().parents[1];O=R/'coverage/scenario01-native';E=O/'case-build/scenario01_cases.exe'
SRC=(R/'coverage/party-motion-native/SCENA01-section00-801F6C00.bin').read_bytes()
assert hashlib.sha256(SRC).hexdigest()=='289b2b95706371c76f70e49226525ef995b33b57f4a2dd653eb5678801324b48'
STATE=0x80146872;EVENT=0x80146874;PARAM=EVENT+1;SUB=0x80146866;FLAGS=0x80010000;CONTROL=0x80146258;VISIBLE=0x8014832e;CAM=0x8014932c
GET=0x8015b5d4;SET=0x8015b580;START=0x80161bbc;POLL=0x80162d00;YIELD=0x8014b87c;ALLOC=0x8019601c;SCREEN=0x801c1df0;RESET=0x8015c088;ACTOR=0x8015d404
cases=[]
def b(a,v):return a,bytes([v&255])
def h(a,v):return a,struct.pack('<H',v&65535)
def w(a,v):return a,struct.pack('<I',v&0xffffffff)
def words(*values):return struct.pack('<'+'I'*len(values),*values)
def add(name,map=0x5a,sub=0,flags=(),checks=(),calls=(),entry=0x801f8050,alloc=3,polls=1,extra=()):
 cases.append(dict(name=name,map=map,sub=sub,flags=list(flags),checks=list(checks),calls=list(calls),entry=entry,alloc=alloc,polls=polls,extra=list(extra)))
def event(n,p=0):return [b(EVENT,n),b(PARAM,p)]
def clear4():return [w(0x80146864,0)]
def flags_call(n):return (GET,FLAGS,n)
# Each case states selected events, preserved defaults and service-call ordering independently of C codegen.
for sub in [0,1,2,255]:
 for setflag in [False,True]:
  checks=[];calls=[]
  if sub in [0,1]:calls=[flags_call(0x3a)]
  if not setflag and sub==0:checks=clear4()+event(13)+[b(VISIBLE,0)];calls += [(START,0),(POLL,)]
  if not setflag and sub==1:checks=[b(0x80149333,2),h(CAM,0xa00+0xf900)]
  add(f'map00_sub{sub}_flag{setflag}',0,sub,[0x3a] if setflag else [],checks,calls)
for sub in list(range(7))+[255]:
 for flag in [False,True]:
  checks=[];calls=[]
  if sub==0:
   calls=[flags_call(0x15)]
   if not flag:checks=[b(0x80146864,0),b(VISIBLE,0),h(CONTROL,0xa007)]+event(12)
  elif sub==1:calls=[(START,8),(POLL,)]
  elif sub==2:checks=[b(VISIBLE,31),h(CONTROL,0xa002^7)]
  elif sub==4:checks=event(16,3)+[b(0x80146864,0)]
  elif sub==5:checks=[b(VISIBLE,31)]
  add(f'map05_sub{sub}_flag{flag}',5,sub,[0x15] if flag else [],checks,calls)
for flag in [False,True]:
 add(f'map07_flag{flag}',7,flags=[0x19] if flag else [],checks=[] if flag else [b(0x80146864,0),b(VISIBLE,0)]+event(11),calls=[flags_call(0x19)]+([] if flag else [(RESET,)]))
for sub in list(range(6))+[255]:
 for flag in [False,True]:
  checks=[];calls=[]
  if sub in [2,3]:
   calls=[flags_call(6 if sub==2 else 5)]
   if not flag:
    checks=event(6,0 if sub==2 else 10)
    if sub==2:checks+=[h(CONTROL,0xa006)]
    else:calls+=[(ACTOR,0,0)]
  elif sub==4:checks=clear4()+[h(0x80146876,0),b(VISIBLE,31)];calls=[(ACTOR,0,0)]
  add(f'map08_sub{sub}_flag{flag}',8,sub,[5,6] if flag else [],checks,calls)
for sub in [0,1]:
 for flag in [False,True]:
  take=sub==0 and not flag
  add(f'map09_sub{sub}_flag{flag}',9,sub,[0] if flag else [],event(1)+[b(VISIBLE,0)] if take else [],[flags_call(0)]+([(RESET,)] if take else []))
for sub in list(range(10))+[255]:
 for flag in [False,True]:
  checks=[];calls=[]
  if sub in [0,7]:
   calls=[flags_call(1)]
   if not flag:
    checks=[b(EVENT,2)]
    if sub==0:checks+=[b(VISIBLE,31)]
    else:checks += [b(0x1f800000,3),b(0x80143fc8+3*0x74,1),b(0x80143fcd+3*0x74,0x12)];calls += [(ALLOC,)]
  elif sub in [3,4]:checks=[b(EVENT,7),h(CONTROL,0xa002)]
  elif sub==8:checks=[b(VISIBLE,31)]
  add(f'map0a_sub{sub}_flag{flag}',10,sub,[1] if flag else [],checks,calls)
add('map0a_allocator_full',10,7,checks=[b(EVENT,2),b(0x1f800000,255)],calls=[flags_call(1),(ALLOC,)],alloc=255)
for sub in [0,1]:
 for mode in [0,1]:
  for flags in [[],[0x3c],[0x3c,0x3e]]:
   take=0x3c in flags and 0x3e not in flags and mode==1
   checks=[b(VISIBLE,31)] if sub==1 else []
   calls=[flags_call(0x3c)]+([flags_call(0x3e)] if 0x3c in flags else [])
   if take:checks=[b(VISIBLE,0),b(0x80146864,0),b(0x80146865,0),b(SUB,0)]+event(14);calls += [(RESET,)]
   add(f'map0d_sub{sub}_mode{mode}_flags{len(flags)}',13,sub,flags,checks,calls,extra=[b(0x80143f03,mode)])
for flags in [[],[0x1b],[0x1b,0x1c]]:
 calls=[flags_call(0x1b)];checks=[]
 if not flags:checks=clear4()+event(0)
 else:
  calls+=[flags_call(0x1c)]
  if 0x1c not in flags:checks=clear4()+[b(FLAGS+0x1c,1),b(0x80149333,2),h(CAM,0xf900+0xb80)];calls += [(SET,FLAGS,0x1c),(SCREEN,1)]
 add('map0e_flags'+str(len(flags)),14,0,flags,checks,calls)
add('map0e_nonzero_substate',14,1)
chain=[0xb,0xc,0xd,0xf,0x10]
for count in range(6):
 calls=[flags_call(f) for f in chain[:min(count+1,5)]];checks=[]
 if count<5:
  checks=event(9,[0,3,8,9,17][count])
  if count in [0,2]:
   flag=chain[count];checks+=[b(FLAGS+flag,1)]
   if count==2:calls += [(RESET,)]
   calls += [(SET,FLAGS,flag)]
 add('map16_flag_chain'+str(count),22,flags=chain[:count],checks=checks,calls=calls)
for sub in list(range(9))+[255]:
 for flag in [False,True]:
  checks=[];calls=[]
  if sub in [0,1,2]:
   calls=[flags_call(9 if sub==0 else 10)]
   if not flag:
    checks=event(8,[0,19,55][sub])
    if sub==0:checks=clear4()+checks
    elif sub==1:calls += [(ACTOR,0,0)]
  elif sub==3:checks=[b(0x1f800000,3),b(0x80143fc8+3*0x74,1),b(0x80143fcd+3*0x74,0x11)];calls=[(ALLOC,),(SCREEN,2)]
  elif sub==4:
   calls=[flags_call(0x39)]
   if not flag:checks=[b(0x80146871,0xa4),b(VISIBLE,0),b(FLAGS+0x39,1),b(FLAGS+0x3f,1)];calls += [(0x80157f98,),(0x8015507c,0x49,0xc),(SET,FLAGS,0x39),(SET,FLAGS,0x3f)]
  elif sub==5:checks=[b(0x80146864,0)]
  elif sub==7:checks=event(8,55)
  add(f'map17_sub{sub}_flag{flag}',23,sub,[9,10,0x39] if flag else [],checks,calls)
add('map17_allocator_full',23,3,checks=[b(0x1f800000,255)],calls=[(ALLOC,)],alloc=255)
for map in [1,0x5a,0x11,0x21,0x10,0xffff]:
 checks=clear4()+event(0) if map in [0x11,0x21,0x10] else []
 if map in [0x21,0x10]:checks += [h(0x80146876,0)]
 add(f'map{map:04x}_default',map,9,checks=checks)
for map,sub in [(0,0),(5,1)]:
 calls=([flags_call(0x3a)] if map==0 else [])+[(START,0 if map==0 else 8),(POLL,),(YIELD,1),(POLL,),(YIELD,1),(POLL,)]
 checks=clear4()+event(13)+[b(VISIBLE,0)] if map==0 else []
 add(f'map{map}_wait_twice',map,sub,checks=checks,calls=calls,polls=3)
# Real nested dispatch nodes. External services alone are doubled.
init_checks=[b(0x80144e90,0),w(0x80146864,0),b(STATE,1)]
init_calls=[(SCREEN,0),(0x8019fa28,9,0x570000,0x40000,7)]
add('initializer',entry=0x801f8000,checks=init_checks,calls=init_calls)
add('idle_leaf',entry=0x801f8adc)
for state in [0,1,2]:
 add('outer_real_state'+str(state),entry=0x801f7fc4,extra=[b(STATE,state),b(EVENT,0)],checks=init_checks if state==0 else [b(STATE,2),b(EVENT,0)],calls=init_calls if state==0 else [])
add('event_real_idle',entry=0x801f8aa0,extra=[b(EVENT,0)])
# Signed-index and live-pointer-table tests are synthetic dispatch inputs, not supported game states.
for entry,field,table in [(0x801f7fc4,STATE,0x801fe29c),(0x801f8aa0,EVENT,0x801fe2a8)]:
 for index in [3,16,127,128,255]:
  signed=index if index<128 else index-256
  add(f'dispatch_{entry:08x}_signed{signed}',entry=entry,extra=[b(field,index),w(table+signed*4,0x8000a000)],calls=[(0x8000a000,)])
results=[];oracle_visited=set()
for case in cases:
 memory=bytearray(0x200400);memory[0x1f6c00:0x1f6c00+len(SRC)]=SRC
 def ix(a):
  p=a&0x1fffffff
  assert p<0x200000 or 0x1f800000<=p<0x1f800400
  return p if p<0x200000 else 0x200000+p-0x1f800000
 def put(a,data):memory[ix(a):ix(a)+len(data)]=data
 defaults=[h(0x80143f00,case['map']),b(0x80143f03,1),w(0x80146864,0x44332211),b(SUB,case['sub']),w(0x8014686c,FLAGS),b(0x80146871,0xa5),b(STATE,1),b(EVENT,0x55),b(PARAM,0x66),h(0x80146876,0x8877),h(CONTROL,0xa002),b(VISIBLE,0x77),h(CAM,0xf900),b(0x80149333,0x44),b(0x80144e90,0xaa),w(0x80009000,case['polls'])]
 for a,d in defaults+[b(FLAGS+f,1) for f in case['flags']]+case['extra']:put(a,d)
 # Test-double implementation is original MIPS executed identically on both sides.
 # Flags use one byte per fixture flag; real bit-packed story storage is out of scope.
 stubs={GET:words(0x00851021,0x90420000,0,0x03e00008,0),SET:words(0x00851821,0x24020001,0xa0620000,0x03e00008,0),ALLOC:words(0x03e00008,0x24020000|case['alloc']),POLL:words(0x3c088001,0x8d089000,0,0x2508ffff,0x3c098001,0xad289000,0x2d020001,0x03e00008,0)}
 for address in [START,YIELD,SCREEN,RESET,ACTOR,0x8019fa28,0x80157f98,0x8015507c,0x8000a000]:stubs[address]=words(0x03e00008,0x24021234)
 for address,data in stubs.items():put(address,data)
 initial=memory[:];regs=[0]+[0x11000000+i for i in range(1,32)];regs[29]=0x80180000;regs[31]=0x80008000
 D=O/'cases'/case['name'];D.mkdir(parents=True,exist_ok=True);inp=D/'input.bin'
 inp.write_bytes(struct.pack('<32I',*regs)+memory+struct.pack('<I',len(stubs))+b''.join(struct.pack('<II',a,len(d)) for a,d in stubs.items()))
 out={}
 for variant in ['oracle','native']:
  proc=subprocess.run([str(E),variant,hex(case['entry']),str(inp),str(D/variant)],capture_output=True,text=True,timeout=5)
  (D/(variant+'.log')).write_text(proc.stdout+proc.stderr,encoding='utf-8');assert proc.returncode==0,(case['name'],variant,proc.stderr)
  out[variant]=(json.loads((D/(variant+'.json')).read_text()),(D/(variant+'.ram')).read_bytes())
 a,am=out['oracle'];z,zm=out['native'];assert am==zm,(case['name'],'RAM differences',[(hex(i),x,y) for i,(x,y) in enumerate(zip(am,zm)) if x!=y][:12])
 for key in ['gpr','hi','lo','trap_pc','trap_code','calls','stub_calls']:assert a[key]==z[key],(case['name'],key,a[key],z[key])
 assert z['trap_pc']==0
 checks=case['checks'][:]
 if case['entry']==0x801f8050:checks += [b(STATE,2)]
 # Check every selected/preserved event/control byte, not only modified values.
 expected=initial[:]
 for addr,data in checks:expected[ix(addr):ix(addr)+len(data)]=data
 for addr,n in [(0x80146864,4),(STATE,1),(EVENT,4),(CONTROL,2),(VISIBLE,1),(CAM,2),(0x80149333,1),(0x80146871,1),(0x80144e90,1),(FLAGS,64)]:
  assert zm[ix(addr):ix(addr)+n]==expected[ix(addr):ix(addr)+n],(case['name'],hex(addr),zm[ix(addr):ix(addr)+n].hex(),expected[ix(addr):ix(addr)+n].hex())
 for addr,data in checks:assert zm[ix(addr):ix(addr)+len(data)]==data,(case['name'],hex(addr))
 assert len(z['calls'])==len(case['calls']),(case['name'],'calls',z['calls'],case['calls'])
 for got,expected_call in zip(z['calls'],case['calls']):assert tuple(got[:len(expected_call)])==expected_call,(case['name'],'call',got,expected_call)
 oracle_visited.update(a['visited']);results.append({'name':case['name'],'entry':hex(case['entry']),'full_memory_and_register_match':True,'expected_outputs_and_call_order_pass':True,'calls':z['calls'],'native_visited':z['visited'],'oracle_visited':a['visited']})
recipes=json.loads((O/'recipes.json').read_text());coverage=[]
for r in recipes['routines']:
 lo=int(r['entry'],16);hi=int(r['end_exclusive'],16);allpcs=set(range(lo,hi,4));seen=allpcs&oracle_visited
 coverage.append({'entry':r['entry'],'instructions':len(allpcs),'visited_original_instructions':len(seen),'unvisited':[hex(p) for p in sorted(allpcs-seen)]})
result={'passed':len(results),'cases':results,'instruction_coverage':coverage,'exe_sha256':hashlib.sha256(E.read_bytes()).hexdigest(),'scope':'Actual generated C versus independently executed original MIPS; complete 2 MiB RAM, 1 KiB scratch, GPR/HI/LO and external call order/arguments. External services are explicitly declared MIPS test doubles, including byte-based flag fixtures and resource polls. Nested dispatch nodes use real source. Timing/devices/IRQs/render/audio and full story-event effects excluded.'}
(O/'case-validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('PASS',len(results),'cases');print(json.dumps(coverage,indent=2))
