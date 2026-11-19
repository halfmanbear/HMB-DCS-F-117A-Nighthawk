// F-117-owned adapter to CockpitBase's native indicator baker.
// Lua owns the session through userdata; DllMain performs no renderer work.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <new>
#include <vector>
#include <string>
#include <mutex>
#include <cmath>
#include <algorithm>

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
    const char* (*tolstring)(lua_State*, int, size_t*);
    void (*rawgeti)(lua_State*, int, int);
    void (*rawseti)(lua_State*, int, int);
    int (*gettop)(lua_State*);
    void (*settop)(lua_State*, int);
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
    LUA_BIND(tonumber,"lua_tonumber"); LUA_BIND(tolstring,"lua_tolstring");
    LUA_BIND(rawgeti,"lua_rawgeti"); LUA_BIND(rawseti,"lua_rawseti");
    LUA_BIND(gettop,"lua_gettop"); LUA_BIND(settop,"lua_settop");
#undef LUA_BIND
    return true;
}

struct Vector {void** begin;void** end;void** capacity;};
bool vectorCount(const Vector& vector,size_t& count) {
    auto begin=reinterpret_cast<uintptr_t>(vector.begin);
    auto end=reinterpret_cast<uintptr_t>(vector.end);
    if ((!begin && end) || end<begin || (end-begin)%sizeof(void*)) return false;
    count=(end-begin)/sizeof(void*);
    return count<=256;
}

// Cockpit contexts are walked through DCS's exported context functions. DCS exports no
// accessor for a context's indicator list, so its position is read from three exported
// context functions that use it and accepted only when all three agree. Child contexts
// come from the exported, bounds-checked get_plugin_by_index.
struct ContextLayout {
    size_t indicators=0;
    void* (*child)(void*,unsigned)=nullptr;
    HMODULE module=nullptr;
};
ContextLayout contextLayout;

const unsigned char* functionCode(const void* function) {
    auto* code=static_cast<const unsigned char*>(function);
    if (code && code[0]==0xE9) {
        std::int32_t jump;std::memcpy(&jump,code+1,4);
        code+=5+jump;
    }
    return code;
}
bool plausibleOffset(std::uint32_t value) {return value>0 && value<0x1000 && value%8==0;}
bool isWideLoad(const unsigned char* c) { // mov r64,[base+disp32]
    return (c[0]&0xF8)==0x48 && c[1]==0x8B && (c[2]&0xC0)==0x80 && (c[2]&7)!=4;
}
// A vector's first and last pointers loaded from the same base, the second 8 bytes on.
std::uint32_t vectorLoadOffset(const void* function,size_t length) {
    const unsigned char* c=functionCode(function);
    if (!c) return 0;
    for (size_t i=0;i+7<=length;++i) {
        if (!isWideLoad(c+i)) continue;
        const int base=((c[i]&1)<<3)|(c[i+2]&7);
        std::uint32_t first;std::memcpy(&first,c+i+3,4);
        for (size_t j=i+7;j<i+23 && j+7<=length;++j) {
            if (!isWideLoad(c+j) || (((c[j]&1)<<3)|(c[j+2]&7))!=base) continue;
            std::uint32_t last;std::memcpy(&last,c+j+3,4);
            if (last==first+8) return plausibleOffset(first) ? first : 0;
        }
    }
    return 0;
}
// The first "lea rcx,[base+disp32]": the list passed as the first argument.
std::uint32_t firstArgumentOffset(const void* function,size_t length) {
    const unsigned char* c=functionCode(function);
    if (!c) return 0;
    for (size_t i=0;i+7<=length;++i)
        if ((c[i]==0x48 || c[i]==0x49) && c[i+1]==0x8D && (c[i+2]&0xF8)==0x88 && (c[i+2]&7)!=4) {
            std::uint32_t offset;std::memcpy(&offset,c+i+3,4);
            return plausibleOffset(offset) ? offset : 0;
        }
    return 0;
}
bool bindContextLayout(HMODULE dll) {
    if (!dll) return false;
    if (contextLayout.module==dll && contextLayout.indicators) return true;
    ContextLayout layout;layout.module=dll;
    const void* draw=GetProcAddress(dll,"?draw@ccCockpitContext@cockpit@@QEAAXXZ");
    const void* drawScreen=GetProcAddress(dll,"?draw_screenspace@ccCockpitContext@cockpit@@QEAAXXZ");
    const void* reinit=GetProcAddress(dll,"?reinit_indicator@ccCockpitContext@cockpit@@QEAAXAEAVConfig@Lua@@H@Z");
    if (!draw || !drawScreen || !reinit ||
        !symbol(dll,"?get_plugin_by_index@ccCockpitContext@cockpit@@QEAAPEAV12@I@Z",layout.child)) return false;
    const std::uint32_t a=vectorLoadOffset(draw,0x80),b=vectorLoadOffset(drawScreen,0x80);
    const std::uint32_t c=firstArgumentOffset(reinit,0x40);
    if (!a || a!=b || a!=c) return false;
    layout.indicators=a;
    contextLayout=layout;
    return true;
}
// Visits every indicator with its owning context and zero-based index, then the child
// contexts. Stops and returns false if the visitor does or a list is malformed.
template<class Visit> bool walkContexts(void* context,Visit& visit,int depth=0) {
    if (!context || depth>8 || !contextLayout.indicators || !contextLayout.child) return false;
    const auto& list=*reinterpret_cast<const Vector*>(static_cast<unsigned char*>(context)+contextLayout.indicators);
    size_t count=0;
    if (!vectorCount(list,count)) return false;
    for (size_t i=0;i<count;++i)
        if (list.begin[i] && !visit(context,list.begin[i],static_cast<int>(i))) return false;
    for (unsigned i=0;i<256;++i) {
        void* child=contextLayout.child(context,i);
        if (!child) break;
        if (!walkContexts(child,visit,depth+1)) return false;
    }
    return true;
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
    bool (*hasPurpose)(const void*,int);
    void* (*parameter)(const char*);
    void (*setNumber)(void*,double);
    const void* indicatorVtable; // source pages are plain ccIndicator objects
};
bool bindNative(NativeAPI& api) {
    HMODULE dll=GetModuleHandleW(L"CockpitBase.dll");
    if (!dll || !bindContextLayout(dll)) return false;
#define NATIVE(field,name) if (!symbol(dll,name,api.field)) return false
    NATIVE(indicatorVtable,"??_7ccIndicator@cockpit@@6BccContextRelatedObject@1@@");
    NATIVE(context,"?binding_context@cockpit@@YAPEAVccCockpitContext@1@XZ");
    NATIVE(construct,"??0ccIndicatorBake@cockpit@@QEAA@XZ");
    NATIVE(destroy,"??1ccIndicatorBake@cockpit@@UEAA@XZ");
    NATIVE(addSource,"?addSource@ccIndicatorBake@cockpit@@QEAAXHHH@Z");
    NATIVE(init,"?init@ccIndicatorBake@cockpit@@QEAA_NPEAVccCockpitContext@2@PEBD1W4IndBakePostEff@2@H@Z");
    NATIVE(element,"?get_element_on_current_page@ccIndicator@cockpit@@UEAAPEAVElement@2@PEBD@Z");
    NATIVE(pushPurpose,"?push_purpose@ccIndicator@cockpit@@UEAAXH@Z");
    NATIVE(removePurpose,"?remove_purpose@ccIndicator@cockpit@@UEAAXH@Z");
    NATIVE(hasPurpose,"?has_a_purpose_assigned@ccIndicator@cockpit@@QEBA_NH@Z");
    NATIVE(parameter,"ed_cockpit_get_parameter_handle");
    NATIVE(setNumber,"ed_cockpit_update_parameter_with_number");
#undef NATIVE
    return true;
}

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
    bool modeSet=false, diagnostic=false;
};
// DCS exports no size for ccIndicatorBake, so each baker gets a generous block, about nine
// times the current class. After construction the adapter finds the last byte the
// constructor set and refuses the baker if it reaches past half the block.
static constexpr size_t BakerBlock=0x1000, BakerLimit=BakerBlock/2;

size_t constructedExtent(const void* block) {
    auto* bytes=static_cast<const unsigned char*>(block);
    size_t end=BakerBlock;
    while (end>0 && !bytes[end-1]) --end;
    return end;
}
bool findSources(Owner& owner,void* root) {
    auto visit=[&owner](void* context,void* indicator,int index) {
        // Only plain ccIndicator pages carry source markers; skip anything else unread.
        if (*static_cast<void* const*>(indicator)!=owner.api.indicatorVtable) return true;
        for (auto& channel:owner.channels)
            if (owner.api.element(indicator,channel.marker)) {
                if (channel.source.indicator && channel.source.indicator!=indicator) return false;
                channel.source={context,indicator,index};
            }
        return true;
    };
    return walkContexts(root,visit);
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
// Render purpose numbers are DCS's own render_purpose table, passed in by Lua from the
// first argument on: whole, distinct and in range, or refused.
bool readPurposes(lua_State* state,int first,int* out,int count) {
    for (int i=0;i<count;++i) {
        const double value=lua.tonumber(state,first+i);
        if (!std::isfinite(value) || value!=std::floor(value) || value<0 || value>1000) return false;
        out[i]=static_cast<int>(value);
        for (int j=0;j<i;++j) if (out[j]==out[i]) return false;
    }
    return true;
}
Owner* upvalue(lua_State* state) {
    return static_cast<Owner*>(lua.touserdata(state,-10003)); // Lua 5.1 upvalue 1
}
int start(lua_State* state) {
    auto* owner=upvalue(state);
    if (!owner) return result(state,false,"missing compositor owner");
    const bool diagnostic=lua.tonumber(state,2)==1;
    if (owner->modeSet && owner->diagnostic!=diagnostic)
        return result(state,false,"compositor mode changed; restart cockpit required");
    owner->modeSet=true;owner->diagnostic=diagnostic;
    if (diagnostic) owner->channels[2].marker="F117_BAKE_TEST_SOURCE";
    if (owner->active) return result(state,true,"native MFD compositor already active");
    if (owner->failed) return result(state,false,"compositor unavailable; direct drawing retained");
    int purposes[3]; // general, HUD-only view, bake
    if (!readPurposes(state,3,purposes,3))
        return result(state,false,"DCS render purposes not supplied; direct drawing retained");
    const int general=purposes[0],hudOnly=purposes[1],bake=purposes[2];
    if (!owner->bound) {
        if (!bindNative(owner->api)) {
            owner->failed=true;
            return result(state,false,"CockpitBase exports or context layout not confirmed; direct drawing retained");
        }
        owner->ready=owner->api.parameter(diagnostic?"F117_LCD_TEST_READY":"F117_LCD_READY");
        owner->api.setNumber(owner->ready,0);
        owner->bound=true;
    }
    for (auto& channel:owner->channels) channel.source={};
    void* context=owner->api.context();
    if (!findSources(*owner,context)) return result(state,false,"waiting for cockpit context");
    const int first=diagnostic?2:0;
    for (int i=first;i<3;++i)
        if (!owner->channels[i].source.indicator) return result(state,false,"waiting for MFD source pages");
    // Each source page declares its purposes from the same DCS table, so it must already
    // hold the general purpose under the number supplied.
    bool hadHudOnly[3]={};
    for (int i=first;i<3;++i) {
        const void* indicator=owner->channels[i].source.indicator;
        if (!owner->api.hasPurpose(indicator,general) || owner->api.hasPurpose(indicator,bake)) {
            owner->failed=true;
            return result(state,false,"source page purposes do not match DCS render purposes; direct drawing retained");
        }
        hadHudOnly[i]=owner->api.hasPurpose(indicator,hudOnly);
    }
    double requested=lua.tonumber(state,1);
    if (!(requested>=128 && requested<=4096)) requested=1024;
    int resolution=static_cast<int>(requested);
    for (int i=first;i<3;++i) {
        auto& channel=owner->channels[i];
        channel.baker=HeapAlloc(GetProcessHeap(),HEAP_ZERO_MEMORY,BakerBlock);
        if (!channel.baker) {
            destroyBakers(*owner);owner->failed=true;
            return result(state,false,"baker allocation failed; direct drawing retained");
        }
        owner->api.construct(channel.baker);
        if (constructedExtent(channel.baker)>BakerLimit) {
            destroyBakers(*owner);owner->failed=true;
            return result(state,false,"native baker larger than expected; direct drawing retained");
        }
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
    for (int i=first;i<3;++i) {
        auto& channel=owner->channels[i];
        owner->api.pushPurpose(channel.source.indicator,bake);
        owner->api.removePurpose(channel.source.indicator,general);
        owner->api.removePurpose(channel.source.indicator,hudOnly);
    }
    bool switched=true;
    for (int i=first;i<3;++i) {
        const void* indicator=owner->channels[i].source.indicator;
        switched=switched && owner->api.hasPurpose(indicator,bake) &&
            !owner->api.hasPurpose(indicator,general) && !owner->api.hasPurpose(indicator,hudOnly);
    }
    if (!switched) {
        for (int i=first;i<3;++i) {
            void* indicator=owner->channels[i].source.indicator;
            owner->api.removePurpose(indicator,bake);
            if (!owner->api.hasPurpose(indicator,general)) owner->api.pushPurpose(indicator,general);
            if (hadHudOnly[i] && !owner->api.hasPurpose(indicator,hudOnly)) owner->api.pushPurpose(indicator,hudOnly);
        }
        destroyBakers(*owner);owner->failed=true;
        return result(state,false,"bake purpose not confirmed; direct drawing restored");
    }
    owner->active=true;
    owner->api.setNumber(owner->ready,1);
    if (diagnostic) {
        const auto& channel=owner->channels[2];
        char message[320];
        std::snprintf(message,sizeof(message),
            "centre native bake test active: marker=%s context=%s index=%d texture=%s resolution=%d; pixels unverified",
            channel.marker,channel.source.context?"ok":"missing",channel.source.index,channel.texture,resolution);
        return result(state,true,message);
    }
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

#include "NativeBrightness.h"
#include "NativeCharts.h"
#include "NativeParameters.h"
