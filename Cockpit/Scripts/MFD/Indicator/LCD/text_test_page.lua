-- Fixed strings and independent line glyphs; no charts or text controllers.
dofile(LockOn_Options.common_script_path.."elements_defs.lua")
SetScale(METERS)
local finish=dofile(LockOn_Options.script_path.."Indicator/native_brightness_page.lua")("F117_IRADS_SOURCE")
local strokes=dofile(LockOn_Options.script_path.."display_strokes.lua")
local font=dofile(LockOn_Options.script_path.."display_font.lua")
local white={255,255,255,255}
local line_material=MakeMaterial(nil,white)
local font_material=MakeFont(font,white)
local root=CreateElement "ceSimple"
root.name="F117_IRADS_SOURCE"
root.element_params={"mainpower"};root.controllers={{"parameter_in_range",0,.9,1.1}}
Add(root)
local function add(e)
    e.parent_element=root.name;e.collimated=false;e.z_enabled=true
    e.h_clip_relation=h_clip_relations.NULL;e.level=0;e.additive_alpha=false
    Add(e)
end
local marker=CreateElement "ceSimple"
marker.name="F117_BAKE_TEST_SOURCE";add(marker)
local background=CreateElement "ceMeshPoly"
background.name="F117_TEXT_TEST_BACKGROUND";background.primitivetype="triangles"
background.vertices={{-.080,.068},{.080,.068},{.080,-.068},{-.080,-.068}}
background.indices={0,1,2,0,2,3};background.material=MakeMaterial(nil,{3,8,10,255})
add(background)
local function text(name,y,size)
    local e=CreateElement "ceStringSLine"
    e.name=name;e.value="TEST 123";e.material=font_material
    e.init_pos={-.065,y,0};e.alignment="LeftCenter";e.stringdefs=size
    strokes.text(e);add(e)
end
-- Three rows: large font text, the same literal drawn as lines, map-size text.
text("F117_TEXT_TEST_LARGE",.044,{.012,.007,.001,0})
local glyphs={
    T={{{0,1},{1,1}},{{.5,1},{.5,0}}},
    E={{{1,1},{0,1},{0,0},{1,0}},{{0,.5},{.8,.5}}},
    S={{{1,1},{0,1},{0,.5},{1,.5},{1,0},{0,0}}},
    ["1"]={{{.2,.8},{.5,1},{.5,0}},{{.1,0},{.9,0}}},
    ["2"]={{{0,1},{1,1},{1,.5},{0,.5},{0,0},{1,0}}},
    ["3"]={{{0,1},{1,1},{1,0},{0,0}},{{0,.5},{1,.5}}},
}
local literal="TEST 123"
for i=1,#literal do
    for j,path in ipairs(glyphs[literal:sub(i,i)] or {}) do
        local points={}
        for k,p in ipairs(path) do points[k]={-.065+(i-1)*.012+p[1]*.008,p[2]*.012} end
        local e=strokes.line(points,1,1)
        e.name="F117_TEXT_TEST_LINE_"..i.."_"..j;e.material=line_material;add(e)
    end
end
text("F117_TEXT_TEST_SMALL",-.034,{.0028,.00165,.00025,0})
local bar=CreateElement "ceMeshPoly"
bar.name="F117_TEXT_TEST_REFERENCE";bar.primitivetype="triangles"
bar.vertices={{-.065,-.052},{.025,-.052},{.025,-.054},{-.065,-.054}}
bar.indices={0,1,2,0,2,3};bar.material=line_material;add(bar)
finish()
