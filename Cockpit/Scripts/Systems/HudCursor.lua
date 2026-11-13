-- Free HUD cursor, driven by the throttle X-Y slew switch while the Designate Select switch is on
-- HUD (TO 1F-117A-1 4-5; supplement 1A). Position is optical-plane tangent coordinates
-- (right/forward, up/forward) in the aircraft frame, the same space as HUD/Device/OCIP_data.lua.
-- OCIP_data.lua draws it with the existing HUD/IRADS cursor symbol while F117_DSS is HUD.
--
-- Ground point (manual): a cursor on or below the horizon is given the elevation of the current
-- destination (or the selected offset aim point). Above the horizon there are no coordinates.
local M = {}

local TFOV_HALF_DEG = 10          -- 20 degree total field of view, as in OCIP_data.lua
local SLEW_DEG_PER_S = 8          -- full deflection
local HORIZON_EPS = 1e-4          -- direction "up" component that still counts as below the horizon

local function finite(v) return type(v) == "number" and v == v and math.abs(v) < 1e12 end

-- Inverse of OCIP_data.lua body(): optical-plane (x, y) to a world direction (north, up, east).
-- World axes are DCS local: x north, y up, z east. getHeading() is counter-clockwise.
function M.world_direction(x, y, heading, pitch, roll)
    local h = -heading
    local ch, sh, cp, sp = math.cos(h), math.sin(h), math.cos(pitch), math.sin(pitch)
    local cr, sr = math.cos(roll), math.sin(roll)
    local f, r, up = 1, x, y
    local level_right = r * cr + up * sr
    local level_up = up * cr - r * sr
    local u = level_up * cp + f * sp
    local along = f * cp - level_up * sp
    local n = along * ch - level_right * sh
    local e = along * sh + level_right * ch
    local length = math.sqrt(n * n + u * u + e * e)
    return n / length, u / length, e / length
end

-- Intersect the cursor ray with the horizontal plane at the reference elevation.
-- pos = {x north, y up, z east}; returns {north, elevation, east} or nil and a reason.
function M.ground_point(x, y, heading, pitch, roll, pos, reference_elevation)
    if not (finite(x) and finite(y) and finite(heading) and finite(pitch) and finite(roll)
        and finite(pos[1]) and finite(pos[2]) and finite(pos[3]) and finite(reference_elevation)) then
        return nil, "invalid input"
    end
    local n, u, e = M.world_direction(x, y, heading, pitch, roll)
    if u >= -HORIZON_EPS then return nil, "above horizon" end
    local t = (reference_elevation - pos[2]) / u
    if not finite(t) or t <= 0 then return nil, "reference above aircraft" end
    return {pos[1] + t * n, reference_elevation, pos[3] + t * e}
end

-- deps.attitude: base-data sensor (pitch, roll, heading); true values, not alignment-biased.
-- deps.position(): ray origin (north, up, east); defaults to the sensor's position.
-- deps.reference_elevation(): elevation (m) of the reference point, or nil when none.
function M.new(deps)
    deps = deps or {}
    local layout = deps.layout or dofile(LockOn_Options.script_path .. "HUD/Indicator/layout_profile.lua")
    local tfov = math.tan(math.rad(TFOV_HALF_DEG))
    local w, h = math.rad(layout.half_width_deg), math.rad(layout.half_height_deg)
    local home_x, home_y = layout.origin_mrad[1] / 1000, layout.origin_mrad[2] / 1000
    local area = {left = home_x - w, right = home_x + w, bottom = home_y - h, top = home_y + h}
    local function handle(name) return get_param_handle("F117_HUDCUR_" .. name) end
    local p_valid, p_az, p_el = handle("VALID"), handle("AZ"), handle("EL")
    local g_valid, g_x, g_y, g_z = handle("GROUND_VALID"), handle("GROUND_X"), handle("GROUND_Y"), handle("GROUND_Z")
    local look_valid, look_az, look_el = get_param_handle("F117_OCIP_IRADS_LOOK_VALID"),
        get_param_handle("F117_OCIP_IRADS_LOOK_AZ"), get_param_handle("F117_OCIP_IRADS_LOOK_EL")
    local active = false
    local cx, cy = home_x, home_y
    local ground

    local function clamp()
        local radius = math.sqrt(cx * cx + cy * cy)
        if radius > tfov then cx, cy = cx * tfov / radius, cy * tfov / radius end
        cx = math.max(area.left, math.min(area.right, cx))
        cy = math.max(area.bottom, math.min(area.top, cy))
    end

    -- The HUD cursor and the IRADS cursor are slaved (one symbol): start from the IRADS look angle.
    local function slave()
        if look_valid:get() > .5 then cx, cy = look_az:get(), look_el:get() else cx, cy = home_x, home_y end
        clamp()
    end

    local function publish()
        p_valid:set(active and 1 or 0)
        p_az:set(cx); p_el:set(cy)
        g_valid:set(ground and 1 or 0)
        g_x:set(ground and ground[1] or 0); g_y:set(ground and ground[2] or 0); g_z:set(ground and ground[3] or 0)
    end

    local function set_active(on)
        if on == active then return end
        active = on
        if on then slave() else ground = nil end
        publish()
    end

    local function slew(dx, dy, dt)
        if not active or not (finite(dx) and finite(dy) and finite(dt)) then return end
        local step = math.rad(SLEW_DEG_PER_S) * dt
        cx, cy = cx + dx * step, cy + dy * step
        clamp()
    end

    local function recenter()
        if active then slave() end
    end

    local function update()
        ground = nil
        if active and deps.attitude then
            local s = deps.attitude
            local position = {(deps.position or s.getSelfCoordinates)()}
            local reference = deps.reference_elevation and deps.reference_elevation()
            if reference then
                ground = M.ground_point(cx, cy, s.getHeading(), s.getPitch(), s.getRoll(), position, reference)
            end
        end
        publish()
    end

    return {
        set_active = set_active, slew = slew, recenter = recenter, update = update,
        position = function() return cx, cy end,
        active = function() return active end,
        ground = function() return ground end,
    }
end
return M
