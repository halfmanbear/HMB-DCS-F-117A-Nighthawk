"""Display power bus, staggered display boot and display data alignment."""
import math
import sys
import unittest
from pathlib import Path

from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'Cockpit/Scripts'
sys.path.insert(0, str(ROOT / 'tools'))
from layout_editor import Model, PAGES, DEFAULTS, POWER_OFF, convert  # noqa: E402

DISPLAYS = ['DEP', 'HUD', 'CMDI_L', 'SD', 'CMDI_R']
STEP = .05


def runtime(birth='GROUND_COLD'):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute("""
        values={};listened={};messages={};rpm_l=0;rpm_r=0;speed=0
        sensor={getEngineLeftRPM=function()return rpm_l end,getEngineRightRPM=function()return rpm_r end,
            getSelfVelocity=function()return speed,0,0 end,
            getPitch=function()return .1 end,getRoll=function()return -.2 end,
            getHeading=function()return 6.2 end,getMagneticHeading=function()return .05 end,
            getBarometricAltitude=function()return 1500 end,getVerticalVelocity=function()return 10 end,
            getMachNumber=function()return .5 end}
        function get_base_data()return sensor end
        function get_param_handle(name)return {get=function()return values[name] or 0 end,
            set=function(_,v)values[name]=v end}end
        function make_default_activity()end
        function GetSelf()return {listen_command=function(_,c)listened[c]=true end}end
        function print_message_to_user(m)messages[#messages+1]=m end
        LockOn_Options={init_conditions={}}
    """)
    g = lua.globals()
    g.LockOn_Options.script_path = SCRIPTS.as_posix() + '/'
    g.LockOn_Options.init_conditions.birth_place = birth
    g.dofile = lambda path: lua.execute(Path(path).read_text(encoding='utf-8-sig'))
    return lua, g


def device(birth='GROUND_COLD'):
    lua, g = runtime(birth)
    g.dofile(SCRIPTS / 'Systems/Electrical.lua')
    g.post_initialize()
    return lua, g


def run(g, seconds):
    for _ in range(int(round(seconds / STEP))):
        g.update()


class PowerTests(unittest.TestCase):
    def test_battery_gates_apu_and_generators(self):
        lua, g = device()
        v, keys = g['values'], g.Keys
        self.assertEqual(v.mainpower, 0)
        self.assertTrue(g.listened[keys.PowerOnOff] and g.listened[keys.APUToggle])
        g.SetCommand(keys.APUToggle, 1)  # no battery: nothing happens
        run(g, 10)
        self.assertEqual((v.mainpower, v.F117_APU_STATE), (0, 0))
        g.SetCommand(keys.PowerOnOff, 1)
        run(g, 1)
        self.assertEqual((v.mainpower, v.F117_BATTERY), (0, 1))
        g.SetCommand(keys.APUToggle, 1)
        run(g, 7.5)
        self.assertEqual((v.mainpower, v.F117_APU_STATE), (0, 1))
        run(g, 1)
        self.assertEqual((v.mainpower, v.F117_APU_STATE), (1, 2))
        g.SetCommand(keys.PowerOnOff, 1)  # battery off drops the APU too
        g.update()
        self.assertEqual((v.mainpower, v.F117_APU_STATE), (0, 0))

    def test_engine_generators_need_the_battery(self):
        lua, g = device()
        v, keys = g['values'], g.Keys
        g.rpm_l = g.rpm_r = .62
        run(g, 1)
        self.assertEqual((v.mainpower, v.F117_GEN_ONLINE), (0, 1))
        g.SetCommand(keys.PowerOnOff, 1)
        g.update()
        self.assertEqual(v.mainpower, 1)
        g.rpm_l, g.rpm_r = 0, .55  # generators come on line at 56 % core rpm
        g.update()
        self.assertEqual(v.mainpower, 0)
        g.rpm_r = .57
        g.update()
        self.assertEqual(v.mainpower, 1)

    def test_engine_start_messages_follow_the_efm(self):
        lua, g = device()
        v, messages = g['values'], g.messages
        def said():
            return [messages[i] for i in range(1, len(messages) + 1)]
        g.update()
        self.assertEqual(said(), [])
        v.F117_ENGINE_START_REJECTED = 2  # Engines Start refuses both engines in one go: one message
        g.update()
        self.assertEqual(said(), ['ENGINE START NEEDS START AIR - APU OR AIR CART'])
        for right, left in ((1, 0), (2, 0), (3, 0), (4, 1), (4, 3), (4, 4), (4, 4)):
            v.F117_ENGINE_START_R, v.F117_ENGINE_START_L = right, left
            g.update()
        self.assertEqual(said()[1:], ['R ENGINE START - STARTER ENGAGED', 'R STARTER DISENGAGED',
                                      'L ENGINE START - STARTER ENGAGED', 'L STARTER DISENGAGED'])
        # A hot start reports running from spawn without a message.
        lua, g = device('GROUND_HOT')
        g['values'].F117_ENGINE_START_L = g['values'].F117_ENGINE_START_R = 4
        run(g, 1)
        self.assertEqual(len(g.messages), 0)

    def test_ground_carts_connect_only_when_stopped_on_the_ground(self):
        lua, g = device()
        v, keys = g['values'], g.Keys
        self.assertTrue(g.listened[keys.GroundPowerToggle] and g.listened[keys.GroundAirToggle])
        g.SetCommand(keys.GroundAirToggle, 1)  # airborne (no weight on wheels): refused
        g.update()
        self.assertEqual(v.F117_GROUND_AIR, 0)
        v.F117_WOW = 1
        g.speed = 1.5
        g.SetCommand(keys.GroundPowerToggle, 1)  # rolling: refused
        g.update()
        self.assertEqual(v.F117_GROUND_POWER, 0)
        g.speed = 0
        g.SetCommand(keys.GroundAirToggle, 1)
        g.SetCommand(keys.GroundPowerToggle, 1)
        g.update()
        self.assertEqual((v.F117_GROUND_AIR, v.F117_GROUND_POWER, v.mainpower), (1, 1, 0))  # no battery yet
        g.SetCommand(keys.PowerOnOff, 1)
        run(g, 1)
        self.assertEqual(v.mainpower, 1)  # ground power alone brings the bus up
        self.assertEqual(v.F117_PWR_DEP, 2)
        g.SetCommand(keys.GroundPowerToggle, 1)
        g.update()
        self.assertEqual((v.F117_GROUND_POWER, v.mainpower), (0, 0))
        g.SetCommand(keys.GroundPowerToggle, 1)
        g.update()
        g.speed = 3  # taxiing away pulls both carts off
        g.update()
        self.assertEqual((v.F117_GROUND_AIR, v.F117_GROUND_POWER, v.mainpower), (0, 0, 0))
        said = [g.messages[i] for i in range(1, len(g.messages) + 1)]
        self.assertEqual(said, ['GROUND AIR NEEDS THE AIRCRAFT STOPPED ON THE GROUND',
                                'GROUND POWER NEEDS THE AIRCRAFT STOPPED ON THE GROUND',
                                'GROUND AIR CONNECTED', 'GROUND POWER CONNECTED', 'BATTERY ON',
                                'GROUND POWER DISCONNECTED', 'GROUND POWER CONNECTED',
                                'GROUND AIR DISCONNECTED', 'GROUND POWER DISCONNECTED'])

    def test_ground_power_keeps_the_displays_up_through_an_engine_shutdown(self):
        lua, g = device()
        v, keys = g['values'], g.Keys
        v.F117_WOW = 1
        g.SetCommand(keys.PowerOnOff, 1)
        g.rpm_l = g.rpm_r = .60
        run(g, 15)
        self.assertEqual((v.mainpower, v.F117_PWR_CMDI_R), (1, 3))
        g.SetCommand(keys.GroundPowerToggle, 1)
        g.rpm_l = g.rpm_r = .30
        run(g, 1)
        self.assertEqual((v.mainpower, v.F117_PWR_CMDI_R), (1, 3))

    def test_hot_and_air_starts_are_powered_and_aligned_from_spawn(self):
        for birth in ('GROUND_HOT', 'AIR_HOT'):
            lua, g = device(birth)
            v = g['values']
            g.rpm_l = g.rpm_r = .62
            for _ in range(2):
                self.assertEqual(v.mainpower, 1)
                for d in DISPLAYS:
                    self.assertEqual((v['F117_PWR_' + d], v['F117_ON_' + d], v['F117_FADE_' + d]), (3, 1, 1))
                for p in ('PITCH', 'ROLL', 'HDG'):
                    self.assertEqual(v[f'F117_ALIGN_{p}_ERR'], 0)
                self.assertEqual(v.F117_ADC_BLEND, 1)
                g.update()

    def test_hot_start_holds_power_until_engine_rpm_is_reported(self):
        lua, g = device('GROUND_HOT')
        run(g, 1.5)  # RPM still 0
        self.assertEqual(g['values'].F117_ON_SD, 1)


class BootTests(unittest.TestCase):
    def test_displays_boot_in_a_staggered_order(self):
        lua, g = device()
        v, keys = g['values'], g.Keys
        g.SetCommand(keys.PowerOnOff, 1)
        g.rpm_l = .62
        ready, seen, last = {}, {d: set() for d in DISPLAYS}, {d: (0, 0, 0) for d in DISPLAYS}
        for i in range(int(12 / STEP)):
            g.update()
            for d in DISPLAYS:
                state, stage, progress = v['F117_PWR_' + d], v['F117_BOOT_STAGE_' + d], v['F117_BOOT_PROGRESS_' + d]
                seen[d].add(state)
                self.assertGreaterEqual(state, last[d][0], d)  # never goes backwards
                if state == 2 and last[d][0] == 2:
                    self.assertGreaterEqual((stage, progress), last[d][1:], d)
                last[d] = (state, stage, progress)
                self.assertEqual(v['F117_ON_' + d], 1 if state == 3 else 0)
                if state == 3 and d not in ready:
                    ready[d] = i
        self.assertEqual(sorted(ready, key=ready.get), DISPLAYS)
        self.assertEqual(len(set(ready.values())), len(DISPLAYS))
        for d in DISPLAYS:
            self.assertTrue({0, 1, 3} <= seen[d], d)
            self.assertEqual(2 in seen[d], d != 'HUD', d)
        g.rpm_l = 0
        g.update()
        for d in DISPLAYS:
            self.assertEqual((v['F117_PWR_' + d], v['F117_FADE_' + d]), (0, 0))

    def test_bit_screen_runs_power_on_self_test_auto_cal_and_pass(self):
        lua, g = runtime()
        boot = g.dofile(SCRIPTS / 'Systems/DisplayBoot.lua')
        stages = []
        t = 0
        while t < 8:
            r = boot.evaluate('CMDI_L', t)
            if r.state == 2 and (not stages or stages[-1] != r.stage):
                stages.append(r.stage)
            t += .01
        self.assertEqual(stages, [1, 2, 3, 4])
        self.assertEqual(boot.evaluate('CMDI_L', None).state, 0)
        hud = [boot.evaluate('HUD', t).fade for t in (3.4, 3.5, 4.75, 6.0)]
        self.assertEqual(hud[:2], [0, 0])
        self.assertAlmostEqual(hud[2], .5)
        self.assertEqual(hud[3], 1)


class AlignmentTests(unittest.TestCase):
    def test_errors_seek_through_zero_and_settle_exactly(self):
        lua, g = runtime()
        alignment = g.dofile(SCRIPTS / 'Systems/Alignment.lua')
        s = alignment.new(lua.eval('function(lo,hi)return hi end'), lua.eval('function()return 1 end'))
        s.seed()
        for axis in ('pitch', 'roll', 'hdg'):
            a = alignment.AXES[axis]
            values = [s.evaluate(t / 10)[axis] for t in range(0, int(a.tau * 60))]
            self.assertAlmostEqual(values[0], a.max)
            self.assertTrue(any(x < 0 for x in values), axis)  # overshoot
            self.assertEqual(s.evaluate(5 * a.tau)[axis], 0)
            magnitudes = [abs(x) for x in values]
            self.assertLess(max(magnitudes[len(magnitudes) // 2:]), a.max * .1)
        self.assertEqual(s.evaluate(0).adc, 0)
        self.assertEqual(s.evaluate(6).adc, 1)
        self.assertEqual(s.evaluate(None).pitch, 0)

    def test_aligned_sensor_applies_errors_and_passes_other_data(self):
        lua, g = runtime()
        v = g['values']
        v.F117_ALIGN_PITCH_ERR, v.F117_ALIGN_ROLL_ERR, v.F117_ALIGN_HDG_ERR, v.F117_ADC_BLEND = .05, .1, .2, .5
        s = g.dofile(SCRIPTS / 'Systems/AlignedSensor.lua')(g.sensor)
        self.assertAlmostEqual(s.getPitch(), .15)
        self.assertAlmostEqual(s.getRoll(), -.1)
        self.assertAlmostEqual(s.getHeading(), 6.0)
        self.assertAlmostEqual(s.getMagneticHeading(), .25)
        v.F117_ALIGN_HDG_ERR = -.2
        self.assertAlmostEqual(s.getHeading(), (6.4) % (2 * math.pi))
        self.assertAlmostEqual(s.getMagneticHeading(), 2 * math.pi - .15)
        self.assertAlmostEqual(s.getBarometricAltitude(), 750)
        self.assertAlmostEqual(s.getVerticalVelocity(), 5)
        self.assertEqual(s.getMachNumber(), .5)

    def test_power_up_reseeds_alignment(self):
        lua, g = device()
        v = g['values']
        g.SetCommand(g.Keys.PowerOnOff, 1)
        g.rpm_l = .62
        g.update()
        first = v.F117_ALIGN_HDG_ERR
        self.assertNotEqual(first, 0)
        self.assertLess(v.F117_ADC_BLEND, .1)
        run(g, 60)
        self.assertEqual((v.F117_ALIGN_PITCH_ERR, v.F117_ALIGN_ROLL_ERR, v.F117_ALIGN_HDG_ERR), (0, 0, 0))
        g.rpm_l = 0
        g.update()
        g.rpm_l = .62
        g.update()
        self.assertNotEqual(v.F117_ALIGN_HDG_ERR, 0)


class BootPageTests(unittest.TestCase):
    def composite(self, entry):
        from check_display_calibration import runtime as page_runtime
        model = Model('Left MFD', PAGES['Left MFD'].read_text(encoding='utf-8-sig'))
        lua, load = page_runtime()
        load(SCRIPTS / entry)
        model.elements = convert(lua.globals()._elements)
        model.by_name = {e['name']: e for e in model.elements}
        return model

    def test_bit_screen_replaces_formats_until_operational(self):
        for entry, display, prefix in (('MFD/Indicator/Left/Left_base_page.lua', 'CMDI_L', 'F117_left_BOOT'),
                                       ('MFD/Indicator/Right/Right_base_page.lua', 'CMDI_R', 'F117_right_BOOT'),
                                       ('MFD/Indicator/MFD_base_page.lua', 'SD', 'F117_SD_BOOT'),
                                       ('DEP/Indicator/DEP_base_page.lua', 'DEP', 'F117_DEP_BOOT')):
            with self.subTest(display=display):
                model = self.composite(entry)

                def scene(state, stage=2):
                    params = dict(DEFAULTS, **{'F117_PWR_' + display: state,
                                               'F117_ON_' + display: 1 if state == 3 else 0,
                                               'F117_BOOT_STAGE_' + display: stage,
                                               'F117_BOOT_PROGRESS_' + display: 40})
                    return [e for e, s in model.scene(params) if s[3] and e['_etype'] != 'ceSimple']
                operational = scene(3)
                self.assertTrue(operational)
                self.assertFalse(any(e['name'].startswith(prefix) for e in operational))
                bit = scene(2)
                self.assertTrue(bit)
                self.assertTrue(all(e['name'].startswith(prefix) for e in bit), [e['name'] for e in bit])
                values = [e.get('value') for e in bit]
                self.assertIn('SELF TEST', values)
                self.assertNotIn('AUTO CAL', values)
                self.assertIn('AUTO CAL', [e.get('value') for e in scene(2, 3)])
                self.assertEqual(len(scene(1)), 1)  # the backlight fill only
                self.assertFalse(scene(0))


if __name__ == '__main__':
    unittest.main()
