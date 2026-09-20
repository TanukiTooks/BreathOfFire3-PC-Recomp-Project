import sys,time,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from record_runtime_coverage import request
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'BoF3 Research';OUT=R/'coverage/loader-verification/runtime';PORT=4386

def call(cmd,**kw):return request(PORT,cmd,**kw)
def wait_frame(target,seconds=45):
 deadline=time.monotonic()+seconds
 while time.monotonic()<deadline:
  try:
   f=call('get_registers').get('frame',0)
   if f>=target:return f
  except OSError:pass
  time.sleep(.15)
 raise RuntimeError('Runtime did not reach checkpoint')
def snapshot(label):
 result={'frame':call('get_registers').get('frame'),'sections':[]}
 for name,address in [('GAME-section-00-80195800.bin',0x80195800),('STATUS-section-00-801D0C00.bin',0x801d0c00)]:
  source=(R/'coverage/ghidra-input'/name).read_bytes();response=call('read_ram',addr=f'0x{address:08X}',len=len(source));live=bytes.fromhex(response['hex'])
  if len(live)!=len(source):raise RuntimeError(f'Incomplete RAM response for {name}: {len(live)} != {len(source)}')
  (OUT/f'{label}-{name}').write_bytes(live)
  differences=[i for i,(a,b) in enumerate(zip(source,live)) if a!=b]
  result['sections'].append({'input':name,'address':f'0x{address:08X}','size':len(source),'matching_bytes':len(source)-len(differences),'exact_match':not differences,'first_different_offsets':differences[:20],'ram_sha256':hashlib.sha256(live).hexdigest()})
 result['cd_reads']=call('cd_read_log',tail=65536,lba_lo=61520,lba_hi=62307,max_entries=4096)
 (OUT/f'{label}.json').write_text(json.dumps(result,indent=2));print(label,json.dumps({k:v for k,v in result.items() if k!='cd_reads'}),flush=True)
frame=wait_frame(3050);snapshot('title')
call('press',buttons=65527,frames=5);frame=wait_frame(frame+650)
call('press',buttons=49151,frames=5);wait_frame(frame+600)
snapshot('load-menu');call('screenshot_file',path=(OUT/'load-menu.png').as_posix());print(call('quit'))
