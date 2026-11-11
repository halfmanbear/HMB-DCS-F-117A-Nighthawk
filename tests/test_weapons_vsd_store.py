"""VSD store legend: the fired store stays listed, crossed out, until a station step or new cue."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/cockpit'))
from check_display_calibration import runtime
SCRIPTS=ROOT/'Cockpit/Scripts'

class WeaponsVsdStoreTests(unittest.TestCase):
    def setUp(self):
        self.lua,load=runtime();g=self.g=self.lua.globals()
        self.lua.execute('''
            counts={[0]=1,[1]=1}
            function GetSelf() return {listen_command=function()end,
                get_station_info=function(_,i) if counts[i] then return {count=counts[i],CLSID="GBU_27"} end end,
                get_weapon_count=function(_,i) return counts[i] or 0 end} end
            function make_default_activity()end
            log={write=function()end,INFO=0}
        ''')
        load(SCRIPTS/'Systems/Weapons.lua');g.post_initialize()

    def state(self):
        p=self.g._parameters
        return p.F117_VSD_STORE,p.F117_VSD_STORE_FIRED

    def release(self):
        self.lua.execute('counts[_parameters.F117_RELEASE_STATION]=nil;_parameters.F117_RELEASE_SEQUENCE=(_parameters.F117_RELEASE_SEQUENCE or 0)+1')
        self.g.update()

    def test_selected_store_listed_before_release(self):
        self.g.update()
        self.assertEqual(self.state(),(4,0))

    def test_fired_store_crossed_out_until_station_step(self):
        self.lua.execute('_parameters.F117_RELEASE_CUE_VALID=1');self.g.update()
        self.release()
        self.assertEqual(self.state(),(4,1))
        self.g.update()
        self.assertEqual(self.state(),(4,1))
        self.g.SetCommand(self.g.f117_commands.WEAPON_STATION_NEXT,1)
        self.assertEqual(self.state(),(4,0))

    def test_new_release_cue_clears_crossed_out_store(self):
        self.lua.execute('_parameters.F117_RELEASE_CUE_VALID=1');self.g.update()
        self.release()
        self.lua.execute('_parameters.F117_RELEASE_CUE_VALID=0');self.g.update()
        self.assertEqual(self.state(),(4,1))
        self.lua.execute('_parameters.F117_RELEASE_CUE_VALID=1');self.g.update()
        self.assertEqual(self.state(),(4,0))

    def test_last_store_fired_stays_crossed_out(self):
        self.release();self.release()
        self.assertEqual(self.state(),(4,1))

if __name__=='__main__':
    unittest.main()
