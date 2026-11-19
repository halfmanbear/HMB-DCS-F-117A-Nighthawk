// Generic DCS chart adapter. Own avKneeboard/ccKneeboard only: no hooks, vtable replacement
// or aircraft DLLs. Page state is read and checked through DCS's exported kneeboard functions.
// Fields with no accessor are located in the exported kneeboard functions that use them,
// each confirmed by a second function or by reading the written page back.
namespace {
struct ChartPage {double scale;unsigned int chart;unsigned int pad;double rotation,x,z;};
static_assert(sizeof(ChartPage)==40,"native chart-page prefix");
struct ChartView {double x=0,z=0,rotation=0,width=0,height=0;};
// Byte positions inside the chart indicator and its kneeboard device.
struct ChartLayout {
    std::uint32_t device=0,condition=0,pilotBody=0,aspect=0,volume=0;  // indicator
    std::uint32_t map=0,mapView=0,follow=0;                             // device
};
struct ChartAPI {
    void* (*context)()=nullptr;
    void* (*element)(void*,const char*)=nullptr;
    const void* (*getMap)(void*)=nullptr;
    void (*change)(void*)=nullptr;
    void* indicatorVtable=nullptr;
    void* deviceVtable=nullptr;
    void (*removePurpose)(void*,int)=nullptr;
    bool (*hasPurpose)(const void*,int)=nullptr;
    double* (*cameraPoint)(void*,double*)=nullptr;   // indicator; returns x,y,z
    int (*renderTarget)(const void*)=nullptr;
    bool (*useT4)(const void*)=nullptr;
    unsigned (*pageNumber)(const void*)=nullptr;
    unsigned (*pagesCount)(const void*)=nullptr;
    unsigned (*pageId)(const void*)=nullptr;
    bool (*mapRotation)(void*,double&)=nullptr;      // map view
    float* (*mapPoint)(const void*,float*)=nullptr;  // map view; returns x,y,z
    ChartLayout layout;
};
ChartAPI chartAPI;
bool chartsBound=false,chartsAttempted=false;
HMODULE chartsCockpit=nullptr;
struct ChartSession {void* previousIndicator=nullptr;ChartView previous;bool pending=false;};

std::uint32_t codeU32(const unsigned char* c) {std::uint32_t v;std::memcpy(&v,c,4);return v;}
bool memoryOperand(unsigned char modrm) {return (modrm&0xC0)==0x80 && (modrm&7)!=4;} // [base+disp32]
bool fieldOffset(std::uint32_t value) {return value>0 && value<0x1000;}
const unsigned char* exportCode(HMODULE dll,const char* name) {
    return functionCode(reinterpret_cast<const void*>(GetProcAddress(dll,name)));
}
// The one export whose decorated name starts with "?method@class@namespace@@", whatever its
// return type. More than one match (an overload) is refused.
const void* uniqueExport(HMODULE dll,const char* prefix) {
    const auto* base=reinterpret_cast<const unsigned char*>(dll);
    const auto* dos=reinterpret_cast<const IMAGE_DOS_HEADER*>(base);
    if (!dll || dos->e_magic!=IMAGE_DOS_SIGNATURE) return nullptr;
    const auto* nt=reinterpret_cast<const IMAGE_NT_HEADERS*>(base+dos->e_lfanew);
    const IMAGE_DATA_DIRECTORY& entry=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXPORT];
    if (nt->Signature!=IMAGE_NT_SIGNATURE || !entry.VirtualAddress) return nullptr;
    const auto* exports=reinterpret_cast<const IMAGE_EXPORT_DIRECTORY*>(base+entry.VirtualAddress);
    const auto* names=reinterpret_cast<const DWORD*>(base+exports->AddressOfNames);
    const size_t length=std::strlen(prefix);
    const char* found=nullptr;
    for (DWORD i=0;i<exports->NumberOfNames;++i) {
        const char* name=reinterpret_cast<const char*>(base+names[i]);
        if (std::strncmp(name,prefix,length)) continue;
        if (found) return nullptr;
        found=name;
    }
    return found ? reinterpret_cast<const void*>(GetProcAddress(dll,found)) : nullptr;
}
// The first "mov rcx,[rcx+disp]": the indicator's device, loaded to call a device method.
std::uint32_t ownerLoad(const unsigned char* c) {
    for (size_t i=0;i+7<=0x40;++i) {
        if (c[i]!=0x48 || c[i+1]!=0x8B) continue;
        if (c[i+2]==0x49) return c[i+3];
        if (c[i+2]==0x89) return codeU32(c+i+3);
    }
    return 0;
}
// get_screen_condition stores update_camera's result: "call update_camera; mov [base+disp32],eax".
std::uint32_t conditionStore(const unsigned char* c,const unsigned char* updateCamera,const void* updateEntry) {
    for (size_t i=0;i+11<=0x100;++i) {
        if (c[i]!=0xE8) continue;
        std::int32_t call;std::memcpy(&call,c+i+1,4);
        const unsigned char* target=c+i+5+call; // compared only, never read
        if ((target==updateCamera || target==updateEntry) && c[i+5]==0x89 && memoryOperand(c[i+6]) && !(c[i+6]&0x38))
            return codeU32(c+i+7);
    }
    return 0;
}
// "cmp byte ptr [base+disp32],0" in the first instructions (or anywhere in length).
std::uint32_t firstByteTest(const unsigned char* c,size_t length) {
    for (size_t i=0;i+7<=length;++i)
        if (c[i]==0x80 && (c[i+1]&0xF8)==0xB8 && (c[i+1]&7)!=4 && c[i+6]==0) return codeU32(c+i+2);
    return 0;
}
// Scalar SSE "F3 [REX] 0F op modrm disp32" with a [base+disp32] operand; returns its length.
size_t scalarOp(const unsigned char* c,unsigned char op,unsigned char& rex,unsigned char& modrm,std::uint32_t& disp) {
    if (c[0]!=0xF3) return 0;
    size_t at=1;rex=0;
    if ((c[at]&0xF0)==0x40) rex=c[at++];
    if (c[at]!=0x0F || c[at+1]!=op || !memoryOperand(c[at+2])) return 0;
    modrm=c[at+2];disp=codeU32(c+at+3);
    return at+7;
}
// update_camera divides the vertical aspect field by the horizontal one before every camera
// build: "movss xmmN,[base+V]" then "divss xmmN,[base+V-4]". All such pairs must agree.
std::uint32_t aspectPair(const unsigned char* c,size_t length) {
    std::uint32_t found=0;int count=0;
    for (size_t i=0;i+24<=length;++i) {
        unsigned char rex,modrm;std::uint32_t vertical;
        const size_t size=scalarOp(c+i,0x10,rex,modrm,vertical);
        if (!size) continue;
        for (size_t j=i+size;j<i+size+16;++j) {
            unsigned char rex2,modrm2;std::uint32_t horizontal;
            if (scalarOp(c+j,0x5E,rex2,modrm2,horizontal) && rex2==rex && modrm2==modrm && horizontal+4==vertical) {
                if (found && found!=horizontal) return 0;
                found=horizontal;++count;break;
            }
        }
    }
    return count>=2 && fieldOffset(found) && found%4==0 ? found : 0;
}
// The fallback camera in update_camera writes its orthographic volume as left=-1, bottom,
// near, right=+1, top. Left takes -1.0 at L and right +1.0 at L+12 from the same base;
// bottom (L+4) and top (L+16) are stored from registers.
std::uint32_t volumeStores(const unsigned char* c,size_t length) {
    for (size_t i=0;i+10<=length;++i) {
        if (c[i]!=0xC7 || !memoryOperand(c[i+1]) || (c[i+1]&0x38) || codeU32(c+i+6)!=0xBF800000u) continue;
        const std::uint32_t left=codeU32(c+i+2);
        bool right=false,bottom=false,top=false;
        for (size_t j=0;j+10<=length;++j) {
            if (c[j]==c[i] && c[j+1]==c[i+1] && codeU32(c+j+2)==left+12 && codeU32(c+j+6)==0x3F800000u) right=true;
            unsigned char rex,modrm;std::uint32_t disp;
            if (scalarOp(c+j,0x11,rex,modrm,disp) && !(rex&1) && (modrm&7)==(c[i+1]&7)) {
                bottom|=disp==left+4;top|=disp==left+16;
            }
        }
        return right && bottom && top && fieldOffset(left) && left%4==0 ? left : 0;
    }
    return 0;
}
bool byteStore(const unsigned char* c,size_t length,std::uint32_t disp) { // "mov byte [base+disp32],r8"
    for (size_t i=0;i+6<=length;++i)
        if (c[i]==0x88 && memoryOperand(c[i+1]) && codeU32(c+i+2)==disp) return true;
    return false;
}
// A [base+disp] operand without index or RIP; returns its length after the ModRM byte's
// position, or 0.
size_t baseOperand(const unsigned char* modrm,unsigned char rex,unsigned& base,std::int32_t& disp) {
    const unsigned mod=*modrm>>6,rm=*modrm&7;
    if (mod==3 || rm==4 || (mod==0 && rm==5)) return 0;
    base=rm|((rex&1u)<<3);
    if (mod==0) {disp=0;return 1;}
    if (mod==1) {disp=static_cast<std::int8_t>(modrm[1]);return 2;}
    std::memcpy(&disp,modrm+1,4);return 5;
}
// find_available_coverage reads a chart record's half-width and centre as doubles and stores
// the chart level it settles on as a 32-bit value, all from one base register. They must sit
// where ChartPage puts them. Its once-only coverage flag must lie past the bytes written.
bool chartRecordConfirmed(const unsigned char* c,size_t length) {
    struct Use {unsigned base;std::int32_t disp;};
    std::vector<Use> doubles,levels;
    bool flagClear=false;
    for (size_t i=0;i+8<=length;++i) {
        size_t at=i;unsigned char rex=0;unsigned base;std::int32_t disp;
        if (c[at]==0x80 && (c[at+1]&0xF8)==0x78 && (c[at+1]&7)!=4 && c[at+3]==0) { // cmp byte [base+disp8],0
            const auto flag=static_cast<std::int8_t>(c[at+2]);
            flagClear|=flag>=static_cast<int>(sizeof(ChartPage)) && flag<48;
            continue;
        }
        const bool sse=c[at]==0xF2;
        if (sse) ++at;
        if ((c[at]&0xF0)==0x40) rex=c[at++];
        if (sse && c[at]==0x0F && c[at+1]==0x10 && baseOperand(c+at+2,rex,base,disp)) doubles.push_back({base,disp});
        else if (!sse && !(rex&8) && c[at]==0x89 && baseOperand(c+at+1,rex,base,disp)) levels.push_back({base,disp});
    }
    const auto has=[](const std::vector<Use>& uses,unsigned base,size_t disp) {
        return std::any_of(uses.begin(),uses.end(),[&](const Use& u){return u.base==base && u.disp==static_cast<std::int32_t>(disp);});
    };
    for (const Use& u:doubles)
        if (u.disp==static_cast<std::int32_t>(offsetof(ChartPage,scale)) && has(doubles,u.base,offsetof(ChartPage,x)) &&
            has(doubles,u.base,offsetof(ChartPage,z)) && has(levels,u.base,offsetof(ChartPage,chart)))
            return flagClear;
    return false;
}
bool bindChartLayout(HMODULE dll,ChartLayout& out) {
    const unsigned char* isMap=exportCode(dll,"?is_map_page@ccKneeboard@cockpit@@IEAA_NXZ");
    const void* updateEntry=uniqueExport(dll,"?update_camera@ccKneeboard@cockpit@@");
    const unsigned char* update=functionCode(updateEntry);
    const unsigned char* condition=functionCode(uniqueExport(dll,"?get_screen_condition@ccKneeboard@cockpit@@"));
    const unsigned char* getMap=exportCode(dll,"?get_map@avKneeboard@cockpit@@QEBAAEBUkneeboard_map_page@2@XZ");
    const unsigned char* rotation=exportCode(dll,"?get_map_rotation@avKneeboard@cockpit@@UEAA_NAEAN@Z");
    const unsigned char* point=exportCode(dll,"?get_camera_point@avKneeboard@cockpit@@MEBA?AVVec3f@osg@@XZ");
    const unsigned char* build=exportCode(dll,"??0avKneeboard@cockpit@@QEAA@XZ");
    const unsigned char* coverage=functionCode(uniqueExport(dll,"?find_available_coverage@avKneeboard@cockpit@@"));
    if (!isMap || !update || !condition || !getMap || !rotation || !point || !build || !coverage) return false;
    // The chart record: scale, level and centre where ChartPage expects them. The rotation and
    // centre are confirmed again by reading each written page back.
    if (!chartRecordConfirmed(coverage,0x120)) return false;
    ChartLayout layout;
    // Indicator: its device is loaded the same way by two kneeboard functions.
    layout.device=ownerLoad(isMap);
    if (!plausibleOffset(layout.device) || ownerLoad(update)!=layout.device) return false;
    layout.condition=conditionStore(condition,update,updateEntry);
    // get_screen_condition first tests the show-pilot-body override, then the view.
    layout.pilotBody=firstByteTest(condition,0x10);
    layout.aspect=aspectPair(update,0x300);
    layout.volume=volumeStores(update,0x300);
    if (!fieldOffset(layout.condition) || layout.condition%4 || !fieldOffset(layout.pilotBody) ||
        !layout.aspect || !layout.volume) return false;
    // Device: the map list, as read by get_map and, through the map view, get_map_rotation.
    // Their difference is the map view's position, which update_camera also passes.
    layout.map=vectorLoadOffset(getMap,0x40);
    const std::uint32_t viewMap=vectorLoadOffset(rotation,0x40);
    if (!layout.map || !viewMap || viewMap>=layout.map) return false;
    layout.mapView=layout.map-viewMap;
    if (firstArgumentOffset(update,0x80)!=layout.mapView) return false;
    // The follow-aircraft flag is the map view's first byte test in get_camera_point; the
    // device constructor must clear the same byte.
    const std::uint32_t follow=firstByteTest(point,0x100);
    if (!fieldOffset(follow)) return false;
    layout.follow=layout.mapView+follow;
    if (!byteStore(build,0x200,layout.follow)) return false;
    out=layout;
    return true;
}
bool bindCharts() {
    // This DLL can be pinned across missions; never keep pointers into a replaced module.
    HMODULE dll=GetModuleHandleW(L"CockpitBase.dll");
    if (dll!=chartsCockpit) {chartsCockpit=dll;chartsBound=false;chartsAttempted=false;}
    if (chartsBound) return true;
    if (chartsAttempted) return false;
    if (!dll) return false;
    chartsAttempted=true;
    ChartAPI api;
    if (!bindContextLayout(dll) || !bindChartLayout(dll,api.layout)) return false;
#define CHART_BIND(field,name) if (!symbol(dll,name,api.field)) return false
    CHART_BIND(context,"?binding_context@cockpit@@YAPEAVccCockpitContext@1@XZ");
    CHART_BIND(element,"?get_element_on_current_page@ccIndicator@cockpit@@UEAAPEAVElement@2@PEBD@Z");
    CHART_BIND(getMap,"?get_map@avKneeboard@cockpit@@QEBAAEBUkneeboard_map_page@2@XZ");
    CHART_BIND(change,"?update_change_counter@avKneeboard@cockpit@@IEAAXXZ");
    CHART_BIND(indicatorVtable,"??_7ccKneeboard@cockpit@@6BccContextRelatedObject@1@@");
    CHART_BIND(deviceVtable,"??_7avKneeboard@cockpit@@6BccContextRelatedObject@1@@");
    CHART_BIND(removePurpose,"?remove_purpose@ccIndicator@cockpit@@UEAAXH@Z");
    CHART_BIND(hasPurpose,"?has_a_purpose_assigned@ccIndicator@cockpit@@QEBA_NH@Z");
    CHART_BIND(cameraPoint,"?get_camera_point@ccKneeboard@cockpit@@UEAA?AVVec3d@osg@@XZ");
    CHART_BIND(renderTarget,"?get_render_target@ccIndicator@cockpit@@UEBA?BHXZ");
    CHART_BIND(useT4,"?use_T4_render@avKneeboard@cockpit@@QEBA_NXZ");
    CHART_BIND(pageNumber,"?get_page_number@avKneeboard@cockpit@@QEBAIXZ");
    CHART_BIND(pagesCount,"?get_pages_count@avKneeboard@cockpit@@QEBAIXZ");
    CHART_BIND(pageId,"?get_page_id@avKneeboard@cockpit@@QEBAIXZ");
    CHART_BIND(mapRotation,"?get_map_rotation@avKneeboard@cockpit@@UEAA_NAEAN@Z");
    CHART_BIND(mapPoint,"?get_camera_point@avKneeboard@cockpit@@MEBA?AVVec3f@osg@@XZ");
#undef CHART_BIND
    chartAPI=api;chartsBound=true;return true;
}
bool findChartSource(void* root,void*& found) {
    auto visit=[&found](void*,void* candidate,int) {
        if (*static_cast<void**>(candidate)!=chartAPI.indicatorVtable) return true;
        if (chartAPI.element(candidate,"F117_CHART_PRODUCER")) {
            if (found && found!=candidate) return false;
            found=candidate;
        }
        return true;
    };
    return walkContexts(root,visit);
}
template<class T> T& field(void* object,std::uint32_t offset) {
    return *reinterpret_cast<T*>(static_cast<unsigned char*>(object)+offset);
}
bool chartClose(double a,double b) {return std::isfinite(a) && std::fabs(a-b)<1.;}
// left, bottom, near, right, top
float volumeAt(void* indicator,int index) {return field<float>(indicator,chartAPI.layout.volume+4*index);}
bool cameraMatches(void* indicator,const ChartView& view) {
    // The native camera update stores the camera position and the copied
    // orthographic volume on the indicator; compare them with the requested view.
    double camera[3]={};
    chartAPI.cameraPoint(indicator,camera);
    return field<int>(indicator,chartAPI.layout.condition)==9 &&
        chartClose(camera[0],view.x) && chartClose(camera[2],view.z) &&
        chartClose(volumeAt(indicator,0),-view.width*.5) && chartClose(volumeAt(indicator,3),view.width*.5) &&
        chartClose(volumeAt(indicator,1),-view.height*.5) && chartClose(volumeAt(indicator,4),view.height*.5);
}
// The map view reads the page back: rotation through get_map_rotation and the centre through
// get_camera_point, which uses the page centre only while follow-aircraft is off.
bool pageReadsBack(void* device,const ChartPage& page) {
    void* view=static_cast<unsigned char*>(device)+chartAPI.layout.mapView;
    double rotation=std::nan("");
    float centre[3]={NAN,NAN,NAN};
    if (!chartAPI.mapRotation(view,rotation)) return false;
    chartAPI.mapPoint(view,centre);
    const auto same=[](double a,double b){return std::isfinite(a) && std::fabs(a-b)<=(std::max)(1.,std::fabs(b)*1e-6);};
    return std::fabs(rotation-page.rotation)<1e-9 && same(centre[0],page.x) && same(centre[2],page.z);
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
    int purposes[4]; // general, HUD-only view, screenspace inside cockpit, bake
    if (!readPurposes(state,7,purposes,4))
        return result(state,false,"DCS render purposes not supplied; previous native state retained");
    auto* session=static_cast<ChartSession*>(lua.touserdata(state,-10003));
    if (!session) return result(state,false,"missing chart session");
    if (!bindCharts()) return result(state,false,"chart exports or kneeboard layout not confirmed");
    void* source=nullptr;
    if (!findChartSource(chartAPI.context(),source) || !source)
        return result(state,false,"waiting for isolated generic chart indicator");
    const ChartLayout& layout=chartAPI.layout;
    void* device=field<void*>(source,layout.device);
    if (!device || *static_cast<void**>(device)!=chartAPI.deviceVtable)
        return result(state,false,"chart device identity mismatch");
    // Only the single-record private map and its single page-index entry may be
    // modified. Never modify a normal multi-page/user kneeboard instance.
    auto* begin=field<unsigned char*>(device,layout.map);
    auto* end=field<unsigned char*>(device,layout.map+8);
    if (!begin || reinterpret_cast<uintptr_t>(end)-reinterpret_cast<uintptr_t>(begin)!=48 ||
        chartAPI.pagesCount(device)!=1 || chartAPI.pageNumber(device)!=0 || chartAPI.pageId(device)!=0 ||
        chartAPI.getMap(device)!=begin || !chartAPI.useT4(device))
        return result(state,false,"chart page layout mismatch; no native fields written");
    // The producer page declares only the bake purpose, from the same DCS table. The generic
    // kneeboard toggle listens globally, so keep it out of every direct and UI purpose.
    if (!chartAPI.hasPurpose(source,purposes[3]))
        return result(state,false,"chart producer purpose does not match DCS render purposes; no native fields written");
    for (int i=0;i<3;++i) chartAPI.removePurpose(source,purposes[i]);
    for (int i=0;i<3;++i) if (chartAPI.hasPurpose(source,purposes[i]))
        return result(state,false,"chart producer purpose removal not confirmed; no page written");
    bool ready=session->pending && session->previousIndicator==source &&
        cameraMatches(source,session->previous) &&
        // Retain a one-update image during ordinary track-up turns. Wrap the
        // angle at +/-pi and bound lag to .02 rad (about 1.15 degrees), while
        // still suppressing stale imagery after an abrupt orientation change.
        std::fabs(session->previous.width-view.width)<.01 &&
        std::fabs(session->previous.height-view.height)<.01 &&
        std::fabs(std::remainder(session->previous.rotation-view.rotation,
            6.28318530717958647692))<.02 &&
        std::hypot(session->previous.x-view.x,session->previous.z-view.z)<view.width*.02;
    ChartPage page{view.width*.5,static_cast<unsigned int>(chart),0,view.rotation,view.x,view.z};
    ChartPage before;std::memcpy(&before,begin,sizeof(before));
    const unsigned char followBefore=field<unsigned char>(device,layout.follow);
    std::memcpy(begin,&page,sizeof(page));
    field<unsigned char>(device,layout.follow)=0; // use explicit centre, not follow-aircraft
    if (!pageReadsBack(device,page)) {
        std::memcpy(begin,&before,sizeof(before));
        field<unsigned char>(device,layout.follow)=followBefore;
        session->pending=false;
        return result(state,false,"chart page not confirmed by read-back; previous page restored");
    }
    // These affect ONLY this owned texture producer. The show-pilot-body test
    // otherwise suppresses chart requests when the floating kneeboard is hidden.
    field<unsigned char>(source,layout.pilotBody)=1;
    // The camera's vertical span is its horizontal span times this aspect, so it must
    // follow the requested window; a fixed aspect never matches a differently shaped view.
    field<float>(source,layout.aspect)=.061f;
    field<float>(source,layout.aspect+4)=static_cast<float>(.061*view.height/view.width);
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
    double camera[3]={};
    chartAPI.cameraPoint(found,camera);
    char message[384];
    // The map samples mfd<target>; report the target DCS really assigned.
    std::snprintf(message,sizeof(message),"chart condition=%d camera=(%.1f,%.1f) volume=(%.1f,%.1f,%.1f,%.1f) target=%d",
        field<int>(found,chartAPI.layout.condition),camera[0],camera[2],
        static_cast<double>(volumeAt(found,0)),static_cast<double>(volumeAt(found,3)),
        static_cast<double>(volumeAt(found,1)),static_cast<double>(volumeAt(found,4)),
        chartAPI.renderTarget(found));
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
