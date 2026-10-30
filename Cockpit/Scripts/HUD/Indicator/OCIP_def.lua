-- Drawing coordinates are milliradians, converted to the existing FOV page units.
-- Keep the tested physical combiner mask and indicator projection unchanged.
local fov = GetScale()
SetScale(MILLYRADIANS)
local mrad = GetScale()
SetScale(FOV)
OCIP_U = mrad/fov
OCIP_FONT_SCALE = mrad
OCIP_READABILITY = dofile(LockOn_Options.script_path.."display_readability.lua")
OCIP_GREEN = {80,255,100,255}
OCIP_LINE = MakeMaterial(nil,OCIP_GREEN)
OCIP_FONT = MakeFont(OCIP_READABILITY.font,OCIP_GREEN)
