"""Mission route source, active waypoint sequencing and HSD/VSD/MAP route readouts."""
import math,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from check_display_calibration import runtime
S=ROOT/'Cockpit/Scripts'
NM=1852

class NavigationTests(unittest.TestCase):
    def setUp(self):
        self.lua,self.load=runtime();self.g=self.lua.globals()
        self.load(S/'command_defs.lua')
        self.lua.execute('''
            heading=0;vn=0;ve=0;x=0;z=0
            function get_base_data()return {
                getHeading=function()return heading end,
                getSelfVelocity=function()return vn,0,ve end,
                getSelfCoordinates=function()return x,100,z end}end
            function require()return {} end
            _logged={}
            log={INFO=1,write=function(tag,level,text)_logged[#_logged+1]=tag..": "..text end}
            -- Map layout points: x north, y east, as in the mission editor.
            function get_mission_route()return {
                {x=0,y=0,type="TakeOff"},
                {x=20*1852,y=0,type="Turning Point"},
                {x=20*1852,y=10*1852,type="Turning Point"},
                {x=0,y=10*1852,type="Land"}}end
        ''')
        self.p=self.g._parameters
        self.nav=self.load(S/'Systems/Navigation.lua').new()
        self.nav.initialize()

    def logged(self):
        return [self.g._logged[i] for i in range(1,len(self.g._logged)+1)]

    def test_no_route_shows_dashes_and_logs_once(self):
        self.g.get_mission_route=None
        for _ in range(1000):self.nav.update()
        self.assertEqual(self.p.F117_NAV_VALID,0)
        self.assertEqual(self.p.F117_NAV_D_TEXT,'D  --')
        self.assertEqual(self.p.F117_NAV_TTG_TEXT,'TTG --:--')
        self.assertEqual(self.p.F117_NAV_RNG_TEXT,'RNG ---.-')
        self.assertEqual(self.p.F117_NAV_CRS_TEXT,'CRS ---')
        self.assertEqual(self.p.F117_NAV_REL_COURSE,0)
        self.assertEqual(self.logged(),['F117_NAV: route unavailable'])

    def test_route_parsed_from_map_points_and_first_leg_selected(self):
        self.g.vn=200
        self.nav.update()
        self.assertEqual(self.logged(),['F117_NAV: route: 4 points, fields: type,x,y'])
        route=self.nav.route()
        self.assertEqual([route[i].label for i in range(1,5)],['00','01','02','03'])
        self.assertEqual(route[1].kind,'takeoff');self.assertEqual(route[2].kind,'navigation')
        self.assertEqual(route[3].z,10*NM)
        self.assertEqual(self.nav.active(),2)
        self.assertEqual(self.p.F117_NAV_VALID,1)
        self.assertEqual(self.p.F117_NAV_D_TEXT,'D  01')
        self.assertAlmostEqual(self.p.F117_NAV_RANGE_NM,20)
        self.assertEqual(self.p.F117_NAV_RNG_TEXT,'RNG  20.0')
        # 20 NM at 200 m/s.
        seconds=round(20*NM/200)
        self.assertEqual(self.p.F117_NAV_TTG_TEXT,'TTG %02d:%02d'%(seconds//60,seconds%60))
        # First leg from takeoff: direct bearing north, matching the card.
        self.g._parameters.HEADING_HUD=0
        self.nav.update()
        self.assertEqual(self.p.F117_NAV_CRS_TEXT,'CRS 000')

    def test_world_points_with_altitude_use_z_as_east(self):
        self.lua.execute('''function get_mission_route()return {route={
            {this_point_num=0,world_point={x=0,y=500,z=0},point_action="TAKEOFF"},
            {this_point_num=1,world_point={x=0,y=500,z=5*1852},point_action="TURNPOINT"}}}end''')
        self.nav.update()
        route=self.nav.route()
        self.assertEqual(route[2].z,5*NM);self.assertEqual(route[1].kind,'takeoff')
        self.assertAlmostEqual(self.p.F117_NAV_BEARING,90)

    def test_course_relative_to_heading_and_card_reference(self):
        self.g.x=20*NM;self.g.z=-5*NM;self.nav.update()
        # 5 NM short of 01, so it is not captured; step on to 02 by hand.
        self.nav.set_command(self.g.nav_commands.WP_NEXT,1)
        self.assertEqual(self.p.F117_NAV_D_TEXT,'D  02')
        # Leg 01 -> 02 runs east (090 true). Heading north: course is 90 deg right.
        self.assertAlmostEqual(self.p.F117_NAV_COURSE,90)
        self.assertAlmostEqual(self.p.F117_NAV_REL_COURSE,math.pi/2)
        # Heading east (DCS heading is counterclockwise): on course.
        self.g.heading=-math.pi/2;self.nav.update()
        self.assertAlmostEqual(self.p.F117_NAV_REL_COURSE,0)
        # Card shows magnetic 084 for true 090: CRS follows the card.
        self.g._parameters.HEADING_HUD=84;self.nav.update()
        self.assertEqual(self.p.F117_NAV_CRS_TEXT,'CRS 084')

    def test_auto_sequence_inside_one_nm_and_manual_steps(self):
        self.nav.update();self.assertEqual(self.nav.active(),2)
        self.g.x=20*NM-1000;self.nav.update()
        self.assertEqual(self.nav.active(),3)
        self.assertEqual(self.p.F117_NAV_D_TEXT,'D  02')
        c=self.g.nav_commands
        self.assertTrue(self.nav.set_command(c.WP_PREV,1));self.assertEqual(self.nav.active(),2)
        self.assertTrue(self.nav.set_command(c.WP_PREV,0));self.assertEqual(self.nav.active(),2)
        for _ in range(6):self.nav.set_command(c.WP_NEXT,1)
        self.assertEqual(self.nav.active(),4) # clamps at the last point
        self.assertFalse(self.nav.set_command(3014,1))

    def test_slow_aircraft_has_no_time_to_go(self):
        self.g.vn=20;self.nav.update()
        self.assertEqual(self.p.F117_NAV_TTG_TEXT,'TTG --:--')
        self.assertEqual(self.p.F117_NAV_VALID,1)

    def test_bad_records_end_the_route(self):
        self.lua.execute('''function get_mission_route()return {
            {x=0,y=0},{x=1000,y=0},{x="bad"},{x=3000,y=0}}end''')
        self.nav.update()
        self.assertEqual(len(self.nav.route()),2)

    def test_map_draws_route_labels_and_steering_leg(self):
        # Native set_string keeps "01" as text (see test_moving_map.py).
        self.lua.execute('''package={loadlib=function(path,entry)
            if entry~="luaopen_f117_params" then return nil,"not faked" end
            return function()return {set_string=function(name,text)_parameters[name]=text;return true end} end
        end}''')
        self.g.x=10*NM;self.nav.update()
        moving=self.load(S/'Systems/MovingMap.lua').new(None,None,self.nav)
        moving.initialize()
        self.assertEqual(self.p.F117_MAP_WP_2_LABEL,'01')
        self.assertEqual(self.p.F117_MAP_STEER_VISIBLE,1)
        # 25 NM over the 106 mm map height; waypoint 01 is 10 NM north of ownship.
        self.assertAlmostEqual(self.p.F117_MAP_STEER_X,0);self.assertAlmostEqual(self.p.F117_MAP_STEER_Y,0)
        self.assertAlmostEqual(self.p.F117_MAP_STEER_BY,.106/25*10)
        moving.set_command(self.g.map_commands.TACTICAL_DECLUTTER,1)
        moving.set_command(self.g.map_commands.TACTICAL_DECLUTTER,1)
        self.assertEqual(self.p.F117_MAP_STEER_VISIBLE,0)

if __name__=='__main__':unittest.main()
