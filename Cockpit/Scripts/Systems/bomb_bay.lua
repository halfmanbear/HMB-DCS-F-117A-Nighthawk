-- Simple gate: open-if-needed on PICKLE, fire when open,
-- close-after-release with 2s hold IFF we (the script) opened the bay.
-- If PICKLE is released before the bay fully opens, close immediately.

local dev = GetSelf()
local DT = 0.02
make_default_activity(DT)

-- === Args / commands ===
local ARG_BAY = 26
local CMD_TRIG_ON, CMD_TRIG_OFF = 84, 85
local CMD_PKL_ON,  CMD_PKL_OFF  = 350, 351
local CMD_BAY_TOGGLE            = 10100 -- EFM bayToggle

-- === Tuning ===
local OPEN_EPS   = 0.995          -- consider "open" at/above this
local CLOSE_EPS  = 0.005          -- consider "closed" at/below this
local TOGGLE_COOLDOWN_S = 0.20    -- debounce so we don't spam 10100
local HOLD_AFTER_RELEASE_S = 1.0  -- hold bay open this long after release (if we opened it)

-- === State ===
local holding                  = false
local trig_on_sent             = false
local open_at_press            = false
local toggle_cooldown          = 0.0

-- Persistent ownership flag:
-- true  -> the script opened the bay at some point and hasn't closed it yet
-- false -> the bay is either manual or already closed by us
local opened_by_script         = false

-- Per-press bookkeeping
local opened_by_us_this_press  = false

-- Delayed-close (for the 2s hold)
local close_pending            = false
local close_delay              = 0.0

-- === Utils ===
local function clamp01(x) if x < 0 then return 0 elseif x > 1 then return 1 else return x end end
local function read_bay()
    if type(get_aircraft_draw_argument_value) == "function" then
        local v = get_aircraft_draw_argument_value(ARG_BAY)
        if v ~= nil then return clamp01(v) end
    end
    return 0.0
end

local function bay_is_open(v)   return v >= OPEN_EPS end
local function bay_is_closed(v) return v <= CLOSE_EPS end

local function can_toggle() return toggle_cooldown <= 0.0 end
local function toggle_bay_once()
    if can_toggle() then
        dispatch_action(nil, CMD_BAY_TOGGLE)
        toggle_cooldown = TOGGLE_COOLDOWN_S
        return true
    end
    return false
end

-- === Lifecycle ===
function post_initialize()
    holding, trig_on_sent = false, false
    open_at_press = false
    toggle_cooldown = 0.0
    opened_by_script = false
    opened_by_us_this_press = false
    close_pending, close_delay = false, 0.0
end

dev:listen_command(CMD_PKL_ON)
dev:listen_command(CMD_PKL_OFF)

function SetCommand(cmd, _)
    if cmd == CMD_PKL_ON then
        -- INTERRUPT: cancel any delayed close during the hold window,
        -- but keep ownership so we'll still close on a later release.
        close_pending, close_delay = false, 0.0

        holding = true
        trig_on_sent = false
        opened_by_us_this_press = false

        local v26 = read_bay()
        open_at_press = bay_is_open(v26)

        if open_at_press then
            -- Already open -> start firing immediately
            dispatch_action(nil, CMD_TRIG_ON)
            trig_on_sent = true
        else
            -- Closed -> request open once; wait for arg to report open
            if toggle_bay_once() then
                opened_by_us_this_press = true
                opened_by_script = true   -- we now "own" the open until we close it
            end
        end

    elseif cmd == CMD_PKL_OFF then
        -- Stop firing if we had started
        if trig_on_sent then
            dispatch_action(nil, CMD_TRIG_OFF)
            trig_on_sent = false
        end

        holding = false

        local v26 = read_bay()

        if opened_by_script then
            if bay_is_open(v26) then
                -- Bay fully open at release -> arm 2s delayed close
                close_pending = true
                close_delay   = HOLD_AFTER_RELEASE_S
            else
                -- Released before fully open -> close immediately (no delay)
                if not toggle_bay_once() then
                    -- If we're in cooldown, queue an immediate close as soon as possible
                    close_pending = true
                    close_delay   = 0.0
                else
                    -- We just sent the close; drop ownership
                    opened_by_script = false
                    close_pending = false
                    close_delay = 0.0
                end
            end
        else
            -- We didn't open it (manual or already ours was cleared) -> do nothing
            close_pending = false
            close_delay   = 0.0
        end

        opened_by_us_this_press = false
        open_at_press = false
    end
end

function update()
    -- Debounce cooldown
    if toggle_cooldown > 0.0 then
        toggle_cooldown = math.max(0.0, toggle_cooldown - DT)
    end

    local v26 = read_bay()

    -- If holding and haven't started firing yet, start as soon as bay is open
    if holding and (not trig_on_sent) and bay_is_open(v26) then
        dispatch_action(nil, CMD_TRIG_ON)
        trig_on_sent = true
    end

    -- If bay got closed externally after we "owned" it, drop ownership and any pending close
    if (not holding) and opened_by_script and bay_is_closed(v26) then
        opened_by_script = false
        close_pending = false
        close_delay = 0.0
    end

    -- Handle delayed / queued close AFTER release (only when we still own the open)
    if (not holding) and close_pending then
        if close_delay > 0.0 then
            close_delay = math.max(0.0, close_delay - DT)
        end
        if (close_delay <= 0.0) and can_toggle() then
            if toggle_bay_once() then
                opened_by_script = false
                close_pending = false
            end
        end
    end
end

need_to_be_closed = false
