-- DCS's own render purpose numbers (render_purpose in devices_defs.lua), or nil.
-- Native display code takes these rather than fixed values.
if not render_purpose and LockOn_Options and LockOn_Options.common_script_path then
    pcall(dofile,LockOn_Options.common_script_path.."devices_defs.lua")
end
return type(render_purpose)=="table" and render_purpose or nil
