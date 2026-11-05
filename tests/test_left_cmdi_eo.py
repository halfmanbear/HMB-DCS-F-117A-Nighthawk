"""Left CMDI EO selection, sensor isolation and shared camera presentation."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from check_display_calibration import runtime
from layout_editor import Model,PAGES,DEFAULTS,POWER_OFF,convert,measured_surfaces
SCRIPTS=ROOT/'Cockpit/Scripts'

def composite(side='Left'):
    model=Model('Left MFD',PAGES['Left MFD'].read_text())
    lua,load=runtime();load(SCRIPTS/f'MFD/Indicator/{side}/{side}_base_page.lua')
    model.elements=convert(lua.globals()._elements)
    model.by_name={e['name']:e for e in model.elements}
    return model

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
            function get_base_data()return {} end
            LockOn_Options.init_conditions={birth_place="GROUND_COLD"}
        ''')
        def modules(path):
            if '/Systems/' in str(path):
                if str(path).endswith(('Displays.lua','AlignedSensor.lua')):return load(path)
                if str(path).endswith('IRADS_Diagnostics.lua'):return lua.eval('function()end')
                return lua.eval('{new=function()return {initialize=function()end,update=function()end,set_command=function()return false end}end,initialize=function()end,update=function()end,set_command=function()return false end,default_side_brightness=function()return 1 end,default_dep_brightness=function()return 1 end}')
            return load(path)
        g.dofile=modules
        load(SCRIPTS/'Systems/Displays.lua');g.post_initialize()
        self.assertEqual(g._parameters.F117_LEFT_EO,0)
        self.assertEqual(g._parameters.F117_RIGHT_FORMAT,2)
        lua.execute('calls={};_parameters.mainpower=1;_parameters.F117_IRADS_LOCK_VALID=1;_parameters.IRADS_ZOOM=3;_parameters.F117_IRADS_POWER=1')
        c=g.left_cmdi_commands
        for command,value,expected in [(c.EO_TOGGLE,1,1),(c.EO_TOGGLE,0,1),
                (c.EO_SELECT,1,1),(c.VSD_SELECT,1,0),(c.EO_TOGGLE,1,1),(c.EO_TOGGLE,1,0)]:
            self.assertTrue(g.listened[command])
            g.SetCommand(command,value)
            self.assertEqual(g._parameters.F117_LEFT_EO,expected)
        for command,expected in [(c.MAP_SELECT,2),(c.HSD_SELECT,3),(c.EO_TOGGLE,1),(c.VSD_SELECT,0)]:
            g.SetCommand(command,1);self.assertEqual(g._parameters.F117_LEFT_EO,expected)
        for command,expected in [(g.right_cmdi_commands.HSD_SELECT,3),(g.right_cmdi_commands.VSD_SELECT,0),(g.right_cmdi_commands.MAP_SELECT,2)]:
            g.SetCommand(command,1);self.assertEqual(g._parameters.F117_RIGHT_FORMAT,expected)
        self.assertEqual(len(g.calls),0)
        self.assertEqual(g._parameters.F117_IRADS_LOCK_VALID,1)
        self.assertEqual(g._parameters.IRADS_ZOOM,3)
        self.assertEqual(g._parameters.F117_IRADS_POWER,1)
        # FOV commands jump directly between EFM endpoint IDs, including the axis centre.
        for command in [g.irads_fov_commands.NARROW,g.irads_fov_commands.WIDE]:
            g.SetCommand(command,0)
        self.assertEqual(len(g.calls),0)
        for command in [g.irads_fov_commands.NARROW,g.irads_fov_commands.WIDE]:
            g.SetCommand(command,1)
        for value in [-1,0,.05,1,0,-.05,-1]:
            g.SetCommand(g.irads_axis_commands.ZOOM,value)
        self.assertEqual([call[3] for call in g.calls.values()],[1,-1,-1,-1,-1,1,1,1,-1])
        self.assertTrue(all(call[2]==g.f117_commands.IRADS_ZOOM_AXIS for call in g.calls.values()))
        count=len(g.calls)
        for value in [float('nan'),float('inf')]:g.SetCommand(g.irads_axis_commands.ZOOM,value)
        self.assertEqual(len(g.calls),count)


    def test_modes_show_exclusive_artwork_and_one_contrast_band(self):
        model=composite()
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
        self.assertEqual(videos[0]['name'],'F117_left_EO_F117_LEFT_EO_VIDEO_61')
        self.assertIn(['set_contrast_raw',1.2],videos[0]['controllers'])
        self.assertTrue(any('F117_IRADS_COORD_TEXT' in e.get('element_params',[]) for e in eo))
        off=visible(1,0)
        self.assertFalse(video(off))
        self.assertFalse(any('F117_IRADS_COORD_TEXT' in e.get('element_params',[]) for e in off))
        self.assertFalse(any(e.get('value')=='VSD' for e in off))

    def test_all_formats_are_exclusive_on_both_cmdis(self):
        for side in ['Left','Right']:
            model=composite(side)
            param='F117_LEFT_EO' if side=='Left' else 'F117_RIGHT_FORMAT'
            modes=[(0,'VSD'),(2,'MAP'),(3,'HSD')]+([(1,'EO')] if side=='Left' else [])
            for mode,kind in modes:
                visible=[e for e,s in model.scene(dict(DEFAULTS,**{param:mode},mainpower=1,F117_IRADS_POWER=1)) if s[3]]
                drawn=[e for e in visible if e['_etype']!='ceSimple']
                self.assertTrue(drawn)
                self.assertTrue(all(e['name'].startswith(f'F117_{side.lower()}_{kind}_') for e in drawn))
                if kind=='MAP':
                    for e in drawn:
                        for x,y in e.get('vertices',[]):
                            self.assertLess(abs(x),.053);self.assertLess(abs(y),.05)

            self.assertFalse(any(s[3] for e,s in model.scene(dict(DEFAULTS,**POWER_OFF))))

    def test_video_samples_camera_texture_not_the_owners_mfd_material(self):
        # Native set_mat_params sends MFD brightness/contrast only when the material
        # is the drawing indicator's own target; elsewhere both are zero, so the
        # shader's (v-.5)*c+.5 flattens the picture to mid grey.
        lua,load=runtime();load(SCRIPTS/'MFD/Indicator/Left/Left_base_page.lua')
        self.assertIsNone(lua.globals().render_target)
        videos=[e for e in convert(lua.globals()._elements) if e['_etype']=='ceTexPoly' and 'EO_VIDEO' in e['name']]
        self.assertEqual(len(videos),66)
        for e in videos:
            self.assertEqual(e['material'],dict(path='mfd0',color=[255,255,255,255]))
            self.assertTrue(e['input_space_SRGB'])
            self.assertTrue(e['additive_alpha'])
        lua,load=runtime();load(SCRIPTS/'MFD/Indicator/DLIR_Camera_init.lua')
        self.assertEqual(lua.globals().render_target,0) # target 0 is texture mfd0

    def test_video_and_symbols_share_one_registered_transform(self):
        lua,load=runtime();load(SCRIPTS/'MFD/Indicator/Left/Left_base_page.lua')
        elements=convert(lua.globals()._elements)
        by_name={e['name']:e for e in elements}
        content=by_name['F117_left_EO_F117_LEFT_EO_CONTENT']
        self.assertEqual(content['init_pos'][:2],[0,.002])
        self.assertEqual(by_name['F117_left_EO_F117_LEFT_EO_SYMBOLOGY']['parent_element'],content['name'])
        videos=[e for e in elements if 'EO_VIDEO' in e['name']]
        self.assertTrue(all(v['parent_element']==content['name'] for v in videos))
        # Picture extents are the centre display's, scaled exactly like the symbols (.62).
        centre=lua.execute('return dofile(LockOn_Options.script_path.."MFD/Indicator/render_config.lua").centre')
        xs=[x for x,y in videos[0]['vertices']];ys=[y for x,y in videos[0]['vertices']]
        self.assertAlmostEqual(max(xs),centre.connector_half_width*.62);self.assertAlmostEqual(min(xs),-max(xs))
        self.assertAlmostEqual(max(ys),centre.connector_half_height*.62);self.assertAlmostEqual(min(ys),-max(ys))

    def test_map_chart_and_aperture_fill_the_whole_cmdi_glass(self):
        outlines={'Left':'left','Right':'right'}
        for side,key in outlines.items():
            model=composite(side)
            glass=measured_surfaces()['Left MFD' if side=='Left' else 'Right MFD']['boundary_local_m']
            gx=[x for x,y in glass];gy=[y for x,y in glass]
            bg=model.by_name[f'F117_{side.lower()}_MAP_F117_MAP_BACKGROUND']
            xs=[x for x,y in bg['vertices']];ys=[y for x,y in bg['vertices']]
            # The stencil aperture is the side glass itself, not a shrunken centre outline.
            self.assertAlmostEqual(min(xs),min(gx),delta=.0005);self.assertAlmostEqual(max(xs),max(gx),delta=.0005)
            self.assertAlmostEqual(min(ys),min(gy),delta=.0005);self.assertAlmostEqual(max(ys),max(gy),delta=.0005)
            # Map text is as legible as the other CMDI formats (it was about 40% of their height).
            sizes=[e['stringdefs'][0] for e in model.elements
                   if e['name'].startswith(f'F117_{side.lower()}_MAP_') and e.get('stringdefs')]
            self.assertTrue(sizes)
            self.assertGreater(min(sizes),.0016)

    def test_overlay_fits_left_glass_without_registering_second_camera(self):
        lua,load=runtime();load(SCRIPTS/'MFD/Indicator/Left/Left_base_page.lua')
        g=lua.globals();elements=convert(g._elements)
        names=[e['name'] for e in elements]
        self.assertEqual(len(names),len(set(names)))
        self.assertIsNone(g.render_target)
        self.assertIsNone(g.F117_IRADS_OVERLAY_OPTIONS)
        self.assertEqual(g._scale,g.METERS)
        overlay=[e for e in elements if e.get('parent_element')=='F117_left_EO_F117_LEFT_EO_SYMBOLOGY']
        self.assertGreater(len(overlay),30)
        for e in overlay:
            self.assertTrue(e['z_enabled'])
            # The bands and gray scale reach the glass edge; the EO aperture clips them.
            if '_BAND_' in e['name'] or '_GRAY_' in e['name']:continue
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
