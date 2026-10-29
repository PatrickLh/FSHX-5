#!/usr/bin/env python3
"""Control edges with source evidence and explicit unresolved runtime branches."""
from pathlib import Path,PurePosixPath
from collections import defaultdict,Counter
import json,re
from audit import ROOT,BASE,MAN,save,rel

def graph(script):
    nodes=script['nodes'];byid={n['node_id']:n for n in nodes};entries=[];edges=[];messages=[]
    for n in nodes:
        parts=n['section_path'].split('/')[1:];parent=byid.get(n['parent_id']);attrs={x['key']:x['value'] for x in n['attributes']}
        if len(parts)==3 and (parts[1].startswith('ActionList') or parts[1]=='Run'):
            entries.append({'node_id':n['node_id'],'owner':parts[0],'list':parts[1],'action':parts[2],'line':n['source_line']})
        if n['condition_raw'] is not None:
            condition=n['condition_raw'];edges.append({'from_node':n['parent_id'],'to_node':n['node_id'],'trigger':'parent_end' if condition=='0' else 'parent_signal_candidate','condition_raw':condition,'source_line':n['source_line'],'evidence':'source comments define 0 as parent end and positive values as numbered events; engine scheduling not validated'})
    for n in nodes:
        attrs={x['key']:x['value'] for x in n['attributes']}
        if n['type']=='SendMessage':
            target=attrs.get('Target','').strip('[]');action=attrs.get('Action','').strip('[]')
            candidates=[e for e in entries if e['owner']==target and e['action']==action]
            messages.append({'from_node':n['node_id'],'target_raw':attrs.get('Target'),'action_raw':attrs.get('Action'),'candidate_entry_nodes':[e['node_id'] for e in candidates],'candidate_entry_paths':[byid[e['node_id']]['section_path'] for e in candidates],'route_status':'external_branch_selection_required' if len(candidates)>1 else 'single_entry_candidate' if candidates else 'external_or_missing_handler','source_line':n['source_line']})
    return {'script_id':script['id'],'source_path':script['source_path'],'entry_points':entries,'condition_edges':edges,'message_routes':messages,'execution_status':'structural graph only; no implicit choice between hit/dodge/result branches'}

def main():
    index=json.loads((MAN/'battle_script_index.json').read_text());out=[];conditions=Counter();routes=Counter()
    for row in index:
        script=json.loads((ROOT/row['structured_path']).read_text());g=graph(script)
        for e in g['condition_edges']:conditions[e['condition_raw']]+=1
        for e in g['message_routes']:routes[e['route_status']]+=1
        path=BASE/'organized'/'effects'/'control_graphs'/PurePosixPath(row['original_path']).with_suffix('.json');save(path,g)
        out.append({'id':row['id'],'path':rel(path),'entry_points':len(g['entry_points']),'condition_edges':len(g['condition_edges']),'message_routes':len(g['message_routes'])})
    save(MAN/'battle_control_graph_index.json',out);save(MAN/'battle_control_graph_summary.json',{'scripts':len(out),'condition_counts':dict(conditions),'message_route_statuses':dict(routes)})
    print('Control graphs:',len(out),'message routes:',dict(routes))
if __name__=='__main__':main()
