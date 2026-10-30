"""Offline F-117 HUD/MFD layout editor. Run with Python 3 + lupa + Pillow."""
from __future__ import annotations

import argparse
import copy
import json
import math
import re
import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from lupa import LuaRuntime
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageTk

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'Cockpit/Scripts'
PAGES = {
    'HUD': SCRIPTS / 'HUD/Indicator/HUD_indication_page.lua',
    'MFD': SCRIPTS / 'MFD/Indicator/MFD_indication_page.lua',
    'Left MFD': SCRIPTS / 'MFD/Indicator/Left/Left_vsd_page.lua',
    'Right MFD': SCRIPTS / 'MFD/Indicator/Right/Right_hsd_page.lua',
}
ENTRIES = {
    'HUD': SCRIPTS / 'HUD/Indicator/HUD_base_page.lua',
    'MFD': SCRIPTS / 'MFD/Indicator/MFD_base_page.lua',
    'Left MFD': SCRIPTS / 'MFD/Indicator/Left/Left_base_page.lua',
    'Right MFD': SCRIPTS / 'MFD/Indicator/Right/Right_base_page.lua',
}
DRAFTS = set()
GEOMETRY_PATH = Path(__file__).with_name('data') / 'cockpit_display_geometry.json'
HUD_PROFILE = SCRIPTS / 'HUD/Indicator/layout_profile.lua'
DCS_LOG = ROOT.parents[2] / 'Logs/dcs.log'


def hud_working_area(log_path=None):
    """Convert accepted angular bounds with scales captured in the DCS HUD state.

    No fallback scale: an invented FOV conversion would give misleading bounds.
    """
    profile=convert(LuaRuntime().execute(HUD_PROFILE.read_text(encoding='utf-8-sig')))
    path=Path(log_path) if log_path is not None else DCS_LOG
    result=dict(profile,boundary=None,units_per_mrad=None)
    if not path.is_file():return result
    with path.open('rb') as stream:
        stream.seek(max(0,path.stat().st_size-1024*1024))
        tail=stream.read().decode('utf-8',errors='replace')
    matches=re.findall(r'F117_HUD_LAYOUT[^\n]*v1 fov_scale=([\d.eE+\-]+) mrad_scale=([\d.eE+\-]+)',tail)
    if not matches:return result
    fov,mrad=map(float,matches[-1])
    if not all(math.isfinite(v) and v>0 for v in (fov,mrad)):return result
    ratio=mrad/fov
    x,y=(v*ratio for v in profile['origin_mrad'])
    w=math.radians(profile['half_width_deg'])*1000*ratio
    h=math.radians(profile['half_height_deg'])*1000*ratio
    result.update(units_per_mrad=ratio,center=(x,y),half_width=w,half_height=h,
                  boundary=[(x-w,y-h),(x+w,y-h),(x+w,y+h),(x-w,y+h)])
    return result


def layout_boundary(mode,units_per_metre=1):
    return hud_working_area()['boundary'] if mode=='HUD' else measured_boundary(mode,units_per_metre)


def default_view(mode):
    if mode=='HUD':
        area=hud_working_area()
        if area['boundary']:
            return max(area['half_width'],area['half_height'])*1.2,area['center']
        return 1.1,(0,-.15)
    if mode in ('Left MFD','Right MFD'):return .058,(0,.002)
    return .09,(0,0)


def measured_surfaces():
    if not GEOMETRY_PATH.is_file():return {}
    return json.loads(GEOMETRY_PATH.read_text(encoding='utf-8'))['surfaces']


def measured_boundary(mode, units_per_metre=1):
    """Physical MFD guide; scale is explicit, not a claimed DCS calibration."""
    surface=measured_surfaces().get(mode)
    if not surface or mode=='HUD':return None
    return [(x*units_per_metre,y*units_per_metre) for x,y in surface['boundary_local_m']]
DEFAULTS = {
    'mainpower': 1, 'HUDBrightness': 1, 'MFD_OVERLAY': 1, 'F117_IRADS_POWER': 1,
    'currentPhase': 8, 'masterMode': 1, 'headingMode': 2, 'ALTITUDE_MODE': 1,
    'altMode': 1, 'RadarAltAvail': 1, 'CURR_IAS': 314, 'GS_HUD': 450,
    'MACH_A': .71, 'machDecimals': 71, 'machWhole': .71, 'ALTITUDE_HUD': 22200,
    'altTape': 16812.45, 'txtAlt': 22200, 'txtRalt': 500, 'AoA': 3,
    'CUR_G': 1, 'HEADING_HUD': 300, 'ROLL_HUD': 0, 'PITCH_HUD': 0,
    'VELVEC_HUD_X': 0, 'VELVEC_HUD_Y': -.05, 'VVI_HUD': -500, 'VVI_SCALE': -500,
    'WHOT_TOGGLE': 1, 'IRADS_ZOOM': 1, 'F117_CCRP_PROFILE': 0,
    'F117_IRADS_LOCK_VALID': 0, 'F117_IRADS_LOCK_RANGE': 4500,
    'F117_RELEASE_STATUS': 3, 'F117_WEAPON_STATION': 1,
    'nextWPRange': 18.4, 'nextWPName': 'D 39', 'nextWPType': 2,
    'F117_RELEASE_CUE_TTG': 30,
    'F117_OCIP_CAS': 314, 'F117_OCIP_ALT': 22200, 'F117_OCIP_HEADING': 300,
    'F117_OCIP_MACH': .71, 'F117_OCIP_VVI': -500,
    'F117_OCIP_VV_X': 0, 'F117_OCIP_VV_Y': -.05, 'F117_OCIP_VV_VALID': 1,
    'F117_OCIP_INS_VALID': 1, 'F117_OCIP_APPROACH': 0, 'F117_OCIP_AOA': .05,
}


def convert(value):
    if hasattr(value, 'keys'):
        keys = list(value.keys())
        if keys and all(isinstance(k, int) for k in keys):
            return [convert(value[k]) for k in range(1, max(keys) + 1)]
        return {k: convert(value[k]) for k in keys}
    return value


def sequence(value):
    return value if isinstance(value, list) else []


def component(values, index, default=0):
    values = sequence(values)
    return values[index] if len(values) > index and values[index] is not None else default


class Model:
    """Executes the actual page, HUD_def and Common_Defs with offline API shims."""
    def __init__(self, mode, source):
        self.mode, self.source = mode, source
        self.path = PAGES[mode]
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute((Path(__file__).with_name('layout_runtime.lua')).read_text())
        g = self.lua.globals()
        if mode == 'HUD':
            # Reproduce the engine's measured ratio for OCIP angular geometry.
            # The physical combiner masks are excluded from this planar preview.
            g._preview_mrad_ratio = hud_working_area()['units_per_mrad'] or 1
            self.lua.execute('''
                function SetScale(s) _preview_scale=s end
                function GetScale()
                    return _preview_scale==MILLYRADIANS and _preview_mrad_ratio or 1
                end
            ''')
        g.LockOn_Options.script_path = SCRIPTS.as_posix() + '/'
        g._tracked = self.path.as_posix()
        self.loaded = set()
        loading = set()

        def load(path):
            path = str(path)
            if path.startswith('__dcs__/'):
                return
            candidate = Path(path).resolve()
            if not candidate.is_relative_to(SCRIPTS.resolve()):
                raise ValueError('Indicator include outside Cockpit/Scripts: ' + path)
            if candidate in loading:
                raise ValueError('Recursive indicator include: ' + path)
            self.loaded.add(candidate)
            loading.add(candidate)
            text = source if candidate == self.path.resolve() else candidate.read_text(encoding='utf-8-sig')
            try:
                return self.lua.execute(text, name='@' + candidate.as_posix())
            finally:
                loading.remove(candidate)

        g.dofile = load
        load(ENTRIES[mode])
        self.elements = convert(g._elements)
        if mode == 'HUD' and g.OCIP_U is not None:
            for element in self.elements:
                element['_coordinate_scale'] = float(g.OCIP_U)
        self.by_name = {e.get('name'): e for e in self.elements}
        self.parameters = sorted({p for e in self.elements
                                  for p in sequence(e.get('element_params')) if isinstance(p, str)})
        self.warnings = set()

    def scene(self, params, show_all=False):
        # Reproduce device-generated ladder positions when scrubbing attitude.
        params = dict(params)
        for degrees in range(-85, 86, 5):
            tag = f'N{-degrees}' if degrees < 0 else f'P{degrees}'
            delta = math.radians(degrees) - params.get('PITCH_HUD', 0)
            visible = abs(delta) < math.radians(80)
            params.setdefault('F117_OCIP_LADDER_' + tag, math.tan(delta) if visible else 0)
            params.setdefault('F117_OCIP_LADDER_VALID_' + tag, int(visible))
        cache = {}
        self.warnings.clear()

        def resolve(e, active=None):
            key = e.get('name', id(e))
            if key in cache:
                return cache[key]
            active = set() if active is None else active
            if key in active:
                raise ValueError('Cyclic element parent: ' + str(key))
            active.add(key)
            pos = e.get('init_pos', [])
            x, y = component(pos, 0), component(pos, 1)
            angle = math.radians(component(e.get('init_rot'), 0))
            visible, opacity = True, 1.0
            text = str(e.get('value', ''))
            vertices = copy.deepcopy(sequence(e.get('vertices')))
            names = sequence(e.get('element_params'))

            def param(index):
                return params.get(names[int(index)], 0) if 0 <= int(index) < len(names) else 0

            for c in sequence(e.get('controllers')):
                if not c:
                    continue
                op = c[0]
                v = param(c[1]) if len(c) > 1 else 0
                if op == 'parameter_in_range':
                    visible &= isinstance(v, (int, float)) and c[2] <= v <= c[3]
                elif op == 'parameter_compare_with_number':
                    visible &= v == c[2]
                elif op == 'compare_parameters':
                    visible &= v == param(c[2])
                elif op == 'opacity_using_parameter':
                    opacity *= max(0, min(1, float(v)))
                elif op == 'move_left_right_using_parameter':
                    x += float(v) * c[2]
                elif op == 'move_up_down_using_parameter':
                    y += float(v) * c[2]
                elif op == 'rotate_using_parameter':
                    angle += float(v) * c[2]
                elif op == 'text_using_parameter':
                    formats = sequence(e.get('formats')) or ['%s']
                    fmt = formats[int(c[2])] if len(c) > 2 and int(c[2]) < len(formats) else formats[0]
                    try:
                        text = fmt % v
                    except (ValueError, TypeError):
                        text = str(v)
                elif op == 'line_object_set_point_using_parameters':
                    i = int(c[1])
                    if i < len(vertices):
                        vertices[i] = [float(param(c[2])) * c[4], float(param(c[3])) * c[5]]
                else:
                    self.warnings.add(str(op))
            if show_all:
                visible, opacity = True, 1
            parent = self.by_name.get(e.get('parent_element'))
            if parent:
                px, py, pa, pv, po, _, _ = resolve(parent, active)
                x, y = px + x*math.cos(pa)-y*math.sin(pa), py+x*math.sin(pa)+y*math.cos(pa)
                angle += pa
                visible &= pv
                opacity *= po
            result = x, y, angle, visible, opacity, text, vertices
            cache[key] = result
            active.remove(key)
            return result

        return [(e, resolve(e)) for e in self.elements]


# Small Lua tokenizer for position edits. Expressions are preserved and offset,
# so positions calculated from constants/loops can be moved as a source group.
TOKEN = re.compile(r'--\[(=*)\[.*?\]\1\]|--[^\n]*|\[(=*)\[.*?\]\2\]|'
                   r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|'
                   r'[A-Za-z_]\w*|(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?|\S', re.S)


def tokens(source):
    return [(m.group(), m.start(), m.end()) for m in TOKEN.finditer(source)
            if not m.group().startswith('--')]


def arguments(ts, opening):
    pairs = {'(': ')', '{': '}', '[': ']'}
    stack, start, result = [], opening + 1, []
    for i in range(opening, len(ts)):
        token = ts[i][0]
        if token in pairs:
            stack.append(pairs[token])
        elif token in pairs.values():
            if not stack or token != stack.pop():
                return []
            if not stack:
                if i > start:
                    result.append((start, i))
                return result
        elif token == ',' and len(stack) == 1:
            result.append((start, i))
            start = i + 1
    return []


def position_spans(source, element):
    """Return source ranges of editable local x/y, or None for generated geometry."""
    ts = tokens(source)
    starts = [0] + [m.end() for m in re.finditer('\n', source)]
    line = int(element.get('_position_line') or element.get('_source_line') or 1)
    low = starts[max(0, min(line-1, len(starts)-1))]
    high = starts[line] if line < len(starts) else len(source)

    def spans(args):
        if len(args) < 2 or any(a == b for a, b in args[:2]):
            return None
        return [(ts[a][1], ts[b-1][2]) for a, b in args[:2]]

    # Explicit element.init_pos = {x, y, z}.
    for i, (word, a, _) in enumerate(ts):
        if low <= a < high and word == 'init_pos' and i+2 < len(ts):
            if ts[i+1][0] == '=' and ts[i+2][0] == '{':
                return spans(arguments(ts, i+2))
    # Calls to the real source helpers, including multiline calls.
    for i, (word, a, _) in enumerate(ts):
        if not (low <= a < high) or i+1 >= len(ts) or ts[i+1][0] != '(':
            continue
        args = arguments(ts, i+1)
        if word in ('text', 'readout', 'group', 'add_text_hud', 'add_text_hud2'):
            return spans(args[1:3])
        if word == 'add_text_hud_param':
            return spans(args[:2])
        if word.startswith('addHUD') and len(args) > 1:
            first, last = args[1]
            if first < last and ts[first][0] == '{':
                return spans(arguments(ts, first))
    return None


def move_source(source, element, dx, dy):
    spans = position_spans(source, element)
    if not spans:
        raise ValueError('This shape has no editable x/y source pair. Use the source pane or select its parent.')
    edits = []
    for (a, b), delta in zip(spans, (dx, dy)):
        # OCIP helper arguments are mrad; mouse deltas are FOV source units.
        # Explicit init_pos assignments already contain source-unit expressions.
        prefix = source[source.rfind('\n',0,a)+1:a]
        if not re.search(r'\binit_pos\s*=',prefix):
            delta /= element.get('_coordinate_scale',1)
        old = source[a:b]
        try:
            new = f'{float(old) + delta:.7g}'
        except ValueError:
            new = f'({old}) + ({delta:.7g})'
        edits.append((a, b, new))
    for a, b, new in reversed(edits):
        source = source[:a] + new + source[b:]
    return source


@dataclass
class Hit:
    element: dict
    box: tuple
    state: tuple


class Renderer:
    def __init__(self):
        self.textures, self.fonts = {}, {}
        self.stroke_glyphs = None

    def texture(self, path):
        if path in self.textures:
            return self.textures[path]
        p = Path(path)
        for suffix in ('', '.tga', '.dds', '.png'):
            q = Path(str(p) + suffix)
            if q.is_file():
                try:
                    # The shipped pitch atlas is 10,000 x 10,000. It is a
                    # trusted local mod asset; downsample the preview cache.
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore', Image.DecompressionBombWarning)
                        atlas=Image.open(q)
                        atlas.thumbnail((4096,4096),Image.Resampling.LANCZOS)
                        self.textures[path] = atlas.convert('RGBA')
                    return self.textures[path]
                except OSError:
                    pass
        self.textures[path] = None
        return None

    def render(self, model, params, size=850, extent=1.1, center=(0, 0),
               show_all=False, grid=True, clipping=True, reference=None, boundary=None):
        scale = size / (2*extent)
        def point(x, y):
            return size/2+(x-center[0])*scale, size/2-(y-center[1])*scale
        image = Image.new('RGBA', (size, size), '#06110d')
        if reference:
            ref, opacity = reference
            ref = ref.convert('RGBA').resize((size, size))
            ref.putalpha(ref.getchannel('A').point(lambda v: int(v*opacity)))
            image.alpha_composite(ref)
        draw = ImageDraw.Draw(image)
        if grid:
            step = 10**math.floor(math.log10(extent/4))
            if extent/step > 20:
                step *= 5
            for i in range(-30, 31):
                x, _ = point(i*step, 0)
                _, y = point(0, i*step)
                draw.line((x, 0, x, size), fill='#132a21')
                draw.line((0, y, size, y), fill='#132a21')
            x, y = point(0, 0)
            draw.line((x, 0, x, size), fill='#2b5640')
            draw.line((0, y, size, y), fill='#2b5640')
        stencil = Image.new('L', (size, size), 0)
        hud_layout=getattr(model,'mode',None)=='HUD'
        if hud_layout:
            # The workbench uses the accepted angular design rectangle, not a
            # 2D rendering of finite-depth glass. Internal tape masks still work.
            if boundary and clipping:
                ImageDraw.Draw(stencil).polygon([point(x,y) for x,y in boundary],fill=2)
            elif not boundary:
                clipping=False
        masks, hits, missing = {}, [], set()
        for e, state in model.scene(params, show_all):
            if str(e.get('name','')).startswith('F117_COMBINER_MASK_'):
                continue
            x, y, angle, visible, opacity, text, vertices = state
            if not visible or opacity <= 0:
                continue
            kind = e.get('_etype', '')
            if kind == 'ceSimple':
                continue
            ca, sa = math.cos(angle), math.sin(angle)
            def world(v):
                vx, vy = component(v, 0), component(v, 1)
                return point(x+vx*ca-vy*sa, y+vx*sa+vy*ca)
            pts = [world(v) for v in vertices]
            origin = point(x, y)
            if pts:
                box = min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)
                if box[2] < -5 or box[0] > size+5 or box[3] < -5 or box[1] > size+5:
                    continue
            else:
                box = (origin[0]-5, origin[1]-5, origin[0]+5, origin[1]+5)
            if not pts and not (-size < origin[0] < 2*size and -size < origin[1] < 2*size):
                continue
            layer = Image.new('RGBA', (size, size))
            ld = ImageDraw.Draw(layer)
            mat = e.get('material') or {}
            color = (80, 255, 135, int(255*opacity))
            if isinstance(mat, dict) and mat.get('color'):
                c = mat['color']
                color = tuple(int(max(0, min(255, component(c, i, 255)))) for i in range(3)) + (int(255*opacity),)
            if kind == 'ceStringPoly':
                # DCS bitmap fonts and font metrics differ; sizes are adjustable
                # in source and remain an approximation in this offline view.
                sd = e.get('stringdefs') or [.007, .007]
                description = mat.get('description', {}) if isinstance(mat, dict) else {}
                stroke_font = description.get('class') == 'ceSLineFont'
                font_size = max(5, min(160, round(component(sd, 0, .007)*scale*(1 if stroke_font else 3))))
                description = mat.get('description', {}) if isinstance(mat, dict) else {}
                bold = 'bold' in str(description.get('ttf', '') or description.get('texture', '')).lower()
                font_key = (font_size, bold)
                if font_key not in self.fonts:
                    try:
                        self.fonts[font_key] = ImageFont.truetype('consolab.ttf' if bold else 'consola.ttf', font_size)
                    except OSError:
                        self.fonts[font_key] = ImageFont.load_default(size=font_size)
                font = self.fonts[font_key]
                # Bound very long off-screen tape strings before allocating.
                text = text[:1200]
                if stroke_font:
                    if self.stroke_glyphs is None:
                        self.stroke_glyphs = json.loads((ROOT/'tools/data/display_stroke_glyphs.json').read_text())
                    glyphs = self.stroke_glyphs
                    height = max(1, component(sd,0)*scale)
                    width = max(1, component(sd,1)*scale)
                    spacing = component(sd,2)*scale
                    tile = Image.new('RGBA', (max(1,math.ceil(len(text)*(width+spacing)+4)),math.ceil(height+4)))
                    td = ImageDraw.Draw(tile)
                    for idx,ch in enumerate(text):
                        if ch == ' ': continue
                        paths = glyphs.get(ch, glyphs.get(ch.upper(),glyphs['?']))
                        for path in paths.split(';'):
                            points = [tuple(float(v) for v in point.split(',')) for point in path.split()]
                            td.line([(2+idx*(width+spacing)+x/13*width,2+y/20*height) for x,y in points],fill=color,width=max(1,round(float(e.get('thickness',.8))*1.5)))
                else:
                    b = font.getbbox(text or ' ')
                    tile = Image.new('RGBA', (max(1,b[2]-b[0]+4), max(1,b[3]-b[1]+4)))
                    ImageDraw.Draw(tile).text((2-b[0], 2-b[1]), text, font=font, fill=color)
                alignment = e.get('alignment', 'CenterCenter')
                # Rotate the text tile around its source anchor.
                ax = 0 if alignment.startswith('Left') else 1 if alignment.startswith('Right') else .5
                ay = 0 if alignment.endswith('Top') else 1 if alignment.endswith('Bottom') else .5
                if abs(angle) > 1e-6:
                    padded = Image.new('RGBA', (tile.width*2, tile.height*2))
                    padded.alpha_composite(tile, (round(tile.width*(1-ax)), round(tile.height*(1-ay))))
                    tile = padded.rotate(math.degrees(angle), Image.Resampling.BICUBIC, expand=True)
                    tx, ty = round(origin[0]-tile.width/2), round(origin[1]-tile.height/2)
                else:
                    tx, ty = round(origin[0]-tile.width*ax), round(origin[1]-tile.height*ay)
                layer.alpha_composite(tile, (tx, ty))
                box = tx, ty, tx+tile.width, ty+tile.height
            elif kind == 'ceSMultiLine' and len(pts)>1:
                indices=sequence(e.get('indices'))
                for i in range(0,len(indices)-1,2):
                    a,b=int(indices[i]),int(indices[i+1])
                    if a<len(pts) and b<len(pts):
                        ld.line([pts[a],pts[b]],fill=color,width=max(1,round(float(e.get('thickness',.8))*1.5)))
            elif kind == 'ceSimpleLineObject' and len(pts) > 1:
                ld.line(pts, fill=color, width=max(1, min(100, round(float(e.get('width') or .002)*scale))))
            elif kind == 'ceTexPoly' and len(pts) >= 4:
                texture = self.texture(mat.get('path', '')) if isinstance(mat, dict) else None
                uv = sequence(e.get('tex_coords'))
                if texture and len(uv) >= 4:
                    # Affine mapping from DCS quad/UV coordinates to the atlas.
                    p0,p1,p3=pts[0],pts[1],pts[3]
                    ux,uy=p1[0]-p0[0],p1[1]-p0[1]
                    vx,vy=p3[0]-p0[0],p3[1]-p0[1]
                    det=ux*vy-uy*vx
                    if abs(det)>1e-9:
                        a,b=vy/det,-vx/det; d,f=-uy/det,ux/det
                        u0,v0=uv[0]; du,dv=uv[1][0]-u0,uv[3][1]-v0
                        coeff=(a*du*texture.width,b*du*texture.width,
                               (u0-du*(a*p0[0]+b*p0[1]))*texture.width,
                               d*dv*texture.height,f*dv*texture.height,
                               (v0-dv*(d*p0[0]+f*p0[1]))*texture.height)
                        sampled=texture.transform((size,size),Image.Transform.AFFINE,coeff,Image.Resampling.BILINEAR)
                        coverage=Image.new('L',(size,size)); ImageDraw.Draw(coverage).polygon(pts,fill=255)
                        # DCS additive atlases may store black backgrounds with opaque alpha.
                        intensity=sampled.convert('L')
                        alpha=ImageChops.multiply(ImageChops.multiply(intensity,sampled.getchannel('A')),coverage)
                        layer=Image.new('RGBA',(size,size),color)
                        layer.putalpha(alpha.point(lambda v:int(v*opacity)))
                elif isinstance(mat,str) and mat.startswith('render_target_'):
                    # Live video is unavailable offline; show an empty sensor backdrop.
                    ld.polygon(pts,fill=(12,18,15,255))
                else:
                    missing.add(mat.get('path','unknown') if isinstance(mat,dict) else str(mat))
                    ld.line(pts+[pts[0]],fill=(80,100,90,150),width=1)
            elif len(pts) >= 3:
                indices=sequence(e.get('indices'))
                if indices:
                    for i in range(0,len(indices)-2,3):
                        tri=[pts[int(j)] for j in indices[i:i+3] if int(j)<len(pts)]
                        if len(tri)==3:
                            ld.polygon(tri,fill=color)
                else:
                    ld.polygon(pts,fill=color)
            level = int(e.get('level') or 0)
            relation = e.get('h_clip_relation', 1)
            allowed = None
            if clipping and relation in (1,3,4):
                if level not in masks:
                    masks[level]=stencil.point(lambda v:255 if v==level else 0)
                allowed=masks[level]
            if clipping and relation in (2,3,4,5,6):
                shape=Image.new('L',(size,size))
                if pts:
                    sd=ImageDraw.Draw(shape)
                    indices=sequence(e.get('indices'))
                    if indices:
                        for i in range(0,len(indices)-2,3):
                            tri=[pts[int(j)] for j in indices[i:i+3] if int(j)<len(pts)]
                            if len(tri)==3:sd.polygon(tri,fill=255)
                    else:sd.polygon(pts,fill=255)
                if relation in (3,4):
                    equal=stencil.point(lambda v:255 if v==level else 0)
                    shape=ImageChops.multiply(shape,equal)
                target=level if relation==2 else level+1 if relation in (3,5) else max(0,level-1)
                stencil.paste(target,mask=shape)
                masks.clear()
            if e.get('isvisible') is False:
                continue
            if allowed is not None:
                layer.putalpha(ImageChops.multiply(layer.getchannel('A'),allowed))
            alpha_box=layer.getchannel('A').getbbox()
            if alpha_box:
                image.alpha_composite(layer)
                hits.append(Hit(e, alpha_box, state))
        if boundary:
            edge=[point(x,y) for x,y in boundary]
            outside=Image.new('L',(size,size),100)
            ImageDraw.Draw(outside).polygon(edge,fill=0)
            shade=Image.new('RGBA',(size,size),(0,0,0,0));shade.putalpha(outside)
            image.alpha_composite(shade)
            ImageDraw.Draw(image).line(edge+[edge[0]],fill='#f5b95d',width=2)
        return image, hits, missing


class Editor:
    def __init__(self, root):
        import tkinter as tk
        from tkinter import ttk
        self.tk, self.ttk, self.root = tk, ttk, root
        root.title('F-117 Layout Studio | HUD + MFD')
        root.geometry('1500x940')
        self.mode=tk.StringVar(value='HUD'); self.status=tk.StringVar()
        self.grid=tk.BooleanVar(value=True); self.clip=tk.BooleanVar(value=True)
        self.all=tk.BooleanVar(value=False); self.snap=tk.DoubleVar(value=.005)
        self.boundary=tk.BooleanVar(value=True); self.guide_scale=tk.DoubleVar(value=1)
        self.extent=tk.DoubleVar(value=1.1)
        self.reference_opacity=tk.DoubleVar(value=.25)
        self.reference_image=None; self.params=dict(DEFAULTS); self.renderer=Renderer()
        self.models={}; self.sources={}; self.disk={}; self.undo_stack=[]
        self.hits=[]; self.selected=None; self.drag=None; self.pending=False
        self.center=(0,0); self.size=800
        bar=ttk.Frame(root,padding=8); bar.pack(fill='x')
        ttk.Label(bar,text='F-117  LAYOUT STUDIO',font=('Segoe UI',12,'bold')).pack(side='left',padx=(0,20))
        picker=ttk.Combobox(bar,textvariable=self.mode,values=list(PAGES),state='readonly',width=11)
        picker.pack(side='left'); picker.bind('<<ComboboxSelected>>',lambda _:self.switch())
        for label,fn in [('Reload',self.reload),('Preview source',self.apply_source),('Undo',self.undo),
                         ('Save Lua',self.save),('Export PNG',self.export),('Reference image',self.reference)]:
            ttk.Button(bar,text=label,command=fn).pack(side='left',padx=3)
        body=ttk.Panedwindow(root,orient='horizontal'); body.pack(fill='both',expand=True)
        left=ttk.Frame(body,width=255,padding=8); body.add(left,weight=0)
        middle=ttk.Frame(body); body.add(middle,weight=4)
        right=ttk.Frame(body,width=420,padding=8); body.add(right,weight=2)
        ttk.Label(left,text='PREVIEW',font=('Segoe UI',10,'bold')).pack(anchor='w')
        for label,var in [('Grid',self.grid),('Approximate stencil clipping',self.clip),('Show all modes / hidden symbols',self.all)]:
            ttk.Checkbutton(left,text=label,variable=var,command=self.redraw).pack(anchor='w')
        ttk.Checkbutton(left,text='HUD / MFD working boundary (amber)',variable=self.boundary,command=self.redraw).pack(anchor='w')
        row=ttk.Frame(left);row.pack(fill='x',pady=5)
        ttk.Label(row,text='Guide units / metre').pack(side='left')
        scale_entry=ttk.Entry(row,textvariable=self.guide_scale,width=8);scale_entry.pack(side='right')
        self.guide_scale_entry=scale_entry
        scale_entry.bind('<Return>',lambda _:self.redraw())
        self.measurement_text=tk.StringVar()
        ttk.Label(left,textvariable=self.measurement_text,wraplength=245,foreground='#765b28').pack(anchor='w')
        ttk.Button(left,text='View measured glass / screen shapes',command=self.measurements).pack(fill='x',pady=5)
        row=ttk.Frame(left);row.pack(fill='x',pady=5)
        ttk.Label(row,text='View half-width').pack(side='left')
        view=ttk.Entry(row,textvariable=self.extent,width=8);view.pack(side='right');view.bind('<Return>',lambda _:self.redraw())
        row=ttk.Frame(left);row.pack(fill='x')
        ttk.Label(row,text='Drag snap (0 = off)').pack(side='left')
        ttk.Entry(row,textvariable=self.snap,width=8).pack(side='right')
        ttk.Button(left,text='Centre view / reset zoom',command=self.reset_view).pack(fill='x',pady=5)
        ttk.Label(left,text='REFERENCE OPACITY').pack(anchor='w',pady=(10,0))
        ttk.Scale(left,from_=0,to=1,variable=self.reference_opacity,command=lambda _:self.queue_draw()).pack(fill='x')
        ttk.Button(left,text='Remove reference',command=self.clear_reference).pack(fill='x')
        ttk.Label(left,text='PARAMETERS',font=('Segoe UI',10,'bold')).pack(anchor='w',pady=(15,5))
        self.filter=tk.StringVar(); entry=ttk.Entry(left,textvariable=self.filter);entry.pack(fill='x')
        self.filter.trace_add('write',lambda *_:self.fill_params())
        self.param_list=tk.Listbox(left,font=('Consolas',9),exportselection=False,width=32)
        self.param_list.pack(fill='both',expand=True,pady=5)
        self.param_list.bind('<<ListboxSelect>>',self.select_param)
        self.param_value=tk.StringVar(); pe=ttk.Entry(left,textvariable=self.param_value);pe.pack(fill='x')
        pe.bind('<Return>',lambda _:self.set_param())
        ttk.Button(left,text='Set parameter',command=self.set_param).pack(fill='x',pady=4)
        ttk.Label(left,text='Roll/pitch parameters use radians.\nMissing parameter values default to 0.',foreground='#666666').pack(anchor='w')
        self.canvas=tk.Canvas(middle,bg='#06110d',highlightthickness=0)
        self.canvas.pack(fill='both',expand=True)
        self.canvas.bind('<Configure>',lambda _:self.queue_draw())
        self.canvas.bind('<ButtonPress-1>',self.press)
        self.canvas.bind('<B1-Motion>',self.motion)
        self.canvas.bind('<ButtonRelease-1>',self.release)
        self.canvas.bind('<MouseWheel>',self.zoom)
        self.canvas.bind('<ButtonPress-2>',self.pan_start)
        self.canvas.bind('<B2-Motion>',self.pan_move)
        self.inspector=tk.StringVar(value='Click a symbol to inspect it. Drag to move its source position.')
        ttk.Label(right,textvariable=self.inspector,wraplength=400,justify='left').pack(fill='x',pady=(0,8))
        ttk.Button(right,text='Select parent / move a group',command=self.parent).pack(fill='x')
        ttk.Label(right,text='LUA SOURCE  |  Ctrl+Enter previews, Ctrl+S saves').pack(anchor='w',pady=(12,5))
        self.code=tk.Text(right,wrap='none',undo=True,font=('Consolas',10),tabs=('4c',))
        scroll=ttk.Scrollbar(right,command=self.code.yview);scroll.pack(side='right',fill='y')
        self.code.configure(yscrollcommand=scroll.set);self.code.pack(fill='both',expand=True)
        self.code.tag_configure('source_line',background='#d8efdc')
        self.code.bind('<Control-Return>',lambda _:self.apply_source())
        self.code.bind('<Control-s>',lambda _:self.save())
        ttk.Label(root,textvariable=self.status,padding=7,wraplength=1450).pack(fill='x')
        root.protocol('WM_DELETE_WINDOW',self.close)
        self.switch()

    def message(self, text):
        self.status.set(text)

    def text(self):
        return self.code.get('1.0','end-1c')

    def dirty(self):
        return any(s!=self.disk.get(m) for m,s in self.sources.items()) or self.text()!=self.sources.get(self.mode.get(),'')

    def switch(self):
        if hasattr(self,'current'):
            self.sources[self.current]=self.text()
        self.current=self.mode.get()
        if self.current not in self.sources:
            self.disk[self.current]=PAGES[self.current].read_text(encoding='utf-8-sig')
            self.sources[self.current]=self.disk[self.current]
        self.code.delete('1.0','end');self.code.insert('1.0',self.sources[self.current])
        self.selected=None;self.reset_view();self.compile()

    def compile(self):
        try:
            model=Model(self.current,self.text())
        except Exception as exc:
            self.message('Lua error - last successful preview retained: '+str(exc));return False
        self.models[self.current]=model;self.sources[self.current]=self.text()
        self.fill_params();self.redraw()
        return True

    def apply_source(self):
        old=self.sources.get(self.current,'')
        if old!=self.text():self.undo_stack.append((self.current,old))
        self.compile()

    def fill_params(self):
        if not hasattr(self,'current') or self.current not in self.models:return
        needle=self.filter.get().lower()
        self.param_names=[p for p in self.models[self.current].parameters if needle in p.lower()]
        self.param_list.delete(0,'end')
        for name in self.param_names:self.param_list.insert('end',f'{name} = {self.params.get(name,0)}')

    def select_param(self,_=None):
        sel=self.param_list.curselection()
        if sel:
            self.active_param=self.param_names[sel[0]]
            self.param_value.set(str(self.params.get(self.active_param,0)))

    def set_param(self):
        if not hasattr(self,'active_param'):return
        value=self.param_value.get()
        try:value=float(value)
        except ValueError:pass
        self.params[self.active_param]=value
        self.fill_params();self.redraw()

    def reset_view(self):
        extent,self.center=default_view(self.mode.get())
        self.extent.set(extent)
        self.queue_draw()

    def queue_draw(self):
        if not self.pending:
            self.pending=True;self.root.after(70,self.redraw)

    def redraw(self):
        self.pending=False
        model=self.models.get(getattr(self,'current',''))
        if not model:return
        try:
            extent=float(self.extent.get())
            if extent<=0:raise ValueError('View half-width must be positive')
            self.size=max(250,min(1200,self.canvas.winfo_width(),self.canvas.winfo_height()))
            ref=(self.reference_image,self.reference_opacity.get()) if self.reference_image else None
            self.preview,self.hits,missing=self.renderer.render(model,self.params,self.size,extent,self.center,
                self.all.get(),self.grid.get(),self.clip.get(),ref,
                layout_boundary(self.current,self.guide_scale.get()) if self.boundary.get() else None)
            self.guide_scale_entry.configure(state='disabled' if self.current=='HUD' else 'normal')
            measurements=measured_surfaces()
            surface=measurements.get(self.current)
            if surface:
                self.measurement_text.set(f"Mesh: {surface['width_m']*1000:.1f} x {surface['height_m']*1000:.1f} mm\n"
                                          'Physical guide; DCS unit scale unverified.')
            elif self.current=='HUD' and measurements:
                area=hud_working_area()
                if area['boundary']:
                    lo,hi=area['boundary'][0],area['boundary'][2]
                    self.measurement_text.set(f"HUD working area: {2*area['half_width_deg']:g} x {2*area['half_height_deg']:g} deg\n"
                        f"Angular centre: {area['origin_mrad']} mrad\n"
                        f"Source X: {lo[0]:.6g} to {hi[0]:.6g}\nSource Y: {lo[1]:.6g} to {hi[1]:.6g}\n"
                        'FOV conversion read from DCS. Glass clipping remains in-game.')
                else:
                    self.measurement_text.set('HUD profile: 20 x 15 deg, centre -50 mrad Y.\n'
                        'Reload the aircraft once in DCS, then click Centre view here. '
                        'Waiting for the engine FOV conversion in dcs.log; no guessed boundary is drawn.')
            self.photo=ImageTk.PhotoImage(self.preview)
            self.canvas.delete('all')
            self.offset=((self.canvas.winfo_width()-self.size)/2,(self.canvas.winfo_height()-self.size)/2)
            self.canvas.create_image(*self.offset,image=self.photo,anchor='nw')
            self.selection_box()
            note=f'{self.current}: {len(model.elements)} elements, {len(self.hits)} visible. '
            if self.current in DRAFTS:note+='DRAFT PAGE: no cockpit indicator registration yet. '
            note+='Drag = move source group; wheel = zoom; middle drag = pan. '
            note+='Font metrics, 3D optics and camera imagery are approximate.'
            if self.current=='HUD':note+=' HUD clipping preview uses the working rectangle, not head/VR glass projection.'
            if missing:note+=f' Missing texture atlases: {len(missing)} (grey outlines).'
            if model.warnings:note+=' Unsupported controllers: '+', '.join(sorted(model.warnings))
            self.message(note)
        except Exception as exc:self.message('Preview error: '+str(exc))

    def selection_box(self):
        self.canvas.delete('selection')
        if not self.selected:return
        e=self.selected.element
        line=int(e.get('_position_line') or e.get('_source_line') or 1)
        parent=e.get('parent_element','none')
        editable=position_spans(self.text(),e)
        self.inspector.set(f"{e.get('_etype')} | {e.get('name')}\nSource line {line} | parent: {parent}\n"
                           +('Drag edits this source position; loops/shared calls move together.' if editable else
                             'Use source pane for this shape, or select its parent.')+
                           '\nParams: '+', '.join(sequence(e.get('element_params'))))
        box=self.selected.box
        self.canvas.create_rectangle(box[0]+self.offset[0]-3,box[1]+self.offset[1]-3,
            box[2]+self.offset[0]+3,box[3]+self.offset[1]+3,outline='#ffca64',width=2,tags='selection')

    def press(self,event):
        x,y=event.x-self.offset[0],event.y-self.offset[1]
        choices=[h for h in self.hits if h.box[0]-5<=x<=h.box[2]+5 and h.box[1]-5<=y<=h.box[3]+5]
        group=self.selected if self.selected and self.selected.element.get('_etype')=='ceSimple' else None
        if group and group.box[0]-5<=x<=group.box[2]+5 and group.box[1]-5<=y<=group.box[3]+5:
            self.selected=group
        elif choices:
            self.selected=min(choices,key=lambda h:max(1,h.box[2]-h.box[0])*max(1,h.box[3]-h.box[1]))
        else:return
        self.selection_box()
        e=self.selected.element
        line=int(e.get('_position_line') or e.get('_source_line') or 1)
        self.code.tag_remove('source_line','1.0','end');self.code.tag_add('source_line',f'{line}.0',f'{line+1}.0')
        self.code.see(f'{line}.0')
        self.drag=(event.x,event.y,self.text(),self.selected)

    def motion(self,event):
        if self.drag:
            self.canvas.delete('selection')
            b=self.drag[3].box
            self.canvas.create_rectangle(b[0]+self.offset[0]-3,b[1]+self.offset[1]-3,
                b[2]+self.offset[0]+3,b[3]+self.offset[1]+3,outline='#ffca64',width=2,tags='selection')
            self.canvas.move('selection',event.x-self.drag[0],event.y-self.drag[1])

    def release(self,event):
        if not self.drag:return
        sx,sy,source,hit=self.drag;self.drag=None
        scale=self.size/(2*self.extent.get())
        dx,dy=(event.x-sx)/scale,-(event.y-sy)/scale
        if abs(event.x-sx)+abs(event.y-sy)<3:return
        # Translate world drag back through the parent rotation.
        model=self.models[self.current];parent=model.by_name.get(hit.element.get('parent_element'))
        if parent:
            states={id(e):s for e,s in model.scene(self.params,self.all.get())}
            a=states[id(parent)][2]
            dx,dy=dx*math.cos(a)+dy*math.sin(a),-dx*math.sin(a)+dy*math.cos(a)
        snap=self.snap.get()
        if snap>0:dx,dy=round(dx/snap)*snap,round(dy/snap)*snap
        try:new=move_source(source,hit.element,dx,dy)
        except ValueError as exc:self.selection_box();self.message(str(exc));return
        self.undo_stack.append((self.current,source))
        self.code.delete('1.0','end');self.code.insert('1.0',new)
        self.selected=None;self.compile()

    def parent(self):
        if not self.selected:return
        e=self.models[self.current].by_name.get(self.selected.element.get('parent_element'))
        if e:
            self.selected=Hit(e,self.selected.box,self.selected.state);self.selection_box()

    def zoom(self,event):
        self.extent.set(max(.005,min(50,self.extent.get()*(.85 if event.delta>0 else 1/.85))))
        self.queue_draw()

    def pan_start(self,event):self.pan=(event.x,event.y,self.center)

    def pan_move(self,event):
        x,y,c=self.pan;s=self.size/(2*self.extent.get())
        self.center=(c[0]-(event.x-x)/s,c[1]+(event.y-y)/s);self.queue_draw()

    def undo(self):
        if not self.undo_stack:return
        mode,source=self.undo_stack.pop()
        if mode!=self.current:
            self.mode.set(mode);self.switch()
        self.code.delete('1.0','end');self.code.insert('1.0',source);self.compile()

    def save(self):
        from tkinter import messagebox
        if not self.compile():return
        path=PAGES[self.current]
        on_disk=path.read_text(encoding='utf-8-sig')
        if on_disk!=self.disk[self.current]:
            messagebox.showerror('File changed on disk','Reload before saving: this Lua file was changed outside the editor.');return
        if self.text()==on_disk:self.message('No changes to save.');return
        folder=ROOT/'tools/layout_editor_backups'/datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        folder.mkdir(parents=True,exist_ok=True)
        (folder/path.name).write_bytes(path.read_bytes())
        temp=path.with_suffix('.lua.layout-tmp')
        # Preserve the original file's BOM/newline style.
        raw=path.read_bytes();newline='\r\n' if b'\r\n' in raw else '\n'
        output=self.text().replace('\r\n','\n').replace('\n',newline).encode('utf-8')
        if raw.startswith(b'\xef\xbb\xbf'):output=b'\xef\xbb\xbf'+output
        temp.write_bytes(output);temp.replace(path)
        self.disk[self.current]=self.text()
        self.message('Saved '+str(path.relative_to(ROOT))+' | Backup: '+str(folder.relative_to(ROOT)))

    def reload(self):
        from tkinter import messagebox
        if self.text()!=self.disk.get(self.current) and not messagebox.askyesno('Discard edits?', 'Reload this page from disk and discard its unsaved edits?'):return
        self.disk[self.current]=PAGES[self.current].read_text(encoding='utf-8-sig')
        self.code.delete('1.0','end');self.code.insert('1.0',self.disk[self.current]);self.compile()

    def reference(self):
        from tkinter import filedialog
        path=filedialog.askopenfilename(title='Choose a cropped HUD/MFD reference',filetypes=[('Images','*.png *.jpg *.jpeg *.bmp *.tga'),('All files','*.*')])
        if path:
            try:self.reference_image=Image.open(path).convert('RGBA');self.redraw()
            except OSError as exc:self.message(str(exc))

    def clear_reference(self):self.reference_image=None;self.redraw()

    def measurements(self):
        path=ROOT/'docs/assets/cockpit-display-boundaries.png'
        if not path.is_file():
            self.message('Measurement diagram is not available yet.');return
        window=self.tk.Toplevel(self.root);window.title('Measured cockpit surfaces | millimetres')
        chart=Image.open(path);chart.thumbnail((1400,900),Image.Resampling.LANCZOS)
        photo=ImageTk.PhotoImage(chart)
        label=self.tk.Label(window,image=photo);label.image=photo;label.pack()

    def export(self):
        from tkinter import filedialog
        path=filedialog.asksaveasfilename(defaultextension='.png',initialfile=self.current.lower()+'-layout.png',filetypes=[('PNG','*.png')])
        if path:self.preview.save(path);self.message('Exported '+path)

    def close(self):
        from tkinter import messagebox
        if self.dirty() and not messagebox.askyesno('Unsaved layouts','Close and discard unsaved layout changes?'):return
        self.root.destroy()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render',choices=list(PAGES),help='Render to PNG without opening the editor')
    parser.add_argument('--output',type=Path,default=ROOT/'tmp/layout-preview.png')
    parser.add_argument('--params',type=Path,help='JSON object of sample DCS parameter values')
    args=parser.parse_args()
    if args.render:
        params=dict(DEFAULTS)
        if args.params:params.update(json.loads(args.params.read_text()))
        model=Model(args.render,PAGES[args.render].read_text(encoding='utf-8-sig'))
        extent,center=default_view(args.render)
        image,hits,missing=Renderer().render(model,params,extent=extent,center=center,
                                            boundary=layout_boundary(args.render))
        args.output.parent.mkdir(parents=True,exist_ok=True);image.save(args.output)
        print(f'{args.render}: {len(model.elements)} elements; {len(hits)} visible; {len(missing)} missing atlases')
        print(args.output)
        if args.render=='HUD' and not hud_working_area()['boundary']:
            print('HUD angular boundary pending: reload the aircraft in DCS to capture its FOV conversion.')
    else:
        import tkinter as tk
        root=tk.Tk();Editor(root);root.mainloop()


if __name__=='__main__':main()
