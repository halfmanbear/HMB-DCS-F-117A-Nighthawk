"""Integration contracts for native stroke resources and source/target/holder routing."""
import sys
import hashlib,json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from check_display_calibration import runtime
from layout_editor import Model,PAGES,DEFAULTS,convert
SCRIPTS=ROOT/'Cockpit/Scripts'

class NativeDisplayTests(unittest.TestCase):
    def test_text_bake_diagnostic_has_fixed_text_line_glyphs_and_direct_comparison(self):
        for direct in [False,True]:
            lua,load=runtime(False)
            def configured_load(path):
                value=load(path)
                if str(path).endswith('render_config.lua'):
                    value.enabled=False;value.holder_test=False;value.bake_test=True
                    value.bake_test_source='text';value.bake_test_direct=direct
                return value
            lua.globals().dofile=configured_load
            load(SCRIPTS/'MFD/Indicator/MFD_indication_init.lua')
            page=lua.globals().page_subsets[1]
            self.assertTrue(page.endswith('/LCD/text_test_page.lua'))
            load(page)
            elements=convert(lua.globals()._elements)
            strings=[e for e in elements if e['_etype'] in ('ceStringPoly','ceStringSLine')]
            self.assertEqual(len(strings),2)
            for text in strings:
                self.assertEqual(text['_etype'],'ceStringSLine')
                self.assertEqual(text['value'],'TEST 123')
                self.assertEqual(text['material']['description']['class'],'ceSLineFont')
                self.assertNotIn('controllers',text)
                self.assertNotIn('element_params',text)
            self.assertGreater(sum(e['_etype']=='ceSMultiLine' for e in elements),7)
            self.assertFalse(any(e['_etype']=='ceTexPoly' for e in elements))
            self.assertTrue(any(e['name']=='F117_TEXT_TEST_REFERENCE' for e in elements))
            lua.execute('''
                _handles={};_loads=0
                function get_param_handle(name)
                    if not _handles[name] then
                        _handles[name]={value=0,set=function(self,v) self.value=v end}
                    end
                    return _handles[name]
                end
                package={loadlib=function() _loads=_loads+1;return nil,"missing DLL" end}
            ''')
            module=load(SCRIPTS/'Systems/DisplayCompositor.lua').new()
            module.initialize();module.update()
            g=lua.globals()
            self.assertEqual(g._loads,0 if direct else 1)
            self.assertEqual(g._handles.F117_LCD_TEST_READY.value,0)
            self.assertEqual(g._handles.F117_LCD_READY.value,0)

    def test_map_bake_diagnostic_specular_override_is_scoped_to_centre_map(self):
        for enabled,diagnostic,source,expected in [
            (False,True,'map',False),(False,False,'map',True),
            (True,True,'map',True),(False,True,'pattern',True),(False,True,'text',False),
        ]:
            lua,load=runtime(False)
            def configured_load(path):
                value=load(path)
                if str(path).endswith('render_config.lua'):
                    value.enabled=enabled;value.bake_test=diagnostic
                    value.bake_test_source=source;value.bake_test_specular=False
                return value
            lua.globals().dofile=configured_load
            load(SCRIPTS/'MFD/Indicator/MFD_indication_init.lua')
            self.assertEqual(lua.globals().shaderLineUseSpecularPass,expected)
            for side in ['Left/Left_init.lua','Right/Right_init.lua']:
                load(SCRIPTS/'MFD/Indicator'/side)
                self.assertTrue(lua.globals().shaderLineUseSpecularPass)

    def test_centre_native_bake_diagnostic_routing_and_missing_module(self):
        for available in [False,True]:
            lua,load=runtime(False)
            def configured_load(path):
                value=load(path)
                if str(path).endswith('render_config.lua'):
                    value.enabled=False;value.holder_test=True;value.bake_test=True;value.bake_test_source="pattern"
                return value
            lua.globals().dofile=configured_load
            load(SCRIPTS/'device_init.lua')
            holders=[row for row in convert(lua.globals().indicators) if '/LCD/' in row[1]]
            self.assertEqual(len(holders),1)
            load(SCRIPTS/'MFD/Indicator/MFD_indication_init.lua')
            self.assertTrue(lua.globals().page_subsets[1].endswith('/LCD/bake_test_page.lua'))
            lua.execute('_elements={}')
            load(SCRIPTS/'MFD/Indicator/LCD/bake_test_page.lua')
            elements=convert(lua.globals()._elements)
            self.assertTrue(any(e['name']=='F117_BAKE_TEST_SOURCE' for e in elements))
            self.assertEqual(sum(e['_etype']=='ceMeshPoly' for e in elements),7)
            self.assertFalse(any(e['_etype']=='ceTexPoly' for e in elements))
            lua.execute('_elements={}')
            load(SCRIPTS/'MFD/Indicator/LCD/centre_page.lua')
            picture=next(e for e in convert(lua.globals()._elements) if e['_etype']=='ceTexPoly')
            self.assertEqual(picture['material']['path'],'F117_LCD_CENTRE')
            self.assertIn('F117_LCD_TEST_READY',picture['element_params'])
            lua.execute('''
                _handles={};_calls=0
                function get_param_handle(name)
                    if not _handles[name] then
                        _handles[name]={value=0,set=function(self,v) self.value=v end}
                    end
                    return _handles[name]
                end
            ''')
            if available:
                lua.execute('''
                    package={loadlib=function() return function() return {
                        start=function(resolution,diagnostic)
                            _calls=_calls+1;_diagnostic=diagnostic;_resolution=resolution
                            get_param_handle("F117_LCD_TEST_READY"):set(1)
                            return true,"centre test active"
                        end
                    } end end}
                ''')
            else:
                lua.execute('package={loadlib=function() return nil,"missing DLL" end}')
            module=load(SCRIPTS/'Systems/DisplayCompositor.lua').new()
            module.initialize();module.update()
            g=lua.globals()
            self.assertEqual(g._handles.F117_LCD_READY.value,0)
            self.assertEqual(g._handles.F117_LCD_TEST_READY.value,int(available))
            self.assertEqual(g._calls,int(available))
            if available:
                self.assertEqual(g._diagnostic,1)
                self.assertEqual(g._resolution,1024)

    def test_map_bake_diagnostic_selects_real_page_with_dedicated_marker(self):
        for diagnostic in [False,True]:
            lua,load=runtime(False)
            def configured_load(path):
                value=load(path)
                if str(path).endswith('render_config.lua'):
                    value.enabled=False;value.holder_test=False
                    value.bake_test=diagnostic;value.bake_test_source="map"
                return value
            lua.globals().dofile=configured_load
            load(SCRIPTS/'MFD/Indicator/MFD_indication_init.lua')
            page=lua.globals().page_subsets[1]
            self.assertTrue(page.endswith('/Map/Map_base_page.lua'))
            load(page)
            elements=convert(lua.globals()._elements)
            self.assertEqual(any(e['name']=='F117_BAKE_TEST_SOURCE' for e in elements),diagnostic)
            self.assertTrue(any(e['name']=='F117_IRADS_SOURCE' for e in elements))
            self.assertTrue(any(e['_etype']=='ceSMultiLine' for e in elements))
            self.assertFalse(any(e['name']=='F117_BAKE_TEST_RED' for e in elements))

    def test_static_holder_diagnostic_is_independent_of_native_compositor(self):
        for enabled in [False,True]:
            lua,load=runtime(False)
            def configured_load(path):
                value=load(path)
                if str(path).endswith('render_config.lua'):
                    value.holder_test=True;value.bake_test=False
                    value.enabled=enabled
                return value
            lua.globals().dofile=configured_load
            load(SCRIPTS/'device_init.lua')
            registered=convert(lua.globals().indicators)
            holders=[row for row in registered if '/LCD/' in row[1]]
            self.assertEqual(len(holders),3 if enabled else 1)
            if not enabled:
                self.assertTrue(holders[0][1].endswith('/centre_init.lua'))
            lua.execute('_elements={}')
            load(SCRIPTS/'MFD/Indicator/LCD/centre_page.lua')
            elements=convert(lua.globals()._elements)
            picture=next(e for e in elements if e['_etype']=='ceTexPoly')
            gate='F117_LCD_READY' if enabled else 'F117_LCD_TEST_READY'
            for element in elements:
                self.assertIn(gate,element['element_params'])
                self.assertTrue(element['z_enabled'])
            expected='F117_LCD_CENTRE' if enabled else (SCRIPTS/'Resources/LCD/holder_test.tga').as_posix()
            self.assertEqual(picture['material']['path'],expected)
            lua.execute('''
                _handles={};_native_calls=0
                function get_param_handle(name)
                    if not _handles[name] then
                        _handles[name]={value=0,set=function(self,v) self.value=v end}
                    end
                    return _handles[name]
                end
                package={loadlib=function() _native_calls=_native_calls+1;return nil,"missing DLL" end}
            ''')
            module=load(SCRIPTS/'Systems/DisplayCompositor.lua').new()
            module.initialize();module.update()
            g=lua.globals()
            self.assertEqual(g._handles.F117_LCD_READY.value,0)
            self.assertEqual(g._handles.F117_LCD_TEST_READY.value,0 if enabled else 1)
            self.assertEqual(g._native_calls,1 if enabled else 0)

    def test_lua_compositor_bootstrap_and_fallback(self):
        for available in [False,True]:
            lua,load=runtime()
            lua.execute('''
                _handles={};_calls=0
                function get_param_handle(name)
                    if not _handles[name] then
                        _handles[name]={value=0,set=function(self,v) self.value=v end}
                    end
                    return _handles[name]
                end
                LockOn_Options.cockpit={render_target_resolution=2048}
            ''')
            if available:
                lua.execute('''
                    package={loadlib=function(path,entry)
                        _module_path=path;_module_entry=entry
                        return function() return {start=function(resolution)
                            _calls=_calls+1;_resolution=resolution
                            if _calls<2 then return false,"waiting for source pages" end
                            get_param_handle("F117_LCD_READY"):set(1)
                            return true,"active"
                        end} end
                    end}
                ''')
            else:
                lua.execute('package={loadlib=function()return nil,"missing DLL" end}')
            # Exercise the bootstrap with enabled forced on, independent of the shipping config.
            original_load=load
            def enabled_load(path):
                value=original_load(path)
                if str(path).endswith('render_config.lua'):
                    value.enabled=True
                    value.resolution=None # Exercise the DCS-option fallback explicitly.
                return value
            lua.globals().dofile=enabled_load
            module=load(SCRIPTS/'Systems/DisplayCompositor.lua').new()
            module.initialize();module.update();module.update()
            g=lua.globals()
            self.assertEqual(g._handles.F117_LCD_READY.value,int(available))
            self.assertEqual(g._calls,2 if available else 0)
            if available:
                self.assertEqual(g._resolution,2048)
                self.assertEqual(g._module_entry,'luaopen_f117_displays')
                self.assertTrue(g._module_path.endswith('/../../bin/F117Displays.dll'))

    def test_operational_pages_have_a_visible_draw_purpose(self):
        # A plain ccIndicator with BAKE-only purpose needs a separate native baker;
        # merely assigning render_target does not supply that compositor.
        lua,load=runtime(False);load(SCRIPTS/'device_init.lua')
        registered=convert(lua.globals().indicators)
        self.assertEqual(len(registered),9)
        self.assertEqual(sum('/LCD/' in indicator[1] for indicator in registered),3)
        for source in ['Left/Left_init.lua','Right/Right_init.lua','MFD_indication_init.lua']:
            lua,load=runtime();load(SCRIPTS/'MFD/Indicator'/source)
            g=lua.globals()
            self.assertEqual(g.indicator_type,0)
            self.assertEqual(convert(g.purposes),[0,1])
            self.assertIsNone(g.render_target)
            self.assertIsNone(g.geometry) # calibrated connector geometry is retained
            self.assertTrue(g.shaderLineParamsUpdatable)
        for kind in ['left','right','centre']:
            lua,load=runtime();load(SCRIPTS/f'MFD/Indicator/LCD/{kind}_page.lua')
            elements=convert(lua.globals()._elements)
            for element in elements:
                self.assertIn('F117_LCD_READY',element['element_params'])
                self.assertTrue(element['z_enabled'])
            picture=next(e for e in elements if e['_etype']=='ceTexPoly')
            self.assertEqual(picture['material']['path'],f'F117_LCD_{kind.upper()}')

    def test_side_mounts_clear_measured_screen_mesh_with_depth_testing(self):
        lua,load=runtime(False);load(SCRIPTS/'device_init.lua')
        registered=convert(lua.globals().indicators)
        surfaces=json.loads((ROOT/'tools/data/cockpit_display_geometry.json').read_text())['surfaces']
        for label,index in [('Left MFD',3),('Right MFD',4)]:
            screen=surfaces[label]
            mount=registered[index][3][1]
            r,u=screen['right_axis_world'],screen['up_axis_world']
            normal=[r[1]*u[2]-r[2]*u[1],r[2]*u[0]-r[0]*u[2],r[0]*u[1]-r[1]*u[0]]
            if normal[0]>0: normal=[-v for v in normal]
            # DCS X forward/Y up/Z right -> Blender X forward/Y left/Z up.
            shift=[mount['sx_l'],-mount['sz_l'],mount['sy_l']]
            origin=[a+b for a,b in zip(screen['basis_origin_world_m'],shift)]
            clearance=[sum((o-p)*n for o,p,n in zip(origin,vertex,normal))
                       for vertex in screen['vertices_world_m']]
            self.assertGreater(min(clearance),.0005)
            self.assertLess(max(clearance),.002)
            model=Model(label,PAGES[label].read_text())
            for e in model.elements:
                if e['_etype']!='ceSimple': self.assertTrue(e['z_enabled'])
        for index in [0,1]:
            mount=registered[index][3][1]
            self.assertEqual([mount[k] for k in ['sx_l','sy_l','sz_l']],[0,0,0])
        # A side holder replaces its source page on screen, so it needs the same clearance.
        holders={Path(row[1]).stem:row[3][1] for row in registered if '/LCD/' in row[1]}
        for kind,index in [('left',3),('right',4)]:
            self.assertEqual(holders[f'{kind}_init'],registered[index][3][1])
        self.assertEqual([holders['centre_init'][k] for k in ['sx_l','sy_l','sz_l']],[0,0,0])

    def test_complete_resource_registration_and_glyphs(self):
        lua,load=runtime(False);load(SCRIPTS/'device_init.lua')
        self.assertEqual(len(lua.globals().indicators),9)
        resources=convert(lua.globals().symbologyPaths)
        self.assertEqual(resources,[(SCRIPTS/'Resources/Stroke').as_posix()])
        font=convert(load(SCRIPTS/'display_font.lua'))
        self.assertEqual(font['class'],'ceSLineFont')
        svg=ET.parse(SCRIPTS/f'Resources/Stroke/{font["symb_storage"]}.svg')
        ids={e.get('id') for e in svg.iter()}
        chars={code:name for code,name in font['chars']}
        self.assertEqual(set(chars),set(range(33,127)))
        self.assertTrue(set(chars.values()).issubset(ids))
        for mode in PAGES:
            model=Model(mode,PAGES[mode].read_text())
            stroke_text=[e for e in model.elements if
                isinstance(e.get('material'),dict) and
                e['material'].get('description',{}).get('class')=='ceSLineFont']
            self.assertTrue(stroke_text,mode)
            # ceStringPoly accepts this font but skips the indicator's bake
            # stroke scaling. Require the native stroke-text override.
            self.assertTrue(all(e['_etype']=='ceStringSLine' for e in stroke_text),mode)
            for e,state in model.scene(DEFAULTS):
                if e['_etype'] in ('ceStringPoly','ceStringSLine'):
                    self.assertEqual(e['material']['description']['class'],'ceSLineFont')
                    self.assertTrue(set(state[5]).issubset(set(chr(n) for n in chars)|{' '}))
                if e['_etype']=='ceSMultiLine':
                    self.assertEqual(len(e['indices'])%2,0)
                    self.assertLess(max(e['indices']),len(e['vertices']))
            dynamic=[e for e in model.elements if e['_etype']=='ceSimpleLineObject']
            if mode=='Central Map':
                self.assertEqual(len(dynamic),64)
                for e in dynamic:
                    self.assertGreater(e['width'],0)
                    self.assertEqual(sum(c[0]=='line_object_set_point_using_parameters' for c in e['controllers']),2)
            else:self.assertFalse(dynamic)

    def test_irads_video_and_overlay_remain_separate(self):
        lua,load=runtime();load(SCRIPTS/'MFD/Indicator/DLIR_Camera_init.lua')
        self.assertEqual(lua.globals().render_target,0)
        self.assertEqual(convert(lua.globals().purposes),[0,1])
        lua,load=runtime();load(SCRIPTS/'MFD/Indicator/DLIR_Camera_page.lua')
        video=next(e for e in convert(lua.globals()._elements) if e['name']=='dlir_picture')
        self.assertEqual(video['material'],'render_target_1')
        model=Model('MFD',PAGES['MFD'].read_text())
        self.assertFalse(any(e['_etype']=='ceTexPoly' for e in model.elements))
        lua,load=runtime();load(SCRIPTS/'MFD/Indicator/MFD_base_page.lua')
        self.assertEqual(lua.globals()._scale,lua.globals().METERS)
        config=load(SCRIPTS/'MFD/Indicator/render_config.lua')
        self.assertTrue(config.enabled)
        self.assertFalse(config.bake_test)
        self.assertFalse(config.holder_test)
        self.assertTrue(any(e['_etype']=='ceSMultiLine' for e in model.elements))

    def test_centre_page_loads_with_native_write_only_table_properties(self):
        # DCS returns an opaque string for assigned table properties. A plain
        # table shim misses read/modify/write failures that abort page loading.
        for composite in [False,True]:
            lua,load=runtime()
            lua.execute('''
                _native=setmetatable({},{__mode="k"});_elements={}
                function CreateElement(kind)
                    local values={_etype=kind}
                    local proxy=setmetatable({}, {
                        __newindex=function(_,key,value) values[key]=value end,
                        __index=function(_,key)
                            local value=values[key]
                            if type(value)=="table" then return "native property" end
                            return value
                        end
                    })
                    _native[proxy]=values
                    return proxy
                end
                function Add(element) table.insert(_elements,_native[element]) end
            ''')
            lua.globals().F117_COMPOSITE_PAGE=composite
            load(SCRIPTS/'MFD/Indicator/DLIR_Camera_page.lua')
            elements=convert(lua.globals()._elements)
            video=next(e for e in elements if e['name']=='dlir_picture')
            self.assertEqual('F117_LCD_READY' in video['element_params'],composite)
            self.assertEqual(len(video['controllers']),5 if composite else 4)
            if composite:
                lua.execute('_elements={}')
                load(SCRIPTS/'MFD/Indicator/MFD_base_page.lua')
                elements=convert(lua.globals()._elements)
                self.assertFalse(any(e['_etype']=='ceTexPoly' for e in elements))
                self.assertEqual(lua.globals()._scale,lua.globals().METERS)
                self.assertTrue(any(e['name']=='F117_IRADS_SOURCE' for e in elements))
                self.assertTrue(any(e['_etype']=='ceSMultiLine' for e in elements))
                self.assertTrue(any('F117_IRADS_COORD_TEXT' in e.get('element_params',[])
                                    for e in elements))

    def test_calibrated_hud_optics_unchanged(self):
        baseline=json.loads((ROOT/'tools/data/hud_optics_baseline.json').read_text())
        for file,digest in baseline.items():
            self.assertEqual(digest,hashlib.sha256((SCRIPTS/'HUD/Indicator'/file).read_bytes()).hexdigest())
        lua,load=runtime();load(SCRIPTS/'HUD/Indicator/HUD_init.lua')
        self.assertEqual(lua.globals().indicator_type,1)
        self.assertFalse(lua.globals().shaderLineUseSpecularPass)

if __name__=='__main__':unittest.main()
