#!/usr/bin/env python3
"""Check source integrity, all reconstructed hashes, output paths and archive coverage."""
from pathlib import Path
import json,hashlib,subprocess
from audit import ROOT,BASE,MAN,save,file_sha

def main():
 counts={};inventory=json.loads((MAN/'source_inventory.json').read_text())
 for r in inventory:
  p=ROOT/r['path'];assert p.stat().st_size==r['bytes'] and file_sha(p)==r['sha256'],r['path']
 counts['source_files_verified']=len(inventory)
 a=json.loads((MAN/'baseline_audit.json').read_text());all_records=[]
 for archive in a['archives']:
  records=json.loads((MAN/(Path(archive['archive']).stem+'_files.json')).read_text());all_records+=records
  intervals=[(r['offset'],r['stored_bytes']) for r in records]+[(r['offset'],r['bytes']) for r in archive['metadata_segments']]
  end=0
  for off,size in sorted(intervals):assert off==end,(archive['archive'],end,off);end=off+size
  assert end==archive['bytes']
  for r in records:
   p=ROOT/r['path'];assert p.stat().st_size==r['raw_bytes'] and file_sha(p)==r['sha256'],r['path']
  for r in archive['metadata_segments']:assert file_sha(ROOT/r['path'])==r['sha256']
 assert len({r['id'] for r in all_records})==len(all_records)
 assert len({r['path'].lower() for r in all_records})==len(all_records)
 counts['reconstructed_files_verified']=len(all_records)
 catalog=json.loads((MAN/'resource_catalog.json').read_text());output_paths=[]
 for r in catalog:
  for output in r['outputs']:
   assert (ROOT/output).is_file(),output;output_paths.append(output)
 assert len(output_paths)==len(set(output_paths)), 'duplicate output paths'
 counts['organized_outputs_exist']=len(output_paths)
 # Verify all tracked story files retain their Git content at the migrated location.
 raw=subprocess.check_output(['git','ls-tree','-rz','HEAD','story','original_resources/organized/story'],cwd=ROOT);checked=0
 for entry in raw.split(b'\0'):
  if not entry:continue
  meta,name=entry.split(b'\t',1);oid=meta.split()[2].decode();name=name.decode()
  target=ROOT/name if name.startswith('original_resources/') else BASE/'organized'/name;b=target.read_bytes();actual=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
  assert actual==oid,name;checked+=1
 assert checked>0,'no tracked story files checked'
 counts['tracked_story_files_unchanged']=checked
 counts['status']='passed';save(MAN/'verification.json',counts);print(json.dumps(counts,ensure_ascii=False))
if __name__=='__main__':main()
