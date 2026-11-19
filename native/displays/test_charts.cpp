// Real DCS Lua 5.1 with instrumented chart objects. No renderer/game is started.
#include "F117Displays.cpp"
#include <cstdlib>
namespace {
void check(bool ok,const char* why){if(!ok){std::fprintf(stderr,"FAIL: %s\n",why);std::exit(1);}}
unsigned char chartContext[0x148]={},chartIndicator[1800]={},chartDevice[1400]={};
unsigned char mapRecord[48]={};
void* chartPointers[]={chartIndicator};
int indicatorIdentity=0,deviceIdentity=0,changes=0;
void* chartContextStub(){return chartContext;}
void* noChild(void*,unsigned){return nullptr;}
void* chartElementStub(void* object,const char* name){return object==chartIndicator && !std::strcmp(name,"F117_CHART_PRODUCER") ? object:nullptr;}
const void* chartMapStub(void*){return mapRecord;}
void chartChangeStub(void*){++changes;}
// The producer page declares {BAKE}=100; the kneeboard toggle may have added 1 and 2.
bool chartPurposes[101]={};
bool stuckPurpose=false;
void chartRemovePurposeStub(void* indicator,int purpose){
    check(indicator==chartIndicator && purpose>=0 && purpose<=2,"UI purpose removed only from owned chart indicator");
    if (!stuckPurpose) chartPurposes[purpose]=false;
}
bool chartHasPurposeStub(const void* indicator,int purpose){
    check(indicator==chartIndicator,"purpose read from owned chart indicator");
    return purpose>=0 && purpose<=100 && chartPurposes[purpose];
}
// Instrumented positions; the adapter receives them only through the layout.
constexpr std::uint32_t MapView=152,Follow=1180;
double cameraX=0,cameraZ=0;
bool corruptReadBack=false;
double* cameraPointStub(void* indicator,double* out){check(indicator==chartIndicator,"camera read from owned indicator");out[0]=cameraX;out[1]=0;out[2]=cameraZ;return out;}
int renderTargetStub(const void* indicator){return *reinterpret_cast<const int*>(static_cast<const unsigned char*>(indicator)+0x470);}
bool useT4Stub(const void* device){return static_cast<const unsigned char*>(device)[1032]==0;}
unsigned pageNumberStub(const void*){return 0;}
unsigned pagesCountStub(const void*){return 1;}
unsigned pageIdStub(const void*){return 0;}
bool mapRotationStub(void* view,double& rotation){
    check(view==chartDevice+MapView,"rotation read through the map view");
    rotation=reinterpret_cast<const ChartPage*>(mapRecord)->rotation+(corruptReadBack ? 1 : 0);return true;
}
float* mapPointStub(const void* view,float* out){
    check(view==chartDevice+MapView,"centre read through the map view");
    const auto& p=*reinterpret_cast<const ChartPage*>(mapRecord);
    const bool follow=chartDevice[Follow]!=0;
    out[0]=follow ? 0.f : static_cast<float>(p.x);out[1]=0;out[2]=follow ? 0.f : static_cast<float>(p.z);return out;
}
void observeCamera(){
    const auto& p=*reinterpret_cast<const ChartPage*>(mapRecord);
    *reinterpret_cast<int*>(chartIndicator+928)=9;
    cameraX=p.x;cameraZ=p.z;
    *reinterpret_cast<float*>(chartIndicator+896)=static_cast<float>(-p.scale);
    *reinterpret_cast<float*>(chartIndicator+908)=static_cast<float>(p.scale);
    // Like the engine, derive the vertical span from the aspect the adapter wrote.
    const double aspect=static_cast<double>(*reinterpret_cast<const float*>(chartIndicator+1128))/
        static_cast<double>(*reinterpret_cast<const float*>(chartIndicator+1124));
    *reinterpret_cast<float*>(chartIndicator+900)=static_cast<float>(-p.scale*aspect);
    *reinterpret_cast<float*>(chartIndicator+912)=static_cast<float>(p.scale*aspect);
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
    Vector indicators{chartPointers,chartPointers+1,chartPointers+1};
    std::memcpy(chartContext+0xb0,&indicators,sizeof(indicators));
    chartAPI={chartContextStub,chartElementStub,chartMapStub,chartChangeStub,&indicatorIdentity,&deviceIdentity,chartRemovePurposeStub,chartHasPurposeStub,
        cameraPointStub,renderTargetStub,useT4Stub,pageNumberStub,pagesCountStub,pageIdStub,mapRotationStub,mapPointStub,
        ChartLayout{56,928,1744,1124,896,1040,MapView,Follow}};
    chartDevice[Follow]=1;
    chartPurposes[100]=chartPurposes[1]=chartPurposes[2]=true;
    chartsBound=true;
    contextLayout.indicators=0xb0;contextLayout.child=noChild;
    double bakePurpose=100;
    auto update=[&](double x=1000,double width=50000,double level=3,double rotation=.25){
        lua.settop(state,0);getfield(state,-10002,"charts");getfield(state,-1,"update");
        for(double value:{x,2000.,rotation,width,width*.9,level,0.,1.,2.,bakePurpose})pushnumber(state,value);
        check(pcall(state,10,2,0)==0,"chart update returned normally");
        bool ready=toboolean(state,-2)!=0;lua.settop(state,0);return ready;
    };
    check(!update() && changes==1,"first update waits for observed render camera");
    const auto& page=*reinterpret_cast<const ChartPage*>(mapRecord);
    check(page.x==1000 && page.z==2000 && page.scale==25000 && page.chart==3 && page.rotation==.25,"native page receives exact view");
    check(chartIndicator[1744]==1 && chartDevice[1180]==0,"only owned producer configured");
    check(!chartPurposes[1] && !chartPurposes[2] && chartPurposes[100],"producer kept out of UI purposes");
    check(std::fabs(*reinterpret_cast<const float*>(chartIndicator+1128)/
        *reinterpret_cast<const float*>(chartIndicator+1124)-.9)<1e-5,"camera aspect follows the requested window");
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
    *reinterpret_cast<void**>(chartDevice+1048)=mapRecord+48;
    chartDevice[1032]=1;
    check(!update() && changes==count,"other kneeboard render mode cannot be modified");
    chartDevice[1032]=0;
    const ChartPage kept=page;const unsigned char followKept=chartDevice[Follow]=1;
    corruptReadBack=true;
    check(!update(7000) && changes==count,"page that does not read back is refused");
    check(!std::memcmp(&kept,mapRecord,sizeof(kept)) && chartDevice[Follow]==followKept,"refused page restored");
    corruptReadBack=false;
    check(!update(7000) && changes==count+1 && chartDevice[Follow]==0,"read-back recovers");
    count=changes;bakePurpose=7;
    check(!update() && changes==count,"bake purpose the page does not hold is refused");
    bakePurpose=100;chartPurposes[1]=true;stuckPurpose=true;
    check(!update() && changes==count,"unconfirmed purpose removal writes no page");
    stuckPurpose=false;
    check(!update() && changes==count+1 && !chartPurposes[1],"purpose removal recovers");
    lua.settop(state,0);getfield(state,-10002,"charts");getfield(state,-1,"update");
    for(double value:{1000.,2000.,0.,50000.,45000.,3.})pushnumber(state,value);
    count=changes;
    check(pcall(state,6,2,0)==0 && !toboolean(state,-2) && changes==count,"update without DCS purposes refused");
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
