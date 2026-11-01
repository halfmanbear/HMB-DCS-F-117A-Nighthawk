dofile(LockOn_Options.common_script_path.."devices_defs.lua")
dofile(LockOn_Options.common_script_path.."ViewportHandling.lua")


indicator_type = indicator_types.COMMON
purposes = {render_purpose.GENERAL,render_purpose.HUD_ONLY_VIEW}

BASE = 1

page_subsets = {
    [BASE] = LockOn_Options.script_path.."MFD/Indicator/Map/Map_base_page.lua",
}
local display_config=dofile(LockOn_Options.script_path.."MFD/Indicator/render_config.lua")
if display_config.bake_test and not display_config.enabled then
    if display_config.bake_test_source=="text" then
        page_subsets[BASE]=LockOn_Options.script_path.."MFD/Indicator/LCD/text_test_page.lua"
    elseif display_config.bake_test_source~="map" then
        page_subsets[BASE]=LockOn_Options.script_path.."MFD/Indicator/LCD/bake_test_page.lua"
    end
end

pages = {
    { BASE, },
}

init_pageID = 1




-- Native screen-space stroke shader settings.
local stroke_style=dofile(LockOn_Options.script_path.."display_readability.lua")
shaderLineParamsUpdatable=true
shaderLineDefaultThickness=stroke_style.thickness
shaderLineDefaultFuzziness=stroke_style.fuzziness
shaderLineDrawAsWire=false
shaderLineUseSpecularPass=true
if display_config.bake_test and not display_config.enabled and
    (display_config.bake_test_source=="map" or display_config.bake_test_source=="text") then
    shaderLineUseSpecularPass=display_config.bake_test_specular~=false
end

-- Draw the stroke page directly. BAKE requires a native ccIndicatorBake owner.
update_screenspace_diplacement(SelfWidth/SelfHeight,false)
dedicated_viewport_arcade=dedicated_viewport
