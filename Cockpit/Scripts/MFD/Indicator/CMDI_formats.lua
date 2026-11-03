-- Compose existing formats on a physical CMDI with one native brightness owner.
-- Selection: 0=VSD, 1=grayscale IRADS, 2=MAP, 3=HSD.
return function(side)
    local marker=side=="left" and "F117_VSD_SOURCE" or "F117_HSD_SOURCE"
    local finish=dofile(LockOn_Options.script_path.."Indicator/native_brightness_page.lua")(marker)
    -- Display power from Systems/Electrical.lua: F117_ON_<D> is 1 once operational,
    -- F117_PWR_<D> covers the boot screen as well.
    local display=side=="left" and "CMDI_L" or "CMDI_R"
    local power="F117_ON_"..display
    local owner=CreateElement "ceSimple";owner.name=marker
    owner.element_params={"F117_PWR_"..display};owner.controllers={{"parameter_in_range",0,.9,3.1}};Add(owner)
    local parameter=side=="left" and "F117_LEFT_EO" or "F117_RIGHT_FORMAT"
    local original_add=Add
    local original_create=CreateElement
    F117_CMDI_BUILDING=true
    local function page(kind,id,entry,scale)
        local collected={}
        local function clone(v)
            if type(v)~="table" then return v end
            local c={};for k,x in pairs(v) do c[k]=clone(x) end;return c
        end
        -- DCS element table properties are write-only. Build plain descriptors,
        -- transform those, then assign each property once to a native element.
        CreateElement=function(kind) return {_cmdi_kind=kind} end
        Add=function(e) collected[#collected+1]=clone(e) end
        dofile(LockOn_Options.script_path..entry)
        Add=original_add;CreateElement=original_create
        local prefix="F117_"..side.."_"..kind.."_"
        local gate=CreateElement "ceSimple";gate.name=prefix.."GATE"
        gate.element_params={power,parameter}
        gate.controllers={{"parameter_in_range",0,.9,1.1},{"parameter_in_range",1,id-.1,id+.1}}
        original_add(gate)
        -- All geometry and controller distances use physical metres.
        local function xy(v) if v then for i=1,2 do v[i]=v[i]*scale end end end
        for _,e in ipairs(collected) do
            e.name=prefix..e.name
            e.parent_element=e.parent_element and prefix..e.parent_element or gate.name
            xy(e.init_pos)
            for _,v in ipairs(e.vertices or {}) do xy(v) end
            if e.stringdefs then
                local d={};for i,v in ipairs(e.stringdefs) do d[i]=v*scale end;e.stringdefs=d
            end
            for _,c in ipairs(e.controllers or {}) do
                if c[1]=="move_left_right_using_parameter" or c[1]=="move_up_down_using_parameter" then c[3]=c[3]*scale end
            end
            -- Side format roots are gated here, independent of the original side.
            if kind=="VSD" and e.name==prefix.."F117_VSD_SOURCE" then
                e.element_params={power};e.controllers={{"parameter_in_range",0,.9,1.1}}
            end
            -- Formats written for another display follow this side's power.
            if e.element_params then
                local p={}
                for i,v in ipairs(e.element_params) do
                    p[i]=(v=="mainpower" or (type(v)=="string" and v:match("^F117_ON_"))) and power or v
                end
                e.element_params=p
            end
            if kind=="HSD" or kind=="MAP" or kind=="VSD" then
                for i,p in ipairs(e.element_params or {}) do
                    if p=="F117_RIGHT_DIM_OPACITY" or p=="F117_LEFT_DIM_OPACITY" or p=="F117_MAP_DIM_OPACITY" then
                        e.element_params[i]=side=="left" and "F117_LEFT_DIM_OPACITY" or "F117_RIGHT_DIM_OPACITY"
                    end
                end
            end
            if kind=="MAP" then
                e.level=1;e.z_enabled=true
                if e.name==prefix.."F117_MAP_BACKGROUND" then e.h_clip_relation=h_clip_relations.REWRITE_LEVEL end
            end
            local native=original_create(e._cmdi_kind)
            for k,v in pairs(e) do if k~="_cmdi_kind" then native[k]=v end end
            original_add(native)
        end
    end
    page("VSD",0,"MFD/Indicator/Left/Left_base_format.lua",1)
    if side=="left" then page("EO",1,"MFD/Indicator/Left/Left_eo_page.lua",1) end
    -- The MAP page sizes its chart and aperture to the whole side glass at this scale.
    F117_CMDI_SIDE=side
    local map_scale=dofile(LockOn_Options.script_path.."MFD/Indicator/Map/Map_window.lua").for_side(side).scale
    page("MAP",2,"MFD/Indicator/Map/Map_base_page.lua",map_scale)
    F117_CMDI_SIDE=nil
    page("HSD",3,"MFD/Indicator/Right/Right_base_format.lua",1)
    F117_CMDI_BUILDING=nil
    dofile(LockOn_Options.script_path.."Indicator/boot_page.lua"){
        display=display,title=side=="left" and "CMDI-L" or "CMDI-R",name="F117_"..side.."_BOOT",
        font=VSD_FONTS.green,line_material=VSD_MATERIALS.green,
        half_w=.050,half_h=.046,sd=VSD_SD,text_scale=VSD_READABILITY.mfd_text_scale}
    finish()
end
