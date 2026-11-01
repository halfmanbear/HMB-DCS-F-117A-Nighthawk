// Stores a cockpit parameter as text. Lua's handle:set() tests lua_isnumber first,
// so "007" becomes the number 7 and a "%s" element then crashes in sprintf.
// These are plain C exports resolved by name, so no CockpitBase hash pin is needed.
// Handles are looked up per call: this DLL outlives each mission's parameters.
#pragma once
namespace {
struct ParameterAPI {
    void* (*handle)(const char*);
    void (*setString)(void*,const char*);
};
ParameterAPI parameterAPI{};
HMODULE parameterCockpit=nullptr;
bool bindParameterAPI() {
    // This DLL can be pinned across missions; never keep pointers into a replaced module.
    HMODULE cockpit=GetModuleHandleW(L"CockpitBase.dll");
    if (cockpit!=parameterCockpit) {parameterCockpit=cockpit;parameterAPI={};}
    if (parameterAPI.handle && parameterAPI.setString) return true;
    ParameterAPI api{};
    if (!cockpit || !symbol(cockpit,"ed_cockpit_get_parameter_handle",api.handle) ||
        !symbol(cockpit,"ed_cockpit_update_parameter_with_string",api.setString)) return false;
    parameterAPI=api;
    return true;
}
int setStringParameter(lua_State* state) {
    const char* name=lua.tolstring(state,1,nullptr);
    const char* text=lua.tolstring(state,2,nullptr);
    bool ok=false;
    if (name && text && bindParameterAPI()) {
        if (void* handle=parameterAPI.handle(name)) {
            parameterAPI.setString(handle,text);
            ok=true;
        }
    }
    lua.pushboolean(state,ok);
    return 1;
}
}

extern "C" __declspec(dllexport) int luaopen_f117_params(lua_State* state) {
    if (!bindLua()) return 0;
    lua.createtable(state,0,1);
    lua.pushcclosure(state,setStringParameter,0);lua.setfield(state,-2,"set_string");
    return 1;
}
