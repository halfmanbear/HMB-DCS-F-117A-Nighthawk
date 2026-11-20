"""Load the real HUD with the string defaults observed on DCS elements."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/cockpit'))
from check_display_calibration import runtime, SCRIPTS


class NativeLayoutDefaultsTests(unittest.TestCase):
    def test_hud_loads_and_registers_brightness_with_native_defaults(self):
        lua, load = runtime()
        lua.execute('''
            local create = CreateElement
            function CreateElement(kind)
                local e = create(kind)
                getmetatable(e).__index = function(_, key)
                    if key=='vertices' or key=='stringdefs' or key=='controllers'
                        or key=='width' or key=='thickness' then return '' end
                end
                return e
            end
            function MakeMaterial(_, _) return create_guid_string() end
            function MakeFont(_, _) return create_guid_string() end
            registered={}
            package={loadlib=function() return function() return {
                register=function(marker,materials) registered[marker]=materials end
            } end end}
            original_add=Add
        ''')
        load(SCRIPTS / 'HUD/Indicator/HUD_base_page.lua')
        self.assertTrue(lua.eval('Add == original_add'))
        self.assertGreater(lua.eval('#registered.OCIP_ROOT'), 0)
        self.assertTrue(lua.eval('''(function()
            for _,e in ipairs(_elements) do
                if e.name=='OCIP_ROOT' then return true end
            end
            return false
        end)()'''))


if __name__ == '__main__':
    unittest.main()
