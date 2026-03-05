dofile(LockOn_Options.script_path .. "command_defs.lua")

local dev = GetSelf()
local update_time_step = 0.02

make_default_activity(update_time_step)

local sensor_data = get_base_data()
local TAILHOOK = get_param_handle("TAILHOOK")
local tailhook = 0

local iCommandPlaneHook = 69

dev:listen_command(69) -- tailhook command

function post_initialize()
    tailhook = 0
end

function SetCommand(command, value)
    if command == 69 then
        tailhook = 0.9 - tailhook
    end
end

function update()
    local tailhook_status = TAILHOOK:get()

    if (hook == 0 and tailhook_status > 0) then
        tailhook_status = tailhook_status - 0.01
        set_aircraft_draw_argument_value(25, tailhook_status)
        TAILHOOK:set(tailhook_status)
    elseif (hook == 0.9 and tailhook_status < 0.9) then
        tailhook_status = tailhook_status + 0.01
        set_aircraft_draw_argument_value(25, tailhook_status)
        TAILHOOK:set(tailhook_status)
    end
end
