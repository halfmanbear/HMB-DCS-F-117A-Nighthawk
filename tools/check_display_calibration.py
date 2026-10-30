"""Validate DCS calibration pages offline and export reference previews.

python tools/check_display_calibration.py [--refresh-outlines]
Requires the same dependencies as layout_editor.py. This cannot verify EDM
connectors, DCS projection, font metrics or in-game rendering.
"""
import argparse
import json
import math
from pathlib import Path

from lupa import LuaRuntime
from layout_editor import Model, Renderer, convert

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'Cockpit/Scripts'
CAL = SCRIPTS / 'Calibration'


def refresh_outlines():
    surfaces = json.loads((ROOT/'tools/data/cockpit_display_geometry.json').read_text())['surfaces']
    lines = ['-- Generated from tools/data/cockpit_display_geometry.json; connector-local metres.', 'return {']
    for kind, name in [('centre','MFD'), ('left','Left MFD'), ('right','Right MFD')]:
        g = surfaces[name]
        (xmin,ymin),(xmax,ymax) = g['bounds_local_m']
        lines += [f'    {kind} = {{', f'        width={g["width_m"]:.12f}, height={g["height_m"]:.12f},',
                  f'        xmin={xmin:.12f}, xmax={xmax:.12f}, ymin={ymin:.12f}, ymax={ymax:.12f},',
                  '        outline={']
        lines += [f'            {{{x:.12f}, {y:.12f}}},' for x,y in g['boundary_local_m']]
        lines += ['        },', '    },']
    (CAL/'measured_outlines.lua').write_text('\n'.join(lines+['}', '']), encoding='utf-8')


def runtime(enabled=None):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute((ROOT/'tools/layout_runtime.lua').read_text())
    lua.execute('''
        METERS=3; h_clip_relations.NULL=0
        function SetScale(s) _scale=s end
        function GetScale() return _scale==MILLYRADIANS and 0.001 or 1 end
        indicator_types={COMMON=0,COLLIMATOR=1,HELMET=2}
        render_purpose={GENERAL=0,HUD_ONLY_VIEW=1,BAKE=100}
        SelfWidth=1920; SelfHeight=1080
        function update_screenspace_diplacement(...) end
        -- Snapshot at Add, matching the native API's consumption of properties.
        function Add(o) table.insert(_elements, Copy(o)) end
    ''')
    lua.globals().LockOn_Options.script_path = SCRIPTS.as_posix()+'/'

    def load(path):
        if str(path).startswith('__dcs__/'):
            return None
        path = Path(path).resolve()
        assert path.is_relative_to(SCRIPTS.resolve()), path
        value = lua.execute(path.read_text(encoding='utf-8-sig'), name='@'+path.as_posix())
        if path == (CAL/'config.lua').resolve() and enabled is not None:
            value.enabled = enabled
        return value

    lua.globals().dofile = load
    return lua, load


def validate():
    # Compile every affected Lua file using the Lua parser, without running it.
    lua = LuaRuntime()
    compile_lua = lua.eval('function(s) local f,e=load(s); assert(f,e) end')
    for path in [*SCRIPTS.glob('display_*.lua'),SCRIPTS/'materials.lua',SCRIPTS/'Systems/DisplayCompositor.lua',SCRIPTS/'Systems/Displays.lua',*(SCRIPTS/'MFD/Indicator/LCD').glob('*.lua'),SCRIPTS/'MFD/Indicator/render_config.lua',SCRIPTS/'device_init.lua', *(SCRIPTS/'HUD/Device').glob('*.lua'), *CAL.glob('*.lua'), *(SCRIPTS/'HUD/Indicator').glob('*.lua'), *(SCRIPTS/'MFD/Indicator/Left').glob('*.lua'), *(SCRIPTS/'MFD/Indicator/Right').glob('*.lua')]:
        compile_lua(path.read_text(encoding='utf-8-sig'))

    for enabled,count in [(False,8),(True,9)]:
        lua,load = runtime(enabled)
        load(SCRIPTS/'device_init.lua')
        indicators=lua.globals().indicators
        assert len(indicators)==count, (enabled,len(indicators))
        assert Path(indicators[4][2]).name == 'Left_init.lua'
        assert [indicators[4][4][1][i] for i in range(1,4)] == [
            'MFD-PLASHKA-CENTER1','MFD-PLASHKA-DOWN1','MFD-PLASHKA-RIGHT1']
        assert Path(indicators[5][2]).name == 'Right_init.lua'
        assert [indicators[5][4][1][i] for i in range(1,4)] == [
            'RADAR-PLASHKA-CENTER','RADAR-PLASHKA-DOWN','RADAR-PLASHKA-RIGHT']
        if enabled:
            assert [Path(indicators[i][2]).stem for i in range(9,10)] == [
                'centre_init']

    # Both operational display pages load independently of their init states.
    for side in ['Left','Right']:
        lua,load = runtime()
        load(SCRIPTS/f'MFD/Indicator/{side}/{side}_init.lua')
        assert lua.globals().init_pageID == 1
        assert lua.globals().indicator_type == lua.globals().indicator_types.COMMON
        page = Path(lua.globals().page_subsets[1])
        lua,load = runtime()
        load(page)
        elements = convert(lua.globals()._elements)
        assert lua.globals()._scale == 3
        assert len(elements) > 100
        assert all(e.get('z_enabled') is True for e in elements if e['_etype'] != 'ceSimple')

    output = ROOT/'tmp/calibration'
    output.mkdir(parents=True,exist_ok=True)
    for kind in ['hud','centre','left','right']:
        lua,load = runtime()
        load(CAL/f'{kind}_init.lua')
        page = Path(lua.globals().page_subsets[1])
        # DCS loads pages separately: globals set only in init are unavailable.
        lua,load = runtime()
        assert lua.globals().CALIBRATION_KIND is None
        load(page)
        assert lua.globals()._scale == (2 if kind=='hud' else 3)
        model = Model.__new__(Model)
        model.elements = convert(lua.globals()._elements)
        model.by_name = {e['name']:e for e in model.elements}
        model.warnings = set()
        masks=[]
        for e in model.elements:
            is_mask=kind=='hud' and e['h_clip_relation']==2
            if is_mask:
                masks.append(e)
                assert e['collimated'] is False
                assert e['z_enabled'] is True
                assert e['level']==8
                assert not e.get('parent_element') # mask cannot follow angular origin
                assert len(e['init_pos'])==3 and e['init_pos'][2]>0
                assert -40<e['init_rot'][2]<-30
            else:
                assert e['collimated'] == (kind=='hud')
                assert e['h_clip_relation']==(1 if kind=='hud' else 0)
                assert e['level']==(8 if kind=='hud' else 0)
                assert e['z_enabled'] == (kind!='hud')
            assert not e.get('parent_element') or e['parent_element'] in model.by_name
            if e['_etype']=='ceMeshPoly':
                assert len(e['indices'])%3==0
                assert all(0<=i<len(e['vertices']) for i in e['indices'])
            if e['_etype']=='ceStringPoly':
                assert 0 < e['stringdefs'][0] < .01, e['stringdefs']
        if kind=='hud':
            assert len(masks)==2
            def attitude_y(pitch):
                return next(s[1] for e,s in model.scene({'PITCH_HUD':pitch,'ROLL_HUD':0})
                            if e.get('value')=='ATT 0')
            assert math.isclose(attitude_y(math.radians(5))-attitude_y(0),-math.radians(5)*1000)
        else:
            square = next(e for e in model.elements if len(e.get('vertices',[]))==16)
            xs=[v[0] for v in square['vertices']]
            assert math.isclose(max(xs)-min(xs), .041, abs_tol=1e-9)
        # The desktop renderer uses geometry units for text too. Convert the
        # validated absolute DCS font sizes back ONLY for its preview rendering.
        if kind=='hud':
            for e in model.elements:
                if e['_etype']=='ceStringPoly':
                    e['stringdefs']=[v/0.001 for v in e['stringdefs']]
        # Finite glass projection needs the DCS camera (and each VR eye).
        # Export angular layout only, without pretending to emulate that mask.
        image,_,missing = Renderer().render(model,{},size=850,extent=215 if kind=='hud' else .10,grid=False,clipping=kind!='hud')
        assert not model.warnings, model.warnings
        assert not missing, missing
        image.save(output/f'{kind}.png')
        print(f'{kind}: {len(model.elements)} elements; reference preview {output/kind}.png')
    print('PASS: Lua syntax, registrations on/off, unit modes, absolute font sizes, geometry, parents and 5-degree pitch movement.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh-outlines',action='store_true')
    args=parser.parse_args()
    if args.refresh_outlines:
        refresh_outlines()
    validate()
