"""Build blender_files/f-117-nighthawk-exterior.blend from the installed exterior model.

Run with Blender 5.2, the iEDM_10 importer and the ED EDM exporter installed:

    blender -b --python tools/models/build_exterior_blend.py

The result is one scene that exports back to Shapes/f-117-nighthawk.edm, including the 25
damage-cell collision sections. Collision objects are hidden and drawn as wireframe, so they
don't cover the aircraft while editing. Don't hide the Collision *collection* (its eye icon):
the exporter skips hidden collections, and the model would lose its damage cells.
"""
import hashlib
from pathlib import Path

import addon_utils
import bpy

ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / 'Shapes/f-117-nighthawk.edm'
BLEND = ROOT / 'blender_files/f-117-nighthawk-exterior.blend'
SCENE = 'F-117 Exterior'

bpy.ops.wm.read_homefile(use_empty=True)
for addon in ('io_scene_edm', 'iEDM_10'):
    addon_utils.enable(addon)
scene = bpy.context.scene
scene.name = SCENE
bpy.ops.import_mesh.edm(filepath=str(MODEL), import_bounding_box=True, import_light_box=True)

collision = bpy.data.collections['Collision']
for obj in collision.all_objects:
    obj.display_type = 'WIRE'
    obj.hide_set(True)

model_sha256 = hashlib.sha256(MODEL.read_bytes()).hexdigest()
scene['f117_status'] = 'Source of Shapes/f-117-nighthawk.edm. Export this scene; see docs/models/model-efm-compatibility.md'
scene['f117_model_sha256'] = model_sha256
scene['f117_efm'] = 'Needs the 25-cell EFM. See docs/models/model-efm-compatibility.md'
scene.edm_export_path = str(MODEL)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), compress=True)
print('EXTERIOR_BLEND_OK', BLEND, model_sha256, len(scene.objects), 'objects,',
      len(collision.all_objects), 'collision')
