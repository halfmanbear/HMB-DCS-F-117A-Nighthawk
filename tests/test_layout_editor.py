"""Behavior checks for offline layout transforms, visibility and source editing."""
import math
import sys
import unittest
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from layout_editor import DEFAULTS, Model, PAGES, Renderer, move_source, measured_boundary, measured_surfaces, hud_working_area


class LayoutEditorTests(unittest.TestCase):
    def load(self, mode):
        return Model(mode, PAGES[mode].read_text(encoding='utf-8-sig'))

    def test_real_pages_execute_without_unknown_controllers(self):
        for mode in PAGES:
            model=self.load(mode)
            scene=model.scene(DEFAULTS)
            self.assertGreater(len(scene), 10)
            self.assertEqual(model.warnings, set())

    def test_side_pages_are_separate_editable_layouts(self):
        for mode,label in [('Left MFD','MEA'),('Right MFD','ENTR')]:
            model=self.load(mode)
            target=next(e for e in model.elements if e.get('value')==label)
            changed=move_source(model.source,target,.01,0)
            moved=next(e for e in Model(mode,changed).elements if e.get('value')==label)
            self.assertAlmostEqual(moved['init_pos'][0],target['init_pos'][0]+.01)
            image,hits,missing=Renderer().render(model,DEFAULTS,size=300,extent=.09)
            self.assertGreaterEqual(len(hits),11)
            self.assertFalse(missing)

    def test_left_vsd_colour_and_flight_data_preview(self):
        model=self.load('Left MFD')
        colours=[e.get('material',{}).get('color') for e in model.elements if isinstance(e.get('material'),dict)]
        self.assertIn([3,16,178,255],colours)
        self.assertIn([163,140,80,255],colours)
        texts={s[5] for e,s in model.scene(dict(DEFAULTS,CURR_IAS=287,ALTITUDE_HUD=18420,HEADING_HUD=42)) if s[3]}
        self.assertIn('287',texts)
        self.assertIn('18420',texts)
        self.assertIn('042',texts)
        self.assertFalse(any(s[3] for _,s in model.scene(dict(DEFAULTS,mainpower=0))))
        model.scene(dict(DEFAULTS,ROLL_HUD=.3,PITCH_HUD=.1))
        self.assertEqual(model.warnings,set())

    def test_right_hsd_heading_card_and_unavailable_navigation(self):
        model=self.load('Right MFD')
        for heading,top in [(0,'N'),(90,'E'),(180,'S'),(270,'W')]:
            scene=model.scene(dict(DEFAULTS,HEADING_HUD=heading,GS_HUD=321))
            state=next(s for e,s in scene if e.get('value')==top)
            self.assertAlmostEqual(state[0],0,places=8)
            self.assertAlmostEqual(state[1],-.001+.033-.0052,places=8)
            self.assertAlmostEqual(state[2],0,places=8)
            self.assertIn('GS  321',{s[5] for e,s in scene if s[3]})
        texts={e.get('value') for e in model.elements}
        self.assertIn('DME ---.-',texts)
        self.assertNotIn('ALERT',texts)
        self.assertFalse(any(s[3] for _,s in model.scene(dict(DEFAULTS,mainpower=0))))
        self.assertEqual(model.warnings,set())

    def test_tracking_switches_exclusive_labels(self):
        model=self.load('MFD')
        def visible(value):
            return {s[5] for e,s in model.scene(dict(DEFAULTS,F117_IRADS_LOCK_VALID=value)) if s[3]}
        self.assertIn('SRCH',visible(0))
        self.assertNotIn('POINT',visible(0))
        self.assertIn('POINT',visible(1))
        self.assertNotIn('SRCH',visible(1))

    def test_hud_has_physical_glass_masks_separate_from_collimated_symbols(self):
        model=self.load('HUD')
        masks=[e for e in model.elements if e.get('h_clip_relation')==2 and not e.get('collimated')]
        self.assertEqual(len(masks),2)
        for mask in masks:
            self.assertEqual(mask['level'],2)
            self.assertFalse(mask.get('parent_element'))
            self.assertEqual(len(mask['init_pos']),3)
            self.assertLess(mask['init_rot'][2],-30)
        self.assertTrue(any(e.get('collimated') and e.get('h_clip_relation')==1 for e in model.elements))

    def test_hud_working_area_uses_engine_scale_and_accepted_angular_profile(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'dcs.log'
            self.assertIsNone(hud_working_area(path)['boundary'])
            path.write_text('unrelated log line\n')
            self.assertIsNone(hud_working_area(path)['boundary'])
            # Deliberately synthetic engine values: conversion uses their ratio,
            # not a hardcoded guess based on the old pitch gain or glass metres.
            path.write_text('INFO F117_HUD_LAYOUT (Main): v1 fov_scale=0.1 mrad_scale=0.0006\n')
            area=hud_working_area(path)
            self.assertAlmostEqual(area['units_per_mrad'],.006)
            self.assertAlmostEqual(area['center'][1],-.3)
            self.assertAlmostEqual(area['half_width'],math.radians(10)*1000*.006)
            self.assertAlmostEqual(area['half_height'],math.radians(7.5)*1000*.006)
            lo,hi=area['boundary'][0],area['boundary'][2]
            self.assertAlmostEqual((hi[0]-lo[0])/(hi[1]-lo[1]),4/3)
            path.write_text(path.read_text()+'INFO F117_HUD_LAYOUT: v1 fov_scale=0 mrad_scale=0.001\n')
            self.assertIsNone(hud_working_area(path)['boundary'])

    def test_measured_boundaries_use_separate_screen_geometry(self):
        surfaces=measured_surfaces()
        self.assertGreater(surfaces['MFD']['width_m'],surfaces['Left MFD']['width_m']*1.6)
        for mode in ('MFD','Left MFD','Right MFD'):
            one=measured_boundary(mode)
            two=measured_boundary(mode,2)
            self.assertGreaterEqual(len(one),4)
            self.assertAlmostEqual(two[0][0],one[0][0]*2)
        self.assertIsNone(measured_boundary('HUD'))
        self.assertIn('HUD glass 1',surfaces)
        self.assertIn('HUD glass 2',surfaces)

    def test_parent_power_hides_children(self):
        model=self.load('MFD')
        self.assertFalse(any(s[3] for _,s in model.scene(dict(DEFAULTS,mainpower=0))))

    def test_drag_updates_actual_text_source(self):
        model=self.load('MFD')
        target=next(e for e in model.elements if e.get('value')=='W-HOT')
        changed=move_source(model.source,target,.01,-.02)
        updated=Model('MFD',changed)
        moved=next(e for e in updated.elements if e.get('value')=='W-HOT')
        self.assertAlmostEqual(moved['init_pos'][0],target['init_pos'][0]+.01)
        self.assertAlmostEqual(moved['init_pos'][1],target['init_pos'][1]-.02)
        unchanged=next(e for e in updated.elements if e.get('value')=='SRCH')
        self.assertEqual(unchanged['init_pos'],[-.070,-.060])

    def test_expression_drag_moves_loop_as_a_group(self):
        source='for i=1,3 do\n add_text_hud("X", i*.1, -.2, nil)\nend'
        changed=move_source(source,{'_source_line':2},.03,.04)
        self.assertIn('(i*.1) + (0.03)',changed)
        self.assertIn('-0.16',changed)

    def test_parent_rotation_moves_child_position(self):
        model=self.load('HUD')
        model.elements=[{'name':'parent','_etype':'ceSimple','init_rot':[90]},
                        {'name':'child','_etype':'ceSimple','parent_element':'parent','init_pos':[1,0]}]
        model.by_name={e['name']:e for e in model.elements}
        state=model.scene(DEFAULTS)[1][1]
        self.assertAlmostEqual(state[0],0,places=6)
        self.assertAlmostEqual(state[1],1)
        self.assertAlmostEqual(state[2],math.pi/2)

    def test_render_and_dynamic_text(self):
        model=self.load('MFD')
        params=dict(DEFAULTS,F117_IRADS_LOCK_VALID=1,F117_IRADS_LOCK_RANGE=1234)
        image,hits,missing=Renderer().render(model,params,size=300,extent=.09)
        self.assertEqual(image.size,(300,300))
        self.assertFalse(missing)
        self.assertTrue(any(h.state[5]=='RNG 1234 M' for h in hits))


if __name__=='__main__':unittest.main()
