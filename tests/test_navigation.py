"""Mission route source, active waypoint sequencing and HSD/VSD/MAP route readouts."""
import math,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/cockpit'))
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

    def load_route(self):
        for _ in range(200):self.nav.update()  # the route loads on the first retry tick

    def test_air_start_point_is_never_a_destination(self):
        self.lua.execute('''
            function get_mission_route()return {
                {x=0,y=0,type="Turning Point"},
                {x=20*1852,y=0,type="Turning Point"},
                {x=20*1852,y=10*1852,type="Turning Point"}}end
        ''')
        nav=self.load(S/'Systems/Navigation.lua').new();nav.initialize()
        for _ in range(200):nav.update()
        self.assertEqual(nav.active_point().number,1)
        nav.set_command(self.g.nav_commands.WP_PREV,1)
        self.assertEqual(nav.active_point().number,1)

    def test_radio_altitude_is_above_ground_and_baro_is_msl(self):
        self.lua.execute('''
            function require()return {GetHeight=function(x,z)return 300 end}end
            function get_mission_route()return {
                {x=0,y=0,alt=0,alt_type="RADIO"},
                {x=1,y=1,alt=50,alt_type="RADIO"},
                {x=2,y=2,alt=500,alt_type="BARO"}}end
        ''')
        nav=self.load(S/'Systems/Navigation.lua')
        route=nav.parse(self.g.get_mission_route())
        self.assertEqual([route[i].elev for i in (1,2,3)],[300,350,500])

    def test_marks_take_destination_numbers_94_to_98_in_order_then_run_out(self):
        self.load_route()
        self.assertEqual(self.nav.remaining(),5)
        self.assertEqual(self.p.F117_NAV_MARK_REMAINING,5)
        numbers=[self.nav.add_mark(1000+i,2000+i,50) for i in range(5)]
        self.assertEqual(numbers,[94,95,96,97,98])
        self.assertEqual((self.nav.remaining(),self.p.F117_NAV_MARK_REMAINING),(0,0))
        self.assertIsNone(self.nav.add_mark(1,2,3))   # five used: the function is inoperative
        self.assertEqual(len(self.nav.marks()),5)
        self.assertIsNone(self.nav.add_mark(float('nan'),0,0))

    def test_ground_activations_use_up_marks(self):
        self.load_route()
        self.nav.consume_ground_mark();self.nav.consume_ground_mark()
        self.assertEqual(self.nav.remaining(),3)
        self.assertEqual([self.nav.add_mark(i,i,0) for i in range(4)],[94,95,96,None])
        for _ in range(10):self.nav.consume_ground_mark()
        self.assertEqual(self.nav.remaining(),0)

    def test_dp_lookup_covers_route_marks_and_the_bias_point(self):
        self.load_route()
        self.nav.add_mark(1234,5678,90)
        mark=self.nav.dp(94)
        self.assertEqual((mark.x,mark.z,mark.elev,mark.kind,mark.label),(1234,5678,90,'mark','94'))
        self.assertEqual(self.nav.dp(1).number,1)
        self.assertIsNone(self.nav.dp(97))
        self.nav.set_bias(100,-200,30)
        bias=self.nav.dp(99)
        self.assertEqual((bias.x,bias.z,bias.elev,bias.kind),(100,-200,30,'bias'))
        self.assertEqual(tuple(self.nav.bias()),(100,-200,30))

    def test_waypoint_stepping_continues_into_the_marks_without_changing_the_route(self):
        self.load_route()
        self.nav.add_mark(5000,6000,0);self.nav.add_mark(7000,8000,0)
        route_length=len(self.nav.route())
        self.assertEqual(route_length,4)
        for _ in range(10):self.nav.set_command(self.g.nav_commands.WP_NEXT,1)
        self.assertEqual(self.nav.active(),route_length+2)
        self.assertEqual(self.nav.active_point().number,95)
        self.assertEqual(self.p.F117_NAV_DEST,95)
        self.assertEqual(self.p.F117_NAV_D_TEXT,'D  95')
        self.assertEqual(len(self.nav.route()),route_length)      # marks never join route[]
        self.nav.set_command(self.g.nav_commands.WP_PREV,1)
        self.assertEqual(self.nav.active_point().number,94)
        self.nav.set_command(self.g.nav_commands.WP_PREV,1)
        self.assertEqual(self.nav.active_point().number,self.nav.route()[route_length].number)  # back on the last route point

    def test_a_mark_is_never_auto_sequenced_past(self):
        self.load_route()
        self.nav.add_mark(5000,6000,0)
        for _ in range(10):self.nav.set_command(self.g.nav_commands.WP_NEXT,1)
        self.g.x,self.g.z=5000-3*NM,6000          # approach from outside the capture radius
        self.nav.update()
        self.g.x,self.g.z=5000,6000                # over the mark
        for _ in range(5):self.nav.update()
        self.assertEqual(self.nav.active_point().number,94)

    def test_initialize_clears_marks_and_the_bias_point(self):
        self.load_route()
        self.nav.add_mark(1,2,3);self.nav.consume_ground_mark();self.nav.set_bias(1,2,3)
        self.nav.initialize()
        self.assertEqual((self.nav.remaining(),len(self.nav.marks())),(5,0))
        self.assertEqual(tuple(self.nav.bias()),(0,0,0))

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
        self.assertEqual(self.logged()[0],'F117_NAV: route: 4 points, fields: type,x,y')
        self.assertEqual(len(self.logged()),5)
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

    def test_reselect_passed_waypoint_activates_stable_direct_to_then_resumes_route(self):
        self.g.x=20*NM;self.g.z=-5*NM;self.nav.update()
        self.nav.set_command(self.g.nav_commands.WP_NEXT,1)  # destination 02
        self.g.z=9.5*NM;self.nav.update()  # capture -> destination 03
        self.assertEqual(self.nav.active_point().number,3)
        self.g.z=10.5*NM;self.nav.update()
        self.nav.set_command(self.g.nav_commands.WP_PREV,1)
        self.assertEqual(self.nav.active_point().number,2)
        self.assertAlmostEqual(self.p.F117_NAV_COURSE,270)
        self.assertAlmostEqual(self.p.F117_NAV_BEARING,270)
        self.assertAlmostEqual(self.p.F117_NAV_RANGE_NM,.5)
        self.assertEqual((self.p.F117_NAV_DEST_X,self.p.F117_NAV_DEST_Z),(20*NM,10*NM))
        self.g.heading=-math.pi/2;self.g._parameters.HEADING_HUD=84
        self.nav.update()
        self.assertAlmostEqual(self.p.F117_NAV_REL_COURSE,-math.pi)
        self.assertEqual(self.p.F117_NAV_CRS_TEXT,'CRS 264')
        # Remain inside capture radius: no immediate sequence, even across the
        # original leg's endpoint plane. Course stays fixed; bearing still moves.
        self.g.x=19.5*NM;self.g.z=9.5*NM;self.nav.update()
        self.assertEqual(self.nav.active_point().number,2)
        self.assertAlmostEqual(self.p.F117_NAV_COURSE,270)
        self.assertAlmostEqual(self.p.F117_NAV_BEARING,45)
        self.g.x=20*NM;self.g.z=12*NM;self.nav.update()  # arm from outside
        self.g.z=10.5*NM;self.nav.update()  # return -> planned 02 -> 03 south
        self.assertEqual(self.nav.active_point().number,3)
        self.assertAlmostEqual(self.p.F117_NAV_COURSE,180)

    def test_manual_selection_before_waypoint_also_uses_direct_to(self):
        self.g.x=18*NM;self.g.z=0;self.nav.update()
        self.nav.set_command(self.g.nav_commands.WP_NEXT,1)
        expected=math.degrees(math.atan2(10,2))
        self.assertAlmostEqual(self.p.F117_NAV_COURSE,expected)
        self.g.x=17*NM;self.nav.update()
        self.assertAlmostEqual(self.p.F117_NAV_COURSE,expected)
        self.assertNotAlmostEqual(self.p.F117_NAV_BEARING,expected)
        # Initialization must discard the manually activated course.
        self.nav.initialize();self.nav.update()
        self.assertAlmostEqual(self.p.F117_NAV_COURSE,0)

    def test_direct_to_waits_for_valid_position_and_ignores_clamped_steps(self):
        self.nav.update()
        self.g.x=float('nan')
        self.nav.set_command(self.g.nav_commands.WP_NEXT,1)
        self.assertEqual(self.p.F117_NAV_VALID,0)
        self.g.x=20*NM;self.g.z=12*NM;self.nav.update()
        self.assertAlmostEqual(self.p.F117_NAV_COURSE,270)
        self.nav.set_command(self.g.nav_commands.WP_NEXT,1)  # final route point
        course=self.p.F117_NAV_COURSE
        self.g.x=18*NM;self.nav.update()
        self.nav.set_command(self.g.nav_commands.WP_NEXT,1)  # clamped
        self.assertAlmostEqual(self.p.F117_NAV_COURSE,course)

    def test_manual_selection_at_waypoint_keeps_inbound_course(self):
        self.nav.update()
        self.g.x=20*NM;self.g.z=10*NM
        self.nav.set_command(self.g.nav_commands.WP_NEXT,1)
        self.assertEqual(self.nav.active_point().number,2)
        self.assertAlmostEqual(self.p.F117_NAV_COURSE,90)
        self.g.z=10*NM+.1;self.nav.update()
        self.assertAlmostEqual(self.p.F117_NAV_COURSE,90)

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
