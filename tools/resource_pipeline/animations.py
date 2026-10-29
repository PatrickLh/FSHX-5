#!/usr/bin/env python3
"""Parse all ANT frames/layers and validate structure against source declarations."""
import json,re,struct,collections,os,html
from pathlib import Path,PurePosixPath
from audit import ROOT,BASE,MAN,save,rel
from references import animation_texture_match,normalized

def parse_ant(text):
    rows=[(i,line.rstrip('\t').split('\t')) for i,line in enumerate(text.splitlines(),1) if line.strip()]
    declared=int(rows[0][1][0]);global_fields=rows[1][1];assert len(global_fields)==4
    frames=[];p=2
    while p<len(rows):
        line,h=rows[p];p+=1;assert len(h)==9
        frame={'line':line,'duration_raw':int(h[0]),'event_fields_raw':h[1:3],'sound_reference':None if h[3]=='-1' else h[3],'layer_count':int(h[4]),'frame_vector_raw':[float(x) for x in h[5:8]],'frame_bound_raw':float(h[8]),'layers':[]}
        for _ in range(frame['layer_count']):
            ln,c=rows[p];p+=1;assert len(c)==20,(ln,len(c))
            layer={'line':ln,'texture_reference':c[0],'flag_raw':int(c[1]),'matrix_3x3':[float(x) for x in c[2:11]],'translation_xyz':[float(x) for x in c[11:14]],'render_fields_raw':[int(x) for x in c[14:19]],'color_hex':c[19]}
            frame['layers'].append(layer)
        frames.append(frame)
    assert declared==len(frames)
    return {'declared_frames':declared,'global_fields_raw':global_fields,'total_duration_raw':sum(f['duration_raw'] for f in frames),'frames':frames}

def ani_resources(b):
    """Read only the resource table's MFC class markers, Pascal paths and five u32s."""
    count=struct.unpack_from('<H',b)[0];p=2;out=[]
    def string():
        nonlocal p
        size=b[p];p+=1;s=b[p:p+size].decode('cp950');p+=size;return s
    for i in range(count):
        marker=struct.unpack_from('<H',b,p)[0];p+=2
        if marker==0xffff:
            schema,ln=struct.unpack_from('<HH',b,p);p+=4;cls=b[p:p+ln];p+=ln
            assert cls==b'JC_AnimationImageResource'
        else:assert marker==0x8001,hex(marker)
        directory=string();name=string();width,height,u0,u1,key=struct.unpack_from('<5I',b,p);p+=20
        out.append({'reference':directory+name,'width':width,'height':height,'fields_raw':[u0,u1,key],'color_key_candidate_rgb':[(key>>16)&255,(key>>8)&255,key&255]})
    return out

def main():
    catalog=json.loads((MAN/'resource_catalog.json').read_text());by_id={r['id']:r for r in catalog};lookup={}
    for r in catalog:
        if r.get('historical_version') or 'archive' not in r:continue
        lookup.setdefault((Path(r['archive']).stem,normalized(r['original_path'])),[]).append(r['id'])
    descriptions=json.loads((MAN/'animation_index.json').read_text());files=json.loads((MAN/'Ani_files.json').read_text());binary={normalized(r['original_path']):r for r in files if r['original_path'].lower().endswith('.ani')}
    pose_file=next(r for r in catalog if r['id'].startswith('GameData:other/PersonPoseList.txt@'))
    poses={int(m[2]):m[1] for m in re.finditer(r'(?m)^\s*(\w+)\s*=\s*(\d+)\s*$',(ROOT/pose_file['canonical_path']).read_text(encoding='cp950'))}
    all_animations=[];errors=[];raw_issues=[];resolved_alias=0;dimension_checks=0;binary_errors=[];audio_count=0;groups=collections.defaultdict(list)
    for r in descriptions:
        record=parse_ant((ROOT/r['path']).read_text(encoding='cp950'))
        record.update(id=r['id'],original_path=r['original_path'],source_path=r['path'],time_unit_status='raw values; milliseconds hypothesis is preview-only',matrix_status='numeric 3x3+translation retained; engine coordinate interpretation pending')
        resources=[];pair=binary.get(normalized(str(PurePosixPath(r['original_path']).with_suffix('.ani'))))
        if pair:
            try:
                resources=ani_resources((ROOT/pair['path']).read_bytes())
                record['binary_resource_table_status']='parsed'
                for resource in resources:
                    ids,evidence=animation_texture_match(resource['reference'],lookup);resource['image_ids']=ids
                    for image_id in ids:
                        image=by_id[image_id].get('image',{})
                        resource['texture_pixel_size']=[image.get('width'),image.get('height')]
                        resource['logical_to_pixel_scale']=[resource['width']/image['width'],resource['height']/image['height']]
                        dimension_checks+=1
            except (AssertionError,ValueError,IndexError,struct.error) as e:
                record['binary_resource_table_status']='unresolved';record['binary_resource_table_error']=str(e);binary_errors.append({'id':r['id'],'error':str(e)})
        else:record['binary_resource_table_status']='missing_companion'
        record['binary_resources']=resources
        resource_keys={normalized(x['reference']):x for x in resources}
        matched_rows={}
        for frame in record['frames']:
            if frame['sound_reference']:
                ref=normalized(frame['sound_reference']);audio_count+=1
                frame['sound_ids']=[x['id'] for x in catalog if x['id'].startswith('source:') and normalized(x['original_path']).endswith('/'+ref)]
            for layer in frame['layers']:
                ids,evidence=animation_texture_match(layer['texture_reference'],lookup);layer.update(image_ids=ids,match_evidence=evidence)
                meta=resource_keys.get(normalized(layer['texture_reference']),{})
                layer['color_key_candidate_rgb']=meta.get('color_key_candidate_rgb')
                layer['logical_size']=[meta['width'],meta['height']] if meta else None
                matched_rows[layer['line']]=(ids,evidence)
                if evidence.startswith('exact_path_after'):resolved_alias+=1
                if not ids:raw_issues.append({'id':r['id'],'kind':'animation_resource_reference','reference':layer['texture_reference'],'line':layer['line']})
        for row in r['resource_rows']:
            row['matched_ids'],row['match_evidence']=matched_rows[row['line']]
        r['sound_events']=[{'frame':i,'reference':f['sound_reference'],'matched_ids':f.get('sound_ids',[])} for i,f in enumerate(record['frames']) if f['sound_reference']]
        r['parameter_status']='frame and layer structure parsed; numeric matrix/translation retained; engine timing unit and coordinate semantics pending'
        p=PurePosixPath(r['original_path']);record['pose']=None
        if len(p.parts)>=3 and p.parts[0].lower()=='man':
            group=p.parts[1];m=re.fullmatch(r'(\d{2})([a-z]+)',p.stem,re.I)
            record['actor_animation_group']=group
            if m:record['pose']={'code':int(m[1]),'name':poses.get(int(m[1])),'variant_suffix':m[2],'direction_status':'suffix retained; compass direction unverified'}
            groups[group].append({'animation_id':r['id'],'original_path':r['original_path'],'frames':len(record['frames']),'pose':record['pose']})
        dest=BASE/'organized'/'animation_data'/p.with_name(p.name+'.json');save(dest,record);record['structured_path']=rel(dest)
        all_animations.append(record)
    save(MAN/'animation_index.json',descriptions)
    compact=[{k:v for k,v in r.items() if k not in ['frames','binary_resources']} for r in all_animations]
    save(MAN/'animation_structure_index.json',compact);save(MAN/'actor_action_groups.json',{'pose_source':pose_file['id'],'pose_codes':poses,'warning':'Folder groups are exact animation paths; no character-name binding inferred.','groups':dict(groups)})
    unresolved=json.loads((MAN/'unresolved.json').read_text());unresolved=[x for x in unresolved if x['kind'] not in ['animation_resource_reference','binary_animation_table']]+raw_issues+[dict(kind='binary_animation_table',**e) for e in binary_errors];save(MAN/'unresolved.json',unresolved)
    summary={'animations':len(all_animations),'frames':sum(len(r['frames']) for r in all_animations),'layers':sum(len(f['layers']) for r in all_animations for f in r['frames']),'structure_errors':len(errors),'authoring_root_alias_rows':resolved_alias,'unmatched_layer_rows':len(raw_issues),'unmatched_unique_references':len(set(x['reference'].lower() for x in raw_issues)),'binary_table_errors':len(binary_errors),'binary_dimension_checks':dimension_checks,'frames_with_sound_events':audio_count,'sound_events_with_matches':sum(bool(f.get('sound_ids')) for a in all_animations for f in a['frames'] if f['sound_reference']),'actor_animation_groups':len(groups),'pose_codes':len(poses)}
    save(MAN/'animation_structure_summary.json',summary)
    make_viewer(all_animations,by_id)
    print(json.dumps(summary,ensure_ascii=False))

def make_viewer(animations,catalog):
    viewer=BASE/'organized'/'animation_viewer.html';chosen=[]
    wanted=['man/0001/00a.ant','man/0001/01a.ant','man/0001/17a.ant','man/0001/30a.ant','face/sf0001.ant','sp/sk_0101.ant','sp/sk_0631.ant','sp/sk_1021.ant']
    for name in wanted:
        chosen += [a for a in animations if a['original_path'].lower()==name]
    for group in ['0002','0003','0004','0010','0043']:
        chosen += [a for a in animations if a['original_path'].lower() in [f'man/{group}/00a.ant',f'man/{group}/17a.ant']]
    chosen += [a for a in animations if a['original_path'].lower().startswith('sp/sk_') and 3<len(a['frames'])<50][:10]
    chosen=list({a['id']:a for a in chosen}.values());image_ids={x for a in chosen for f in a['frames'] for l in f['layers'] for x in l['image_ids']}
    images={i:{'url':os.path.relpath(ROOT/catalog[i]['outputs'][0],viewer.parent),'width':catalog[i]['image']['width'],'height':catalog[i]['image']['height']} for i in image_ids}
    data={'animations':chosen,'images':images}
    report=ROOT/'docs'/'animation-analysis.md'
    if report.exists():(viewer.parent/'animation-analysis.md').write_text(report.read_text())
    template=(Path(__file__).parent/'animation_viewer.html').read_text();viewer.write_text(template.replace('__DATA_JSON__',json.dumps(data,ensure_ascii=False).replace('</','<\\/')),encoding='utf-8')
if __name__=='__main__':main()
