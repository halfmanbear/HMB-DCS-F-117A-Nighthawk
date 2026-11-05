"""IRADS presentation telemetry: formatting, invalid inputs and lock lifecycle."""
import unittest
from pathlib import Path
from lupa import LuaRuntime

ROOT=Path(__file__).resolve().parents[1]

class IRADSReadoutTests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute("""
            values={}; calls=0; altitude=5980.176; lat=42.884; lon=20.8716666667
            mach=.8812; ias=216.07; clock=69607.4
            function get_param_handle(name)
                return {get=function() return values[name] or 0 end,
                        set=function(self,v) values[name]=v end}
            end
            function get_base_data() return {getBarometricAltitude=function() return altitude end,
                getMachNumber=function() return mach end,
                getIndicatedAirSpeed=function() return ias end} end
            function get_absolute_model_time() return clock end
            function require(name) return {convertMetersToLatLon=function(x,z)
                calls=calls+1;return lat,lon
            end} end
        """)
        self.module=self.lua.execute((ROOT/'Cockpit/Scripts/Systems/IRADS_Readouts.lua').read_text())
        self.g=self.lua.globals()
        self.v=self.g['values']

    def test_unlocked_shows_destination_range_and_ttg(self):
        self.module.update()
        self.assertEqual(self.v.F117_IRADS_ALT_TEXT,'ALT 19620')
        self.assertEqual(self.v.F117_IRADS_RANGE_TEXT,' R -----')
        self.assertEqual(self.v.F117_IRADS_TIME_TEXT,'TTG --:--')
        self.assertEqual(self.v.F117_IRADS_COORD_TEXT,'')
        self.assertEqual(self.v.F117_IRADS_LASER_TEXT,'')
        self.v.F117_NAV_VALID=1;self.v.F117_NAV_RANGE_NM=15.3;self.v.F117_NAV_TTG_TEXT='TTG 01:18'
        self.module.update()
        self.assertEqual(self.v.F117_IRADS_RANGE_TEXT,' R 015NM')
        self.assertEqual(self.v.F117_IRADS_TIME_TEXT,'TTG 01:18')

    def test_air_data_and_clock(self):
        self.module.update()
        # Numbers, not strings: the page formats them as .88 and 420.
        self.assertAlmostEqual(self.v.F117_IRADS_MACH,88.12)
        self.assertAlmostEqual(self.v.F117_IRADS_CAS,216.07*1.94384449)
        self.assertEqual(self.v.F117_IRADS_CLOCK_TEXT,'GPS 1920:07')
        # The EFM's calibrated airspeed wins when its air data is valid.
        self.v.F117_AIR_DATA_VALID=1;self.v.F117_CAS_MPS=100
        self.module.update()
        self.assertAlmostEqual(self.v.F117_IRADS_CAS,194.384449)

    def test_locked_range_source_and_laser_mode(self):
        self.v.F117_IRADS_LOCK_VALID=1;self.v.F117_IRADS_LOCK_RANGE=1000
        self.v.F117_LASER_ARMED=1
        self.module.update()
        self.assertEqual(self.v.F117_IRADS_RANGE_TEXT,'ER 03281')
        self.assertEqual(self.v.F117_IRADS_LASER_TEXT,'AX')
        self.v.F117_LASER_FIRING=1
        self.module.update()
        self.assertEqual(self.v.F117_IRADS_RANGE_TEXT,'LR 03281')
        self.assertEqual(self.v.F117_IRADS_LASER_TEXT,'AF')
        self.assertEqual(self.v.F117_IRADS_COORD_TEXT,"N LAT 42'53.04 E LNG 020'52.30")
        self.v.F117_IRADS_LOCK_VALID=0;self.v.F117_LASER_FIRING=0
        self.module.update()
        self.assertEqual(self.v.F117_IRADS_LASER_TEXT,'A')

    def test_tti_from_release_until_designation_dropped(self):
        self.v.F117_IRADS_LOCK_VALID=1;self.v.F117_RELEASE_SEQUENCE=0
        self.v.F117_RELEASE_CUE_VALID=1;self.v.F117_RELEASE_CUE_TTG=12.4
        self.module.update()
        self.assertEqual(self.v.F117_IRADS_TIME_TEXT,'TTG 00:12')
        self.v.F117_RELEASE_SEQUENCE=1;self.v.F117_STORE_FLIGHT_TIME=65
        self.module.update()
        self.assertEqual(self.v.F117_IRADS_TIME_TEXT,'TTI 01:05')
        # Impact: TTI holds at zero while the designation stays.
        self.v.F117_STORE_FLIGHT_TIME=0
        self.module.update()
        self.assertEqual(self.v.F117_IRADS_TIME_TEXT,'TTI 00:00')
        self.v.F117_IRADS_LOCK_VALID=0;self.v.F117_NAV_TTG_TEXT='TTG 01:18'
        self.module.update()
        self.assertEqual(self.v.F117_IRADS_TIME_TEXT,'TTG 01:18')
        # A new designation does not bring the old TTI back.
        self.v.F117_IRADS_LOCK_VALID=1
        self.module.update()
        self.assertEqual(self.v.F117_IRADS_TIME_TEXT,'TTG 00:12')

    def test_rounding_hemispheres_and_relock_cache(self):
        self.v.F117_IRADS_LOCK_VALID=1
        self.g.lat=-12.9999999; self.g.lon=-179.9999999
        self.module.update()
        self.assertEqual(self.v.F117_IRADS_COORD_TEXT,"S LAT 13'00.00 W LNG 180'00.00")
        self.module.update()
        self.assertEqual(self.g.calls,1)
        self.v.F117_IRADS_LOCK_VALID=0;self.module.update()
        self.assertEqual(self.v.F117_IRADS_COORD_TEXT,'')
        self.v.F117_IRADS_LOCK_VALID=1;self.module.update()
        self.assertEqual(self.g.calls,2)

    def test_bad_inputs_do_not_display_plausible_values(self):
        self.g.lat=999
        self.v.F117_IRADS_LOCK_VALID=1
        self.module.update()
        self.assertEqual(self.v.F117_IRADS_COORD_TEXT,'GPS COORD UNAVAILABLE')
        self.v.F117_IRADS_LOCK_RANGE=float('nan')
        self.v.F117_RELEASE_CUE_VALID=1;self.v.F117_RELEASE_CUE_TTG=float('inf')
        self.g.mach=float('nan')
        self.module.update()
        self.assertEqual(self.v.F117_IRADS_RANGE_TEXT,' R -----')
        self.assertEqual(self.v.F117_IRADS_TIME_TEXT,'TTG --:--')
        self.assertEqual(self.v.F117_IRADS_MACH,0)

if __name__=='__main__':unittest.main()
