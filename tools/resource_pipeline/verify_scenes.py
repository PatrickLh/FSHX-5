#!/usr/bin/env python3
"""Corpus geometry/scene invariants plus truncated binary and invalid-index regressions."""
from pathlib import Path
import json,math
from audit import ROOT,MAN,save
from model_geometry import audit_text,binary_tokens

def main():
    models=json.loads((MAN/'model_geometry_index.json').read_text());binary=0;meshes=0
    for r in models:
        assert r['status'].endswith('structure_parsed'),r['id']
        for frame in r['frame_transforms']:assert len(frame['matrix_raw_16'])==16 and all(math.isfinite(v) for v in frame['matrix_raw_16'])
        for m in r['meshes']:
            assert m['invalid_vertex_indices']==0
            if m['uv']:assert m['uv']['count_matches_vertices']
            if m['normals']:assert m['normals']['face_layout_matches_mesh'] and m['normals']['invalid_indices']==0
            if m['materials']:assert m['materials']['count_matches_faces'] and m['materials']['invalid_indices']==0
            meshes+=1
        if r['status']=='binary_structure_parsed':
            data=(ROOT/r['source_path']).read_bytes();tokens,count=binary_tokens(data);assert r['binary_bytes_consumed']==len(data) and count==r['binary_token_count'];binary+=1
            try:binary_tokens(data[:-1])
            except (ValueError,IndexError):pass
            else:raise AssertionError('truncated binary was silently accepted')
    bad='xof 0303txt 0032\nMesh { 3; 0;0;0;,1;0;0;,0;1;0;; 1;3;0,1,3;; }'
    assert audit_text(bad)['meshes'][0]['invalid_vertex_indices']==1
    scenes=json.loads((MAN/'scene_index.json').read_text());elements=json.loads((MAN/'scene_element_index.json').read_text());partial=[]
    for r in scenes+elements:
        d=json.loads((ROOT/r['structured_path']).read_text());text=(ROOT/d['source_path']).read_text()
        expected=sum('=' in l.split('//',1)[0] and not l.split('//',1)[0].strip().startswith('[') for l in text.splitlines())
        assert expected==sum(len(n['attributes']) for n in d['nodes']),r['id']
        if d['parse_issues']:partial.append(r['original_path'])
    assert partial==['SceneElement/WF5_Par_M41_ghost.se'],partial
    map4=next(r for r in scenes if r['original_path']=='Scene/map004.sce');d=json.loads((ROOT/map4['structured_path']).read_text());assert len(d['earth_slots'])==6
    assert any(e['reference']=='Effect\\VA\\WF5_180_北_頂點VA.xef' and e['exact_path_targets'] for slot in d['earth_slots'] for e in slot['references'])
    result={'status':'passed','model_versions':len(models),'mesh_blocks':meshes,'binary_models_checked':binary,'truncated_binary_rejected':True,'invalid_index_fixture_detected':True,'scenes':len(scenes),'scene_elements':len(elements),'known_unclosed_source_elements':partial,'scope':'static geometry and source row coverage; not renderer/import validation'}
    save(MAN/'scene_verification.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
