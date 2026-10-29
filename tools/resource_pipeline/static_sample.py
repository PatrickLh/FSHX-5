#!/usr/bin/env python3
"""Derived local-coordinate diagnostic meshes; never a reconstructed game scene."""
import json,re,hashlib
from pathlib import Path
from model_geometry import TOKEN,parse_blocks,Cursor
from audit import ROOT,MAN,save

def extract(data):
    text=data.decode('cp950');text=re.sub(r'/\*.*?\*/','',text,flags=re.S);text=re.sub(r'//[^\r\n]*','',text)
    tokens=TOKEN.findall(text[16:]);blocks=parse_blocks(tokens);meshes=[]
    for i,b in enumerate(blocks):
        if b['template'] or b['kind']!='Mesh':continue
        c=Cursor(tokens,b['start'],b['end']);vertices=[c.vector(3) for _ in range(c.number(True))];faces=[]
        for _ in range(c.number(True)):faces.append([c.number(True) for _ in range(c.number(True))])
        assert all(len(f)>=3 and all(v<len(vertices) for v in f) for f in faces)
        uv=[]
        for child in blocks:
            if child['parent']==i and child['kind']=='MeshTextureCoords':
                cc=Cursor(tokens,child['start'],child['end']);uv=[cc.vector(2) for _ in range(cc.number(True))];assert len(uv)==len(vertices)
        meshes.append({'name':b['name'],'vertices':vertices,'faces':faces,'uv':uv})
    return meshes

def main():
    scene=json.loads((ROOT/'original_resources/organized/scenes/Scene/map004.sce.json').read_text());catalog={r['id']:r for r in json.loads((MAN/'resource_catalog.json').read_text())};models={r['id']:r for r in json.loads((MAN/'model_index.json').read_text())};out=ROOT/'godot/assets/static_sample';out.mkdir(parents=True,exist_ok=True);rows=[]
    for slot in scene['earth_slots']:
        ids=slot['references'][0]['exact_path_targets'];assert len(ids)==1
        rid=ids[0];r=models[rid];data=(ROOT/r['path']).read_bytes();digest=hashlib.sha256(data).hexdigest();assert digest==catalog[rid]['sha256']
        meshes=extract(data);name=Path(r['original_path']).stem;lines=['# Diagnostic local coordinates; no frame/scene transforms or source materials.'];offset=0;uvoffset=0
        for i,m in enumerate(meshes):
            lines.append(f'o mesh_{i}')
            lines += ['v '+' '.join(format(v,'.17g') for v in p) for p in m['vertices']]
            lines += ['vt '+' '.join(format(v,'.17g') for v in p) for p in m['uv']]
            for f in m['faces']:lines.append('f '+' '.join(f'{v+1+offset}/{v+1+uvoffset}' if m['uv'] else str(v+1+offset) for v in f))
            offset+=len(m['vertices']);uvoffset+=len(m['uv'])
        path=out/(name+'.obj');path.write_text('\n'.join(lines)+'\n');payload=out/(name+'.mesh.json');save(payload,meshes)
        # Read back OBJ numeric payload: a conversion must not silently lose geometry.
        parsed=path.read_text().splitlines();assert sum(x.startswith('v ') for x in parsed)==offset;assert sum(x.startswith('f ') for x in parsed)==sum(len(m['faces']) for m in meshes)
        assert [[float(v) for v in x.split()[1:]] for x in parsed if x.startswith('v ')]==[p for m in meshes for p in m['vertices']]
        rows.append({'source_id':rid,'source_path':r['path'],'source_sha256':digest,'slot':slot['slot'],'obj':str(path.relative_to(ROOT)),'obj_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'mesh_json':str(payload.relative_to(ROOT)),'mesh_json_sha256':hashlib.sha256(payload.read_bytes()).hexdigest(),'meshes':len(meshes),'vertices':offset,'faces':sum(len(m['faces']) for m in meshes)})
    save(out/'manifest.json',{'scene_id':scene['id'],'status':'diagnostic_local_geometry_only','omitted':['frame and scene transforms','original normals','vertex colors','material assignments and textures','animation','skin weights','effects'],'coordinate_policy':'source local XYZ; no unit or axis conversion; OBJ UV unchanged','models':rows});print(json.dumps({'models':len(rows),'vertices':sum(r['vertices'] for r in rows),'faces':sum(r['faces'] for r in rows)}))
if __name__=='__main__':main()
