dofile(LockOn_Options.common_script_path.."elements_defs.lua")
SetScale(METERS)
MAP_READABILITY=dofile(LockOn_Options.script_path.."display_readability.lua")
-- Symbology is pale amber, as in the cockpit video frames, so it reads over the
-- chart without dimming it.
MAP_COLOURS={background={3,8,10,255},symbol={255,214,120,255},
    grid={20,41,43,255},cyan={80,220,225,255},yellow={235,205,95,255}}
MAP_MATERIALS,MAP_FONTS={},{}
for name,colour in pairs(MAP_COLOURS) do
    MAP_MATERIALS[name]=MakeMaterial(nil,colour)
    MAP_FONTS[name]=MakeFont(MAP_READABILITY.font,colour)
end
-- The page is drawn at about .58 on the CMDIs; the gain keeps its text as legible as the
-- VSD/HSD text instead of shrinking with it.
MAP_TEXT_GAIN=1.4
-- Stroke weights: the page is drawn at about .58 on the CMDIs, and thin strokes
-- vanish against a bright chart.
MAP_LINE_WEIGHT=2.2
MAP_TEXT_WEIGHT=1.8
MAP_LEG_WIDTH=.0004 -- route and steering legs, metres
MAP_SD={.0028*MAP_TEXT_GAIN,.00165*MAP_TEXT_GAIN,.00025*MAP_TEXT_GAIN,0}
MAP_SMALL={.0021*MAP_TEXT_GAIN,.00125*MAP_TEXT_GAIN,.00018*MAP_TEXT_GAIN,0}
dofile(LockOn_Options.script_path.."MFD/Indicator/Map/Map_page.lua")
