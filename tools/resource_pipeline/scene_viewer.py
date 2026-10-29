#!/usr/bin/env python3
"""Local audit browser with source links, geometry summaries and material thumbnails."""
from pathlib import Path
import json,os
from audit import ROOT,BASE,MAN

def main():
    scenes=json.loads((MAN/'scene_index.json').read_text());geom={r['id']:r for r in json.loads((MAN/'model_geometry_index.json').read_text())};catalog={r['id']:r for r in json.loads((MAN/'resource_catalog.json').read_text())};page=BASE/'organized'/'scene_audit.html';data=[]
    for row in scenes:
        scene=json.loads((ROOT/row['structured_path']).read_text());models=[];images=[]
        for ident in scene['model_ids']:
            g=geom[ident];models.append({'id':ident,'original_path':g['original_path'],'source_url':os.path.relpath(ROOT/g['source_path'],page.parent),'status':g['status'],'mesh_count':len(g.get('meshes',[])),'vertices':sum(m['vertices'] for m in g.get('meshes',[])),'faces':sum(m['faces'] for m in g.get('meshes',[])),'skin_weight_blocks':g.get('skin_weight_blocks',0),'animation_sets':g.get('animation_sets',0),'meshes':g.get('meshes',[])})
        for ident in scene['reachable_resource_ids']:
            r=catalog[ident]
            if r['status']=='image_decoded':images.append({'id':ident,'path':r['original_path'],'url':os.path.relpath(ROOT/r['outputs'][0],page.parent),'width':r['image']['width'],'height':r['image']['height']})
        data.append({'path':row['original_path'],'source_url':os.path.relpath(ROOT/scene['source_path'],page.parent),'slots':scene['earth_slots'],'models':models,'images':images,'missing':scene['unresolved_dependencies'],'lighting':[n for n in scene['nodes'] if n['section']=='LightMan' or n['section'].startswith('LightBulb')]})
    template=(Path(__file__).parent/'scene_audit.html').read_text();page.write_text(template.replace('__SCENE_DATA__',json.dumps(data,ensure_ascii=False).replace('</','<\\/')))
    print('Scene audit viewer:',len(data),'scenes')
if __name__=='__main__':main()
