dofile(LockOn_Options.script_path.."HUD/Indicator/HUD_def.lua")
local add_combiner_mask = dofile(LockOn_Options.script_path.."HUD/Indicator/combiner_mask.lua")
if add_combiner_mask(HUD_DEFAULT_LEVEL) then
    dofile(LockOn_Options.script_path.."HUD/Indicator/HUD_indication_page.lua")
else
    dofile(LockOn_Options.script_path.."HUD/Indicator/HUD_legacy_base_page.lua")
end
