"""MARK points and sensor update (SNSR / map UPDT) against a drifting INS."""
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/cockpit'))
from check_display_calibration import runtime  # noqa: E402

S = ROOT / 'Cockpit/Scripts'
NM = 1852.0


class NavUpdateTests(unittest.TestCase):
    def setUp(self):
        self.lua, self.load = runtime()
        self.load(S / 'command_defs.lua')
        self.lua.execute('''
            truth={x=0,y=3000,z=0}
            base={getSelfCoordinates=function()return truth.x,truth.y,truth.z end,
                  getHeading=function()return 0 end,getSelfVelocity=function()return 0,0,0 end}
            states={IRADS=0,HUD=1,MAP=2,NONE=3}
            dss_state=0
            dss={state=function()return dss_state end}
            hud_on=false;hud_ground=nil
            hud={active=function()return hud_on end,ground=function()return hud_ground end}
            map_manual=0;mx,mz=nil,nil;cursor_calls={}
            map={manual=function()return map_manual end,pick=function()return mx,mz end,
                 set_update_cursor=function(on,x,z)cursor_calls[#cursor_calls+1]={on,x,z}end}
            messages={}
            ground_height=nil
        ''')
        self.g = self.lua.globals()
        seq = '{0.5,0.9,0.25,0.75}'
        self.ins = self.load(S / 'Systems/INS.lua').new(self.lua.eval('{random=(function()local i=0;local s=' + seq +
                                                                    ';return function()i=i%#s+1;return s[i]end end)()}'))
        self.g.ins = self.ins
        # Route: a take-off point, then the destination 10 km north and 20 km east of the origin.
        self.lua.execute('''
            nav=nil
            function route_source()return {{x=0,y=0,type="TakeOff"},{x=10000,y=20000,type="Turning Point"},
                {x=30000,y=40000,type="Turning Point"}} end
        ''')
        self.nav = self.load(S / 'Systems/Navigation.lua').new(self.ins.wrap(self.g.base), self.g.route_source)
        self.nav.initialize()
        for _ in range(200):
            self.nav.update()
        self.g.nav = self.nav
        self.nu = self.load(S / 'Systems/NavUpdate.lua').new(self.lua.eval('''{
            navigation=nav,ins=ins,dss=dss,hud=hud,map=map,states=states,
            position=function()return truth.x,truth.y,truth.z end,
            elevation=function()return ground_height end,
            message=function(t)messages[#messages+1]=t end}'''))
        self.p = self.g._parameters
        self.c = self.g.update_commands
        self.ins.update(0, True, True)
        for _ in range(3600):
            self.ins.update(1.0, True, True)  # an hour of drift
        self.dest = (10000.0, 20000.0)

    def press(self, name):
        self.assertTrue(self.nu.set_command(self.c[name], 1))

    def lock(self, x, z, y=100.0, valid=1):
        self.p.F117_IRADS_LOCK_VALID = valid
        self.p.F117_IRADS_LOCK_X, self.p.F117_IRADS_LOCK_Y, self.p.F117_IRADS_LOCK_Z = x, y, z

    def bias(self):
        bn, be, balt = self.ins.bias()
        return bn, be

    def test_active_destination_is_the_mission_point(self):
        point = self.nav.active_point()
        self.assertEqual((point.x, point.z), self.dest)
        bn, be = self.bias()
        self.assertGreater(math.hypot(bn, be), 100)  # an hour of drift is a real error

    # --- MARK ---------------------------------------------------------------------------------
    def test_mark_stores_the_irads_point_in_the_ins_frame(self):
        bn, be = self.bias()
        self.press('MARK')
        self.assertEqual((self.p.F117_MARK_ACTIVE, self.p.F117_MARK_X), (1, 1))  # no ground coordinates yet
        self.press('ENTR')
        self.assertEqual(self.nav.remaining(), 5)  # nothing stored without a point
        self.lock(5000, 7000, 120)
        self.nu.update()
        self.assertEqual(self.p.F117_MARK_X, 0)
        self.press('ENTR')
        mark = self.nav.dp(94)
        self.assertAlmostEqual(mark.x, 5000 + bn)
        self.assertAlmostEqual(mark.z, 7000 + be)
        self.assertAlmostEqual(mark.elev, 120)
        self.assertEqual((self.p.F117_MARK_ACTIVE, self.p.F117_MARK_LAST, self.nav.remaining()), (0, 94, 4))

    def test_mark_falls_back_to_the_hud_cursor_and_needs_irads_or_hud_selected(self):
        self.g.hud_on, self.g.hud_ground = True, self.lua.table_from([4000.0, 80.0, 6000.0])
        self.g.dss_state = 1
        self.press('MARK')
        self.assertEqual(self.p.F117_MARK_X, 0)
        self.press('ENTR')
        mark = self.nav.dp(94)
        self.assertEqual((mark.x, mark.z, mark.elev), (4000, 6000, 80))
        self.g.dss_state = 2  # MAP: not a position the manual defines for MARK
        self.press('MARK')
        self.nu.update()
        self.assertEqual(self.p.F117_MARK_X, 1)
        self.g.dss_state = 3  # down: not used
        self.nu.update()
        self.assertEqual(self.p.F117_MARK_X, 1)

    def test_mark_exits_on_mark_or_clr_and_runs_out_after_five(self):
        self.lock(1000, 1000)
        self.press('MARK'); self.press('MARK')
        self.assertEqual(self.p.F117_MARK_ACTIVE, 0)
        self.press('MARK'); self.press('CLR')
        self.assertEqual(self.p.F117_MARK_ACTIVE, 0)
        for i in range(5):
            self.lock(1000 + i, 1000)
            self.press('MARK'); self.press('ENTR')
        self.assertEqual([self.nav.dp(94 + i).x - self.bias()[0] for i in range(5)], [1000, 1001, 1002, 1003, 1004])
        self.press('MARK')
        self.assertEqual(self.p.F117_MARK_ACTIVE, 0)  # inoperative: five used

    def test_mark_is_not_available_in_manual_map_mode_and_ground_activations_count(self):
        self.g.map_manual = 1
        self.press('MARK')
        self.assertEqual(self.p.F117_MARK_ACTIVE, 0)
        self.g.map_manual = 0
        self.p.F117_WOW = 1
        self.press('MARK'); self.press('MARK'); self.press('MARK')  # on, off, on: two activations on the ground
        self.assertEqual(self.nav.remaining(), 3)

    # --- SNSR ----------------------------------------------------------------------------------
    def test_irads_update_removes_the_ins_error(self):
        bn, be = self.bias()
        self.lock(*self.dest)  # the pilot has the sensor on the destination itself
        self.press('SNSR')
        self.nu.update()
        self.assertEqual((self.p.F117_SNSR_ACTIVE, self.p.F117_SNSR_BOXED, self.p.F117_SNSR_VALID), (1, 0, 1))
        self.assertAlmostEqual(self.p.F117_SNSR_RNG, min(99.99, math.hypot(bn, be) / NM), places=3)
        expected_bearing = math.degrees(math.atan2(-be, -bn)) % 360
        self.assertAlmostEqual(self.p.F117_SNSR_BRG, expected_bearing, places=3)
        self.press('ENTR')
        self.assertAlmostEqual(self.ins.magnitude_nm(), 0, places=6)
        self.assertAlmostEqual(self.ins.total_n, -bn)
        self.assertAlmostEqual(self.ins.total_e, -be)
        for got, want in zip(self.nav.bias(), (-bn, -be, 0)):  # DP 99
            self.assertAlmostEqual(got, want)
        self.assertEqual((self.p.F117_SNSR_ACTIVE, self.p.F117_SNSR_VALID), (0, 0))

    def test_pilot_cursor_error_is_what_remains_after_the_update(self):
        bn, be = self.bias()
        self.lock(self.dest[0] + 300, self.dest[1] - 400)  # 300 m north and 400 m west of the destination
        self.press('SNSR'); self.press('ENTR')
        rn, re = self.bias()
        # The cursor was 300 m north and 400 m west of the destination, so the INS now reads the aircraft
        # 300 m south and 400 m east of where it is: the pilot's error, with the opposite sign.
        self.assertAlmostEqual(rn, -300)
        self.assertAlmostEqual(re, 400)

    def test_snsr_is_boxed_until_the_conditions_are_met(self):
        self.press('SNSR')
        self.assertEqual((self.p.F117_SNSR_ACTIVE, self.p.F117_SNSR_BOXED, self.p.F117_SNSR_VALID), (1, 1, 0))
        self.press('ENTR')
        self.assertEqual(self.p.F117_SNSR_ACTIVE, 1)  # nothing to accept yet
        self.lock(*self.dest)
        self.g.dss_state = 2  # MAP: SNSR stays boxed
        self.nu.update()
        self.assertEqual(self.p.F117_SNSR_BOXED, 1)
        self.g.dss_state = 0
        self.nu.update()
        self.assertEqual((self.p.F117_SNSR_BOXED, self.p.F117_SNSR_VALID), (0, 1))

    def test_hud_update_is_used_when_irads_has_no_lock(self):
        bn, be = self.bias()
        self.g.dss_state = 1
        self.g.hud_on = True
        # Cursor on the destination: the INS projects it from where it believes the aircraft is.
        self.g.hud_ground = self.lua.table_from([self.dest[0] + bn, 0.0, self.dest[1] + be])
        self.press('SNSR'); self.nu.update()
        self.assertEqual(self.p.F117_SNSR_VALID, 1)
        self.press('ENTR')
        self.assertAlmostEqual(self.ins.magnitude_nm(), 0, places=6)

    def test_irads_needs_the_aircraft_above_the_ground_at_the_reference(self):
        self.g.ground_height = 5000.0  # terrain above the aircraft (true altitude is 3000 m)
        self.lock(*self.dest)
        self.press('SNSR'); self.nu.update()
        self.assertEqual((self.p.F117_SNSR_BOXED, self.p.F117_SNSR_VALID), (1, 0))
        self.g.ground_height = 500.0
        self.nu.update()
        self.assertEqual(self.p.F117_SNSR_VALID, 1)

    def test_laser_range_adds_an_altitude_correction_otherwise_none(self):
        self.ins.apply_correction(0, 0, 25.0)  # an altitude error in the INS
        self.lock(*self.dest)
        self.press('SNSR'); self.nu.update()
        self.assertEqual(self.p.F117_SNSR_ALT, 0)
        self.p.F117_LASER_ARMED = 1
        self.nu.update()
        self.assertAlmostEqual(self.p.F117_SNSR_ALT, -25.0 * 3.2808399, places=3)

    def test_clr_and_deselect_reject_without_changing_the_ins(self):
        before = self.bias()
        self.lock(*self.dest)
        self.press('SNSR'); self.nu.update()
        self.press('CLR')
        self.assertEqual((self.p.F117_SNSR_ACTIVE, self.p.F117_SNSR_VALID), (0, 0))
        self.press('SNSR'); self.press('SNSR')
        self.assertEqual(self.p.F117_SNSR_ACTIVE, 0)
        self.assertEqual(self.bias(), before)
        self.assertEqual(self.nav.dp(99).x, 0)

    def test_corrections_accumulate_as_a_vector_sum(self):
        self.lock(*self.dest)
        self.press('SNSR'); self.press('ENTR')  # removes the drift
        self.ins.update(1.0, True, True)
        for _ in range(1800):
            self.ins.update(1.0, True, True)    # half an hour more drift
        b2 = self.bias()
        self.press('SNSR'); self.press('ENTR')
        self.assertAlmostEqual(self.ins.total_n, self.ins.total_n)  # recorded
        self.assertEqual(tuple(self.nav.bias())[:2], (self.ins.total_n, self.ins.total_e))
        self.assertAlmostEqual(self.ins.magnitude_nm(), 0, places=6)
        self.assertGreater(math.hypot(b2[0], b2[1]), 0)

    def test_a_120_nm_correction_raises_posunr_and_inhibits_until_cleared(self):
        self.lock(self.dest[0] + 130 * NM, self.dest[1])
        self.press('SNSR'); self.nu.update()
        self.assertEqual((self.p.F117_INS_POSUNR, self.p.F117_INS_ALERT), (0, 0))  # published on the INS tick
        self.assertFalse(self.nu.sensor_active())
        self.ins.update(.05, True, True)
        self.assertEqual((self.p.F117_INS_POSUNR, self.p.F117_INS_ALERT), (1, 1))
        self.assertEqual(list(self.g.messages.values()), ['POSUNR', 'INS'])
        self.lock(*self.dest)
        self.press('SNSR')
        self.assertFalse(self.nu.sensor_active())  # inhibited
        self.press('CLR')
        self.ins.update(.05, True, True)
        self.assertEqual((self.p.F117_INS_POSUNR, self.p.F117_INS_ALERT), (0, 0))
        self.press('SNSR')
        self.assertTrue(self.nu.sensor_active())

    # --- map UPDT --------------------------------------------------------------------------------
    def test_map_update_compares_the_map_cursor_with_the_irads_point(self):
        bn, be = self.bias()
        self.g.dss_state = 2
        self.lock(7000, 9000)
        self.press('UPDT')
        calls = [tuple(v.values()) for v in self.g.cursor_calls.values()]
        self.assertEqual(calls[-1][0], True)
        self.assertAlmostEqual(calls[-1][1], 7000 + bn)  # the cursor starts on the point as the INS plots it
        self.assertAlmostEqual(calls[-1][2], 9000 + be)
        self.assertEqual(self.p.F117_UPDT_ACTIVE, 1)
        self.nu.update()
        self.assertEqual(self.p.F117_SNSR_VALID, 0)  # nothing until the pilot designates
        self.g.mx, self.g.mz = 7000.0, 9000.0        # slewed onto the landmark's true position
        self.nu.designate(2)
        self.nu.update()
        self.assertEqual((self.p.F117_UPDT_LATCHED, self.p.F117_SNSR_VALID), (1, 1))
        self.press('ENTR')
        self.assertAlmostEqual(self.ins.magnitude_nm(), 0, places=6)
        self.assertEqual(self.p.F117_UPDT_ACTIVE, 0)

    def test_map_update_needs_the_switch_on_map_an_irads_point_and_auto_mode(self):
        self.lock(7000, 9000)
        self.press('UPDT')
        self.assertEqual(self.p.F117_UPDT_ACTIVE, 0)  # switch on IRADS
        self.g.dss_state = 2
        self.g.map_manual = 2
        self.press('UPDT')
        self.assertEqual(self.p.F117_UPDT_ACTIVE, 0)  # manual map mode
        self.g.map_manual = 0
        self.lock(7000, 9000, valid=0)
        self.press('UPDT')
        self.assertEqual(self.p.F117_UPDT_ACTIVE, 0)  # no IRADS point

    def test_map_update_is_rejected_by_updt_the_switch_or_losing_the_irads_point(self):
        self.g.dss_state = 2
        self.lock(7000, 9000)
        self.press('UPDT'); self.press('UPDT')
        self.assertEqual(self.p.F117_UPDT_ACTIVE, 0)
        self.press('UPDT')
        self.nu.on_dss_change(0)  # switch back to CENTER
        self.assertEqual(self.p.F117_UPDT_ACTIVE, 0)
        self.press('UPDT')
        self.lock(7000, 9000, valid=0)
        self.nu.update()
        self.assertEqual(self.p.F117_UPDT_ACTIVE, 0)
        self.assertFalse(bool(list(self.g.cursor_calls.values())[-1][1]))  # cursor removed

    def test_functions_are_mutually_exclusive(self):
        self.lock(*self.dest)
        self.press('MARK')
        self.press('SNSR')
        self.assertEqual((self.p.F117_MARK_ACTIVE, self.p.F117_SNSR_ACTIVE), (0, 1))
        self.press('MARK')
        self.assertEqual((self.p.F117_MARK_ACTIVE, self.p.F117_SNSR_ACTIVE), (1, 0))

    def test_only_press_events_for_known_commands_are_consumed(self):
        self.assertFalse(self.nu.set_command(self.c.MARK, 0))
        self.assertFalse(self.nu.set_command(87, 1))


if __name__ == '__main__':
    unittest.main()
