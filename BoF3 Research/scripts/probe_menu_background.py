from pathlib import Path
import argparse,time,json
from record_runtime_coverage import request
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
def call(cmd,**kw):
 r=request(4387,cmd,**kw)
 if not r.get('ok',True):raise RuntimeError((cmd,r))
 return r
def frame():return call('get_registers')['frame']
def wait(n):
 goal=frame()+n;end=time.monotonic()+60
 while frame()<goal:
  if time.monotonic()>end:raise RuntimeError('Frame timeout')
  time.sleep(.06)
def ram(addr,n):return bytes.fromhex(call('read_ram',addr=hex(addr),len=n)['hex'])
def press(mask,n=150):call('press',buttons=mask,frames=5);wait(n)
def snap(label):
 seq=call('present_shot_seq')['seq'];call('present_shot',path=(a.out/(label+'-present.png')).resolve().as_posix());end=time.monotonic()+10
 while call('present_shot_seq')['seq']==seq:
  if time.monotonic()>end:raise RuntimeError('Presentation capture timeout')
  time.sleep(.05)
 assert call('present_shot_seq')['wrote']
 call('screenshot_file',path=(a.out/(label+'.png')).resolve().as_posix())
 state={'frame':frame(),'outer':int.from_bytes(ram(0x80143b92,2),'little'),'menu':ram(0x801ed860,1)[0],'pattern':ram(0x80144953,1)[0],'code':ram(0x801df21c,500).hex(),'draw_pointer':ram(0x8014598c,4).hex()}
 pointer=int.from_bytes(bytes.fromhex(state['draw_pointer']),'little');state['sampled_draw_bytes']=(pointer-0x8001ffcc)%0x9000;state['draw_arena_capacity']=0x9000
 (a.out/(label+'.json')).write_text(json.dumps(state,indent=2));print(label,state['outer'],state['menu'],flush=True)
end=time.monotonic()+25
while True:
 try:frame();break
 except OSError:
  if time.monotonic()>end:raise
  time.sleep(.1)
while frame()<3050:time.sleep(.1)
press(0xfff7,650);press(0xbfff,400)
assert int.from_bytes(ram(0x80143b92,2),'little')==3 and ram(0x801ed860,1)[0]==5
original=ram(0x80144953,1)[0];assert original<4
try:
 for pattern in range(4):
  call('write_ram',addr='0x80144953',val=hex(pattern));wait(30);snap('card-pattern'+str(pattern))
finally:call('write_ram',addr='0x80144953',val=hex(original))
button=int.from_bytes(ram(0x80145ac4,2),'little');cancel=0xffff^(((button&255)<<8)|(button>>8))
press(cancel,450);snap('title-return')
press(0xffef,80);snap('title-new-game');press(0xbfff,350);snap('new-game-entry')
assert int.from_bytes(ram(0x80143b92,2),'little')==2
try:
 for pattern in range(4):
  call('write_ram',addr='0x80144953',val=hex(pattern));wait(30);snap('name-pattern'+str(pattern))
finally:call('write_ram',addr='0x80144953',val=hex(original))
(a.out/'complete.json').write_text(json.dumps({'complete':True,'original_pattern_restored':ram(0x80144953,1)[0]==original,'scope':'All four patterns on card selection and character naming, return to title, copied-card runtime; no save writes.'}))
