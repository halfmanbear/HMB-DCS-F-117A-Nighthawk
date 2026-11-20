"""HUD fixed readout masks follow the editor's real source transformations."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/cockpit'))
from layout_editor import Model, PAGES, DEFAULTS, sync_hud_masks, transform_selection, scale_page_source, thicken_selection


class HudLayoutMaskTests(unittest.TestCase):
    def setUp(self):
        self.source=sync_hud_masks(PAGES['HUD'].read_text())
        self.model=Model('HUD',self.source)

    def rectangle(self,model,name='OCIP_CAS'):
        # Fixed artwork enumeration also determines the generated mask order.
        fixed=[e for e in model.elements if e.get('parent_element')=='OCIP_ROOT'
               and e.get('isvisible') is not False
               and e.get('_etype') in ('ceSMultiLine','ceStringSLine','ceStringPoly')]
        index=next(i for i,e in enumerate(fixed) if e['name']==name)
        masks=[e for e in model.elements if e.get('_etype')=='ceMeshPoly'
               and e.get('parent_element')=='OCIP_ROOT' and e.get('isvisible') is False
               and e.get('h_clip_relation')==3]
        points=masks[index]['vertices']
        return min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)

    def test_move_and_undo_preserve_mask_attachment(self):
        target=self.model.by_name['OCIP_CAS']
        moved=transform_selection(self.source,[target],self.model,DEFAULTS,dx=.3,dy=-.3)
        result=Model('HUD',moved)
        before=self.rectangle(self.model);after=self.rectangle(result)
        for i in range(4):self.assertAlmostEqual(after[i]-before[i],.3 if i%2==0 else -.3,places=6)
        self.assertEqual(self.rectangle(Model('HUD',self.source)),before)

    def test_text_resize_and_stroke_width_expand_mask(self):
        target=self.model.by_name['OCIP_CAS']
        scaled=transform_selection(self.source,[target],self.model,DEFAULTS,factor=1.5)
        before=self.rectangle(self.model);after=self.rectangle(Model('HUD',scaled))
        self.assertGreater(after[2]-after[0],before[2]-before[0])
        self.assertGreater(after[3]-after[1],before[3]-before[1])
        thicker,_=thicken_selection(self.source,[target],self.model,2)
        after=self.rectangle(Model('HUD',thicker))
        self.assertLess(after[0],before[0]);self.assertGreater(after[2],before[2])

    def test_page_scale_applies_once_and_regeneration_is_stable(self):
        self.assertEqual(sync_hud_masks(self.source),self.source)
        full=Model('HUD',scale_page_source(self.source,1))
        small=Model('HUD',scale_page_source(self.source,.8))
        for a,b in zip(self.rectangle(full),self.rectangle(small)):
            self.assertAlmostEqual(a*.8,b,places=7)


if __name__=='__main__':unittest.main()
