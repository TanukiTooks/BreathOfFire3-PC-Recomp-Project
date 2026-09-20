"""Game-owned display preferences for PSXRecomp's existing settings.toml."""
from pathlib import Path
import argparse,hashlib,json,os,re,tempfile,tomllib
import bof3_widescreen_settings as widescreen
ROOT=Path(__file__).resolve().parents[2]
DEFAULT_PATH=ROOT/'BoF3 PSXRecomp/BreathOfFireIII/build-release/settings.toml'
WIDTHS=(640,960,1280,1600,1920)
def read(path):
 raw=path.read_bytes() if path.exists() else b''
 doc=tomllib.loads(raw.decode('utf-8-sig')) if raw else {}
 if not isinstance(doc.get('bof3',{}),dict):raise ValueError('Invalid BoF3 settings section; left unchanged.')
 if not isinstance(doc.get('video',{}),dict):raise ValueError('The video settings section is not a table; the file was left unchanged.')
 return raw,doc,hashlib.sha256(raw).hexdigest()
def show(path):
 raw,doc,sha=read(path);v=doc.get('video',{})
 mod_raw,_,wide=widescreen.read(path.parent/'mods/state.toml');sha=hashlib.sha256(raw+b'\0'+mod_raw).hexdigest()
 geom=bool(v.get('geometry_correction',False));tex=bool(v.get('perspective_texturing',False))
 return {'psx_wobble':(not geom) if geom==tex else None,'skip_capcom_logo':doc.get('bof3',{}).get('skip_capcom_logo',False),'turbo_speed':doc.get('bof3',{}).get('turbo_speed',2),'path':str(path),'source_sha':sha,'aspect':'16:9' if wide else '4:3','window_mode':'borderless' if v.get('fullscreen',0) else 'windowed','width':v.get('window_width',960),'scale':v.get('supersampling',1),'filter':v.get('texture_filtering','nearest'),'vsync':v.get('vsync','on')}
def update_table(text,section_name,values):
 doc=tomllib.loads(text) if text else {}
 headers=list(re.finditer(r'^\s*\[([^\]\r\n]+)\][ \t]*(?:#[^\r\n]*)?\r?$',text,re.M));section=next((m for m in headers if m[1].strip()==section_name),None)
 if section:
  end=next((m.start() for m in headers if m.start()>section.start()),len(text));body=text[section.end():end]
  for key,value in values.items():
   line=key+' = '+json.dumps(value);pattern=r'^[ \t]*'+re.escape(key)+r'[ \t]*=[^\r\n]*'
   if re.search(pattern,body,re.M):body=re.sub(pattern,lambda _:line,body,flags=re.M)
   else:body=body.rstrip()+'\n'+line+'\n'
  updated=text[:section.end()]+body.rstrip()+'\n\n'+text[end:]
 else:
  if section_name in doc:raise ValueError('The video settings use an unsupported layout; the file was left unchanged.')
  updated=text.rstrip()+'\n\n['+section_name+']\n'+'\n'.join(k+' = '+json.dumps(v) for k,v in values.items())+'\n'
 return updated

def save(path,mode,width,scale,filtering,vsync,expected_sha=None,aspect=None,turbo_speed=None,skip_capcom_logo=None,psx_wobble=None):
 if mode not in ('windowed','borderless') or width not in WIDTHS or scale not in (1,2,3,4) or filtering not in ('nearest','bilinear') or vsync not in ('on','off'):raise ValueError('Choose a supported display setting.')
 if turbo_speed is not None and (type(turbo_speed) is not int or turbo_speed not in (2,4)):raise ValueError('Turbo speed must be 2x or 4x.')
 if skip_capcom_logo is not None and type(skip_capcom_logo) is not bool:raise ValueError('Skip Capcom logo must be on or off.')
 if psx_wobble is not None and type(psx_wobble) is not bool:raise ValueError('PSX polygon wobble must be on or off.')
 raw,doc,sha=read(path)
 sha=show(path)['source_sha']
 if aspect not in (None,'4:3','16:9'):raise ValueError('Choose 4:3 or experimental 16:9.')
 mod_path=path.parent/'mods/state.toml';mod_update=widescreen.prepare(mod_path,aspect=='16:9') if aspect is not None else None
 if expected_sha is not None and expected_sha!=sha:raise ValueError('Settings changed since this window opened. Close and reopen it before saving.')
 values={'renderer':'opengl','aspect_ratio':'4:3','fullscreen':int(mode=='borderless'),'window_width':width,'supersampling':scale,'texture_filtering':filtering,'antialiasing':False,'vsync':vsync}
 if psx_wobble is not None:values.update(geometry_correction=not psx_wobble,perspective_texturing=not psx_wobble)
 updated=update_table(raw.decode('utf-8-sig'),'video',values)
 owned={}
 if turbo_speed is not None:owned['turbo_speed']=turbo_speed
 if skip_capcom_logo is not None:owned['skip_capcom_logo']=skip_capcom_logo
 if owned:updated=update_table(updated,'bof3',owned)
 parsed=tomllib.loads(updated);assert all(parsed['video'][k]==v for k,v in values.items())
 for k,v in doc.items():
  if k not in ('video','bof3'):assert parsed[k]==v
 for k,v in doc.get('bof3',{}).items():
  if k not in owned:assert parsed['bof3'][k]==v
 for k,v in doc.get('video',{}).items():
  if k not in values:assert parsed['video'][k]==v
 path.parent.mkdir(parents=True,exist_ok=True)
 if raw:
  backup=path.with_name(path.name+'.before-display-settings')
  if not backup.exists():backup.write_bytes(raw)
 fd,temp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
 try:
  with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as f:f.write(updated)
  os.replace(temp,path)
 finally:
  if os.path.exists(temp):os.unlink(temp)
 if mod_update is not None:
  previous,updated_mods=mod_update
  try:
   if previous:
    backup=mod_path.with_name('state.toml.before-widescreen')
    if not backup.exists():backup.write_bytes(previous)
   widescreen.write(mod_path,updated_mods)
  except OSError:
   if raw:widescreen.write(path,raw)
   else:path.unlink(missing_ok=True)
   raise
 return show(path)
def main():
 p=argparse.ArgumentParser();p.add_argument('--path',type=Path,default=DEFAULT_PATH);sub=p.add_subparsers(dest='command',required=True);sub.add_parser('show');s=sub.add_parser('save')
 s.add_argument('--window-mode',required=True);s.add_argument('--width',type=int,required=True);s.add_argument('--scale',type=int,required=True);s.add_argument('--filter',required=True);s.add_argument('--vsync',required=True);s.add_argument('--expected-sha');s.add_argument('--aspect',choices=['4:3','16:9']);s.add_argument('--turbo-speed',type=int,choices=[2,4]);s.add_argument('--skip-capcom-logo',choices=['on','off']);s.add_argument('--psx-wobble',choices=['on','off'])
 a=p.parse_args()
 try:result=show(a.path) if a.command=='show' else save(a.path,a.window_mode,a.width,a.scale,a.filter,a.vsync,a.expected_sha,a.aspect,a.turbo_speed,None if a.skip_capcom_logo is None else a.skip_capcom_logo=='on',None if a.psx_wobble is None else a.psx_wobble=='on')
 except (ValueError,OSError,tomllib.TOMLDecodeError) as e:print(str(e));raise SystemExit(1)
 print(json.dumps(result))
if __name__=='__main__':main()
