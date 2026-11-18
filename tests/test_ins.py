"""INS position error model: alignment gating, drift, display-layer position and sensor-update correction."""
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/cockpit'))
from check_display_calibration import runtime  # noqa: E402

S = ROOT / 'Cockpit/Scripts'
NM = 1852.0


class InsTests(unittest.TestCase):
    def setUp(self):
        self.lua, self.load = runtime()
        self.lua.execute('''
            seq={0.5,0.25,0.0,1.0,0.5};n=0
            function fixed_random()n=n%#seq+1;return seq[n]end
            truth={x=1000,y=2000,z=3000}
            base={getSelfCoordinates=function()return truth.x,truth.y,truth.z end,getHeading=function()return 1.5 end}
        ''')
        self.g = self.lua.globals()
        self.module = self.load(S / 'Systems/INS.lua')
        self.p = self.g._parameters
        self.ins = self.module.new(self.lua.eval('{random=fixed_random}'))

    def test_unaligned_ins_reports_the_advisory_and_no_error(self):
        self.ins.update(.05, False, False)
        self.assertEqual((self.p.F117_INS_ADVISORY, self.p.F117_INS_ALIGNED), (0, 0))
        self.ins.update(.05, True, False)
        self.assertEqual((self.p.F117_INS_ADVISORY, self.p.F117_INS_ALIGNED), (1, 0))  # ALIGN
        self.assertEqual(tuple(self.ins.coordinates(1, 2, 3)), (1, 2, 3))
        self.ins.update(.05, True, True)
        self.assertEqual((self.p.F117_INS_ADVISORY, self.p.F117_INS_ALIGNED), (2, 1))  # INS UP

    def test_error_starts_small_and_drifts_at_the_documented_rate(self):
        self.ins.update(0, True, True)
        bn, be, balt = self.ins.bias()
        self.assertLessEqual(math.hypot(bn, be), self.module.INITIAL_ERROR_NM * NM + 1e-9)
        self.assertEqual(balt, 0)
        for _ in range(3600):
            self.ins.update(1.0, True, True)
        bn2, be2, _ = self.ins.bias()
        moved_nm = math.hypot(bn2 - bn, be2 - be) / NM
        self.assertGreaterEqual(moved_nm, self.module.DRIFT_NM_PER_HR * .5 - 1e-6)
        self.assertLessEqual(moved_nm, self.module.DRIFT_NM_PER_HR + 1e-6)
        self.assertAlmostEqual(self.p.F117_INS_BIAS_N, bn2)

    def test_error_is_deterministic_for_a_given_random_source(self):
        other = self.module.new(self.lua.eval('(function()local i=0;local s={0.5,0.25,0.0,1.0,0.5};'
                                              'return {random=function()i=i%#s+1;return s[i]end} end)()'))
        self.ins.update(0, True, True)
        other.update(0, True, True)
        self.assertEqual(tuple(self.ins.bias()), tuple(other.bias()))

    def test_wrapped_sensor_adds_the_bias_to_position_only(self):
        self.ins.update(0, True, True)
        for _ in range(600):
            self.ins.update(1.0, True, True)
        bn, be, balt = self.ins.bias()
        wrapped = self.ins.wrap(self.g.base)
        x, y, z = wrapped.getSelfCoordinates()
        self.assertAlmostEqual(x, 1000 + bn)
        self.assertAlmostEqual(z, 3000 + be)
        self.assertAlmostEqual(y, 2000 + balt)
        self.assertEqual(wrapped.getHeading(), 1.5)  # everything else passes through untouched
        self.assertEqual(tuple(wrapped.getInsBias()), (bn, be, balt))
        self.assertEqual(tuple(self.g.base.getSelfCoordinates()), (1000, 2000, 3000))  # truth is unchanged

    def test_correction_removes_the_bias_and_accumulates_in_the_total(self):
        self.ins.update(0, True, True)
        for _ in range(1200):
            self.ins.update(1.0, True, True)
        bn, be, balt = self.ins.bias()
        self.assertTrue(self.ins.apply_correction(-bn, -be, -balt))
        self.assertAlmostEqual(self.ins.magnitude_nm(), 0)
        self.assertAlmostEqual(self.ins.total_n, -bn)
        self.assertAlmostEqual(self.ins.total_e, -be)
        self.ins.update(1.0, True, True)  # drift carries on after an update
        self.assertGreater(self.ins.magnitude_nm(), 0)
        self.assertFalse(self.ins.apply_correction(float('nan'), 0, 0))

    def test_losing_power_loses_alignment_and_the_error(self):
        self.ins.update(0, True, True)
        for _ in range(100):
            self.ins.update(1.0, True, True)
        self.ins.update(1.0, False, False)
        self.assertEqual(tuple(self.ins.bias()), (0, 0, 0))
        self.assertEqual((self.ins.total_n, self.ins.total_e), (0, 0))
        self.ins.update(0, True, True)  # re-aligned: a fresh error is drawn
        self.assertNotEqual(tuple(self.ins.bias()), (0, 0, 0))

    def test_alerts_inhibit_updates_and_show_dead_reckoning(self):
        self.ins.update(.05, True, True)
        self.assertFalse(self.ins.inhibited())
        self.assertEqual(self.p.F117_NAV_DR, 0)
        self.ins.raise_alerts()
        self.ins.update(.05, True, True)
        self.assertTrue(self.ins.inhibited())
        self.assertEqual((self.p.F117_INS_POSUNR, self.p.F117_INS_ALERT, self.p.F117_NAV_DR), (1, 1, 1))
        self.ins.clear_alerts()
        self.ins.update(.05, True, True)
        self.assertEqual((self.p.F117_INS_POSUNR, self.p.F117_INS_ALERT, self.p.F117_NAV_DR), (0, 0, 0))


if __name__ == '__main__':
    unittest.main()
