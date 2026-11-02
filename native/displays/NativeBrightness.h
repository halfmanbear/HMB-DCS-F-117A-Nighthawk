// Private CockpitBase layouts are accepted only for the hash checked above.
// No hooks, vtable replacement, baker activation or DCS binary modification.
namespace {
constexpr size_t IndicatorParserOffset=1144; // parser the indicator uses when drawing
struct BrightnessAPI {
    void* (*context)()=nullptr;
    void* (*element)(void*,const char*)=nullptr;
    void* (*configConstruct)(void*,lua_State*,int)=nullptr;
    void (*configDestroy)(void*)=nullptr;
    void (*readState)(void*,void*)=nullptr;
    void (*changeBrightness)(void*,float)=nullptr;
    void (*shaderBrightness)(void*,float)=nullptr;
};
struct BrightnessChannel {
    const char* marker;
    std::vector<std::string> materials;
    void* configured=nullptr; // identity only; never dereferenced after this call
    size_t resolved=0;
    bool materialsReady=false;
};
BrightnessChannel brightnessChannels[]={
    {"OCIP_ROOT"},{"F117_VSD_SOURCE"},{"F117_HSD_SOURCE"},{"F117_IRADS_SOURCE"},{"dlir_picture"}};
BrightnessAPI brightnessAPI;
bool brightnessBound=false;
bool brightnessAttempted=false;
HMODULE brightnessCockpit=nullptr;
std::mutex brightnessMutex; // pages register on loader threads

// Each page's Lua state holds this DLL through package.loadlib and releases it when
// DCS closes that state after load. Pages load before the display device, so without
// a pin the DLL unloads between them and the registered names are lost.
void pinThisModule() {
    HMODULE self=nullptr;
    GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_PIN,
        reinterpret_cast<LPCWSTR>(&pinThisModule),&self);
}
bool bindBrightness() {
    // The pin outlives missions, so never keep pointers into a replaced module.
    HMODULE cockpit=GetModuleHandleW(L"CockpitBase.dll");
    if (cockpit!=brightnessCockpit) {
        brightnessCockpit=cockpit;brightnessBound=false;brightnessAttempted=false;
    }
    if (brightnessBound) return true;
    if (brightnessAttempted) return false;
    HMODULE core=GetModuleHandleW(L"edCore.dll");
    if (!cockpit || !core) return false;
    brightnessAttempted=true;
    if (!knownCockpitBuild(cockpit)) return false;
    BrightnessAPI api;
#define BRIGHT_BIND(module,field,name) if (!symbol(module,name,api.field)) return false
    BRIGHT_BIND(cockpit,context,"?binding_context@cockpit@@YAPEAVccCockpitContext@1@XZ");
    BRIGHT_BIND(cockpit,element,"?get_element_on_current_page@ccIndicator@cockpit@@UEAAPEAVElement@2@PEBD@Z");
    BRIGHT_BIND(core,configConstruct,"??0Config@Lua@@QEAA@PEAUlua_State@@H@Z");
    BRIGHT_BIND(core,configDestroy,"??1Config@Lua@@QEAA@XZ");
    BRIGHT_BIND(cockpit,readState,"?read_from_state@ccIndicationRenderParser@cockpit@@QEAAXAEAVConfig@Lua@@@Z");
    BRIGHT_BIND(cockpit,changeBrightness,"?change_brightness@ccIndicationRenderParser@cockpit@@QEAAXM@Z");
    BRIGHT_BIND(cockpit,shaderBrightness,"?set_mfd_shader_brightness@ccIndicationRenderParser@cockpit@@QEAAXM@Z");
#undef BRIGHT_BIND
    brightnessAPI=api;brightnessBound=true;return true;
}
int registerBrightness(lua_State* state) {
    const char* marker=lua.tolstring(state,1,nullptr);
    if (!marker) return result(state,false,"missing brightness marker");
    size_t index=0;
    while (index<5 && std::strcmp(marker,brightnessChannels[index].marker)) ++index;
    if (index==5) return result(state,false,"unknown brightness marker");
    std::vector<std::string> names;
    for (int i=1;i<=4096;++i) {
        lua.rawgeti(state,2,i);
        const char* name=lua.tolstring(state,-1,nullptr);
        if (!name) {lua.settop(state,-2);break;}
        if (*name && std::find(names.begin(),names.end(),name)==names.end()) names.emplace_back(name);
        lua.settop(state,-2);
    }
    if (names.empty()) return result(state,false,"no brightness materials");
    // Names must outlive the caller: DCS closes a page's Lua state straight after
    // loading it. A later mission's page load replaces them.
    std::lock_guard<std::mutex> lock(brightnessMutex);
    auto& channel=brightnessChannels[index];
    channel.materials=std::move(names);channel.configured=nullptr;channel.materialsReady=false;
    return result(state,true,"brightness materials registered");
}
bool findBrightnessSources(void* context,void* (&found)[5],int depth=0) {
    if (!context || depth>8) return false;
    auto* bytes=static_cast<unsigned char*>(context);
    const auto& indicators=*reinterpret_cast<Vector*>(bytes+0xb0);
    size_t count=0;
    if (!vectorCount(indicators,count)) return false;
    for (size_t i=0;i<count;++i) {
        void* indicator=indicators.begin[i];
        if (!indicator) continue;
        for (size_t j=0;j<5;++j) if (brightnessAPI.element(indicator,brightnessChannels[j].marker)) {
            if (found[j] && found[j]!=indicator) return false;
            found[j]=indicator;
        }
    }
    const auto& children=*reinterpret_cast<Vector*>(bytes+0x130);
    if (!vectorCount(children,count)) return false;
    for (size_t i=0;i<count;++i)
        if (children.begin[i] && !findBrightnessSources(children.begin[i],found,depth+1)) return false;
    return true;
}
// 0.5 is the native MFD shader's neutral brightness. Its negative branch has
// gain 1+1.6*(setting-0.5), so translate the existing luminance-gain controls.
float nativeVideoBrightness(float gain) {return .5f+(gain-1.f)/1.6f;}
int updateBrightness(lua_State* state) {
    float gains[5];
    for (int i=0;i<5;++i) {
        double value=lua.tonumber(state,i+1);
        if (!std::isfinite(value) || value<0 || value>1)
            return result(state,false,"invalid brightness; previous state retained");
        gains[i]=static_cast<float>(value);
    }
    std::lock_guard<std::mutex> lock(brightnessMutex);
    if (!bindBrightness()) return result(state,false,"native brightness unavailable for this CockpitBase build");
    void* found[5]={};
    auto reset=[&]() {
        for (size_t j=0;j<5;++j) if (found[j]) {
            auto* parser=static_cast<unsigned char*>(found[j])+IndicatorParserOffset;
            brightnessAPI.changeBrightness(parser,1.f);
            if (j==4) brightnessAPI.shaderBrightness(parser,.5f);
        }
    };
    if (!findBrightnessSources(brightnessAPI.context(),found))
        {reset();return result(state,false,"waiting for brightness context");}
    std::string status;
    for (size_t i=0;i<5;++i) {
        if (!found[i]) status="waiting for brightness page ";
        else if (brightnessChannels[i].materials.empty()) status="no brightness materials registered for ";
        if (!status.empty()) {
            reset();status+=brightnessChannels[i].marker;
            return result(state,false,status.c_str());
        }
    }
    for (size_t i=0;i<5;++i) {
        auto& channel=brightnessChannels[i];
        auto* parser=static_cast<unsigned char*>(found[i])+IndicatorParserOffset;
        if (channel.configured!=found[i]) {
            int top=lua.gettop(state);
            lua.createtable(state,0,1);
            lua.createtable(state,static_cast<int>(channel.materials.size()),0);
            int n=0;
            for (const auto& material:channel.materials) {
                lua.pushstring(state,material.c_str());lua.rawseti(state,-2,++n);
            }
            lua.setfield(state,-2,"brightness_sensitive_materials");
            alignas(8) unsigned char config[24]={};
            brightnessAPI.configConstruct(config,state,-1);
            const size_t before=*reinterpret_cast<size_t*>(parser+80);
            brightnessAPI.readState(parser,config);
            const size_t after=*reinterpret_cast<size_t*>(parser+80);
            channel.resolved=after>=before ? after-before : 0;
            channel.materialsReady=channel.resolved==channel.materials.size();
            brightnessAPI.configDestroy(config);
            lua.settop(state,top);
            channel.configured=found[i];
        }
    }
    for (const auto& channel:brightnessChannels) if (!channel.materialsReady) {
        reset();
        status=std::string("brightness materials unresolved for ")+channel.marker+" ("+
            std::to_string(channel.resolved)+" of "+std::to_string(channel.materials.size())+"); existing dimming retained";
        return result(state,false,status.c_str());
    }
    for (size_t i=0;i<5;++i) {
        auto* parser=static_cast<unsigned char*>(found[i])+IndicatorParserOffset;
        brightnessAPI.changeBrightness(parser,gains[i]);
        if (i==4) brightnessAPI.shaderBrightness(parser,nativeVideoBrightness(gains[i]));
    }
    return result(state,true,"native HUD/MFD renderer brightness active");
}
}
extern "C" __declspec(dllexport) int luaopen_f117_brightness(lua_State* state) {
    if (!bindLua()) return 0;
    pinThisModule();
    lua.createtable(state,0,2);
    lua.pushcclosure(state,registerBrightness,0);lua.setfield(state,-2,"register");
    lua.pushcclosure(state,updateBrightness,0);lua.setfield(state,-2,"update");
    return 1;
}
