"""OCIP angular geometry, validity and sensor-unit behaviour."""
import math
import sys
import unittest
from pathlib import Path
from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from layout_editor import Model,PAGES,DEFAULTS,move_source


class OcipHudTests(unittest.TestCase):
    def test_designer_drag_converts_source_units_to_mrad(self):
        model=Model('HUD',PAGES['HUD'].read_text())
        target=next(e for e in model.elements if e['name']=='OCIP_CAS')
        edited=move_source(model.source,target,.025,-.01)
        updated=Model('HUD',edited)
        moved=next(e for e in updated.elements if e['name']=='OCIP_CAS')
        self.assertAlmostEqual(moved['init_pos'][0]-target['init_pos'][0],.025,places=7)
        self.assertAlmostEqual(moved['init_pos'][1]-target['init_pos'][1],-.01,places=7)
        altitude=next(e for e in model.elements if e['name']=='OCIP_ALT')
        unchanged=next(e for e in updated.elements if e['name']=='OCIP_ALT')
        self.assertEqual(altitude['init_pos'],unchanged['init_pos'])

    def test_angular_ladder_scale_and_reference_modes(self):
        model=Model('HUD',PAGES['HUD'].read_text())
        unit=model.lua.globals().OCIP_U
        def state(name,**params):
            return next(s for e,s in model.scene(dict(DEFAULTS,**params)) if e['name']==name)
        zero=state('OCIP_PITCH_P0',PITCH_HUD=0,ROLL_HUD=0)
        up=state('OCIP_PITCH_P0',PITCH_HUD=math.radians(5),ROLL_HUD=0)
        self.assertAlmostEqual(up[1]-zero[1],-math.tan(math.radians(5))*1000*unit)
        self.assertAlmostEqual(state('OCIP_DATUM')[1],0)
        self.assertTrue(state('OCIP_VV')[3])
        self.assertFalse(state('OCIP_PITCH_REFERENCE')[3])
        self.assertFalse(state('OCIP_VV',F117_OCIP_INS_VALID=0)[3])
        self.assertTrue(state('OCIP_PITCH_REFERENCE',F117_OCIP_INS_VALID=0)[3])
        # Manual: one degree high AOA puts the bracket's top arm at the VV.
        for aoa,arm in [(13,1),(11,-1)]:
            bracket=state('OCIP_AOA_OPTIMUM',F117_OCIP_AOA=math.radians(aoa),F117_OCIP_APPROACH=1)
            vv=state('OCIP_VV')
            self.assertAlmostEqual(bracket[1]+arm*math.radians(1)*1000*unit,vv[1])
        for cue in ['OCIP_DESTINATION','OCIP_OFFSET','OCIP_IRADS_CURSOR']:
            self.assertFalse(state(cue)[3])
        self.assertFalse(any(s[3] for e,s in model.scene(dict(DEFAULTS,mainpower=0)) if e.get('collimated')))

    def test_all_native_text_formats_accept_zero_before_device_update(self):
        model=Model('HUD',PAGES['HUD'].read_text())
        count=0
        for e in model.elements:
            for controller in e.get('controllers',[]) or []:
                if controller[0]!='text_using_parameter':continue
                fmt=e['formats'][int(controller[2]) if len(controller)>2 else 0]
                self.assertNotIn('%s',fmt)
                self.assertIsInstance(fmt % 0,str)
                count+=1
        self.assertGreater(count,5)
        texts={s[5] for e,s in model.scene(dict(DEFAULTS,F117_OCIP_MACH=0)) if s[3]}
        self.assertIn('0.00',texts)

    def test_sensor_units_rounding_and_approach_hysteresis(self):
        lua=LuaRuntime()
        lua.execute('''
            values={ias=314/1.94384449,alt=22204/3.2808399,vv=-500/196.850394,
                    heading=math.rad(300),mach=.71,aoa=math.rad(12),slip=math.rad(2),
                    pitch=0,roll=0,north=100,up=0,east=0,yaw=0}
            output={}
            function get_param_handle(name)
                return {set=function(_,v) output[name]=v end}
            end
            sensor={getIndicatedAirSpeed=function() return values.ias end,
              getBarometricAltitude=function() return values.alt end,
              getVerticalVelocity=function() return values.vv end,
              getMagneticHeading=function() return values.heading end,
              getMachNumber=function() return values.mach end,
              getAngleOfAttack=function() return values.aoa end,
              getAngleOfSlide=function() return values.slip end,
              getPitch=function() return values.pitch end,
              getRoll=function() return values.roll end,
              getHeading=function() return values.yaw end,
              getSelfVelocity=function() return values.north,values.up,values.east end}
        ''')
        update=lua.execute((ROOT/'Cockpit/Scripts/HUD/Device/OCIP_data.lua').read_text())(lua.globals().sensor)
        def value(name):return lua.globals().output['F117_OCIP_'+name]
        update(.05)
        self.assertEqual(value('CAS'),314)
        self.assertEqual(value('ALT'),22200)
        self.assertEqual(value('VVI'),-500)
        self.assertAlmostEqual(value('MACH'),.71)
        self.assertAlmostEqual(value('VV_Y'),0)
        self.assertAlmostEqual(value('VV_X'),0)
        self.assertAlmostEqual(value('HEADING'),300)
        vals=lua.globals()['values']
        for knots,expected in [(199,1),(215,1),(231,0),(215,0)]:
            vals.ias=knots/1.94384449;update(1)
            self.assertEqual(value('APPROACH'),expected)
        # A nose-up aircraft on a level ground track: FPV must meet zero bar.
        vals.pitch=math.radians(10);update(.05)
        self.assertAlmostEqual(value('VV_Y'),-math.tan(math.radians(10)))
        self.assertAlmostEqual(value('VV_Y'),value('LADDER_P0'))
        self.assertAlmostEqual(value('LADDER_P10'),0)
        # At 90 degrees bank that depression becomes lateral, not screen-down.
        vals.roll=math.pi/2;update(.05)
        self.assertAlmostEqual(value('VV_Y'),0,places=10)
        self.assertAlmostEqual(value('VV_X'),math.tan(math.radians(10)))
        # Feed the real device output into the page and compare the two cues.
        model=Model('HUD',PAGES['HUD'].read_text())
        for bank in (-60,0,45,90):
            vals.roll=math.radians(bank);update(.05)
            params=dict(DEFAULTS,PITCH_HUD=vals.pitch,ROLL_HUD=vals.roll)
            params.update(dict(lua.globals().output.items()))
            scene={e['name']:state for e,state in model.scene(params)}
            self.assertAlmostEqual(scene['OCIP_VV'][0],scene['OCIP_PITCH_P0'][0])
            self.assertAlmostEqual(scene['OCIP_VV'][1],scene['OCIP_PITCH_P0'][1])
        # A straight climb/descent aligned with the nose has a centred marker.
        vals.roll=0
        for angle in (-10,0,15):
            vals.pitch=math.radians(angle)
            vals.north=100*math.cos(vals.pitch);vals.up=100*math.sin(vals.pitch)
            update(.05)
            self.assertAlmostEqual(value('VV_Y'),0,places=10)
        vals.up=0
        # World east motion while pointing east must be straight ahead.
        vals.pitch=0;vals.roll=0;vals.yaw=-math.pi/2
        vals.north=0;vals.east=100;update(.05)
        self.assertAlmostEqual(value('VV_X'),0,places=10)
        # Ground track drifts right; marker follows velocity, independent of AoA.
        vals.yaw=0;vals.north=100;vals.east=10;vals.up=5;update(.05)
        self.assertAlmostEqual(value('VV_X'),.1)
        self.assertAlmostEqual(value('VV_Y'),.05)
        # Missing/zero/behind velocity never emits a NaN or a false valid marker.
        vals.north=0;vals.up=0;vals.east=0;update(.05)
        self.assertEqual(value('VV_VALID'),0)
        self.assertEqual(value('INS_VALID'),0)
        vals.north=-100;update(.05)
        self.assertEqual(value('VV_VALID'),0)
        vals.north=float('nan');update(.05)
        self.assertEqual(value('VV_X'),0)
        self.assertEqual(value('VV_VALID'),0)
        lua.globals().sensor.getSelfVelocity=None;update(.05)
        self.assertEqual(value('VV_VALID'),0)
        vals.pitch=math.radians(85);update(.05)
        self.assertEqual(value('LADDER_VALID_P0'),0)
        vals.alt=22244/3.2808399;vals.vv=2500/196.850394;update(1)
        self.assertEqual(value('ALT'),22200) # high rate: nearest hundred feet


if __name__=='__main__':unittest.main()
