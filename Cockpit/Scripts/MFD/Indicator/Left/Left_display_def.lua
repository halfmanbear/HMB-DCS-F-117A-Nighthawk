-- Colour VSD design resources. Values are physical indicator metres.
dofile(LockOn_Options.common_script_path.."elements_defs.lua")
SetScale(METERS)
VSD_READABILITY = dofile(LockOn_Options.script_path.."display_readability.lua")
VSD_COLOURS = {
    background={7,9,20,255},
    sky={3,16,178,255},       -- #0310B2, supplied by Fraser
    earth={163,140,80,255},   -- #A38C50, supplied by Fraser
    white={255,255,255,255},
    magenta={225,195,255,255},
    red={255,48,48,255},      -- ARS minimum pullout altitude (manual 4-6)
}
VSD_MATERIALS, VSD_FONTS = {},{}
for name,colour in pairs(VSD_COLOURS) do
    VSD_MATERIALS[name]=MakeMaterial(nil,colour)
    VSD_FONTS[name]=MakeFont(VSD_READABILITY.font,colour)
end
VSD_SD={0.00090,0.00075,0,0}
VSD_SD_SMALL={0.00070,0.00060,0,0}
VSD_SD_VALUE={0.00115,0.00090,0,0}
