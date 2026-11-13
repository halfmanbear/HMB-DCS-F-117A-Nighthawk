-- MARK points and sensor update (SNSR), TO 1F-117A-1A. Follows the supplement where it differs
-- from the base TO.
--
-- MARK: stores the IRADS lock point (or, failing that, the HUD cursor ground point) as the next
-- destination point 94-98. Needs the Designate Select switch on IRADS or HUD; with no ground
-- coordinates an X shows over the MARK legend (F117_MARK_X). ENTR stores, CLR / MARK exits.
--
-- SNSR / map UPDT: the pilot puts a sensor point (IRADS lock, HUD cursor, or the map cursor) on
-- the selected destination. The INS sees that point at true + bias, so the correction is
--   correction = destination - sensor point (INS frame)
-- ENTR moves the INS by the correction and adds it to the running bias (DP 99); CLR, deselecting
-- SNSR, UPDT, or moving the switch off MAP rejects it. A correction of 120 nm or more raises POSUNR
-- and then the INS alert, which inhibit updates until CLR clears them.
--
-- Not available: OAP (offset select needs the CDU keypad, so SNSR always uses the current
-- destination), ALT CAL and visual update (also CDU).
local M = {}
local NM = 1852
local MAX_RANGE_NM, MAX_ALT_FT = 99.99, 99999
local M_TO_FT = 3.2808399

local function finite(v) return type(v) == "number" and v == v and math.abs(v) < 1e12 end
local function clamp(v, lo, hi) return v < lo and lo or v > hi and hi or v end

-- deps: navigation, ins, dss (state()), hud (active(), ground()), map (manual(), pick(),
-- set_update_cursor()), states = DesignateSelect (IRADS/HUD/MAP/NONE), position() = true (x, y, z),
-- elevation(x, z) = terrain height or nil, message(text).
function M.new(deps)
    local nav, ins, dss, hud, map, states = deps.navigation, deps.ins, deps.dss, deps.hud, deps.map, deps.states
    local elevation = deps.elevation or function() return nil end
    local function handle(name) return get_param_handle(name) end
    local lock_valid, lock_x, lock_y, lock_z = handle("F117_IRADS_LOCK_VALID"), handle("F117_IRADS_LOCK_X"),
        handle("F117_IRADS_LOCK_Y"), handle("F117_IRADS_LOCK_Z")
    local laser, wow = handle("F117_LASER_ARMED"), handle("F117_WOW")
    local out = {}
    for _, name in ipairs({"MARK_ACTIVE", "MARK_X", "MARK_LAST", "SNSR_ACTIVE", "SNSR_BOXED", "SNSR_VALID",
                           "SNSR_BRG", "SNSR_RNG", "SNSR_ALT", "UPDT_ACTIVE", "UPDT_LATCHED"}) do
        out[name] = handle("F117_" .. name)
    end
    local mark_active, sensor_active, upd_active, upd_latched = false, false, false, false
    local latched_cursor
    local correction, boxed = nil, false
    local last_mark = 0
    local publish -- defined below; designate and the switch callback refresh the outputs at once

    local function message(text) if deps.message then deps.message(text) end end

    -- Points are in the INS frame: true world data plus the INS bias.
    local function lock_point()
        if lock_valid:get() <= .5 then return nil end
        local x, y, z = lock_x:get(), lock_y:get(), lock_z:get()
        if not (finite(x) and finite(y) and finite(z)) then return nil end
        local bn, be, balt = ins.bias()
        return {x = x + bn, z = z + be, elev = y + balt, source = 1}
    end
    local function hud_point()
        local g = hud and hud.active() and hud.ground()
        if not g then return nil end
        return {x = g[1], z = g[3], elev = g[2], source = 2}
    end
    -- Ground coordinates for MARK and SNSR: the switch must be on IRADS or HUD; IRADS data is used if
    -- it is valid, the HUD cursor if not, whichever of the two positions is selected.
    local function source_point()
        local state = dss.state()
        if state ~= states.IRADS and state ~= states.HUD then return nil end
        return lock_point() or hud_point()
    end
    -- The reference is the current destination: a mission route point (marks and DP 99 are INS-frame).
    local function reference_point()
        local point = nav.active_point()
        if type(point) ~= "table" or point.kind == "mark" or point.kind == "bias" then return nil end
        if not (finite(point.x) and finite(point.z)) then return nil end
        return point
    end

    -- Returns a correction table, "posunr", or nil when the conditions are not met.
    local function compute(q, allow_altitude)
        local ref = reference_point()
        if not (q and ref) then return nil end
        if q.source == 1 and deps.position then
            -- IRADS needs the aircraft above the ground at the reference point.
            local _, y = deps.position()
            local height = elevation(ref.x, ref.z)
            if finite(y) and finite(height) and y <= height then return nil end
        end
        local dn, de = ref.x - q.x, ref.z - q.z
        local dalt = 0
        if allow_altitude and q.source == 1 and laser:get() > .5 then
            local _, _, balt = ins.bias()
            dalt = -balt -- an independent laser range solves altitude
        end
        local tn, te = ins.total_n + dn, ins.total_e + de
        if math.sqrt(tn * tn + te * te) >= ins.POSUNR_NM * NM then return "posunr" end
        return {dn = dn, de = de, dalt = dalt, source = q.source}
    end

    local function raise_posunr()
        ins.raise_alerts()
        message("POSUNR")
        message("INS")
    end

    local function exit_mark() mark_active = false end
    local function reject_sensor() sensor_active, boxed, correction = false, false, nil end
    local function exit_upd()
        upd_active, upd_latched, latched_cursor, correction = false, false, nil, nil
        if map then map.set_update_cursor(false) end
    end

    local function on_ground() return wow:get() > .5 end

    local function mark_press()
        if map and map.manual() ~= 0 then return end -- not available in manual map mode
        if mark_active then exit_mark() return end
        if nav.remaining() == 0 then return end -- five used: the function is inoperative
        reject_sensor(); exit_upd()
        mark_active = true
        if on_ground() then nav.consume_ground_mark() end
    end

    local function sensor_press()
        if sensor_active then reject_sensor() return end
        if ins.inhibited() or not reference_point() then return end
        exit_mark(); exit_upd()
        sensor_active = true
    end

    local function updt_press()
        if upd_active then exit_upd() return end
        if (map and map.manual() ~= 0) or not map then return end
        local q = lock_point()
        if dss.state() ~= states.MAP or not q or ins.inhibited() then return end
        exit_mark(); reject_sensor()
        upd_active, upd_latched = true, false
        map.set_update_cursor(true, q.x, q.z)
    end

    local function entr()
        if mark_active then
            local q = source_point()
            if q then
                local number = nav.add_mark(q.x, q.z, q.elev)
                if number then last_mark, mark_active = number, false end
            end
            return
        end
        local ready = correction and ((sensor_active and not boxed) or (upd_active and upd_latched))
        if ready then
            ins.apply_correction(correction.dn, correction.de, correction.dalt)
            nav.set_bias(ins.total_n, ins.total_e, ins.total_alt)
            reject_sensor(); exit_upd()
        end
    end

    local function clr()
        if mark_active then exit_mark()
        elseif sensor_active then reject_sensor()
        elseif upd_active then exit_upd()
        elseif ins.inhibited() then ins.clear_alerts() end
    end

    -- Throttle designate released while the switch is on MAP: latch the map cursor.
    local function designate(state)
        if state == states.MAP and upd_active and not upd_latched and map then
            local x, z = map.pick()
            if finite(x) and finite(z) then latched_cursor, upd_latched = {x = x, z = z}, true end
        end
        publish()
    end

    -- Moving the switch off MAP rejects a pending map update.
    local function on_dss_change(state)
        if upd_active and state ~= states.MAP then exit_upd() end
        publish()
    end

    function publish()
        out.MARK_ACTIVE:set(mark_active and 1 or 0)
        out.MARK_X:set(mark_active and not source_point() and 1 or 0)
        out.MARK_LAST:set(last_mark)
        out.SNSR_ACTIVE:set((sensor_active or upd_active) and 1 or 0)
        out.SNSR_BOXED:set((sensor_active and boxed) and 1 or 0)
        out.UPDT_ACTIVE:set(upd_active and 1 or 0)
        out.UPDT_LATCHED:set(upd_latched and 1 or 0)
        local shown = correction ~= nil
        out.SNSR_VALID:set(shown and 1 or 0)
        if shown then
            local bearing = ((math.atan2 or math.atan)(correction.de, correction.dn) * 180 / math.pi) % 360
            local range = math.sqrt(correction.dn ^ 2 + correction.de ^ 2) / NM
            out.SNSR_BRG:set(bearing)
            out.SNSR_RNG:set(clamp(range, 0, MAX_RANGE_NM))
            out.SNSR_ALT:set(clamp(correction.dalt * M_TO_FT, -MAX_ALT_FT, MAX_ALT_FT))
        end
    end

    local function update()
        if sensor_active then
            local c = compute(source_point(), true)
            if c == "posunr" then raise_posunr(); reject_sensor()
            elseif c then correction, boxed = c, false
            else correction, boxed = nil, true end -- boxed until the conditions are met
        elseif upd_active then
            if not lock_point() then exit_upd() -- the IRADS point the cursor is compared with is gone
            elseif upd_latched then
                -- Map update: the latched cursor point minus the IRADS point, both in the INS frame.
                local q = lock_point()
                local dn, de = latched_cursor.x - q.x, latched_cursor.z - q.z
                local tn, te = ins.total_n + dn, ins.total_e + de
                if math.sqrt(tn * tn + te * te) >= ins.POSUNR_NM * NM then raise_posunr(); exit_upd()
                else correction = {dn = dn, de = de, dalt = 0, source = 3} end
            end
        end
        publish()
    end

    local function set_command(command, value)
        if not update_commands or not value or value <= 0 then return false end
        if command == update_commands.MARK then mark_press()
        elseif command == update_commands.SNSR then sensor_press()
        elseif command == update_commands.ENTR then entr()
        elseif command == update_commands.CLR then clr()
        elseif command == update_commands.UPDT then updt_press()
        else return false end
        update()
        return true
    end

    local function initialize()
        mark_active, sensor_active, upd_active, upd_latched = false, false, false, false
        correction, boxed, last_mark, latched_cursor = nil, false, 0, nil
        publish()
    end

    initialize()
    return {
        set_command = set_command, update = update, initialize = initialize,
        designate = designate, on_dss_change = on_dss_change,
        mark_active = function() return mark_active end,
        sensor_active = function() return sensor_active end,
        update_active = function() return upd_active end,
        correction = function() return correction end,
    }
end
return M
