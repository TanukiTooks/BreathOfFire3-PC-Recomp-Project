import socket,json,time,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
def call(cmd,**kw):
    with socket.create_connection(('127.0.0.1',4381),timeout=5) as s:
        s.sendall((json.dumps(dict(id=1,cmd=cmd,**kw))+'\n').encode()); data=b''
        while True:
            chunk=s.recv(65536)
            if not chunk:return {'closed':True}
            data+=chunk
            try:return json.loads(data)
            except json.JSONDecodeError:pass
start=time.monotonic()
while True:
    try:call('pad_status');break
    except OSError:
        if time.monotonic()-start>15:raise
        time.sleep(.1)
samples=[]
for i in range(16):
    row={'seconds':round(time.monotonic()-start,3),'regs':call('get_registers'),'perf':call('frame_perf'),'phase':call('phase_profile',window=2),'mdec':call('mdec_state')}
    samples.append(row)
    print(json.dumps({'seconds':row['seconds'],'frame':row['regs'].get('frame'),'frame_ms':row['perf'].get('all',{}).get('total_ms_avg'),'interp_share':row['phase'].get('interp_share'),'mdec':row['mdec']}),flush=True)
    if i in [2,5,8,12,15]:call('screenshot_file',path=(root/f'intro-timing-{i}.png').as_posix())
    if i<15:time.sleep(2)
samples.append({'pad_status':call('pad_status')})
(root/'logs/intro-timing.json').write_text(json.dumps(samples,indent=2))
