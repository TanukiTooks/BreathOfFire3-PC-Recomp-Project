import argparse,time,json,struct,hashlib
from pathlib import Path
from record_runtime_coverage import request
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=4387);p.add_argument('--out',type=Path,required=True);p.add_argument('--load-save',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
def call(cmd,**kw):
 r=request(a.port,cmd,**kw)
 if not r.get('ok',True):raise RuntimeError((cmd,r))
 return r
def frame():return call('get_registers')['frame']
def wait_frames(n):
 goal=frame()+n;deadline=time.monotonic()+40
 while frame()<goal:
  if time.monotonic()>deadline:raise RuntimeError('Frame timeout')
  time.sleep(.06)
def ram(addr,n):return bytes.fromhex(call('read_ram',addr=hex(addr),len=n)['hex'])
def state():return {'frame':frame(),'slot':int.from_bytes(ram(0x8018e260,4),'little'),'outer_phase':int.from_bytes(ram(0x80143b92,2),'little'),'menu_phase':ram(0x801ed860,1)[0],'mask':ram(0x801ed870,1)[0]}
def snap(label):
 s=state();s['gameplay_phase']=int.from_bytes(ram(0x80143b90,2),'little');s['dirty']=call('dirty_ram_stats');s['overlays']=call('overlay_loader_status');s['phase']=call('phase_profile',window=1);call('screenshot_file',path=(a.out/(label+'.png')).resolve().as_posix());(a.out/(label+'.json')).write_text(json.dumps(s,indent=2));print(label,{k:v for k,v in s.items() if k not in ('dirty','overlays','phase')},flush=True);return s
def configured_button(address):
 value=int.from_bytes(ram(address,2),'little');assert value
 return 0xffff ^ (((value & 255)<<8)|(value>>8))
def press(mask,after=50):call('press',buttons=mask,frames=5);wait_frames(after)
def wait_menu():
 deadline=time.monotonic()+30
 while time.monotonic()<deadline:
  s=state()
  if s['outer_phase']==3 and s['menu_phase']==5 and s['mask']==3:return
  time.sleep(.08)
 raise RuntimeError('Card selection did not become ready: '+str(state()))
deadline=time.monotonic()+20
while True:
 try:frame();break
 except OSError:
  if time.monotonic()>deadline:raise
  time.sleep(.1)
while frame()<3050:time.sleep(.1)
press(0xfff7,650);press(0xbfff,400);wait_menu();initial=snap('card0');assert initial['slot']==0
press(0xffbf);one=snap('card1');assert one['slot']==1
press(0xffef);zero=snap('card0-return');assert zero['slot']==0
press(configured_button(0x80145ac4),450);cancel=snap('cancel');assert cancel['outer_phase']==1
press(0xbfff,350);wait_menu();snap('reenter')
press(0xbfff,350);confirmed=snap('confirm');assert confirmed['outer_phase']==3 and confirmed['menu_phase']!=5
if a.load_save:
 press(0xbfff,100);prompt=snap('load-prompt');assert prompt['menu_phase']==10
 press(0xbfff,1000);loaded=snap('loaded-save');assert loaded['outer_phase']==0
assert a.load_save,'Gameplay-loop probe requires --load-save'
code_ranges=[(0x801a8f94,0x801a96e4),(0x801a9de8,0x801aa470)]
code_evidence=[]
for lo,hi in code_ranges:
 data=ram(lo,hi-lo);path=a.out/f'live-code-{lo:08X}.bin';path.write_bytes(data)
 code_evidence.append({'entry':hex(lo),'end_exclusive':hex(hi),'sha256':hashlib.sha256(data).hexdigest(),'path':path.name})
(a.out/'live-state-jump-table.bin').write_bytes(ram(0x80195830,40))
for table,size in [(0x80195cc0,60),(0x80195d80,64)]:
 (a.out/f'live-command-table-{table:08X}.bin').write_bytes(ram(table,size))
(a.out/'live-code.json').write_text(json.dumps(code_evidence,indent=2)+'\n')
def gameplay_snap(label):
 data=ram(0x80146888,30*0x98);(a.out/f'{label}-records.bin').write_bytes(data)
 for name,addr,size in [('primary-records',0x80145e90,3*0x140),('small-records',0x80143fc8,20*0x74),('palette-records',0x80145bd4,32*12),('primary-controls',0x80146254,8),('palette-tables',0x801c7ac0,24),('sequence-records',0x80145d94,8*16)]:
  (a.out/f'{label}-{name}.bin').write_bytes(ram(addr,size))
 primary=ram(0x80145e90,0x140);index=primary[1];target=int.from_bytes(ram(0x801cd0ac+index*4,4),'little')
 (a.out/f'{label}-primary-callback.json').write_text(json.dumps({'record':'0x80145E90','state_index':index,'table_entry':hex(0x801cd0ac+index*4),'target':hex(target)},indent=2))
 substate=primary[2];subaddr=0x801cd0e8+substate*4;subtarget=int.from_bytes(ram(subaddr,4),'little')
 mode=struct.unpack('b',ram(0x80146870,1))[0];mode_addr=0x801c8454+mode*4;mode_pointer=int.from_bytes(ram(mode_addr,4),'little');mode_target=int.from_bytes(ram(mode_pointer,4),'little')
 (a.out/f'{label}-dispatch-context.json').write_text(json.dumps({'primary_substate':substate,'primary_table_entry':hex(subaddr),'primary_target':hex(subtarget),'mode':mode,'mode_table_entry':hex(mode_addr),'mode_pointer':hex(mode_pointer),'mode_target':hex(mode_target),'flag_helper_table_entry':'0x801C83F0','flag_helper_target':hex(int.from_bytes(ram(0x801c83f0,4),'little'))},indent=2))
 before=frame();clock_bytes=ram(0x80144fc0,4);countdowns=ram(0x80145554,8);phase=ram(0x80143bb0,1)[0];after=frame()
 (a.out/f'{label}-timers.json').write_text(json.dumps({'before_frame':before,'after_frame':after,'play_clock_bytes':list(clock_bytes),'countdown_bytes':list(countdowns),'phase':phase},indent=2))
 secondary_mode=struct.unpack('b',ram(0x801448ea,1))[0];secondary_entry=0x801c84a4+secondary_mode*4;secondary_target=int.from_bytes(ram(secondary_entry,4),'little')
 (a.out/f'{label}-position-context.json').write_text(json.dumps({'primary_footprint_selector':primary[0x70],'secondary_mode':secondary_mode,'secondary_table_entry':hex(secondary_entry),'secondary_target':hex(secondary_target),'primary_count':ram(0x80146254,1)[0],'primary_skip_flags':[ram(0x80145e90+i*0x140,1)[0]&0x40 for i in range(3)]},indent=2))
 s=snap(label);assert s['outer_phase']==0;return s
wait_frames(600);gameplay_snap('gameplay-idle')
call('press',buttons=0xffdf,frames=30);wait_frames(90);gameplay_snap('gameplay-right')
call('press',buttons=0xff7f,frames=30);wait_frames(90);gameplay_snap('gameplay-left')
wait_frames(600);gameplay_snap('gameplay-settled')
seq=call('present_shot_seq')['seq'];call('present_shot',path=(a.out/'present.png').resolve().as_posix())
deadline=time.monotonic()+10
while call('present_shot_seq')['seq']==seq:
 if time.monotonic()>deadline:raise RuntimeError('Presentation capture timed out')
 time.sleep(.1)
assert call('present_shot_seq')['wrote']

(a.out/'probe-result.json').write_text(json.dumps({'status':'complete','initial':{k:v for k,v in initial.items() if k in ('slot','menu_phase','outer_phase','mask')},'cancel':{k:v for k,v in cancel.items() if k in ('slot','menu_phase','outer_phase','mask')},'confirm':{k:v for k,v in confirmed.items() if k in ('slot','menu_phase','outer_phase','mask')}},indent=2))
# Controlled active palette cases run only after all untouched gameplay checkpoints.
# This process uses copied cards and is discarded; enable a descriptor only after all bytes are ready.
def write_bytes(addr,data):
 for i,value in enumerate(data):call('write_ram',addr=hex(addr+i),val=hex(value))
assert not any(ram(0x80145bd4,32*12)[i*12]&1 for i in range(32)), 'Synthetic cases require the observed inactive descriptor pool'
tables=ram(0x801c7ac0,24);assert (tables[0],tables[8],tables[16])==(1,16,16)
source=[0,0x7fff,0xffff,0x8000,0x001f,0x03e0,0x7c00,0x4210,0xc210,0x1234,0x9234,0x0421,0x7bde,0xfbde,0x2222,0xaaaa]
source_addr=0x80037800+(240//16)*512+(240%16)*32;dest_addr=source_addr+32
palette_cases=[]
for label,flags,bias in [('preserve-bit15',1,[12,244,0]),('force-bit15',3,[12,244,0]),('identity',1,[0,0,0]),('signed-wrap',3,[128,127,255])]:
 write_bytes(0x80145bd4,b'\0')
 write_bytes(source_addr,struct.pack('<16H',*source));write_bytes(dest_addr,b'\xa5'*32)
 descriptor=bytes([0,240,*bias,0,241,0,0,0,0,0]);write_bytes(0x80145bd4,descriptor)
 write_bytes(0x80145bd4,bytes([flags]));wait_frames(12)
 actual=list(struct.unpack('<16H',ram(dest_addr,32)))
 expected=[]
 for i,color in enumerate(source):
  channels=[]
  for shift,delta in zip([0,5,10],bias):
   v=(((color>>shift)&31)+delta)&255;v=v if v<128 else v-256;channels.append(max(0,min(31,v)))
  expected.append(0 if i==0 else channels[0]|channels[1]<<5|channels[2]<<10|(0x8000 if flags&2 else color&0x8000))
 palette_cases.append({'label':label,'flags':flags,'bias_bytes':bias,'source':source,'source_address':hex(source_addr),'destination_address':hex(dest_addr),'expected':expected,'actual':actual,'matches':actual==expected})
 assert actual==expected,(label,actual,expected)
 write_bytes(0x80145bd4,b'\0')
(a.out/'palette-active-cases.json').write_text(json.dumps({'scope':'Synthetic descriptor input after normal checkpoints in disposable copied-card session; no save writes requested. Tests type 0, RGB clamps/wrap, first-entry zero and bit15 behavior; not completion flags or all descriptor types.','cases':palette_cases},indent=2)+'\n')
print('Four controlled active palette cases passed',flush=True)

try:request(a.port,'quit')
except OSError:pass
