-- Indicator/Fonts.lua
-- HUD font definitions for the F-117 Nighthawk.
-- Loaded by Common_Defs.lua; at this point HUD_def.lua has already run so
-- Gripen_Font_green and the fonts[] table are already defined.

-- Alias used by addText / addTextParam as the fallback default font.
fonts["white"] = fonts["FONT_WHITE"] or fonts["F-117_Font_green"]

-- Font object table consumed by the addHUD* wrappers in HUD_def.lua.
newFonts = {
    HUD = "F-117_Font_green",
}
