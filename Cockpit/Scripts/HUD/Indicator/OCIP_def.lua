-- Drawing coordinates are milliradians, converted to the existing FOV page units.
-- Keep the tested physical combiner mask and indicator projection unchanged.
local fov = GetScale()
SetScale(MILLYRADIANS)
local mrad = GetScale()
SetScale(FOV)
OCIP_U = mrad/fov
OCIP_MRAD_SCALE = mrad -- metres per milliradian for native movement controllers
OCIP_FONT_SCALE = mrad
OCIP_READABILITY = dofile(LockOn_Options.script_path.."display_readability.lua")
OCIP_GREEN = {0,255,0,255} -- #00FF00
OCIP_LINE = MakeMaterial(nil,OCIP_GREEN)
OCIP_FONT = MakeFont(OCIP_READABILITY.font,OCIP_GREEN)
