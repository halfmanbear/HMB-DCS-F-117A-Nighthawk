"""Free HUD cursor (Designate Select = HUD): slew, slaving, clamping and the manual's ground-point rules."""
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/cockpit'))
from check_display_calibration import runtime  # noqa: E402

S = ROOT / 'Cockpit/Scripts'


class HudCursorTests(unittest.TestCase):
    def setUp(self):
        self.lua, self.load = runtime()
        self.lua.execute('''
            att={heading=0,pitch=0,roll=0,x=1000,y=2000,z=3000}
            sensor={getHeading=function()return att.heading end,getPitch=function()return att.pitch end,
                getRoll=function()return att.roll end,getSelfCoordinates=function()return att.x,att.y,att.z end}
            ref=0
        ''')
        self.g = self.lua.globals()
        self.module = self.load(S / 'Systems/HudCursor.lua')
        self.p = self.g._parameters

    def cursor(self):
        return self.module.new(self.lua.eval('{attitude=sensor,reference_elevation=function()return ref end}'))

    def ground(self, *args):
        result = self.module.ground_point(*args)  # (nil, reason) comes back as a tuple
        return result[0] if isinstance(result, tuple) else result

    def forward(self, n, u, e, heading, pitch, roll):
        """OCIP_data.lua body(), reproduced for the round trip."""
        h = -heading
        ch, sh, cp, sp, cr, sr = math.cos(h), math.sin(h), math.cos(pitch), math.sin(pitch), math.cos(roll), math.sin(roll)
        along = n * ch + e * sh
        level_right = -n * sh + e * ch
        level_up = u * cp - along * sp
        return along * cp + u * sp, level_right * cr - level_up * sr, level_up * cr + level_right * sr

    def test_world_direction_inverts_the_hud_projection(self):
        for heading, pitch, roll in [(0, 0, 0), (1.1, .2, -.3), (-2.5, -.15, .9), (3.0, .05, 1.4)]:
            for x, y in [(0, 0), (.1, -.05), (-.17, .06), (.02, -.17)]:
                n, u, e = self.module.world_direction(x, y, heading, pitch, roll)
                f, r, up = self.forward(n, u, e, heading, pitch, roll)
                self.assertGreater(f, 0)
                self.assertAlmostEqual(r / f, x, places=9)
                self.assertAlmostEqual(up / f, y, places=9)

    def test_ground_point_is_the_intersection_with_the_reference_plane(self):
        pos = self.lua.table_from([1000, 2000, 3000])
        # Heading 0 is north. Looking 45 degrees down from 2000 m with the ground at 500 m: 1500 m ahead.
        point = self.ground(0, -1, 0, 0, 0, pos, 500)
        self.assertAlmostEqual(point[1], 1000 + 1500)
        self.assertAlmostEqual(point[2], 500)
        self.assertAlmostEqual(point[3], 3000)
        # Heading east (counter-clockwise radians, so -90 degrees): the offset goes east.
        point = self.ground(0, -1, -math.pi / 2, 0, 0, pos, 500)
        self.assertAlmostEqual(point[1], 1000, places=6)
        self.assertAlmostEqual(point[3], 3000 + 1500, places=6)
        # Pitched nose-down 30 degrees, cursor on the axis: 1500 / tan(30) ahead.
        point = self.ground(0, 0, 0, -math.radians(30), 0, pos, 500)
        self.assertAlmostEqual(point[1], 1000 + 1500 / math.tan(math.radians(30)), places=6)

    def test_no_coordinates_at_or_above_the_horizon_or_below_the_reference(self):
        pos = self.lua.table_from([0, 2000, 0])
        self.assertIsNone(self.ground(0, 0, 0, 0, 0, pos, 0))  # exactly on the horizon
        self.assertIsNone(self.ground(0, .05, 0, 0, 0, pos, 0))
        self.assertIsNone(self.ground(0, -.1, 0, 0, 0, pos, 2500))  # reference above the aircraft
        self.assertIsNone(self.ground(float('nan'), 0, 0, 0, 0, pos, 0))

    def test_cursor_starts_slaved_to_the_irads_look_angle_and_returns_to_it(self):
        cursor = self.cursor()
        self.p.F117_OCIP_IRADS_LOOK_VALID = 1
        self.p.F117_OCIP_IRADS_LOOK_AZ = .05
        self.p.F117_OCIP_IRADS_LOOK_EL = -.08
        cursor.set_active(True)
        self.assertEqual(tuple(cursor.position()), (.05, -.08))
        cursor.slew(1, 0, .5)
        self.assertGreater(cursor.position()[0], .05)
        cursor.recenter()
        self.assertEqual(tuple(cursor.position()), (.05, -.08))
        self.p.F117_OCIP_IRADS_LOOK_VALID = 0  # no IRADS look: the centre of the HUD area
        cursor.recenter()
        self.assertEqual(tuple(cursor.position()), (0, -.05))

    def test_slew_rate_and_clamp_to_the_field_of_view(self):
        cursor = self.cursor()
        cursor.set_active(True)
        x0, y0 = cursor.position()
        cursor.slew(1, 1, .5)  # half a second at full deflection: 4 degrees (8 deg/s)
        x1, y1 = cursor.position()
        self.assertAlmostEqual(x1 - x0, math.radians(4))
        self.assertAlmostEqual(y1 - y0, math.radians(4))
        for _ in range(20):
            cursor.slew(1, 1, 1.0)
        x, y = cursor.position()
        self.assertLessEqual(math.hypot(x, y), math.tan(math.radians(10)) + 1e-12)
        self.assertLessEqual(x, math.radians(10) + 1e-12)
        for _ in range(40):
            cursor.slew(-1, -1, 1.0)
        x, y = cursor.position()
        self.assertGreaterEqual(x, -math.radians(10) - 1e-12)
        self.assertLessEqual(math.hypot(x, y), math.tan(math.radians(10)) + 1e-12)

    def test_inactive_cursor_ignores_slew_and_publishes_invalid(self):
        cursor = self.cursor()
        before = tuple(cursor.position())
        cursor.slew(1, 1, 1.0)
        cursor.update()
        self.assertEqual(tuple(cursor.position()), before)
        self.assertEqual(self.p.F117_HUDCUR_VALID, 0)
        self.assertEqual(self.p.F117_HUDCUR_GROUND_VALID, 0)
        cursor.set_active(True)
        cursor.update()
        self.assertEqual(self.p.F117_HUDCUR_VALID, 1)
        cursor.set_active(False)
        self.assertEqual(self.p.F117_HUDCUR_VALID, 0)

    def test_ground_point_is_published_below_the_horizon_only(self):
        cursor = self.cursor()
        self.g.att.pitch = -math.radians(10)  # nose low, so the area centre looks below the horizon
        cursor.set_active(True)
        cursor.update()
        self.assertEqual(self.p.F117_HUDCUR_GROUND_VALID, 1)
        self.assertAlmostEqual(self.p.F117_HUDCUR_GROUND_Y, 0)
        self.assertGreater(self.p.F117_HUDCUR_GROUND_X, 1000)
        self.g.att.pitch = math.radians(10)  # nose high: above the horizon, no coordinates
        cursor.update()
        self.assertEqual(self.p.F117_HUDCUR_GROUND_VALID, 0)
        self.g.ref = None  # no destination elevation either
        self.g.att.pitch = -math.radians(10)
        cursor.update()
        self.assertEqual(self.p.F117_HUDCUR_GROUND_VALID, 0)


if __name__ == '__main__':
    unittest.main()
