"""IRADS image presets, manual controls and live rendering contracts."""
import unittest
from pathlib import Path
from lupa import LuaRuntime
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/cockpit'))
from check_display_calibration import runtime
from layout_editor import Model,PAGES,DEFAULTS,convert
SCRIPTS=ROOT/'Cockpit/Scripts'

class IRADSImageTests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute((SCRIPTS/'command_defs.lua').read_text())
        self.lua.execute('''
            values={};clock=43200
            function get_param_handle(name) return {
                get=function()return values[name] or 0 end,
                set=function(_,v)values[name]=v end} end
            function get_absolute_model_time()return clock end
        ''')
        self.module=self.lua.execute((SCRIPTS/'Systems/IRADS_ImageControls.lua').read_text())
        self.g=self.lua.globals();self.v=self.g['values'];self.cmd=self.g.irads_image_commands
        self.module.initialize()

    def test_day_night_twilight_and_multiday_presets(self):
        for hour,expected in [(0,.065),(5,.065),(6,.065),(7,.4325),(8,.80),(12,.80),
                              (17,.80),(18,.4325),(19,.065),(23,.065),(31,.4325)]:
            self.assertAlmostEqual(self.module.default_brightness(hour*3600),expected)
        self.assertAlmostEqual(self.v.F117_IRADS_CONTRAST,.8)
        self.assertAlmostEqual(self.v.F117_IRADS_DIM_OPACITY,.20)
        self.assertEqual(self.v.F117_IRADS_CONTRAST_BAND,45)

    def test_dep_default_is_dim_at_night(self):
        for hour,expected in [(0,.3),(7,.575),(12,.85),(18,.575),(23,.3)]:
            self.assertAlmostEqual(self.module.default_dep_brightness(hour*3600),expected)

    def test_night_contrast_and_side_dimming_presets(self):
        for hour,contrast,side in [(0,.96,.12),(7,.88,.56),(12,.8,1),(18,.88,.56),(23,.96,.12)]:
            self.assertAlmostEqual(self.module.default_contrast(hour*3600),contrast)
            self.assertAlmostEqual(self.module.default_side_brightness(hour*3600),side)
        for mode,param in [('Left MFD','F117_LEFT_DIM_OPACITY'),('Right MFD','F117_RIGHT_DIM_OPACITY')]:
            model=Model(mode,PAGES[mode].read_text())
            e,state=next((e,s) for e,s in model.scene(dict(DEFAULTS,F117_LEFT_EO=0,**{param:.82})) if e.get('element_params')==[param])
            self.assertEqual(e['element_params'],[param])
            self.assertEqual(e['material']['color'],[0,0,0,255])
            self.assertTrue(e['z_enabled'])
            self.assertEqual(e['level'],1)
            self.assertAlmostEqual(state[4],.82)

    def test_steps_clamping_manual_persistence_and_reset(self):
        self.module.set_command(self.cmd.BRIGHTNESS_DOWN,1)
        manual=self.v.F117_IRADS_BRIGHTNESS
        self.assertLess(manual,.80)
        self.g.clock=0
        self.module.set_command(self.cmd.CONTRAST_DOWN,1)
        self.assertAlmostEqual(self.v.F117_IRADS_BRIGHTNESS,manual)
        self.assertAlmostEqual(self.v.F117_IRADS_CONTRAST,.75)
        for _ in range(40):
            self.module.set_command(self.cmd.BRIGHTNESS_DOWN,1)
            self.module.set_command(self.cmd.CONTRAST_DOWN,1)
        self.assertAlmostEqual(self.v.F117_IRADS_BRIGHTNESS,.025)
        self.assertAlmostEqual(self.v.F117_IRADS_CONTRAST,.35)
        for _ in range(40):
            self.module.set_command(self.cmd.BRIGHTNESS_UP,1)
            self.module.set_command(self.cmd.CONTRAST_UP,1)
        self.assertEqual(self.v.F117_IRADS_BRIGHTNESS,.80)
        self.assertEqual(self.v.F117_IRADS_CONTRAST,1)
        self.module.initialize()  # a fresh sortie starts from the mission-time default
        self.assertAlmostEqual(self.v.F117_IRADS_BRIGHTNESS,.065)
        self.assertAlmostEqual(self.v.F117_IRADS_CONTRAST,.96)
        self.assertFalse(self.module.set_command(87,1))

    def test_axes_reject_nonfinite_and_cover_endpoints(self):
        for axis,param,low,high in [(self.cmd.BRIGHTNESS_AXIS,'F117_IRADS_BRIGHTNESS',.025,.80),
                               (self.cmd.CONTRAST_AXIS,'F117_IRADS_CONTRAST',.35,1)]:
            self.module.set_command(axis,-1);self.assertAlmostEqual(self.v[param],low)
            self.module.set_command(axis,1);self.assertAlmostEqual(self.v[param],high)
            self.module.set_command(axis,float('nan'));self.assertAlmostEqual(self.v[param],high)

    def test_brightness_full_travel_and_button_resolution(self):
        for i in range(101):
            self.module.set_command(self.cmd.BRIGHTNESS_AXIS,-1+2*i/100)
            self.assertAlmostEqual(self.v.F117_IRADS_BRIGHTNESS,.025+.775*(i/100)**2)
            self.assertAlmostEqual(self.v.F117_IRADS_LEVEL,i/100)
        self.module.set_command(self.cmd.BRIGHTNESS_AXIS,-1)
        for _ in range(40):
            self.module.set_command(self.cmd.BRIGHTNESS_UP,1)
        self.assertAlmostEqual(self.v.F117_IRADS_BRIGHTNESS,.80)

    def test_level_dims_markings_and_has_fine_low_end(self):
        self.module.set_command(self.cmd.BRIGHTNESS_AXIS,-1)
        low_symbols=self.v.F117_IRADS_DRAW_BRIGHTNESS
        self.module.set_command(self.cmd.BRIGHTNESS_UP,1)
        self.assertAlmostEqual(self.v.F117_IRADS_LEVEL,.025)
        self.assertLess(self.v.F117_IRADS_BRIGHTNESS-.025,.001)
        self.module.set_command(self.cmd.BRIGHTNESS_AXIS,1)
        self.assertAlmostEqual(self.v.F117_IRADS_DRAW_BRIGHTNESS,low_symbols*1/.075)
        self.assertAlmostEqual(self.v.F117_IRADS_VIDEO_DRAW_BRIGHTNESS,1)

    def test_native_symbol_registration_excludes_direct_video_materials(self):
        lua,load=runtime()
        lua.execute('''
            material_id=0
            function MakeMaterial()
                material_id=material_id+1;return 'material_'..material_id
            end
            registrations={}
            package={loadlib=function()return function()return {
                register=function(marker,materials)
                    registrations[marker]=materials;return true,'registered'
                end}end end}
        ''')
        load(SCRIPTS/'MFD/Indicator/MFD_base_page.lua')
        g=lua.globals()
        registered=set(g.registrations.F117_IRADS_SOURCE.values())
        self.assertTrue(registered)
        videos=[e for e in g._elements.values() if str(e.name).startswith('F117_CENTRE_BAKED_VIDEO_')]
        self.assertEqual(len(videos),66)
        for video in videos:
            self.assertNotIn(video.material,registered)
            self.assertEqual(video.element_params[4],'F117_IRADS_VIDEO_DRAW_BRIGHTNESS')
        elements=list(g._elements.values())
        names=[e.name for e in elements]
        dim_at=names.index('F117_CENTRE_VIDEO_DIM_LAYER')
        self.assertGreater(dim_at,max(i for i,e in enumerate(elements) if str(e.name).startswith('F117_CENTRE_BAKED_VIDEO_')))
        self.assertLess(dim_at,names.index('F117_IRADS_SOURCE'))
        self.assertFalse(elements[dim_at].additive_alpha)
        self.assertNotIn(elements[dim_at].material,registered)

    def test_video_layers_and_symbology_use_separate_controls(self):
        lua,load=runtime();load(SCRIPTS/'MFD/Indicator/DLIR_Camera_page.lua')
        elements=convert(lua.globals()._elements)
        video=[e for e in elements if e['_etype']=='ceTexPoly']
        self.assertEqual(len(video),66)
        for band,e in enumerate(video):
            self.assertEqual(e['material'],dict(path='mfd0',color=[0,90,0,255]))
            self.assertEqual(e['controllers'][-2],['parameter_in_range',2,band-.1,band+.1])
            self.assertEqual(e['controllers'][-1][0],'set_contrast_raw')
            self.assertAlmostEqual(e['controllers'][-1][1],(.35+band*.01)/.8)
        # The dim layer draws over every video band; a non-drawing marker may follow it.
        at=next(i for i,e in enumerate(elements) if e['name']=='F117_IRADS_DIM_LAYER')
        self.assertGreater(at,max(i for i,e in enumerate(elements) if e['_etype']=='ceTexPoly'))
        self.assertTrue(all(e['_etype']=='ceSimple' for e in elements[at+1:]))
        dim=elements[at]
        self.assertFalse(dim['additive_alpha'])
        self.assertEqual(dim['controllers'][-1][0],'opacity_using_parameter')
        self.assertIn('F117_IRADS_POWER',dim['element_params'])
        self.g.clock=0;self.module.initialize()
        self.assertEqual(self.v.F117_IRADS_CONTRAST_BAND,61)
        model=Model('MFD',PAGES['MFD'].read_text())
        for e,state in model.scene(dict(DEFAULTS,F117_IRADS_DRAW_BRIGHTNESS=.22)):
            # The black bands behind the top and bottom rows stay opaque.
            if e['_etype']!='ceSimple' and state[3] and '_BAND_' not in e['name']:self.assertAlmostEqual(state[4],.22)

if __name__=='__main__':unittest.main()
