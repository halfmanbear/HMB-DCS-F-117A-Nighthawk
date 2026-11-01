dofile(LockOn_Options.common_script_path.."devices_defs.lua")
dofile(LockOn_Options.common_script_path.."elements_defs.lua")

local readability = dofile(LockOn_Options.script_path.."display_readability.lua")

-- Neutral white sensor-video symbology, matched to the supplied IRADS references.
MFD_WHITE = MakeMaterial(nil, {230, 230, 230, 255})

-- Font for symbology text
MFD_FONT  = MakeFont(
    readability.font,
    {230, 230, 230, 255}
)

MFD_READABILITY = readability
MFD_LEVEL  = 0   -- 0 = default stencil; COMPARE at level 0 renders everywhere in the indicator viewport
MFD_SD     = {0.010, 0.010, 0, 0}
MFD_SD_SM  = {0.006, 0.006, 0, 0}
MFD_SD_XS  = {0.004, 0.004, 0, 0}

-- The overlay is a separate physical indicator. Do not inherit the sensor's
-- FOV scale or resample its render target into this page.
SetScale(METERS)
dofile(LockOn_Options.script_path.."MFD/Indicator/MFD_indication_page.lua")
