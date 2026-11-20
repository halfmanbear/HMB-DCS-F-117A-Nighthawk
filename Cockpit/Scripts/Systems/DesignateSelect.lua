-- Control-stick DESIGNATE SELECT switch (TO 1F-117A-1A Figure 4-1): decides what the throttle
-- X-Y slew/designate switch drives, and what MARK and sensor update read from.
--   CENTER = IRADS, UP = HUD, LEFT = MAP, DOWN and RIGHT = not used (nothing selected).
-- The supplement is followed where it differs from the base TO (LEFT is MAP, not "left MDI").
--
-- IRADS: TDC input goes to the EFM exactly as before (hotas_commands / f117_commands IDs).
-- HUD and MAP: nothing reaches the EFM; the deflection is integrated here and handed to the
-- cursor owner. The designate switch acts on release, as the manual describes
-- (press shows the gate, release commands).
--
-- The profiles bind stock iCommandPlane_HOTAS_TargetManagementSwitch* commands to the
-- DISPLAYS device. Bind Up/Left/Off to a hat and the switch is momentary; bind them to
-- buttons and it latches, like the detented switch.
local M = {}
M.IRADS, M.HUD, M.MAP, M.NONE = 0, 1, 2, 3

local DEADZONE = 0.05 -- the EFM's own slew deadzone

function M.new(deps)
    deps = deps or {}
    local function dispatch(...)
        if deps.dispatch then return deps.dispatch(...) end
        return dispatch_action(...)
    end
    local state = M.IRADS
    local state_param = get_param_handle("F117_DSS")
    local designate_param = get_param_handle("F117_DSS_DESIGNATE") -- counts HUD / MAP designates
    local held = {up = false, down = false, left = false, right = false}
    local axis_h, axis_v = 0, 0
    local pressed, designates = false, 0
    local depress_logs=0
    local function report_depress(edge)
        if log and log.write and depress_logs<24 then
            depress_logs=depress_logs+1
            local owner=state==M.IRADS and "IRADS" or state==M.HUD and "HUD" or state==M.MAP and "MAP" or "NONE"
            log.write("F117_DESIGNATE",log.INFO,"TDC "..edge.." owner="..owner)
        end
    end

    local EFM_DIRECTION = {
        up = hotas_commands.THROTTLE_DESIGNATOR_CONTROLLER_UP,
        down = hotas_commands.THROTTLE_DESIGNATOR_CONTROLLER_DOWN,
        left = hotas_commands.THROTTLE_DESIGNATOR_CONTROLLER_LEFT,
        right = hotas_commands.THROTTLE_DESIGNATOR_CONTROLLER_RIGHT,
    }
    local DIRECTION_ORDER = {"up", "down", "left", "right"} -- EFM release order
    local DIRECTION_FOR = {
        [native_commands.SELECTER_UP] = "up", [native_commands.SELECTER_DOWN] = "down",
        [native_commands.SELECTER_LEFT] = "left", [native_commands.SELECTER_RIGHT] = "right",
    }
    local STATE_FOR = {
        [native_commands.DSS_OFF] = M.IRADS, [native_commands.DSS_UP] = M.HUD,
        [native_commands.DSS_LEFT] = M.MAP, [native_commands.DSS_DOWN] = M.NONE,
        [native_commands.DSS_RIGHT] = M.NONE,
    }

    local function publish()
        state_param:set(state)
        designate_param:set(designates)
    end

    -- Stop any gimbal motion the EFM still holds from keys or an axis.
    local function release_efm()
        for _, name in ipairs(DIRECTION_ORDER) do dispatch(nil, EFM_DIRECTION[name], 0.0) end
        dispatch(nil, f117_commands.IRADS_SLEW_HORIZONTAL, 0.0)
        dispatch(nil, f117_commands.IRADS_SLEW_VERTICAL, 0.0)
        dispatch(nil, hotas_commands.THROTTLE_DESIGNATOR_CONTROLLER_DEPRESS, 0.0)
    end

    local function clear_demand()
        for name in pairs(held) do held[name] = false end
        axis_h, axis_v, pressed = 0, 0, false
    end

    local function set_state(new_state)
        if new_state == state then return end
        if state == M.IRADS then release_efm() end
        clear_demand()
        local old = state
        state = new_state
        publish()
        if deps.on_change then deps.on_change(state, old) end
    end

    local function clamp(v)
        if type(v) ~= "number" or v ~= v then return 0 end
        return math.max(-1, math.min(1, v))
    end

    local function set_command(command, value)
        local new_state = STATE_FOR[command]
        if new_state ~= nil then set_state(new_state) return true end

        local direction = DIRECTION_FOR[command]
        if direction then
            if state == M.IRADS then dispatch(nil, EFM_DIRECTION[direction], 1.0)
            elseif state ~= M.NONE then held[direction] = true end
            return true
        end
        if command == native_commands.SELECTER_STOP then -- no direction: release all four
            if state == M.IRADS then
                for _, name in ipairs(DIRECTION_ORDER) do dispatch(nil, EFM_DIRECTION[name], 0.0) end
            end
            for name in pairs(held) do held[name] = false end
            return true
        end
        if command == native_commands.TDC_DEPRESS_ON then
            report_depress("press")
            if state == M.IRADS then
                dispatch(nil, hotas_commands.THROTTLE_DESIGNATOR_CONTROLLER_DEPRESS, 1.0)
            elseif state ~= M.NONE then pressed = true end
            return true
        end
        if command == native_commands.TDC_DEPRESS_OFF then
            report_depress("release")
            if state == M.IRADS then
                dispatch(nil, hotas_commands.THROTTLE_DESIGNATOR_CONTROLLER_DEPRESS, 0.0)
            elseif pressed and state ~= M.NONE then
                pressed = false
                designates = designates + 1
                publish()
                if deps.on_designate then deps.on_designate(state) end
            end
            pressed = false
            return true
        end
        if command == irads_axis_commands.HORIZONTAL or command == irads_axis_commands.VERTICAL then
            local horizontal = command == irads_axis_commands.HORIZONTAL
            if state == M.IRADS then
                dispatch(nil, horizontal and f117_commands.IRADS_SLEW_HORIZONTAL or f117_commands.IRADS_SLEW_VERTICAL, value)
            elseif state ~= M.NONE then
                if horizontal then axis_h = clamp(value) else axis_v = clamp(value) end
            end
            return true
        end
        if command == native_commands.SENSOR_RESET then
            -- SCAN RETURN: the EFM undesignates and recentres IRADS (global command). HUD slew is
            -- cancelled and the cursor returns; the map cursor returns to the selected DP.
            if state == M.HUD and deps.hud then deps.hud.recenter() end
            if state == M.MAP and deps.map then deps.map.return_to_dp() end
            return true
        end
        return false
    end

    -- Integrate HUD / MAP cursor demand. dt is the device step (s).
    local function update(dt)
        if state ~= M.HUD and state ~= M.MAP then return end
        local dx = (held.right and 1 or 0) - (held.left and 1 or 0)
        local dy = (held.up and 1 or 0) - (held.down and 1 or 0)
        if math.abs(axis_h) > DEADZONE then dx = axis_h end
        if math.abs(axis_v) > DEADZONE then dy = axis_v end
        if dx == 0 and dy == 0 then return end
        local owner = state == M.HUD and deps.hud or deps.map
        if owner then owner.slew(dx, dy, dt) end
    end

    local function initialize()
        state = M.IRADS
        designates = 0
        clear_demand()
        publish()
    end

    initialize()
    return {
        set_command = set_command,
        update = update,
        initialize = initialize,
        state = function() return state end,
        designates = function() return designates end,
    }
end
return M
