// Real DCS Lua 5.1 with instrumented chart objects. No renderer/game is started.
#include "F117Displays.cpp"
#include <cstdlib>
namespace {
void check(bool ok,const char* why){if(!ok){std::fprintf(stderr,"FAIL: %s\n",why);std::exit(1);}}
unsigned char chartContext[0x148]={},chartIndicator[1800]={},chartDevice[1400]={};
unsigned char mapRecord[48]={},indexRecord[8]={};
void* chartPointers[]={chartIndicator};
int indicatorIdentity=0,deviceIdentity=0,changes=0;
void* chartContextStub(){return chartContext;}
void* chartElementStub(void* object,const char* name){return object==chartIndicator && !std::strcmp(name,"F117_CHART_PRODUCER") ? object:nullptr;}
const void* chartMapStub(void*){return mapRecord;}
void chartChangeStub(void*){++changes;}
void chartRemovePurposeStub(void* indicator,int purpose){check(indicator==chartIndicator && purpose>=0 && purpose<=2,"UI purpose removed only from owned chart indicator");}
void observeCamera(){
    const auto& p=*reinterpret_cast<const ChartPage*>(mapRecord);
    *reinterpret_cast<int*>(chartIndicator+928)=9;
    *reinterpret_cast<float*>(chartIndicator+752)=static_cast<float>(p.x);
    *reinterpret_cast<float*>(chartIndicator+760)=static_cast<float>(p.z);
    *reinterpret_cast<float*>(chartIndicator+896)=static_cast<float>(-p.scale);
    *reinterpret_cast<float*>(chartIndicator+908)=static_cast<float>(p.scale);
    *reinterpret_cast<float*>(chartIndicator+900)=static_cast<float>(-p.scale*.049/.061);
    *reinterpret_cast<float*>(chartIndicator+912)=static_cast<float>(p.scale*.049/.061);
}
}
int main(int argc,char** argv){
    check(argc==3,"supply DCS lua.dll and built adapter");
    HMODULE runtime=LoadLibraryExA(argv[1],nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);
    check(runtime && bindLua(),"real Lua runtime loaded");
    lua_State* (*newState)()=nullptr;void (*closeState)(lua_State*)=nullptr;
    void (*getfield)(lua_State*,int,const char*)=nullptr;void (*pushnumber)(lua_State*,double)=nullptr;
    int (*pcall)(lua_State*,int,int,int)=nullptr;int (*toboolean)(lua_State*,int)=nullptr;
    check(symbol(runtime,"luaL_newstate",newState) && symbol(runtime,"lua_close",closeState) &&
        symbol(runtime,"lua_getfield",getfield) && symbol(runtime,"lua_pushnumber",pushnumber) &&
        symbol(runtime,"lua_pcall",pcall) && symbol(runtime,"lua_toboolean",toboolean),"host exports");
    auto* state=newState();check(luaopen_f117_charts(state)==1,"chart module created");lua.setfield(state,-10002,"charts");
    *reinterpret_cast<void**>(chartIndicator)=&indicatorIdentity;
    *reinterpret_cast<void**>(chartDevice)=&deviceIdentity;
    *reinterpret_cast<void**>(chartIndicator+56)=chartDevice;
    *reinterpret_cast<void**>(chartDevice+1040)=mapRecord;
    *reinterpret_cast<void**>(chartDevice+1048)=mapRecord+48;
    *reinterpret_cast<void**>(chartDevice+1152)=indexRecord;
    *reinterpret_cast<void**>(chartDevice+1160)=indexRecord+8;
    Vector indicators{chartPointers,chartPointers+1,chartPointers+1};
    std::memcpy(chartContext+0xb0,&indicators,sizeof(indicators));
    chartAPI={chartContextStub,chartElementStub,chartMapStub,chartChangeStub,&indicatorIdentity,&deviceIdentity,chartRemovePurposeStub};
    chartsBound=true;
    auto update=[&](double x=1000,double width=50000,double level=3,double rotation=.25){
        lua.settop(state,0);getfield(state,-10002,"charts");getfield(state,-1,"update");
        for(double value:{x,2000.,rotation,width,width*.098/.122,level})pushnumber(state,value);
        check(pcall(state,6,2,0)==0,"chart update returned normally");
        bool ready=toboolean(state,-2)!=0;lua.settop(state,0);return ready;
    };
    check(!update() && changes==1,"first update waits for observed render camera");
    const auto& page=*reinterpret_cast<const ChartPage*>(mapRecord);
    check(page.x==1000 && page.z==2000 && page.scale==25000 && page.chart==3 && page.rotation==.25,"native page receives exact view");
    check(chartIndicator[1744]==1 && chartDevice[1180]==0,"only owned producer configured");
    observeCamera();check(update(),"matching previous camera allows source image");
    for (double rate:{-3.,1.,3.}) {
        update();observeCamera();
        for (int i=1;i<=20;++i) {
            check(update(1000,50000,3,.25+i*rate*3.141592653589793/180*.05),
                "continuous track-up turn retains chart readiness");
            observeCamera();
        }
    }
    check(!update(1000,50000,3,3.14),"abrupt orientation change clears readiness");
    observeCamera();check(update(1000,50000,3,3.14),"orientation change recovers after camera update");
    check(update(1000,50000,3,-3.14),"track crossing +/-pi retains readiness");
    observeCamera();
    check(!update(1000,50000,3,0),"switch from track-up to north-up clears readiness");
    observeCamera();check(update(1000,50000,3,0),"north-up recovers after camera update");
    check(!update(5000,50000,3,0),"large pan clears readiness");
    check(!update(5000,50000,3,0),"stale camera cannot become ready");
    observeCamera();check(update(5000,50000,3,0),"pan recovers when camera catches up");
    update();observeCamera();check(update(),"restore baseline view");
    int count=changes;check(!update(std::nan("")) && changes==count,"NaN rejected without writes");
    check(!update(1000,50000,100) && changes==count,"invalid chart rejected without writes");
    check(!update(1000,100000),"zoom change clears readiness");
    observeCamera();check(update(1000,100000),"new zoom requires matching camera");
    *reinterpret_cast<void**>(chartDevice)=nullptr;count=changes;
    check(!update() && changes==count,"foreign device cannot be modified");
    *reinterpret_cast<void**>(chartDevice)=&deviceIdentity;
    *reinterpret_cast<void**>(chartDevice+1048)=mapRecord+96;
    check(!update() && changes==count,"multi-record/user kneeboard cannot be modified");
    *reinterpret_cast<int*>(chartIndicator+0x470)=5;
    lua.settop(state,0);getfield(state,-10002,"charts");getfield(state,-1,"status");
    check(pcall(state,0,2,0)==0 && toboolean(state,-2),"status returns normally");
    const std::string status=lua.tolstring(state,-1,nullptr);
    check(status.find("target=5")!=std::string::npos,"status reports the assigned render target");
    closeState(state);
    HMODULE adapter=LoadLibraryExA(argv[2],nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);
    check(adapter && GetProcAddress(adapter,"luaopen_f117_charts"),"installed chart entry point exported");
    std::puts("native chart host checks passed (pixels not rendered)");return 0;
}
