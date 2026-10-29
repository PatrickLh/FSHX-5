#!/usr/bin/env python3
"""Audit JBF directory records, reassemble chunked files, compare legacy streams.
Run: python3 tools/resource_pipeline/audit.py (standard library only).
The directory parser recognizes timestamped file entries and validates them against
all compressed extents; it does not infer filenames from stream ordering.
"""
from pathlib import Path, PurePosixPath
import hashlib, json, struct, zlib, re
from collections import Counter, defaultdict
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'original_resources';MAN=BASE/'manifests';OUT=BASE/'unpacked_verified_v1'
DATE=re.compile(rb'\x14\d{4}/\d{2}/\d{2}  \d{2}:\d{2}:\d{2}')
def sha(b):return hashlib.sha256(b).hexdigest()
def file_sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def save(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def kind(b):
 for sig,ext in [(b'BM','bmp'),(b'\xff\xd8\xff','jpg'),(b'\x89PNG\r\n\x1a\n','png'),(b'xof ','x')]:
  if b.startswith(sig):return ext
 if b'JC_Animation' in b[:64]:return 'ani'
 if b'\0' not in b:
  try:b.decode('big5');return 'txt'
  except UnicodeDecodeError:pass
 return 'bin'
def directory(b):
 entries=[]
 for m in DATE.finditer(b):
  # Pascal strings: name, timestamp, raw-size, parent-path; then a 30-byte descriptor.
  candidates=[s for s in range(max(0,m.start()-256),m.start()) if b[s]==m.start()-s-1 and all(c>=32 for c in b[s+1:m.start()])]
  for s in candidates:
   name=b[s+1:m.start()].decode('cp950');q=m.end()
   if not name or '/' in name or '\\' in name:continue
   raw=struct.unpack_from('<I',b,q)[0];q+=4;ln=b[q];q+=1
   parent=b[q:q+ln].decode('cp950');q+=ln
   chunks,comp,stored,offset=struct.unpack_from('<IIII',b,q)
   if chunks<1 or chunks>65536 or stored!=comp+8*chunks or offset+stored>s:continue
   path=PurePosixPath(parent.replace('\\','/'))/name
   if path.is_absolute() or '..' in path.parts or ':' in str(path):raise ValueError('unsafe archive path')
   entries.append({'original_path':str(path),'raw_bytes':raw,'chunks':chunks,'compressed_bytes':comp,'stored_bytes':stored,'offset':offset,'directory_entry_offset':s,'descriptor_offset':q,'timestamp':m.group()[1:].decode()})
 unique={}
 for e in entries:
  if e['offset'] in unique:
   previous=unique[e['offset']]
   for k in ['original_path','raw_bytes','chunks','compressed_bytes','stored_bytes']:
    if e[k]!=previous[k]:raise ValueError('conflicting directory copies')
   previous.setdefault('duplicate_directory_entry_offsets',[]).append(e['directory_entry_offset'])
  else:unique[e['offset']]=e
 return sorted(unique.values(),key=lambda x:x['offset'])
def main():
 MAN.mkdir(parents=True,exist_ok=True);inventory=[]
 for p in sorted((BASE/'source').rglob('*')):
  if p.is_file():inventory.append({'path':rel(p),'bytes':p.stat().st_size,'sha256':file_sha(p),'extension':p.suffix.lower()})
 save(MAN/'source_inventory.json',inventory);print('source inventory',len(inventory),flush=True)
 reports=[]
 for item in inventory:
  if item['extension']!='.jbf':continue
  p=ROOT/item['path'];b=p.read_bytes();entries=directory(b);records=[];streams=[];old=BASE/'unpacked'/p.stem
  old_files=defaultdict(list)
  for f in old.iterdir():
   if f.stem.isdigit():old_files[int(f.stem)].append(f)
  old_idx={}
  for line in (old/'_index.txt').read_text().splitlines():
   m=re.match(r'(\d+)\.\w+\toff=0x([0-9A-Fa-f]+)\tcomp=(\d+)\traw=(\d+)',line)
   if m:old_idx[int(m[1])]=tuple(int(m[i],16 if i==2 else 10) for i in [2,3,4])
  latest={}
  for e in entries:latest[e['original_path'].lower()]=e['offset']
  expected=0;metadata=[]
  for e in entries:
   if e['offset']<expected:raise ValueError('overlapping file extents')
   if e['offset']>expected:
    gap=b[expected:e['offset']]
    if not DATE.search(gap):raise ValueError(f'unidentified gap at {expected}')
    meta=MAN/'container_metadata'/f'{p.stem}_{expected:08x}.bin';meta.parent.mkdir(exist_ok=True);meta.write_bytes(gap)
    metadata.append({'offset':expected,'bytes':len(gap),'sha256':sha(gap),'path':rel(meta),'classification':'historical directory metadata; preserved verbatim, not fully structurally parsed'})
   pos=e['offset'];parts=[];first=len(streams)
   table=struct.unpack_from('<'+'I'*(e['chunks']*2),b,e['offset']+e['compressed_bytes'])
   sizes=list(table[:e['chunks']]);flags=list(table[e['chunks']:])
   if sum(sizes)!=e['compressed_bytes'] or any(x not in [0,1] for x in flags):raise ValueError('chunk table mismatch')
   for chunk_num,(size,flag) in enumerate(zip(sizes,flags)):
    start=pos;payload=b[pos:pos+size];pos+=size
    if flag==1:
     d=zlib.decompressobj();raw=d.decompress(payload)+d.flush()
     if not d.eof or d.unused_data or d.unconsumed_tail:raise ValueError('zlib boundary mismatch')
    else:raw=payload
    parts.append(raw)
    if flag==0:continue  # Historical scanner omitted uncompressed blocks entirely.
    i=len(streams);digest=sha(raw);matches=[];different=[]
    for f in old_files.get(i,[]):
     (matches if file_sha(f)==digest else different).append(rel(f))
    streams.append({'stream':i,'offset':start,'compressed_bytes':size,'raw_bytes':len(raw),'sha256':digest,'file_id':f'{p.stem}:{e["original_path"]}@{e["offset"]:08x}','chunk_in_file':chunk_num,'legacy_matches':matches,'legacy_different':different,'legacy_index_matches':old_idx.get(i)==(start,size,len(raw))})
   e['chunk_codecs']=flags
   raw=b''.join(parts)
   if len(raw)!=e['raw_bytes']:raise ValueError('raw size mismatch')
   e['historical_version']=latest[e['original_path'].lower()]!=e['offset']
   output_path=Path('__versions__')/f'{e["offset"]:08x}'/e['original_path'] if e['historical_version'] else Path(e['original_path'])
   dest=OUT/p.stem/output_path;dest.parent.mkdir(parents=True,exist_ok=True);digest=sha(raw)
   if dest.exists():
    if file_sha(dest)!=digest:raise ValueError(f'refuse overwrite changed output: {dest}')
   else:dest.write_bytes(raw)
   records.append(dict(e,id=f'{p.stem}:{e["original_path"]}@{e["offset"]:08x}',archive=item['path'],sha256=digest,type=kind(raw),path=rel(dest),first_stream=first))
   expected=pos+8*e['chunks']
  if not entries:raise ValueError('no directory entries')
  meta=MAN/'container_metadata'/f'{p.stem}.bin';meta.parent.mkdir(exist_ok=True);meta.write_bytes(b[expected:])
  metadata.append({'offset':expected,'bytes':len(b)-expected,'sha256':sha(b[expected:]),'path':rel(meta),'classification':'terminal directory metadata; preserved verbatim, not fully structurally parsed'})
  save(MAN/f'{p.stem}_files.json',records);save(MAN/f'{p.stem}_streams.json',streams)
  report={'archive':item['path'],'archive_sha256':item['sha256'],'bytes':len(b),'files':len(records),'streams':len(streams),'multi_chunk_files':sum(e['chunks']>1 for e in entries),'uncompressed_chunks':sum(e['chunk_codecs'].count(0) for e in entries),'historical_versions':sum(e['historical_version'] for e in entries),'data_end':expected,'metadata_bytes':len(b)-expected,'metadata_path':rel(meta),'metadata_sha256':sha(b[expected:]),'metadata_segments':metadata,'types':dict(Counter(r['type'] for r in records)),'legacy_files':sum(map(len,old_files.values())),'legacy_matching_files':sum(len(s['legacy_matches']) for s in streams),'legacy_different_files':sum(len(s['legacy_different']) for s in streams),'legacy_missing_streams':sum(not s['legacy_matches'] for s in streams),'legacy_index_mismatches':sum(not s['legacy_index_matches'] for s in streams),'legacy_extra_files':[rel(f) for i,fs in old_files.items() if i>=len(streams) for f in fs],'status':'verified'}
  reports.append(report);print(p.name,report['files'],'files',report['streams'],'streams','legacy mismatches',report['legacy_different_files'],flush=True)
 save(MAN/'baseline_audit.json',{'schema_version':2,'format':'directory file descriptor: chunk_count, payload_sum, stored_size, data_offset; concatenated blocks followed by block lengths and per-block codec (0=raw, 1=zlib)','directory_parsing':'timestamped file entries recovered and validated by contiguous data extents, chunk tables, raw sizes and zlib checksums; directory-only metadata preserved verbatim','archives':reports,'historical_data_retained':True,'canonical_root':rel(OUT)})
if __name__=='__main__':main()
