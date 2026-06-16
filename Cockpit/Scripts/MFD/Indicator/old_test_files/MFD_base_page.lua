dofile(LockOn_Options.common_script_path.."devices_defs.lua")
dofile(LockOn_Options.common_script_path.."elements_defs.lua")

-- Phosphor green, matching the real F-117 DLIR display colour
MFD_GREEN = MakeMaterial(nil, {0, 255, 0, 255})

-- Font for symbology text
MFD_FONT  = MakeFont(
    {used_DXUnicodeFontData = "FUI/Fonts/font_arial_17"},
    {0, 255, 0, 255},
    50,
    "mfd_font_green"
)

MFD_LEVEL  = 0   -- 0 = default stencil; COMPARE at level 0 renders everywhere in the flat NOTYPE viewport
MFD_SD     = {0.040, 0.040, 0, 0}   -- normal label size  -- tune these values
MFD_SD_SM  = {0.028, 0.028, 0, 0}   -- small corner text  -- if text appears too large/small

dofile(LockOn_Options.script_path.."MFD/Indicator/MFD_indication_page.lua")
