"""Differential execution of the generated AREA033 renderer and original MIPS.
External rendering services are explicit MIPS test doubles; live route tests
separately cover integration with the real services.
"""
from pathlib import Path
import itertools,json,re,struct,subprocess
R=Path(__file__).resolve().parents[1];G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII';O=R/'coverage/world-native-investigation';H=O/'harness';H.mkdir(exist_ok=True)
F=G/'psxrecomp/runtime';S=G/'generated-world-tiles-overlays'
h=(R/'coverage/scenario01-events-native/harness/harness.c').read_text()
h=h.replace('p>=0x801f7fc4&&p<0x801f8f34','p>=0x801f469c&&p<0x801f4cb0').replace('calls[128][6]','calls[1024][6]').replace('call_count>=128','call_count>=1024')
h+='\nint dirty_ram_resolve_bne(uint32_t p,uint32_t i,int taken){return taken;}\nint dirty_ram_resolve_immediate(uint32_t p,uint32_t i,int32_t*v){return 0;}\n'
(H/'harness.c').write_text(h)
decls=re.findall(r'void (ov_\w+_func_([0-9A-F]{8}))\(CPUState \*cpu\);',(S/'overlays_static.c').read_text())
assert len(decls)==44
header='\n'.join(f'void {name}(CPUState*);' for name,pc in decls)
header+='\nstatic int native_dispatch(CPUState*c){switch(c->pc){\n'+''.join(f'case 0x{pc}: {name}(c); return 1;\n' for name,pc in decls)+'default:return 0;}}\n'
(H/'functions.h').write_text(header)
cmake=f'''cmake_minimum_required(VERSION 3.20)
project(world_tiles_cases C)
add_executable(world_tiles_cases harness.c "{F.as_posix()}/src/psx_interpreter.c" "{S.as_posix()}/overlays_static_0000.c")
target_include_directories(world_tiles_cases PRIVATE "{F.as_posix()}/include")
target_compile_definitions(world_tiles_cases PRIVATE PSX_NO_DEBUG_TOOLS _CRT_SECURE_NO_WARNINGS)
'''
(H/'CMakeLists.txt').write_text(cmake)
if not (O/'case-build/world_tiles_cases.exe').exists():
 print('Harness prepared. Build case-build, then rerun this script.');raise SystemExit(0)
source=(O/'AREA033-section13-801F2C00.bin').read_bytes();recipe=json.loads((O/'recipe.json').read_text());results=[]
words=lambda *v:struct.pack('<'+'I'*len(v),*v)
def ix(a):return (a&0x1fffffff) if (a&0x1fffffff)<0x200000 else 0x200000+(a&0x3ff)
for initial,flag,size,present,mode,far in itertools.product((0,1),(0,4),(2,3,4),(0,1),(0,1,2),(0,1)):
 # Avoid duplicating rendering dimensions when the routine exits before drawing.
 if (not flag or far) and (size,present,mode)!=(2,0,0):continue
 name=f'i{initial}-f{flag}-s{size}-p{present}-m{mode}-far{far}'
 D=O/'cases'/name;D.mkdir(parents=True,exist_ok=True)
 memory=bytearray(0x200400);memory[0x1f2c00:0x1f2c00+len(source)]=source
 def put(a,data):memory[ix(a):ix(a)+len(data)]=data
 record=0x80100000;packet=0x80120000;tile=0x80110000
 put(0x1f800044,words(record));put(0x8014598c,words(packet));put(record+2,bytes([initial]));put(record+11,bytes([size]));put(record+0x34,words(0x00100000,0x00100000));put(0x8014832e,bytes([flag]));put(0x80143e6c,words(7));put(0x80104001,b'\x40')
 camera=100 if far else 16
 put(0x8014930a,struct.pack('<h',camera));put(0x8014930e,struct.pack('<h',camera))
 put(tile,bytes(range(64)))
 stubs=[]
 for address in sorted({int(c['target'],16) for c in recipe['calls']}):
  value=(tile if present else 0) if address==0x801559ac else mode if address==0x8017b2b4 else 0
  code=words(0x3c020000|(value>>16),0x34420000|(value&65535),0x03e00008,0)
  put(address,code);stubs.append((address,len(code)))
 regs=[0]*32;regs[29]=0x801ff000;regs[31]=0x80008000
 inp=D/'input.bin';inp.write_bytes(words(*regs)+memory+words(len(stubs))+b''.join(words(*s) for s in stubs))
 data={}
 for variant in ('native','oracle'):
  run=subprocess.run([str(O/'case-build/world_tiles_cases.exe'),variant,'801f469c',str(inp),str(D/variant)],capture_output=True,text=True,timeout=10)
  assert run.returncode==0,(name,variant,run.stderr)
  data[variant]=(json.loads((D/(variant+'.json')).read_text()),(D/(variant+'.ram')).read_bytes())
 a,am=data['native'];b,bm=data['oracle'];assert am==bm,(name,'memory')
 for key in ('gpr','hi','lo','trap_pc','trap_code','calls'):assert a[key]==b[key],(name,key)
 assert a['trap_pc']==0
 assert am[ix(record+2)]==1
 if not flag or far:assert not a['calls'],name
 elif size==4:assert len(a['calls'])==5,name
 elif present:
  assert am[ix(packet+4):ix(packet+7)]==b'\x28'*3
  assert struct.unpack_from('<H',am,ix(packet+0x16))[0]==(0x12b if mode in (1,2) else 0x5b)
 results.append(dict(name=name,calls=len(a['calls']),visited=b['visited']))
(O/'case-validation.json').write_text(json.dumps(dict(passed=len(results),scope='Exact RAM, scratchpad, GPR/HI/LO and external-call comparison against original MIPS; external rendering services are doubles.',cases=results),indent=2))
print('PASS:',len(results),'renderer differential cases')
