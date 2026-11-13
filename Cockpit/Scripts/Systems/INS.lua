-- INS position error model. A display-layer position: Navigation and the map see the true
-- position plus a bias that drifts slowly. IRADS, the HUD velocity vector and weapons stay on
-- true data (same policy as Systems/AlignedSensor.lua).
--
-- The sensor update function (Systems/NavUpdate.lua) estimates this bias from a sensor point and
-- removes it with apply_correction(). Drift continues afterwards, as in the aircraft.
--
-- Not from the manual: the drift rate and the starting error are tuning constants chosen for a
-- ring-laser-gyro INS class. The manual only gives the HSD deviation scales (+-3 / +-6 nm).
local M = {}
M.NM = 1852
M.DRIFT_NM_PER_HR = 1.0     -- drift speed once aligned (tuning constant)
M.INITIAL_ERROR_NM = 0.1    -- largest position error at the moment alignment completes
M.POSUNR_NM = 120           -- a correction this large raises POSUNR then the INS alert (TO 1F-117A-1 4-86)

local function finite(v) return type(v) == "number" and v == v and math.abs(v) < 1e12 end

-- opts.random(): 0..1, injectable for tests. opts.drift_nm_per_hr, opts.initial_error_nm override the constants.
function M.new(opts)
    opts = opts or {}
    local random = opts.random or math.random
    local drift_nm_per_hr = opts.drift_nm_per_hr or M.DRIFT_NM_PER_HR
    local initial_error_nm = opts.initial_error_nm or M.INITIAL_ERROR_NM
    local s = {POSUNR_NM = M.POSUNR_NM, bn = 0, be = 0, balt = 0, vn = 0, ve = 0, seeded = false,
               total_n = 0, total_e = 0, total_alt = 0, -- running sensor-update correction (DP 99)
               posunr = false, alert = false}
    local function handle(name) return get_param_handle("F117_INS_" .. name) end
    local p_aligned, p_advisory = handle("ALIGNED"), handle("ADVISORY")
    local p_bn, p_be, p_balt = handle("BIAS_N"), handle("BIAS_E"), handle("BIAS_ALT")
    local p_posunr, p_alert = handle("POSUNR"), handle("ALERT")
    local p_dr = get_param_handle("F117_NAV_DR") -- drawn by the VSD page

    local function seed()
        local a = 2 * math.pi * random()
        local r = initial_error_nm * M.NM * random()
        s.bn, s.be, s.balt = r * math.cos(a), r * math.sin(a), 0
        local d = 2 * math.pi * random()
        local speed = drift_nm_per_hr * M.NM / 3600 * (0.5 + 0.5 * random())
        s.vn, s.ve = speed * math.cos(d), speed * math.sin(d)
        s.seeded = true
    end

    local function publish(powered, aligned)
        p_aligned:set(aligned and 1 or 0)
        -- 0 blank, 1 ALIGN, 2 INS UP (VSD "INS mode advisory"). DR means dead reckoning after an INS alert.
        p_advisory:set(powered and (aligned and 2 or 1) or 0)
        p_bn:set(s.bn); p_be:set(s.be); p_balt:set(s.balt)
        p_posunr:set(s.posunr and 1 or 0); p_alert:set(s.alert and 1 or 0)
        p_dr:set(powered and s.alert and 1 or 0)
    end

    -- aligned: the INS has finished aligning (Electrical publishes F117_INS_ALIGNED); powered: bus is up.
    function s.update(dt, powered, aligned)
        if not powered or not aligned then
            -- Alignment is lost with power: the next alignment starts from a fresh error.
            if not powered then s.seeded = false; s.total_n, s.total_e, s.total_alt = 0, 0, 0 end
            s.bn, s.be, s.balt, s.vn, s.ve = 0, 0, 0, 0, 0
            s.posunr, s.alert = false, false
        else
            if not s.seeded then seed() end
            if finite(dt) and dt > 0 then s.bn, s.be = s.bn + s.vn * dt, s.be + s.ve * dt end
        end
        publish(powered, aligned)
    end

    -- True position (north, up, east) as the INS reports it.
    function s.coordinates(x, y, z)
        return x + s.bn, y + s.balt, z + s.be
    end

    -- The error to subtract from INS-frame points: INS position = true + bias.
    function s.bias() return s.bn, s.be, s.balt end

    -- ENTR on an accepted update: move the INS toward the truth by the correction vector.
    function s.apply_correction(dn, de, dalt)
        if not (finite(dn) and finite(de) and finite(dalt)) then return false end
        s.bn, s.be, s.balt = s.bn + dn, s.be + de, s.balt + dalt
        s.total_n, s.total_e, s.total_alt = s.total_n + dn, s.total_e + de, s.total_alt + dalt
        return true
    end

    function s.magnitude_nm() return math.sqrt(s.bn * s.bn + s.be * s.be) / M.NM end

    -- POSUNR then INS alert; both inhibit further updates until cleared (BIT 83 in the manual).
    function s.raise_alerts() s.posunr, s.alert = true, true end
    function s.clear_alerts() s.posunr, s.alert = false, false end
    function s.inhibited() return s.posunr or s.alert end

    -- Wrap a base-data style sensor so Navigation and the map see the INS position.
    function s.wrap(sensor)
        local wrapped = {
            getSelfCoordinates = function()
                local x, y, z = sensor.getSelfCoordinates()
                if not (finite(x) and finite(y) and finite(z)) then return x, y, z end
                return s.coordinates(x, y, z)
            end,
            getInsBias = function() return s.bn, s.be, s.balt end,
        }
        return setmetatable(wrapped, {__index = function(_, k) return sensor[k] end})
    end

    return s
end
return M
