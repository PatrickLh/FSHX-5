#!/usr/bin/env python3
"""Export PSD merged previews; retain the layered source and base catalog status."""
from pathlib import Path,PurePosixPath
import json,os,html
from PIL import Image
from audit import ROOT,BASE,MAN,save,rel

def main():
    catalog=json.loads((MAN/'resource_catalog.json').read_text());items=[]
    for r in catalog:
        if PurePosixPath(r['original_path']).suffix.lower()!='.psd':continue
        source=ROOT/r['canonical_path'];dest=BASE/'organized'/'source_art'/Path(r['archive']).stem/(r['original_path']+'.png');dest.parent.mkdir(parents=True,exist_ok=True)
        with Image.open(source) as im:
            im.load();pixels=im.convert('RGBA')
            if not dest.exists():pixels.save(dest,format='PNG')
            with Image.open(dest) as check:
                assert check.size==pixels.size and check.convert('RGBA').tobytes()==pixels.tobytes(),r['id']
            preview={'id':r['id'],'source_path':r['canonical_path'],'path':rel(dest),'width':im.width,'height':im.height,'mode':im.mode,'preview_kind':'merged composite; PSD layers remain in original source','source_sha256':r['sha256']}
        r['source_art_preview']=preview
        if rel(dest) not in r['outputs']:r['outputs'].append(rel(dest))
        items.append(preview)
    save(MAN/'resource_catalog.json',catalog);save(MAN/'source_art_index.json',items)
    page=BASE/'organized'/'source_art'/'index.html';cards=[]
    for r in items:
        url=os.path.relpath(ROOT/r['path'],page.parent);cards.append(f'<section><h2>{html.escape(r["id"])}</h2><p>{r["width"]}×{r["height"]} · PSD 合成预览；原始分层文件保持不变。</p><a href="{html.escape(url,quote=True)}"><img style="max-width:100%;max-height:700px" src="{html.escape(url,quote=True)}"></a></section>')
    page.write_text('<!doctype html><meta charset="utf-8"><title>PSD 源图预览</title><style>body{font:15px system-ui;background:#17202b;color:white;margin:24px}</style><h1>PSD 源图合成预览</h1>'+''.join(cards))
    print('PSD merged previews:',len(items))
if __name__=='__main__':main()
