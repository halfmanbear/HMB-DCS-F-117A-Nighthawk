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
    'Left EO': SCRIPTS / 'MFD/Indicator/Left/Left_eo_page.lua',
    'Central Map': SCRIPTS / 'MFD/Indicator/Map/Map_page.lua',
    'DEP': SCRIPTS / 'DEP/Indicator/DEP_page.lua',
}
ENTRIES = {
    'HUD': SCRIPTS / 'HUD/Indicator/HUD_base_page.lua',
    'MFD': SCRIPTS / 'MFD/Indicator/MFD_base_page.lua',
    'Left MFD': SCRIPTS / 'MFD/Indicator/Left/Left_base_format.lua',
    'Right MFD': SCRIPTS / 'MFD/Indicator/Right/Right_base_format.lua',
    'Left EO': SCRIPTS / 'MFD/Indicator/Left/Left_eo_page.lua',
    'Central Map': SCRIPTS / 'MFD/Indicator/Map/Map_base_page.lua',
    'DEP': SCRIPTS / 'DEP/Indicator/DEP_base_page.lua',
}
# Pages that share a physical screen with another page, and per-page sample values.
SURFACES = {'Central Map': 'MFD', 'Left EO': 'Left MFD'}
# DEP sample: VNAV and SRCH engaged, as in the reference frames.
MODE_PARAMS = {'Left EO': {'F117_LEFT_EO': 1}, 'DEP': {'F117_DEP_VNAV': 1, 'F117_DEP_SRCH': 1}}
# Symbols come from another page file, so position/colour edits belong to that page.
PREVIEW_ONLY = {'Left EO'}
# Physical screens and the pages each can show. Page labels map to the page key in PAGES.
# The VSD, MAP and HSD formats are shared by both CMDIs; EO/IRADS is left CMDI and centre only.
SCREENS = {
    'HUD': {'HUD': 'HUD'},
    'Left CMDI (MFD)': {'VSD': 'Left MFD', 'EO (IRADS)': 'Left EO', 'MAP': 'Central Map', 'HSD': 'Right MFD'},
    'Central Sensor Display': {'IRADS': 'MFD'},
    'Right CMDI (MFD)': {'VSD': 'Left MFD', 'MAP': 'Central Map', 'HSD': 'Right MFD'},
    'Data Entry Panel (DEP)': {'MAIN MENU': 'DEP'},
}
SCREEN_SURFACE = {'HUD': None, 'Left CMDI (MFD)': 'Left MFD', 'Central Sensor Display': 'MFD',
                  'Right CMDI (MFD)': 'Right MFD', 'Data Entry Panel (DEP)': 'DEP'}
# Screen shown first when a page key is selected without a screen (live default formats).
DEFAULT_SCREEN = {'HUD': 'HUD', 'MFD': 'Central Sensor Display', 'Left MFD': 'Left CMDI (MFD)',
                  'Left EO': 'Left CMDI (MFD)', 'Right MFD': 'Right CMDI (MFD)', 'Central Map': 'Right CMDI (MFD)',
                 'DEP': 'Data Entry Panel (DEP)'}
# CMDI_formats.lua selection ids: 0 VSD, 1 EO, 2 MAP, 3 HSD.
FORMAT_IDS = {'Left MFD': 0, 'Left EO': 1, 'Central Map': 2, 'Right MFD': 3}
GEOMETRY_PATH = Path(__file__).with_name('data') / 'cockpit_display_geometry.json'
# Reference photo folders offered by the Reference image dialog, per page.
REFERENCES = ROOT / 'docs/reference/CockpitImages'
REFERENCE_DIRS = {'HUD': 'HUD', 'MFD': 'IRADS', 'Left EO': 'IRADS', 'Left MFD': 'CMDI_VSD',
                  'Right MFD': 'CMDI_HSD', 'Central Map': 'CMDI_Map',
                  'DEP': 'DEP(DATA_ENTRY_PANEL)/rectified'}
# Screens far from square: a reference cropped to the glass is fitted to the
# measured glass instead of being stretched over the square preview.
GLASS_FIT_REFERENCE = {'Data Entry Panel (DEP)'}
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


def reference_fit(screen,units_per_metre=1):
    """Glass bounding box in source units for GLASS_FIT_REFERENCE screens, else None."""
    if screen not in GLASS_FIT_REFERENCE:return None
    surface=measured_surfaces().get(SCREEN_SURFACE[screen])
    if not surface:return None
    (x0,y0),(x1,y1)=surface['bounds_local_m']
    return x0*units_per_metre,y0*units_per_metre,x1*units_per_metre,y1*units_per_metre


def layout_boundary(mode,units_per_metre=1,screen=None):
    return hud_working_area()['boundary'] if mode=='HUD' else measured_boundary(mode,units_per_metre,screen)


def context_params(mode,screen=None):
    """Sample parameters that select this page's format on its screen."""
    params={'F117_LEFT_EO':0,**MODE_PARAMS.get(mode,{})}
    if screen=='Right CMDI (MFD)' and mode in FORMAT_IDS:params['F117_RIGHT_FORMAT']=FORMAT_IDS[mode]
    return params


def page_scale(mode,screen=None):
    """CMDI_formats.lua draws the centre-sized MAP source scaled to fit a side screen."""
    if mode!='Central Map' or screen not in ('Left CMDI (MFD)','Right CMDI (MFD)'):return 1
    surfaces=measured_surfaces();side=surfaces.get(SCREEN_SURFACE[screen]);centre=surfaces.get('MFD')
    if not side or not centre:return 1
    def span(surface):
        xs,ys=zip(*surface['boundary_local_m']);return max(xs)-min(xs),max(ys)-min(ys)
    (sw,sh),(cw,ch)=span(side),span(centre)
    return .98*min(sw/cw,sh/ch)


def default_view(mode,screen=None):
    if mode=='HUD':
        area=hud_working_area()
        if area['boundary']:
            return max(area['half_width'],area['half_height'])*1.2,area['center']
        return 1.1,(0,-.15)
    if mode=='DEP':return .085,(0,0)
    scale=page_scale(mode,screen)
    if mode in ('Left MFD','Right MFD','Left EO') or scale!=1:return .058/scale,(0,.002/scale)
    return .09,(0,0)


def measured_surfaces():
    if not GEOMETRY_PATH.is_file():return {}
    return json.loads(GEOMETRY_PATH.read_text(encoding='utf-8'))['surfaces']


def measured_boundary(mode, units_per_metre=1, screen=None):
    """Physical MFD guide; scale is explicit, not a claimed DCS calibration.

    With a screen, the guide is that screen's glass in this page's source units."""
    name=SCREEN_SURFACE.get(screen) if screen else SURFACES.get(mode,mode)
    surface=measured_surfaces().get(name)
    if not surface or mode=='HUD':return None
    k=units_per_metre/page_scale(mode,screen)
    return [(x*k,y*k) for x,y in surface['boundary_local_m']]
DEFAULTS = {
    'F117_LEFT_EO': 0, 'F117_RIGHT_FORMAT': 2, 'ONE': 1, 'F117_IRADS_CONTRAST_BAND': 45,
    'F117_MAP_VALID': 1, 'F117_MAP_RANGE_TEXT': '25 NM', 'F117_MAP_ORIENTATION_TEXT': 'CNUP',
    'F117_MAP_GS_TEXT': 'GS 450', 'F117_MAP_HDG_TEXT': 'HDG 300 T',
    'F117_MAP_POSITION_TEXT': 'POSITION UNAVAILABLE',
    'mainpower': 1, 'HUDBrightness': 1, 'F117_HUD_DRAW_BRIGHTNESS': 1, 'F117_DEP_DRAW_BRIGHTNESS': 1, 'F117_IRADS_DRAW_BRIGHTNESS': .45, 'MFD_OVERLAY': 1, 'F117_IRADS_POWER': 1,
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
    'F117_IRADS_ALT_TEXT': 'ALT 19620', 'F117_IRADS_RANGE_TEXT': 'LR -----',
    'F117_IRADS_TIME_TEXT': 'TTI --:--', 'F117_IRADS_MAG_TEXT': 'WIDE',
    'F117_IRADS_COORD_TEXT': '', 'F117_IRADS_BRIGHTNESS': .45,
    'F117_OCIP_CAS': 314, 'F117_OCIP_ALT': 22200, 'F117_OCIP_HEADING': 300,
    'F117_OCIP_MACH': .71, 'F117_OCIP_VVI': -500,
    'F117_OCIP_VV_X': 0, 'F117_OCIP_VV_Y': -.05, 'F117_OCIP_VV_VALID': 1,
    'F117_OCIP_INS_VALID': 1, 'F117_OCIP_APPROACH': 0, 'F117_OCIP_AOA': .05,
}


DEFAULTS.update(F117_MAP_SOURCE_VISIBLE=0,F117_MAP_FUNCTION_TEXT='FUNC',F117_MAP_FUNCTION=0,F117_MAP_MANUAL=0,F117_MAP_DATABASE_TEXT='DMAP',
    F117_MAP_CRS_TEXT='CRS 300',F117_MAP_RANGE=25,F117_MAP_TDC_TEXT='TDC0',
    F117_MAP_BGD_TEXT='BGD 0',F117_MAP_REFEL_TEXT='REFEL',F117_MAP_ELEVATION_FT=3000)
# Mission route readouts (Systems/Navigation.lua); sample values for previews.
DEFAULTS.update(F117_NAV_VALID=1,F117_NAV_REL_COURSE=0,F117_NAV_D_TEXT='D  03',
    F117_NAV_TTG_TEXT='TTG 13:47',F117_NAV_RNG_TEXT='RNG 108.4',F117_NAV_CRS_TEXT='CRS 345')

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
    def __init__(self, mode, source, screen=None):
        self.mode, self.source = mode, source
        self.screen = screen or DEFAULT_SCREEN[mode]
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
        # The MAP page sizes its chart to the CMDI glass it is shown on (CMDI_formats.lua).
        side = {'Left CMDI (MFD)': 'left', 'Right CMDI (MFD)': 'right'}.get(self.screen)
        if mode == 'Central Map' and side:
            g.F117_CMDI_SIDE = side
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
                elif op == 'set_contrast_raw':
                    pass  # Native video shader; the editor has no live camera texture.
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
                # Black brightness dimmers cover the whole display; forcing them
                # opaque would black out the preview, so they keep their opacity.
                mat = e.get('material')
                rgb = sequence(mat.get('color'))[:3] if isinstance(mat, dict) else []
                dimmer = rgb == [0, 0, 0] and any(
                    c and c[0] == 'opacity_using_parameter' for c in sequence(e.get('controllers')))
                visible = True
                if not dimmer:
                    opacity = 1
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
        if word in ('text', 'readout', 'label', 'param_label', 'group', 'add_text_hud', 'add_text_hud2'):
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


def _expression(value, factor=1, offset=0):
    try:
        return f'{float(value)*factor+offset:.10g}'
    except ValueError:
        result=value
        if factor!=1: result=f'({result}) * {factor:.10g}'
        if abs(offset)>1e-12: result=f'({result}) + ({offset:.10g})'
        return result


def source_call(source, element):
    ts=tokens(source)
    line=int(element.get('_source_line') or 1)
    starts=[0]+[m.end() for m in re.finditer('\n',source)]
    low=starts[max(0,min(line-1,len(starts)-1))]
    high=starts[line] if line<len(starts) else len(source)
    names={'text','readout','label','param_label','group','line','poly','box','circle','add_text_hud','add_text_hud2','add_text_hud_param'}
    for i,(word,start,_) in enumerate(ts[:-1]):
        if low<=start<high and word in names and ts[i+1][0]=='(':
            args=arguments(ts,i+1)
            return word,[(ts[a][1],ts[b-1][2]) if a<b else None for a,b in args]
    return None,[]



def lua_literal(value):
    if value is None:return 'nil'
    if isinstance(value,bool):return 'true' if value else 'false'
    if isinstance(value,(int,float)):return repr(value)
    if isinstance(value,str):return json.dumps(value,ensure_ascii=False)
    if isinstance(value,list):return '{'+','.join(lua_literal(v) for v in value)+'}'
    if isinstance(value,dict):return '{'+','.join('['+lua_literal(k)+']='+lua_literal(v) for k,v in value.items())+'}'
    raise ValueError('Unsupported material definition.')


def recolor_selection(source, elements, model, hex_color):
    """Rebuild each source call's own material, keeping its font/texture and alpha."""
    if not re.fullmatch(r'#?[0-9a-fA-F]{6}',hex_color.strip()):
        raise ValueError('Enter a six-digit hex color, for example #00FF00.')
    value=hex_color.strip().lstrip('#')
    rgb=[int(value[i:i+2],16) for i in (0,2,4)]
    chosen={e['name'] for e in elements}
    work=[]
    for e in model.elements:
        parent=e.get('parent_element');seen=set()
        while parent in model.by_name and parent not in seen and parent not in chosen:
            seen.add(parent);parent=model.by_name[parent].get('parent_element')
        if e['name'] in chosen or parent in chosen:
            if e.get('material') and e.get('isvisible') is not False:work.append(e)
    edits={}
    ts=tokens(source)
    for e in work:
        word,args=source_call(source,e)
        if not word or word=='group' or not args:
            raise ValueError('This element needs its material edited in Lua; select a drawing helper call.')
        # Locate this call exactly, including its closing parenthesis.
        opening=next(i for i,t in enumerate(ts) if t[1]==args[0][0])-1
        start=ts[opening-1][1]
        depth=0;end=None
        for token,_,stop in ts[opening:]:
            if token=='(':depth+=1
            elif token==')':
                depth-=1
                if depth==0:end=stop;break
        mat=e['material']
        if not isinstance(mat,dict):raise ValueError('Material definition is unavailable.')
        color=rgb+[component(mat.get('color'),3,255)]
        material=('MakeFont('+lua_literal(mat['description'])+','+lua_literal(color)+')' if mat.get('font') else
                  'MakeMaterial('+lua_literal(mat.get('path'))+','+lua_literal(color)+')')
        replacement='F117_layout_color(function() return '+source[start:end]+' end, '+material+')'
        span=(start,end)
        if span in edits and edits[span]!=replacement:
            raise ValueError('This call creates different materials; edit their Lua separately.')
        edits[span]=replacement
    if not edits:raise ValueError('Select a drawable element or a group containing symbols.')
    ordered=sorted(edits)
    if any(a[1]>b[0] for a,b in zip(ordered,ordered[1:])):raise ValueError('Selected calls overlap.')
    for (a,b),replacement in sorted(edits.items(),reverse=True):source=source[:a]+replacement+source[b:]
    include='dofile(LockOn_Options.script_path.."Indicator/layout_color.lua")'
    if include not in source:source=include+'\n'+source
    return source


def transform_selection(source, elements, model, params, dx=0, dy=0, factor=1, pivot=(0,0)):
    """One atomic source edit, deduplicating loops and selected parent/children.

    World-space transforms are converted through each parent rotation. Geometry
    arguments remain expressions; point arrays are transformed before Add().
    """
    if not math.isfinite(factor) or factor<=0: raise ValueError('Scale must be positive.')
    states={e['name']:state for e,state in model.scene(params)}
    chosen={e['name']:e for e in elements}
    def ancestors(e):
        seen=set()
        while e.get('parent_element') in model.by_name:
            e=model.by_name[e['parent_element']]
            if e['name'] in seen:break
            seen.add(e['name']);yield e['name']
    roots={name:e for name,e in chosen.items() if not any(a in chosen for a in ancestors(e))}
    work=dict(roots)
    if factor!=1:
        for e in model.elements:
            if any(a in roots for a in ancestors(e)):work[e['name']]=e
    edits={}
    def put(span,value):
        if span is None:raise ValueError('This source argument is not editable.')
        if span in edits and edits[span]!=value:
            raise ValueError('Selected instances share source code but require different transforms. Select their parent instead.')
        edits[span]=value
    for name,e in work.items():
        state=states[name]
        inherited=any(a in roots for a in ancestors(e))
        parent=states.get(e.get('parent_element'),(0,0,0))
        angle=parent[2];ca,sa=math.cos(angle),math.sin(angle)
        unit=e.get('_coordinate_scale',1)
        px,py=(0,0) if inherited else pivot
        wx,wy=(0,0) if inherited else (dx,dy)
        # desired local affine transform, around world pivot (or scaled parent origin)
        if inherited: ox=oy=0
        else:
            ox=(wx+(1-factor)*(parent[0]-px))*ca+(wy+(1-factor)*(parent[1]-py))*sa
            oy=-(wx+(1-factor)*(parent[0]-px))*sa+(wy+(1-factor)*(parent[1]-py))*ca
        word,args=source_call(source,e)
        spans=position_spans(source,e)
        if word=='group' and len(args)>1 and source[slice(*args[0])].lstrip().startswith('{'):
            # Side-display group({x,y},parent,...), unlike named HUD group(name,x,y,...).
            ts=tokens(source);opening=next(i for i,t in enumerate(ts) if t[1]==args[0][0])
            spans=[(ts[a][1],ts[b-1][2]) for a,b in arguments(ts,opening)[:2]]
        if word in ('line','poly') and args:
            span=args[0];value=source[slice(*span)]
            # Points are expressed relative to the element, normally at its parent origin.
            lx,ly=ox/unit,oy/unit
            new=(f'(function(points) local result={{}} for i,p in ipairs(points) do '
                 f'result[i]={{p[1]*{factor:.10g}+({lx:.10g}),p[2]*{factor:.10g}+({ly:.10g})}} '
                 f'end return result end)({value})')
            put(span,new)
        elif word in ('box','circle') and len(args)>=3:
            for span,offset in zip(args[:2],(ox/unit,oy/unit)):
                put(span,_expression(source[slice(*span)],factor,offset))
            if factor!=1:
                for span in args[2:4 if word=='box' else 3]:
                    put(span,_expression(source[slice(*span)],factor))
        elif spans:
            for span,offset in zip(spans,(ox,oy)):
                prefix=source[source.rfind('\n',0,span[0])+1:span[0]]
                units=1 if re.search(r'\binit_pos\s*=',prefix) else unit
                put(span,_expression(source[slice(*span)],factor,offset/units))
            if factor!=1 and e.get('_etype') in ('ceStringPoly','ceStringSLine'):
                index=2 if word=='add_text_hud_param' else 3
                if word not in ('text','readout','add_text_hud','add_text_hud2','add_text_hud_param') or len(args)<=index:
                    raise ValueError('Text size is defined outside this call. Select a text/readout call or edit its size in Lua.')
                span=args[index];size=source[slice(*span)]
                if size=='nil':
                    size={'HUD':'2.8','MFD':'SD','Left MFD':'VSD_SD','Right MFD':'HSD_SD'}.get(model.mode)
                    if size is None:raise ValueError('This page has no default text size. Edit the size in Lua.')
                new=(f'(function(s) if type(s)=="table" then return '
                     f'{{s[1]*{factor:.10g},s[2]*{factor:.10g},(s[3] or 0)*{factor:.10g},s[4]}} '
                     f'else return s*{factor:.10g} end end)({size})')
                put(span,new)
        else:
            raise ValueError(f"Cannot transform {e.get('name')} at source line {e.get('_source_line')}; edit its Lua or select an editable parent.")
    ordered=sorted(edits)
    for a,b in zip(ordered,ordered[1:]):
        if a[1]>b[0]:raise ValueError('Selected source expressions overlap. Select their parent instead.')
    for (a,b),value in sorted(edits.items(),reverse=True):source=source[:a]+value+source[b:]
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
               show_all=False, grid=True, clipping=True, reference=None, boundary=None,
               reference_above=True):
        scale = size / (2*extent)
        def point(x, y):
            return size/2+(x-center[0])*scale, size/2-(y-center[1])*scale
        image = Image.new('RGBA', (size, size), '#06110d')
        reference_layer = None
        if reference:
            # An optional source-unit rectangle (x0, y0, x1, y1) places the
            # reference on the glass; otherwise it fills the square preview.
            ref, opacity, *fit = reference
            box = (0, 0, size, size)
            if fit and fit[0]:
                x0, y0, x1, y1 = fit[0]
                (left, top), (right, bottom) = point(x0, y1), point(x1, y0)
                box = tuple(round(v) for v in (left, top, right, bottom))
            width, height = box[2]-box[0], box[3]-box[1]
            if width > 0 and height > 0:
                ref = ref.convert('RGBA').resize((width, height))
                ref.putalpha(ref.getchannel('A').point(lambda v: int(v*opacity)))
                reference_layer = Image.new('RGBA', (size, size))
                reference_layer.paste(ref, box[:2])
                # Above: visible over opaque page backgrounds; below: under symbols.
                if not reference_above:
                    image.alpha_composite(reference_layer)
                    reference_layer = None
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
            if kind in ('ceStringPoly','ceStringSLine'):
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
                elif (isinstance(mat,str) and mat.startswith('render_target_')) or (
                        isinstance(mat,dict) and re.fullmatch(r'mfd\d+',str(mat.get('path')))):
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
        if reference_layer:
            image.alpha_composite(reference_layer)
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
        self.screen=tk.StringVar(value='HUD'); self.page=tk.StringVar(value='HUD')
        self.grid=tk.BooleanVar(value=True); self.clip=tk.BooleanVar(value=True)
        self.all=tk.BooleanVar(value=False); self.snap=tk.DoubleVar(value=.005)
        self.boundary=tk.BooleanVar(value=True); self.guide_scale=tk.DoubleVar(value=1)
        self.extent=tk.DoubleVar(value=1.1)
        self.reference_opacity=tk.DoubleVar(value=.25); self.reference_above=tk.BooleanVar(value=True)
        self.reference_image=None; self.params=dict(DEFAULTS); self.renderer=Renderer()
        self.models={}; self.sources={}; self.disk={}; self.undo_stack=[]
        self.hits=[]; self.selected=None; self.selection=[]; self.drag=None; self.marquee=None; self.pending=False
        self.center=(0,0); self.size=800
        bar=ttk.Frame(root,padding=8); bar.pack(fill='x')
        ttk.Label(bar,text='F-117  LAYOUT STUDIO',font=('Segoe UI',12,'bold')).pack(side='left',padx=(0,20))
        ttk.Label(bar,text='Screen').pack(side='left')
        screens=ttk.Combobox(bar,textvariable=self.screen,values=list(SCREENS),state='readonly',width=22)
        screens.pack(side='left',padx=(4,10)); screens.bind('<<ComboboxSelected>>',lambda _:self.choose_screen())
        ttk.Label(bar,text='Page').pack(side='left')
        self.page_picker=ttk.Combobox(bar,textvariable=self.page,values=list(SCREENS['HUD']),state='readonly',width=11)
        self.page_picker.pack(side='left',padx=(4,10)); self.page_picker.bind('<<ComboboxSelected>>',lambda _:self.choose_page())
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
        ttk.Checkbutton(left,text='Draw reference above symbols',variable=self.reference_above,command=self.redraw).pack(anchor='w')
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
        self.canvas.bind('<KeyPress>',self.keypress)
        root.bind('<Control-z>',self.shortcut_undo)
        root.bind('<Control-Z>',self.shortcut_undo)
        self.inspector=tk.StringVar(value='Click a symbol to inspect it. Drag to move its source position.')
        ttk.Label(right,textvariable=self.inspector,wraplength=400,justify='left').pack(fill='x',pady=(0,8))
        ttk.Button(right,text='Select parent / move a group',command=self.parent).pack(fill='x')
        color_row=ttk.Frame(right);color_row.pack(fill='x',pady=6)
        ttk.Label(color_row,text='Hex color').pack(side='left')
        self.hex_color=tk.StringVar(value='#00FF00')
        color_entry=ttk.Entry(color_row,textvariable=self.hex_color,width=10)
        color_entry.pack(side='left',padx=6)
        color_entry.bind('<Return>',lambda _:self.apply_color())
        ttk.Button(color_row,text='Apply to selected',command=self.apply_color).pack(side='left')
        ttk.Button(right,text='Select all symbols',command=self.select_all_symbols).pack(fill='x')

        ttk.Label(right,text='LUA SOURCE  |  Ctrl+Enter previews, Ctrl+S saves').pack(anchor='w',pady=(12,5))
        self.code=tk.Text(right,wrap='none',undo=True,font=('Consolas',10),tabs=('4c',))
        scroll=ttk.Scrollbar(right,command=self.code.yview);scroll.pack(side='right',fill='y')
        self.code.configure(yscrollcommand=scroll.set);self.code.pack(fill='both',expand=True)
        self.code.tag_configure('source_line',background='#d8efdc')
        self.code.bind('<Control-Return>',lambda _:self.apply_source())
        self.code.bind('<Control-s>',lambda _:self.save())
        self.code.bind('<Control-z>',self.shortcut_undo)
        self.code.bind('<Control-Z>',self.shortcut_undo)
        ttk.Label(root,textvariable=self.status,padding=7,wraplength=1450).pack(fill='x')
        root.protocol('WM_DELETE_WINDOW',self.close)
        self.switch()

    def message(self, text):
        self.status.set(text)

    def text(self):
        return self.code.get('1.0','end-1c')

    def dirty(self):
        return any(s!=self.disk.get(m) for m,s in self.sources.items()) or self.text()!=self.sources.get(self.mode.get(),'')

    def choose_screen(self):
        pages=SCREENS[self.screen.get()]
        if self.page.get() not in pages:self.page.set(next(iter(pages)))
        self.choose_page()

    def choose_page(self):
        pages=SCREENS[self.screen.get()]
        self.page_picker.configure(values=list(pages))
        self.mode.set(pages[self.page.get()]);self.switch()

    def reconcile_selection(self):
        """Keep the screen/page pickers consistent with the page key in self.mode."""
        mode=self.mode.get()
        if mode not in SCREENS[self.screen.get()].values():self.screen.set(DEFAULT_SCREEN[mode])
        pages=SCREENS[self.screen.get()]
        self.page_picker.configure(values=list(pages))
        if pages.get(self.page.get())!=mode:self.page.set(next(k for k,v in pages.items() if v==mode))

    def switch(self):
        if hasattr(self,'current'):
            self.sources[self.current]=self.text()
        self.reconcile_selection()
        self.current=self.mode.get()
        self.params.update(context_params(self.current,self.screen.get()))
        if self.current not in self.sources:
            self.disk[self.current]=PAGES[self.current].read_text(encoding='utf-8-sig')
            self.sources[self.current]=self.disk[self.current]
        self.code.delete('1.0','end');self.code.insert('1.0',self.sources[self.current])
        self.selected=None;self.selection=[];self.reset_view();self.compile()

    def compile(self):
        try:
            model=Model(self.current,self.text(),self.screen.get())
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
        extent,self.center=default_view(self.mode.get(),self.screen.get())
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
            ref=(self.reference_image,self.reference_opacity.get(),reference_fit(self.screen.get(),self.guide_scale.get())) if self.reference_image else None
            self.preview,self.hits,missing=self.renderer.render(model,self.params,self.size,extent,self.center,
                self.all.get(),self.grid.get(),self.clip.get(),ref,
                layout_boundary(self.current,self.guide_scale.get(),self.screen.get()) if self.boundary.get() else None,
                self.reference_above.get())
            self.guide_scale_entry.configure(state='disabled' if self.current=='HUD' else 'normal')
            measurements=measured_surfaces()
            surface=measurements.get(SCREEN_SURFACE.get(self.screen.get()) or self.current)
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
            lookup={h.element['name']:h for h in self.hits}
            states={e['name']:state for e,state in model.scene(self.params,self.all.get())}
            self.selection=[lookup[h.element['name']] if h.element['name'] in lookup else
                Hit(model.by_name[h.element['name']],h.box,states[h.element['name']])
                for h in self.selection if h.element['name'] in model.by_name]
            self.selection_box()
            note=f'{self.current}: {len(model.elements)} elements, {len(self.hits)} visible. '
            if self.current in PREVIEW_ONLY:note+='EO (IRADS) is a composition preview: edit its symbols on the Central Sensor Display IRADS page. '
            note+='Box drag = select; Shift = add/toggle; arrows = move; +/- = scale; Ctrl+Z = undo. '
            note+='Font metrics, 3D optics and camera imagery are approximate.'
            if self.current=='HUD':note+=' HUD clipping preview uses the working rectangle, not head/VR glass projection.'
            if missing:note+=f' Missing texture atlases: {len(missing)} (grey outlines).'
            if model.warnings:note+=' Unsupported controllers: '+', '.join(sorted(model.warnings))
            self.message(note)
        except Exception as exc:self.message('Preview error: '+str(exc))

    def selection_box(self):
        self.canvas.delete('selection')
        if not self.selection:
            self.selected=None
            self.inspector.set('Click or drag a box to select. Arrows move; +/- scales; Ctrl+Z undoes.')
            return
        self.selected=self.selection[0]
        for hit in self.selection:
            box=hit.box
            self.canvas.create_rectangle(box[0]+self.offset[0]-3,box[1]+self.offset[1]-3,
                box[2]+self.offset[0]+3,box[3]+self.offset[1]+3,outline='#ffca64',width=2,tags='selection')
        e=self.selected.element
        line=int(e.get('_position_line') or e.get('_source_line') or 1)
        self.inspector.set(f"{len(self.selection)} selected | {e.get('_etype')} | {e.get('name')}\n"
            f"Source line {line} | parent: {e.get('parent_element','none')}\n"
            'Arrows move all selected; Shift+arrow = 10x; +/- scales 5%.\n'
            'Loops/shared source calls move together. Ctrl+Z undoes one action.')

    def selectable_hits(self):
        # Screen-filling backgrounds/dimmers must not intercept empty-space drags.
        return [h for h in self.hits if (h.box[2]-h.box[0])*(h.box[3]-h.box[1])<self.size*self.size*.65]

    def press(self,event):
        self.canvas.focus_set()
        x,y=event.x-self.offset[0],event.y-self.offset[1]
        choices=[h for h in self.selectable_hits() if h.box[0]-5<=x<=h.box[2]+5 and h.box[1]-5<=y<=h.box[3]+5]
        hit=min(choices,key=lambda h:max(1,h.box[2]-h.box[0])*max(1,h.box[3]-h.box[1])) if choices else None
        group=self.selected if self.selected and self.selected.element.get('_etype')=='ceSimple' else None
        if group and group.box[0]-5<=x<=group.box[2]+5 and group.box[1]-5<=y<=group.box[3]+5:hit=group
        if event.state & 1 or not hit:
            self.marquee=(event.x,event.y,list(self.selection) if event.state & 1 else [],hit)
            self.drag=None
            return
        if not any(h.element['name']==hit.element['name'] for h in self.selection):self.selection=[hit]
        self.selection_box()
        e=hit.element;line=int(e.get('_position_line') or e.get('_source_line') or 1)
        self.code.tag_remove('source_line','1.0','end');self.code.tag_add('source_line',f'{line}.0',f'{line+1}.0')
        self.code.see(f'{line}.0')
        self.drag=(event.x,event.y,list(self.selection))

    def motion(self,event):
        if self.marquee:
            self.canvas.delete('marquee')
            x,y,_,_=self.marquee
            self.canvas.create_rectangle(x,y,event.x,event.y,outline='#73ceff',dash=(4,3),tags='marquee')
        elif self.drag:
            self.selection_box()
            self.canvas.move('selection',event.x-self.drag[0],event.y-self.drag[1])

    def release(self,event):
        if self.marquee:
            x,y,base,hit=self.marquee;self.marquee=None
            self.canvas.delete('marquee')
            if abs(event.x-x)+abs(event.y-y)<3:
                if hit:
                    names={h.element['name'] for h in base}
                    self.selection=[h for h in base if h.element['name']!=hit.element['name']] if hit.element['name'] in names else base+[hit]
                else:self.selection=base
            else:
                x0,x1=sorted((x-self.offset[0],event.x-self.offset[0]))
                y0,y1=sorted((y-self.offset[1],event.y-self.offset[1]))
                found=[h for h in self.selectable_hits() if x0<=h.box[0] and h.box[2]<=x1 and y0<=h.box[1] and h.box[3]<=y1]
                combined={h.element['name']:h for h in base+found}
                self.selection=list(combined.values())
            self.selection_box();return
        if not self.drag:return
        sx,sy,hits=self.drag;self.drag=None
        if abs(event.x-sx)+abs(event.y-sy)<3:return
        scale=self.size/(2*self.extent.get())
        dx,dy=(event.x-sx)/scale,-(event.y-sy)/scale
        snap=self.snap.get()
        if snap>0:dx,dy=round(dx/snap)*snap,round(dy/snap)*snap
        self.transform(dx,dy)

    def transform(self,dx=0,dy=0,factor=1):
        if not self.selection:return
        if self.text()!=self.sources.get(self.current):
            self.message('Preview source edits before transforming a selection.');return
        boxes=[h.box for h in self.selection]
        cx=(min(b[0] for b in boxes)+max(b[2] for b in boxes))/2
        cy=(min(b[1] for b in boxes)+max(b[3] for b in boxes))/2
        scale=self.size/(2*self.extent.get())
        pivot=(self.center[0]+(cx-self.size/2)/scale,self.center[1]-(cy-self.size/2)/scale)
        old=self.text()
        try:
            new=transform_selection(old,[h.element for h in self.selection],self.models[self.current],
                                    self.params,dx,dy,factor,pivot)
            if new==old:return
            Model(self.current,new,self.screen.get()) # validate the complete action before changing the editor
        except Exception as exc:
            self.selection_box();self.message('Selection unchanged: '+str(exc));return
        self.undo_stack.append((self.current,old))
        self.code.delete('1.0','end');self.code.insert('1.0',new);self.code.edit_reset()
        self.compile()

    def select_all_symbols(self):
        self.selection=self.selectable_hits()
        self.selection_box()

    def apply_color(self):
        if not self.selection:
            self.message('Select one or more elements first.');return
        if self.text()!=self.sources.get(self.current):
            self.message('Preview source edits before applying color to a selection.');return
        old=self.text()
        try:
            new=recolor_selection(old,[h.element for h in self.selection],self.models[self.current],self.hex_color.get())
            Model(self.current,new,self.screen.get())
        except Exception as exc:
            self.message('Color unchanged: '+str(exc));return
        self.undo_stack.append((self.current,old))
        self.code.delete('1.0','end');self.code.insert('1.0',new);self.code.edit_reset()
        self.compile()

    def keypress(self,event):
        if event.state & 4:return # Ctrl+Z is handled by the window binding.
        arrows={'Left':(-1,0),'Right':(1,0),'Up':(0,1),'Down':(0,-1)}
        if event.keysym in arrows:
            step=self.snap.get() or 2*self.extent.get()/self.size
            if event.state & 1:step*=10
            x,y=arrows[event.keysym];self.transform(x*step,y*step)
            return 'break'
        if event.keysym in ('plus','equal','KP_Add','minus','KP_Subtract'):
            self.transform(factor=1.05 if event.keysym in ('plus','equal','KP_Add') else 1/1.05)
            return 'break'
        if event.keysym=='Escape':
            self.selection=[];self.selection_box();return 'break'

    def shortcut_undo(self,event=None):
        if self.root.focus_get()==self.code and self.text()!=self.sources.get(self.current):
            try:self.code.edit_undo()
            except self.tk.TclError:pass
        else:self.undo()
        return 'break'

    def parent(self):
        if not self.selected:return
        e=self.models[self.current].by_name.get(self.selected.element.get('parent_element'))
        if e:
            self.selection=[Hit(e,self.selected.box,self.selected.state)]
            self.selection_box();self.canvas.focus_set()

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
        self.code.delete('1.0','end');self.code.insert('1.0',source);self.code.edit_reset();self.compile()

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
        folder=REFERENCES/REFERENCE_DIRS.get(self.current,'')
        hint='cropped to the glass' if self.screen.get() in GLASS_FIT_REFERENCE else 'cropped HUD/MFD'
        path=filedialog.askopenfilename(title=f'Choose a {hint} reference',
            initialdir=str(folder if folder.is_dir() else REFERENCES),filetypes=[('Images','*.png *.jpg *.jpeg *.bmp *.tga'),('All files','*.*')])
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
    parser.add_argument('--screen',choices=list(SCREENS),help='Physical screen for the guide outline and scale (default: the live default for the page)')
    parser.add_argument('--output',type=Path,default=ROOT/'tmp/layout-preview.png')
    parser.add_argument('--params',type=Path,help='JSON object of sample DCS parameter values')
    parser.add_argument('--reference',type=Path,help='Reference image overlaid as in the editor')
    parser.add_argument('--reference-opacity',type=float,default=.5)
    args=parser.parse_args()
    if args.render:
        screen=args.screen or DEFAULT_SCREEN[args.render]
        if args.render not in SCREENS[screen].values():parser.error(f'{screen} cannot show page {args.render}')
        params=dict(DEFAULTS,**context_params(args.render,screen))
        if args.params:params.update(json.loads(args.params.read_text()))
        model=Model(args.render,PAGES[args.render].read_text(encoding='utf-8-sig'),screen)
        extent,center=default_view(args.render,screen)
        reference=(Image.open(args.reference),args.reference_opacity,reference_fit(screen)) if args.reference else None
        image,hits,missing=Renderer().render(model,params,extent=extent,center=center,reference=reference,
                                            boundary=layout_boundary(args.render,1,screen))
        args.output.parent.mkdir(parents=True,exist_ok=True);image.save(args.output)
        print(f'{args.render}: {len(model.elements)} elements; {len(hits)} visible; {len(missing)} missing atlases')
        print(args.output)
        if args.render=='HUD' and not hud_working_area()['boundary']:
            print('HUD angular boundary pending: reload the aircraft in DCS to capture its FOV conversion.')
    else:
        import tkinter as tk
        root=tk.Tk();Editor(root);root.mainloop()


if __name__=='__main__':main()
