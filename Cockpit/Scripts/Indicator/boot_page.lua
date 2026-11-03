-- Power-up screen for one display, driven by Systems/Electrical.lua:
-- F117_PWR_<D> 1 = backlight only, 2 = BIT screen; F117_BOOT_STAGE_<D> picks
-- POWER ON / SELF TEST / AUTO CAL / PASS; F117_BOOT_PROGRESS_<D> is 0-100.
-- Illustrative: real F-117 boot screens are not documented in our references.
-- Options: display, title, font, line_material, fill_colour, half_w, half_h,
-- sd (stringdefs base), text_scale, row (one-line layout), parent, level, name.
local strokes=dofile(LockOn_Options.script_path.."display_strokes.lua")
return function(o)
    local D=o.display
    local state,stage,progress="F117_PWR_"..D,"F117_BOOT_STAGE_"..D,"F117_BOOT_PROGRESS_"..D
    local prefix=o.name or ("F117_BOOT_"..D)
    -- Level 0 COMPARE draws everywhere in the viewport: the formats' aperture
    -- stencils are hidden while the display boots.
    local level=o.level or 0
    local count=0
    local function props(e,parent,params,controllers)
        count=count+1
        e.name=prefix.."_"..count
        e.parent_element=parent
        e.collimated=false;e.z_enabled=true
        e.h_clip_relation=h_clip_relations.COMPARE;e.level=level
        e.additive_alpha=false;e.blend_mode=blend_mode.IBM_REGULAR
        e.element_params=params;e.controllers=controllers
        Add(e);return e
    end
    local root=CreateElement "ceSimple"
    props(root,o.parent,{state},{{"parameter_in_range",0,.9,2.1}})
    local w,h=o.half_w,o.half_h
    -- Backlight: the glass lifts from black before anything is drawn.
    local fill=CreateElement "ceMeshPoly"
    fill.primitivetype="triangles"
    fill.vertices={{-w,-h},{w,-h},{w,h},{-w,h}};fill.indices={0,1,2,0,2,3}
    fill.material=MakeMaterial(nil,o.fill_colour or {5,6,8,255})
    props(fill,root.name)
    local bit=CreateElement "ceSimple"
    props(bit,root.name,{state},{{"parameter_in_range",0,1.9,2.1}})
    local function line(points)
        local e=strokes.line(points,1,1);e.material=o.line_material
        return props(e,bit.name)
    end
    local function text(value,x,y,params,controllers,formats,size)
        local e=CreateElement "ceStringSLine"
        e.value=value;e.init_pos={x,y,0};e.material=o.font
        local height=o.sd[1]*GetScale()*o.text_scale*(size or 1)
        e.stringdefs={height,height*.55,height*.10,o.sd[4] or 0}
        strokes.text(e);e.alignment="CenterCenter";e.formats=formats
        return props(e,bit.name,params,controllers)
    end
    -- Test pattern: inset border, corner ticks and a centre cross.
    local bw,bh=w*.92,h*.88
    line({{-bw,-bh},{bw,-bh},{bw,bh},{-bw,bh},{-bw,-bh}})
    local c=math.min(w,h)*.06
    if not o.row then
        line({{-c,0},{c,0}});line({{0,-c},{0,c}})
        for _,s in ipairs({{-1,-1},{1,-1},{1,1},{-1,1}}) do
            local x,y=s[1]*bw*.9,s[2]*bh*.9
            line({{x,y},{x-s[1]*c*1.5,y}});line({{x,y},{x,y-s[2]*c*1.5}})
        end
    end
    local names={"POWER ON","SELF TEST","AUTO CAL","PASS"}
    local tx,ty,sx,sy,px,py
    if o.row then tx,ty,sx,sy,px,py=-w*.6,0,0,0,w*.6,0
    else tx,ty,sx,sy,px,py=0,h*.45,0,-h*.25,0,-h*.5 end
    text(o.title,tx,ty)
    for i,label in ipairs(names) do
        text(label,sx,sy,{stage},{{"parameter_in_range",0,i-.1,i+.1}})
    end
    text("",px,py,{progress,stage},{{"text_using_parameter",0,0},{"parameter_in_range",1,.9,3.1}},{"%3.0f%%"},.8)
end
