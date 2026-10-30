-- HSD resources; pale violet markings interpreted from the cockpit photograph. Values are physical indicator metres.
dofile(LockOn_Options.common_script_path.."elements_defs.lua")
SetScale(METERS)
HSD_READABILITY = dofile(LockOn_Options.script_path.."display_readability.lua")
HSD_COLOURS = {
    background={7,9,20,255},
    white={255,255,255,255},
    magenta={225,195,255,255},
}
HSD_MATERIALS, HSD_FONTS = {},{}
for name,colour in pairs(HSD_COLOURS) do
    HSD_MATERIALS[name]=MakeMaterial(nil,colour)
    HSD_FONTS[name]=MakeFont(HSD_READABILITY.font,colour)
end
HSD_SD={0.00090,0.00075,0,0}
HSD_SD_SMALL={0.00070,0.00060,0,0}
HSD_SD_VALUE={0.00115,0.00090,0,0}
