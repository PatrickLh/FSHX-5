#!/usr/bin/env python3
"""Parse BattleScript trees; retain conditional triggers instead of inventing absolute timing."""
import json,re,collections,os,html
from pathlib import Path,PurePosixPath
from audit import ROOT,BASE,MAN,save,rel

def parse_tree(text):
    root={'name':'__root__','line':0,'attributes':[],'children':[]};stack=[root];pending=None;issues=[]
    for number,raw in enumerate(text.splitlines(),1):
        line=raw.split('//',1)[0].strip()
        if not line:continue
        m=re.fullmatch(r'\[(.+)\]',line)
        if m:
            if pending:issues.append({'line':number,'error':'new section before previous opening brace'})
            pending={'name':m[1],'line':number,'attributes':[],'children':[]}
        elif line=='{':
            if not pending:issues.append({'line':number,'error':'brace without section'});continue
            stack[-1]['children'].append(pending);stack.append(pending);pending=None
        elif line=='}':
            if len(stack)==1:issues.append({'line':number,'error':'unmatched closing brace'})
            else:stack.pop()
        elif '=' in line:
            key,value=line.split('=',1);stack[-1]['attributes'].append({'key':key.strip(),'value':value.strip(),'line':number})
        else:issues.append({'line':number,'error':'unrecognized line','raw':line})
    if len(stack)!=1 or pending:issues.append({'line':len(text.splitlines()),'error':'unclosed block'})
    return root,issues

def flatten(root):
    out=[]
    def walk(node,parent=None,path=''):
        nid=len(out);attrs={x['key']:x['value'] for x in node['attributes']};path=path+'/'+node['name']
        row={'node_id':nid,'parent_id':parent,'section':node['name'],'section_path':path,'source_line':node['line'],'attributes':node['attributes'],'type':attrs.get('Type'),'delay_raw':attrs.get('fDelayTime'),'work_time_raw':attrs.get('fWorkTime'),'condition_raw':attrs.get('dwConditionOfStart'),'object_raw':attrs.get('Object')};out.append(row)
        for child in node['children']:walk(child,nid,path)
    for c in root['children']:walk(c)
    return out

def main():
    catalog=json.loads((MAN/'resource_catalog.json').read_text());byid={x['id']:x for x in catalog}
    configs=json.loads((MAN/'game_config_index.json').read_text());edges=json.loads((MAN/'config_dependencies.json').read_text());material=MAN/'material_dependencies.json'
    if material.exists():edges+=json.loads(material.read_text())
    edgeby=collections.defaultdict(list)
    for e in edges:edgeby[e['from']].append(e)
    animations=json.loads((MAN/'animation_index.json').read_text());animationby={x['id']:x for x in animations};models=json.loads((MAN/'model_index.json').read_text());modelby={x['id']:x for x in models}
    def reachable(start):
        visited=set();todo=[start];unresolved=[]
        while todo:
            nid=todo.pop()
            if nid in visited:continue
            visited.add(nid)
            for e in edgeby.get(nid,[]):
                todo+=e['exact_path_targets']
                if not e['exact_path_targets']:unresolved.append({'from':nid,'reference':e['reference'],'line':e['line']})
            for row in animationby.get(nid,{}).get('resource_rows',[]):
                todo+=row['matched_ids']
                if not row['matched_ids']:unresolved.append({'from':nid,'reference':row['resource'],'line':row['line']})
            for row in animationby.get(nid,{}).get('sound_events',[]):
                todo+=row['matched_ids']
                if not row['matched_ids']:unresolved.append({'from':nid,'reference':row['reference'],'frame':row['frame']})
            for row in modelby.get(nid,{}).get('texture_resolution',[]):
                todo+=row['exact_path_candidates']
                if not row['exact_path_candidates']:unresolved.append({'from':nid,'reference':row['reference']})
        return sorted(visited),unresolved
    records=[];errors=[];types=collections.Counter();review=[]
    for c in configs:
        if not c['original_path'].lower().startswith('battlescript/'):continue
        tree,problems=parse_tree((ROOT/c['path']).read_text());nodes=flatten(tree);actions=[n for n in nodes if n['type'] is not None]
        for a in actions:types[a['type']]+=1
        resources=[n for n in nodes if '/Resource/' in n['section_path']]
        reachable_ids,missing=reachable(c['id'])
        result={'id':c['id'],'original_path':c['original_path'],'source_path':c['path'],'parse_issues':problems,'nodes':nodes,'resource_nodes':resources,'typed_nodes':actions,'reachable_resource_ids':reachable_ids,'unresolved_dependencies':missing,'timing_status':'delays and durations are raw per-node values; condition/event/parent semantics retained, not flattened into absolute start times'}
        out=BASE/'organized'/'effects'/'script_data'/PurePosixPath(c['original_path']).with_suffix('.json');save(out,result)
        records.append({'id':c['id'],'original_path':c['original_path'],'structured_path':rel(out),'nodes':len(nodes),'typed_nodes':len(actions),'reachable_resources':len(reachable_ids),'missing_references':len(missing),'parse_issue_count':len(problems)})
        if problems:errors.append({'id':c['id'],'issues':problems})
        if c['original_path'].lower() in ['battlescript/common0065.txt','battlescript/attack00.txt','battlescript/s1014.txt']:review.append(result)
    save(MAN/'battle_script_index.json',records);save(MAN/'battle_script_parse_issues.json',errors)
    summary={'scripts':len(records),'scripts_without_parse_issues':sum(not x['parse_issue_count'] for x in records),'typed_nodes':sum(x['typed_nodes'] for x in records),'node_types':dict(types),'parse_issue_scripts':len(errors)};save(MAN/'battle_script_summary.json',summary)
    # Review dossiers provide concrete evidence for each resource and action, with line references.
    docs=ROOT/'docs'/'skill-reviews';docs.mkdir(exist_ok=True)
    for r in review:
        lines=[f'# {r["original_path"]} 演出资源核验','',f'来源：`{r["source_path"]}`','', '文件名尚未绑定游戏中文技能名；动作表中的延迟、时长按源文本保留，未折算成绝对时间。人物动作、粒子发射、3D 模型、镜头与条件触发尚未组合渲染。','', '## 显式依赖','', '| 行 | 原引用 | 匹配资源数 |','|---:|---|---:|']
        lines += [f'| {e["line"]} | `{e["reference"]}` | {len(e["exact_path_targets"])} |' for e in edgeby[r['id']]]
        lines += ['', '## 动作节点','', '| 行 | 节点 | Type | 对象 | 触发条件 | 延迟原值 | 时长原值 |','|---:|---|---|---|---|---|---|']
        lines += [f'| {a["source_line"]} | {a["section"]} | {a["type"]} | {a["object_raw"] or ""} | {a["condition_raw"] or ""} | {a["delay_raw"] or ""} | {a["work_time_raw"] or ""} |'.replace('| |','| |') for a in r['typed_nodes']]
        lines += ['',f'递归可达资源 {len(r["reachable_resource_ids"])} 个；未匹配依赖 {len(r["unresolved_dependencies"])} 条。结构数据：`original_resources/organized/effects/script_data/{PurePosixPath(r["original_path"]).with_suffix(".json")}`。','', '## 待验证依赖','']
        lines += [f'- `{x["reference"]}`（来源 `{x["from"]}`）' for x in r['unresolved_dependencies']]
        (docs/(PurePosixPath(r['original_path']).stem+'.md')).write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='node_types'},ensure_ascii=False))
if __name__=='__main__':main()
