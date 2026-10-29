#!/usr/bin/env python3
"""Scene/environment dependency dossiers; retain original coordinate and render fields."""
from pathlib import Path,PurePosixPath
from collections import defaultdict,Counter
import json
from audit import ROOT,BASE,MAN,save,rel
from battle_scripts import parse_tree,flatten

def main():
    catalog=json.loads((MAN/'resource_catalog.json').read_text());byid={r['id']:r for r in catalog};configs=json.loads((MAN/'game_config_index.json').read_text());geometry={r['id']:r for r in json.loads((MAN/'model_geometry_index.json').read_text())}
    deps=json.loads((MAN/'config_dependencies.json').read_text())+json.loads((MAN/'material_dependencies.json').read_text());edgeby=defaultdict(list)
    for e in deps:edgeby[e['from']].append(e)
    for a in json.loads((MAN/'animation_index.json').read_text()):
        for r in a['resource_rows']:edgeby[a['id']].append({'reference':r['resource'],'line':r['line'],'exact_path_targets':r['matched_ids']})
    for m in json.loads((MAN/'model_index.json').read_text()):
        for t in m.get('texture_resolution',[]):edgeby[m['id']].append({'reference':t['reference'],'exact_path_targets':t['exact_path_candidates']})
    def closure(start):
        seen=set();todo=[start];unresolved=[]
        while todo:
            key=todo.pop()
            if key in seen:continue
            seen.add(key)
            for e in edgeby[key]:
                todo+=e['exact_path_targets']
                if not e['exact_path_targets']:unresolved.append({'from':key,**e})
        return sorted(seen),unresolved
    scenes=[];elements=[];backgrounds=[];issues=[];scene_reachability={}
    for r in configs:
        ext=PurePosixPath(r['original_path']).suffix.lower()
        if ext not in ['.sce','.se']:continue
        tree,errors=parse_tree((ROOT/r['path']).read_text());nodes=flatten(tree);reachable,missing=closure(r['id'])
        slots=[]
        for n in nodes:
            if n['section']=='Earth':
                for a in n['attributes']:
                    refs=[e for e in edgeby[r['id']] if e.get('line')==a['line']]
                    slots.append({'slot':a['key'],'value_raw':a['value'],'line':a['line'],'references':refs})
            fields={a['key']:a['value'] for a in n['attributes']}
            if fields.get('Type','').lower()=='background':
                backgrounds.append({'config_id':r['id'],'original_path':r['original_path'],'node_path':n['section_path'],'source_line':n['source_line'],'declared_type':fields['Type'],'attributes':n['attributes'],'image_references':[e for e in edgeby[r['id']] if e.get('attribute') in ['TextureName','Texture']]})
        model_ids=[i for i in reachable if i in geometry]
        record={'id':r['id'],'original_path':r['original_path'],'source_path':r['path'],'nodes':nodes,'earth_slots':slots,'reachable_resource_ids':reachable,'model_ids':model_ids,'unresolved_dependencies':missing,'parse_issues':errors,'coordinate_policy':'retain raw model-local/frame/scene matrices separately; units, handedness and combined transforms require validation'}
        out=BASE/'organized'/'scenes'/PurePosixPath(r['original_path']).with_name(PurePosixPath(r['original_path']).name+'.json');save(out,record)
        summary={'id':r['id'],'original_path':r['original_path'],'structured_path':rel(out),'nodes':len(nodes),'attribute_rows':sum(len(n['attributes']) for n in nodes),'earth_slots':len(slots),'models':len(model_ids),'reachable_resources':len(reachable),'missing_reference_rows':len(missing),'parse_issue_count':len(errors)}
        (scenes if ext=='.sce' else elements).append(summary)
        if ext=='.sce':scene_reachability[r['id']]=set(reachable)
        if errors:issues.append({'id':r['id'],'issues':errors})
    save(MAN/'scene_index.json',scenes);save(MAN/'scene_element_index.json',elements);save(MAN/'declared_background_index.json',backgrounds);save(MAN/'scene_parse_issues.json',issues)
    summary={'scenes':len(scenes),'scene_element_files':len(elements),'scene_earth_slots':sum(s['earth_slots'] for s in scenes),'declared_background_nodes':len(backgrounds),'parse_issue_files':len(issues),'scene_attribute_rows':sum(s['attribute_rows'] for s in scenes),'element_attribute_rows':sum(s['attribute_rows'] for s in elements)}
    save(MAN/'scene_summary.json',summary)
    unresolved=json.loads((MAN/'unresolved.json').read_text());unresolved=[r for r in unresolved if r['kind']!='scene_structure']
    unresolved += [dict(kind='scene_structure',**r) for r in issues];save(MAN/'unresolved.json',unresolved)
    texture_lists=json.loads((MAN/'texture_list_index.json').read_text());usage=[]
    for tl in texture_lists:
        scene_ids=[]
        for row in scenes:
            if tl['id'] in scene_reachability[row['id']]:scene_ids.append(row['id'])
        usage.append({'texture_list_id':tl['id'],'original_path':tl['original_path'],'scene_ids':scene_ids,'evidence':'static explicit dependency closure only; dynamically constructed runtime paths are not covered'})
    save(MAN/'scene_texture_list_usage.json',usage)
    print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
