-- Generic chart producer owns target 5 (texture mfd5).
-- Target 0 / texture mfd0 stays reserved for IRADS.
local charts=dofile(LockOn_Options.script_path.."MFD/Indicator/Map/Charts/config.lua")
return {enabled=charts.enabled,material="mfd"..tostring(charts.render_target)}
