import argparse,time,json,struct
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
 s=state();s['dirty']=call('dirty_ram_stats');s['overlays']=call('overlay_loader_status');s['phase']=call('phase_profile',window=1);call('screenshot_file',path=(a.out/(label+'.png')).resolve().as_posix());(a.out/(label+'.json')).write_text(json.dumps(s,indent=2));print(label,{k:v for k,v in s.items() if k not in ('dirty','overlays','phase')},flush=True);return s
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
(a.out/'probe-result.json').write_text(json.dumps({'status':'complete','initial':{k:v for k,v in initial.items() if k in ('slot','menu_phase','outer_phase','mask')},'cancel':{k:v for k,v in cancel.items() if k in ('slot','menu_phase','outer_phase','mask')},'confirm':{k:v for k,v in confirmed.items() if k in ('slot','menu_phase','outer_phase','mask')}},indent=2))
try:request(a.port,'quit')
except OSError:pass
