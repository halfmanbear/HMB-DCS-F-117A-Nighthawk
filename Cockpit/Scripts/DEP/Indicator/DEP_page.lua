-- DEP MAIN MENU: TO 1F-117A-1A Figure FO-3 (PDF 83) and the film frames in
-- docs/reference/CockpitImages/DEP(DATA_ENTRY_PANEL). Metres on the DEP
-- connector frame; the measured glass is 152.7 x 24.5 mm. Two rows of seven
-- equal cells, one per bezel button. Submenus and keypads are not drawn yet.
-- HUD power and brightness also control the DEP (manual 4-4). Native renderer
-- brightness dims the DEP materials; without it F117_DEP_DRAW_BRIGHTNESS falls
-- back to the HUD control as opacity (Systems/NativeBrightness.lua).
local finish_native_brightness=dofile(LockOn_Options.script_path.."Indicator/native_brightness_page.lua")("F117_DEP_SOURCE")
local SD,SM=DEP_SD,DEP_SD_SMALL
local ROOT=CreateElement "ceSimple"
ROOT.name="F117_DEP_SOURCE"
ROOT.element_params={"F117_ON_DEP","F117_DEP_DRAW_BRIGHTNESS"}
ROOT.controllers={{"parameter_in_range",0,0.9,1.1},{"opacity_using_parameter",1}}
Add(ROOT)
local function props(e,parent,level,params,controllers)
    e.name=e.name or create_guid_string()
    e.parent_element=(parent or ROOT).name
    e.collimated=false
    e.z_enabled=true
    e.h_clip_relation=h_clip_relations.COMPARE
    e.level=level or 1
    e.additive_alpha=false
    e.blend_mode=blend_mode.IBM_REGULAR
    e.element_params=params
    e.controllers=controllers
    Add(e)
    return e
end
local function group(pos,parent,params,controllers)
    local e=CreateElement "ceSimple"
    e.init_pos={pos[1],pos[2],0}
    return props(e,parent,1,params,controllers)
end
local function poly(vertices,colour,parent,level,relation)
    local e=CreateElement "ceMeshPoly"
    e.primitivetype="triangles"
    e.material=DEP_MATERIALS[colour or "cell"]
    e.vertices=vertices
    local indices={}
    for i=1,#vertices-2 do for _,j in ipairs({0,i,i+1}) do table.insert(indices,j) end end
    e.indices=indices
    if relation then
        e.name=create_guid_string();e.parent_element=ROOT.name
        e.h_clip_relation=relation;e.level=level;e.isvisible=false
        e.collimated=false;e.z_enabled=true;Add(e);return e
    end
    return props(e,parent,level)
end
local strokes=dofile(LockOn_Options.script_path.."display_strokes.lua")
local function line(points,colour,parent,width)
    local e=strokes.line(points,1,(width or .00020)/.00020)
    e.material=DEP_MATERIALS[colour or "rule"]
    return props(e,parent)
end
local function text(value,x,y,sd,colour,parent)
    local e=CreateElement "ceStringSLine"
    e.value=value;e.init_pos={x,y,0}
    e.material=DEP_FONTS[colour or "legend"]
    local height=sd[1]*GetScale()*DEP_READABILITY.mfd_text_scale
    e.stringdefs={height,height*.55,height*.10,sd[4]}
    strokes.text(e)
    e.alignment="CenterCenter"
    return props(e,parent)
end
local function rect(hw,hh)
    return {{-hw,-hh},{hw,-hh},{hw,hh},{-hw,hh}}
end
-- Centred legend lines: one line at full size, two lines stacked smaller.
local function line_y(count,i) return count==1 and 0 or (i==1 and .0029 or -.0029) end
local function line_sd(count,small) return (small or count>1) and SM or SD end

-- Glass aperture: clip everything to the measured screen.
local GW,GH=.0763,.0122
poly(rect(GW,GH),"glass",nil,1,h_clip_relations.REWRITE_LEVEL)
poly(rect(GW,GH),"glass")

-- Seven equal columns across the glass, two equal rows.
local LEFT,RIGHT,TOP,BOTTOM,INSET=-.0755,.0755,.0117,-.0117,.0004
local EDGES={}
for i=0,7 do EDGES[i+1]=LEFT+(RIGHT-LEFT)*i/7 end
-- A cell shows `label`; while `param` is 1 it shows `engaged` (or `label`) in
-- reverse video. Only F117_AT_ENGAGED has a live source so far.
local MENU={
    {{label={"SPD"},engaged={"CAS"},param="F117_AT_ENGAGED"},
     {label={"TOT"},param="F117_DEP_TOT"},
     {label={"SNAV"},param="F117_DEP_SNAV"},
     {label={"EDIT"},param="F117_DEP_EDIT"},
     {label={"TRK","SEL"},param="F117_DEP_TRK_SEL"},
     {label={"MAP","DP"},param="F117_DEP_MAP_DP"},
     {label={"RCRD"},param="F117_DEP_RCRD"}},
    {{label={"ALT"},param="F117_DEP_ALT"},
     {label={"ILS"},param="F117_DEP_ILS"},
     {label={"VNAV"},param="F117_DEP_VNAV"},
     {label={"HNAV"},param="F117_DEP_HNAV"},
     {label={"ATK"},engaged={"LVL","ATK"},param="F117_DEP_ATK"},
     {label={"STR"},param="F117_DEP_STR"},
     -- Cyclic OFF/TM/SRCH switch (manual 4-42): each half lights on its own.
     {split={{label={"TM"},param="F117_DEP_TM"},{label={"SRCH"},param="F117_DEP_SRCH"}}}},
}
for row,cells in ipairs(MENU) do
    local y0,y1=row==1 and 0 or BOTTOM,row==1 and TOP or 0
    for column,spec in ipairs(cells) do
        local x0,x1=EDGES[column],EDGES[column+1]
        local cell=group({(x0+x1)/2,(y0+y1)/2})
        local parts=spec.split or {spec}
        local hw,hh=(x1-x0)/2-INSET,((y1-y0)/2-INSET)/#parts-(#parts-1)*INSET/2
        for half,part in ipairs(parts) do
            local face=#parts==1 and cell or group({0,(half==1 and 1 or -1)*(y1-y0)/4},cell)
            local small=#parts>1
            poly(rect(hw,hh),"cell",face)
            for i,value in ipairs(part.label) do
                text(value,0,line_y(#part.label,i),line_sd(#part.label,small),"legend",face)
            end
            local on=group({0,0},face,{part.param},{{"parameter_in_range",0,.9,1.1}})
            poly(rect(hw,hh),"engaged",on)
            local engaged=part.engaged or part.label
            for i,value in ipairs(engaged) do
                text(value,0,line_y(#engaged,i),line_sd(#engaged,small),"engaged_legend",on)
            end
        end
    end
end

-- Rules: a heavy row divider and light column dividers, as in the film frames.
line({{LEFT,0},{RIGHT,0}},"rule",nil,.00045)
for i=2,#EDGES-1 do line({{EDGES[i],BOTTOM},{EDGES[i],TOP}},"rule",nil,.00020) end
line({{EDGES[7],BOTTOM/2},{EDGES[8],BOTTOM/2}},"rule",nil,.00020)
dofile(LockOn_Options.script_path.."Indicator/boot_page.lua"){
    display="DEP",title="DEP",name="F117_DEP_BOOT",font=DEP_FONTS.legend,line_material=DEP_MATERIALS.rule,
    half_w=.0760,half_h=.0120,sd=DEP_SD,text_scale=DEP_READABILITY.mfd_text_scale,row=true}
finish_native_brightness()
