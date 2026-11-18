"""Control-stick Designate Select switch: routes throttle slew/designate to IRADS, the HUD cursor or the map."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/cockpit'))
from check_display_calibration import runtime  # noqa: E402

S = ROOT / 'Cockpit/Scripts'


class DesignateSelectTests(unittest.TestCase):
    def setUp(self):
        self.lua, self.load = runtime()
        self.load(S / 'command_defs.lua')
        self.lua.execute('''
            events={};slews={};designated={};recenters=0;returns=0
            function record(_,id,value)events[#events+1]={id,value}end
            hud={slew=function(dx,dy,dt)slews[#slews+1]={'hud',dx,dy,dt}end,recenter=function()recenters=recenters+1 end}
            map={slew=function(dx,dy,dt)slews[#slews+1]={'map',dx,dy,dt}end,return_to_dp=function()returns=returns+1 end}
        ''')
        self.g = self.lua.globals()
        self.dss = self.load(S / 'Systems/DesignateSelect.lua').new(self.lua.eval(
            '{dispatch=record,hud=hud,map=map,on_designate=function(s)designated[#designated+1]=s end}'))
        self.n = self.g.native_commands
        self.h = self.g.hotas_commands
        self.f = self.g.f117_commands
        self.p = self.g._parameters

    def events(self):
        out = [tuple(e.values()) if hasattr(e, 'values') else e for e in self.g.events.values()]
        self.lua.execute('events={}')
        return out

    def test_center_forwards_to_the_efm_unchanged(self):
        self.assertEqual(self.dss.state(), 0)
        self.assertTrue(self.dss.set_command(self.n.SELECTER_UP, 1))
        self.assertEqual(self.events(), [(self.h.THROTTLE_DESIGNATOR_CONTROLLER_UP, 1.0)])
        self.assertTrue(self.dss.set_command(self.n.SELECTER_STOP, 0))
        ids = [self.h.THROTTLE_DESIGNATOR_CONTROLLER_UP, self.h.THROTTLE_DESIGNATOR_CONTROLLER_DOWN,
               self.h.THROTTLE_DESIGNATOR_CONTROLLER_LEFT, self.h.THROTTLE_DESIGNATOR_CONTROLLER_RIGHT]
        self.assertEqual(self.events(), [(i, 0.0) for i in ids])
        self.dss.set_command(self.n.TDC_DEPRESS_ON, 1)
        self.dss.set_command(self.n.TDC_DEPRESS_OFF, 0)
        d = self.h.THROTTLE_DESIGNATOR_CONTROLLER_DEPRESS
        self.assertEqual(self.events(), [(d, 1.0), (d, 0.0)])
        self.dss.set_command(self.g.irads_axis_commands.HORIZONTAL, -.4)
        self.dss.set_command(self.g.irads_axis_commands.VERTICAL, .7)
        self.assertEqual(self.events(), [(self.f.IRADS_SLEW_HORIZONTAL, -.4), (self.f.IRADS_SLEW_VERTICAL, .7)])

    def test_leaving_irads_releases_every_efm_demand_once(self):
        self.assertTrue(self.dss.set_command(self.n.DSS_UP, 1))
        self.assertEqual(self.dss.state(), 1)
        self.assertEqual(self.p.F117_DSS, 1)
        released = self.events()
        self.assertEqual(len(released), 7)  # four directions, two axes, depress
        self.assertTrue(all(e[1] == 0.0 for e in released))
        self.dss.set_command(self.n.DSS_UP, 1)  # already there: nothing more
        self.assertEqual(self.events(), [])

    def test_hud_state_integrates_held_keys_and_never_reaches_the_efm(self):
        self.dss.set_command(self.n.DSS_UP, 1); self.events()
        self.dss.set_command(self.n.SELECTER_RIGHT, 1)
        self.dss.set_command(self.n.SELECTER_UP, 1)
        self.assertEqual(self.events(), [])
        self.dss.update(.05)
        self.assertEqual([tuple(v.values()) for v in self.g.slews.values()], [('hud', 1, 1, .05)])
        self.dss.set_command(self.n.SELECTER_STOP, 0)
        self.lua.execute('slews={}'); self.dss.update(.05)
        self.assertEqual(len(self.g.slews), 0)

    def test_axis_beats_keys_outside_the_deadzone_and_is_ignored_inside_it(self):
        self.dss.set_command(self.n.DSS_LEFT, 1); self.events()
        self.assertEqual(self.dss.state(), 2)
        self.dss.set_command(self.g.irads_axis_commands.HORIZONTAL, .03)
        self.dss.update(.05)
        self.assertEqual(len(self.g.slews), 0)
        self.dss.set_command(self.g.irads_axis_commands.HORIZONTAL, -.5)
        self.dss.set_command(self.g.irads_axis_commands.VERTICAL, 9)  # clamped
        self.dss.update(.05)
        self.assertEqual([tuple(v.values()) for v in self.g.slews.values()], [('map', -.5, 1, .05)])
        self.assertEqual(self.events(), [])

    def test_designate_acts_on_release_for_hud_and_map(self):
        self.dss.set_command(self.n.DSS_UP, 1)
        self.dss.set_command(self.n.TDC_DEPRESS_OFF, 0)  # release without a press: nothing
        self.assertEqual(self.dss.designates(), 0)
        self.dss.set_command(self.n.TDC_DEPRESS_ON, 1)
        self.assertEqual(self.dss.designates(), 0)
        self.dss.set_command(self.n.TDC_DEPRESS_OFF, 0)
        self.assertEqual((self.dss.designates(), self.p.F117_DSS_DESIGNATE), (1, 1))
        self.assertEqual(list(self.g.designated.values()), [1])
        self.dss.set_command(self.n.DSS_LEFT, 1)
        self.dss.set_command(self.n.TDC_DEPRESS_ON, 1); self.dss.set_command(self.n.TDC_DEPRESS_OFF, 0)
        self.assertEqual(list(self.g.designated.values()), [1, 2])

    def test_down_and_right_select_nothing(self):
        for command in (self.n.DSS_DOWN, self.n.DSS_RIGHT):
            self.dss.set_command(self.n.DSS_OFF, 1)
            self.dss.set_command(command, 1); self.events()
            self.assertEqual(self.dss.state(), 3)
            self.dss.set_command(self.n.SELECTER_UP, 1)
            self.dss.set_command(self.n.TDC_DEPRESS_ON, 1); self.dss.set_command(self.n.TDC_DEPRESS_OFF, 0)
            self.dss.update(.05)
            self.assertEqual((self.events(), len(self.g.slews), self.dss.designates()), ([], 0, 0))
        self.dss.set_command(self.n.DSS_OFF, 1)
        self.assertEqual(self.dss.state(), 0)

    def test_scan_return_recentres_the_selected_cursor_only(self):
        self.dss.set_command(self.n.SENSOR_RESET, 1)
        self.assertEqual((self.g.recenters, self.g.returns), (0, 0))  # IRADS: the EFM does it
        self.dss.set_command(self.n.DSS_UP, 1); self.dss.set_command(self.n.SENSOR_RESET, 1)
        self.assertEqual((self.g.recenters, self.g.returns), (1, 0))
        self.dss.set_command(self.n.DSS_LEFT, 1); self.dss.set_command(self.n.SENSOR_RESET, 1)
        self.assertEqual((self.g.recenters, self.g.returns), (1, 1))

    def test_unrelated_commands_are_not_consumed(self):
        self.assertFalse(self.dss.set_command(87, 1))
        self.assertFalse(self.dss.set_command(self.g.irads_axis_commands.ZOOM, .5))


class MapCursorTests(unittest.TestCase):
    def setUp(self):
        self.lua, self.load = runtime()
        self.load(S / 'command_defs.lua')
        self.lua.execute('''
            allowed=false;x=1000;z=2000
            function get_base_data()return {getHeading=function()return 0 end,
                getSelfVelocity=function()return 200,0,0 end,getSelfCoordinates=function()return x,100,z end}end
            function require()return {convertMetersToLatLon=function()return 42.5,-20.5 end}end
            nav={route=function()return {{x=5000,z=-3000,kind="navigation",number=1,label="1"},
                {x=9000,z=4000,kind="navigation",number=2,label="2"}} end,active=function()return 2 end}
        ''')
        self.g = self.lua.globals()
        self.map = self.load(S / 'Systems/MovingMap.lua').new(
            None, None, self.g.nav, self.lua.eval('{manual_allowed=function()return allowed end}'))
        self.map.initialize()
        self.p = self.g._parameters
        self.c = self.g.map_commands

    def test_look_and_scroll_need_the_switch_on_map(self):
        self.map.set_command(self.c.LOOK, 1)
        self.assertEqual(self.p.F117_MAP_MANUAL, 0)
        self.map.set_command(self.c.SCROLL, 1)
        self.assertEqual(self.p.F117_MAP_MANUAL, 0)
        self.g.allowed = True
        self.map.set_command(self.c.LOOK, 1)
        self.assertEqual(self.p.F117_MAP_MANUAL, 1)
        self.g.allowed = False
        self.map.set_command(self.c.LOOK, 1)  # leaving manual is always possible
        self.assertEqual(self.p.F117_MAP_MANUAL, 0)

    def test_manual_mode_starts_at_the_selected_destination_and_look_is_north_up(self):
        self.g.allowed = True
        self.map.set_command(self.c.ORIENTATION, 1)  # CTUP
        self.map.set_command(self.c.LOOK, 1)
        self.assertEqual(self.p.F117_MAP_ORIENTATION_TEXT, 'CNUP')
        # Own ship at (1000, 2000); the view centre is the active destination (9000, 4000).
        self.assertAlmostEqual(self.p.F117_MAP_VIEW_CENTER_X, 9000)
        self.assertAlmostEqual(self.p.F117_MAP_VIEW_CENTER_Z, 4000)

    def test_slew_moves_the_cursor_and_return_goes_back_to_the_destination(self):
        self.g.allowed = True
        self.map.set_command(self.c.SCROLL, 1)
        self.map.slew(1, 0, 1.0)  # full east for one second: a quarter of the 25 nm range
        self.map.update()
        self.assertAlmostEqual(self.p.F117_MAP_VIEW_CENTER_Z, 4000 + 25 * 1852 * .25)
        self.assertAlmostEqual(self.p.F117_MAP_VIEW_CENTER_X, 9000)
        self.map.return_to_dp(); self.map.update()
        self.assertAlmostEqual(self.p.F117_MAP_VIEW_CENTER_Z, 4000)

    def test_slew_and_return_do_nothing_in_auto_mode(self):
        self.map.update()
        before = (self.p.F117_MAP_VIEW_CENTER_X, self.p.F117_MAP_VIEW_CENTER_Z)
        self.map.slew(1, 1, 1.0); self.map.return_to_dp(); self.map.update()
        self.assertEqual(before, (self.p.F117_MAP_VIEW_CENTER_X, self.p.F117_MAP_VIEW_CENTER_Z))


if __name__ == '__main__':
    unittest.main()
