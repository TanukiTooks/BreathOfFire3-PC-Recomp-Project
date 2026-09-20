"""Tests event 1/2 transitions using real original flag/control helpers and declared other service doubles."""
from pathlib import Path
import hashlib,json,struct,subprocess
R=Path(__file__).resolve().parents[1];O=R/'coverage/scenario01-events-native';E=O/'case-build/scenario01_events_cases.exe'
SRC=(R/'coverage/party-motion-native/SCENA01-section00-801F6C00.bin').read_bytes();BOOT=(R/'input/SLUS_004.22').read_bytes();BASE=struct.unpack_from('<I',BOOT,0x18)[0]
assert hashlib.sha256(SRC).hexdigest()=='289b2b95706371c76f70e49226525ef995b33b57f4a2dd653eb5678801324b48'
assert hashlib.sha256(BOOT).hexdigest()=='0af39fb1ffcf25e4bdf2730173f397b5b5f6c44989114fe9b59b92ab7c0eb21a'
PROGRESS=0x80146864;EVENT=0x80146874;SUB=EVENT+1;CONTROL=0x80146258;FLAGS=0x80010000;SLOTS=0x80143fc8
SET=0x8015b580;CLEAN=0x8015c058;LOAD=0x8019fa28;CAMERA=0x801c601c;ACTOR=0x8015d404;SERVICE=0x8014ecac
cases=[]
def b(a,v):return a,bytes([v&255])
def h(a,v):return a,struct.pack('<H',v&65535)
def w(a,v):return a,struct.pack('<I',v&0xffffffff)
def words(*v):return struct.pack('<'+'I'*len(v),*v)
def ix(a):
 p=a&0x1fffffff;assert p<0x200000 or 0x1f800000<=p<0x1f800400
 return p if p<0x200000 else 0x200000+p-0x1f800000

def specification(event,sub,progress,control,busy,cam,slot,service_slot):
 changes=[];calls=[]
 if event==1:
  if sub==0 and progress==1:
   changes=[b(PROGRESS+1,1),b(PROGRESS+2,1),b(SUB,1)];calls=[(LOAD,9,0x470000,0x1d0000,3)]
  elif sub==1:
   changes=[b(0x8014832e,31),b(SUB,2)];calls=[(CAMERA,0)]
  elif sub==2 and progress==30:
   changes=[b(FLAGS,0xa5),b(PROGRESS,0),b(PROGRESS+1,0),b(PROGRESS+2,0),b(EVENT,0),b(SUB,0)];calls=[(SET,FLAGS,0),(LOAD,10,0x2b0000,0x200000,3)]
 else:
  gate={0:2,1:4,2:10,3:1,9:3,10:1,11:1}
  if sub in gate and progress!=gate[sub]:return changes,calls
  if sub==0:changes=[b(PROGRESS+1,1),b(SUB,1)];calls=[(LOAD,10,0x520000,0x230000,3)]
  elif sub==1:
   changes=[b(PROGRESS+1,2),b(SUB,2),h(CONTROL,control|0x80)];calls=[(ACTOR,0,0),(0x80161c20,14,100,8),(LOAD,10,0x4f0000,0x50000,3)]
  elif sub==2:
   changes=[b(PROGRESS+1,3),b(PROGRESS+2,7),b(SUB,3)];calls=[(ACTOR,0,1),(LOAD,10,0x600000,0x120000,3)]
  elif sub==3:changes=[b(SUB,4)];calls=[(SERVICE,15),(0x8015df18,0x201)]
  elif sub==4 and busy==0:
   selected=slot if service_slot is None else service_slot
   changes=[b(SLOTS+selected*0x74,0),b(SUB,8)];calls=[(SERVICE,16)]
  elif sub==8 and busy==0:changes=[b(PROGRESS,2),b(SUB,9)]
  elif sub==9:changes=[b(PROGRESS+1,4),b(PROGRESS+2,0),b(SUB,10)];calls=[(LOAD,10,0x5f0000,0x310000,3)]
  elif sub==10:changes=[b(PROGRESS+1,5),b(SUB,11),h(CONTROL,control^0x80)];calls=[(LOAD,10,0x4f0000,0x50000,0x85)]
  elif sub==11 and cam==0:
   changes=[b(FLAGS,0xa6),b(0x80146871,0xb5),w(PROGRESS,0),b(SUB,0),b(EVENT,0),h(CONTROL,(control&0xfeff)|0x60)];calls=[(SET,FLAGS,1),(CLEAN,)]
 return changes,calls

def add(name,event,sub,progress=0,control=0xa102,busy=0,cam=0,slot=3,service_slot=None,nested=False):
 cases.append(dict(name=name,event=event,sub=sub,progress=progress,control=control,busy=busy,cam=cam,slot=slot,service_slot=service_slot,nested=nested))
for sub in [0,1,2,3,127,128,255]:
 for progress in ([0,1,2,29,30,31,255] if sub in [0,2] else [0,255]):add(f'event1_sub{sub}_progress{progress}',1,sub,progress)
for sub in list(range(13))+[127,128,255]:
 gate={0:2,1:4,2:10,3:1,9:3,10:1,11:1}.get(sub)
 for progress in ([0,gate,255] if gate is not None else [0]):add(f'event2_sub{sub}_progress{progress}',2,sub,progress)
for sub in [4,8]:
 for busy in [1,0x100,0xffff]:add(f'event2_sub{sub}_busy{busy}',2,sub,busy=busy)
for cam in [1,128,255]:add(f'event2_finish_camera{cam}',2,11,1,cam=cam)
for control in [0,0x80,0x100,0xffff]:
 for sub,progress in [(1,4),(10,1),(11,1)]:add(f'event2_sub{sub}_control{control}',2,sub,progress,control=control)
for slot in [0,19]:add(f'event2_release_slot{slot}',2,4,slot=slot)
add('event2_service_changes_scratch_slot',2,4,slot=3,service_slot=19)
for event,sub,progress in [(1,0,1),(1,1,0),(1,2,30),(2,0,2),(2,4,0),(2,11,1)]:add(f'nested_event{event}_sub{sub}',event,sub,progress,nested=True)

def initial(case):
 memory=bytearray(0x200400);memory[0x1f6c00:0x1f6c00+len(SRC)]=SRC
 patches=[w(PROGRESS,0x44332211),b(PROGRESS,case['progress']),b(EVENT,case['event']),b(SUB,case['sub']),b(0x80146872,2),b(0x80146871,0xf5),w(0x8014686c,FLAGS),b(FLAGS,0xa4),h(CONTROL,case['control']),h(0x80143c40,case['busy']),b(0x80149332,case['cam']),b(0x1f800000,case['slot']),b(0x8014832e,0x77)]
 patches += [b(SLOTS+i*0x74,0x80+i) for i in range(20)]
 for a,d in patches:memory[ix(a):ix(a)+len(d)]=d
 return memory

results=[];visited=set()
def run(name,case,memory):
 memory=bytearray(memory);ranges={}
 # Real original helpers: 40-byte packed-bit setter, 48-byte control-bit cleanup.
 for address,size in [(SET,40),(CLEAN,48)]:
  code=BOOT[0x800+address-BASE:0x800+address-BASE+size]
  assert struct.unpack_from('<I',code,len(code)-8)[0]==0x03e00008
  ranges[address]=code
 for address in [LOAD,CAMERA,ACTOR,SERVICE,0x80161c20,0x8015df18]:ranges[address]=words(0x03e00008,0x24021234)
 if case['service_slot'] is not None:ranges[SERVICE]=words(0x3c081f80,0x24090000|case['service_slot'],0xa1090000,0x03e00008,0x24021234)
 for address,data in ranges.items():memory[ix(address):ix(address)+len(data)]=data
 before=memory[:];sub=memory[ix(SUB)];progress=memory[ix(PROGRESS)];control=struct.unpack_from('<H',memory,ix(CONTROL))[0]
 changes,expected_calls=specification(case['event'],sub,progress,control,struct.unpack_from('<H',memory,ix(0x80143c40))[0],memory[ix(0x80149332)],memory[ix(0x1f800000)],case['service_slot'])
 regs=[0]+[0x11000000+i for i in range(1,32)];regs[29]=0x80180000;regs[31]=0x80008000
 D=O/'cases'/name;D.mkdir(parents=True,exist_ok=True);inp=D/'input.bin'
 inp.write_bytes(struct.pack('<32I',*regs)+memory+struct.pack('<I',len(ranges))+b''.join(struct.pack('<II',a,len(d)) for a,d in ranges.items()))
 entry=0x801f7fc4 if case['nested'] else (0x801f8ae4 if case['event']==1 else 0x801f8c0c)
 output={}
 for variant in ['oracle','native']:
  p=subprocess.run([str(E),variant,hex(entry),str(inp),str(D/variant)],capture_output=True,text=True,timeout=5)
  (D/(variant+'.log')).write_text(p.stdout+p.stderr,encoding='utf-8');assert p.returncode==0,(name,variant,p.stderr)
  output[variant]=(json.loads((D/(variant+'.json')).read_text()),(D/(variant+'.ram')).read_bytes())
 a,am=output['oracle'];z,zm=output['native'];assert am==zm,(name,'RAM',[(hex(i),x,y) for i,(x,y) in enumerate(zip(am,zm)) if x!=y][:10])
 for key in ['gpr','hi','lo','trap_pc','trap_code','calls','stub_calls']:assert a[key]==z[key],(name,key,a[key],z[key])
 assert z['trap_pc']==0
 expected=before[:]
 for address,data in changes:expected[ix(address):ix(address)+len(data)]=data
 for address,size in [(PROGRESS,4),(EVENT,2),(CONTROL,2),(FLAGS,8),(0x80146871,2),(0x8014832e,1),(SLOTS,20*0x74)]:assert zm[ix(address):ix(address)+size]==expected[ix(address):ix(address)+size],(name,hex(address),zm[ix(address):ix(address)+size].hex(),expected[ix(address):ix(address)+size].hex())
 assert len(z['calls'])==len(expected_calls),(name,z['calls'],expected_calls)
 for got,want in zip(z['calls'],expected_calls):assert tuple(got[:len(want)])==want,(name,got,want)
 visited.update(a['visited']);results.append({'name':name,'entry':hex(entry),'event':case['event'],'substate':sub,'nested_dispatch':case['nested'],'full_memory_registers_expected_outputs_and_calls_pass':True,'real_helpers_called':[hex(c[0]) for c in z['calls'] if c[0] in [SET,CLEAN]],'calls':z['calls'],'oracle_visited':a['visited'],'native_visited':z['visited']})
 return bytearray(zm)
for case in cases:run(case['name'],case,initial(case))
# Consecutive invocations retain the exact prior output RAM. Only explicit progress gates are advanced.
chains=[]
for event,progressions in [(1,[1,None,30]),(2,[2,4,10,1,None,None,3,1,1])]:
 case=dict(name='chain',event=event,sub=0,progress=0,control=0xa102,busy=0,cam=0,slot=3,service_slot=None,nested=True);memory=initial(case);states=[]
 for step,progress in enumerate(progressions):
  if progress is not None:memory[ix(PROGRESS)]=progress
  memory=run(f'chain_event{event}_step{step}',case,memory);states.append(memory[ix(SUB)])
 assert memory[ix(EVENT)]==0 and memory[ix(SUB)]==0
 assert states==([1,2,0] if event==1 else [1,2,3,4,8,9,10,11,0])
 chains.append({'event':event,'substates_after_steps':states,'complete':True,'external_script_progress_is_fixture_driven':True})
coverage=[]
for lo,hi in [(0x801f8ae4,0x801f8c0c),(0x801f8c0c,0x801f8f34)]:
 pcs=set(range(lo,hi,4));coverage.append({'entry':hex(lo),'instructions':len(pcs),'observed_original_instruction_entries':len(pcs&visited),'unobserved':[hex(p) for p in sorted(pcs-visited)]})
result={'passed':len(results),'isolated_cases':len(cases),'chained_steps':12,'chains':chains,'instruction_coverage':coverage,'cases':results,'source_sha256':hashlib.sha256(SRC).hexdigest(),'boot_sha256':hashlib.sha256(BOOT).hexdigest(),'harness_sha256':hashlib.sha256(E.read_bytes()).hexdigest(),'scope':'Generated C versus independent original MIPS with exact full RAM/scratch/register/call comparison. Packed story-bit setter 0x8015B580 and event-control cleanup 0x8015C058 are original MIPS, interpreted on both sides. Other external services are explicit doubles. Chained event progress is fixture-driven; no claim of a complete natural story sequence or timing/device/audio equivalence.'}
(O/'case-validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('PASS',len(results),'checks;',len(cases),'isolated plus 12 chained steps');print(json.dumps(coverage,indent=2))
