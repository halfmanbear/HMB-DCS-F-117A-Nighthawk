// Host-side lifecycle tests using DCS's Lua 5.1 and an instrumented baker API.
// No DCS context or renderer is started by these tests.
#include "F117Displays.cpp"
#include <cstdlib>

namespace {
int constructed=0,destroyed=0,initialized=0,switched=0,failAt=0;
int indices[3]={},dimensions[3]={};
double readiness=-1;
unsigned char contextMemory[0x148]={};
struct Indicator {const char* marker;};
Indicator indicators[]={{"F117_HSD_SOURCE"},{"HUD"},{"F117_VSD_SOURCE"},{"F117_IRADS_SOURCE"}};
void* pointers[]={&indicators[0],&indicators[1],&indicators[2],&indicators[3]};
void check(bool ok,const char* message) {
    if (!ok) {std::fprintf(stderr,"FAIL: %s\n",message);std::exit(1);}
}
void* fakeContext(){return contextMemory;}
void* fakeConstruct(void* object){++constructed;return object;}
void fakeDestroy(void*){++destroyed;}
void fakeSource(void*,int index,int width,int height) {
    check(width==height,"square target dimensions");
    indices[constructed-1]=index;dimensions[constructed-1]=width;
}
bool fakeInit(void*,void* context,const char* texture,const char* effect,int effectId,int format) {
    check(context==contextMemory,"source context selected");
    check(texture && !effect && effectId==0 && format==-1,"unfiltered named bake channel");
    ++initialized;return failAt!=initialized;
}
void* fakeElement(void* indicator,const char* name) {
    return std::strcmp(static_cast<Indicator*>(indicator)->marker,name)==0 ? indicator : nullptr;
}
void fakePush(void*,int purpose){check(initialized==3 && purpose==100,"commit follows all init calls");++switched;}
void fakeRemove(void*,int purpose){check(initialized==3 && (purpose==0 || purpose==1),"remove direct purposes after init");++switched;}
void fakeNumber(void*,double value){readiness=value;}
}

int main(int argc,char** argv) {
    check(argc==3,"supply DCS lua.dll and the built F117Displays.dll paths");
    HMODULE runtime=LoadLibraryExA(argv[1],nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);
    check(runtime && bindLua(),"load DCS Lua C API");
    lua_State* (*newState)()=nullptr; void (*closeState)(lua_State*)=nullptr;
    void (*getfield)(lua_State*,int,const char*)=nullptr; void (*pushnumber)(lua_State*,double)=nullptr;
    int (*pcall)(lua_State*,int,int,int)=nullptr; int (*toboolean)(lua_State*,int)=nullptr; void (*settop)(lua_State*,int)=nullptr;
    check(symbol(runtime,"luaL_newstate",newState) && symbol(runtime,"lua_close",closeState) &&
        symbol(runtime,"lua_getfield",getfield) && symbol(runtime,"lua_pushnumber",pushnumber) &&
        symbol(runtime,"lua_pcall",pcall) && symbol(runtime,"lua_toboolean",toboolean) &&
        symbol(runtime,"lua_settop",settop),"host Lua exports");
    for (int scenario=0;scenario<4;++scenario) {
        constructed=destroyed=initialized=switched=0;readiness=-1;failAt=scenario==1?2:0;
        std::memset(contextMemory,0,sizeof(contextMemory));
        Vector view{pointers,pointers+4,pointers+4};
        std::memcpy(contextMemory+0xb0,&view,sizeof(view));
        auto* state=newState();
        auto* owner=new(lua.newuserdata(state,sizeof(Owner))) Owner();
        if (scenario!=3) {
            owner->bound=true;owner->ready=reinterpret_cast<void*>(1);
            owner->api.context=fakeContext;owner->api.construct=fakeConstruct;owner->api.destroy=fakeDestroy;
            owner->api.addSource=fakeSource;owner->api.init=fakeInit;owner->api.element=fakeElement;
            owner->api.pushPurpose=fakePush;owner->api.removePurpose=fakeRemove;owner->api.setNumber=fakeNumber;
        }
        lua.newmetatable(state,"test.owner");lua.pushcclosure(state,collect,0);lua.setfield(state,-2,"__gc");
        lua.setmetatable(state,-2);
        lua.pushcclosure(state,start,1);lua.setfield(state,-10002,"run");
        if (scenario==2) indicators[2].marker="not ready";
        auto run=[&](double resolution) {
            getfield(state,-10002,"run");pushnumber(state,resolution);
            check(pcall(state,1,2,0)==0,"native start returns normally");
            bool ok=toboolean(state,-2)!=0;settop(state,0);return ok;
        };
        bool ok=run(scenario==2?2048:1024);
        if (scenario==0) {
            check(ok && constructed==3 && initialized==3 && switched==9 && readiness==1,"successful commit");
            check(indices[0]==2 && indices[1]==0 && indices[2]==3,"markers select reordered sources");
            check(run(1024) && constructed==3,"start is idempotent");
        } else if (scenario==1) {
            check(!ok && constructed==2 && destroyed==2 && switched==0 && readiness==0,"partial failure rolls back");
            check(!run(1024) && constructed==2,"failed native initialization is not repeated");
        } else if (scenario==2) {
            check(!ok && constructed==0 && switched==0,"missing page preserves direct drawing");
            indicators[2].marker="F117_VSD_SOURCE";
            check(run(2048) && dimensions[0]==2048,"late page initialization can retry at selected resolution");
        } else {
            check(!ok && constructed==0 && switched==0,"absent CockpitBase preserves direct drawing");
        }
        closeState(state);
        check(destroyed==constructed,"Lua GC destroys every constructed baker exactly once");
        if (scenario!=3) check(readiness==0,"Lua GC clears readiness");
    }
    // Exercise the actual DLL export, userdata/metatable construction and GC.
    HMODULE adapter=LoadLibraryExA(argv[2],nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);
    LuaFunction open=nullptr;
    check(adapter && symbol(adapter,"luaopen_f117_displays",open),"built DLL Lua export");
    auto* state=newState();
    check(open(state)==1,"actual module returns API table");
    getfield(state,-1,"start");pushnumber(state,1024);
    check(pcall(state,1,2,0)==0 && !toboolean(state,-2),"actual module fails gracefully without CockpitBase");
    closeState(state);FreeLibrary(adapter);
    std::puts("PASS: commit, source selection, resolution, idempotence, rollback, retry, missing module, Lua GC, actual DLL load/export");
    return 0;
}
