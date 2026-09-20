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

def capture(label):
 s=snap(label)
 for name,addr,size in [('primary',0x80145e90,3*0x140),('scene',0x80146888,30*0x98),('small',0x80143fc8,20*0x74),('party-stats',0x801448e8,8*0xa4),('controls',0x80146254,12),('palette',0x80145bd4,32*12),('sequences',0x80145d94,128),('camera',0x801492d8,0x70)]:
  (a.out/(label+'-'+name+'.bin')).write_bytes(ram(addr,size))
 for lo,hi in [(0x801bdbc4,0x801bdcf8),(0x801a2ae4,0x801a2c10),(0x801f2c00,0x80200000)]:
  (a.out/(label+'-code-'+format(lo,'08X')+'.bin')).write_bytes(ram(lo,hi-lo))
 (a.out/(label+'-context.json')).write_text(json.dumps({'party_count':ram(0x80146254,1)[0],'scene_mode':ram(0x80146870,1)[0],'map':ram(0x80143f00,4).hex(),'clock':list(ram(0x80144fc0,4))},indent=2))
 return s
wait_frames(600);capture('camp-idle')
call('press',buttons=0xffdf,frames=30);wait_frames(120);capture('camp-right')
call('press',buttons=0xff7f,frames=30);wait_frames(120);capture('camp-return')
wait_frames(600);capture('camp-settled')
call('press',buttons=0xff7f,frames=60);wait_frames(120);capture('camp-exit-approach')
call('press',buttons=0xffbf,frames=100);wait_frames(1100);capture('world-loaded')
call('press',buttons=0xffdf,frames=20);wait_frames(180);capture('world-right')
call('press',buttons=0xff7f,frames=20);wait_frames(180);capture('world-return')
wait_frames(600);capture('world-settled')
(a.out/'complete.json').write_text(json.dumps({'complete':True,'scope':'Copied full-party save: camp movement/following, camp-to-world transition, world movement; no save writes or synthetic state changes.'}))
