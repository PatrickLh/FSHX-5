#!/usr/bin/env python3
"""Read-only text-X geometry audit; no triangulation, normalization or repair."""
from pathlib import Path
from collections import Counter
import json,re,math,struct,uuid,hashlib
from audit import ROOT,BASE,MAN,save
TOKEN=re.compile(r'"(?:\\.|[^"\\])*"|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?|[A-Za-z_][\w.\-]*|[^\s]')
NUMBER=re.compile(r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?$')

def parse_blocks(tokens):
    blocks=[];stack=[]
    for i,t in enumerate(tokens):
        if t=='{':
            prev=tokens[i-1] if i else '';prev2=tokens[i-2] if i>=2 else ''
            if re.match(r'^[A-Za-z_]',prev):
                if re.match(r'^[A-Za-z_]',prev2) and prev2!='template':kind,name=prev2,prev
                else:kind,name=prev,None
            else:kind,name='_reference',None
            is_template=(prev2=='template' or (i>=3 and tokens[i-3]=='template'))
            if stack:is_template=is_template or blocks[stack[-1]]['template']
            block={'kind':kind,'name':name,'start':i+1,'end':None,'parent':stack[-1] if stack else None,'template':is_template};blocks.append(block);stack.append(len(blocks)-1)
        elif t=='}':
            if not stack:raise ValueError('unmatched closing brace')
            blocks[stack.pop()]['end']=i
    if stack:raise ValueError('unclosed block')
    return blocks

class Cursor:
    def __init__(self,tokens,start,end):self.t=tokens;self.p=start;self.end=end
    def number(self,integer=False):
        while self.p<self.end and self.t[self.p] in [';',',']:self.p+=1
        if self.p>=self.end or not NUMBER.fullmatch(self.t[self.p]):raise ValueError(f'expected number near token {self.p}: {self.t[self.p:self.p+3]}')
        value=float(self.t[self.p]);self.p+=1
        if not math.isfinite(value):raise ValueError('nonfinite numeric value')
        if integer:
            if int(value)!=value or value<0:raise ValueError('invalid count/index')
            return int(value)
        return value
    def vector(self,n):return [self.number() for _ in range(n)]

def audit_text(text):
    text=re.sub(r'/\*.*?\*/','',text,flags=re.S);text=re.sub(r'//[^\r\n]*','',text)
    return audit_tokens(TOKEN.findall(text[16:]))

def audit_tokens(tokens):
    blocks=parse_blocks(tokens);meshes=[];warnings=[];frames=[]
    for i,b in enumerate(blocks):
        if b['template']:continue
        if b['kind']=='FrameTransformMatrix':
            c=Cursor(tokens,b['start'],b['end']);frames.append({'frame':blocks[b['parent']]['name'] if b['parent'] is not None else None,'matrix_raw_16':c.vector(16)})
        if b['kind']!='Mesh':continue
        c=Cursor(tokens,b['start'],b['end']);nv=c.number(True);vertices=[c.vector(3) for _ in range(nv)];nf=c.number(True);faces=[]
        for _ in range(nf):degree=c.number(True);faces.append([c.number(True) for _ in range(degree)])
        bad_indices=sum(v>=nv for f in faces for v in f);repeated=sum(len(set(f))<len(f) for f in faces);tri_zero=0
        for f in faces:
            if len(f)!=3 or any(v>=nv for v in f):continue
            a,bb,cc=[vertices[v] for v in f];u=[bb[k]-a[k] for k in range(3)];v=[cc[k]-a[k] for k in range(3)];cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
            tri_zero+=sum(x*x for x in cross)<1e-20
        row={'mesh_name':b['name'],'vertices':nv,'faces':nf,'polygon_degrees':dict(Counter(map(len,faces))),'invalid_vertex_indices':bad_indices,'faces_with_repeated_indices':repeated,'near_zero_area_triangles':tri_zero,'local_aabb_min':[min(v[k] for v in vertices) for k in range(3)] if vertices else None,'local_aabb_max':[max(v[k] for v in vertices) for k in range(3)] if vertices else None,'uv':None,'normals':None,'materials':None}
        for child in [x for x in blocks if x['parent']==i and not x['template']]:
            cc=Cursor(tokens,child['start'],child['end'])
            if child['kind']=='MeshTextureCoords':
                n=cc.number(True);uv=[cc.vector(2) for _ in range(n)];row['uv']={'count':n,'count_matches_vertices':n==nv,'min':[min(v[k] for v in uv) for k in range(2)] if uv else None,'max':[max(v[k] for v in uv) for k in range(2)] if uv else None,'outside_unit_square':sum(any(x<0 or x>1 for x in v) for v in uv)}
            elif child['kind']=='MeshNormals':
                n=cc.number(True);normals=[cc.vector(3) for _ in range(n)];count=cc.number(True);normal_faces=[]
                for _ in range(count):degree=cc.number(True);normal_faces.append([cc.number(True) for _ in range(degree)])
                row['normals']={'count':n,'face_count':count,'face_layout_matches_mesh':count==nf and [len(f) for f in normal_faces]==[len(f) for f in faces],'invalid_indices':sum(x>=n for f in normal_faces for x in f),'nonunit_or_zero_vectors':sum(abs(math.sqrt(sum(x*x for x in v))-1)>0.02 for v in normals)}
            elif child['kind']=='MeshMaterialList':
                n=cc.number(True);assign=cc.number(True);indices=[cc.number(True) for _ in range(assign)];row['materials']={'declared_materials':n,'face_assignments':assign,'count_matches_faces':assign==nf,'invalid_indices':sum(x>=n for x in indices)}
        meshes.append(row)
    return {'meshes':meshes,'frame_transforms':frames,'skin_weight_blocks':sum(b['kind']=='SkinWeights' and not b['template'] for b in blocks),'animation_sets':sum(b['kind']=='AnimationSet' and not b['template'] for b in blocks),'coordinate_status':'local source coordinates and raw frame matrices; no axis/unit conversion or animation evaluation'}

def binary_tokens(data):
    # Microsoft DirectX token records; all reads are bounded to original source bytes.
    p=16;out=[];token_count=0;standalone={10:'{',11:'}',12:'(',13:')',14:'[',15:']',16:'<',17:'>',18:'.',19:',',20:';',31:'template',40:'WORD',41:'DWORD',42:'FLOAT',43:'DOUBLE',44:'CHAR',45:'UCHAR',46:'SWORD',47:'SDWORD',48:'VOID',49:'LPSTR',50:'UNICODE',51:'CSTRING',52:'array'}
    def read(fmt):
        nonlocal p
        size=struct.calcsize(fmt)
        if p+size>len(data):raise ValueError('truncated binary token')
        values=struct.unpack_from(fmt,data,p);p+=size;return values
    while p<len(data):
        start=p;token=read('<H')[0];token_count+=1
        if token in [1,2]:
            n=read('<I')[0]
            if p+n>len(data):raise ValueError('truncated binary string')
            value=data[p:p+n].rstrip(b'\0').decode('cp950');p+=n;out.append(json.dumps(value,ensure_ascii=False) if token==2 else value)
            if token==2:
                if p+4<=len(data) and struct.unpack_from('<I',data,p)[0] in [19,20]:out.append(standalone[read('<I')[0]])
                else:
                    term=read('<H')[0]
                    if term not in [19,20]:raise ValueError('invalid string terminator')
                    out.append(standalone[term])
        elif token==3:out.append(str(read('<I')[0]))
        elif token==5:
            if p+16>len(data):raise ValueError('truncated GUID')
            out+=['<',str(uuid.UUID(bytes_le=data[p:p+16])),'>'];p+=16
        elif token in [6,7]:
            n=read('<I')[0];fmt='I' if token==6 else ('d' if data[12:16]==b'0064' else 'f')
            if n*struct.calcsize(fmt)>len(data)-p:raise ValueError('invalid list count')
            out.extend(str(v) for v in read('<'+str(n)+fmt))
        elif token in standalone:out.append(standalone[token])
        else:raise ValueError(f'unsupported binary token {token} at {start}')
    return out,token_count

def main():
    models=json.loads((MAN/'model_index.json').read_text());catalog={r['id']:r for r in json.loads((MAN/'resource_catalog.json').read_text())};records=[];issues=[]
    for r in models:
        data=(ROOT/r['path']).read_bytes();digest=hashlib.sha256(data).hexdigest();assert digest==catalog[r['id']]['sha256'],r['id'];out={'id':r['id'],'original_path':r['original_path'],'source_path':r['path'],'source_sha256':digest,'historical_version':'/__versions__/' in r['path'],'header':data[:16].decode('ascii',errors='replace')}
        try:
            if data[8:12]==b'bin ':
                tokens,count=binary_tokens(data);out.update(audit_tokens(tokens),status='binary_structure_parsed',binary_token_count=count,binary_bytes_consumed=len(data))
            elif data[8:12]==b'txt ':out.update(audit_text(data.decode('cp950')),status='text_structure_parsed')
            else:raise ValueError('unsupported encoding header')
        except (ValueError,IndexError,UnicodeDecodeError,struct.error) as e:out.update(status='parse_unresolved',error=str(e))
        if out['status']=='parse_unresolved':issues.append({'kind':'model_geometry_parse','id':r['id'],'status':out['status'],'error':out.get('error',out.get('reason'))})
        records.append(out)
    save(MAN/'model_geometry_index.json',records);save(MAN/'model_geometry_issues.json',issues)
    parsed=[r for r in records if r['status'].endswith('structure_parsed')];meshes=[m for r in parsed for m in r['meshes']]
    summary={'model_versions':len(records),'current_versions':sum(not r['historical_version'] for r in records),'models_parsed':len(parsed),'status_counts':dict(Counter(r['status'] for r in records)),'meshes':len(meshes),'vertices':sum(m['vertices'] for m in meshes),'faces':sum(m['faces'] for m in meshes),'invalid_vertex_indices':sum(m['invalid_vertex_indices'] for m in meshes),'meshes_with_uv_count_mismatch':sum(m['uv'] is not None and not m['uv']['count_matches_vertices'] for m in meshes),'meshes_with_normal_layout_mismatch':sum(m['normals'] is not None and not m['normals']['face_layout_matches_mesh'] for m in meshes),'models_with_skin_weight_blocks':sum(r['skin_weight_blocks']>0 for r in parsed),'models_with_animation_sets':sum(r['animation_sets']>0 for r in parsed)}
    save(MAN/'model_geometry_summary.json',summary);print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
