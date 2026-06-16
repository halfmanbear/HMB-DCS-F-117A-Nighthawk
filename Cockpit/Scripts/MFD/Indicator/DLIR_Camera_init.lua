dofile(LockOn_Options.common_script_path.."devices_defs.lua")
dofile(LockOn_Options.common_script_path.."ViewportHandling.lua")

-- COMMON renders the 3D camera scene via avTVSensor into an off-screen render target.
-- The sensor's camera position, FOV, and gimbal are controlled by the avTVSensor device
-- (driven by the IRADS sensor database entry), not by this Lua file.
indicator_type = indicator_types.COMMON

-- Page that renders the camera's off-screen image onto the MFD surface.
page_subsets = {LockOn_Options.script_path.."MFD/Indicator/DLIR_Camera_page.lua"}
pages        = {{1}}
init_pageID  = 1

-- Register this indicator as render_targets[0].
-- set_render_materials() reads this value and calls assign_as_render_target_source(self, 0),
-- which wires the avTVSensor camera feed into the render pipeline.
-- The Graphics material created is "render_target_1" (sprintf("render_target_%d", 0+1)).
render_target = 0

-- Route the COMMON camera viewport to this indicator's screen-space area.
update_screenspace_diplacement(SelfWidth / SelfHeight, false)
dedicated_viewport_arcade = dedicated_viewport
