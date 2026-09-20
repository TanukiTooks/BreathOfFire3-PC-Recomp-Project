from pathlib import Path
import argparse,json,time
from record_runtime_coverage import request
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();D=a.out

def call(cmd,**kw):
 r=request(4387,cmd,**kw)
 if not r.get('ok',True):raise RuntimeError((cmd,r))
 return r

def frame():return call('get_registers')['frame']
def wait(target):
 end=time.monotonic()+40
 while frame()<target:
  if time.monotonic()>end:raise RuntimeError('Frame timeout')
  time.sleep(.045)
def ram(addr,n):return bytes.fromhex(call('read_ram',addr=hex(addr),len=n)['hex'])
end=time.monotonic()+25
while True:
 try:frame();break
 except OSError:
  assert time.monotonic()<end;time.sleep(.1)
rows=[]
for target in [1000,1100,1200,1300,1400,1500,1600,1700,1800,1900,2000,2200,2600]:
 wait(target+2);r=request(4387,'display_ring_get',frame=target,path=(D/f'frame-{target}.png').as_posix())
 seq=call('present_shot_seq')['seq'];call('present_shot',path=(D/f'present-{target}.png').as_posix());end=time.monotonic()+10
 while call('present_shot_seq')['seq']==seq:
  assert time.monotonic()<end;time.sleep(.03)
 now=frame();state=ram(0x80143c10,0x24);code=ram(0x801d18f8,520);gpu=[call('gpu_frame_dump',frame=f,count=128) for f in range(now-3,now)]
 rows.append({'target':target,'capture':r,'observed_frame':now,'state':state.hex(),'scroll':int.from_bytes(state[18:20],'little'),'brightness':int.from_bytes(state[20:22],'little'),'mural_phase':state[33],'title_phase':state[34],'gpu':gpu,'code':code.hex()});print(target,rows[-1]['scroll'],rows[-1]['mural_phase'],flush=True)
(D/'samples.json').write_text(json.dumps(rows,indent=2))
wait(3050);call('press',buttons=0xfff7,frames=5);wait(frame()+650);call('press',buttons=0xbfff,frames=5);wait(frame()+400)
assert int.from_bytes(ram(0x80143b92,2),'little')==3 and ram(0x801ed860,1)[0]==5
call('present_shot',path=(D/'menu-present.png').as_posix());wait(frame()+5)
(D/'complete.json').write_text(json.dumps({'complete':True,'card_selection_reached':True,'fmv':call('fmv_state')}))
