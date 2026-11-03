"""Behavior checks for offline layout transforms, visibility and source editing."""
import math
import sys
import unittest
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from layout_editor import DEFAULTS, Model, PAGES, Renderer, move_source, transform_selection, recolor_selection, Editor, measured_boundary, measured_surfaces, hud_working_area, MODE_PARAMS, PREVIEW_ONLY, SURFACES, SCREENS, SCREEN_SURFACE, DEFAULT_SCREEN, context_params, page_scale, layout_boundary


class LayoutEditorTests(unittest.TestCase):
    def load(self, mode):
        return Model(mode, PAGES[mode].read_text(encoding='utf-8-sig'))

    def test_real_pages_execute_without_unknown_controllers(self):
        for mode in PAGES:
            model=self.load(mode)
            scene=model.scene(DEFAULTS)
            self.assertGreater(len(scene), 10)
            self.assertEqual(model.warnings, set())

    def test_screen_dropdown_offers_four_screens_with_shared_pages(self):
        self.assertEqual(list(SCREENS),['HUD','Left CMDI (MFD)','Central Sensor Display','Right CMDI (MFD)'])
        self.assertEqual(set(SCREENS['Left CMDI (MFD)']),{'VSD','EO (IRADS)','MAP','HSD'})
        self.assertEqual(set(SCREENS['Right CMDI (MFD)']),{'VSD','MAP','HSD'})
        self.assertEqual(list(SCREENS['Central Sensor Display']),['IRADS'])
        # IRADS targeting is only on the left CMDI (EO) and the centre sensor display.
        irads=[(s,p) for s,pages in SCREENS.items() for p,m in pages.items() if m in ('MFD','Left EO')]
        self.assertEqual(sorted(irads),[('Central Sensor Display','IRADS'),('Left CMDI (MFD)','EO (IRADS)')])
        for screen,pages in SCREENS.items():
            for mode in pages.values():self.assertIn(mode,PAGES)
        for mode,screen in DEFAULT_SCREEN.items():self.assertIn(mode,SCREENS[screen].values())

    def test_cmdi_format_ids_and_map_guide_scale(self):
        self.assertEqual(context_params('Central Map','Right CMDI (MFD)'),{'F117_LEFT_EO':0,'F117_RIGHT_FORMAT':2})
        self.assertEqual(context_params('Right MFD','Right CMDI (MFD)')['F117_RIGHT_FORMAT'],3)
        self.assertEqual(context_params('Left EO','Left CMDI (MFD)'),{'F117_LEFT_EO':1})
        self.assertEqual(context_params('Left MFD','Left CMDI (MFD)'),{'F117_LEFT_EO':0})
        for screen in ('Left CMDI (MFD)','Right CMDI (MFD)'):
            scale=page_scale('Central Map',screen)
            self.assertTrue(0.3<scale<1,scale)
            xs,ys=zip(*layout_boundary('Central Map',1,screen))
            side=measured_surfaces()[SCREEN_SURFACE[screen]]
            sx,sy=zip(*side['boundary_local_m'])
            self.assertAlmostEqual(max(xs)-min(xs),(max(sx)-min(sx))/scale)
        # Pages that are not rescaled keep the screen's own outline.
        self.assertEqual(layout_boundary('Left MFD',1,'Right CMDI (MFD)'),measured_boundary('Right MFD'))
        self.assertEqual(page_scale('Right MFD','Left CMDI (MFD)'),1)

    def test_editor_screen_and_page_selectors(self):
        import tkinter as tk
        try:root=tk.Tk()
        except tk.TclError:self.skipTest('no display')
        root.withdraw()
        try:
            editor=Editor(root)
            editor.screen.set('Right CMDI (MFD)');editor.choose_screen()
            self.assertEqual(editor.page.get(),'VSD');self.assertEqual(editor.current,'Left MFD')
            editor.page.set('MAP');editor.choose_page()
            self.assertEqual(editor.current,'Central Map');self.assertEqual(editor.params['F117_RIGHT_FORMAT'],2)
            editor.screen.set('Left CMDI (MFD)');editor.choose_screen()
            self.assertEqual((editor.page.get(),editor.current),('MAP','Central Map'))
            editor.page.set('EO (IRADS)');editor.choose_page()
            self.assertEqual(editor.params['F117_LEFT_EO'],1)
            editor.screen.set('Right CMDI (MFD)');editor.choose_screen()  # EO is left-only
            self.assertEqual(editor.page.get(),'VSD');self.assertEqual(editor.params['F117_LEFT_EO'],0)
            editor.screen.set('Central Sensor Display');editor.choose_screen()
            self.assertEqual((editor.page.get(),editor.current),('IRADS','MFD'))
            editor.mode.set('Right MFD');editor.switch()  # undo-style direct switch re-syncs pickers
            self.assertEqual((editor.screen.get(),editor.page.get()),('Right CMDI (MFD)','HSD'))
        finally:root.destroy()

    def test_left_eo_composition_matches_live_cmdi_format(self):
        model=self.load('Left EO')
        params=dict(DEFAULTS,**MODE_PARAMS['Left EO'])
        self.assertEqual(params['F117_LEFT_EO'],1)
        names={e.get('name') for e,s in model.scene(params) if s[3]}
        self.assertIn('F117_LEFT_EO_SYMBOLOGY',names)
        self.assertTrue(any(n.startswith('F117_LEFT_EO_VIDEO_') for n in names))
        self.assertEqual(model.warnings,set())
        # The VSD gate hides the EO composition, as the live CMDI format selector does.
        hidden=[s[3] for e,s in model.scene(dict(params,F117_LEFT_EO=0)) if e.get('name')=='F117_LEFT_EO_SYMBOLOGY']
        self.assertEqual(hidden,[False])
        self.assertIsNotNone(measured_boundary('Left EO'))
        self.assertEqual(SURFACES['Left EO'],'Left MFD')

    def test_left_eo_cli_render_writes_png(self):
        import subprocess
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'eo.png'
            result=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve().parents[1]/'tools/layout_editor.py'),
                '--render','Left EO','--output',str(out)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertGreater(out.stat().st_size,1000)

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
        colours=[(e.get('material') if isinstance(e.get('material'),dict) else {}).get('color') for e in model.elements if isinstance(e.get('material'),dict)]
        self.assertIn([3,16,178,255],colours)
        self.assertIn([163,140,80,255],colours)
        texts={s[5] for e,s in model.scene(dict(DEFAULTS,F117_LEFT_EO=0,CURR_IAS=287,ALTITUDE_HUD=18420,HEADING_HUD=42)) if s[3]}
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
        self.assertEqual(unchanged['init_pos'],[-.073,-.049])

    def test_multi_move_and_scale_real_text_and_geometry(self):
        model=self.load('MFD')
        labels=[next(e for e in model.elements if e.get('value')==name) for name in ['W-HOT','SRCH']]
        changed=transform_selection(model.source,labels,model,DEFAULTS,dx=.01,dy=.02)
        moved=Model('MFD',changed)
        for before in labels:
            after=moved.by_name[before['name']]
            self.assertAlmostEqual(after['init_pos'][0],before['init_pos'][0]+.01)
            self.assertAlmostEqual(after['init_pos'][1],before['init_pos'][1]+.02)
        scaled=Model('MFD',transform_selection(model.source,labels,model,DEFAULTS,factor=1.05))
        for before in labels:
            after=scaled.by_name[before['name']]
            self.assertAlmostEqual(after['stringdefs'][0],before['stringdefs'][0]*1.05)
            self.assertAlmostEqual(after['init_pos'][0],before['init_pos'][0]*1.05)
        arm=next(e for e in model.elements if e['_etype']=='ceSMultiLine')
        enlarged=Model('MFD',transform_selection(model.source,[arm],model,DEFAULTS,dx=.01,factor=2))
        self.assertAlmostEqual(enlarged.by_name[arm['name']]['vertices'][0][0],arm['vertices'][0][0]*2+.01)
        # Repeated transforms preserve selection identities and valid Lua.
        again=Model('MFD',transform_selection(enlarged.source,[enlarged.by_name[arm['name']]],enlarged,DEFAULTS,dx=.01))
        self.assertAlmostEqual(again.by_name[arm['name']]['vertices'][0][0],arm['vertices'][0][0]*2+.02)

    def test_shared_loop_moves_once_and_parent_rotation_is_respected(self):
        model=self.load('MFD')
        ticks=[e for e in model.elements if e['_etype']=='ceSMultiLine' and len(e['vertices'])==2
               and abs(e['vertices'][0][0]+.073)<1e-8]
        self.assertEqual(len(ticks),5)
        result=Model('MFD',transform_selection(model.source,ticks,model,DEFAULTS,dx=.01))
        self.assertAlmostEqual(result.by_name[ticks[0]['name']]['vertices'][0][0],-.063)
        source='''local p=group("P",0,0)
text("X",.1,.2,2,p)
'''
        # Synthetic model exercises parent rotation independently of page drawing helpers.
        from types import SimpleNamespace
        parent={'name':'p','_etype':'ceSimple'}
        child={'name':'c','parent_element':'p','_etype':'ceStringPoly','_source_line':2}
        synthetic=SimpleNamespace(mode='HUD',by_name={'p':parent,'c':child},elements=[parent,child],
            scene=lambda _: [(parent,(0,0,math.pi/2)),(child,(-.2,.1,math.pi/2))])
        changed=transform_selection(source,[child],synthetic,{},dx=.03)
        self.assertIn('text("X",0.1,0.17',changed)

    def test_hud_scaling_uses_mrad_positions_and_scalar_font_sizes(self):
        model=self.load('HUD')
        e=model.by_name['OCIP_GS']
        result=Model('HUD',transform_selection(model.source,[e],model,DEFAULTS,factor=1.05))
        self.assertAlmostEqual(result.by_name[e['name']]['init_pos'][0],e['init_pos'][0]*1.05)
        self.assertAlmostEqual(result.by_name[e['name']]['stringdefs'][0],e['stringdefs'][0]*1.05)

    def test_parent_child_selection_transforms_once(self):
        base=PAGES['HUD'].read_text(encoding='utf-8-sig')
        source=base+'''\nlocal edit_group=group("EDIT_GROUP",20,10)
text("E",2,3,2.8,edit_group,nil,nil,nil,nil,nil,"EDIT_CHILD")
'''
        model=Model('HUD',source)
        parent,child=model.by_name['EDIT_GROUP'],model.by_name['EDIT_CHILD']
        delta=5*parent['_coordinate_scale']
        moved=Model('HUD',transform_selection(source,[parent,child],model,DEFAULTS,dx=delta))
        self.assertAlmostEqual(moved.by_name['EDIT_GROUP']['init_pos'][0],parent['init_pos'][0]+delta)
        self.assertEqual(moved.by_name['EDIT_CHILD']['init_pos'],child['init_pos'])
        scaled=Model('HUD',transform_selection(source,[parent,child],model,DEFAULTS,factor=2))
        self.assertAlmostEqual(scaled.by_name['EDIT_GROUP']['init_pos'][0],parent['init_pos'][0]*2)
        self.assertAlmostEqual(scaled.by_name['EDIT_CHILD']['init_pos'][0],child['init_pos'][0]*2)
        self.assertAlmostEqual(scaled.by_name['EDIT_CHILD']['stringdefs'][0],child['stringdefs'][0]*2)

    def test_editor_marquee_keyboard_transforms_and_undo(self):
        import tkinter as tk
        from types import SimpleNamespace
        root=tk.Tk();root.withdraw()
        try:
            editor=Editor(root);editor.mode.set('MFD');editor.switch()
            root.update_idletasks();editor.redraw()
            hits=[h for h in editor.hits if h.element.get('value') in ['W-HOT','SRCH']]
            self.assertEqual(len(hits),2)
            x0=min(h.box[0] for h in hits)-8+editor.offset[0]
            y0=min(h.box[1] for h in hits)-8+editor.offset[1]
            x1=max(h.box[2] for h in hits)+8+editor.offset[0]
            y1=max(h.box[3] for h in hits)+8+editor.offset[1]
            editor.press(SimpleNamespace(x=x0,y=y0,state=1))
            editor.motion(SimpleNamespace(x=x1,y=y1))
            editor.release(SimpleNamespace(x=x1,y=y1))
            names={h.element.get('value') for h in editor.selection}
            self.assertTrue({'W-HOT','SRCH'}<=names)
            old=editor.text()
            editor.keypress(SimpleNamespace(keysym='Right',state=0))
            self.assertNotEqual(editor.text(),old)
            self.assertEqual(len(editor.undo_stack),1)
            self.assertGreaterEqual(len(editor.selection),2)
            editor.shortcut_undo()
            self.assertEqual(editor.text(),old)
            editor.keypress(SimpleNamespace(keysym='plus',state=1))
            self.assertNotEqual(editor.text(),old)
            editor.shortcut_undo()
            self.assertEqual(editor.text(),old)
            editor.hex_color.set('#FF4000');editor.apply_color()
            self.assertNotEqual(editor.text(),old)
            self.assertTrue(any((e.get('material') if isinstance(e.get('material'),dict) else {}).get('color')==[255,64,0,255] for e in editor.models['MFD'].elements))
            editor.shortcut_undo();self.assertEqual(editor.text(),old)
        finally:root.destroy()

    def test_hex_colors_preserve_fonts_textures_and_unselected_materials(self):
        for mode in (m for m in PAGES if m not in PREVIEW_ONLY):
            model=self.load(mode)
            target=next(e for e in model.elements if e.get('_etype') in ('ceStringPoly','ceStringSLine') and e.get('isvisible') is not False)
            changed=recolor_selection(model.source,[target],model,'#123aEF')
            result=Model(mode,changed)
            matches=[e for e in result.elements if (e.get('material') if isinstance(e.get('material'),dict) else {}).get('color')==[18,58,239,255]]
            self.assertTrue(matches,mode)
            self.assertEqual(matches[0]['material']['description'],target['material']['description'])
            self.assertTrue(any((e.get('material') if isinstance(e.get('material'),dict) else {}).get('color')!=[18,58,239,255] for e in result.elements if e.get('material')),mode)
            # Color wrappers remain compatible with position editing and recoloring.
            target=matches[0]
            moved=move_source(changed,target,.01,0)
            moved_model=Model(mode,moved)
            target=next(e for e in moved_model.elements if (e.get('material') if isinstance(e.get('material'),dict) else {}).get('color')==[18,58,239,255])
            again=Model(mode,recolor_selection(moved,[target],moved_model,'00FF00'))
            self.assertTrue(any((e.get('material') if isinstance(e.get('material'),dict) else {}).get('color')==[0,255,0,255] for e in again.elements))
        model=self.load('HUD')
        colors=[e['material']['color'] for e in model.elements if e.get('material') and e.get('isvisible') is not False]
        self.assertTrue(colors)
        self.assertTrue(all(c==[0,255,0,255] for c in colors))

    def test_group_color_includes_children_and_rejects_invalid_hex(self):
        model=self.load('HUD')
        group=model.by_name['OCIP_PITCH_REFERENCE']
        changed=recolor_selection(model.source,[group],model,'#FF8000')
        result=Model('HUD',changed)
        children=[e for e in result.elements if e.get('parent_element')==group['name']]
        self.assertTrue(children)
        self.assertTrue(all(e['material']['color']==[255,128,0,255] for e in children))
        with self.assertRaises(ValueError):recolor_selection(model.source,[group],model,'#xyz')

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
        params=dict(DEFAULTS,F117_IRADS_LOCK_VALID=1,F117_IRADS_LOCK_RANGE=1234,F117_IRADS_RANGE_TEXT='LR 04049')
        image,hits,missing=Renderer().render(model,params,size=300,extent=.09)
        self.assertEqual(image.size,(300,300))
        self.assertFalse(missing)
        self.assertTrue(any(h.state[5]=='LR 04049' for h in hits))


if __name__=='__main__':unittest.main()
