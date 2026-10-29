#!/usr/bin/env python3
"""Parse particle settings and texture-list dependencies, retaining duplicate list keys."""
from pathlib import Path,PurePosixPath
from collections import defaultdict,Counter
import json,re
from audit import ROOT,BASE,MAN,save,rel
from index_resources import norm
from battle_scripts import parse_tree,flatten
from config_refs import assignment_references

def main():
    catalog=json.loads((MAN/'resource_catalog.json').read_text());lookup=defaultdict(list)
    for r in catalog:
        if 'archive' in r and not r.get('historical_version'):lookup[(Path(r['archive']).stem,norm(r['original_path']))].append(r['id'])
    dependencies=[];materials=[];particles=[];errors=[]
    for r in catalog:
        if 'archive' not in r or r.get('historical_version'):continue
        ext=PurePosixPath(r['original_path']).suffix.lower()
        if ext not in ['.tl','.par']:continue
        text=(ROOT/r['canonical_path']).read_text(encoding='cp950');tree,problems=parse_tree(text);nodes=flatten(tree);references=[];batch=[]
        for n in nodes:
            for a in n['attributes']:
                if a['key']=='TextureBatch':
                    match=re.fullmatch(r'(.+\(\*\)\.\w+)\s*,?\s*(\d+)\s*~\s*(\d+)\s*,?\s*(\d+)',a['value'])
                    batch.append(dict(a,expanded_candidates=[match[1].replace('(*)',str(i).zfill(int(match[4]))) for i in range(int(match[2]),int(match[3])+1)] if match else [],status='declared fallback; not mixed with explicit List rows'))
        for rr in assignment_references(text,r['original_path']):
            ref=rr['reference'];found=[];archives=['Texture','XFile'] if ref.lower().endswith('.tl') else ['Texture','XFile','AniTexture']
            for archive in archives:
                for key in [norm(ref),norm(str(PurePosixPath(r['original_path']).parent/ref.replace('\\','/')))]:found+=lookup.get((archive,key),[])
            edge={'from':r['id'],'line':rr['line'],'attribute':rr['attribute'],'reference':ref,'exact_path_targets':sorted(set(found)),'status':'resolved' if found else 'unresolved','origin':'particle_or_texture_list'}
            references.append(edge)
            if ext=='.tl':dependencies.append(edge) # .par refs already belong to the GameData config index.
        has_list=any(n['section'] in ['List','TextureList'] and n['attributes'] for n in nodes)
        for declaration in batch:
            declaration['active_candidate']=not has_list
            if not has_list:
                if not declaration['expanded_candidates']:problems.append({'line':declaration['line'],'error':'unparsed TextureBatch declaration'})
                for ref in declaration['expanded_candidates']:
                    found=[]
                    for archive in ['Texture','XFile','AniTexture']:
                        for key in [norm(ref),norm(str(PurePosixPath(r['original_path']).parent/ref.replace('\\','/')))]:found+=lookup.get((archive,key),[])
                    edge={'from':r['id'],'line':declaration['line'],'attribute':'TextureBatch','reference':ref,'exact_path_targets':sorted(set(found)),'status':'resolved' if found else 'unresolved','origin':'texture_batch_range_expansion','batch_source_raw':declaration['value']}
                    references.append(edge);dependencies.append(edge)
        record={'id':r['id'],'original_path':r['original_path'],'source_path':r['canonical_path'],'nodes':nodes,'parse_issues':problems,'references':references,'batch_fallback':batch,'frame_time_fields':[a for n in nodes for a in n['attributes'] if a['key']=='fFrameTime'],'list_order_policy':'explicit List attributes preserved as ordered rows; duplicate tex00 keys are not collapsed','runtime_status':'parameters retained; emission random distribution and engine texture-selection rules unverified'}
        out=BASE/'organized'/'effects'/'material_data'/Path(r['archive']).stem/PurePosixPath(r['original_path']).with_name(PurePosixPath(r['original_path']).name+'.json');save(out,record)
        summary={'id':r['id'],'original_path':r['original_path'],'structured_path':rel(out),'reference_rows':len(references),'unmatched_rows':sum(not x['exact_path_targets'] for x in references),'attribute_rows':sum(len(n['attributes']) for n in nodes),'parse_issue_count':len(problems)}
        (materials if ext=='.tl' else particles).append(summary)
        if problems:errors.append({'id':r['id'],'issues':problems})
    save(MAN/'texture_list_index.json',materials);save(MAN/'particle_index.json',particles);save(MAN/'material_dependencies.json',dependencies);save(MAN/'material_parse_issues.json',errors)
    unresolved=json.loads((MAN/'unresolved.json').read_text());unresolved=[r for r in unresolved if r['kind'] not in ['material_reference','material_parse']]
    unresolved += [dict(kind='material_reference',**e) for e in dependencies if not e['exact_path_targets']]
    unresolved += [dict(kind='material_parse',**e) for e in errors];save(MAN/'unresolved.json',unresolved)
    summary={'texture_lists':len(materials),'particle_files':len(particles),'texture_list_reference_rows':len(dependencies),'unmatched_texture_list_rows':sum(not e['exact_path_targets'] for e in dependencies),'parse_issue_files':len(errors),'particle_attribute_rows':sum(r['attribute_rows'] for r in particles)}
    save(MAN/'material_summary.json',summary);print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
