"""Resource paths in assignment values, including Chinese names and .par files.
Shader swizzles are not asset references. Preserve exact tokens and line evidence.
"""
import re
EXT=r'(?:bmp|jpe?g|png|tga|ant|ani|xef|se|sce|par|mat|vsh|tl|x|wav|mp3|cfg|ini|txt)'
TOKEN=re.compile(r'[^\s,;()={}<>"\']+\.'+EXT+r'\b',re.I)
def assignment_references(text,source_path):
    if source_path.lower().endswith(('.vsh','.scc')):return []
    result=[]
    for lineno,raw in enumerate(text.splitlines(),1):
        line=raw.split('//',1)[0].strip()
        if '=' not in line:continue
        key,value=line.split('=',1)
        for match in TOKEN.finditer(value):
            result.append({'line':lineno,'reference':match[0],'attribute':key.strip()})
    return result
