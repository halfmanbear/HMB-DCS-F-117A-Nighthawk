"""Data entry panel: registration, main menu page and Layout Studio support."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools/cockpit'))
from check_display_calibration import runtime
from layout_editor import (DEFAULTS, GLASS_FIT_REFERENCE, Model, PAGES, REFERENCE_DIRS, REFERENCES,
                           Renderer, context_params, convert, layout_boundary, reference_fit)
from PIL import Image

SCRIPTS = ROOT/'Cockpit/Scripts'
SCREEN = 'Data Entry Panel (DEP)'


def surface():
    return json.loads((ROOT/'tools/data/cockpit_display_geometry.json').read_text())['surfaces']['DEP']


def page(params=None):
    lua, load = runtime()
    load(SCRIPTS/'DEP/Indicator/DEP_base_page.lua')
    return convert(lua.globals()._elements)


class DEPTests(unittest.TestCase):
    def test_registered_on_dep_connectors_before_charts_with_clearance(self):
        lua, load = runtime(False)
        load(SCRIPTS/'device_init.lua')
        registered = convert(lua.globals().indicators)
        index = next(i for i, row in enumerate(registered) if row[1].endswith('DEP/Indicator/DEP_init.lua'))
        self.assertGreater(index, 4)                       # the first five stay stable
        self.assertEqual(registered[-1][0], 'ccKneeboard')  # charts remain last
        connectors, mount = registered[index][3]
        self.assertEqual(connectors, ['DEP-CENTER', 'DEP-DOWN', 'DEP-RIGHT'])
        # Same check as the side displays: artwork 0.5-2 mm in front of the glass.
        glass = surface()
        r, u = glass['right_axis_world'], glass['up_axis_world']
        normal = [r[1]*u[2]-r[2]*u[1], r[2]*u[0]-r[0]*u[2], r[0]*u[1]-r[1]*u[0]]
        if normal[0] > 0: normal = [-v for v in normal]
        shift = [mount['sx_l'], -mount['sz_l'], mount['sy_l']]
        origin = [a+b for a, b in zip(glass['basis_origin_world_m'], shift)]
        clearance = [sum((o-p)*n for o, p, n in zip(origin, v, normal)) for v in glass['vertices_world_m']]
        self.assertGreater(min(clearance), .0005)
        self.assertLess(max(clearance), .002)
        lua, load = runtime()
        load(SCRIPTS/'DEP/Indicator/DEP_init.lua')
        g = lua.globals()
        self.assertEqual(convert(g.purposes), [0, 1])
        self.assertIsNone(g.render_target)

    def test_main_menu_legends_follow_fo3(self):
        elements = page()
        values = [e['value'] for e in elements if e['_etype'] == 'ceStringSLine']
        for legend in ['SPD', 'TOT', 'SNAV', 'EDIT', 'TRK', 'SEL', 'MAP', 'DP', 'RCRD',
                       'ALT', 'ILS', 'VNAV', 'HNAV', 'ATK', 'STR', 'TM', 'SRCH']:
            self.assertIn(legend, values)
        # Engaged speed mode reads CAS; engaged attack reads LVL ATK (film frames).
        for legend in ['CAS', 'LVL']:
            self.assertIn(legend, values)
        gates = {e['element_params'][0] for e in elements
                 if e['_etype'] == 'ceSimple' and e.get('controllers') and e.get('name') != 'F117_DEP_SOURCE'
                 and not e.get('name', '').startswith('F117_DEP_BOOT')}
        self.assertEqual(len(gates), 15)
        self.assertIn('F117_AT_ENGAGED', gates)
        root = next(e for e in elements if e.get('name') == 'F117_DEP_SOURCE')
        self.assertEqual(root['element_params'], ['F117_ON_DEP', 'F117_DEP_DRAW_BRIGHTNESS'])

    def test_page_registers_its_materials_for_native_brightness(self):
        lua, load = runtime()
        # DCS material and font constructors return names; register sends those names.
        lua.execute('''
            local n=0
            function MakeMaterial() n=n+1 return "material_"..n end
            function MakeFont() n=n+1 return "font_"..n end
            package={loadlib=function(path,entry)return function()return {
                register=function(marker,materials)captured_marker=marker;captured=materials;return true end}end end}''')
        load(SCRIPTS/'DEP/Indicator/DEP_base_page.lua')
        g = lua.globals()
        self.assertEqual(g.captured_marker, 'F117_DEP_SOURCE')
        used = {e['material'] for e in convert(g._elements) if e.get('material')}
        self.assertEqual(sorted(convert(g.captured)), sorted(used))
        self.assertEqual(len(used), 7)  # glass, cell, engaged, rule, boot backlight; legend and engaged fonts

    def test_artwork_stays_on_the_measured_glass(self):
        (x0, y0), (x1, y1) = surface()['bounds_local_m']
        model = Model('DEP', PAGES['DEP'].read_text(encoding='utf-8-sig'))
        for e, (x, y, angle, visible, opacity, text, vertices) in model.scene(DEFAULTS, show_all=True):
            if e['_etype'] == 'ceSimple': continue
            self.assertTrue(e['z_enabled'])
            for v in vertices:
                self.assertTrue(x0-1e-6 <= x+v[0] <= x1+1e-6 and y0-1e-6 <= y+v[1] <= y1+1e-6, e.get('name'))

    def test_layout_studio_screen_reference_folder_and_glass_fit(self):
        self.assertEqual(context_params('DEP', SCREEN), {'F117_LEFT_EO': 0, 'F117_DEP_VNAV': 1, 'F117_DEP_SRCH': 1})
        self.assertEqual(context_params('Left EO', 'Left CMDI (MFD)'), {'F117_LEFT_EO': 1})
        self.assertIsNotNone(layout_boundary('DEP', 1, SCREEN))
        # docs/reference is local-only (gitignored); check the frames when present.
        folder = REFERENCES/REFERENCE_DIRS['DEP']
        if folder.is_dir():
            self.assertEqual(len(sorted(folder.glob('*.png'))), 4)
        self.assertIn(SCREEN, GLASS_FIT_REFERENCE)
        self.assertIsNone(reference_fit('Left CMDI (MFD)'))
        (x0, y0), (x1, y1) = surface()['bounds_local_m']
        self.assertEqual(reference_fit(SCREEN), (x0, y0, x1, y1))
        # A solid reference fitted to the glass covers it and nothing outside it.
        model = Model('DEP', PAGES['DEP'].read_text(encoding='utf-8-sig'))
        red = Image.new('RGBA', (60, 10), (255, 0, 0, 255))
        size, extent = 400, .1
        image, _, _ = Renderer().render(model, dict(DEFAULTS), size, extent, (0, 0), grid=False,
                                        reference=(red, 1, reference_fit(SCREEN)))
        px = lambda x, y: image.getpixel((round(size/2+x*size/(2*extent)), round(size/2-y*size/(2*extent))))
        self.assertEqual(px(0, 0)[:3], (255, 0, 0))
        self.assertEqual(px(x1*.95, y1*.8)[:3], (255, 0, 0))
        self.assertNotEqual(px(0, y1+.01)[:3], (255, 0, 0))


if __name__ == '__main__':
    unittest.main()
