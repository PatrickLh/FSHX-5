"""Conservative path aliases observed in WF5's animation authoring files."""
def normalized(path):
    return path.replace('\\','/').lower()
def animation_texture_match(path,lookup):
    key=normalized(path)
    direct=lookup.get(('AniTexture',key),[])
    if direct:return direct,'exact_archive_path'
    for prefix in ['anitexture/','bmp/']:
        if key.startswith(prefix):
            found=lookup.get(('AniTexture',key[len(prefix):]),[])
            if found:return found,'exact_path_after_authoring_root:'+prefix
    return [],'unresolved'
