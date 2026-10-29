#!/usr/bin/env python3
"""Build explicit reference graphs, character bindings and a local visual index."""
from pathlib import Path, PurePosixPath
from collections import defaultdict,Counter
import json,re,html,os
from audit import ROOT,BASE,MAN,save,rel
from config_refs import assignment_references

def norm(s):return re.sub('/+','/',s.replace('\\','/')).lstrip('./').lower()
def main():
 catalog=json.loads((MAN/'resource_catalog.json').read_text());by_id={r['id']:r for r in catalog};lookup=defaultdict(list)
 for r in catalog:
  if r.get('historical_version'):continue
  archive=Path(r.get('archive','source')).stem
  lookup[(archive,norm(r['original_path']))].append(r['id'])
 # Resolve exact archive-relative names; a basename search is only a candidate list.
 def resolve(ref,archives,parent=''):
  found=[]
  for a in archives:
   for path in [norm(ref),norm(str(PurePosixPath(parent)/ref.replace('\\','/')))]:found+=lookup.get((a,path),[])
  return sorted(set(found))
 animations=json.loads((MAN/'animation_index.json').read_text());ani_by_path={norm(a['original_path']):a for a in animations}
 person=next(r for r in catalog if r['id'].startswith('GameData:Dialogue/DialoguePersonData.txt@'))
 persons=[]
 for i,line in enumerate((ROOT/person['canonical_path']).read_text(encoding='cp950').splitlines()):
  cols=line.split()
  if len(cols)<2:continue
  face=cols[2] if len(cols)>2 else None;animation=ani_by_path.get(norm(face)) if face else None
  frame_ids=sorted(set(k for row in (animation['resource_rows'] if animation else []) for k in row['matched_ids']))
  persons.append({'table_row':i,'name':cols[1],'raw_first_field':cols[0],'face_animation_reference':face,'animation_id':animation['id'] if animation else None,'image_ids':frame_ids,'evidence':'DialoguePersonData.txt row and exact animation texture references','model_or_man_binding':'not yet established'})
 save(MAN/'character_index.json',persons)
 configs=json.loads((MAN/'game_config_index.json').read_text());dependencies=[];skills=defaultdict(lambda:{'resources':[]});missing=[]
 for c in configs:
  txt=(ROOT/c['path']).read_text();refs=[]
  for source_ref in assignment_references(txt,c['original_path']):
    ref=source_ref['reference'];lineno=source_ref['line'];ext=PurePosixPath(ref.replace('\\','/')).suffix.lower();archives=['Ani'] if ext in ['.ant','.ani'] else ['XFile'] if ext=='.x' else ['Texture','XFile'] if ext=='.tl' else ['GameData'] if ext in ['.se','.sce','.par','.mat','.vsh','.xef','.cfg','.ini','.txt'] else ['source'] if ext in ['.wav','.mp3'] else ['Texture','AniTexture','XFile']
    targets=resolve(ref,archives,str(PurePosixPath(c['original_path']).parent))
    if ext in ['.wav','.mp3']:
     targets=sorted(set(targets+[r['id'] for r in catalog if r['id'].startswith('source:') and norm(r['original_path']).endswith('/'+norm(ref))]))
    edge={'from':c['id'],'line':lineno,'attribute':source_ref['attribute'],'reference':ref,'exact_path_targets':targets,'status':'resolved' if targets else 'unresolved'};refs.append(edge)
    if not targets:missing.append(edge)
  dependencies+=refs
  c['dependency_count']=len(refs)
  # These are filename tokens, not a proven mapping to gameplay skill IDs.
  token=re.search(r'(?i)(?:sk_?|skill)(\d+)',c['original_path'])
  if token:skills[token[1]]['resources'].append(c['id'])
 save(MAN/'game_config_index.json',configs);save(MAN/'config_dependencies.json',dependencies);save(MAN/'config_unresolved.json',missing)
 save(MAN/'skill_filename_groups.json',{'warning':'Groups use filename numeric tokens only; gameplay skill ID/name mapping and execution timing are unverified.','groups':dict(skills)})
 # A compact gallery samples each original directory, with links to the full output folder.
 groups=defaultdict(list)
 for r in catalog:
  if r['status']=='image_decoded' and not r.get('historical_version'):
   top=r['original_path'].split('/')[0] if '/' in r['original_path'] else '(root)'
   groups[(r['category'],Path(r['archive']).stem,top)].append(r)
 gallery=BASE/'organized'/'index.html';sections=[]
 for (cat,archive,top),rows in sorted(groups.items()):
  cards=[]
  for r in rows[:8]:
   url=os.path.relpath(ROOT/r['outputs'][0],gallery.parent)
   cards.append(f'<a href="{html.escape(url,quote=True)}"><img loading="lazy" src="{html.escape(url,quote=True)}"><span>{html.escape(r["original_path"])}</span></a>')
  folder=os.path.relpath((ROOT/rows[0]['outputs'][0]).parent,gallery.parent)
  sections.append(f'<section><h2>{html.escape(cat+" / "+archive+" / "+top)} ({len(rows)})</h2><p><a href="{html.escape(folder,quote=True)}/">打开资源目录</a> · 仅展示前 8 张，保留原色，未处理透明色。</p><div>{"".join(cards)}</div></section>')
 gallery.write_text('<!doctype html><meta charset="utf-8"><title>风色幻想 5 资源预览</title><style>body{font:15px system-ui;background:#17202b;color:#e5edf6;margin:28px}a{color:#a9d2ff}section{border-top:1px solid #526070;margin-top:24px}div{display:flex;flex-wrap:wrap;gap:12px}div a{width:150px;font-size:11px;overflow-wrap:anywhere}img{width:150px;height:140px;object-fit:contain;background:#333}span{display:block}</style><h1>资源预览目录</h1><p><a href="animation_viewer.html">人物与特效动画预览</a> · <a href="attack_sample.html">基础攻击组合实验</a> · <a href="scene_audit.html">场景与模型审计</a> · <a href="source_art/index.html">PSD 源图预览</a></p><p>按原目录组织；同名文件采用最后追加的数据版本，旧版本另存 __versions__。此目录用于检查素材，不代表人物动作或技能演出已经还原。</p>'+''.join(sections),encoding='utf-8')
 summary={'characters_table_rows':len(persons),'characters_with_animation':sum(bool(p['animation_id']) for p in persons),'characters_with_images':sum(bool(p['image_ids']) for p in persons),'config_reference_rows':len(dependencies),'config_resolved_rows':len(dependencies)-len(missing),'config_unresolved_rows':len(missing),'filename_skill_groups':len(skills),'gallery_groups':len(groups),'reference_parser':'unicode assignment values; includes .par/.tl/.sce/.mat/.vsh; shader bodies excluded'}
 save(MAN/'link_summary.json',summary)
 issues=json.loads((MAN/'unresolved.json').read_text())
 issues=[i for i in issues if i['kind'] not in ['config_reference','config_encoding']]
 issues += [dict(kind='config_reference',**edge) for edge in missing]
 issues += [{'id':c['id'],'kind':'config_encoding','error':c['decode_error']} for c in configs if c['decode_error']]
 save(MAN/'unresolved.json',issues)
 print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
