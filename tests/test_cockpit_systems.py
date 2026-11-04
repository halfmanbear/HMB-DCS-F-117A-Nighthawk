"""Regression checks for the extended-review cockpit and preview fixes."""
import importlib.util
import math
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'Cockpit/Scripts'


class CockpitSystemsTests(unittest.TestCase):
    def runtime(self):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute("""
            values={F117_ADC_BLEND=1,mainpower=1};args={};vn=200;vu=0;ve=0;ias=100;baro=1000;radar=100
            sensor=setmetatable({
                getSelfVelocity=function()return vn,vu,ve end,
                getSelfAirspeed=function()return 150,0,0 end,
                getBarometricAltitude=function()return baro end,
                getRadarAltitude=function()return radar end,
                getIndicatedAirSpeed=function()return ias end
            },{__index=function()return function()return 0 end end})
            function get_base_data()return sensor end
            function get_param_handle(name)return {
                get=function()return values[name] or 0 end,
                set=function(_,v)values[name]=v end}end
            function make_default_activity()end
            function GetSelf()return {listen_command=function()end,
                performClickableAction=function()end}end
            function get_aircraft_type()return 'F-117-NightHawk' end
            function dispatch_action()end
            function get_absolute_model_time()return 43200 end
            function set_aircraft_draw_argument_value(a,v)args[a]=v end
            function create_sound_host()return {create_sound=function()
                return {play_once=function()end}end}end
            LockOn_Options={init_conditions={birth_place='AIR_HOT'}}
        """)
        lua.globals().LockOn_Options.script_path = SCRIPTS.as_posix() + '/'

        def load(path):
            return lua.execute(Path(path).read_text(encoding='utf-8-sig'))

        lua.globals().dofile = load
        return lua, load

    def test_real_altitude_selector_drives_baro_and_radar_readouts(self):
        lua, load = self.runtime()
        load(SCRIPTS / 'HUD/Device/HUD_Device.lua')
        g = lua.globals()
        g.post_initialize()
        hud_update = g['update']

        def modules(path):
            if '/Systems/' in str(path) and not str(path).endswith(('/Displays.lua','/AlignedSensor.lua')):
                if str(path).endswith('IRADS_Diagnostics.lua'):
                    return lua.eval('function()end')
                return lua.eval("""{new=function()return {
                    initialize=function()end,update=function()end,set_command=function()return false end}end,
                    initialize=function()end,update=function()end,set_command=function()return false end,
                    default_side_brightness=function()return 1 end,default_dep_brightness=function()return 1 end}""")
            return load(path)

        g.dofile = modules
        load(SCRIPTS / 'Systems/Displays.lua')
        g.post_initialize()
        hud_update()
        self.assertEqual(g['values'].altMode, 1)
        self.assertAlmostEqual(g['values'].ALTITUDE_HUD, 3280.8399)
        g.SetCommand(g['keys'].LDSK_14, 1)
        hud_update()
        self.assertEqual(g['values'].altMode, 2)
        self.assertAlmostEqual(g['values'].ALTITUDE_HUD, 328.08399)
        g.radar = 250
        hud_update()
        self.assertAlmostEqual(g['values'].ALTITUDE_HUD, 820.209975)
        g.SetCommand(g['keys'].LDSK_14, 1)
        hud_update()
        self.assertAlmostEqual(g['values'].ALTITUDE_HUD, 3280.8399)

    def test_ground_speed_uses_horizontal_ground_velocity_despite_wind_or_climb(self):
        lua, load = self.runtime()
        load(SCRIPTS / 'HUD/Device/HUD_Device.lua')
        g = lua.globals()
        g.post_initialize()
        for vn, vu, ve, ias in [(200, 0, 0, 100), (120, -40, 160, 90),
                                 (0, 100, 0, 0), (0, 0, 15, 10)]:
            g.vn, g.vu, g.ve, g.ias = vn, vu, ve, ias
            g['update']()
            expected = math.hypot(vn, ve) * 1.94384449
            self.assertAlmostEqual(g['values'].GS_HUD, expected)
            self.assertAlmostEqual(g['values'].CURR_IAS,
                                   expected if ias * 1.94384449 < 50 else ias * 1.94384449)

    def test_beacon_phase_wraps_smoothly_at_eighty_five_cycles_per_minute(self):
        lua, load = self.runtime()
        load(SCRIPTS / 'Systems/lights_system.lua')
        g = lua.globals()
        g.post_initialize()
        previous = .5
        for _ in range(400):
            g['update']()
            phase = g.args[1001]
            self.assertGreaterEqual(phase, 0)
            self.assertLess(phase, 1)
            self.assertAlmostEqual((phase - previous) % 1, .05 * 85 / 60)
            previous = phase
        g.SetCommand(10007, 1)
        g['update']()
        self.assertEqual(g.args[1001], 0)

    def test_platypus_glow_follows_each_engine_rpm_through_a_thermal_lag(self):
        lua, load = self.runtime()
        lua.execute("""lrpm=0;rrpm=0
            sensor.getEngineLeftRPM=function()return lrpm end
            sensor.getEngineRightRPM=function()return rrpm end""")
        load(SCRIPTS / 'Systems/lights_system.lua')
        g = lua.globals()
        g.post_initialize()
        g.lrpm, g.rrpm = 1.0, 0.5
        previous = 0
        for _ in range(400):  # 20 s
            g['update']()
            self.assertGreaterEqual(g.args[1002], previous)
            previous = g.args[1002]
        self.assertGreater(g.args[1002], 0.95)
        self.assertLessEqual(g.args[1002], 1)
        self.assertEqual(g.args[1003], 0)
        g.lrpm, g.rrpm = 0.0, 0.7  # left shut down, right at about ground idle
        for _ in range(600):
            g['update']()
        self.assertLess(g.args[1002], 0.01)
        self.assertAlmostEqual(g.args[1003], 0.0625, places=3)

    def test_platypus_nozzles_and_glow_lights_lie_along_each_exhaust_slot(self):
        text = (ROOT / 'F-117-NightHawk.lua').read_text(encoding='utf-8')
        helpers = text[text.index('-- Platypus exhaust slots.'):text.index('F_117_NightHawk = {')]
        lua = LuaRuntime(unpack_returned_tuples=True)
        nozzles, glow = lua.execute(helpers + '\nreturn platypus_nozzles(), platypus_glow_lights()')
        nozzles = [nozzles[i] for i in range(1, len(nozzles) + 1)]
        self.assertEqual(len(nozzles), 8)
        inboard, outboard = (-5.29, 0.66), (-3.19, 2.48)
        for n in nozzles:
            x, y, z = n.pos[1], n.pos[2], n.pos[3]
            side = -1 if n.engine_number == 1 else 1
            self.assertEqual(math.copysign(1, z), side)  # engine 1 left, 2 right
            t = (abs(z) - inboard[1]) / (outboard[1] - inboard[1])
            self.assertTrue(0 < t < 1)
            self.assertAlmostEqual(x, inboard[0] + (outboard[0] - inboard[0]) * t - 0.05)
            self.assertAlmostEqual(y, -0.155)
            o = n.orientation
            self.assertAlmostEqual(math.hypot(o[1], o[2], o[3]), 1)
            self.assertGreater(o[1], 0.98)  # flow runs aft...
            self.assertEqual(math.copysign(1, o[3]), -side)  # ...and splays outboard
        for engine in (1, 2):
            self.assertAlmostEqual(sum(n.smokiness_level for n in nozzles
                                       if n.engine_number == engine), 0.02)
        lights = [glow.lights[i] for i in range(1, len(glow.lights) + 1)]
        self.assertEqual(sorted(l.argument for l in lights), [1002, 1002, 1003, 1003])
        for light in lights:
            self.assertEqual(math.copysign(1, light.position[3]), -1 if light.argument == 1002 else 1)
        self.assertIn('engines_nozzles = platypus_nozzles(),', text)
        net = text[text.index('net_animation ='):]
        net = net[:net.index('}')]
        args = [int(line.split(',')[0]) for line in net.splitlines()
                if line.strip()[:1].isdigit()]
        self.assertIn(1002, args)
        self.assertIn(1003, args)
        self.assertLessEqual(len(args), 32)

    def test_color_action_rejects_selection_from_stale_source_lines(self):
        import sys
        sys.path.insert(0, str(ROOT / 'tools'))
        from layout_editor import Editor, Model, PAGES
        source = PAGES['Right MFD'].read_text(encoding='utf-8-sig')
        model = Model('Right MFD', source)
        selected = next(e for e in model.elements if e.get('value') == 'SNSR')
        changed = source.replace('text("MARK",', '\ntext("MARK",', 1)
        messages = []
        editor = Editor.__new__(Editor)
        editor.current = 'Right MFD'
        editor.sources = {'Right MFD': source}
        editor.models = {'Right MFD': model}
        editor.selection = [SimpleNamespace(element=selected)]
        editor.text = lambda: changed
        editor.message = messages.append
        with patch('layout_editor.recolor_selection') as recolor:
            editor.apply_color()
            recolor.assert_not_called()
        self.assertIn('Preview source edits', messages[-1])
        self.assertEqual(editor.text(), changed)

    def test_nosewheel_steering_limits_and_authority_button_are_consistent(self):
        lua=LuaRuntime(unpack_returned_tuples=True)
        lua.execute((ROOT/'FM/config.lua').read_text(encoding='utf-8'))
        yaw_limit=lua.globals().FM.suspension[1].yaw_limit
        self.assertAlmostEqual(yaw_limit,math.radians(45))
        aircraft=(ROOT/'F-117-NightHawk.lua').read_text(encoding='utf-8')
        self.assertIn(f'tand_gear_max = {math.tan(yaw_limit):.1f},',aircraft)
        defs=(SCRIPTS/'command_defs.lua').read_text(encoding='utf-8')
        self.assertIn('NWS_AUTHORITY_ON        = 10128',defs)
        self.assertIn('NWS_AUTHORITY_OFF       = 10129',defs)
        for device in ('keyboard','joystick'):
            profile=(ROOT/'Input/F-117-NightHawk'/device/'default.lua').read_text(encoding='utf-8')
            self.assertIn('down = f117_commands.NWS_AUTHORITY_ON, up = f117_commands.NWS_AUTHORITY_OFF',profile)

    def test_legacy_preview_renders_the_current_hud_without_a_gui(self):
        spec = importlib.util.spec_from_file_location('hud_preview', ROOT / 'tools/hud_preview.py')
        preview = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(preview)
        image, model, hits = preview.render_preview(roll=30, pitch=-5, size=300)
        self.assertEqual(image.size, (300, 300))
        self.assertIn('OCIP_ROOT', model.by_name)
        self.assertGreater(len(hits), 10)
        _, level, _ = preview.render_preview(size=300)
        states = {e['name']: s for e, s in model.scene(
            dict(preview.DEFAULTS, ROLL_HUD=math.radians(30), PITCH_HUD=math.radians(-5)))}
        level_states = {e['name']: s for e, s in level.scene(preview.DEFAULTS)}
        self.assertNotEqual(states['OCIP_LADDER_BANK'][2], level_states['OCIP_LADDER_BANK'][2])


if __name__ == '__main__':
    unittest.main()
