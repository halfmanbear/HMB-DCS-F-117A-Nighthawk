import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / 'tools/fm_bench'
sys.path.insert(0, str(BENCH))

import sim  # noqa: E402


class FlightModelBenchTests(unittest.TestCase):
    def test_atmosphere_and_airspeed_conversions(self):
        temperature, pressure, density, sound = sim.isa(0.0)
        self.assertAlmostEqual(temperature, 288.15)
        self.assertAlmostEqual(pressure, 101325.0)
        self.assertAlmostEqual(density, 1.225, places=3)
        self.assertAlmostEqual(sound, 340.3, places=0)
        # The manual's own table: 424 KCAS is Mach 0.90 at 20,000 ft, and 347 KCAS is Mach 0.90 at 30,000 ft.
        self.assertAlmostEqual(sim.mach_from_cas(424.0, 20000 * sim.FT_TO_M), 0.90, places=2)
        self.assertAlmostEqual(sim.mach_from_cas(347.0, 30000 * sim.FT_TO_M), 0.90, places=2)
        self.assertAlmostEqual(sim.cas_from_mach(sim.mach_from_cas(300.0, 5000.0), 5000.0), 300.0, places=6)

    def test_pilot_stick_shaping_matches_the_flight_controls(self):
        source = self._efm_source('FlightControls/FlightControls.cpp')
        if source is None:
            self.skipTest('EFM source not found')
        self.assertIn('kNegativeStickForceScale = 180.0', source)
        self.assertIn('kPositiveStickForceScale = 80.0', source)
        self.assertGreater(sim.pitch_axis_for_nz_delta(2.0), 0.0)  # Aft stick asks for more g.
        self.assertLess(sim.pitch_axis_for_nz_delta(-0.5), 0.0)
        self.assertLessEqual(sim.pitch_axis_for_nz_delta(50.0), 1.0)
        self.assertEqual(sim.roll_axis_for_rate(0.0), 0.0)
        self.assertLess(sim.roll_axis_for_rate(-90.0), 0.0)

    def test_targets_are_complete_and_cite_the_manual(self):
        targets = json.loads((BENCH / 'targets.json').read_text(encoding='utf-8'))
        for name, block in targets.items():
            if isinstance(block, dict):
                self.assertTrue(block.get('note'), name)
        for table in targets['level_accel']['tables']:
            for row in table['rows']:
                self.assertEqual(len(row['min']), len(table['kcas']))
        block = targets['sustained_turn']
        for row in block['rows']:
            self.assertEqual(len(row['g']), len(block['mach']))
        for row in targets['climb']['rows']:
            self.assertEqual(len(row['min']), len(row['fuel_lb']))

    def test_bench_flies_the_built_efm_on_the_manuals_lift_line(self):
        dll = self._efm_dll()
        if dll is None:
            self.skipTest('EFM has not been built here')
        script = (
            "import sys, tempfile\n"
            f"sys.path.insert(0, {str(BENCH)!r})\n"
            "import efm, scenarios, sim\n"
            "efm.build_stub()\n"
            f"s = sim.Sim(efm.Efm({str(dll)!r}, tempfile.mkdtemp()), (40000, 260000, 225000))\n"
            "got = scenarios.trim_aoa(s, 32000, 222, 0, False)\n"
            "weight = s.mass / sim.LB_TO_KG\n"
            "stop = scenarios.roll_stop(s, 40000, 400, 10000, 1.0)\n"
            "bumps = scenarios.ground_bumps(s)\n"
            "print(got['aoa'], got['nz'], weight, stop['reversal'], stop['late_swing'])\n"
            "print(*(bumps[k] for k in ('air_roll', 'air_pitch', 'ground_roll', 'ground_pitch', 'ground_stick_roll', 'after_roll', 'after_pitch')))\n"
        )
        try:
            result = subprocess.run([sys.executable, '-W', 'ignore', '-c', script], capture_output=True, text=True, timeout=180)
        except subprocess.TimeoutExpired:
            self.fail('the bench did not finish')
        if result.returncode and 'vswhere' in result.stderr:
            self.skipTest('Visual Studio C++ tools are not installed')
        self.assertEqual(result.returncode, 0, result.stderr)
        first, second = result.stdout.strip().splitlines()[-2:]
        aoa, nz, weight, reversal, late_swing = (float(v) for v in first.split())
        air_roll, air_pitch, ground_roll, ground_pitch, ground_stick_roll, after_roll, after_pitch = (float(v) for v in second.split())
        self.assertAlmostEqual(aoa, 4.9, delta=0.7)  # TO 1F-117A-1 Figure A6-1.
        self.assertAlmostEqual(nz, 1.0, delta=0.05)
        # The EFM must report the loaded fuel, or the aircraft flies at its empty weight.
        self.assertAlmostEqual(weight, 32000.0, delta=10.0)
        # Releasing a full-stick roll must stop it without the rate reversing and ringing.
        self.assertLess(reversal, 5.0)
        self.assertLess(late_swing, 2.0)
        # With a wheel on the ground, bumps must not reach the elevons. What's left in roll is the airflow's own damping.
        self.assertLess(ground_roll, 0.5 * air_roll)
        self.assertLess(ground_pitch, 0.1 * air_pitch)
        # The stick must still move the elevons on the ground, and the flight controls must come back after liftoff.
        self.assertGreater(ground_stick_roll, air_roll)
        self.assertGreater(after_roll, 0.8 * air_roll)
        self.assertGreater(after_pitch, 0.5 * air_pitch)

    @staticmethod
    def _efm_root():
        if os.environ.get('F117_EFM_ROOT'):
            return Path(os.environ['F117_EFM_ROOT'])
        ini = ROOT / 'bin/efm.proxy.ini'
        if ini.exists():
            for line in ini.read_text(encoding='utf-8').splitlines():
                if line.startswith('target='):
                    return Path(line[len('target='):]).parents[2]
        return None

    def _efm_source(self, relative):
        root = self._efm_root()
        path = root / 'EFM Source Code' / relative if root else None
        return path.read_text(encoding='utf-8-sig') if path and path.exists() else None

    def _efm_dll(self):
        root = self._efm_root()
        path = root / 'EFM Source Code/bin/F_117_NightHawk.dll' if root else None
        return path if path and path.exists() else None


if __name__ == '__main__':
    unittest.main()
