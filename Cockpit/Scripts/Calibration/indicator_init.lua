dofile(LockOn_Options.common_script_path.."devices_defs.lua")
dofile(LockOn_Options.common_script_path.."ViewportHandling.lua")

indicator_type = CALIBRATION_KIND == "hud" and indicator_types.COLLIMATOR or indicator_types.COMMON
purposes = {render_purpose.GENERAL}
if CALIBRATION_KIND == "hud" then
    purposes = {render_purpose.GENERAL, render_purpose.HUD_ONLY_VIEW}
    collimator_default_distance_factor = {0.6,0,0}
end
-- Page scripts have their own Lua environment. Each entry sets its own kind.
page_subsets = {[1]=LockOn_Options.script_path.."Calibration/"..CALIBRATION_KIND.."_page.lua"}
pages = {{1}}
init_pageID = 1
update_screenspace_diplacement(SelfWidth/SelfHeight,false)
dedicated_viewport_arcade = dedicated_viewport
