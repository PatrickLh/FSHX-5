#!/usr/bin/env python3
"""Compile a source-backed attack00 experiment. Role choices are demonstration bindings."""
from pathlib import Path
import json,os
from audit import ROOT,BASE,MAN,save,rel
from script_graphs import graph

def main():
    index=json.loads((MAN/'animation_structure_index.json').read_text());animation_by_path={r['original_path'].lower():r for r in index}
    catalog=json.loads((MAN/'resource_catalog.json').read_text());byid={r['id']:r for r in catalog}
    scripts=json.loads((MAN/'battle_script_index.json').read_text());scriptrow=next(r for r in scripts if r['original_path'].lower()=='battlescript/attack00.txt');script=json.loads((ROOT/scriptrow['structured_path']).read_text());g=graph(script);nodes=script['nodes']
    def attrs(n):return {a['key']:a['value'] for a in n['attributes']}
    def find(pred):return next(n for n in nodes if pred(n,attrs(n)))
    attack=find(lambda n,a:n['section_path'].startswith('/ActivePerson/ActionList/Init/') and a.get('Type')=='SetPose' and a.get('Pose')=='Attack')
    signal=find(lambda n,a:n['parent_id']==attack['node_id'] and a.get('dwConditionOfStart')=='1')
    send1=find(lambda n,a:n['parent_id']==signal['node_id'] and a.get('Type')=='SendMessage')
    send2=find(lambda n,a:n['section_path'].startswith('/ActivePerson/ActionList_Hit/Hit/') and a.get('Type')=='SendMessage')
    hit_show=find(lambda n,a:n['section_path'].startswith('/PassivePerson/ActionList_Hit/Hit/') and a.get('Type')=='SetShow' and a.get('Object')=='Hit000')
    result_message=find(lambda n,a:n['section_path'].startswith('/PassivePerson/ActionList_Hit/Hit/') and a.get('Type')=='SendMessage' and a.get('Action')=='[Result]')
    hurt=find(lambda n,a:'/PassivePerson/ActionList/Result/ResultLive/' in n['section_path'] and a.get('Type')=='SetPose')
    hit_resource=find(lambda n,a:n['section_path'].startswith('/PassivePerson/Resource/') and a.get('Name')=='Hit000')
    assert attrs(hit_resource)['AniName'].replace('\\','/').lower()=='sp/hit000.ant'
    specs={'active_idle':'man/0001/00a.ant','active_attack':'man/0001/17a.ant','target_idle':'man/0002/00a.ant','target_hurt':'man/0002/04a.ant','hit_effect':'sp/hit000.ant'}
    animations={};images={};sounds={};page=BASE/'organized'/'attack_sample.html'
    for key,path in specs.items():
        a=json.loads((ROOT/animation_by_path[path]['structured_path']).read_text());animations[key]=a
        for frame in a['frames']:
            for layer in frame['layers']:
                assert layer['image_ids'],(path,layer['texture_reference'])
                for ident in layer['image_ids']:
                    r=byid[ident];images[ident]={'url':os.path.relpath(ROOT/r['outputs'][0],page.parent),'width':r['image']['width'],'height':r['image']['height'],'sha256':r['sha256']}
            for ident in frame.get('sound_ids',[]):
                r=byid[ident];sounds[ident]={'url':os.path.relpath(ROOT/r['outputs'][0],page.parent),'sha256':r['sha256']}
    offsets=[];t=0
    for i,f in enumerate(animations['active_attack']['frames']):
        if f['event_fields_raw']!=['0','0']:offsets.append({'frame':i,'offset_raw':t,'fields_raw':f['event_fields_raw']})
        t+=f['duration_raw']
    event1=next(e for e in offsets if e['fields_raw'][0]=='1')
    assert event1['offset_raw']==sum(f['duration_raw'] for f in animations['active_attack']['frames'][:event1['frame']])
    data={'source_script_id':script['id'],'source_script_path':script['source_path'],'control_graph':g,'evidence_nodes':[attack,signal,send1,send2,hit_show,result_message,hurt], 'preview_layout':{'active':{'x':380,'y':475,'scale':2.1},'target':{'x':760,'y':475,'scale':2.1},'effect':{'x':760,'y':340,'scale':1.5}},'animations':animations,'images':images,'sounds':sounds,'attack_markers':offsets,'event1_candidate':event1,'engine_verified':False,'demo_role_bindings':{'ActivePerson':'MAN animation group 0001; character identity unconfirmed','PassivePerson':'MAN animation group 0002; character identity unconfirmed'},'manual_branches':['ActionList_Hit selected instead of ActionList_Dodge','ResultLive selected instead of death-result branches'],'preview_policies':['1000 raw time units per second by default; adjustable','marker field 1 tested as event 1 hypothesis, paused for manual confirmation','XY plane, fixed actor placement, source XYZ expressions not executed','completed attack and hurt clips hold final frame; effect hidden after its last frame','original projection, particle and engine-specific blending are not executed']}
    bundle=BASE/'organized'/'effects'/'samples'/'attack00'/'bundle.json';save(bundle,data)
    template=(Path(__file__).parent/'attack_sample.html').read_text();page.write_text(template.replace('__SAMPLE_JSON__',json.dumps(data,ensure_ascii=False).replace('</','<\\/')))
    summary={'source_script_id':script['id'],'bundle_path':rel(bundle),'viewer_path':rel(page),'animation_clips':len(animations),'unique_images':len(images),'unique_sounds':len(sounds),'event1_candidate_frame_zero_based':event1['frame'],'event1_candidate_offset_raw':event1['offset_raw'],'source_evidence_nodes':len(data['evidence_nodes']),'engine_verified':False}
    save(MAN/'attack_sample_manifest.json',summary);print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
