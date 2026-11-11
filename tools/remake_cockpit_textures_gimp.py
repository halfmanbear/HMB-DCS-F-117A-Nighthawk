"""Run in the GIMP MCP Python console; preserves the old layer and UV layout.

The flight manual supplies stencil/layout evidence, not surface colours.
All colour treatments below are editorial restoration of the existing artwork.
"""
from pathlib import Path
from gi.repository import Gimp, Gegl, Gio
import json
import math
import struct
import time

ROOT = Path(r'E:\Saved Games\DCS\Mods\aircraft\F-117-Nighthawk')
WORK = ROOT / 'dist/cockpit-texture-remake'
TEX = ROOT / 'Cockpit/Textures/F-117-NightHawk-CPT-TEXTURES'
SOURCE = WORK / 'sources'
STAGE = WORK / 'replacements'
STAGE.mkdir(exist_ok=True)
DOCUMENTS = {}


def load_original(row):
    image = Gimp.file_load(Gimp.RunMode.NONINTERACTIVE,
                           Gio.File.new_for_path(str(TEX / row['original'])))
    for mip in image.get_layers()[1:]:
        image.remove_layer(mip)
    image.get_layers()[0].set_name('Original artwork - UV and colour reference')
    return image


def write_export(image, path, procedure='file-png-export', **settings):
    proc = Gimp.get_pdb().lookup_procedure(procedure)
    cfg = proc.create_config()
    for name, value in {'run-mode': Gimp.RunMode.NONINTERACTIVE,
                        'image': image,
                        'file': Gio.File.new_for_path(str(path)),
                        **settings}.items():
        cfg.set_property(name, value)
    status = proc.run(cfg).index(0)
    if status != Gimp.PDBStatusType.SUCCESS:
        raise RuntimeError(f'{path}: export status {status}')


def save_document(image, stem, normal=False, keep_size=True):
    if not Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, image,
                          Gio.File.new_for_path(str(SOURCE / (stem + '.xcf')))):
        raise RuntimeError('XCF save failed: ' + stem)
    composite = image.duplicate()
    composite.merge_visible_layers(Gimp.MergeType.CLIP_TO_IMAGE)
    write_export(composite, SOURCE / (stem + '.png'))
    # DDS-imported images carry saved compression options. A fresh PNG load
    # prevents those options overriding the requested BC7/BC5 output format.
    clean = Gimp.file_load(Gimp.RunMode.NONINTERACTIVE,
                          Gio.File.new_for_path(str(SOURCE / (stem + '.png'))))
    write_export(clean, STAGE / (stem + '.dds'), 'file-dds-export',
                 **{'compression-format': 'bc5' if normal else 'bc7',
                    'mipmaps': 'generate', 'mipmap-filter': 'box',
                    'mipmap-wrap': 'clamp', 'gamma-correct': not normal,
                    'srgb': not normal, 'flip-image': False})
    clean.delete()
    preview = composite.duplicate()
    w, h = preview.get_width(), preview.get_height()
    if max(w, h) > 1024:
        preview.scale(round(w * 1024 / max(w, h)), round(h * 1024 / max(w, h)))
    write_export(preview, WORK / (stem + '-after.png'))
    preview.delete()
    composite.delete()


def transform_colour(rgb, kind):
    r, g, b = rgb
    lo, hi = min(rgb), max(rgb)
    lum = (r * 54 + g * 183 + b * 19) / 256
    if kind in ('panel', 'structure', 'airframe'):
        # Neutral dark coating only: retain coloured lights, stencils, and gaps.
        if 18 < lum < 115 and hi - lo < 30:
            # Reduce the old blue cast and restore a less chalky graphite coat.
            grey = 34 + (lum - 34) * .70
            strength = .55 if kind == 'panel' else .70
            target = (grey * .98, grey, grey * 1.025)
            return tuple(round(v * (1-strength) + t * strength)
                         for v, t in zip(rgb, target))
    elif kind in ('cloth', 'seat'):
        # Chromatic mask excludes skin, hardware, placards, and black padding.
        if 22 < lum < 170 and g > r * 1.025 and g > b * 1.025 and hi-lo > 6:
            grey = lum
            target = (grey * .91, grey * 1.025, grey * .84)
            return tuple(round(v * .45 + t * .55) for v,t in zip(rgb,target))
    elif kind == 'gear':
        if 65 < lum < 230 and hi-lo < 22:
            # Clean the neutral alloy finish while retaining its shading.
            target = min(240, lum * 1.025 + 2)
            return tuple(round(v * .55 + target * .45) for v in rgb)
    return rgb


def restore_colour(row, kind):
    started = time.time()
    image = load_original(row)
    base = image.get_layers()[0]
    w, h = image.get_width(), image.get_height()
    layer = Gimp.Layer.new(image, 'Restored ' + kind + ' finish - colour masked',
                           w, h, Gimp.ImageType.RGBA_IMAGE, 100, Gimp.LayerMode.NORMAL)
    image.insert_layer(layer, None, 0)
    layer.fill(Gimp.FillType.TRANSPARENT)
    cache = {}
    changed = 0
    # Small strips keep GI copies and Python allocations bounded for 8K assets.
    for y in range(0, h, 64):
        rows = min(64, h-y)
        rect = Gegl.Rectangle.new(0, y, w, rows)
        src = bytes(base.get_buffer().get(rect, 1.0, "R'G'B'A u8", Gegl.AbyssPolicy.NONE))
        dst = bytearray(len(src))
        for p in range(0, len(src), 4):
            rgb = src[p:p+3]
            new = cache.get(rgb)
            if new is None:
                new = bytes(max(0,min(255,v)) for v in transform_colour(tuple(rgb),kind))
                cache[rgb] = new
            if new != rgb:
                dst[p:p+3] = new
                dst[p+3] = src[p+3]
                changed += 1
        layer.get_buffer().set(rect, "R'G'B'A u8", bytes(dst))
    layer.update(0,0,w,h)
    DOCUMENTS[row['renamed'][:-4]] = image
    Gimp.displays_flush()
    return {'texture': row['renamed'], 'kind':kind, 'changed_pixels':changed,
            'width':w,'height':h,'seconds':round(time.time()-started,2)}


def repair_normal(row):
    image = load_original(row)
    base = image.get_layers()[0]
    w,h = image.get_width(), image.get_height()
    layer = base.copy()
    image.insert_layer(layer,None,0)
    layer.set_name('Reconstructed unit normals - BC5 delivery')
    rect = Gegl.Rectangle.new(0,0,w,h)
    src = bytes(base.get_buffer().get(rect,1.0,"R'G'B'A u8",Gegl.AbyssPolicy.NONE))
    dst = bytearray(src)
    # BC5 source R/G are authoritative; rebuild positive Z. The BC1 pilot map
    # has explicit XYZ; normalize all three to avoid changing its slope direction.
    bc5 = row['fourcc'] == 'ATI2'
    for p in range(0,len(src),4):
        x,y = src[p]/127.5-1, src[p+1]/127.5-1
        z = math.sqrt(max(0,1-x*x-y*y)) if bc5 else src[p+2]/127.5-1
        length = math.sqrt(x*x+y*y+z*z)
        if src[p+3]==0:
            x,y,z,length = 0,0,1,1
        if length < 1e-8: x,y,z,length = 0,0,1,1
        dst[p:p+3] = bytes(round(max(0,min(255,(v/length+1)*127.5))) for v in (x,y,z))
        dst[p+3] = 255  # BC5 has no alpha: unused UV space must be a flat normal.
    layer.get_buffer().set(rect,"R'G'B'A u8",bytes(dst))
    layer.update(0,0,w,h)
    stem = row['renamed'][:-4]
    DOCUMENTS[stem] = image
    save_document(image,stem,normal=True)
    return {'texture':row['renamed'],'action':'unit_normal_reconstruction_BC5',
            'width':w,'height':h,'added_geometric_detail':False}


def load_manifest():
    return json.loads((WORK / 'texture-manifest.json').read_text())


def add_svg(image, path, label):
    layer = Gimp.file_load_layer(Gimp.RunMode.NONINTERACTIVE, image,
                                Gio.File.new_for_path(str(path)))
    image.insert_layer(layer,None,0)
    layer.set_name(label)
    Gimp.displays_flush()
    return layer


def run_remaining():
    report = []
    (WORK/'remaining-progress.json').write_text('[]')
    kinds = {'Aircraft 03_BaseColor.dds':'airframe',
             'Cockpit 01_BaseColor.dds':'structure',
             'Cockpit 02_BaseColor.dds':'structure',
             'Cockpit 03_BaseColor.dds':'panel',
             'Cockpit 04_BaseColor.dds':'panel',
             'Gear front_BaseColor.dds':'gear',
             'Pilot_F117.dds':'cloth', 'seat_BaseColor.dds':'seat'}
    for row in load_manifest()['textures']:
        if row['original']=='nighthawk_att.dds':
            continue
        stem=row['renamed'][:-4]
        try:
            if row['original'] in kinds:
                # Reuse the already authored stencils in saved layered sources.
                if row['original'] in ['Cockpit 03_BaseColor.dds','Cockpit 04_BaseColor.dds']:
                    image=Gimp.file_load(Gimp.RunMode.NONINTERACTIVE,
                              Gio.File.new_for_path(str(SOURCE/(stem+'.xcf'))))
                    item={'texture':row['renamed'],'kind':'restored_finish_and_vector_stencils'}
                else:
                    item=restore_colour(row,kinds[row['original']])
                    image=DOCUMENTS[stem]
                save_document(image,stem)
                image.delete()
            elif stem.endswith('_normal'):
                item=repair_normal(row)
                DOCUMENTS[stem].delete()
            elif row['original']=='nighthawkgreen.dds':
                image=load_original(row)
                base=image.get_layers()[0]
                rect=Gegl.Rectangle.new(0,0,image.get_width(),image.get_height())
                pixels=bytes(base.get_buffer().get(rect,1.,"R'G'B'A u8",Gegl.AbyssPolicy.NONE))
                if pixels != pixels[:4]*(len(pixels)//4):
                    raise RuntimeError('Green texture is not constant; refusing downsize')
                image.scale(4,4)
                image.get_layers()[0].set_name('Exact original constant green - 4px tile')
                save_document(image,stem)
                image.delete()
                item={'texture':row['renamed'],'action':'exact_constant_colour_4x4_tile'}
            else:
                image=load_original(row)
                image.get_layers()[0].set_name('Original optical RGB and alpha preserved')
                save_document(image,stem)
                image.delete()
                item={'texture':row['renamed'],'action':'preserve_optical_pixels_BC7_full_mip_chain'}
            report.append({'status':'success',**item})
        except Exception as error:
            report.append({'texture':row['renamed'],'status':'error','error':repr(error)})
        (WORK/'remaining-progress.json').write_text(json.dumps(report,indent=2))
    (WORK/'remaining-batch-finished.json').write_text(json.dumps(report,indent=2))
    return report


def run_calibrated_faces():
    stem='f117_cpt_instrument_panels_albedo'
    image=Gimp.file_load(Gimp.RunMode.NONINTERACTIVE,
                        Gio.File.new_for_path(str(SOURCE/(stem+'.xcf'))))
    for layer in image.get_layers():
        if layer.get_name().startswith('Calibrated gauge faces'):
            image.remove_layer(layer)
    add_svg(image,SOURCE/'f117_cpt_calibrated_gauge_faces.svg',
            'Calibrated gauge faces - ALT 1005 and IAS 1006')
    save_document(image,stem)
    image.delete()
    (WORK/'calibrated-faces-finished.json').write_text(json.dumps(
        {'status':'success','texture':stem+'.dds',
         'manual_reference':'TO 1F-117A-1 Figures 1-33 and 1-34',
         'scale_registration':'Existing Blender animations and mainpanel_init.lua',
         'airspeed_range':'0-600 knots, retaining current mod calibration',
         'runtime_verification_pending':True},indent=2))


def remove_unapproved_layout_faces():
    """User's OCIP layout overrides the draft based on existing model bindings."""
    stem='f117_cpt_instrument_panels_albedo'
    image=Gimp.file_load(Gimp.RunMode.NONINTERACTIVE,
                        Gio.File.new_for_path(str(SOURCE/(stem+'.xcf'))))
    for layer in image.get_layers():
        if layer.get_name().startswith('Calibrated gauge faces'):
            image.remove_layer(layer)
    save_document(image,stem)
    image.delete()
    (WORK/'calibrated-faces-finished.json').write_text(json.dumps({
        'status':'excluded_from_replacement_atlas',
        'reason':'User specifies OCIP layout; existing model gauge bindings need reconciliation with that layout.',
        'draft_source':'sources/f117_cpt_calibrated_gauge_faces.svg',
        'runtime_code_modified':False},indent=2))


def finish_data_corrections():
    rows=load_manifest()['textures']
    row=next(r for r in rows if r['original']=='Pilot_F117_nm.dds')
    repair_normal(row)
    DOCUMENTS[row['renamed'][:-4]].delete()
    stem='f117_cpt_display_green_albedo'
    image=Gimp.file_load(Gimp.RunMode.NONINTERACTIVE,
                        Gio.File.new_for_path(str(SOURCE/(stem+'.png'))))
    write_export(image,STAGE/(stem+'.dds'),'file-dds-export',
                 **{'compression-format':'none','format':'rgba8','mipmaps':'generate',
                    'gamma-correct':False,'srgb':False,'flip-image':False})
    image.delete()
    (WORK/'data-corrections-finished.json').write_text('{"status":"success"}')
