"""Bounded read-only coverage recording from the runtime's loopback debug API."""
import argparse,collections,json,socket,time
from pathlib import Path

def request(port,cmd,**values):
    with socket.create_connection(('127.0.0.1',port),timeout=5) as connection:
        connection.sendall((json.dumps(dict(id=1,cmd=cmd,**values))+'\n').encode())
        data=b''
        while len(data)<4*1024*1024:
            chunk=connection.recv(65536)
            if not chunk:raise OSError('Runtime closed the response')
            data+=chunk
            try:return json.loads(data)
            except json.JSONDecodeError:pass
        raise ValueError('Oversized debug response')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=4385)
    parser.add_argument('--seconds',type=int,default=35)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if not 1<=args.seconds<=600:parser.error('seconds must be 1..600')
    args.out.mkdir(parents=True,exist_ok=True)
    startup=time.monotonic()
    while True:
        try:request(args.port,'get_registers');break
        except OSError:
            if time.monotonic()-startup>20:raise
            time.sleep(.1)
    began=time.monotonic();samples=[];status='complete'
    with (args.out/'samples.jsonl').open('w') as output:
        while True:
            row={'seconds':round(time.monotonic()-began,3)}
            try:
                for key,cmd in [('cpu','get_registers'),('phase','phase_profile'),('dirty','dirty_ram_stats'),('overlays','overlay_loader_status')]:
                    row[key]=request(args.port,cmd,**({'window':1} if key=='phase' else {}))
            except (OSError,ValueError) as error:
                row['error']=str(error);status='interrupted'
            output.write(json.dumps(row)+'\n');output.flush();samples.append(row)
            if status!='complete' or row['seconds']>=args.seconds:break
            time.sleep(min(1,max(0,args.seconds-(time.monotonic()-began))))
    top={}
    for row in samples:
        for pc in row.get('dirty',{}).get('per_pc',[]):
            if pc.get('insns',0)>top.get(pc['pc'],{}).get('insns',-1):top[pc['pc']]=pc
    good=[r for r in samples if 'error' not in r]
    summary={'status':status,'elapsed_seconds':round(time.monotonic()-began,3),'sample_count':len(good),
      'first_frame':good[0]['cpu'].get('frame') if good else None,'last_frame':good[-1]['cpu'].get('frame') if good else None,
      'interpreter_hotspots':sorted(top.values(),key=lambda x:x.get('insns',0),reverse=True)[:30],
      'limitations':['Headless throughput is not presentation FPS or audio quality.','per_pc table can be truncated; totals may include activity before recording.','Same PC may host different code; occ_crc is observational context, not a complete per-image attribution.','No whole-game native percentage is implied.']}
    if status=='complete':
        summary['capture_flush']=request(args.port,'overlay_capture_dump')
        summary['screenshot']=request(args.port,'screenshot_file',path=(args.out/'last-frame.png').as_posix())
    (args.out/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps({k:v for k,v in summary.items() if k not in ['interpreter_hotspots','limitations','screenshot']},indent=2))
    if status!='complete':raise SystemExit(2)
if __name__=='__main__':main()
