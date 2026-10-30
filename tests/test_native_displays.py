"""Integration contracts for native stroke resources and source/target/holder routing."""
import sys
import hashlib,json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from check_display_calibration import runtime
from layout_editor import Model,PAGES,DEFAULTS,convert
SCRIPTS=ROOT/'Cockpit/Scripts'

class NativeDisplayTests(unittest.TestCase):
    def test_lua_compositor_bootstrap_and_fallback(self):
        for available in [False,True]:
            lua,load=runtime()
            lua.execute('''
                _handles={};_calls=0
                function get_param_handle(name)
                    if not _handles[name] then
                        _handles[name]={value=0,set=function(self,v) self.value=v end}
                    end
                    return _handles[name]
                end
                LockOn_Options.cockpit={render_target_resolution=2048}
            ''')
            if available:
                lua.execute('''
                    package={loadlib=function(path,entry)
                        _module_path=path;_module_entry=entry
                        return function() return {start=function(resolution)
                            _calls=_calls+1;_resolution=resolution
                            if _calls<2 then return false,"waiting for source pages" end
                            get_param_handle("F117_LCD_READY"):set(1)
                            return true,"active"
                        end} end
                    end}
                ''')
            else:
                lua.execute('package={loadlib=function()return nil,"missing DLL" end}')
            module=load(SCRIPTS/'Systems/DisplayCompositor.lua').new()
            module.initialize();module.update();module.update()
            g=lua.globals()
            self.assertEqual(g._handles.F117_LCD_READY.value,int(available))
            self.assertEqual(g._calls,2 if available else 0)
            if available:
                self.assertEqual(g._resolution,2048)
                self.assertEqual(g._module_entry,'luaopen_f117_displays')
                self.assertTrue(g._module_path.endswith('/../../bin/F117Displays.dll'))

    def test_operational_pages_have_a_visible_draw_purpose(self):
        # A plain ccIndicator with BAKE-only purpose needs a separate native baker;
        # merely assigning render_target does not supply that compositor.
        lua,load=runtime(False);load(SCRIPTS/'device_init.lua')
        registered=convert(lua.globals().indicators)
        self.assertEqual(len(registered),8)
        self.assertEqual(sum('/LCD/' in indicator[1] for indicator in registered),3)
        for source in ['Left/Left_init.lua','Right/Right_init.lua','MFD_indication_init.lua']:
            lua,load=runtime();load(SCRIPTS/'MFD/Indicator'/source)
            g=lua.globals()
            self.assertEqual(g.indicator_type,0)
            self.assertEqual(convert(g.purposes),[0,1])
            self.assertIsNone(g.render_target)
            self.assertIsNone(g.geometry) # calibrated connector geometry is retained
            self.assertTrue(g.shaderLineParamsUpdatable)
        for kind in ['left','right','centre']:
            lua,load=runtime();load(SCRIPTS/f'MFD/Indicator/LCD/{kind}_page.lua')
            elements=convert(lua.globals()._elements)
            for element in elements:
                self.assertIn('F117_LCD_READY',element['element_params'])
                self.assertTrue(element['z_enabled'])
            picture=next(e for e in elements if e['_etype']=='ceTexPoly')
            self.assertEqual(picture['material']['path'],f'F117_LCD_{kind.upper()}')

    def test_complete_resource_registration_and_glyphs(self):
        lua,load=runtime(False);load(SCRIPTS/'device_init.lua')
        self.assertEqual(len(lua.globals().indicators),8)
        resources=convert(lua.globals().symbologyPaths)
        self.assertEqual(resources,[(SCRIPTS/'Resources/Stroke').as_posix()])
        font=convert(load(SCRIPTS/'display_font.lua'))
        self.assertEqual(font['class'],'ceSLineFont')
        svg=ET.parse(SCRIPTS/f'Resources/Stroke/{font["symb_storage"]}.svg')
        ids={e.get('id') for e in svg.iter()}
        chars={code:name for code,name in font['chars']}
        self.assertEqual(set(chars),set(range(33,127)))
        self.assertTrue(set(chars.values()).issubset(ids))
        for mode in PAGES:
            model=Model(mode,PAGES[mode].read_text())
            for e,state in model.scene(DEFAULTS):
                if e['_etype']=='ceStringPoly':
                    self.assertEqual(e['material']['description']['class'],'ceSLineFont')
                    self.assertTrue(set(state[5]).issubset(set(chr(n) for n in chars)|{' '}))
                if e['_etype']=='ceSMultiLine':
                    self.assertEqual(len(e['indices'])%2,0)
                    self.assertLess(max(e['indices']),len(e['vertices']))
            self.assertFalse(any(e['_etype']=='ceSimpleLineObject' for e in model.elements))

    def test_irads_video_and_overlay_remain_separate(self):
        lua,load=runtime();load(SCRIPTS/'MFD/Indicator/DLIR_Camera_init.lua')
        self.assertEqual(lua.globals().render_target,0)
        self.assertEqual(convert(lua.globals().purposes),[0,1])
        lua,load=runtime();load(SCRIPTS/'MFD/Indicator/DLIR_Camera_page.lua')
        video=next(e for e in convert(lua.globals()._elements) if e['name']=='dlir_picture')
        self.assertEqual(video['material'],'render_target_1')
        model=Model('MFD',PAGES['MFD'].read_text())
        composite=next(e for e in model.elements if e['name']=='dlir_picture')
        self.assertIn('F117_LCD_READY',composite['element_params'])
        self.assertEqual(composite['material'],'render_target_1')
        self.assertTrue(any(e['_etype']=='ceSMultiLine' for e in model.elements))

    def test_calibrated_hud_optics_unchanged(self):
        baseline=json.loads((ROOT/'tools/data/hud_optics_baseline.json').read_text())
        for file,digest in baseline.items():
            self.assertEqual(digest,hashlib.sha256((SCRIPTS/'HUD/Indicator'/file).read_bytes()).hexdigest())
        lua,load=runtime();load(SCRIPTS/'HUD/Indicator/HUD_init.lua')
        self.assertEqual(lua.globals().indicator_type,1)
        self.assertFalse(lua.globals().shaderLineUseSpecularPass)

if __name__=='__main__':unittest.main()
