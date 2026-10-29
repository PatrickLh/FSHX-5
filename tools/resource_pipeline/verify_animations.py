#!/usr/bin/env python3
"""Corpus checks for lossless animation row grouping and BattleScript tree coverage."""
from pathlib import Path
import json,re,math
from audit import ROOT,BASE,MAN,save
from animations import parse_ant
from battle_scripts import parse_tree,flatten

def main():
    index=json.loads((MAN/'animation_structure_index.json').read_text());catalog=json.loads((MAN/'resource_catalog.json').read_text());byid={x['id']:x for x in catalog};frame_count=0;layers=0;row_count=0
    for r in index:
        a=json.loads((ROOT/r['structured_path']).read_text());source=(ROOT/r['source_path']).read_text(encoding='cp950');parsed=parse_ant(source)
        assert a['declared_frames']==len(a['frames'])==parsed['declared_frames']
        expected_rows=[line for line in source.splitlines() if line.strip()]
        assert len(expected_rows)==2+len(a['frames'])+sum(len(f['layers']) for f in a['frames']),r['id']
        for f in a['frames']:
            if f['sound_reference']:
                assert f.get('sound_ids'),(r['id'],f['sound_reference'])
                for ident in f['sound_ids']:assert ident in byid and byid[ident]['category']=='audio'
        for old,new in zip(parsed['frames'],a['frames']):
            for key in old:
                if key!='layers':assert old[key]==new[key],(r['id'],key)
            for ol,nl in zip(old['layers'],new['layers']):
                for key in ol:assert ol[key]==nl[key],(r['id'],key)
                for ident in nl['image_ids']:assert ident in byid and byid[ident]['status']=='image_decoded'
                assert len(nl['matrix_3x3'])==9 and len(nl['translation_xyz'])==3
                assert all(math.isfinite(v) for v in nl['matrix_3x3']+nl['translation_xyz'])
        frame_count+=len(a['frames']);layers+=sum(len(f['layers']) for f in a['frames']);row_count+=len(expected_rows)
    scripts=json.loads((MAN/'battle_script_index.json').read_text());attrs=0
    for s in scripts:
        structured=json.loads((ROOT/s['structured_path']).read_text());text=(ROOT/structured['source_path']).read_text();tree,problems=parse_tree(text);nodes=flatten(tree)
        assert not problems,s['id'];assert nodes==structured['nodes']
        lines=[l.split('//',1)[0].strip() for l in text.splitlines()]
        expected=sum('=' in l and not re.fullmatch(r'\[(.+)\]',l) for l in lines)
        actual=sum(len(n['attributes']) for n in nodes)
        assert expected==actual,(s['id'],expected,actual)
        attrs+=actual
    result={'status':'passed','animations':len(index),'frames':frame_count,'layers':layers,'source_rows_accounted':row_count,'battle_scripts':len(scripts),'script_attributes_accounted':attrs,'notes':'Frame time/coordinate and engine execution semantics require separate runtime validation.'}
    save(MAN/'animation_verification.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
