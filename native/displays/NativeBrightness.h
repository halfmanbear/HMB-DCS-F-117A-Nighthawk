// Native renderer brightness through DCS's exported render parser functions.
// No hooks, vtable replacement, baker activation or DCS binary modification.
namespace {
// Bytes of the parser compared before and after its material list is read.
constexpr size_t ParserSnapshotBytes=0x80;
struct BrightnessAPI {
    void* (*context)()=nullptr;
    void* (*element)(void*,const char*)=nullptr;
    void* (*configConstruct)(void*,lua_State*,int)=nullptr;
    void (*configDestroy)(void*)=nullptr;
    void (*readState)(void*,void*)=nullptr;
    void (*changeBrightness)(void*,float)=nullptr;
    void (*shaderBrightness)(void*,float)=nullptr;
    size_t parser=0; // position of the indicator's render parser
};
struct BrightnessChannel {
    const char* marker;
    std::vector<std::string> materials;
    void* configured=nullptr; // identity only; never dereferenced after this call
    size_t resolved=0;
    bool materialsReady=false;
};
// Update gains arrive in this order. The DEP follows the HUD brightness control.
BrightnessChannel brightnessChannels[]={
    {"OCIP_ROOT"},{"F117_VSD_SOURCE"},{"F117_HSD_SOURCE"},{"F117_IRADS_SOURCE"},{"dlir_picture"},
    {"F117_DEP_SOURCE"}};
constexpr size_t BrightnessChannelCount=sizeof(brightnessChannels)/sizeof(brightnessChannels[0]);
constexpr size_t VideoChannel=4; // camera picture: also drives the MFD video shader
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
// The indicator's render parser has no accessor. Its position is read from ccIndicator::draw,
// which hands the parser to the renderer, and used only if set_render_materials stores the
// parser's target material at the same place.
size_t parserOffset(HMODULE cockpit) {
    const unsigned char* draw=functionCode(reinterpret_cast<const void*>(
        GetProcAddress(cockpit,"?draw@ccIndicator@cockpit@@UEAAXE@Z")));
    const unsigned char* materials=functionCode(reinterpret_cast<const void*>(
        GetProcAddress(cockpit,"?set_render_materials@ccIndicator@cockpit@@IEAAXXZ")));
    if (!draw || !materials) return 0;
    std::uint32_t offset=0;
    for (size_t i=0;i+7<=0x80;++i)  // first "lea rdx,[base+disp32]"
        if ((draw[i]==0x48 || draw[i]==0x49) && draw[i+1]==0x8D && (draw[i+2]&0xF8)==0x90 && (draw[i+2]&7)!=4) {
            std::memcpy(&offset,draw+i+3,4);
            break;
        }
    if (!plausibleOffset(offset)) return 0;
    for (size_t i=0;i+7<=0x400;++i)  // "mov [base+disp32],rax" at the same position
        if ((materials[i]==0x48 || materials[i]==0x49) && materials[i+1]==0x89 && (materials[i+2]&0xF8)==0x80 &&
            (materials[i+2]&7)!=4 && !std::memcmp(materials+i+3,&offset,4))
            return offset;
    return 0;
}
// read_from_state appends the registered materials to the parser's brightness list. The one
// parser field that grows by the number found is that list's size; anything else is refused.
size_t resolvedMaterials(const unsigned char* before,const unsigned char* after,size_t expected) {
    size_t changed=0,grown=0;
    for (size_t at=0;at+8<=ParserSnapshotBytes;at+=8) {
        std::uint64_t a,b;std::memcpy(&a,before+at,8);std::memcpy(&b,after+at,8);
        if (a!=b) {++changed;grown=b>a ? static_cast<size_t>(b-a) : 0;}
    }
    return changed==1 && grown<=expected ? grown : 0;
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
    if (!bindContextLayout(cockpit)) return false;
    BrightnessAPI api;
    api.parser=parserOffset(cockpit);
    if (!api.parser) return false;
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
    while (index<BrightnessChannelCount && std::strcmp(marker,brightnessChannels[index].marker)) ++index;
    if (index==BrightnessChannelCount) return result(state,false,"unknown brightness marker");
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
bool findBrightnessSources(void* root,void* (&found)[BrightnessChannelCount]) {
    auto visit=[&found](void*,void* indicator,int) {
        for (size_t j=0;j<BrightnessChannelCount;++j) if (brightnessAPI.element(indicator,brightnessChannels[j].marker)) {
            if (found[j] && found[j]!=indicator) return false;
            found[j]=indicator;
        }
        return true;
    };
    return walkContexts(root,visit);
}
// 0.5 is the native MFD shader's neutral brightness. Its negative branch has
// gain 1+1.6*(setting-0.5), so translate the existing luminance-gain controls.
float nativeVideoBrightness(float gain) {return .5f+(gain-1.f)/1.6f;}
int updateBrightness(lua_State* state) {
    float gains[BrightnessChannelCount];
    for (int i=0;i<static_cast<int>(BrightnessChannelCount);++i) {
        double value=lua.tonumber(state,i+1);
        if (!std::isfinite(value) || value<0 || value>1)
            return result(state,false,"invalid brightness; previous state retained");
        gains[i]=static_cast<float>(value);
    }
    std::lock_guard<std::mutex> lock(brightnessMutex);
    if (!bindBrightness()) return result(state,false,"native brightness exports or parser position not confirmed");
    void* found[BrightnessChannelCount]={};
    auto reset=[&]() {
        for (size_t j=0;j<BrightnessChannelCount;++j) if (found[j]) {
            auto* parser=static_cast<unsigned char*>(found[j])+brightnessAPI.parser;
            brightnessAPI.changeBrightness(parser,1.f);
            if (j==VideoChannel) brightnessAPI.shaderBrightness(parser,.5f);
        }
    };
    if (!findBrightnessSources(brightnessAPI.context(),found))
        {reset();return result(state,false,"waiting for brightness context");}
    std::string status;
    for (size_t i=0;i<BrightnessChannelCount;++i) {
        if (!found[i]) status="waiting for brightness page ";
        else if (brightnessChannels[i].materials.empty()) status="no brightness materials registered for ";
        if (!status.empty()) {
            reset();status+=brightnessChannels[i].marker;
            return result(state,false,status.c_str());
        }
    }
    for (size_t i=0;i<BrightnessChannelCount;++i) {
        auto& channel=brightnessChannels[i];
        auto* parser=static_cast<unsigned char*>(found[i])+brightnessAPI.parser;
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
            unsigned char before[ParserSnapshotBytes],after[ParserSnapshotBytes];
            std::memcpy(before,parser,sizeof(before));
            brightnessAPI.readState(parser,config);
            std::memcpy(after,parser,sizeof(after));
            channel.resolved=resolvedMaterials(before,after,channel.materials.size());
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
    for (size_t i=0;i<BrightnessChannelCount;++i) {
        auto* parser=static_cast<unsigned char*>(found[i])+brightnessAPI.parser;
        brightnessAPI.changeBrightness(parser,gains[i]);
        if (i==VideoChannel) brightnessAPI.shaderBrightness(parser,nativeVideoBrightness(gains[i]));
    }
    return result(state,true,"native HUD/MFD/DEP renderer brightness active");
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
