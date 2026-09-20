import sys,time,json
from pathlib import Path
from record_runtime_coverage import request
out=Path(sys.argv[1]);label=sys.argv[2]
def sample():
 t=time.perf_counter();a=request(4387,'get_registers')['frame'];c=bytes.fromhex(request(4387,'read_ram',addr='0x80144fc0',len=4)['hex']);b=request(4387,'get_registers')['frame'];return {'time':t,'frame':a,'after_frame':b,'clock':list(c),'ticks':((c[0]*60+c[1])*60+c[2])*30+c[3]}
a=sample();time.sleep(6);b=sample();elapsed=b['time']-a['time'];result={'label':label,'before':a,'after':b,'elapsed':elapsed,'guest_frames_per_second':(b['frame']-a['frame'])/elapsed,'game_clock_seconds_per_wall_second':(b['ticks']-a['ticks'])/30/elapsed}
(out/(label+'.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
