"""Run inside GIMP 3's Python console. Stage a reversible exterior restoration.
Keeps runtime filenames, UVs, source dimensions and separate original layers.
Reuses cockpit work only after matching the original SHA-256.
"""
from pathlib import Path
from gi.repository import Gimp, Gio, Gegl
import json, hashlib, subprocess, shutil, time, re

ROOT=Path(r'E:\Saved Games\DCS\Mods\aircraft\F-117-Nighthawk')
WORK=ROOT/'dist/exterior-texture-remake'
TEX=ROOT/'Textures/F-117-NightHawk-TEXTURES'
if (WORK/'originals').exists():TEX=WORK/'originals'
SOURCE=WORK/'sources'
STAGE=WORK/'replacements'
PYTHON=r'C:\Users\Fraser\AppData\Local\Programs\Python\Python311\python.exe'
for directory in [WORK,SOURCE,STAGE]:directory.mkdir(exist_ok=True)
PRIOR=ROOT/'dist/cockpit-texture-remake'
PRIOR_TEX=ROOT/'Cockpit/Textures/F-117-NightHawk-CPT-TEXTURES'
PRIOR_ROWS={r['original']:r for r in json.loads((PRIOR/'texture-manifest.json').read_text())['textures']}
REPORT=[]
INDEX_SHA=hashlib.sha256((ROOT/'.git/index').read_bytes()).hexdigest()

def export(image,path,procedure='file-png-export',**settings):
    cfg=Gimp.get_pdb().lookup_procedure(procedure).create_config()
    for key,value in {'run-mode':Gimp.RunMode.NONINTERACTIVE,'image':image,'file':Gio.File.new_for_path(str(path)),**settings}.items():cfg.set_property(key,value)
    status=Gimp.get_pdb().lookup_procedure(procedure).run(cfg).index(0)
    if status!=Gimp.PDBStatusType.SUCCESS:raise RuntimeError(str(path)+': '+str(status))

def process(filename):
    started=time.time()
    path=TEX/filename
    original_sha=hashlib.sha256(path.read_bytes()).hexdigest()
    stem='f117_ext_'+re.sub(r'[^a-z0-9]+','_',path.stem.lower()).strip('_')
    row={'original':filename,'stem':stem,'original_sha256':original_sha}
    old=PRIOR_ROWS.get(filename)
    if old and original_sha==hashlib.sha256((PRIOR_TEX/filename).read_bytes()).hexdigest():
        old_stem=Path(old['renamed']).stem
        for extension in ['.xcf','.png']:
            shutil.copy2(PRIOR/'sources'/(old_stem+extension),SOURCE/(stem+extension))
        # Installed named cockpit assets include the final stencil corrections.
        shutil.copy2(PRIOR_TEX/old['renamed'],STAGE/filename)
        row.update(action='reuse_completed_cockpit_restoration',reuse=old['renamed'])
    else:
        image=Gimp.file_load(Gimp.RunMode.NONINTERACTIVE,Gio.File.new_for_path(str(path)))
        try:
            for mip in image.get_layers()[1:]:image.remove_layer(mip)
            image.get_layers()[0].set_name('Original artwork - UV, markings and alpha reference')
            kind='airframe' if filename.startswith('Aircraft ') else 'gear' if filename.startswith(('Bay ','Door Missiles ','Gear ','Missile')) else 'preserve'
            row['action']='preserve_pixels' if kind=='preserve' else 'selective_'+kind+'_finish'
            if kind!='preserve':
                overlay=WORK/'mask-overlay.png'
                output=subprocess.run([PYTHON,str(ROOT/'tools/exterior_texture_pixels.py'),'mask',str(path),kind,str(overlay)],capture_output=True,text=True,check=True)
                row.update(json.loads(output.stdout))
                layer=Gimp.file_load_layer(Gimp.RunMode.NONINTERACTIVE,image,Gio.File.new_for_path(str(overlay)))
                image.insert_layer(layer,None,0)
                layer.set_name('Selective '+kind+' finish - markings and UV layout retained')
                overlay.unlink()
            if not Gimp.file_save(Gimp.RunMode.NONINTERACTIVE,image,Gio.File.new_for_path(str(SOURCE/(stem+'.xcf')))):raise RuntimeError('XCF save failed')
            composite=image.duplicate()
            try:
                composite.merge_visible_layers(Gimp.MergeType.CLIP_TO_IMAGE)
                export(composite,SOURCE/(stem+'.png'))
            finally:composite.delete()
            clean=Gimp.file_load(Gimp.RunMode.NONINTERACTIVE,Gio.File.new_for_path(str(SOURCE/(stem+'.png'))))
            try:
                export(clean,STAGE/filename,'file-dds-export',**{'compression-format':'none' if filename=='F-117_frontmesh.dds' else 'bc7','format':'rgba8','mipmaps':'generate','mipmap-filter':'box','mipmap-wrap':'clamp','gamma-correct':True,'srgb':True,'flip-image':False})
            finally:clean.delete()
        finally:image.delete()
    row['seconds']=round(time.time()-started,2)
    REPORT.append(row)
    (WORK/'texture-manifest.json').write_text(json.dumps({'index_sha256_before':INDEX_SHA,'runtime_names_preserved':True,'textures':REPORT},indent=2))
    Gimp.displays_flush()
    return row


def run_batch():
    """Build all candidates; never installs or stages Git changes."""
    for path in sorted(TEX.glob('*.dds')):
        if any(row['original']==path.name for row in REPORT):continue
        try:
            process(path.name)
        except Exception as error:
            (WORK/'batch-error.json').write_text(json.dumps({'texture':path.name,'error':repr(error)},indent=2))
            raise
    (WORK/'batch-finished.json').write_text(json.dumps({'count':len(REPORT)},indent=2))
    return REPORT
