"""OCIP angular geometry, validity and sensor-unit behaviour."""
import math
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from layout_editor import Model,PAGES,DEFAULTS,move_source

# The HUD scale line DCS logs when the F-117 spawns.
HUD_SCALE_LOG='F117_HUD_LAYOUT (Main): v1 fov_scale=0.085879072547 mrad_scale=0.000600000028498\n'


class OcipHudTests(unittest.TestCase):
    def test_designer_drag_converts_source_units_to_mrad(self):
        # The editor reads this scale from dcs.log, so use a fixed copy rather than the live log.
        with tempfile.TemporaryDirectory() as folder:
            log=Path(folder)/'dcs.log'
            log.write_text(HUD_SCALE_LOG)
            with patch('layout_editor.DCS_LOG',log):
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

    def test_collimation_is_set_at_every_hud_parent(self):
        model=Model('HUD',PAGES['HUD'].read_text())
        # Native ceSimple::get_orient copies the parent's collimated flag over
        # the child's flag. A correct leaf flag cannot repair a false root.
        for element in model.elements:
            if not element.get('collimated'):
                continue
            current=element
            while current:
                self.assertTrue(current.get('collimated'),current['name'])
                current=model.by_name.get(current.get('parent_element'))
        self.assertTrue(model.by_name['OCIP_ROOT']['collimated'])

    def test_visible_conformal_artwork_has_no_layout_translation(self):
        model=Model('HUD',PAGES['HUD'].read_text())
        unit=model.lua.globals().OCIP_U
        horizon=[e for e in model.elements if e.get('parent_element')=='OCIP_PITCH_P0']
        self.assertEqual(len(horizon),2)
        for element in horizon:
            self.assertTrue(all(abs(v[1])<1e-12 for v in element['vertices']))
        ring=next(e for e in model.elements if e.get('parent_element')=='OCIP_VV' and len(e.get('vertices',[]))==33)
        vertices=ring['vertices'][:-1]  # omit the repeated closure vertex
        self.assertAlmostEqual(sum(v[0] for v in vertices)/len(vertices),0)
        self.assertAlmostEqual(sum(v[1] for v in vertices)/len(vertices),0)
        # Check visible geometry, not just empty group origins. A level ground
        # track lies on the world horizon at any pitch/bank, including drift.
        for pitch_deg in (-15,0,12):
            pitch=math.radians(pitch_deg)
            for bank_deg in (-80,-45,0,35,80):
                bank=math.radians(bank_deg)
                right,up=.12,-math.tan(pitch)
                params=dict(DEFAULTS,PITCH_HUD=pitch,ROLL_HUD=bank,
                    F117_OCIP_VV_X=right*math.cos(bank)-up*math.sin(bank),
                    F117_OCIP_VV_Y=up*math.cos(bank)+right*math.sin(bank))
                scene={e['name']:s for e,s in model.scene(params)}
                cx,cy=scene['OCIP_VV'][:2]
                # Unroll the visible marker back into the horizon reference.
                self.assertAlmostEqual(-cx*math.sin(bank)+cy*math.cos(bank),up*1000*unit)
                for element in horizon:
                    x,y,a=scene[element['name']][:3]
                    for vx,vy in element['vertices']:
                        px=x+vx*math.cos(a)-vy*math.sin(a)
                        py=y+vx*math.sin(a)+vy*math.cos(a)
                        self.assertAlmostEqual(-px*math.sin(bank)+py*math.cos(bank),up*1000*unit)
        for element in model.elements:
            parent=element.get('parent_element','')
            if parent.startswith('OCIP_PITCH_') and 'value' in element:
                self.assertAlmostEqual(element['init_pos'][1],0)

    @staticmethod
    def motion_runtime(options=None):
        lua=LuaRuntime(unpack_returned_tuples=True)
        lua.execute('''
            values={north=200,up=0,east=0,pitch=0,roll=0,yaw=0}
            output={}
            function get_param_handle(name)
                return {set=function(_,v) output[name]=v end}
            end
            sensor={getIndicatedAirSpeed=function() return 200 end,
                getTrueAirSpeed=function() return 220 end,
                getBarometricAltitude=function() return 2000 end,
                getVerticalVelocity=function() return values.up end,
                getMagneticHeading=function() return -values.yaw end,
                getMachNumber=function() return .6 end,
                getAngleOfAttack=function() return 0 end,
                getPitch=function() return values.pitch end,
                getRoll=function() return values.roll end,
                getHeading=function() return values.yaw end,
                getSelfVelocity=function() return values.north,values.up,values.east end}
        ''')
        factory=lua.execute((ROOT/'Cockpit/Scripts/HUD/Device/OCIP_data.lua').read_text())
        update=factory(lua.globals().sensor,lua.table_from(options or {}))
        return lua,update

    def test_native_move_gains_use_metres_and_match_descent_angle(self):
        from check_display_calibration import runtime
        from layout_editor import convert
        lua,load=runtime()
        # Unlike the normalized layout preview, use the actual logged DCS
        # scales. Native move controllers bypass rescale() and add metres.
        lua.execute('''
            function GetScale()
                return _scale==MILLYRADIANS and .000600000028498 or .085879072547
            end
        ''')
        load(ROOT/'Cockpit/Scripts/HUD/Indicator/HUD_base_page.lua')
        elements={e['name']:e for e in convert(lua.globals()._elements)}
        vv=elements['OCIP_VV']
        gain_x,gain_y=vv['controllers'][0][2],vv['controllers'][1][2]
        distance=.600000028498
        self.assertAlmostEqual(gain_x,distance)
        self.assertAlmostEqual(gain_y,distance)
        self.assertAlmostEqual(elements['OCIP_PITCH_N5']['controllers'][0][2],distance)
        motion,update=self.motion_runtime({'vv_filter_time':0})
        vals=motion.globals()['values']
        vals.north=494/1.94384449
        vals.up=-4710/196.850394
        gamma=math.atan2(vals.up,vals.north)
        for pitch_deg in (-5,0,4):
            vals.pitch=math.radians(pitch_deg)
            update(.01)
            slope=motion.globals().output['F117_OCIP_VV_Y']
            self.assertAlmostEqual(math.atan(gain_y*slope/distance),gamma-vals.pitch)
        # Regression: the previous 1000*U gain was about 6.986, not .6.
        self.assertLess(gain_y,1)

    def test_velocity_average_is_time_based_and_does_not_lag_attitude(self):
        results=[]
        for dt in (.001,.01,.1):
            lua,update=self.motion_runtime()
            vals=lua.globals()['values']
            out=lua.globals().output
            update(dt)  # first sample initializes at the actual velocity
            vals.up=20
            for _ in range(round(.5/dt)):update(dt)
            expected=20*(1-math.exp(-.5/.25))
            self.assertAlmostEqual(out['F117_OCIP_VV_Y'],expected/200,places=10)
            results.append(out['F117_OCIP_VV_Y'])
            # A pitch change reprojects the same averaged world velocity
            # immediately; do not average the old screen-space position.
            vals.pitch=math.radians(10)
            update(0)
            forward=200*math.cos(vals.pitch)+expected*math.sin(vals.pitch)
            up=expected*math.cos(vals.pitch)-200*math.sin(vals.pitch)
            self.assertAlmostEqual(out['F117_OCIP_VV_Y'],up/forward)
            vals.roll=math.pi/2
            update(0)
            self.assertAlmostEqual(out['F117_OCIP_VV_X'],-up/forward)
            self.assertAlmostEqual(out['F117_OCIP_VV_Y'],0,places=10)
        self.assertAlmostEqual(max(results),min(results),places=10)

    def test_velocity_average_rejects_noise_and_resets_after_data_loss(self):
        lua,update=self.motion_runtime()
        vals=lua.globals()['values']
        out=lua.globals().output
        update(.01)
        observed=[]
        for i in range(200):
            vals.up=2 if i%2 else -2
            update(.01)
            observed.append(abs(out['F117_OCIP_VV_Y']))
        self.assertLess(max(observed),.0005)  # raw jitter would be .01
        vals.north=float('nan');update(.01)
        self.assertEqual(out['F117_OCIP_VV_VALID'],0)
        self.assertEqual(out['F117_OCIP_VV_Y'],0)
        vals.north=200;vals.up=20;update(.01)
        self.assertAlmostEqual(out['F117_OCIP_VV_Y'],.1)
        vals.up=0;update(2)  # long update gap initializes from fresh data
        self.assertEqual(out['F117_OCIP_VV_Y'],0)

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
              getTrueAirSpeed=function() return values.ias*1.1 end,
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
        update=lua.execute((ROOT/'Cockpit/Scripts/HUD/Device/OCIP_data.lua').read_text())(lua.globals().sensor,lua.table_from({'vv_filter_time':0}))
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
