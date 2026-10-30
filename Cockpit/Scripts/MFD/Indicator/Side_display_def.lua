-- Shared drawing resources for the two side-display layout starters.
-- No camera/render target is required for these flat symbology pages.
dofile(LockOn_Options.common_script_path.."elements_defs.lua")
SIDE_GREEN = MakeMaterial(nil, {0, 255, 0, 255})
SIDE_FONT = MakeFont(
    {used_DXUnicodeFontData = "FUI/Fonts/font_arial_17"},
    {0, 255, 0, 255}, 18, "side_display_green"
)
SIDE_SD = {0.003, 0.003, 0, 0}
SIDE_LEVEL = 0
