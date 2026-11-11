"""Blender preview only. Builds a temporary scene; preserves export scene and materials."""
import bpy, math, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(r'E:\Saved Games\DCS\Mods\aircraft\F-117-Nighthawk')
WORK=ROOT/'dist/exterior-texture-remake'

def render_review(label, restored):
    manifest=json.loads((WORK/'texture-manifest.json').read_text())
    rows={Path(r['original']).stem.lower():r for r in manifest['textures']}
    base=WORK/'originals' if (WORK/'originals').exists() else ROOT/'Textures/F-117-NightHawk-TEXTURES'
    originals={p.stem.lower():p for p in base.glob('*.dds')}
    saved=[]
    for im in bpy.data.images:
        if im.name.lower() not in originals:continue
        saved.append((im,im.filepath,im.source,im.colorspace_settings.name))
        row=rows.get(im.name.lower())
        path=WORK/'sources'/(row['stem']+'.png') if restored and row else originals[im.name.lower()]
        im.source='FILE';im.filepath=str(path);im.reload()
        im.colorspace_settings.name='Non-Color' if im.name.endswith('_nm') else 'sRGB'
    previous=bpy.context.window.scene
    scene=bpy.data.scenes.new('Texture review temporary')
    rig=[]
    collision=set(bpy.data.collections['Collision'].all_objects)
    for obj in bpy.data.collections['Vehicle'].all_objects:
        if obj not in collision:scene.collection.objects.link(obj)
    bpy.context.window.scene=scene
    scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_x=1400
    scene.render.resolution_y=1000
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.filepath=str(WORK/(label+'.png'))
    scene.render.film_transparent=False
    scene.world=bpy.data.worlds.new('Texture review neutral studio')
    scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.22,.25,.29,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
    scene.view_settings.view_transform='AgX'
    scene.view_settings.exposure=1
    camdata=bpy.data.cameras.new('Texture review camera')
    camera=bpy.data.objects.new('Texture review camera',camdata)
    scene.collection.objects.link(camera);rig.append(camera)
    camera.location=(24,-26,16)
    target=Vector((0,0,0))
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    camdata.type='ORTHO';camdata.ortho_scale=24
    scene.camera=camera
    for name,location,power,size in [('Key',(-6,-8,15),2400,12),('Fill',(7,5,12),1800,10)]:
        data=bpy.data.lights.new('Texture review '+name,'AREA')
        data.energy=power;data.shape='DISK';data.size=size
        obj=bpy.data.objects.new(data.name,data);scene.collection.objects.link(obj);rig.append(obj)
        obj.location=location;obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler()
    try:
        bpy.ops.render.render(write_still=True)
    finally:
        bpy.context.window.scene=previous
        world=scene.world
        bpy.data.scenes.remove(scene)
        for obj in rig:
            data=obj.data
            bpy.data.objects.remove(obj,do_unlink=True)
            if isinstance(data,bpy.types.Camera):bpy.data.cameras.remove(data)
            else:bpy.data.lights.remove(data)
        bpy.data.worlds.remove(world)
        for im,path,source,space in saved:
            im.source=source;im.filepath=path
            if source=='FILE' and path:im.reload()
            im.colorspace_settings.name=space
    return str(WORK/(label+'.png'))
