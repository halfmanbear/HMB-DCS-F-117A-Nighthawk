"""Exercise the capture hook with EFM-like slew deadzone and screenshot acknowledgements."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('irads_level_shots', ROOT / 'tools/missions/irads_level_shots.py')
calibration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calibration)


class LevelSweepTests(unittest.TestCase):
    def simulate(self, level, gain, initial_y, valid=1, drift=0, transitions=False):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            calibration.build('day' if gain==.8 else 'night', folder, transitions=transitions)
            lua = LuaRuntime()
            lua.execute((ROOT / 'Cockpit/Scripts/command_defs.lua').read_text())
            lua.globals().extended = not transitions
            lua.execute('''
                now=0; y=0; axis=0; level=.15; gain=.8; valid=1; stopped=false
                values={};LockOn_Options={script_path='test/'}
                function dofile() return extended end
                function get_absolute_model_time() return 43200 end
                function get_param_handle(name) return {
                    get=function() return values[name] or 0 end,
                    set=function(_,v) values[name]=v end} end
                function GetDevice(id)
                    assert(id==7)
                    return {performClickableAction=function(_,command,value) image.set_command(command,value) end}
                end
                DCS={getPause=function() return false end,
                     getModelTime=function() return now end,
                     exitProcess=function() stopped=true end,
                     setUserCallbacks=function(h) hook=h end}
                Export={
                    LoGetSelfData=function() return {Heading=0,Pitch=0,Bank=0,LatLongAlt={Alt=4500}} end,
                    LoGetVectorVelocity=function() return {y=0} end,
                    LoGetTrueAirSpeed=function() return 230 end,
                    LoSetCommand=function(c,v)
                        if c==10120 then axis=v end
                    end}
                function list_cockpit_params()
                    return string.format('F117_IRADS_POWER:1\\nF117_IRADS_LOS_VALID:%d\\n'..
                        'F117_IRADS_LOS_X:%.8f\\nF117_IRADS_LOS_Y:%.8f\\nF117_IRADS_LOS_Z:0\\n'..
                        'F117_IRADS_BRIGHTNESS:%.8f\\nF117_IRADS_CONTRAST:%.8f\\n',
                        valid,math.sqrt(1-y*y),y,values.F117_IRADS_BRIGHTNESS,values.F117_IRADS_CONTRAST)
                end
                net={dostring_in=function(_,code) return assert(load(code))() end}
                function tick()
                    now=now+.05
                    if math.abs(axis)>.05 then y=y+axis*.05 end
                    y=y+drift
                    hook.onSimulationFrame()
                end
            ''')
            g = lua.globals()
            image = lua.execute((ROOT / 'Cockpit/Scripts/Systems/IRADS_ImageControls.lua').read_text())
            g.image = image
            image.initialize()
            low, high = (.025, .8) if transitions else (0, 1)
            image.set_command(g.irads_image_commands.BRIGHTNESS_AXIS, 2*((level-low)/(high-low))**.5-1)
            image.set_command(g.irads_image_commands.CONTRAST_AXIS, 2*(gain-.35)/.65-1)
            g.drift = drift
            g.level, g.gain, g.y, g.valid = level, gain, initial_y, valid
            hook = (folder / 'capture_hook.lua').read_text()
            lua.execute(hook)
            names = []
            for _ in range(72000):
                g.tick()
                request = folder / 'shot.req'
                if request.exists():
                    names.append(request.read_text())
                    request.unlink()
                if g.stopped:
                    break
            return (folder / 'done.txt').read_text(), names, (folder / 'measurements.csv').read_text()

    def test_day_and_night_complete_all_detents_with_deadzone(self):
        for level, gain, y in ((.60, .8, 0), (.065, .96, -.294)):
            with self.subTest(gain=gain):
                reason, names, csv = self.simulate(level, gain, y)
                self.assertEqual(reason, 'done')
                self.assertEqual(len(names), 42)
                rows = csv.splitlines()[1:-1]
                self.assertEqual(len(rows), 42)
                for n, row in enumerate(rows[1:]):
                    fields = row.split(',')
                    self.assertAlmostEqual(float(fields[2]), n*.025, places=6)
                    self.assertAlmostEqual(float(fields[3]), gain)
                    self.assertLess(abs(float(fields[5])+.31), .025)

    def test_flight_drift_does_not_stall_settling(self):
        reason, names, _ = self.simulate(.15, .8, -.298, drift=.00002)
        self.assertEqual(reason, 'done')
        self.assertEqual(len(names), 42)

    def test_transition_sequence_uses_production_mapping(self):
        reason, names, csv = self.simulate(.6, .8, 0, transitions=True)
        self.assertEqual(reason, 'done')
        self.assertEqual(len(names), 28)
        self.assertEqual(names[:4], ['default_ground_before', 'default_sky',
                                     'default_ground_return', 'default_ground_settled'])
        for row in csv.splitlines()[1:-1]:
            fields = row.split(',')
            self.assertAlmostEqual(float(fields[3]), .8)
            target = .035 if fields[0].endswith('_sky') else -.31
            self.assertLess(abs(float(fields[5])-target), .025)

    def test_ctrl_c_terminates_owned_process_and_removes_overrides(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / 'Scripts/Hooks').mkdir(parents=True)
            (folder / 'capture_hook.lua').write_text('-- test')
            (folder / 'plan.json').write_text(json.dumps({'extended_range': True}))
            override = folder / 'range.lua'
            process = Mock()
            process.poll.return_value = None
            with patch.object(calibration.drop, 'SAVED_GAMES', folder), \
                 patch.object(calibration, 'OVERRIDE', override), \
                 patch.object(calibration.subprocess, 'run', return_value=Mock(stdout='')), \
                 patch.object(calibration.subprocess, 'Popen', return_value=process), \
                 patch.object(calibration.shots, 'screenshots', return_value=set()), \
                 patch.object(calibration.time, 'sleep', side_effect=KeyboardInterrupt):
                calibration.run(folder / 'test.miz', folder)
            process.terminate.assert_called_once()
            self.assertFalse(override.exists())
            self.assertFalse((folder / 'Scripts/Hooks/zz_f117_irads_level_shots.lua').exists())

    def test_missing_los_reports_diagnostic_without_false_captures(self):
        reason, names, _ = self.simulate(.15, .8, 0, valid=0)
        self.assertIn('FAIL LOS aiming timeout: valid=0', reason)
        self.assertEqual(names, [])

    def test_controller_extended_range_requires_temporary_override(self):
        for enabled, low, high in ((False, .025, .8), (True, 0, 1)):
            lua = LuaRuntime()
            lua.execute((ROOT / 'Cockpit/Scripts/command_defs.lua').read_text())
            lua.globals().enabled = enabled
            lua.execute('''
                LockOn_Options={script_path='test/'}
                function dofile(path)
                    assert(path=='test/Systems/IRADS_LevelCalibration.local.lua')
                    if enabled then return true else error('file absent') end
                end
                values={}
                function get_param_handle(name) return {
                    get=function() return values[name] or 0 end,
                    set=function(_,v) values[name]=v end} end
                function get_absolute_model_time() return 43200 end
            ''')
            image = lua.execute((ROOT / 'Cockpit/Scripts/Systems/IRADS_ImageControls.lua').read_text())
            image.initialize()
            command = lua.globals().irads_image_commands
            for value, expected in ((-1, low), (1, high)):
                image.set_command(command.BRIGHTNESS_AXIS, value)
                self.assertAlmostEqual(lua.globals()['values'].F117_IRADS_BRIGHTNESS, expected)
                self.assertAlmostEqual(lua.globals()['values'].F117_IRADS_CONTRAST, .8)

    def test_scene_provides_buildings_and_moving_vehicles_near_roads(self):
        lua = LuaRuntime()
        lua.execute('''
            buildings={};vehicles={};road_queries=0
            country={id={RUSSIA=0}};Group={Category={GROUND=2}}
            coalition={addStaticObject=function(_,o) buildings[#buildings+1]=o end,
                       addGroup=function(_,_,g) vehicles[#vehicles+1]=g end}
            land={getClosestPointOnRoads=function(_,x,z)
                road_queries=road_queries+1;return x+30,z+40 end}
            env={info=function()end}
        ''')
        lua.execute(calibration.SCENE_SCRIPT)
        g = lua.globals()
        self.assertEqual(len(g.buildings),111)
        self.assertEqual(len(g.vehicles),37)
        self.assertEqual(g.road_queries,37)
        for group in g.vehicles.values():
            self.assertGreater(group.route.points[1].speed,0)
            self.assertEqual(group.units[1].type,'Ural-375')
            self.assertNotEqual(group.route.points[1].x,group.route.points[2].x)


if __name__ == '__main__':
    unittest.main()
