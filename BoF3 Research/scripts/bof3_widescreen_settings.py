"""Edit only BoF3's optional widescreen feature in the runtime mod state."""
import hashlib,json,os,re,tempfile,tomllib
PACKAGE='bof3.presentation.widescreen'
VERSION='0.1.0'
def read(path):
 raw=path.read_bytes() if path.exists() else b''
 doc=tomllib.loads(raw.decode('utf-8-sig')) if raw else {'format_version':2}
 if doc.get('format_version')!=2:raise ValueError('Unsupported mod state version; left unchanged.')
 for key in ('package','feature'):
  if not isinstance(doc.get(key,[]),list) or any(not isinstance(x,dict) for x in doc.get(key,[])):raise ValueError('Invalid mod state; left unchanged.')
 owned=[x for x in doc.get('feature',[]) if x.get('package_id')==PACKAGE and x.get('id')=='widescreen']
 if len(owned)>1:raise ValueError('Duplicate widescreen feature; left unchanged.')
 enabled=owned[0].get('enabled',False) if owned else False
 if not isinstance(enabled,bool):raise ValueError('Invalid widescreen state; left unchanged.')
 return raw,doc,enabled

def prepare(path,enabled):
 raw,doc,_=read(path);text=raw.decode('utf-8-sig') if raw else 'format_version = 2\n'
 blocks=list(re.finditer(r'^\[\[(package|feature)\]\][ \t]*(?:#[^\r\n]*)?\r?$',text,re.M))
 replacements=[];found=set()
 for i,m in enumerate(blocks):
  end=blocks[i+1].start() if i+1<len(blocks) else len(text)
  body=text[m.start():end];kind=m[1];parsed=tomllib.loads(body)[kind][0]
  own=(kind=='package' and parsed.get('id')==PACKAGE) or (kind=='feature' and parsed.get('package_id')==PACKAGE and parsed.get('id')=='widescreen')
  if not own:continue
  if kind in found:raise ValueError('Duplicate widescreen mod entry; left unchanged.')
  found.add(kind);key='version' if kind=='package' else 'enabled';value=json.dumps(VERSION if kind=='package' else enabled)
  pattern=r'^[ \t]*'+key+r'[ \t]*=[^\r\n]*'
  if re.search(pattern,body,re.M):new=re.sub(pattern,lambda _:key+' = '+value,body,count=1,flags=re.M)
  else:new=body[:m.end()-m.start()]+'\n'+key+' = '+value+body[m.end()-m.start():]
  replacements.append((m.start(),end,new))
 for start,end,new in reversed(replacements):text=text[:start]+new+text[end:]
 if 'package' not in found:text+='\n[[package]]\nid = '+json.dumps(PACKAGE)+'\nversion = '+json.dumps(VERSION)+'\n'
 if 'feature' not in found:text+='\n[[feature]]\npackage_id = '+json.dumps(PACKAGE)+'\nid = "widescreen"\nenabled = '+json.dumps(enabled)+'\n'
 parsed=tomllib.loads(text)
 def unrelated(d):
  d=dict(d);d['package']=[x for x in d.get('package',[]) if x.get('id')!=PACKAGE];d['feature']=[x for x in d.get('feature',[]) if not(x.get('package_id')==PACKAGE and x.get('id')=='widescreen')];return d
 if unrelated(doc)!=unrelated(parsed):raise ValueError('Unsupported mod layout; left unchanged.')
 return raw,text.encode('utf-8')

def write(path,data):
 path.parent.mkdir(parents=True,exist_ok=True)
 fd,temp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(data)
  os.replace(temp,path)
 finally:
  if os.path.exists(temp):os.unlink(temp)
