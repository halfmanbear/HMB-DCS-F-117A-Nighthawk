-- Default right cockpit display: HSD.
dofile(LockOn_Options.common_script_path.."devices_defs.lua")
dofile(LockOn_Options.common_script_path.."ViewportHandling.lua")


indicator_type = indicator_types.COMMON
purposes = {render_purpose.GENERAL,render_purpose.HUD_ONLY_VIEW}
page_subsets = {[1]=LockOn_Options.script_path.."MFD/Indicator/Right/Right_base_page.lua"}
pages = {{1}}
init_pageID = 1



-- Native screen-space stroke shader settings.
local stroke_style=dofile(LockOn_Options.script_path.."display_readability.lua")
shaderLineParamsUpdatable=true
shaderLineDefaultThickness=stroke_style.thickness
shaderLineDefaultFuzziness=stroke_style.fuzziness
shaderLineDrawAsWire=false
shaderLineUseSpecularPass=true

-- Draw the stroke page directly. BAKE requires a native ccIndicatorBake owner.
update_screenspace_diplacement(SelfWidth/SelfHeight,false)
dedicated_viewport_arcade=dedicated_viewport
