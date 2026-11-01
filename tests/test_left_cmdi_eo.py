"""Left CMDI EO selection, sensor isolation and shared camera presentation."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from check_display_calibration import runtime
from layout_editor import Model,PAGES,DEFAULTS,convert
SCRIPTS=ROOT/'Cockpit/Scripts'

class LeftEOTests(unittest.TestCase):
    def test_selector_does_not_dispatch_or_reset_sensor_state(self):
        lua,load=runtime();g=lua.globals()
        lua.execute('''
            calls={};listened={}
            function GetSelf() return {listen_command=function(_,c)listened[c]=true end,
                performClickableAction=function()end} end
            function make_default_activity()end
            function dispatch_action(...)calls[#calls+1]={...}end
            function get_absolute_model_time()return 43200 end
            LockOn_Options.init_conditions={birth_place="GROUND_COLD"}
        ''')
        def modules(path):
            if '/Systems/' in str(path):
                if str(path).endswith('Displays.lua'):return load(path)
                if str(path).endswith('IRADS_Diagnostics.lua'):return lua.eval('function()end')
                return lua.eval('{new=function()return {initialize=function()end,update=function()end}end,initialize=function()end,update=function()end,set_command=function()return false end,default_side_brightness=function()return 1 end}')
            return load(path)
        g.dofile=modules
        load(SCRIPTS/'Systems/Displays.lua');g.post_initialize()
        self.assertEqual(g._parameters.F117_LEFT_EO,1)
        lua.execute('calls={};_parameters.mainpower=1;_parameters.F117_IRADS_LOCK_VALID=1;_parameters.IRADS_ZOOM=3;_parameters.F117_IRADS_POWER=1')
        c=g.left_cmdi_commands
        for command,value,expected in [(c.EO_TOGGLE,1,0),(c.EO_TOGGLE,0,0),
                (c.EO_SELECT,1,1),(c.VSD_SELECT,1,0),(c.EO_TOGGLE,1,1),(c.EO_TOGGLE,1,0)]:
            self.assertTrue(g.listened[command])
            g.SetCommand(command,value)
            self.assertEqual(g._parameters.F117_LEFT_EO,expected)
        self.assertEqual(len(g.calls),0)
        self.assertEqual(g._parameters.F117_IRADS_LOCK_VALID,1)
        self.assertEqual(g._parameters.IRADS_ZOOM,3)
        self.assertEqual(g._parameters.F117_IRADS_POWER,1)

    def test_modes_show_exclusive_artwork_and_one_contrast_band(self):
        model=Model('Left MFD',PAGES['Left MFD'].read_text())
        def visible(mode,power=1):
            return [e for e,state in model.scene(dict(DEFAULTS,F117_LEFT_EO=mode,
                F117_IRADS_POWER=power,F117_IRADS_CONTRAST_BAND=61,mainpower=1,MFD_OVERLAY=1,ONE=1)) if state[3]]
        def video(elements):
            return [e for e in elements if e.get('_etype')=='ceTexPoly']
        vsd=visible(0);eo=visible(1)
        self.assertTrue(any(e.get('value')=='VSD' for e in vsd))
        self.assertFalse(any(e.get('value')=='VSD' for e in eo))
        self.assertFalse(video(vsd))
        videos=video(eo)
        self.assertEqual(len(videos),1)
        self.assertEqual(videos[0]['name'],'F117_LEFT_EO_VIDEO_61')
        self.assertIn(['set_contrast_raw',1.2],videos[0]['controllers'])
        self.assertTrue(any('F117_IRADS_COORD_TEXT' in e.get('element_params',[]) for e in eo))
        off=visible(1,0)
        self.assertFalse(video(off))
        self.assertFalse(any('F117_IRADS_COORD_TEXT' in e.get('element_params',[]) for e in off))
        self.assertFalse(any(e.get('value')=='VSD' for e in off))

    def test_video_samples_camera_texture_not_the_owners_mfd_material(self):
        # Native set_mat_params sends MFD brightness/contrast only when the material
        # is the drawing indicator's own target; elsewhere both are zero, so the
        # shader's (v-.5)*c+.5 flattens the picture to mid grey.
        lua,load=runtime();load(SCRIPTS/'MFD/Indicator/Left/Left_base_page.lua')
        self.assertIsNone(lua.globals().render_target)
        videos=[e for e in convert(lua.globals()._elements) if e['_etype']=='ceTexPoly']
        self.assertEqual(len(videos),66)
        for e in videos:
            self.assertEqual(e['material'],dict(path='mfd0',color=[255,255,255,255]))
            self.assertTrue(e['input_space_SRGB'])
            self.assertTrue(e['additive_alpha'])
        lua,load=runtime();load(SCRIPTS/'MFD/Indicator/DLIR_Camera_init.lua')
        self.assertEqual(lua.globals().render_target,0) # target 0 is texture mfd0

    def test_overlay_fits_left_glass_without_registering_second_camera(self):
        lua,load=runtime();load(SCRIPTS/'MFD/Indicator/Left/Left_base_page.lua')
        g=lua.globals();elements=convert(g._elements)
        names=[e['name'] for e in elements]
        self.assertEqual(len(names),len(set(names)))
        self.assertIsNone(g.render_target)
        self.assertIsNone(g.F117_IRADS_OVERLAY_OPTIONS)
        self.assertEqual(g._scale,g.METERS)
        overlay=[e for e in elements if e.get('parent_element')=='F117_LEFT_EO_SYMBOLOGY']
        self.assertGreater(len(overlay),30)
        for e in overlay:
            self.assertTrue(e['z_enabled'])
            self.assertEqual(e['level'],1)
            self.assertIn('ONE',e['element_params'])
            for x,y in e.get('vertices',[]):
                self.assertLess(abs(x),.05);self.assertLess(abs(y),.046)
            if 'init_pos' in e:
                self.assertLess(abs(e['init_pos'][0]),.05)
                self.assertLess(abs(e['init_pos'][1]),.046)
        lua,load=runtime();load(SCRIPTS/'MFD/Indicator/MFD_base_page.lua')
        centre=convert(lua.globals()._elements)
        self.assertTrue(any(e['name']=='F117_IRADS_SOURCE' for e in centre))
        self.assertFalse(any('F117_LEFT_EO' in e.get('element_params',[]) for e in centre))

if __name__=='__main__':unittest.main()
