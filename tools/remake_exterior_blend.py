"""Run in Blender with blender_files/f-117-nighthawk-exterior.blend open.
Connects finished sources without renaming EDM texture identifiers or touching meshes.
Saves only the review project under dist/exterior-texture-remake.
"""
import bpy, json, hashlib
from pathlib import Path
ROOT=Path(r'E:\Saved Games\DCS\Mods\aircraft\F-117-Nighthawk')
WORK=ROOT/'dist/exterior-texture-remake'

def structure():
    return {'objects':[(o.name,o.type,o.parent.name if o.parent else None) for o in bpy.data.objects],
            'meshes':[(m.name,len(m.vertices),len(m.polygons),[(u.name,len(u.data)) for u in m.uv_layers]) for m in bpy.data.meshes],
            'actions':[(a.name,a.users) for a in bpy.data.actions]}

manifest=json.loads((WORK/'texture-manifest.json').read_text())
assert len(manifest['textures'])==27, 'Wait for all 27 textures'
assert (WORK/'batch-finished.json').exists(), 'Texture batch still running'
before=structure()
report={'images':[],'errors':[],'runtime_names_preserved':True}
lookup={Path(r['original']).stem.lower():r for r in manifest['textures']}
for image in bpy.data.images:
    row=lookup.get(image.name.lower())
    if row is None:continue
    path=WORK/'sources'/(row['stem']+'.png')
    assert path.exists(), str(path)
    old_name=image.name
    image.source='FILE'
    image.filepath=str(path)
    image.reload()
    image.colorspace_settings.name='Non-Color' if row['original'].endswith('_nm.dds') else 'sRGB'
    assert image.name==old_name
    report['images'].append({'name':image.name,'path':str(path),'size':list(image.size)})
after=structure()
if before!=after:report['errors'].append('Model structure changed')
if len(report['images'])!=27:report['errors'].append('Expected 27 connected images')
for m in bpy.data.materials:
    if not m.node_tree:continue
    for n in m.node_tree.nodes:
        if n.type=='TEX_IMAGE' and n.image and n.image.name.lower() in lookup:
            if not Path(bpy.path.abspath(n.image.filepath)).exists():report['errors'].append(m.name+': missing image')
report['objects']=len(bpy.data.objects)
report['meshes']=len(bpy.data.meshes)
report['collision_objects']=len(bpy.data.collections['Collision'].all_objects)
report['unresolved_external_images']=[i.name for i in bpy.data.images if i.name.lower() not in lookup and tuple(i.size)==(1,1)]
(WORK/'blender-validation.json').write_text(json.dumps(report,indent=2))
assert not report['errors'], report['errors']
bpy.ops.wm.save_as_mainfile(filepath=str(WORK/'F117_Exterior_Texture_Remake.blend'),compress=True)
result=report
