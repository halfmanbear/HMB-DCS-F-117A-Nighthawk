dofile(LockOn_Options.common_script_path.."devices_defs.lua")
dofile(LockOn_Options.common_script_path.."elements_defs.lua")

local readability = dofile(LockOn_Options.script_path.."display_readability.lua")

-- Phosphor green, matching the real F-117 DLIR display colour
MFD_GREEN = MakeMaterial(nil, {0, 255, 0, 255})

-- Font for symbology text
MFD_FONT  = MakeFont(
    readability.font,
    {0, 255, 0, 255}
)

MFD_READABILITY = readability
MFD_LEVEL  = 0   -- 0 = default stencil; COMPARE at level 0 renders everywhere in the indicator viewport
MFD_SD     = {0.010, 0.010, 0, 0}
MFD_SD_SM  = {0.006, 0.006, 0, 0}
MFD_SD_XS  = {0.004, 0.004, 0, 0}

-- Only the baked source includes video. Direct fallback keeps the separate
-- camera indicator underneath this overlay, preserving its established mapping.
F117_COMPOSITE_PAGE=true
dofile(LockOn_Options.script_path.."MFD/Indicator/DLIR_Camera_page.lua")
F117_COMPOSITE_PAGE=nil
dofile(LockOn_Options.script_path.."MFD/Indicator/MFD_indication_page.lua")
