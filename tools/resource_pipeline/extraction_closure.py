#!/usr/bin/env python3
"""Close extraction coverage; keep decoding and runtime-reference gaps distinct."""
import json,hashlib,zipfile,shutil,collections,struct,sys,platform
import PIL
from pathlib import Path
from PIL import Image,ImageSequence
from audit import ROOT,BASE,MAN,save,rel,file_sha
from animations import ani_resources

def main():
    catalog=json.loads((MAN/'resource_catalog.json').read_text());inventory=json.loads((MAN/'source_inventory.json').read_text());by_source={r['canonical_path']:r for r in catalog};records=[];support=[];media=[];backups=[]
    # Account for every loose file: archive, distribution, executable, support, media or OS metadata.
    for s in inventory:
        p=ROOT/s['path'];ext=s['extension'];row=dict(s)
        if s['path'] in by_source:row.update(disposition='loose_media_in_catalog',resource_id=by_source[s['path']]['id'])
        elif ext=='.jbf':row['disposition']='archive_fully_reconstructed'
        elif ext=='.zip':row['disposition']='distribution_container_audited'
        elif p.name=='.DS_Store':row['disposition']='os_metadata_preserved'
        elif ext in ['.exe','.dll','.bin']:row['disposition']='runtime_binary_preserved_not_executed'
        else:
            sub=p.relative_to(BASE/'source');dest=BASE/'organized/support/source'/sub;dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists():shutil.copyfile(p,dest)
            assert file_sha(dest)==s['sha256'];row.update(disposition='support_original_copied',output=rel(dest));support.append(row)
        records.append(row)
        if ext not in ['.gif','.ico']:continue
        with Image.open(p) as im:
            destdir=BASE/'organized/source_art/loose'/p.relative_to(BASE/'source');destdir.mkdir(parents=True,exist_ok=True);exports=[]
            variants=[(f'{w}x{h}',im.ico.getimage((w,h))) for w,h in sorted(im.info['sizes'])] if ext=='.ico' else [(f'frame_{i:04d}',f.copy()) for i,f in enumerate(ImageSequence.Iterator(im))]
            for label,img in variants:
                dest=destdir/(label+'.png');img=img.convert('RGBA');img.save(dest)
                with Image.open(dest) as check:assert check.convert('RGBA').tobytes()==img.tobytes()
                exports.append({'path':rel(dest),'sha256':file_sha(dest),'width':img.width,'height':img.height})
            media.append({'source':s['path'],'source_sha256':s['sha256'],'format':im.format,'duration_raw_ms':im.info.get('duration'),'exports':exports})
    # BAK files are retained source files, never substituted for current animation resources.
    for r in catalog:
        if r['original_path'].lower().endswith('.ani.bak'):
            row={'id':r['id'],'source_sha256':r['sha256'],'original_path':r['original_path']}
            try:row.update(status='resource_table_parsed',resources=ani_resources((ROOT/r['canonical_path']).read_bytes()))
            except (ValueError, IndexError, AssertionError, UnicodeDecodeError, struct.error) as e:row.update(status='parse_unresolved',error=str(e))
            backups.append(row)
    save(MAN/'loose_source_coverage.json',records);save(MAN/'loose_media_exports.json',media);save(MAN/'backup_animation_tables.json',backups)
    # Compare every ZIP member against its unpacked original by bytes/hash, not just filename.
    ziprows=[]
    for s in inventory:
        if s['extension']!='.zip':continue
        zp=ROOT/s['path'];unpacked=zp.with_suffix('')
        with zipfile.ZipFile(zp) as z:
            names=set()
            for info in z.infolist():
                if info.is_dir():continue
                name=info.filename;parts=Path(name).parts;assert not Path(name).is_absolute() and '..' not in parts and name not in names;names.add(name)
                digest=hashlib.sha256();data=None
                with z.open(info) as f:
                    if not (unpacked/name).exists():data=f.read();digest.update(data)
                    else:
                        for block in iter(lambda:f.read(1024*1024),b''):digest.update(block)
                row={'zip':s['path'],'member':name,'bytes':info.file_size,'sha256':digest.hexdigest(),'zip_crc32':f'{info.CRC:08x}'}
                target=unpacked/name
                if target.exists():assert file_sha(target)==row['sha256'];row.update(status='matches_unpacked_source',path=rel(target))
                else:
                    # Missing ZIP members are ancillary distribution documents/links. Preserve exact bytes, never open links.
                    target=BASE/'organized/support/distribution_zip'/name;target.parent.mkdir(parents=True,exist_ok=True)
                    if target.exists():assert target.read_bytes()==data
                    else:target.write_bytes(data)
                    row.update(status='additional_member_preserved',path=rel(target))
                ziprows.append(row)
    save(MAN/'distribution_zip_audit.json',ziprows)
    # Hash every organized catalog output, including converted pixels, as a handoff receipt.
    outputs=[]
    for r in catalog:
        for path in r['outputs']:
            p=ROOT/path;outputs.append({'resource_id':r['id'],'path':path,'bytes':p.stat().st_size,'sha256':file_sha(p)})
    save(MAN/'organized_output_checksums.json',outputs)
    issues=json.loads((MAN/'unresolved.json').read_text());summary={'status':'archive_and_loose_extraction_verified_with_declared_decode_gaps','archive_file_versions':sum('archive' in r for r in catalog),'archive_current_versions':sum('archive' in r and not r.get('historical_version') for r in catalog),'catalog_resources':len(catalog),'organized_catalog_outputs_hashed':len(outputs),'loose_source_files_accounted':len(records),'loose_dispositions':dict(collections.Counter(r['disposition'] for r in records)),'zip_file_members_verified':len(ziprows),'zip_additional_members_preserved':sum(r['status']=='additional_member_preserved' for r in ziprows),'loose_media_pngs':sum(len(r['exports']) for r in media),'backup_animation_tables':len(backups),'backup_animation_tables_parsed':sum(r['status']=='resource_table_parsed' for r in backups),'image_decode_failures':sum(r['status']=='image_unresolved' for r in catalog),'open_issues_by_kind':dict(collections.Counter(r['kind'] for r in issues)),'wrap_files_preserved_not_decoded':10,'runtime_fidelity_validation':'outside extraction completion; not claimed','godot_work':'paused by user scope'}
    save(MAN/'extraction_environment.json',{'python':sys.version,'platform':platform.platform(),'pillow':PIL.__version__,'text_codec':'cp950; original bytes retained on decode failures','zip_checks':'CRC32 by zipfile and SHA256 comparison','scope':'resource extraction only'})
    save(MAN/'extraction_completion.json',summary);print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
