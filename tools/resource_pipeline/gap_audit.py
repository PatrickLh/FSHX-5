#!/usr/bin/env python3
"""Classify unresolved evidence; inspect wrap structure without guessing identities."""
from pathlib import Path,PurePosixPath
from collections import Counter,defaultdict
import json,struct,math
from audit import ROOT,BASE,MAN,save,rel,file_sha
from index_resources import norm

def entropy(b):
    n=len(b);return -sum((v/n)*math.log2(v/n) for v in Counter(b).values()) if n else 0

def main():
    catalog=json.loads((MAN/'resource_catalog.json').read_text());lookup=defaultdict(list);stemlookup=defaultdict(list)
    for r in catalog:
        if not r.get('historical_version'):
            lookup[PurePosixPath(norm(r['original_path'])).name].append(r)
            stemlookup[str(PurePosixPath(norm(r['original_path'])).with_suffix(''))].append(r)
    deps=json.loads((MAN/'config_dependencies.json').read_text());directly_referenced={t for e in deps for t in e['exact_path_targets']}
    issues=json.loads((MAN/'unresolved.json').read_text());diagnostics=[]
    for issue in issues:
        if 'reference' not in issue:continue
        ref=issue['reference'];candidates=lookup.get(PurePosixPath(norm(ref)).name,[])
        extension_candidates=[r for r in stemlookup.get(str(PurePosixPath(norm(ref)).with_suffix('')),[]) if PurePosixPath(norm(r['original_path'])).suffix!=PurePosixPath(norm(ref)).suffix]
        if issue['kind']=='animation_resource_reference':candidates=[c for c in candidates if 'archive' in c and Path(c['archive']).stem=='AniTexture']
        diagnostics.append(dict(issue,basename_candidates=[{'id':c['id'],'original_path':c['original_path'],'sha256':c['sha256']} for c in candidates],same_path_stem_different_extension_candidates=[{'id':r['id'],'original_path':r['original_path'],'sha256':r['sha256']} for r in extension_candidates],classification='same_basename_at_other_path' if candidates else 'same_path_stem_different_extension' if extension_candidates else 'no_current_file_with_same_basename',source_animation_directly_referenced_by_config=(issue.get('id') in directly_referenced) if issue['kind']=='animation_resource_reference' else None,candidate_status='diagnostic only; not substituted into resolved references'))
    save(MAN/'gap_diagnostics.json',diagnostics)
    wraps=[]
    for p in sorted((BASE/'source').rglob('*.wrap')):
        b=p.read_bytes();assert b[:8]==b'WFAPe\0\0\0';header=struct.unpack_from('<8I',b,8);count,table_offset=header[6:8]
        assert len(b)-table_offset==count*268,(p,len(b),count,table_offset)
        wraps.append({'path':rel(p),'sha256':file_sha(p),'bytes':len(b),'header_bytes':40,'header_u32_at_8':list(header),'entry_count_candidate':count,'table_offset_candidate':table_offset,'tail_bytes':len(b)-table_offset,'candidate_entry_bytes':268,'size_relation_verified':True,'payload_entropy_bits':entropy(b[40:table_offset]),'table_entropy_bits':entropy(b[table_offset:]),'decoding_status':'undecoded; size relation proves boundaries, not filenames or plaintext object fields'})
    save(MAN/'wrap_structure_inventory.json',wraps)
    summary={'reference_issues':len(diagnostics),'reference_issue_kinds':dict(Counter(d['kind'] for d in diagnostics)),'no_basename_candidates':sum(not d['basename_candidates'] for d in diagnostics),'candidate_rows_only':sum(bool(d['basename_candidates']) for d in diagnostics),'extension_candidate_rows':sum(bool(d['same_path_stem_different_extension_candidates']) for d in diagnostics),'wrap_files':len(wraps),'wrap_size_relations_verified':sum(w['size_relation_verified'] for w in wraps)}
    save(MAN/'gap_audit_summary.json',summary);print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
