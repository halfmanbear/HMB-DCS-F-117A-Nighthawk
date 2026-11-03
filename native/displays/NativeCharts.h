// Generic DCS chart adapter. All private offsets require knownCockpitBuild().
// Own avKneeboard/ccKneeboard only: no hooks, vtable replacement or aircraft DLLs.
namespace {
struct ChartPage {double scale;unsigned int chart;unsigned int pad;double rotation,x,z;};
static_assert(sizeof(ChartPage)==40,"native chart-page prefix");
struct ChartView {double x=0,z=0,rotation=0,width=0,height=0;};
struct ChartAPI {
    void* (*context)()=nullptr;
    void* (*element)(void*,const char*)=nullptr;
    const void* (*getMap)(void*)=nullptr;
    void (*change)(void*)=nullptr;
    void* indicatorVtable=nullptr;
    void* deviceVtable=nullptr;
    void (*removePurpose)(void*,int)=nullptr;
};
ChartAPI chartAPI;
bool chartsBound=false,chartsAttempted=false;
HMODULE chartsCockpit=nullptr;
struct ChartSession {void* previousIndicator=nullptr;ChartView previous;bool pending=false;};
bool bindCharts() {
    // This DLL can be pinned across missions; never keep pointers into a replaced module.
    HMODULE dll=GetModuleHandleW(L"CockpitBase.dll");
    if (dll!=chartsCockpit) {chartsCockpit=dll;chartsBound=false;chartsAttempted=false;}
    if (chartsBound) return true;
    if (chartsAttempted) return false;
    if (!dll) return false;
    chartsAttempted=true;
    if (!knownCockpitBuild(dll)) return false;
    ChartAPI api;
#define CHART_BIND(field,name) if (!symbol(dll,name,api.field)) return false
    CHART_BIND(context,"?binding_context@cockpit@@YAPEAVccCockpitContext@1@XZ");
    CHART_BIND(element,"?get_element_on_current_page@ccIndicator@cockpit@@UEAAPEAVElement@2@PEBD@Z");
    CHART_BIND(getMap,"?get_map@avKneeboard@cockpit@@QEBAAEBUkneeboard_map_page@2@XZ");
    CHART_BIND(change,"?update_change_counter@avKneeboard@cockpit@@IEAAXXZ");
    CHART_BIND(indicatorVtable,"??_7ccKneeboard@cockpit@@6BccContextRelatedObject@1@@");
    CHART_BIND(deviceVtable,"??_7avKneeboard@cockpit@@6BccContextRelatedObject@1@@");
    CHART_BIND(removePurpose,"?remove_purpose@ccIndicator@cockpit@@UEAAXH@Z");
#undef CHART_BIND
    chartAPI=api;chartsBound=true;return true;
}
bool findChartSource(void* context,void*& found,int depth=0) {
    if (!context || depth>8) return false;
    auto* bytes=static_cast<unsigned char*>(context);
    const auto& indicators=*reinterpret_cast<Vector*>(bytes+0xb0);
    size_t count=0;
    if (!vectorCount(indicators,count)) return false;
    for (size_t i=0;i<count;++i) {
        void* candidate=indicators.begin[i];
        if (!candidate || *static_cast<void**>(candidate)!=chartAPI.indicatorVtable) continue;
        if (chartAPI.element(candidate,"F117_CHART_PRODUCER")) {
            if (found && found!=candidate) return false;
            found=candidate;
        }
    }
    const auto& children=*reinterpret_cast<Vector*>(bytes+0x130);
    if (!vectorCount(children,count)) return false;
    for (size_t i=0;i<count;++i)
        if (children.begin[i] && !findChartSource(children.begin[i],found,depth+1)) return false;
    return true;
}
bool chartClose(double a,double b) {return std::isfinite(a) && std::fabs(a-b)<1.;}
bool cameraMatches(const unsigned char* indicator,const ChartView& view) {
    // The native camera update stores the camera position and the copied
    // orthographic volume on the indicator; compare them with the requested view.
    return *reinterpret_cast<const int*>(indicator+928)==9 &&
        chartClose(*reinterpret_cast<const float*>(indicator+752),view.x) &&
        chartClose(*reinterpret_cast<const float*>(indicator+760),view.z) &&
        chartClose(*reinterpret_cast<const float*>(indicator+896),-view.width*.5) &&
        chartClose(*reinterpret_cast<const float*>(indicator+908),view.width*.5) &&
        chartClose(*reinterpret_cast<const float*>(indicator+900),-view.height*.5) &&
        chartClose(*reinterpret_cast<const float*>(indicator+912),view.height*.5);
}
int updateCharts(lua_State* state) {
    ChartView view{lua.tonumber(state,1),lua.tonumber(state,2),lua.tonumber(state,3),
        lua.tonumber(state,4),lua.tonumber(state,5)};
    double chart=lua.tonumber(state,6);
    if (!std::isfinite(view.x) || !std::isfinite(view.z) || !std::isfinite(view.rotation) ||
        !std::isfinite(view.width) || !std::isfinite(view.height) || !std::isfinite(chart) ||
        std::fabs(view.x)>1e8 || std::fabs(view.z)>1e8 || std::fabs(view.rotation)>7 ||
        view.width<100 || view.width>1e6 || view.height<100 || view.height>1e6 ||
        chart!=std::floor(chart) || chart<2 || chart>6)
        return result(state,false,"invalid chart view; previous native state retained");
    auto* session=static_cast<ChartSession*>(lua.touserdata(state,-10003));
    if (!session) return result(state,false,"missing chart session");
    if (!bindCharts()) return result(state,false,"unsupported CockpitBase build or missing chart exports");
    void* source=nullptr;
    if (!findChartSource(chartAPI.context(),source) || !source)
        return result(state,false,"waiting for isolated generic chart indicator");
    auto* indicator=static_cast<unsigned char*>(source);
    auto* device=*reinterpret_cast<unsigned char**>(indicator+56);
    if (!device || *reinterpret_cast<void**>(device)!=chartAPI.deviceVtable)
        return result(state,false,"chart device identity mismatch");
    // Only the single-record private map and its single page-index entry may be
    // modified. Never modify a normal multi-page/user kneeboard instance.
    auto* begin=*reinterpret_cast<unsigned char**>(device+1040);
    auto* end=*reinterpret_cast<unsigned char**>(device+1048);
    auto* pages=*reinterpret_cast<unsigned char**>(device+1152);
    auto* pagesEnd=*reinterpret_cast<unsigned char**>(device+1160);
    if (!begin || reinterpret_cast<uintptr_t>(end)-reinterpret_cast<uintptr_t>(begin)!=48 ||
        !pages || reinterpret_cast<uintptr_t>(pagesEnd)-reinterpret_cast<uintptr_t>(pages)!=8 ||
        *reinterpret_cast<unsigned int*>(device+1036)!=0 || *reinterpret_cast<int*>(pages+4)!=0 ||
        chartAPI.getMap(device)!=begin || device[1032]!=0)
        return result(state,false,"chart page layout mismatch; no native fields written");
    bool ready=session->pending && session->previousIndicator==source &&
        cameraMatches(indicator,session->previous) &&
        // Retain a one-update image during ordinary track-up turns. Wrap the
        // angle at +/-pi and bound lag to .02 rad (about 1.15 degrees), while
        // still suppressing stale imagery after an abrupt orientation change.
        std::fabs(session->previous.width-view.width)<.01 &&
        std::fabs(session->previous.height-view.height)<.01 &&
        std::fabs(std::remainder(session->previous.rotation-view.rotation,
            6.28318530717958647692))<.02 &&
        std::hypot(session->previous.x-view.x,session->previous.z-view.z)<view.width*.02;
    ChartPage page{view.width*.5,static_cast<unsigned int>(chart),0,view.rotation,view.x,view.z};
    std::memcpy(begin,&page,sizeof(page));
    // These affect ONLY this owned texture producer. The show-pilot-body test
    // otherwise suppresses chart requests when the floating kneeboard is hidden.
    indicator[1744]=1;
    // Generic kneeboard toggle listens globally. Keep this owned producer out
    // of all direct/UI purposes even if that command has been received.
    for (int purpose:{0,1,2}) chartAPI.removePurpose(source,purpose);
    // The camera's vertical span is its horizontal span times this aspect, so it must
    // follow the requested window; a fixed aspect never matches a differently shaped view.
    *reinterpret_cast<float*>(indicator+1124)=.061f;
    *reinterpret_cast<float*>(indicator+1128)=static_cast<float>(.061*view.height/view.width);
    device[1180]=0; // use explicit centre, not the kneeboard follow-aircraft mode
    chartAPI.change(device);
    session->previous=view;session->previousIndicator=source;session->pending=true;
    return result(state,ready,ready ? "generic chart camera aligned" :
        "generic chart configured; waiting for render camera");
}
int chartStatus(lua_State* state) {
    if (!bindCharts()) return result(state,false,"chart adapter not bound to this DCS build");
    void* found=nullptr;
    if (!findChartSource(chartAPI.context(),found) || !found)
        return result(state,false,"chart source marker not found");
    const auto* p=static_cast<const unsigned char*>(found);
    char message[384];
    // The map samples mfd<target>; report the target DCS really assigned.
    std::snprintf(message,sizeof(message),"chart condition=%d camera=(%.1f,%.1f) volume=(%.1f,%.1f,%.1f,%.1f) target=%d",
        *reinterpret_cast<const int*>(p+928),static_cast<double>(*reinterpret_cast<const float*>(p+752)),
        static_cast<double>(*reinterpret_cast<const float*>(p+760)),
        static_cast<double>(*reinterpret_cast<const float*>(p+896)),static_cast<double>(*reinterpret_cast<const float*>(p+908)),
        static_cast<double>(*reinterpret_cast<const float*>(p+900)),static_cast<double>(*reinterpret_cast<const float*>(p+912)),
        *reinterpret_cast<const int*>(p+0x470));
    return result(state,true,message);
}
int collectChartSession(lua_State* state) {
    auto* session=static_cast<ChartSession*>(lua.touserdata(state,1));
    if (session) session->~ChartSession(); // no retained native pointers dereferenced
    return 0;
}
}
extern "C" __declspec(dllexport) int luaopen_f117_charts(lua_State* state) {
    if (!bindLua()) return 0;
    auto* memory=lua.newuserdata(state,sizeof(ChartSession));new(memory) ChartSession();
    lua.newmetatable(state,"F117Displays.Charts.v1");
    lua.pushcclosure(state,collectChartSession,0);lua.setfield(state,-2,"__gc");
    lua.setmetatable(state,-2);
    lua.createtable(state,0,2);
    lua.pushvalue(state,-2);lua.pushcclosure(state,updateCharts,1);lua.setfield(state,-2,"update");
    lua.pushcclosure(state,chartStatus,0);lua.setfield(state,-2,"status");
    return 1;
}
