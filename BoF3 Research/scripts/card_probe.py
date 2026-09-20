import socket,json,time,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
def call(cmd,**kw):
    with socket.create_connection(('127.0.0.1',4381),timeout=5) as s:
        s.sendall((json.dumps(dict(id=1,cmd=cmd,**kw))+'\n').encode()); data=b''
        while True:
            chunk=s.recv(65536)
            if not chunk:raise RuntimeError('Server closed response')
            data+=chunk
            try:return json.loads(data)
            except json.JSONDecodeError:pass
if __name__=='__main__':
    start=time.monotonic()
    while time.monotonic()-start<50:
        try:
            state=call('get_registers')
            if state.get('frame',0)>=3050:break
        except OSError:pass
        time.sleep(.2)
    else:raise RuntimeError('Did not reach title checkpoint within 50 seconds')
    print(call('press',buttons=65527,frames=20))
    time.sleep(.7)
    print(call('screenshot_file',path=(root/'card-probe-menu.png').as_posix()))
