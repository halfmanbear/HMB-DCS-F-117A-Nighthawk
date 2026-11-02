"""Native brightness bootstrap, material capture and fallback handover."""
import unittest
from pathlib import Path
from lupa import LuaRuntime
ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'Cockpit/Scripts'

class NativeBrightnessTests(unittest.TestCase):
    def runtime(self):
        lua=LuaRuntime(unpack_returned_tuples=True)
        lua.execute('''
            LockOn_Options={script_path='test/'};values={}
            function get_param_handle(name) return {
                get=function()return values[name] or 0 end,
                set=function(_,v)values[name]=v end} end
            values.CDBrightness=.9;values.HUDBrightness=.7;values.LDBrightness=.88
            values.RDBrightness=.86;values.F117_IRADS_BRIGHTNESS=.16
        ''')
        return lua

    def test_native_handover_and_runtime_fallback_do_not_double_dim(self):
        lua=self.runtime();g=lua.globals()
        lua.execute('''
            ready=false;calls=0
            package={loadlib=function(path,entry)
                assert(entry=='luaopen_f117_brightness')
                return function()return {update=function(...)
                    calls=calls+1;gains={...};return ready,'brightness status'
                end}end
            end}
        ''')
        module=lua.execute((SCRIPTS/'Systems/NativeBrightness.lua').read_text()).new()
        module.initialize();v=g['values']
        self.assertAlmostEqual(v.F117_HUD_DRAW_BRIGHTNESS,.7)
        self.assertAlmostEqual(v.F117_IRADS_DIM_OPACITY,.84)
        g.ready=True;module.update()
        self.assertEqual(v.F117_NATIVE_BRIGHTNESS_ACTIVE,1)
        self.assertEqual(v.F117_HUD_DRAW_BRIGHTNESS,1)
        self.assertEqual(v.F117_IRADS_DRAW_BRIGHTNESS,1)
        for param in ['F117_LEFT_DIM_OPACITY','F117_RIGHT_DIM_OPACITY','F117_IRADS_DIM_OPACITY']:
            self.assertEqual(v[param],0)
        for actual,expected in zip(g.gains.values(),[.7,.12,.14,.16,.16]):
            self.assertAlmostEqual(actual,expected)
        g.ready=False;module.update()
        self.assertEqual(v.F117_NATIVE_BRIGHTNESS_ACTIVE,0)
        self.assertAlmostEqual(v.F117_IRADS_DRAW_BRIGHTNESS,.16)
        self.assertAlmostEqual(v.F117_LEFT_DIM_OPACITY,.88)

    def test_eo_image_brightness_is_independent_of_right_map(self):
        lua=self.runtime();g=lua.globals()
        lua.execute('''
            ready=false
            values.F117_LEFT_EO=1;values.LDBrightness=.2
            package={loadlib=function()return function()return {
                update=function(...)gains={...};return ready,'status' end}end end}
        ''')
        module=lua.execute((SCRIPTS/'Systems/NativeBrightness.lua').read_text()).new()
        module.initialize();v=g['values']
        self.assertAlmostEqual(v.F117_LEFT_EO_DIM_OPACITY,.84)
        self.assertAlmostEqual(v.F117_MAP_DIM_OPACITY,.86)
        v.F117_IRADS_BRIGHTNESS=.4;module.update()
        self.assertAlmostEqual(v.F117_LEFT_EO_DIM_OPACITY,.6)
        self.assertAlmostEqual(v.F117_MAP_DIM_OPACITY,.86)
        g.ready=True;module.update()
        self.assertEqual(v.F117_LEFT_EO_DIM_OPACITY,0)
        self.assertEqual(v.F117_MAP_DIM_OPACITY,0)
        self.assertAlmostEqual(g.gains[2],.4)
        self.assertAlmostEqual(g.gains[4],.4)
        v.F117_LEFT_EO=0;module.update()
        self.assertAlmostEqual(g.gains[2],.8)
        self.assertAlmostEqual(g.gains[4],.4)

    def test_missing_loader_preserves_existing_controls(self):
        lua=self.runtime();lua.execute('package=nil')
        module=lua.execute((SCRIPTS/'Systems/NativeBrightness.lua').read_text()).new()
        module.initialize();module.update()
        v=lua.globals()['values']
        self.assertEqual(v.F117_NATIVE_BRIGHTNESS_ACTIVE,0)
        self.assertAlmostEqual(v.F117_RIGHT_DIM_OPACITY,.86)

    def test_material_capture_restores_add_and_retains_page_token(self):
        lua=self.runtime();g=lua.globals();g.token=object()
        lua.execute('''
            added={};function Add(e)added[#added+1]=e end
            original_add=Add
            package={loadlib=function()return function()return {
                register=function(marker,materials)
                    captured_marker=marker;captured_materials=materials;return true,'registered'
                end}end end}
        ''')
        finish=lua.execute((SCRIPTS/'Indicator/native_brightness_page.lua').read_text())('OCIP_ROOT')
        lua.execute('Add({material="font_A"});Add({material="line_B"});Add({material="font_A"});Add({})')
        finish()
        self.assertTrue(lua.eval('Add==original_add'))
        self.assertEqual(g.captured_marker,'OCIP_ROOT')
        self.assertEqual(list(g.captured_materials.values()),['font_A','line_B'])
        self.assertEqual(len(g.added),4)
        # DCS closes the page state after load, so nothing there may own the names.
        self.assertIsNone(g.F117_NATIVE_BRIGHTNESS_REGISTRATION)

    def test_manual_irads_changes_keep_native_handover(self):
        lua=self.runtime();lua.execute((SCRIPTS/'command_defs.lua').read_text())
        lua.execute('function get_absolute_model_time()return 0 end;values.F117_NATIVE_BRIGHTNESS_ACTIVE=1')
        image=lua.execute((SCRIPTS/'Systems/IRADS_ImageControls.lua').read_text())
        image.initialize();image.set_command(lua.globals().irads_image_commands.BRIGHTNESS_UP,1)
        v=lua.globals()['values']
        self.assertAlmostEqual(v.F117_IRADS_BRIGHTNESS,.21)
        self.assertEqual(v.F117_IRADS_DRAW_BRIGHTNESS,1)
        self.assertEqual(v.F117_IRADS_DIM_OPACITY,0)

if __name__=='__main__':unittest.main()
