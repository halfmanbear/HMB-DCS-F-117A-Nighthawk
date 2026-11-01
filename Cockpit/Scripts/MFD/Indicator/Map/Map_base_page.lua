dofile(LockOn_Options.common_script_path.."elements_defs.lua")
SetScale(METERS)
MAP_READABILITY=dofile(LockOn_Options.script_path.."display_readability.lua")
MAP_COLOURS={background={3,8,10,255},white={220,232,220,255},
    grid={20,41,43,255},cyan={80,220,225,255},yellow={235,205,95,255}}
MAP_MATERIALS,MAP_FONTS={},{}
for name,colour in pairs(MAP_COLOURS) do
    MAP_MATERIALS[name]=MakeMaterial(nil,colour)
    MAP_FONTS[name]=MakeFont(MAP_READABILITY.font,colour)
end
MAP_SD={.0028,.00165,.00025,0}
MAP_SMALL={.0021,.00125,.00018,0}
dofile(LockOn_Options.script_path.."MFD/Indicator/Map/Map_page.lua")
