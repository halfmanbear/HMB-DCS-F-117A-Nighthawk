-- Global cockpit commands (no cockpit_device_id): every Lua device and the EFM
-- receive them. Each ID is written out, because saved user bindings store the
-- number. Never renumber one; add new commands with a fresh ID instead.
-- 10100-10129 belong to the EFM tables below and 10200 to the damage monitor.
Keys = {
    PowerOnOff        = 315,   -- stock iCommandPowerOnOff
    IRADSZoomIn       = 10008, -- the EFM matches these two by number (Inputs.h)
    IRADSZoomOut      = 10009,
    GroundPowerToggle = 10012,
    GroundAirToggle   = 10013,

    -- Lighting, handled by Systems/lights_system.lua.
    FloodLight = 10141,
}

-- Stock iCommand IDs the Lua devices also act on. The base input profile binds
-- keys to these, so no mod binding is needed (docs/reference/iCommands.lua).
native_commands = {
    WP_NEXT          = 102,  -- iCommandPlaneChangeTarget
    WP_PREV          = 1315, -- iCommandPlaneUFC_STEER_DOWN
    NAV_LIGHTS       = 175,  -- iCommandPlaneLightsOnOff
    COCKPIT_LIGHT    = 300,  -- iCommandPlaneCockpitIllumination
    LANDING_LIGHT    = 328,  -- iCommandPlaneHeadLightOnOff
    BEACON_LIGHT     = 518,  -- iCommandPlaneAntiCollisionLights
    TAXI_LIGHT       = 1398, -- iCommandPlaneLGPTaxiLight
    WEAPON_NEXT      = 101,  -- iCommandPlaneChangeWeapon: next loaded station (Weapons.lua)
    SENSOR_RESET     = 1635, -- iCommandSensorReset: the EFM undesignates and returns the IRADS gimbal to home
    -- The profiles target these at the DISPLAYS device, which forwards to the
    -- mod's own IDs, so the EFM never sees the stock number as well.
    ZOOM_IN          = 103,  -- iCommandPlaneZoomIn: IRADS FOV narrow
    ZOOM_OUT         = 104,  -- iCommandPlaneZoomOut: IRADS FOV wide
    I251_BRIGHTNESS_UP   = 842, -- iCommandPlane_I251_Brightness_Up
    I251_BRIGHTNESS_DOWN = 843,
    I251_CONTRAST_UP     = 844,
    I251_CONTRAST_DOWN   = 845,
    NWS_ON           = 562,  -- iCommandPlane_HOTAS_NoseWheelSteeringButton
    NWS_OFF          = 606,  -- iCommandPlane_HOTAS_NoseWheelSteeringButtonOff
    TDC_DEPRESS_ON   = 634,  -- iCommandPlane_HOTAS_TDC_depress_on
    TDC_DEPRESS_OFF  = 635,  -- iCommandPlane_HOTAS_TDC_depress_off
    -- Stock commands the EFM (master arm, laser arm) and Electrical.lua (APU) handle themselves.
    MASTER_ARM       = 1374, -- iCommandPlaneAHCPMasterArm (EFM)
    MASTER_SAFE      = 1375, -- iCommandPlaneAHCPMasterSafe
    LASER_ARM        = 1380, -- iCommandPlaneAHCPLaserArm
    LASER_SAFE       = 1381, -- iCommandPlaneAHCPLaserSafe
    APU_START        = 1055, -- iCommandPlane_APU_Start (Electrical.lua)
    APU_OFF          = 1056, -- iCommandPlane_APU_Off (Electrical.lua)
    SELECTER_LEFT    = 139,  -- iCommandSelecterLeft: TDC slew, forwarded to hotas_commands
    SELECTER_RIGHT   = 140,
    SELECTER_UP      = 141,
    SELECTER_DOWN    = 142,
    DSS_UP           = 544,  -- iCommandPlane_HOTAS_TargetManagementSwitchUp: Designate Select HUD
    DSS_DOWN         = 545,  -- ...Down: not used
    DSS_LEFT         = 546,  -- ...Left: MAP
    DSS_RIGHT        = 547,  -- ...Right: not used
    DSS_OFF          = 548,  -- ...Off: CENTER, IRADS
    SELECTER_STOP    = 230,  -- iCommandSelecterStop: released slew key
}

-- Global EFM commands (no cockpit_device_id). Member names follow the FA-18C
-- hotas_commands table, but the IDs are this mod's own: official *_commands
-- tables are device-local to each module and not shared between modules.
hotas_commands =
{
    THROTTLE_DESIGNATOR_CONTROLLER_UP      = 10112,
    THROTTLE_DESIGNATOR_CONTROLLER_DOWN    = 10113,
    THROTTLE_DESIGNATOR_CONTROLLER_LEFT    = 10110,
    THROTTLE_DESIGNATOR_CONTROLLER_RIGHT   = 10111,
    THROTTLE_DESIGNATOR_CONTROLLER_DEPRESS = 10114,
    THROTTLE_FLIR_FOV_NARROW               = 103, -- iCommandPlaneZoomIn
    THROTTLE_FLIR_FOV_WIDE                 = 104, -- iCommandPlaneZoomOut
}

-- F-117A weapons delivery commands, handled by the EFM (Inputs.h).
-- The input profiles bind Weapon Release to iCommandPlanePickleOn/Off (350/351).
-- The EFM treats 350/351 exactly like WEAPON_RELEASE_ON/OFF: open the bay, then
-- release only when the delivery gates pass. A live DCS check on 2026-11-03
-- (Master Arm SAFE and ARMED, bay open, no designation) released nothing on 350.
f117_commands =
{
    BOMB_BAY_TOGGLE        = 10100, -- bombay: both bays together
    BOMB_BAY_SELECTED_TOGGLE = 10130, -- bombaySelected: the bay of the selected store
    BOMB_BAY_LEFT_TOGGLE   = 10131, -- bombayLeft: station 1
    BOMB_BAY_RIGHT_TOGGLE  = 10132, -- bombayRight: station 2
    WEAPON_RELEASE_ON      = 10103, -- weaponReleaseHoldOn
    WEAPON_RELEASE_OFF     = 10104, -- weaponReleaseHoldOff
    IRADS_SLEW_HORIZONTAL = 10119, -- absolute axis: negative left, positive right
    IRADS_SLEW_VERTICAL   = 10120, -- absolute axis: negative down, positive up
    WEAPON_STATION_PREV   = 10124,
    IRADS_ZOOM_AXIS       = 10121, -- absolute axis: -1 wide, +1 narrow (cockpit selects endpoints only)
    AUTOTHROTTLE_ENGAGE     = 10125, -- A/T engage switch: CAS hold at current CAS
    AUTOTHROTTLE_DISCONNECT = 10126, -- inboard throttle A/T disengage button
    PAARS_TOGGLE            = 10127, -- stick ARS switch: automatic recovery on/off
    NWS_AUTHORITY_ON        = 10128, -- stick NWS authority button pressed: 45 deg steering range
    NWS_AUTHORITY_OFF       = 10129, -- stick NWS authority button released: back to 10 deg
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

-- Device-local IRADS image controls, independent of native camera/EFM commands.
irads_image_commands = {
    BRIGHTNESS_UP=3004, BRIGHTNESS_DOWN=3005,
    CONTRAST_UP=3006, CONTRAST_DOWN=3007,
    BRIGHTNESS_AXIS=3009, CONTRAST_AXIS=3010,
}

-- Device-local display selection; independent of sensor power and tracking.
left_cmdi_commands = { EO_TOGGLE=3011, EO_SELECT=3012, VSD_SELECT=3013, MAP_SELECT=3031, HSD_SELECT=3032 }
right_cmdi_commands = { MAP_SELECT=3033, HSD_SELECT=3034, VSD_SELECT=3035 }
irads_fov_commands = { WIDE=3036, NARROW=3037 }
-- Mission route: step the active waypoint (Systems/Navigation.lua).
nav_commands = { WP_NEXT=3038, WP_PREV=3039 }
-- MARK and sensor update (Systems/NavUpdate.lua). The CMDI MARK / SNSR / UPDT switches and the
-- CDU ENTR / CLR keys have no cockpit model yet, so these are bound in the input profiles.
update_commands = { MARK=3040, SNSR=3041, ENTR=3042, CLR=3043, UPDT=3044 }

-- Central map outline controls; not a replica of the real bezel switch layout.
map_commands = { RANGE_UP=3014, RANGE_DOWN=3015, ORIENTATION=3016,
    DATABASE=3017, FUNCTION=3018, LOOK=3019, SCROLL=3020, AUTO=3021,
    PAN_LEFT=3022, PAN_RIGHT=3023, PAN_UP=3024, PAN_DOWN=3025,
    TACTICAL_DECLUTTER=3026, BACKGROUND_DECLUTTER=3027,
    REFERENCE_ELEVATION=3028, ELEVATION_UP=3029, ELEVATION_DOWN=3030 }
