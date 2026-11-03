"""Generic chart registration, level selection, producer protocol and fallback."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from check_display_calibration import runtime
from layout_editor import convert
S=ROOT/'Cockpit/Scripts'
class ChartBackendTests(unittest.TestCase):
    def test_theatre_chart_levels_match_common_dcs_defaults(self):
        lua,load=runtime();levels=load(S/'Systems/ChartLevels.lua')
        self.assertEqual([levels.level('Caucasus',r) for r in [10,25,50,100,140]],[2,3,6,6,6])
        self.assertEqual([levels.level('Syria',r) for r in [10,25,50,100,140]],[2,4,5,6,6])

    def test_registered_source_is_generic_dedicated_and_texture_only(self):
        lua,load=runtime();load(S/'device_init.lua');g=lua.globals()
        registered=convert(g.indicators);self.assertEqual(registered[-1][0],'ccKneeboard')
        self.assertEqual(registered[-1][3][2],6)
        self.assertEqual(g.creators[g.devices.MAP_CHARTS][1],'avKneeboard')
        lua.execute('map_calls={};function GetSelf()return {Add_Map_Page=function(_,id,path)map_calls={id,path}end}end')
        load(S/'MFD/Indicator/Map/Charts/init.lua')
        self.assertEqual(convert(g.purposes),[100])
        self.assertEqual(g.map_calls[1],3)
        self.assertTrue(g.map_calls[2].endswith('Charts/page.lua'))
        lua.execute('x_start=123;z_start=456')
        load(S/'MFD/Indicator/Map/Charts/device.lua');g.generate_maps()
        self.assertEqual(len(g.map_pages),1)
        self.assertEqual((g.map_pages[1].x,g.map_pages[1].z),(123,456))
        self.assertFalse(g.use_lat_lon)

    def test_disabled_config_does_not_register_source(self):
        lua,load=runtime()
        def disabled(path):
            if str(path).endswith('/Charts/config.lua'):return lua.table_from(dict(enabled=False,render_target=5))
            return load(path)
        lua.globals().dofile=disabled;load(S/'device_init.lua')
        self.assertEqual(len(lua.globals().indicators),9)
        self.assertIsNone(lua.globals().creators[lua.globals().devices.MAP_CHARTS])

    def test_ready_camera_drives_texture_but_failures_clear_it(self):
        lua,load=runtime();g=lua.globals()
        lua.execute('''
            calls=0;ready=false;fail=false;loads=0
            package.loadlib=function(path,entry)
                loads=loads+1;module_entry=entry
                return function()return {update=function(...)
                    calls=calls+1;view={...};if fail then error('render unavailable')end
                    return ready,'camera status'
                end}end
            end
            function get_terrain_related_data()return 'Syria'end
            _parameters.mainpower=1;_parameters.F117_MAP_VIEW_VALID=1
            _parameters.F117_MAP_VIEW_CENTER_X=123;_parameters.F117_MAP_VIEW_CENTER_Z=456
            _parameters.F117_MAP_VIEW_UP_RAD=.5;_parameters.F117_MAP_VIEW_WIDTH_M=50000
            _parameters.F117_MAP_VIEW_HEIGHT_M=40000;_parameters.F117_MAP_RANGE=25
        ''')
        backend=load(S/'Systems/ChartBackend.lua').new();backend.initialize();backend.update()
        self.assertEqual(g._parameters.F117_MAP_SOURCE_READY,0)
        self.assertEqual(convert(g.view),[123,456,.5,50000,40000,4])
        g.ready=True;backend.update();self.assertEqual(g._parameters.F117_MAP_SOURCE_READY,1)
        self.assertEqual(g.loads,1);self.assertEqual(g.module_entry,'luaopen_f117_charts')
        g.fail=True;backend.update();self.assertEqual(g._parameters.F117_MAP_SOURCE_READY,0)
        self.assertEqual(g._parameters.F117_MAP_CHART_CAMERA_READY,0)
        g.fail=False;g._parameters.F117_MAP_VIEW_VALID=0;before=g.calls;backend.update()
        self.assertEqual(g.calls,before)
        self.assertEqual(g._parameters.F117_MAP_SOURCE_READY,0)

    def test_external_source_and_missing_adapter_fall_back_cleanly(self):
        lua,load=runtime();g=lua.globals()
        lua.execute('package.loadlib=function()return nil end')
        module=load(S/'Systems/ChartBackend.lua')
        backend=module.new();backend.initialize();backend.update()
        self.assertEqual(g._parameters.F117_MAP_SOURCE_READY,0)
        external=module.new(lua.table_from(dict(enabled=True,material='ANOTHER_MAP')))
        external.initialize();g._parameters.F117_MAP_SOURCE_READY=1;external.update()
        self.assertEqual(g._parameters.F117_MAP_SOURCE_READY,1)
if __name__=='__main__':unittest.main()
