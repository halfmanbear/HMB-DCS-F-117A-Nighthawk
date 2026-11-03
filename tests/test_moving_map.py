"""Map scaffold navigation math, display isolation and native element contracts."""
import math,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from check_display_calibration import runtime
from layout_editor import Model,PAGES,DEFAULTS,POWER_OFF,convert
S=ROOT/'Cockpit/Scripts'

class MovingMapTests(unittest.TestCase):
    def setUp(self):
        self.lua,self.load=runtime();g=self.lua.globals()
        self.load(S/'command_defs.lua')
        self.lua.execute('''
            heading=0;vn=200;ve=0;x=1000;z=2000
            function get_base_data()return {
                getHeading=function()return heading end,
                getSelfVelocity=function()return vn,0,ve end,
                getSelfCoordinates=function()return x,100,z end}end
            function require()return {convertMetersToLatLon=function()return 42.5,-20.5 end}end
            -- Native set_string stores text unchanged, unlike the handle's set().
            _text_writes=0;_text_fail=false
            package={loadlib=function(path,entry)
                if entry~="luaopen_f117_params" then return nil,"not faked" end
                _text_path=path
                return function()return {set_string=function(name,text)
                    if _text_fail then return false end
                    _text_writes=_text_writes+1;_parameters[name]=text;return true
                end} end
            end}
        ''')
        self.module=self.load(S/'Systems/MovingMap.lua').new()
        self.module.initialize();self.g=g;self.p=g._parameters;self.c=g.map_commands

    def window(self):
        """Half extents of the chart/aperture, which fill the whole CMDI glass."""
        return self.load(S/'MFD/Indicator/Map/Map_window.lua').cmdi()

    def test_documented_ranges_clamp_and_ignore_release(self):
        self.assertEqual(self.p.F117_MAP_RANGE,25)
        self.module.set_command(self.c.RANGE_UP,0);self.assertEqual(self.p.F117_MAP_RANGE,25)
        for value in [50,100,140,140]:
            self.module.set_command(self.c.RANGE_UP,1);self.assertEqual(self.p.F117_MAP_RANGE,value)
        for _ in range(8):self.module.set_command(self.c.RANGE_DOWN,1)
        self.assertEqual(self.p.F117_MAP_RANGE,10)
        self.assertFalse(self.module.set_command(87,1))
        self.module.initialize();self.assertEqual(self.p.F117_MAP_RANGE,25)

    def test_live_navigation_orientation_and_target_projection(self):
        self.assertEqual(self.p.F117_MAP_POSITION_TEXT,'N 42.500  W 020.500')
        self.assertEqual(self.p.F117_MAP_GS_TEXT,'GS 389')
        self.p.F117_IRADS_LOCK_VALID=1
        self.p.F117_IRADS_LOCK_X=2852;self.p.F117_IRADS_LOCK_Z=2000
        self.module.update()
        self.assertEqual(self.p.F117_MAP_TARGET_VISIBLE,1)
        self.assertAlmostEqual(self.p.F117_MAP_TARGET_Y,.106/25)
        self.assertAlmostEqual(self.p.F117_MAP_TARGET_X,0)
        self.g.heading=-math.pi/2;self.g.vn=0;self.g.ve=200
        self.module.set_command(self.c.ORIENTATION,1) # CTUP
        self.assertEqual(self.p.F117_MAP_ORIENTATION_TEXT,'CTUP')
        self.assertAlmostEqual(self.p.F117_MAP_OWN_ROT,0)
        self.assertAlmostEqual(self.p.F117_MAP_TARGET_X,-.106/25)
        self.module.set_command(self.c.ORIENTATION,1) # DNUP
        self.assertEqual(self.p.F117_MAP_ORIENTATION_TEXT,'DNUP')
        self.assertAlmostEqual(self.p.F117_MAP_OWN_Y,-.0265)
        self.assertAlmostEqual(self.p.F117_MAP_TARGET_Y,-.0265+.106/25)
        self.module.set_command(self.c.ORIENTATION,1)
        self.assertEqual(self.p.F117_MAP_ORIENTATION_TEXT,'DTUP')
        self.module.set_command(self.c.ORIENTATION,1)
        self.assertEqual(self.p.F117_MAP_ORIENTATION_TEXT,'CNUP')

    def test_invalid_or_offscreen_data_never_leaves_a_target(self):
        self.p.F117_IRADS_LOCK_VALID=1;self.p.F117_IRADS_LOCK_X=1000;self.p.F117_IRADS_LOCK_Z=2000
        self.module.update();self.assertEqual(self.p.F117_MAP_TARGET_VISIBLE,1)
        self.p.F117_IRADS_LOCK_Z=1e8;self.module.update()
        self.assertEqual(self.p.F117_MAP_TARGET_VISIBLE,0)
        self.g.heading=float('nan');self.g.vn=float('nan');self.g.x=float('nan')
        self.module.update()
        self.assertEqual(self.p.F117_MAP_VALID,0)
        self.assertEqual(self.p.F117_MAP_GS_TEXT,'GS ---')
        self.assertEqual(self.p.F117_MAP_POSITION_TEXT,'POSITION UNAVAILABLE')

    def test_right_cmdi_has_opaque_map_and_centre_has_sensor_overlay(self):
        lua,load=runtime();load(S/'MFD/Indicator/MFD_indication_init.lua')
        self.assertTrue(lua.globals().page_subsets[1].endswith('Indicator/MFD_base_page.lua'))
        load(lua.globals().page_subsets[1])
        self.assertTrue(any('F117_IRADS_COORD_TEXT' in e.get('element_params',[]) for e in convert(lua.globals()._elements)))
        lua,load=runtime();load(S/'MFD/Indicator/Right/Right_base_page.lua')
        elements=convert(lua.globals()._elements)
        images=[e for e in elements if e['_etype']=='ceTexPoly' and 'MAP_SOURCE_IMAGE' in e['name']]
        self.assertEqual(len(images),1)
        # Not render_target_7: the map does not own that target, so its MFD shader
        # would receive zero brightness and contrast and draw flat grey.
        self.assertEqual(images[0]['material'],dict(path='mfd5',color=[255,255,255,255]))
        self.assertEqual(images[0]['element_params'],['F117_MAP_SOURCE_VISIBLE'])
        self.assertFalse(any('F117_IRADS_COORD_TEXT' in e.get('element_params',[]) for e in elements))
        bg=next(e for e in elements if e['name']=='F117_right_MAP_F117_MAP_BACKGROUND')
        self.assertEqual(bg['material']['color'][3],255)
        self.assertFalse(bg['additive_alpha'])
        self.assertTrue(bg['z_enabled'])
        self.assertEqual(len(bg['indices']),3*(len(bg['vertices'])-2))
        model=Model('Central Map',PAGES['Central Map'].read_text())
        self.assertFalse(any(s[3] for _,s in model.scene(dict(DEFAULTS,**POWER_OFF))))

    def test_planning_symbols_and_clipped_crossing_route(self):
        plan=self.lua.eval('{route={{x=-100000,z=2000},{x=100000,z=2000}},threats={{x=1000,z=2000,code="6"},{x=1000,z=2000,code="bogus"}}}')
        module=self.load(S/'Systems/MovingMap.lua').new(None,plan);module.initialize()
        self.assertEqual(self.p.F117_MAP_WP_1_VISIBLE,0)
        self.assertEqual(self.p.F117_MAP_WP_2_VISIBLE,0)
        self.assertEqual(self.p.F117_MAP_LEG_2_VISIBLE,1)
        self.assertAlmostEqual(self.p.F117_MAP_LEG_2_Y,-self.window().half_height)
        self.assertAlmostEqual(self.p.F117_MAP_LEG_2_BY,self.window().half_height)
        self.assertEqual(self.p.F117_MAP_THREAT_1_VISIBLE,1)
        self.assertEqual(self.p.F117_MAP_THREAT_1_LABEL,'6')
        self.assertEqual(self.p.F117_MAP_THREAT_2_VISIBLE,0)
        module.set_command(self.c.TACTICAL_DECLUTTER,1)
        self.assertEqual(self.p.F117_MAP_THREAT_1_VISIBLE,0)
        self.assertEqual(self.p.F117_MAP_LEG_2_VISIBLE,1)
        module.set_command(self.c.TACTICAL_DECLUTTER,1)
        self.assertEqual(self.p.F117_MAP_LEG_2_VISIBLE,0)
        plan.route[2]=None;module.update()
        self.assertEqual(self.p.F117_MAP_LEG_2_VISIBLE,0)

    def test_all_manual_waypoint_kinds_and_live_symbol_parameters(self):
        plan=self.lua.eval('{route={},threats={}}')
        names=['navigation','target','offset','initial','refuel','takeoff','ingress']
        for i,kind in enumerate(names,1):
            plan.route[i]=self.lua.table_from(dict(x=1000+i*100,z=2000,kind=kind,label=str(i)))
        module=self.load(S/'Systems/MovingMap.lua').new(None,plan);module.initialize()
        for i,kind in enumerate([1,2,3,4,5,1,1],1):
            self.assertEqual(self.p[f'F117_MAP_WP_{i}_VISIBLE'],1)
            self.assertEqual(self.p[f'F117_MAP_WP_{i}_KIND'],kind)
        model=Model('Central Map',PAGES['Central Map'].read_text())
        params=dict(DEFAULTS,**convert(self.p))
        visible=[e['name'] for e,state in model.scene(params) if state[3]]
        self.assertIn('F117_MAP_WP_2_KIND_2',visible)
        self.assertNotIn('F117_MAP_WP_2_KIND_1',visible)
        self.assertIn('F117_MAP_LEG_2_LINE',visible)
        self.g.x=float('nan');module.update()
        self.assertEqual(self.p.F117_MAP_LEG_2_VISIBLE,0)
        self.assertEqual(self.p.F117_MAP_WP_2_VISIBLE,0)

    def test_manual_pan_holds_world_centre_and_auto_recovers(self):
        self.module.set_command(self.c.PAN_UP,1) # inert in auto
        self.assertAlmostEqual(self.p.F117_MAP_OWN_Y,0)
        self.module.set_command(self.c.LOOK,1)
        self.module.set_command(self.c.PAN_RIGHT,1)
        self.assertAlmostEqual(self.p.F117_MAP_OWN_X,-.106*.05)
        self.g.x=2852;self.module.update()
        self.assertAlmostEqual(self.p.F117_MAP_OWN_Y,.106/25)
        self.module.set_command(self.c.SCROLL,1)
        self.assertEqual(self.p.F117_MAP_MANUAL,2)
        self.module.set_command(self.c.AUTO,1)
        self.assertAlmostEqual(self.p.F117_MAP_OWN_X,0)
        self.assertAlmostEqual(self.p.F117_MAP_OWN_Y,0)
        self.assertEqual(self.p.F117_MAP_MANUAL,0)

    def test_map_function_and_database_actions_ignore_release(self):
        self.module.set_command(self.c.DATABASE,0)
        self.assertEqual(self.p.F117_MAP_DATABASE_TEXT,'DMAP')
        self.module.set_command(self.c.DATABASE,1)
        self.assertEqual(self.p.F117_MAP_DATABASE_TEXT,'PMAP')
        self.module.set_command(self.c.FUNCTION,1)
        self.assertEqual(self.p.F117_MAP_FUNCTION,1)
        self.module.set_command(self.c.ELEVATION_UP,1)
        self.assertEqual(self.p.F117_MAP_ELEVATION_FT,4000)
        self.module.set_command(self.c.BACKGROUND_DECLUTTER,1)
        self.assertEqual(self.p.F117_MAP_BGD_TEXT,'BGD 1')
        self.module.initialize()
        self.assertEqual(self.p.F117_MAP_DATABASE_TEXT,'DMAP')
        self.assertEqual(self.p.F117_MAP_FUNCTION,0)

    def test_native_source_is_opt_in_and_never_reuses_irads(self):
        adapter=self.load(S/'MFD/Indicator/Map/Map_source.lua')
        for config in [dict(enabled=False,material='render_target_2'),dict(enabled=True),
                       dict(enabled=True,material=''),dict(enabled=True,material='mfd0'),
                       dict(enabled=True,material='render_target_1'),dict(enabled=True,material='render_target_7')]:
            self.assertFalse(adapter.configured(self.lua.table_from(config)))
        self.assertTrue(adapter.configured(self.lua.table_from(dict(enabled=True,material='F117_TEST_MAP'))))
        self.p.F117_MAP_SOURCE_READY=1;self.module.update()
        self.assertEqual(self.p.F117_MAP_SOURCE_VISIBLE,0) # no aligned producer camera has been observed

    def test_enabled_source_requires_ready_and_valid_navigation(self):
        config=self.lua.table_from(dict(enabled=True,material='F117_TEST_MAP'))
        def source_load(path):
            return config if str(path).endswith('/Map/render_source.lua') else self.load(path)
        self.g.dofile=source_load
        module=self.load(S/'Systems/MovingMap.lua').new();module.initialize()
        self.assertEqual(self.p.F117_MAP_SOURCE_READY,0)
        self.assertEqual(self.p.F117_MAP_SOURCE_VISIBLE,0)
        self.p.F117_MAP_SOURCE_READY=1;module.update()
        self.assertEqual(self.p.F117_MAP_SOURCE_VISIBLE,1)
        self.g.heading=float('nan');module.update()
        self.assertEqual(self.p.F117_MAP_SOURCE_VISIBLE,0)
        self.assertEqual(self.p.F117_MAP_VIEW_VALID,0)
        module.initialize();self.assertEqual(self.p.F117_MAP_SOURCE_READY,0)

    def test_background_view_contract_matches_overlay_transform(self):
        self.module.set_command(self.c.ORIENTATION,1) # CTUP
        self.module.set_command(self.c.ORIENTATION,1) # DNUP
        scale=self.p.F117_MAP_VIEW_SCALE
        self.assertAlmostEqual(self.p.F117_MAP_VIEW_CENTER_X,1000+.0265/scale)
        self.assertAlmostEqual(self.p.F117_MAP_VIEW_CENTER_Z,2000)
        self.assertAlmostEqual(self.p.F117_MAP_VIEW_WIDTH_M*scale,2*self.window().half_width)
        self.assertAlmostEqual(self.p.F117_MAP_VIEW_HEIGHT_M*scale,2*self.window().half_height)
        self.module.set_command(self.c.ORIENTATION,1) # DTUP, eastward track
        self.g.vn=0;self.g.ve=200;self.module.update()
        self.assertAlmostEqual(self.p.F117_MAP_VIEW_UP_RAD,math.pi/2)
        self.assertAlmostEqual(self.p.F117_MAP_VIEW_CENTER_X,1000)
        self.assertAlmostEqual(self.p.F117_MAP_VIEW_CENTER_Z,2000+.0265/scale)
        self.module.set_command(self.c.SCROLL,1)
        before=self.p.F117_MAP_VIEW_CENTER_X
        self.module.set_command(self.c.PAN_RIGHT,1)
        self.assertLess(self.p.F117_MAP_VIEW_CENTER_X,before)

    def test_chart_page_makes_the_whole_target_opaque_without_changing_colour(self):
        # The stock kneeboard map page also writes alpha only. Without this, the
        # chart target's alpha is unset and the map draws it fully transparent.
        lua,load=runtime();load(S/'MFD/Indicator/Map/Charts/page.lua')
        g=lua.globals();elements=convert(g._elements)
        self.assertEqual(len(elements),1)
        opaque=elements[0]
        self.assertEqual(opaque['blend_mode'],g.blend_mode.IBM_ONLY_ALPHA)
        self.assertEqual(opaque['material']['color'],[255,255,255,255])
        self.assertGreaterEqual(min(abs(v) for point in opaque['vertices'] for v in point),2)

    def test_source_texture_sits_below_overlay_and_inside_map_window(self):
        lua,load=runtime()
        def source_load(path):
            if str(path).endswith('/Map/render_source.lua'):
                return lua.table_from(dict(enabled=True,material='F117_TEST_MAP'))
            return load(path)
        lua.globals().dofile=source_load
        load(S/'MFD/Indicator/Map/Map_base_page.lua')
        elements=convert(lua.globals()._elements)
        image=next(e for e in elements if e['name']=='F117_MAP_SOURCE_IMAGE')
        self.assertEqual(image['material'],dict(path='F117_TEST_MAP',color=[255,255,255,255]))
        self.assertTrue(image['input_space_SRGB'])
        self.assertTrue(image['additive_alpha'])
        self.assertTrue(image['z_enabled'])
        self.assertEqual(image['element_params'],['F117_MAP_SOURCE_VISIBLE'])
        self.assertEqual(image['tex_coords'],[[0,0],[1,0],[1,1],[0,1]])
        names=[e['name'] for e in elements]
        self.assertLess(names.index('F117_MAP_BACKGROUND'),names.index(image['name']))
        self.assertLess(names.index(image['name']),names.index('F117_MAP_OWNSHIP'))
        self.assertLess(names.index('F117_MAP_OWNSHIP'),names.index('F117_MAP_DIM_LAYER'))
        # Centre-glass window here (no CMDI side); on a CMDI it is the side glass over its scale.
        xs=[x for x,y in image['vertices']];ys=[y for x,y in image['vertices']]
        self.assertAlmostEqual(max(xs),-min(xs));self.assertAlmostEqual(max(ys),-min(ys))
        self.assertGreater(max(xs),.087);self.assertGreater(max(ys),.073)

    def text_bindings(self):
        """Yield (parameter, format) for every parameter-driven map text element."""
        lua,load=runtime();load(S/'MFD/Indicator/Map/Map_base_page.lua')
        for e in convert(lua.globals()._elements):
            for c in e.get('controllers') or []:
                if c[0]=='text_using_parameter':
                    yield e['element_params'][int(c[1])],e['formats'][int(c[2])]

    def assert_text_arguments_match_formats(self):
        # sprintf("%s",25.0) reads the double as a pointer and crashes DCS.
        seen=0
        for name,fmt in self.text_bindings():
            value=self.p[name];seen+=1
            if fmt=='%s':
                self.assertNotIsInstance(value,(int,float),f'{name} is numeric but drawn with %s')
            else:
                self.assertIsInstance(value,(int,float),f'{name} is not numeric but drawn with {fmt}')
        self.assertGreater(seen,100)

    def test_text_arguments_match_formats_in_every_map_state(self):
        route='{'+','.join(f'{{x=1000,z=2000,label="{label}"}}' for label in
            ['23','0','007','1.5','1E5','0X1F',' 5','A1','WP12'])+',{x=1000,z=2000}}'
        codes=['2','10','12','Q','N1']
        threats='{'+','.join(f'{{x=1000,z=2000,code="{code}"}}' for code in codes)+'}'
        plan=self.lua.eval(f'{{route={route},threats={threats}}}')
        module=self.load(S/'Systems/MovingMap.lua').new(None,plan);module.initialize()
        self.assert_text_arguments_match_formats()
        for command in ['RANGE_UP','RANGE_DOWN','FUNCTION','ELEVATION_UP','ELEVATION_DOWN',
                        'REFERENCE_ELEVATION','BACKGROUND_DECLUTTER','DATABASE','ORIENTATION','TACTICAL_DECLUTTER']:
            module.set_command(self.c[command],1)
            self.assert_text_arguments_match_formats()

    def map_with_labels(self,labels):
        route='{'+','.join(f'{{x=1000,z=2000,label="{label}"}}' for label in labels)+'}'
        plan=self.lua.eval(f'{{route={route},threats={{{{x=1000,z=2000,code="6"}}}}}}')
        module=self.load(S/'Systems/MovingMap.lua').new(None,plan);module.initialize()
        return plan,module

    def test_numeric_looking_labels_are_stored_as_exact_text(self):
        labels=['23','0','007','1.5','1E5','0X1F',' 5','A1','WP12','123456']
        self.map_with_labels(labels)
        self.assertEqual([self.p[f'F117_MAP_WP_{i}_LABEL'] for i in range(1,len(labels)+1)],labels)
        self.assertEqual(self.p.F117_MAP_THREAT_1_LABEL,'6')
        self.assertEqual(self.g._text_path[-len('/../../bin/F117Displays.dll'):],'/../../bin/F117Displays.dll')

    def test_chart_image_samples_the_target_dcs_assigns(self):
        lua,load=runtime()
        for script in ('devices.lua','device_init.lua'):load(S/script)
        chart=next(v for v in convert(lua.globals().indicators) if v[0]=='ccKneeboard' and v[1].endswith('Map/Charts/init.lua'))
        # ccCockpitContext stores the third parameter minus one, and mfd<target> is its texture.
        source=lua.execute('return dofile(LockOn_Options.script_path.."MFD/Indicator/Map/render_source.lua")')
        self.assertEqual(source['material'],'mfd%d'%(chart[3][2]-1))

    def test_labels_are_only_written_when_their_text_changes(self):
        plan,module=self.map_with_labels(['23'])
        writes=self.g._text_writes
        module.update();self.assertEqual(self.g._text_writes,writes)
        plan.route[1].label='ALPHA';module.update()
        self.assertEqual(self.g._text_writes,writes+1)
        self.assertEqual(self.p.F117_MAP_WP_1_LABEL,'ALPHA')

    def assert_fallback_labels_stay_text(self):
        labels=['23','007','1E5','ALPHA']
        _,module=self.map_with_labels(labels)
        self.assertEqual([self.p[f'F117_MAP_WP_{i}_LABEL'] for i in range(1,5)],['W23','W007','W1E5','ALPHA'])
        self.assertEqual(self.p.F117_MAP_THREAT_1_LABEL,'W6')
        self.assert_text_arguments_match_formats()

    def test_missing_native_module_falls_back_without_numeric_labels(self):
        self.lua.execute('package={loadlib=function()return nil,"missing DLL" end}')
        self.assert_fallback_labels_stay_text()

    def test_failed_native_write_falls_back_without_numeric_labels(self):
        self.g._text_fail=True
        self.assert_fallback_labels_stay_text()

    def test_each_label_has_one_text_element(self):
        lua,load=runtime();load(S/'MFD/Indicator/Map/Map_base_page.lua')
        elements=convert(lua.globals()._elements)
        for name in ['F117_MAP_WP_64_LABEL','F117_MAP_THREAT_32_LABEL']:
            bound=[e for e in elements if name in (e.get('element_params') or [])]
            self.assertEqual(len(bound),1)
            self.assertEqual(bound[0]['formats'],['%s'])

    def test_pages_do_not_read_back_native_table_properties(self):
        for page in ['Map/Map_base_page.lua','Left/Left_base_page.lua']:
            lua,load=runtime()
            lua.execute('''
                _native={}
                function CreateElement(kind)
                    local values={_etype=kind}
                    local proxy=setmetatable({}, {
                        __newindex=function(_,key,value) values[key]=value end,
                        __index=function(_,key)
                            local value=values[key]
                            if type(value)=="table" then return "native property" end
                            return value
                        end})
                    _native[proxy]=values;return proxy
                end
                function Add(e)table.insert(_elements,_native[e])end
            ''')
            load(S/'MFD/Indicator'/page)
            self.assertGreater(len(lua.globals()._elements),20)

if __name__=='__main__':unittest.main()
