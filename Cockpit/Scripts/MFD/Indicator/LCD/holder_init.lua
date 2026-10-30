dofile(LockOn_Options.common_script_path.."devices_defs.lua")
dofile(LockOn_Options.common_script_path.."ViewportHandling.lua")
indicator_type=indicator_types.COMMON
purposes={render_purpose.GENERAL,render_purpose.HUD_ONLY_VIEW}
local output=dofile(LockOn_Options.script_path.."MFD/Indicator/render_config.lua")[F117_LCD_KIND]
geometry={HalfWidth=output.half_width,HalfHeight=output.half_height}
page_subsets={[1]=LockOn_Options.script_path.."MFD/Indicator/LCD/"..F117_LCD_KIND.."_page.lua"}
pages={{1}}
init_pageID=1
update_screenspace_diplacement(SelfWidth/SelfHeight,false)
dedicated_viewport_arcade=dedicated_viewport
