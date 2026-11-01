// Real DCS Lua 5.1, instrumented native renderer; no DCS renderer is started.
#include "F117Displays.cpp"
#include <cstdlib>
namespace {
void check(bool ok,const char* message) {
    if (!ok) {std::fprintf(stderr,"FAIL: %s\n",message);std::exit(1);}
}
struct FakeIndicator {const char* marker;unsigned char memory[1300];};
FakeIndicator displays[5]={};
void* displayPointers[5]={};
unsigned char brightnessContext[0x148]={};
float applied[5]={},videoSetting=0;
int configuredCount=0;
bool resolveMaterials=true;
void (*getfield)(lua_State*,int,const char*)=nullptr;
void* fakeContext(){return brightnessContext;}
void* fakeElement(void* object,const char* marker) {
    return !std::strcmp(static_cast<FakeIndicator*>(object)->marker,marker) ? object : nullptr;
}
void* fakeConfig(void* config,lua_State* state,int) {
    getfield(state,-1,"brightness_sensitive_materials");
    size_t count=0;
    for (int i=1;i<=4096;++i) {
        lua.rawgeti(state,-1,i);const char* name=lua.tolstring(state,-1,nullptr);
        lua.settop(state,-2);if (!name) break;++count;
    }
    lua.settop(state,-2);*static_cast<size_t*>(config)=count;return config;
}
void fakeConfigDestroy(void*){}
void fakeRead(void* parser,void* config) {
    ++configuredCount;
    if (resolveMaterials) *reinterpret_cast<size_t*>(static_cast<unsigned char*>(parser)+80)+=*static_cast<size_t*>(config);
}
void fakeGain(void* parser,float gain) {
    for (size_t i=0;i<5;++i) if (parser==reinterpret_cast<unsigned char*>(&displays[i])+IndicatorParserOffset) {
        applied[i]=gain;return;
    }
    check(false,"renderer belongs to the discovered marker");
}
void fakeShader(void* parser,float setting) {
    check(parser==reinterpret_cast<unsigned char*>(&displays[4])+IndicatorParserOffset,"video shader receives camera parser");
    videoSetting=setting;
}
}
int main(int argc,char** argv) {
    check(argc==3,"supply lua.dll and adapter paths");
    HMODULE runtime=LoadLibraryExA(argv[1],nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);
    check(runtime && bindLua(),"real DCS Lua API");
    lua_State* (*newState)()=nullptr;void (*closeState)(lua_State*)=nullptr;
    void (*pushnumber)(lua_State*,double)=nullptr;
    int (*pcall)(lua_State*,int,int,int)=nullptr;int (*toboolean)(lua_State*,int)=nullptr;
    check(symbol(runtime,"luaL_newstate",newState) && symbol(runtime,"lua_close",closeState) &&
        symbol(runtime,"lua_getfield",getfield) && symbol(runtime,"lua_pushnumber",pushnumber) &&
        symbol(runtime,"lua_pcall",pcall) && symbol(runtime,"lua_toboolean",toboolean),"host exports");
    auto* state=newState();
    auto registerPage=[&](size_t index) {
        lua.pushcclosure(state,registerBrightness,0);lua.pushstring(state,brightnessChannels[index].marker);
        lua.createtable(state,2,0);
        lua.pushstring(state,"font_A");lua.rawseti(state,-2,1);
        lua.pushstring(state,"font_A");lua.rawseti(state,-2,2);
        check(pcall(state,2,1,0)==0 && toboolean(state,-1),"page registration succeeds");
        lua.settop(state,0);
        check(brightnessChannels[index].materials.size()==1,"materials deduplicated");
    };
    for (size_t i=0;i<5;++i) {
        displays[i].marker=brightnessChannels[i].marker;
        displayPointers[4-i]=&displays[i];registerPage(i);
    }
    Vector view{displayPointers,displayPointers+5,displayPointers+5};
    std::memcpy(brightnessContext+0xb0,&view,sizeof(view));
    brightnessAPI={fakeContext,fakeElement,fakeConfig,fakeConfigDestroy,fakeRead,fakeGain,fakeShader};
    brightnessBound=true;
    auto update=[&](double hud=.7) {
        lua.settop(state,0);lua.pushcclosure(state,updateBrightness,0);
        for (double gain:{hud,.12,.14,.16,.16}) pushnumber(state,gain);
        check(pcall(state,5,2,0)==0,"brightness update returns normally");
        bool ok=toboolean(state,-2)!=0;lua.settop(state,0);return ok;
    };
    check(update() && configuredCount==5,"all five native parsers configured");
    check(std::fabs(applied[0]-.7f)<1e-6f && std::fabs(applied[1]-.12f)<1e-6f &&
          std::fabs(applied[2]-.14f)<1e-6f && std::fabs(applied[3]-.16f)<1e-6f,"independent gains and marker discovery");
    check(std::fabs((1.f+1.6f*(videoSetting-.5f))-.16f)<1e-6f,"camera shader preserves luminance gain");
    check(update() && configuredCount==5,"updates do not append duplicate native material lists");
    check(!update(std::nan("")) && std::fabs(applied[0]-.7f)<1e-6f,"nonfinite input leaves native state intact");
    displays[2].marker="missing";
    check(!update() && applied[0]==1.f && videoSetting==.5f,"missing page resets live native gains before fallback");
    displays[2].marker=brightnessChannels[2].marker;
    check(update(),"late source can retry");
    resolveMaterials=false;registerPage(1);
    check(!update() && applied[0]==1.f,"unresolved materials retain fallback");
    int failedCount=configuredCount;
    check(!update() && configuredCount==failedCount,"unresolved registration does not leak duplicate material lists");
    resolveMaterials=true;registerPage(1);check(update(),"fresh page registration retries material resolution");
    // DCS closes each page's Lua state straight after load; registration must survive it.
    closeState(state);
    state=newState();
    for (const auto& channel:brightnessChannels) check(!channel.materials.empty(),"page state closure keeps registered names");
    configuredCount=0;
    for (auto& channel:brightnessChannels) channel.configured=nullptr;
    check(update() && configuredCount==5,"brightness activates after every page state has closed");
    std::vector<std::string> saved;
    saved.swap(brightnessChannels[1].materials);
    lua.settop(state,0);lua.pushcclosure(state,updateBrightness,0);
    for (int i=0;i<5;++i) pushnumber(state,.5);
    check(pcall(state,5,2,0)==0 && !toboolean(state,-2),"missing materials report failure");
    check(std::strstr(lua.tolstring(state,-1,nullptr),"F117_VSD_SOURCE")!=nullptr,"status names the blocking page");
    lua.settop(state,0);
    saved.swap(brightnessChannels[1].materials);
    closeState(state);
    // A page loads the DLL through package.loadlib and DCS then closes that state.
    // Lua's handle GC calls FreeLibrary, which must not discard registered names.
    void (*openLibs)(lua_State*)=nullptr;
    check(symbol(runtime,"luaL_openlibs",openLibs),"Lua standard library export");
    check(!GetModuleHandleA("F117Displays.dll"),"adapter is not loaded before the first page");
    state=newState();openLibs(state);
    getfield(state,-10002,"package");getfield(state,-1,"loadlib");
    lua.pushstring(state,argv[2]);lua.pushstring(state,"luaopen_f117_brightness");
    check(pcall(state,2,1,0)==0 && pcall(state,0,1,0)==0,"page loads the module through package.loadlib");
    getfield(state,-1,"register");lua.pushstring(state,"OCIP_ROOT");
    lua.createtable(state,1,0);lua.pushstring(state,"font_A");lua.rawseti(state,-2,1);
    check(pcall(state,2,1,0)==0 && toboolean(state,-1),"page registers through the real module");
    closeState(state);
    check(GetModuleHandleA("F117Displays.dll")!=nullptr,"closing the page state keeps the module and its names");
    HMODULE adapter=LoadLibraryExA(argv[2],nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);
    LuaFunction open=nullptr;
    check(adapter && symbol(adapter,"luaopen_f117_brightness",open),"built brightness export");
    state=newState();check(open(state)==1,"actual DLL API table");
    getfield(state,-1,"update");for (int i=0;i<5;++i) pushnumber(state,.5);
    check(pcall(state,5,2,0)==0 && !toboolean(state,-2),"unsupported native runtime falls back");
    closeState(state);FreeLibrary(adapter);
    std::puts("PASS: native brightness discovery, material registration, gains, camera conversion, retries, fallback, page state closure and DLL export");
    return 0;
}
