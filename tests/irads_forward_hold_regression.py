"""Compile and exercise the linked EFM's production forward-hold routine."""
from pathlib import Path
import configparser
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
ini=configparser.ConfigParser();ini.read(ROOT/'bin/efm.proxy.ini')
src=Path(ini['General']['target']).parents[1]
text=(src/'Avionics/Interop/InputHandler.cpp').read_text()
def extract(signature):
    start=text.index(signature);a=text.index('{',start);depth=1;b=a+1
    while depth:
        depth+=(text[b]=='{')-(text[b]=='}');b+=1
    return text[start:b]
code=r"""
#include <cassert>
#include <cmath>
#include <cstdio>
bool s_irads_homing=false,s_irads_home_arrived=false,s_irads_lock_valid=false,s_irads_terrain_pending=false;
int stops=0,requests=0,rebases=0;
constexpr double rad_to_deg=180/3.141592653589793,slew_rate_at_min_zoom=60;
double pose[16]{},h_rate=0,v_rate=0,cache_h=.7,cache_v=-.4;
struct Motor{double current,target;};Motor hm{.7,.7},vm{-.4,-.4};
void* g_av_tv_sensor_instance=pose;
void stop(void*){++stops;h_rate=v_rate=0;}
auto g_av_tv_sensor_slew_stop=stop;
void left(void*,double v){h_rate=-v;} void right(void*,double v){h_rate=v;}
void down(void*,double v){v_rate=-v;} void up(void*,double v){v_rate=v;}
auto g_av_tv_sensor_slew_left=left;auto g_av_tv_sensor_slew_right=right;
auto g_av_tv_sensor_slew_up=up;auto g_av_tv_sensor_slew_down=down;
void* h_axis(void*){return &hm;}void* v_axis(void*){return &vm;}
auto g_platform_h_axis=h_axis;auto g_platform_v_axis=v_axis;
void force(void* m,double v){static_cast<Motor*>(m)->current=v;}
void motor_stop(void* m){static_cast<Motor*>(m)->target=static_cast<Motor*>(m)->current;}
auto g_motor_force=force;auto g_motor_stop=motor_stop;
void rebase(void*){cache_h=hm.current;cache_v=vm.current;++rebases;}
auto g_sensor_slew_rebase=rebase;
double* sensor_world_pose(){return pose;}
void clear_slew_demand(){}
void clear_irads_lock(){s_irads_lock_valid=s_irads_terrain_pending=false;}
void set_external_designation(bool){}
void log_message(const char*){}
bool ground_stabilize_irads(){++requests;return true;}
void native_frame(double dt){
 hm.current+=h_rate*dt/rad_to_deg;vm.current+=v_rate*dt/rad_to_deg;
 pose[0]=std::cos(hm.current)*std::cos(vm.current);
 pose[1]=std::sin(vm.current);pose[2]=std::sin(hm.current)*std::cos(vm.current);
}
"""
code+=extract('static void stop_slew_and_designate(')
code+=extract('static void reset_sensor(')
code+=extract('static double dot3(')
code+=extract('void service_irads_home(')
code+=r"""
int main(){
 double mount[16]={1,0,0,0,0,1,0,0,0,0,1,0,100,200,300,1};
 pose[12]=7;pose[13]=8;pose[14]=9;
 native_frame(0);double old=pose[2];
 reset_sensor();assert(s_irads_homing&&!s_irads_home_arrived);
 service_irads_home(mount);
 assert(pose[2]==old&&h_rate<0&&v_rate>0&&!s_irads_home_arrived); // no teleport
 for(int frame=0;frame<300&&!s_irads_home_arrived;++frame){native_frame(.05);service_irads_home(mount);}
 assert(s_irads_homing&&s_irads_home_arrived&&rebases>0);
 assert(hm.current==0&&hm.target==0&&vm.current==0&&vm.target==0);
 assert(cache_h==0&&cache_v==0);
 for(int frame=0;frame<100;++frame){
  double h=frame*.03;
  mount[0]=std::cos(h);mount[2]=std::sin(h);mount[8]=-std::sin(h);mount[10]=std::cos(h);
  service_irads_home(mount);
  for(int i=0;i<12;++i)assert(pose[i]==mount[i]);
  assert(s_irads_homing&&pose[12]==7&&pose[13]==8&&pose[14]==9);
 }
 // Native slew resumes from the rebased motor/cache, never the original .7/- .4 rad angles.
 s_irads_homing=false;hm.current=cache_h;vm.current=cache_v;left(nullptr,1);native_frame(.05);
 assert(std::abs(hm.current)<.001&&vm.current==0);
 s_irads_homing=true;
 stop_slew_and_designate(false);assert(s_irads_homing);
 stop_slew_and_designate(true);assert(!s_irads_homing&&requests==1);
 int before=stops;service_irads_home(mount);assert(stops==before);
 puts("PASS gradual homing, native current/target/cache reset, forward hold and first-slew continuity");
}
"""
out=ROOT/'tmp/irads-forward';out.mkdir(parents=True,exist_ok=True)
harness=out/'forward.cpp';harness.write_text(code)
vcvars=Path(r'C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Auxiliary/Build/vcvars64.bat')
command=f'call "{vcvars}" >nul && cl /nologo /EHsc /std:c++17 "{harness}" /Fo"{out / "forward.obj"}" /Fe"{out / "forward.exe"}"'
subprocess.run(command,shell=True,check=True)
subprocess.run([str(out/'forward.exe')],check=True)
for name in ('SensorFrame.cpp','CameraBridge.cpp'):
    assert 'service_irads_home(sensor_mount_pose());' in (src/'Avionics/Interop'/name).read_text()
print('PASS simulation and render paths both apply forward hold')

# Test the production projector-power bridge, including independent off states.
text=(src/'Avionics/Interop/SensorFrame.cpp').read_text()
light_code=r"""
#include <cassert>
#include <cstring>
#include <cstdio>
#include <cmath>
using FARPROC=void(*)();
struct Light{double power=0;};Light landing,taxi;
bool ready=false,have_root=true;double landing_request=0,taxi_request=0;int calls=0;
bool read_named_param(void*&,const char* n,double& v){
 v=std::strcmp(n,"F117_LIGHT_CONTROL_READY")==0?double(ready):
   std::strcmp(n,"F117_LIGHT_LANDING")==0?landing_request:taxi_request;return true;
}
void publish_named_param(void*&,const char*,double){}
void log_format(const char*,...){}
void* lights(){return have_root?reinterpret_cast<void*>(1):nullptr;}
void* child(void*,unsigned i){assert(i==1||i==5);return i==1?&landing:&taxi;}
void power(void* p,double v){static_cast<Light*>(p)->power=v;++calls;}
double current(void* p){return static_cast<Light*>(p)->power;}
FARPROC resolve_cockpit_base_export(const char* n){
 if(std::strcmp(n,"ed_cockpit_external_lights_get_reference")==0)return reinterpret_cast<FARPROC>(lights);
 if(std::strcmp(n,"ed_cockpit_external_lights_get_child")==0)return reinterpret_cast<FARPROC>(child);
 if(std::strcmp(n,"ed_cockpit_set_external_lights_power")==0)return reinterpret_cast<FARPROC>(power);
 if(std::strcmp(n,"ed_cockpit_get_external_lights_power")==0)return reinterpret_cast<FARPROC>(current);
 assert(false);return nullptr;
}
"""
light_code+=extract('static void update_gear_light_power(')
light_code+='\nconstexpr double rad_to_deg=180/3.141592653589793;\n'
light_code+=extract('static double irads_housing_target(')
light_code+=r"""
int main(){
 update_gear_light_power();assert(calls==0);
 ready=true;taxi_request=1;update_gear_light_power();assert(taxi.power==1&&landing.power==0);
 taxi_request=0;landing_request=1;update_gear_light_power();assert(taxi.power==0&&landing.power==1);
 taxi_request=0;landing_request=0;update_gear_light_power();assert(taxi.power==0&&landing.power==0);
 have_root=false;int before=calls;update_gear_light_power();assert(calls==before);
 double mount[16]={1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1};
 double los[16]={1,0,0};
 assert(std::abs(irads_housing_target(los,mount)-44.2/129.44)<1e-9);
 los[0]=std::sqrt(.5);los[1]=-std::sqrt(.5);
 assert(std::abs(irads_housing_target(los,mount)-89.2/129.44)<1e-9);
 los[0]=0;los[1]=-1;assert(irads_housing_target(los,mount)==1);
 los[1]=1;assert(irads_housing_target(los,mount)==0);
 // Same body-forward ray with aircraft heading east remains at the forward housing key.
 mount[0]=0;mount[2]=1;mount[8]=-1;mount[10]=0;
 los[0]=0;los[1]=0;los[2]=1;
 assert(std::abs(irads_housing_target(los,mount)-44.2/129.44)<1e-9);
 puts("PASS native projector power and IRADS housing body-elevation mapping/clamps");
}
"""
harness=out/'lights.cpp';harness.write_text(light_code)
command=f'call "{vcvars}" >nul && cl /nologo /EHsc /std:c++17 "{harness}" /Fo"{out / "lights.obj"}" /Fe"{out / "lights.exe"}"'
subprocess.run(command,shell=True,check=True)
subprocess.run([str(out/'lights.exe')],check=True)
body=extract('void update_irads_sensor_frame(')
assert body.index('update_gear_light_power();')<body.index('if (!is_irads_powered())')
print('PASS projector power updates with IRADS switched off')
