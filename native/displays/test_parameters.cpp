// Real DCS Lua 5.1, instrumented parameter store; no cockpit is started.
#include "F117Displays.cpp"
#include <cstdlib>
namespace {
void check(bool ok,const char* message) {
    if (!ok) {std::fprintf(stderr,"FAIL: %s\n",message);std::exit(1);}
}
int fakeHandleStorage=0;
std::string storedName,storedText;
int writes=0;
bool handleAvailable=true;
void* fakeHandle(const char* name) {
    storedName=name;
    return handleAvailable ? &fakeHandleStorage : nullptr;
}
void fakeSetString(void* handle,const char* text) {
    check(handle==&fakeHandleStorage,"text is written through the looked-up handle");
    storedText=text;++writes;
}
}
int main(int argc,char** argv) {
    check(argc==3,"supply lua.dll and adapter paths");
    HMODULE runtime=LoadLibraryExA(argv[1],nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);
    check(runtime && bindLua(),"real DCS Lua API");
    lua_State* (*newState)()=nullptr;void (*closeState)(lua_State*)=nullptr;
    void (*getfield)(lua_State*,int,const char*)=nullptr;
    void (*pushnil)(lua_State*)=nullptr;
    int (*pcall)(lua_State*,int,int,int)=nullptr;int (*toboolean)(lua_State*,int)=nullptr;
    int (*isnumber)(lua_State*,int)=nullptr;
    check(symbol(runtime,"luaL_newstate",newState) && symbol(runtime,"lua_close",closeState) &&
        symbol(runtime,"lua_getfield",getfield) && symbol(runtime,"lua_pushnil",pushnil) &&
        symbol(runtime,"lua_pcall",pcall) && symbol(runtime,"lua_toboolean",toboolean) &&
        symbol(runtime,"lua_isnumber",isnumber),"host exports");
    auto* state=newState();
    parameterAPI={fakeHandle,fakeSetString};
    auto write=[&](const char* text) {
        lua.settop(state,0);lua.pushcclosure(state,setStringParameter,0);
        lua.pushstring(state,"F117_MAP_WP_1_LABEL");
        if (text) lua.pushstring(state,text); else pushnil(state);
        check(pcall(state,2,1,0)==0,"set_string returns normally");
        bool ok=toboolean(state,-1)!=0;lua.settop(state,0);return ok;
    };
    // Confirms this Lua runtime treats these as numbers, which is the reason for the export.
    for (const char* text:{"25","007","1.5","1E5","0X1F"," 5","INF","NAN"}) {
        lua.settop(state,0);lua.pushstring(state,text);
        check(isnumber(state,1)!=0,"DCS Lua reports numeric-looking text as a number");
        lua.settop(state,0);
        check(write(text) && storedText==text,"numeric-looking text reaches the store unchanged");
    }
    check(storedName=="F117_MAP_WP_1_LABEL","parameter is selected by name");
    check(write("ALPHA") && storedText=="ALPHA","ordinary text is stored");
    check(write("") && storedText.empty(),"empty text clears a label");
    int before=writes;
    check(!write(nullptr) && writes==before,"missing text reports failure and writes nothing");
    handleAvailable=false;
    check(!write("23") && writes==before,"missing handle reports failure and writes nothing");
    closeState(state);
    HMODULE adapter=LoadLibraryExA(argv[2],nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);
    LuaFunction open=nullptr;
    check(adapter && symbol(adapter,"luaopen_f117_params",open),"built parameter export");
    state=newState();check(open(state)==1,"actual DLL API table");
    getfield(state,-1,"set_string");lua.pushstring(state,"F117_TEST");lua.pushstring(state,"007");
    check(pcall(state,2,1,0)==0 && !toboolean(state,-1),"no cockpit runtime reports failure so Lua can fall back");
    closeState(state);FreeLibrary(adapter);
    std::puts("PASS: native text parameters, numeric-looking text, failure reporting and DLL export");
    return 0;
}
