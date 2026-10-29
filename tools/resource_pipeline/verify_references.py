#!/usr/bin/env python3
"""Regression checks using real Unicode scene, particle and shader source files."""
from pathlib import Path
import json
from audit import ROOT,MAN,save
from config_refs import assignment_references
from script_graphs import graph

def main():
    catalog=json.loads((MAN/'resource_catalog.json').read_text());byid={r['id']:r for r in catalog};configs=json.loads((MAN/'game_config_index.json').read_text());configby={r['id']:r for r in configs};edges=json.loads((MAN/'config_dependencies.json').read_text())
    expected=0
    for c in configs:
        expected+=len(assignment_references((ROOT/c['path']).read_text(),c['original_path']))
    assert expected==len(edges)
    for e in edges:
        c=configby[e['from']];line=(ROOT/c['path']).read_text().splitlines()[e['line']-1].split('//',1)[0]
        assert e['reference'] in line.split('=',1)[1]
        for ident in e['exact_path_targets']:assert ident in byid and not byid[ident].get('historical_version')
    unicode_path='Effect\\VA\\WF5_180_北_頂點VA.xef'
    assert any(e['reference']==unicode_path and e['exact_path_targets'] for e in edges)
    assert not any(configby[e['from']]['original_path'].lower().endswith('.vsh') for e in edges)
    particle=[e for e in edges if e['reference'].lower().endswith('.par')]
    for name in ['Particle\\music_01.par','Particle\\hit_z07.par']:
        assert any(e['reference']==name and e['exact_path_targets'] and configby[e['from']]['original_path']=='BattleScript/common0065.txt' for e in particle)
    assert not any(e['reference']=='va.xef' for e in edges)
    bundle=json.loads((ROOT/'original_resources/organized/effects/samples/attack00/bundle.json').read_text());clip=bundle['animations']['active_attack'];event=bundle['event1_candidate']
    assert event['fields_raw'][0]=='1' and event['offset_raw']==sum(f['duration_raw'] for f in clip['frames'][:event['frame']])
    assert not bundle['engine_verified'] and len(bundle['manual_branches'])==2
    for n in bundle['evidence_nodes']:assert n['attributes'] and n['source_line']>0
    # Attack00 must retain ambiguous Hit routing rather than silently selecting one handler.
    assert any(r['target_raw']=='[ActivePerson]' and r['action_raw']=='[Hit]' and r['route_status']=='external_branch_selection_required' for r in bundle['control_graph']['message_routes'])
    for clip_name,layout_name in [('active_attack','active'),('target_hurt','target'),('hit_effect','effect')]:
        layout=bundle['preview_layout'][layout_name]
        for frame in bundle['animations'][clip_name]['frames']:
            for layer in frame['layers']:
                size=layer['logical_size'] or [bundle['images'][layer['image_ids'][0]][k] for k in ['width','height']]
                w,h=size;m=layer['matrix_3x3'];tx,ty,_=layer['translation_xyz']
                for u in [-w/2,w/2]:
                    for v in [-h/2,h/2]:
                        x=layout['x']+layout['scale']*(m[0]*u+m[3]*v+tx)
                        y=layout['y']-layout['scale']*(m[1]*u+m[4]*v+ty)
                        assert 0<=x<=1000 and 0<=y<=580,(clip_name,x,y)
    for section in ['images','sounds']:
        for ident in bundle[section]:assert ident in byid
    material_rows=json.loads((MAN/'texture_list_index.json').read_text())
    materials={r['original_path'].lower():json.loads((ROOT/r['structured_path']).read_text()) for r in material_rows}
    for rows in [material_rows,json.loads((MAN/'particle_index.json').read_text())]:
        for row in rows:
            record=json.loads((ROOT/row['structured_path']).read_text());assert not record['parse_issues']
            text=(ROOT/record['source_path']).read_text(encoding='cp950')
            expected_attrs=sum('=' in line.split('//',1)[0] and not line.split('//',1)[0].strip().startswith('[') for line in text.splitlines())
            assert expected_attrs==sum(len(n['attributes']) for n in record['nodes'])
    music=materials['particle/music_01.tl'];assert len(music['references'])==5 and all(e['exact_path_targets'] for e in music['references'])
    bobo=materials['particle/bobo.tl'];assert [e['reference'].replace('\\','/') for e in bobo['references']]==['particle//bobo01.bmp','particle//bobo02.bmp','particle//bobo03.bmp','particle//bobo04.bmp']
    assert all(e['exact_path_targets'] for e in bobo['references'])
    sea=materials['sea/sea.tl'];assert len(sea['references'])==31
    assert all(not b['active_candidate'] for b in sea['batch_fallback'])
    assert sum(a['key']=='tex00' for n in sea['nodes'] for a in n['attributes'])==31
    common=json.loads((ROOT/'original_resources/organized/effects/script_data/BattleScript/common0065.json').read_text())
    assert any(byid[i]['original_path'].lower()=='particle/music_p01.bmp' for i in common['reachable_resource_ids'])
    wraps=json.loads((MAN/'wrap_structure_inventory.json').read_text())
    for w in wraps:assert w['bytes']-w['table_offset_candidate']==w['entry_count_candidate']*268
    result={'status':'passed','config_reference_rows':len(edges),'unicode_reference_regression':'passed','shader_swizzle_exclusion':'passed','particle_reference_rows':len(particle),'attack_event_offset_raw':event['offset_raw'],'attack_event_frame_zero_based':event['frame'],'manual_branch_gates_retained':True,'wrap_structures_checked':len(wraps),'texture_lists_verified':len(material_rows),'texture_batch_and_duplicate_keys':'passed'}
    save(MAN/'reference_verification.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
