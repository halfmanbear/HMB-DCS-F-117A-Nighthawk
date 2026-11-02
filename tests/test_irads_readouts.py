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
            function get_param_handle(name)
                return {get=function() return values[name] or 0 end,
                        set=function(self,v) values[name]=v end}
            end
            function get_base_data() return {getBarometricAltitude=function() return altitude end} end
            function require(name) return {convertMetersToLatLon=function(x,z)
                calls=calls+1;return lat,lon
            end} end
        """)
        self.module=self.lua.execute((ROOT/'Cockpit/Scripts/Systems/IRADS_Readouts.lua').read_text())
        self.g=self.lua.globals()
        self.v=self.g['values']

    def test_readout_units_and_unavailable_state(self):
        self.module.update()
        self.assertEqual(self.v.F117_IRADS_ALT_TEXT,'ALT 19620')
        self.assertEqual(self.v.F117_IRADS_RANGE_TEXT,'LR -----')
        self.assertEqual(self.v.F117_IRADS_TIME_TEXT,'TTI --:--')
        self.assertEqual(self.v.F117_IRADS_COORD_TEXT,'')
        self.v.F117_IRADS_LOCK_VALID=1
        self.v.F117_IRADS_LOCK_RANGE=1000
        self.v.F117_STORE_FLIGHT_TIME=65
        self.v.IRADS_ZOOM=3
        self.module.update()
        self.assertEqual(self.v.F117_IRADS_RANGE_TEXT,'LR 03281')
        self.assertEqual(self.v.F117_IRADS_TIME_TEXT,'TTI 01:05')
        self.assertEqual(self.v.F117_IRADS_MAG_TEXT,'NARROW')
        self.assertEqual(self.v.F117_IRADS_COORD_TEXT,"N LAT 42'53.04  E LNG 020'52.30")

    def test_rounding_hemispheres_and_relock_cache(self):
        self.v.F117_IRADS_LOCK_VALID=1
        self.g.lat=-12.9999999; self.g.lon=-179.9999999
        self.module.update()
        self.assertEqual(self.v.F117_IRADS_COORD_TEXT,"S LAT 13'00.00  W LNG 180'00.00")
        self.module.update()
        self.assertEqual(self.g.calls,1)
        self.v.F117_IRADS_LOCK_VALID=0;self.module.update()
        self.assertEqual(self.v.F117_IRADS_COORD_TEXT,'')
        self.v.F117_IRADS_LOCK_VALID=1;self.module.update()
        self.assertEqual(self.g.calls,2)

    def test_bad_coordinate_conversion_does_not_display_plausible_zeroes(self):
        self.g.lat=999
        self.v.F117_IRADS_LOCK_VALID=1
        self.module.update()
        self.assertEqual(self.v.F117_IRADS_COORD_TEXT,'GPS COORD UNAVAILABLE')
        self.v.F117_IRADS_LOCK_RANGE=float('nan')
        self.v.F117_STORE_FLIGHT_TIME=float('inf')
        self.module.update()
        self.assertEqual(self.v.F117_IRADS_RANGE_TEXT,'LR -----')
        self.assertEqual(self.v.F117_IRADS_TIME_TEXT,'TTI --:--')

if __name__=='__main__':unittest.main()
