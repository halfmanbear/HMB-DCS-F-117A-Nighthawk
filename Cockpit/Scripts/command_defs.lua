start_custom_command = 10000
local __count_custom = start_custom_command
local function __custom_counter()
    __count_custom = __count_custom + 1
    return __count_custom
end

Keys = {
    PlanePickleOn = 350,
    PlanePickleOff = 351,
    LeftEngineStart = 311,
    RightEngineStart = 312,
    LeftEngineStop = 313,
    RightEngineStop = 314,
    PowerOnOff = 315,

    -- The custom button starts from here, and can be automatically increased from 10000 to avoid conflicts
    PanelLight       = __custom_counter(), -- 10001
    FloodLight       = __custom_counter(), -- 10002
    LdgLight         = __custom_counter(), -- 10003
    NavLight         = __custom_counter(), -- 10004
    TaxiLgt          = __custom_counter(), -- 10005
    MemeLgt          = __custom_counter(), -- 10006
    BcnLgt           = __custom_counter(), -- 10007
    IRADSZoomIn      = __custom_counter(), -- 10008
    IRADSZoomOut     = __custom_counter(), -- 10009
    MFDOverlayToggle = __custom_counter(), -- 10010
}

hotas_commands =
{
    THROTTLE_DESIGNATOR_CONTROLLER_UP      = 10112,
    THROTTLE_DESIGNATOR_CONTROLLER_DOWN    = 10113,
    THROTTLE_DESIGNATOR_CONTROLLER_LEFT    = 10110,
    THROTTLE_DESIGNATOR_CONTROLLER_RIGHT   = 10111,
    THROTTLE_DESIGNATOR_CONTROLLER_DEPRESS = 10114,
    THROTTLE_FLIR_FOV_NARROW               = 103,
    THROTTLE_FLIR_FOV_WIDE                 = 104,
}

-- F-117A weapons delivery commands, handled by the EFM (Inputs.h).
-- Weapon release deliberately does NOT use iCommandPlanePickleOn (350): that
-- command makes avSimpleWeaponSystem release immediately, bypassing CCRP.
f117_commands =
{
    WEAPON_RELEASE_ON      = 10103, -- weaponReleaseHoldOn
    WEAPON_RELEASE_OFF     = 10104, -- weaponReleaseHoldOff
    IRADS_DESIGNATION_CLEAR = 10117,
    IRADS_LASER_ARM_TOGGLE = 10118,
    IRADS_SLEW_HORIZONTAL = 10119, -- absolute axis: negative left, positive right
    IRADS_SLEW_VERTICAL   = 10120, -- absolute axis: negative down, positive up
    MASTER_ARM_TOGGLE    = 10122,
    WEAPON_STATION_NEXT   = 10123,
    WEAPON_STATION_PREV   = 10124,
    IRADS_ZOOM_AXIS       = 10121, -- absolute axis: -1 wide, 0 medium, +1 narrow
    AUTOTHROTTLE_ENGAGE     = 10125, -- A/T engage switch: CAS hold at current CAS
    AUTOTHROTTLE_DISCONNECT = 10126, -- inboard throttle A/T disengage button
    PAARS_TOGGLE            = 10127, -- stick ARS switch: automatic recovery on/off
}


--Incremental click commands from 5000
start_command = 5000
local __count_click = start_command - 1
local function __click_counter()
    __count_click = __count_click + 1
    return __count_click
end

click_cmd = {
    GearLevel = __click_counter()
}

-- Stubs for ported Gripen systems (Displays.lua, FC3.lua).
-- Each unknown key gets a unique ID via __index so listen_command() doesn't crash.
-- IDs start well above the F-117's own ranges to avoid conflicts.
-- Replace individual entries here with real F-117 input command IDs as you implement them.
local __keys_count = 11000
keys = keys or setmetatable({}, {
    __index = function(t, k)
        __keys_count = __keys_count + 1
        rawset(t, k, __keys_count)
        return __keys_count
    end
})

local __dev_count = 12000
deviceCommands = deviceCommands or setmetatable({}, {
    __index = function(t, k)
        __dev_count = __dev_count + 1
        rawset(t, k, __dev_count)
        return __dev_count
    end
})

-- Device-local axis actions; input profiles explicitly target DISPLAYS.
-- Displays forwards signed values on custom EFM commands, avoiding stock axes.
irads_axis_commands = { HORIZONTAL = 3001, VERTICAL = 3002, ZOOM = 3003 }
