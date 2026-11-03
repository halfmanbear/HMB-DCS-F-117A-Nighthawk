-- DEP design resources. Values are physical indicator metres.
dofile(LockOn_Options.common_script_path.."elements_defs.lua")
SetScale(METERS)
DEP_READABILITY = dofile(LockOn_Options.script_path.."display_readability.lua")
-- Manual 4-29: white characters on a dark background; an engaged mode is shown
-- in reverse video. The film reference shows slate cells and pale yellow engaged cells.
DEP_COLOURS = {
    glass={4,5,10,255},
    cell={38,48,86,255},
    legend={228,230,222,255},
    engaged={214,210,132,255},
    engaged_legend={22,24,18,255},
    rule={205,208,205,255},
}
DEP_MATERIALS, DEP_FONTS = {},{}
for name,colour in pairs(DEP_COLOURS) do
    DEP_MATERIALS[name]=MakeMaterial(nil,colour)
    DEP_FONTS[name]=MakeFont(DEP_READABILITY.font,colour)
end
-- Glyph heights after mfd_text_scale: 4.2 mm one-line, 3.2 mm two-line legends.
DEP_SD={0.00105,0.00085,0,0}
DEP_SD_SMALL={0.00080,0.00065,0,0}
