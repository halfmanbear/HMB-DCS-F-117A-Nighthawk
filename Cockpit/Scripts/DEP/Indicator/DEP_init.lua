-- Data entry panel (DEP) display, drawn directly on the DEP connector frame.
-- It is not part of the three-screen native bake.
dofile(LockOn_Options.common_script_path.."devices_defs.lua")
dofile(LockOn_Options.common_script_path.."ViewportHandling.lua")

indicator_type = indicator_types.COMMON
purposes = {render_purpose.GENERAL,render_purpose.HUD_ONLY_VIEW}
page_subsets = {[1]=LockOn_Options.script_path.."DEP/Indicator/DEP_base_page.lua"}
pages = {{1}}
init_pageID = 1

-- Native screen-space stroke shader settings.
local stroke_style=dofile(LockOn_Options.script_path.."display_readability.lua")
shaderLineParamsUpdatable=true
shaderLineDefaultThickness=stroke_style.thickness
shaderLineDefaultFuzziness=stroke_style.fuzziness
shaderLineDrawAsWire=false
shaderLineUseSpecularPass=true

update_screenspace_diplacement(SelfWidth/SelfHeight,false)
dedicated_viewport_arcade=dedicated_viewport
