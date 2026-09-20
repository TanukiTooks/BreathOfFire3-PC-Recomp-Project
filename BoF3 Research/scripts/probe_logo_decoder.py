"""Capture frame-exact logo samples, then run the established card/load probe."""
import argparse,hashlib,json,runpy,sys,time
from PIL import Image
from pathlib import Path
from record_runtime_coverage import request
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=4387);p.add_argument('--out',type=Path,required=True);p.add_argument('--load-save',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
def call(cmd,**kw):
 result=request(a.port,cmd,**kw)
 if not result.get('ok',True):raise RuntimeError((cmd,result))
 return result
started=time.monotonic()
while True:
 try:call('get_registers');break
 except OSError:
  if time.monotonic()-started>20:raise
  time.sleep(.1)
rows=[];skipped=[]
for target in range(550,991,20):
 deadline=time.monotonic()+40
 while call('get_registers')['frame']<=target:
  if time.monotonic()>deadline:raise RuntimeError(('Logo frame timeout',target))
  time.sleep(.035)
 path=a.out/f'logo-frame-{target:04d}.png'
 image=request(a.port,'display_ring_get',frame=target,path=path.resolve().as_posix())
 if not image.get('ok',True) and image.get('error')=='frame not in display ring':
  skipped.append({'frame':target,'ring':call('display_ring_stats'),'observed_frame':call('get_registers')['frame']});continue
 if not image.get('ok',True):
  assert image.get('error')=='frame is 24bpp scanout (unsupported)',image
  raw_path=a.out/f'logo-frame-{target:04d}.vram'
  dump=call('display_ring_aux',frame=target,path=raw_path.resolve().as_posix())
  history=call('get_frame',frame=target);di=history['display'];raw=raw_path.read_bytes();assert len(raw)==1024*512*2
  w=min(di['w'],640);h=min(di['h'],512);rgb=bytearray(w*h*3)
  # Same byte layout and edge blanking as gpu_display_pixel_rgb's depth24 path.
  for y in range(h):
   vy=(di['y']+y)&511
   for x in range(w):
    byte_x=(di['x']&1023)*2+x*3
    if byte_x+2<2048:rgb[(y*w+x)*3:(y*w+x+1)*3]=raw[vy*2048+byte_x:vy*2048+byte_x+3]
  Image.frombytes('RGB',(w,h),bytes(rgb)).save(path)
  image={'ok':True,'frame':target,'path':path.resolve().as_posix(),'width':w,'height':h,'method':'24-bit same-frame raw VRAM and display-history rectangle','vram_sha256':hashlib.sha256(raw).hexdigest(),'frame_record':history}
 rows.append({'frame':target,'image':image,'fmv':call('fmv_state')})
while call('get_registers')['frame']<1100:time.sleep(.05)
assert len(rows)>=10,('Insufficient retained logo samples',len(rows),skipped)
(a.out/'logo-samples.json').write_text(json.dumps({'status':'complete','samples':rows,'skipped':skipped,'dirty_after_logo':call('dirty_ram_stats'),'fmv_after_logo':call('fmv_state')},indent=2)+'\n')
print('Captured',len(rows),'frame-exact logo images.',flush=True)
runpy.run_path(str(Path(__file__).with_name('probe_card_selection.py')),run_name='__main__')
