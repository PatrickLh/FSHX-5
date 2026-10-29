#!/usr/bin/env python3
"""Export verified files without guessing names, colors, timing or identities."""
from pathlib import Path, PurePosixPath
from collections import Counter
import json, re, shutil, hashlib, io
from PIL import Image
from audit import ROOT,BASE,MAN,save,rel,file_sha
from references import animation_texture_match
ORG=BASE/'organized'

def category(archive,path):
 p=PurePosixPath(path);top=p.parts[0].lower();lower=path.lower()
 if archive=='XFile':return 'models'
 if archive=='GameData':
  return 'effects/configs' if any(x in lower for x in ['particle','battle','skill']) else 'configurations'
 if top in ['man','face','consulateface']:return 'characters/'+('portraits' if top!='man' else 'sprites')
 if top in ['scriptbg','consulatebg','bg','sea','avcg','colorbg']:return 'backgrounds'
 if top in ['sp','map_efc','particle'] or 'efc' in top:return 'effects'
 if archive=='Texture':return 'ui' # provisional archive grouping; semantic category is recorded below
 return 'ui'

def text_decode(b):
 try:return b.decode('cp950'),None
 except UnicodeDecodeError as e:return b.decode('cp950',errors='replace'),str(e)

def main():
 audit=json.loads((MAN/'baseline_audit.json').read_text())
 if audit['schema_version']!=2 or any(x['status']!='verified' for x in audit['archives']):raise SystemExit('run successful audit first')
 files=[]
 for a in audit['archives']:files.extend(json.loads((MAN/(Path(a['archive']).stem+'_files.json')).read_text()))
 catalog=[];issues=[];animations=[];models=[];configs=[];counts=Counter()
 for n,r in enumerate(files):
  src=ROOT/r['path'];archive=Path(r['archive']).stem;cat=category(archive,r['original_path']);orig=PurePosixPath(r['original_path']);b=src.read_bytes()
  entry={'id':r['id'],'archive':r['archive'],'original_path':r['original_path'],'source_offset':r['offset'],'sha256':r['sha256'],'bytes':r['raw_bytes'],'canonical_path':r['path'],'category':cat,'classification_evidence':'archive and original directory; not visual or gameplay verification','name_confidence':'exact directory entry','historical_version':r['historical_version'],'status':'extracted','outputs':[]}
  output=ORG/cat/archive/(PurePosixPath('__versions__')/f'{r["offset"]:08x}'/orig if r['historical_version'] else orig)
  if r['type'] in ['bmp','jpg','png'] or orig.suffix.lower() in ['.bmp','.jpg','.jpeg','.png','.gif']:
   # Include the original suffix to avoid overwriting different source formats with the same stem.
   dest=output.with_name(output.name+'.png');dest.parent.mkdir(parents=True,exist_ok=True)
   try:
    with Image.open(io.BytesIO(b)) as im:
     im.load();entry['image']={'width':im.width,'height':im.height,'mode':im.mode,'source_format':im.format,'frames':getattr(im,'n_frames',1)}
     if getattr(im,'n_frames',1)>1:raise ValueError('multi-frame image: original retained; animation export pending')
     if im.mode not in ['RGB','RGBA','L','LA','P','1','I','I;16']:im=im.convert('RGBA')
     if not dest.exists():im.save(dest,format='PNG')
     with Image.open(dest) as exported:
      exported.load()
      if exported.size!=im.size or exported.convert('RGBA').tobytes()!=im.convert('RGBA').tobytes():raise ValueError('PNG pixel round-trip mismatch')
    entry.update(status='image_decoded',outputs=[rel(dest)]);counts['images_decoded']+=1
   except Exception as e:
    entry.update(status='image_unresolved',error=str(e));issues.append({'id':r['id'],'kind':'image_decode','error':str(e)})
  else:
   output.parent.mkdir(parents=True,exist_ok=True)
   # Keep a separate organized copy: consumers may edit derived files later.
   if not output.exists():shutil.copyfile(src,output)
   elif file_sha(output)!=r['sha256']:raise ValueError(f'refuse overwrite {output}')
   entry['outputs']=[rel(output)]
   if archive=='Ani' and orig.suffix.lower()=='.ant':
    txt,err=text_decode(b);lines=txt.splitlines();refs=[]
    for ln,line in enumerate(lines,1):
     cols=line.split('\t')
     if re.search(r'\.(bmp|jpe?g|png|wav)$',cols[0].strip(),re.I):refs.append({'line':ln,'resource':cols[0].strip(),'raw_columns':cols[1:]})
    animations.append({'id':r['id'],'original_path':r['original_path'],'path':rel(output),'declared_first_line':lines[0] if lines else '', 'resource_rows':refs,'parameter_status':'raw columns preserved; timing, anchors, transforms and direction semantics not yet validated','decode_error':err})
   if r['type']=='x':
    txt,err=text_decode(b);refs=re.findall(r'TextureFilename\s*\{\s*"([^"]+)"',txt)
    models.append({'id':r['id'],'original_path':r['original_path'],'path':rel(output),'texture_references':refs,'contains_skin_weights':bool(re.search(r'(?m)^\s*SkinWeights\s*\{',txt)),'contains_animation_sets':bool(re.search(r'(?m)^\s*AnimationSet\s',txt)),'decode_error':err})
   if archive=='GameData':
    txt,err=text_decode(b)
    dest=output.with_name(output.name+'.utf8.txt');dest.write_text(txt,encoding='utf-8');entry['outputs'].append(rel(dest))
    sections=re.findall(r'(?m)^\s*\[([^\]\r\n]+)\]',txt)
    refs=sorted(set(re.findall(r'[A-Za-z0-9_!~.\-]+(?:\\[A-Za-z0-9_!~.\-]+)*\.(?:bmp|jpg|png|ant|ani|x|wav|mp3|cfg|ini)',txt,re.I)))
    configs.append({'id':r['id'],'original_path':r['original_path'],'path':rel(dest),'sections':sections,'references':refs,'contains_particle':'Particle' in sections,'contains_battle_script':'BattleScriptSys' in sections,'decode_error':err})
  catalog.append(entry)
  if n%5000==0:print('organized',n,'/',len(files),'images',counts['images_decoded'],flush=True)
 # Match references using original full paths, then record basename candidates without pretending they are exact.
 image_lookup={}
 for e in catalog:
  if not e['historical_version'] and Path(e['archive']).stem in ['AniTexture','Texture','XFile']:
   image_lookup.setdefault((Path(e['archive']).stem,e['original_path'].replace('\\','/').lower()),[]).append(e['id'])
 for a in animations:
  for row in a['resource_rows']:
   row['matched_ids'],row['match_evidence']=animation_texture_match(row['resource'],image_lookup)
   if not row['matched_ids']:issues.append({'id':a['id'],'kind':'animation_resource_reference','reference':row['resource'],'line':row['line']})
 for model in models:
  for ref in model['texture_references']:
   key=ref.replace('\\','/').lower();parent=str(PurePosixPath(model['original_path']).parent)
   candidates=[]
   for k in [key,str(PurePosixPath(parent)/key).lower()]:candidates.extend(image_lookup.get(('XFile',k),[]))
   model.setdefault('texture_resolution',[]).append({'reference':ref,'exact_path_candidates':sorted(set(candidates))})
   if not candidates:issues.append({'id':model['id'],'kind':'model_texture_reference','reference':ref})
 # Source loose media retain names relative to the game directory. No processing of game executable or wrap.
 loose=[]
 for s in json.loads((MAN/'source_inventory.json').read_text()):
  ext=s['extension']
  if ext not in ['.wav','.mp3','.jpg','.jpeg','.png','.gif','.ico']:continue
  src=ROOT/s['path'];sub=src.relative_to(BASE/'source');cat='audio' if ext in ['.wav','.mp3'] else 'backgrounds/source_loose'
  dest=ORG/cat/'source'/sub;dest.parent.mkdir(parents=True,exist_ok=True)
  if not dest.exists():shutil.copyfile(src,dest)
  if file_sha(dest)!=s['sha256']:raise ValueError('loose copy mismatch')
  e={'id':'source:'+sub.as_posix(),'original_path':sub.as_posix(),'canonical_path':s['path'],'sha256':s['sha256'],'bytes':s['bytes'],'category':cat,'status':'extracted','outputs':[rel(dest)],'classification_evidence':'audio extension or unclassified loose image; names retained'};catalog.append(e);loose.append(e)
 save(MAN/'resource_catalog.json',catalog);save(MAN/'animation_index.json',animations);save(MAN/'model_index.json',models);save(MAN/'game_config_index.json',configs);save(MAN/'unresolved.json',issues)
 summary={'archive_files':len(files),'loose_media':len(loose),'images_decoded':counts['images_decoded'],'status_counts':dict(Counter(e['status'] for e in catalog)),'animation_descriptions':len(animations),'animation_resource_rows':sum(len(a['resource_rows']) for a in animations),'animation_unmatched_rows':sum(not row['matched_ids'] for a in animations for row in a['resource_rows']),'models':len(models),'particle_configs':sum(x['contains_particle'] for x in configs),'battle_scripts':sum(x['contains_battle_script'] for x in configs),'issues':len(issues)}
 save(MAN/'export_summary.json',summary);print(json.dumps(summary,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
