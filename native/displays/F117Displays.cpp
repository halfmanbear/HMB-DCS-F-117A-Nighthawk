// F-117-owned adapter to CockpitBase's native indicator baker.
// Lua owns the session through userdata; DllMain performs no renderer work.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <bcrypt.h>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <new>

struct lua_State;
using LuaFunction = int (*)(lua_State*);
namespace {
struct LuaAPI {
    void* (*newuserdata)(lua_State*, size_t);
    int (*newmetatable)(lua_State*, const char*);
    int (*setmetatable)(lua_State*, int);
    void (*pushcclosure)(lua_State*, LuaFunction, int);
    void (*pushvalue)(lua_State*, int);
    void (*setfield)(lua_State*, int, const char*);
    void (*createtable)(lua_State*, int, int);
    void (*pushboolean)(lua_State*, int);
    void (*pushstring)(lua_State*, const char*);
    void* (*touserdata)(lua_State*, int);
    double (*tonumber)(lua_State*, int);
} lua;
template<class T> bool symbol(HMODULE dll, const char* name, T& out) {
    out = reinterpret_cast<T>(GetProcAddress(dll, name));
    return out != nullptr;
}
bool bindLua() {
    HMODULE dll = GetModuleHandleW(L"lua.dll");
    if (!dll) return false;
#define LUA_BIND(field, name) if (!symbol(dll, name, lua.field)) return false
    LUA_BIND(newuserdata,"lua_newuserdata"); LUA_BIND(newmetatable,"luaL_newmetatable");
    LUA_BIND(setmetatable,"lua_setmetatable"); LUA_BIND(pushcclosure,"lua_pushcclosure");
    LUA_BIND(pushvalue,"lua_pushvalue"); LUA_BIND(setfield,"lua_setfield");
    LUA_BIND(createtable,"lua_createtable"); LUA_BIND(pushboolean,"lua_pushboolean");
    LUA_BIND(pushstring,"lua_pushstring"); LUA_BIND(touserdata,"lua_touserdata");
    LUA_BIND(tonumber,"lua_tonumber");
#undef LUA_BIND
    return true;
}

// The opaque allocation and context vector offsets are pinned to this build.
// Export lookup alone does not establish C++ object-layout compatibility.
bool knownCockpitBuild(HMODULE dll) {
    const unsigned char expected[32] = {
        0xfb,0x0a,0x09,0xbe,0x70,0x62,0x7c,0x77,0x90,0xde,0xa1,0x52,0x7c,0xed,0xfe,0xe4,
        0x30,0x82,0xbb,0x8b,0x11,0x24,0x84,0xd5,0xc8,0x5b,0xe1,0xd9,0x9d,0x33,0xde,0x95};
    wchar_t path[32768];
    DWORD length = GetModuleFileNameW(dll,path,32768);
    if (!length || length >= 32768) return false;
    HANDLE file = CreateFileW(path,GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,
        nullptr,OPEN_EXISTING,FILE_FLAG_SEQUENTIAL_SCAN,nullptr);
    if (file == INVALID_HANDLE_VALUE) return false;
    BCRYPT_ALG_HANDLE algorithm = nullptr;
    BCRYPT_HASH_HANDLE hash = nullptr;
    unsigned char digest[32], buffer[16384];
    bool ok = BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0) >= 0;
    if (ok) ok = BCryptCreateHash(algorithm,&hash,nullptr,0,nullptr,0,0) >= 0;
    DWORD count = 0;
    while (ok) {
        if (!ReadFile(file,buffer,sizeof(buffer),&count,nullptr)) {ok=false;break;}
        if (!count) break;
        ok = BCryptHashData(hash,buffer,count,0) >= 0;
    }
    if (ok) ok = BCryptFinishHash(hash,digest,sizeof(digest),0) >= 0;
    if (hash) BCryptDestroyHash(hash);
    if (algorithm) BCryptCloseAlgorithmProvider(algorithm,0);
    CloseHandle(file);
    return ok && std::memcmp(digest,expected,sizeof(digest)) == 0;
}

struct NativeAPI {
    void* (*context)();
    void* (*construct)(void*);
    void (*destroy)(void*);
    void (*addSource)(void*,int,int,int);
    bool (*init)(void*,void*,const char*,const char*,int,int);
    void* (*element)(void*,const char*);
    void (*pushPurpose)(void*,int);
    void (*removePurpose)(void*,int);
    void* (*parameter)(const char*);
    void (*setNumber)(void*,double);
};
bool bindNative(NativeAPI& api) {
    HMODULE dll=GetModuleHandleW(L"CockpitBase.dll");
    if (!dll || !knownCockpitBuild(dll)) return false;
#define NATIVE(field,name) if (!symbol(dll,name,api.field)) return false
    NATIVE(context,"?binding_context@cockpit@@YAPEAVccCockpitContext@1@XZ");
    NATIVE(construct,"??0ccIndicatorBake@cockpit@@QEAA@XZ");
    NATIVE(destroy,"??1ccIndicatorBake@cockpit@@UEAA@XZ");
    NATIVE(addSource,"?addSource@ccIndicatorBake@cockpit@@QEAAXHHH@Z");
    NATIVE(init,"?init@ccIndicatorBake@cockpit@@QEAA_NPEAVccCockpitContext@2@PEBD1W4IndBakePostEff@2@H@Z");
    NATIVE(element,"?get_element_on_current_page@ccIndicator@cockpit@@UEAAPEAVElement@2@PEBD@Z");
    NATIVE(pushPurpose,"?push_purpose@ccIndicator@cockpit@@UEAAXH@Z");
    NATIVE(removePurpose,"?remove_purpose@ccIndicator@cockpit@@UEAAXH@Z");
    NATIVE(parameter,"ed_cockpit_get_parameter_handle");
    NATIVE(setNumber,"ed_cockpit_update_parameter_with_number");
#undef NATIVE
    return true;
}

struct Vector {void** begin;void** end;void** capacity;};
struct Source {void* context=nullptr;void* indicator=nullptr;int index=-1;};
struct Channel {
    const char* marker;
    const char* texture;
    Source source;
    void* baker=nullptr;
};
struct Owner {
    NativeAPI api{};
    Channel channels[3] = {
        {"F117_VSD_SOURCE","F117_LCD_LEFT"},
        {"F117_HSD_SOURCE","F117_LCD_RIGHT"},
        {"F117_IRADS_SOURCE","F117_LCD_CENTRE"}};
    void* ready=nullptr;
    bool bound=false, active=false, failed=false;
};
// Native ccIndicatorBake's vector-deleting destructor uses a 0x1D0 stride.
static constexpr size_t BakerSize=0x1d0;
static constexpr int General=0, HudOnly=1, Bake=100;

bool vectorCount(const Vector& vector,size_t& count) {
    auto begin=reinterpret_cast<uintptr_t>(vector.begin);
    auto end=reinterpret_cast<uintptr_t>(vector.end);
    if ((!begin && end) || end<begin || (end-begin)%sizeof(void*)) return false;
    count=(end-begin)/sizeof(void*);
    return count<=256;
}
bool findSources(Owner& owner,void* context,int depth=0) {
    if (!context || depth>8) return false;
    auto bytes=static_cast<unsigned char*>(context);
    const auto& indicators=*reinterpret_cast<Vector*>(bytes+0xb0);
    size_t count=0;
    if (!vectorCount(indicators,count)) return false;
    for (size_t i=0;i<count;++i) {
        void* indicator=indicators.begin[i];
        if (!indicator) continue;
        for (auto& channel:owner.channels)
            if (owner.api.element(indicator,channel.marker)) {
                if (channel.source.indicator && channel.source.indicator!=indicator) return false;
                channel.source={context,indicator,static_cast<int>(i)};
            }
    }
    const auto& children=*reinterpret_cast<Vector*>(bytes+0x130);
    if (!vectorCount(children,count)) return false;
    for (size_t i=0;i<count;++i)
        if (children.begin[i] && !findSources(owner,children.begin[i],depth+1)) return false;
    return true;
}
void destroyBakers(Owner& owner) {
    if (owner.ready) owner.api.setNumber(owner.ready,0);
    // Reverse construction order; the native destructor unregisters callbacks
    // and releases its render textures. It does not dereference source pointers.
    for (int i=2;i>=0;--i) {
        auto& channel=owner.channels[i];
        if (channel.baker) {
            owner.api.destroy(channel.baker);
            HeapFree(GetProcessHeap(),0,channel.baker);
            channel.baker=nullptr;
        }
    }
    owner.active=false;
}
int result(lua_State* state,bool ok,const char* message) {
    lua.pushboolean(state,ok);lua.pushstring(state,message);return 2;
}
Owner* upvalue(lua_State* state) {
    return static_cast<Owner*>(lua.touserdata(state,-10003)); // Lua 5.1 upvalue 1
}
int start(lua_State* state) {
    auto* owner=upvalue(state);
    if (!owner) return result(state,false,"missing compositor owner");
    if (owner->active) return result(state,true,"native MFD compositor already active");
    if (owner->failed) return result(state,false,"compositor unavailable; direct drawing retained");
    if (!owner->bound) {
        if (!bindNative(owner->api)) {
            owner->failed=true;
            return result(state,false,"CockpitBase build/export mismatch; direct drawing retained");
        }
        owner->ready=owner->api.parameter("F117_LCD_READY");
        owner->api.setNumber(owner->ready,0);
        owner->bound=true;
    }
    for (auto& channel:owner->channels) channel.source={};
    void* context=owner->api.context();
    if (!findSources(*owner,context)) return result(state,false,"waiting for cockpit context");
    for (auto& channel:owner->channels)
        if (!channel.source.indicator) return result(state,false,"waiting for MFD source pages");
    double requested=lua.tonumber(state,1);
    if (!(requested>=128 && requested<=4096)) requested=1024;
    int resolution=static_cast<int>(requested);
    for (auto& channel:owner->channels) {
        channel.baker=HeapAlloc(GetProcessHeap(),HEAP_ZERO_MEMORY,BakerSize);
        if (!channel.baker) {
            destroyBakers(*owner);owner->failed=true;
            return result(state,false,"baker allocation failed; direct drawing retained");
        }
        owner->api.construct(channel.baker);
        // addSource arguments are source index, pixel WIDTH, pixel HEIGHT.
        // The native function lays out source rectangles; they are not offsets.
        owner->api.addSource(channel.baker,channel.source.index,resolution,resolution);
        if (!owner->api.init(channel.baker,channel.source.context,channel.texture,nullptr,0,-1)) {
            destroyBakers(*owner);owner->failed=true;
            return result(state,false,"native bake init failed; direct drawing retained");
        }
    }
    // Commit only after all channels have been created. Before this point the
    // original pages still draw normally and every texture holder is hidden.
    for (auto& channel:owner->channels) {
        owner->api.pushPurpose(channel.source.indicator,Bake);
        owner->api.removePurpose(channel.source.indicator,General);
        owner->api.removePurpose(channel.source.indicator,HudOnly);
    }
    owner->active=true;
    owner->api.setNumber(owner->ready,1);
    return result(state,true,"native MFD compositor active (VSD/HSD/IRADS)");
}
int collect(lua_State* state) {
    auto* owner=static_cast<Owner*>(lua.touserdata(state,1));
    if (owner) {destroyBakers(*owner);owner->~Owner();}
    return 0;
}
}

extern "C" __declspec(dllexport) int luaopen_f117_displays(lua_State* state) {
    if (!bindLua()) return 0;
    void* memory=lua.newuserdata(state,sizeof(Owner));
    new(memory) Owner();
    lua.newmetatable(state,"F117Displays.Session.v1");
    lua.pushcclosure(state,collect,0);lua.setfield(state,-2,"__gc");
    lua.setmetatable(state,-2);
    lua.createtable(state,0,1);
    lua.pushvalue(state,-2);lua.pushcclosure(state,start,1);lua.setfield(state,-2,"start");
    return 1;
}
