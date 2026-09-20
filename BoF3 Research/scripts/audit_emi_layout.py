"""Infer and validate EMI section layout against every indexed local EMI.
Header field meanings beyond size/destination/type are deliberately unresolved.
"""
from pathlib import Path
import collections,hashlib,json,struct
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'BoF3 Research';OUT=R/'coverage'
files=json.loads((OUT/'disc-inventory.json').read_text())
track=ROOT/'iso/Breath of Fire III (USA)/Breath of Fire III (USA) (Track 1).bin'
sections=[];archives=[];issues=[]
with track.open('rb') as source:
 def read_file(f):
  data=bytearray()
  for sector in range((f['size']+2047)//2048):
   source.seek((f['lba']+sector)*2352+24);data.extend(source.read(2048))
  return bytes(data[:f['size']])
 for f in files:
  if not f['path'].upper().endswith('.EMI'):continue
  data=read_file(f)
  if len(data)<2048 or data[8:16]!=b'MATH_TBL':
   issues.append({'file':f['path'],'reason':'Unrecognized header'});continue
  count,header_word=struct.unpack_from('<II',data)
  if not 0<count<=127:
   issues.append({'file':f['path'],'reason':'Section count does not fit header sector'});continue
  cursor=2048;local=[]
  for i in range(count):
   size,destination,word2,word3=struct.unpack_from('<4I',data,16+i*16)
   if size<=0 or cursor+size>len(data):
    issues.append({'file':f['path'],'section':i,'reason':'Declared data outside archive'});break
   blob=data[cursor:cursor+size]
   row={'file':f['path'],'index':i,'file_offset':cursor,'size':size,'destination_field':f'0x{destination:08X}',
     'header_word2':f'0x{word2:08X}','type_low16':word3&0xffff,'header_high16':word3>>16,
     'sha256':hashlib.sha256(blob).hexdigest(),'ram_destination_plausible':0x80000000<=destination<0x80200000 and destination+size<=0x80200000,
     'code_status':'unclassified; header alone does not distinguish code from data'}
   local.append(row);cursor+=(size+2047)&~2047
   if (f['path'],i) in [('BIN/ETC/GAME.EMI',0),('BIN/ETC/STATUS.EMI',0)]:
    p=OUT/'ghidra-input'/f"{Path(f['path']).stem}-section-{i:02d}-{destination:08X}.bin"
    p.write_bytes(blob);row['extracted_file']=str(p.relative_to(R))
  else:
   if cursor!=len(data):issues.append({'file':f['path'],'reason':'Sector-padded section lengths do not equal file length','expected':cursor,'actual':len(data)})
   archives.append({'file':f['path'],'section_count':count,'header_word':header_word,'size':len(data),'layout_exact':cursor==len(data)})
   sections.extend(local)
clusters=collections.defaultdict(list)
for s in sections:
 if s['ram_destination_plausible'] and s['type_low16']==0:
  clusters[(s['destination_field'],s['size'],s['sha256'])].append({'file':s['file'],'index':s['index'],'file_offset':s['file_offset']})
unique=[{'destination':k[0],'size':k[1],'sha256':k[2],'occurrences':v} for k,v in clusters.items()]
summary={'emi_files':sum(f['path'].upper().endswith('.EMI') for f in files),'archives_parsed':len(archives),'layout_exact_archives':sum(a['layout_exact'] for a in archives),'section_count':len(sections),'type_counts':dict(collections.Counter(s['type_low16'] for s in sections)),'type0_ram_section_occurrences':sum(len(v) for v in clusters.values()),'unique_type0_ram_images':len(unique),'issues':issues,'model':'One 2048-byte header; count at 0, MATH_TBL at 8; 16-byte records at 16; sequential payloads each padded to 2048 bytes. Type meanings are not yet loader-verified.'}
(OUT/'emi-layout-summary.json').write_text(json.dumps(summary,indent=2))
(OUT/'emi-sections.json').write_text(json.dumps(sections,indent=2))
(OUT/'emi-ram-image-groups.json').write_text(json.dumps(unique,indent=2))
print(json.dumps(summary,indent=2))
for group in unique:
 if any(o['file']=='BIN/ETC/STATUS.EMI' and o['index']==0 for o in group['occurrences']):print('Shared STATUS first section:',json.dumps(group))
