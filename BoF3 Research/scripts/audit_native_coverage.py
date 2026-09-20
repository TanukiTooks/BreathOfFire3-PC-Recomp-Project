"""Read-only source/disc audit; writes reports under BoF3 Research/coverage.
Counts generated dispatch entries, not semantic functions or whole-game coverage.
"""
from pathlib import Path
import base64,bisect,collections,csv,hashlib,json,mmap,re,struct
ROOT=Path(__file__).resolve().parents[2]
RESEARCH=ROOT/'BoF3 Research'
GAME=ROOT/'BoF3 PSXRecomp/BreathOfFireIII'
OUT=RESEARCH/'coverage'
OUT.mkdir(exist_ok=True)
probe=json.loads((RESEARCH/'recompone-disc-probe.json').read_text(encoding='utf-8-sig'))
files=sorted(probe['files'],key=lambda f:f['lba'])
starts=[f['lba']*2048 for f in files]
track=ROOT/'iso/Breath of Fire III (USA)/Breath of Fire III (USA) (Track 1).bin'
with track.open('rb') as stream:
 with mmap.mmap(stream.fileno(),0,access=mmap.ACCESS_READ) as raw:
  payload=b''.join(raw[n+24:n+2072] for n in range(0,len(raw),2352))
# Ensure this interpretation agrees with the independently extracted boot input.
boot=next(f for f in files if f['path']==probe['boot'])
assert payload[boot['lba']*2048:boot['lba']*2048+boot['size']]==(RESEARCH/'input/SLUS_004.22').read_bytes()
main_text=(GAME/'generated/SLUS_004.22_dispatch.c').read_text()
overlay_text=(GAME/'generated-startup-card-overlays/overlays_static.c').read_text()
main_table=re.search(r'k_psx_game_dispatch\s*\[.*?\]\s*=\s*\{(.*?)\n\};',main_text,re.S)
if main_table is None:
 # Locate the table by its declared element type rather than one historical name.
 main_table=re.search(r'static const PsxGameDispatchEntry\s+\w+\s*\[.*?\]\s*=\s*\{(.*?)\n\};',main_text,re.S)
if main_table is None:raise ValueError('Generated game dispatch table format changed')
main_entries=set(int(x,16) for x in re.findall(r'\{\s*0x([0-9A-Fa-f]+)u',main_table.group(1)))
ov_entries=re.search(r'psx_ov_entries\[(\d+)\]\s*=\s*\{(.*?)\n\};',overlay_text,re.S)
ov_variants=re.search(r'psx_ov_variants\[(\d+)\]',overlay_text)
assert ov_entries and ov_variants
ov_addresses=set(int(x,16) for x in re.findall(r'\{\s*0x([0-9A-Fa-f]+)u',ov_entries.group(2)))
assert len(ov_addresses)==int(ov_entries.group(1))
prototypes=set(re.findall(r'^void (\w+)\(CPUState \*cpu\);',overlay_text,re.M))
ghidra=list(csv.DictReader((RESEARCH/'ghidra-functions.tsv').open(),delimiter='\t'))
in_game=[r for r in ghidra if 0x80096800<=int(r['address'],16)<0x801f7000]
source_rows=[]
for f in files:
 blob=payload[f['lba']*2048:f['lba']*2048+f['size']]
 row=dict(f,sha256=hashlib.sha256(blob).hexdigest(),family=f['path'].rsplit('/',1)[0] if '/' in f['path'] else '(root)')
 if blob.startswith(b'PS-X EXE'):
  row['verified_header']={'entry_pc':f'0x{struct.unpack_from("<I",blob,0x10)[0]:08X}','load_address':f'0x{struct.unpack_from("<I",blob,0x18)[0]:08X}','text_size':struct.unpack_from('<I',blob,0x1c)[0]}
 source_rows.append(row)
# 64-byte instruction anchors; all matches are retained, including ambiguous SDK copies.
captures=json.loads((RESEARCH/'startup-card-overlay-captures.json').read_text())
match_rows=[]
for number,cap in enumerate(captures):
 data=base64.b64decode(cap['bytes_b64']); lo=int(cap['load_addr'],16)
 offsets=set()
 for field in ['dispatch_entry_pcs','function_entry_pcs','executed_pcs']:
  for value in cap.get(field,[]):
   pc=int(value,0) if isinstance(value,str) else value
   off=(pc&0x1fffffff)-(lo&0x1fffffff)
   if 0<=off<=len(data)-64:offsets.add(off)
 candidates=sorted(offsets)
 if len(candidates)>12:candidates=[candidates[i*(len(candidates)-1)//11] for i in range(12)]
 anchors=[]; matches=collections.defaultdict(set)
 for off in candidates:
  anchor=data[off:off+64]
  if len(set(struct.unpack('<16I',anchor)))<6:continue
  positions=[]; pos=payload.find(anchor)
  while pos>=0 and len(positions)<65:
   positions.append(pos);pos=payload.find(anchor,pos+1)
  if len(positions)>=65:continue
  anchors.append(off)
  for pos in positions:
   index=bisect.bisect_right(starts,pos)-1
   if index<0:continue
   f=files[index];foff=pos-starts[index]
   if foff+64>f['size']:continue
   mapping=(lo+off-foff)&0xffffffff
   matches[(index,mapping)].add(off)
 ranked=[]
 for (index,mapping),support in matches.items():
  if len(support)<2:continue
  f=files[index];fileoff=lo-mapping
  start=max(0,-fileoff);end=min(len(data)-cap.get('guard_bytes',0),f['size']-fileoff)
  if end<=start:continue
  disk=payload[starts[index]+fileoff+start:starts[index]+fileoff+end]
  live=data[start:end]
  equal=sum(a==b for a,b in zip(live,disk))
  ranked.append({'file':f['path'],'file_byte_zero_ram_address':f'0x{mapping:08X}','matching_anchors':len(support),'anchor_offsets':sorted(support),'compared_bytes':len(live),'equal_bytes':equal,'byte_match_fraction':round(equal/len(live),6)})
 ranked.sort(key=lambda x:(-x['matching_anchors'],-x['byte_match_fraction'],x['file']))
 match_rows.append({'capture_id':number,'load_address':cap['load_addr'],'size':cap['size'],'sha256':hashlib.sha256(data).hexdigest(),'anchors_tested':len(anchors),'candidates':ranked,'note':'Exact byte anchors support a file-to-RAM translation, not a complete loader/relocation proof. Shared code can match multiple files.'})
print('Disc matching complete.',flush=True)
for row in source_rows:
 evidence=[m['capture_id'] for m in match_rows if any(c['file']==row['path'] for c in m['candidates'])]
 row['capture_match_ids']=evidence
 row['audit_status']='boot-static-generated' if row['path']==probe['boot'] else 'runtime-byte-anchor-candidate' if evidence else 'code-candidate-unmapped' if row['kind']=='rawcode' else 'header-executable' if 'verified_header' in row else 'unreviewed-data-or-media'
summary={'source':'Current generated source, existing captures, supplied disc; no new runtime benchmark','disc_files':len(files),'probe_kind_counts':dict(collections.Counter(f['kind'] for f in files)),'main_generated_function_declarations':len(set(re.findall(r'extern void (func_[0-9A-F]+)\(',main_text))),'main_dispatch_entries':len(main_entries),'overlay_dispatch_addresses':len(ov_addresses),'overlay_address_variants':int(ov_variants.group(1)),'overlay_generated_function_prototypes':len(prototypes),'captured_byte_image_variants':len(captures),'ghidra_game_image_functions':len(in_game),'ghidra_game_starts_in_main_dispatch':sum(int(r['address'],16) in main_entries for r in in_game),'ghidra_external_functions':len(ghidra)-len(in_game),'captures_with_disc_anchor_candidates':sum(bool(m['candidates']) for m in match_rows),'whole_game_native_percentage':None,'percentage_unavailable_reason':'Total executable code and reachable overlay variants are not established; dispatch entries include continuation addresses and are not semantic function counts.'}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2))
(OUT/'disc-inventory.json').write_text(json.dumps(source_rows,indent=2))
(OUT/'capture-disc-matches.json').write_text(json.dumps(match_rows,indent=2))
with (OUT/'disc-inventory.tsv').open('w',newline='') as stream:
 writer=csv.writer(stream,delimiter='\t');writer.writerow(['file','bytes','kind_heuristic','base_guess','status','capture_ids','sha256'])
 for r in source_rows:writer.writerow([r['path'],r['size'],r['kind'],r.get('baseAddress'),r['audit_status'],','.join(map(str,r['capture_match_ids'])),r['sha256']])
print(json.dumps(summary,indent=2))
for m in match_rows:
 print(m['load_address'],[(c['file'],c['file_byte_zero_ram_address'],c['matching_anchors'],c['byte_match_fraction']) for c in m['candidates'][:3]])
