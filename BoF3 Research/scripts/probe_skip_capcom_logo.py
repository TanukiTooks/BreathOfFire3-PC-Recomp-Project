from pathlib import Path
import argparse,time,json,runpy,sys
from PIL import Image
from record_runtime_coverage import request
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--load-save',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
def call(cmd,**kw):
 r=request(4387,cmd,**kw)
 if not r.get('ok',True):raise RuntimeError((cmd,r))
 return r
end=time.monotonic()+25
while True:
 try:call('get_registers');break
 except OSError:
  if time.monotonic()>end:raise
  time.sleep(.05)
rows=[]
for target in [550,650,750,850,950,1100,1500,2000,2500,3000]:
 end=time.monotonic()+45
 while call('get_registers')['frame']<=target:
  if time.monotonic()>end:raise RuntimeError('Frame timeout')
  time.sleep(.02)
 path=a.out/f'frame-{target}.png';meta=call('get_frame',frame=target);di=meta['display']
 if di.get('depth24',False) or di.get('depth',0)==24:
  pass
 r=request(4387,'display_ring_get',frame=target,path=path.resolve().as_posix())
 if not r.get('ok',True) and r.get('error')=='frame not in display ring':
  meta['capture_method']='no rendered display-ring entry at target; transition/disabled display'
  meta['fallback_capture']=request(4387,'screenshot_file',path=path.resolve().as_posix())
  r={'ok':True}
 if not r.get('ok',True):
  assert r.get('error')=='frame is 24bpp scanout (unsupported)',r
  rawpath=a.out/f'frame-{target}.vram';call('display_ring_aux',frame=target,path=rawpath.resolve().as_posix());raw=rawpath.read_bytes();w=min(di['w'],640);h=min(di['h'],512);rgb=bytearray(w*h*3)
  for y in range(h):
   for x in range(w):
    bx=(di['x']&1023)*2+x*3
    if bx+2<2048:rgb[(y*w+x)*3:(y*w+x+1)*3]=raw[((di['y']+y)&511)*2048+bx:((di['y']+y)&511)*2048+bx+3]
  Image.frombytes('RGB',(w,h),bytes(rgb)).save(path)
 rows.append({'target':target,'frame':meta,'fmv':call('fmv_state'),'logo_exit_code':call('read_ram',addr='0x801cee28',len=84)['hex']})
 print(target,rows[-1]['fmv'].get('mdec_decode_count'),flush=True)
(a.out/'startup.json').write_text(json.dumps(rows,indent=2))
runpy.run_path(str(Path(__file__).with_name('probe_card_selection.py')),run_name='__main__')
