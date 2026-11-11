-- F-117A Nighthawk aircraft definition, loaded by entry.lua.
--
-- Conventions used below:
--   Positions are {+forward/-back, +up/-down, +right/-left} in metres from the model origin.
--   "AI" marks values that describe the AI aircraft. The player flies the EFM set up in
--   entry.lua and FM/config.lua, and the AI flies SFM_Data.
--   "ME" means the Mission Editor.
--
-- SOURCES - internet:
-- https://www.lockheedmartin.com/content/dam/lockheed-martin/aero/documents/F-117/F117%20Fast%20Facts_FINAL.pdf
-- http://www.f-117a.com/Specs.html
-- https://aerospaceweb.org/aircraft/bomber/f117/
-- https://www.thisdayinaviation.com/18-june-1981/
-- https://www.key.aero/article/aircraft-report-f-117a-nighthawk
-- https://nationalinterest.org/blog/buzz/we-now-know-america-still-secretly-flying-f-117-nighthawk-hk-091125
-- https://www.airforce-technology.com/projects/f117/
-- http://news.bbc.co.uk/1/hi/world/americas/2737617.stm
-- https://skybrary.aero/aircraft/f117
-- https://www.dreamlandresort.com/black_projects/f-117_articles.html
--
-- SOURCES - research / white papers:
-- Development of the F-117 Flight Control System by Robert Loschke (AIAA 2003-5762)
--
-- SOURCES - books:
-- Skunk Works: A Personal Memoir of My Years at Lockheed (by Ben R. Rich, Leo Janos)
-- F-117 Nighthawk Stealth Fighter: An Illustrated Developmental History (by Yancy D. Mailes, Tony R. Landis)

-- Platypus exhaust slots. Each engine exhausts through a flat, vaned slot about 2.85 m long
-- and 0.10 m tall, swept along the aft deck trailing edge. DCS draws heat blur, smoke and
-- contrails per nozzle, so each slot is split into narrow nozzles along its length to give
-- a flat sheet of hot gas instead of one round plume. Slot centreline taken from the model.
local PLATYPUS_SLOT = {inboard = {-5.29, -0.155, 0.66}, outboard = {-3.19, -0.155, 2.48}}
local PLATYPUS_SEGMENTS = 1 -- nozzles per slot; each one adds a heat-blur emitter, so more means a denser haze
local PLATYPUS_SPLAY = math.rad(30) -- exhaust flow turns this far outboard of straight aft

-- Point on a slot centreline: t = 0 inboard end, 1 outboard end; side -1 left, +1 right;
-- aft moves the point behind the slot face, in metres.
local function platypus_point(t, side, aft)
    local a, b = PLATYPUS_SLOT.inboard, PLATYPUS_SLOT.outboard
    return {a[1] + (b[1] - a[1]) * t - aft, a[2], side * (a[3] + (b[3] - a[3]) * t)}
end

local function platypus_nozzles()
    local nozzles = {}
    for engine, side in ipairs({-1, 1}) do -- engine 1 left, engine 2 right
        for i = 1, PLATYPUS_SEGMENTS do
            nozzles[#nozzles + 1] = {
                engine_number = engine,
                pos = platypus_point((i - 0.5) / PLATYPUS_SEGMENTS, side, 0.05),
                -- Points back up the exhaust flow, so x is positive for flow going aft.
                orientation = {math.cos(PLATYPUS_SPLAY), 0, -side * math.sin(PLATYPUS_SPLAY)},
                diameter = 0.05, -- m: same area as a quarter of the 2.85 x 0.10 m slot
                exhaust_length_ab = 5.00, -- m: afterburner flame length; none fitted
                exhaust_length_ab_K = 5.00, -- Afterburner flame animation factor
                smokiness_level = 0.02 / PLATYPUS_SEGMENTS, -- Engine smoke, up to 1.0; 0.02 per engine in total
            }
        end
    end
    return nozzles
end

-- Faint heat glow off the hot slot and lower lip at night. Two dim orange lights per slot,
-- just behind the slot face. Brightness follows draw arguments 1002 (left) and 1003 (right),
-- which Cockpit/Scripts/Systems/lights_system.lua drives from engine rpm.
local function platypus_glow_lights(diag_color)
    local lights = {}
    for engine, side in ipairs({-1, 1}) do
        for _, t in ipairs({0.3, 0.7}) do
            lights[#lights + 1] = {
                typename = "omnilight",
                position = platypus_point(t, side, 0.15),
                argument = (not diag_color) and (1001 + engine) or nil, -- TEMP TEST: diag lights have no argument
                color = diag_color or {1.0, 0.30, 0.08, 0.65}, -- TEMP TEST was 0.12; dull orange; fourth value is brightness
                range = 4.0, -- TEMP TEST was 1.8; m: lights the slot lip and aft deck, not the ground
                movable = false,
            }
        end
    end
    return {typename = "collection", lights = lights}
end

F_117_NightHawk = {
    ---------------------------------------------------------------------------
    -- Identity and database registration
    ---------------------------------------------------------------------------
    Name = "F-117-NightHawk", -- Unit type ID; missions, payload files and input profiles use this name
    DisplayName = _("F-117A Nighthawk"), -- Name shown in the DCS UI
    WorldID = WSTYPE_PLACEHOLDER, -- Numeric type ID, assigned by DCS at load
    attribute = {wsType_Air, wsType_Airplane, wsType_Fighter, WSTYPE_PLACEHOLDER, "Bombers", "Refuelable", "All", "NonAndLightArmoredUnits", "NonArmoredUnits", "Air", "Planes", "Battle airplanes"}, -- Type levels, then attribute names used by AI and mission logic; from DCS F-117A, required for AI bombing
    Categories = {}, -- ME unit categories; none needed
    Countries = {"USA"}, -- Countries that can field this unit
    country_of_origin = "USA", -- Country of manufacture
    mapclasskey = "P0091000027", -- ME map icon, from MissionEditor/data/NewMap/images; from DCS F-117A
    Picture = "F-117A.png", -- Aircraft image on the loadout and resource screens
    Rate = "70", -- Multiplayer reward points; also counted in debrief and logbook scores
    _file = current_mod_path .. "/F-117NightHawk.lua", -- Source path; the Encyclopedia prints it and the datalink code uses its folder
    _file_flyable = current_mod_path .. "/entry.lua", -- Flyable entry path; no stock Lua reads it
    swapped_names = true, -- Encyclopedia and cargo UI use obj.type instead of obj.Name as the unit type

    ---------------------------------------------------------------------------
    -- Callsigns
    ---------------------------------------------------------------------------
    InheriteCommonCallnames = false, -- Offer only the callsigns below, not the common list
    SpecificCallnames =
    {
        -- Each entry is {displayed name, internal name}
        ["USA"] = {
                    {_('Knight'),           'Knight'},
                    {_('Vega'),             'Vega'},
                    {_('Merk'),             'Merk'},
                    {_('Flash'),            'Flash'},
                    {_('Hand'),             'Hand'},
                    {_('Ghost'),            'Ghost'},
                    {_('Shade'),            'Shade'},
                    {_('Shadow'),           'Shadow'},
                    {_('Scorpion'),         'Scorpion'},
                    {_('Specter'),          'Specter'},
                    {_('Senior Trend'),     'Senior Trend'},
                    {_('Goblin'),           'Goblin'},
                    {_('Diamond'),          'Diamond'},
                    {_('Delta Dawn'),       'Delta Dawn'},
                    {_('Toxic Death'),      'Toxic Death'},
                    {_('Midnight Rider'),   'Midnight Rider'},
                    {_('Unexpected Guest'), 'Unexpected Guest'},
                    {_('Dark Angel'),       'Dark Angel'},
                    {_('Dark Knights'),     'Dark Knights'},
                    {_('Toxic Avenger'),    'Toxic Avenger'},
                    {_('Lone Wolf'),        'Lone Wolf'},
                    {_('Shaba'),            'Shaba'},
                    {_('Raven Beauty'),     'Raven Beauty'},
                    {_('Black Devil'),      'Black Devil'},
                    {_('Gray Dragon'),      'Gray Dragon'},
        }
    },

    ---------------------------------------------------------------------------
    -- Player cockpit
    ---------------------------------------------------------------------------
    HumanCockpit = true, -- Makes the aircraft flyable by players in the ME
    HumanCockpitPath = current_mod_path .. "/Cockpit/Scripts", -- Cockpit script folder
    HumanCommPanelPath = current_mod_path .. "/comm.lua", -- Radio menu script for this aircraft
    Waypoint_Custom_Panel = true, -- Shows the custom waypoint properties panel in the ME
    --_MAC_compatible = true, -- FC3 profile inheritance, not used with the EFM

    ---------------------------------------------------------------------------
    -- Mission roles
    ---------------------------------------------------------------------------
    Tasks = { -- Mission types offered in the ME; UnitPayloads tags must match these to be listed
        aircraft_task(GroundAttack),
        aircraft_task(PinpointStrike),
        aircraft_task(RunwayAttack),
    },
    DefaultTask = aircraft_task(PinpointStrike), -- Task selected for a new group

    ---------------------------------------------------------------------------
    -- Model and animation
    ---------------------------------------------------------------------------
    Shape = "f-117-nighthawk", -- Main .edm model name
    shape_table_data =
    {
        {
            file = "f-117-nighthawk", -- Main .edm file
            username = "F-117-NightHawk", -- Must be the same as Name
            -- Nil on first load, because the global is only assigned once this table is complete.
            -- Newer stock aircraft use WSTYPE_PLACEHOLDER.
            index = F_117_NightHawk;
            classname   = "lLandPlane"; -- Model object class
            positioning = "BYNORMAL"; -- Placement on terrain: BYNORMAL, ONLYHEIGTH, BY_XZ or ADD_HEIGTH
            life = 12, -- Lifebar: overall object strength
            vis = 3, -- Visibility gain; stock advises lower values for small objects
            desrt = "f-117-nighthawk-oblomok", -- .edm shown once destroyed
            fire = {300, 2}, -- Fire on the ground after destruction: {seconds, size in metres}
        },
        {
            name  = "f-117-nighthawk-oblomok"; -- Destroyed model name
            file  = "f-117-nighthawk-oblomok"; -- Destroyed model .edm file
            classname = "lLandPlane", -- Model object class
            positioning = "BYNORMAL"; -- Placement on terrain
            fire  = { 0, 1}; -- Fire on the wreck: {seconds, size in metres}
        },
    },
    -- Debris models for parts that break off. None are authored for the six small moving
    -- surfaces, and the whole-wing debris models don't suit them.
    DamageParts = {},
    -- Model draw arguments sent over the network, so other players see them move.
    -- Limit is 32, per the earlier note here (stock F-5E's comment says 16). 32 are in use;
    -- the list is full, so enabling any of the 12 commented entries needs another dropped.
    net_animation =
    {
        0,  -- Nose gear
        1,  -- Nose gear strut
        2,  -- Nose wheel steering
        3,  -- Right gear
        4,  -- Right gear strut
        5,  -- Left gear
        6,  -- Left gear strut
        9,  -- (Coupled) right rudder and elevon
        10, -- (Coupled) left rudder and elevon
        11, -- Right elevon
        12, -- Left elevon
        15, -- Right elevon (mixed)
        16, -- Left elevon (mixed)
        18, -- Rudder
        22, -- Refuel bay
        --25, -- Hook; the main .edm doesn't have this integrated yet
        26, -- Bomb bay: either bay open; DCS draws the stores only while it is
        27, -- Left bay door and trapeze
        28, -- Right bay door and trapeze
        35, -- Drag chute
        38, -- Canopy
        --50, -- Pilot remove
        101,-- Nose wheel rotate
        102,-- Left wheel rotate
        103,-- Right wheel rotate
        --114,-- Remove entire cockpit
        190,-- Taxi light
        191,-- Wing lights
        192,-- Landing lights
        193,-- Beacon light
        --224,-- Left wing damage
        --247,-- Left rudder damage
        --248,-- Right rudder damage
        --903,-- IRADS rotate
        --1000,-- Meme light
        324, -- Left inlet fan rotate
        325, -- Right inlet fan rotate
        1001,-- Beacon rotate
        1002,-- Left platypus heat glow
        1003,-- Right platypus heat glow
        --1010,-- Left elevon damage (outer)
        --1011,-- Left elevon damage (inner)
        --1014,-- Right elevon damage (inner)
        --1015,-- Right elevon damage (outer)
    },
    effects_presets = {{effect = "OVERWING_VAPOR", file = current_mod_path.."/Effects/f-117-nighthawk_overwingVapor.lua"}}, -- Extra visual effects
    -- Lights defined here, not in the model. The model's own lights run on their draw
    -- arguments and aren't listed. The group number is one AI never switches on, so only
    -- arguments 1002 and 1003 control the glow.
    lights_data = {
        typename = "collection",
        lights = {
            [WOLALIGHT_CABIN_WORK or 14] = {typename = "collection", lights = {
                platypus_glow_lights(),
                platypus_glow_lights({1.0, 1.0, 0.0, 0.65}), -- TEMP TEST yellow, group 14, no argument
            }},
            [12] = platypus_glow_lights({0.0, 1.0, 0.0, 0.65}), -- TEMP TEST green, group 12, no argument
            [3] = platypus_glow_lights({0.0, 0.3, 1.0, 0.65}), -- TEMP TEST blue, group 3, no argument
            [9] = platypus_glow_lights({1.0, 0.0, 1.0, 0.65}), -- TEMP TEST magenta, group 9, no argument
        },
    },
    wing_tip_pos = {-6.627, -0.265, 6.6}, -- Wingtip position for visual effects
    fires_pos = { -- Fire effect positions when damaged; stock files mark this for deprecation
        { -0.865, 1.01, 1 },
        { -0.37, -0.23, 3.01 },
        { -0.37, -0.23, -3.01 },
        { -0.82, 0.265, 2.774 },
        { -0.82, 0.265, -2.774 },
        { -0.82, 0.255, 4.274 },
        { -0.82, 0.255, -4.274 },
        { -4.45, 0.08, 1.7 },
        { -4.45, 0.08, -1.7 },
        { 2, -0.56, -1 },
        { -4.08, 0.22, 0 },
    },

    ---------------------------------------------------------------------------
    -- Dimensions
    ---------------------------------------------------------------------------
    length = 19.43, -- m: 63ft 9in (TO 1F-117A-1 page 1-1)
    height = 3.78, -- m: 12ft 5in
    wing_span = 13.21, -- m: 43ft 4in; also sets the footprint for ME parking checks
    wing_area = 84.8, -- m2: 912.7 sq ft. Lockheed states 780 sq ft (72 m2); a research paper suggests 105.9 m2
    wing_type = 0, -- 0 fixed, 1 variable geometry, 2 folded, 3 variable geometry and folded

    ---------------------------------------------------------------------------
    -- Mass and fuel
    ---------------------------------------------------------------------------
    -- Max payload is 2268 kg (5000 lb); typical combat payload is 1814 kg (4000 lb).
    M_empty = 13381, -- kg: 29500 lb, empty mass
    M_nominal = 19278, -- kg: typical mass, about half fuel plus a typical combat payload
    M_max = 23814, -- kg: 52500 lb, maximum mass
    M_fuel_max = 8255, -- kg: 18200 lb public figure, internal fuel (about 19000 lb in Paul Crickmore's book)
    AmmoWeight = 0, -- kg: gun ammunition; no gun
    average_fuel_consumption = 0.59, -- kg/s: average burn, a rough estimate (earlier value 0.184)

    ---------------------------------------------------------------------------
    -- Values shown or enforced by the ME and other UI screens
    ---------------------------------------------------------------------------
    EmptyWeight = 13381, -- kg: base of the payload screen's total weight
    MaxFuelWeight = 8255, -- kg: full-scale value of the fuel slider
    MaxTakeOffWeight = 23814, -- kg: payload screen weight limit
    MaxHeight = 13716, -- m: 45000 ft, upper limit for altitude entry
    MaxSpeed = 1100, -- km/h: 684 mph, Mach 0.92 at 35000 ft, upper limit for route speed
    WingSpan = 13.21, -- m: 43ft 4in; no stock Lua reads it, and the ME uses wing_span
    range = 1720, -- km: about 930 nmi. Stock labels this max range (AI); the source figure is combat radius

    ---------------------------------------------------------------------------
    -- Flight performance and limits (AI)
    ---------------------------------------------------------------------------
    H_max = 13716, -- m: 45000 ft, maximum altitude
    Mach_max = 0.92, -- Maximum Mach: 684 mph at 35000 ft (562 KEAS, Mach 0.90 in Paul Crickmore's book)
    V_max_sea_level = 292, -- m/s: maximum speed at sea level
    V_max_h = 273, -- m/s: maximum speed at maximum altitude (45000 ft)
    V_opt = 230, -- m/s: cruise speed; also the default ME route speed
    V_take_off = 84.9, -- m/s: 165 kt take-off speed (170 kt unstick in Paul Crickmore's book)
    V_land = 77.2, -- m/s: 150 kt landing speed; also the lowest ME route speed
    CAS_min = 64, -- m/s: minimum calibrated airspeed
    Vy_max = 14.3, -- m/s: maximum climb rate
    AOA_take_off = 0.14, -- rad: about 8 deg take-off AoA (sources mention 9 deg landing AoA)
    bank_angle_max = 60, -- deg: maximum bank angle
    Ny_min = -3, -- Minimum G
    Ny_max = 6, -- Maximum G
    Ny_max_e = 6, -- Second maximum-G limit; stock labels it only "Max G (for AI)"
    flaps_maneuver = 1, -- Maximum flaps for take-off and maneuvering: 0.5 first stage, 1.0 second stage (was 0)

    ---------------------------------------------------------------------------
    -- Engines
    ---------------------------------------------------------------------------
    has_afteburner = false, -- No afterburner
    engines_count = 2, -- Number of engines
    -- kgf for both engines: 80415 N or 18078 lb, about 9040 lb per engine (earlier value 8668.2).
    -- Paul Crickmore's book gives 10800 lb, with possible losses in the airframe and platypus exhaust.
    thrust_sum_max = 8200, -- Military thrust
    thrust_sum_ab = 8200, -- Afterburner thrust; same as military, as there is no afterburner
    engines_nozzles = platypus_nozzles(), -- Four per slot; see PLATYPUS_SLOT at the top

    ---------------------------------------------------------------------------
    -- Landing gear and ground handling
    ---------------------------------------------------------------------------
    main_gear_pos = {-0.292856, -2.055, 2.095716}, -- Main gear position
    nose_gear_pos = {5.0765, -2.020, 0}, -- Nose gear position
    main_gear_wheel_diameter = 0.8128, -- m: 32 in
    nose_gear_wheel_diameter = 0.5588, -- m: 22 in
    -- Tangent of the maximum nosewheel steering angle: tan(45 deg), matching yaw_limit in FM/config.lua.
    tand_gear_max = 1.0,
    has_speedbrake = false, -- No speedbrake
    brakeshute_name = 3, -- Drag chute visual shape after separation
    bigParkingRamp = false, -- true would limit the aircraft to large parking spots in the ME

    ---------------------------------------------------------------------------
    -- Air refuelling
    ---------------------------------------------------------------------------
    tanker_type = 1, -- 1 boom, as on stock F-16C and F-15E; 2 drogue
    air_refuel_receptacle_pos = {2.356, 1.119, 0.0}, -- Refuelling receptacle position

    ---------------------------------------------------------------------------
    -- Crew and visibility
    ---------------------------------------------------------------------------
    crew_size = 1, -- Number of crew
    crew_members =
    {
        [1] =
        {
            role = "pilot", -- Crew role
            role_display_name    = _("Pilot"), -- Role name shown in the UI
            can_be_playable = true, -- A player can take this seat
            pos = {5.213, 0.744, 0}, -- Crew position
            --canopy_pos = {4.5, 1, 0}, -- Canopy position, left to the model
            g_suit =  5.0, -- G-suit rating; stock uses 0.7 to 5 (was 2.0)
            ejection_seat_name = 17, -- Ejection seat model, the same as stock F-5E
            ejection_order = 1, -- Order in which crew eject
            ejection_added_speed = {-5, 15, 0}, -- m/s added to the seat at ejection
            drop_canopy_name = "f-117-nighthawk_canopy", -- .edm for the jettisoned canopy (earlier value 12)
            canopy_arg = 38, -- Canopy jettison draw argument. Arg 50 is pilot and seat; arg 114 is the dash
        },
    },
    CanopyGeometry = { -- Pilot view limits in degrees (AI)
        azimuth = {-160.0, 160.0}, -- Horizontal
        elevation = {-50.0, 90.0} -- Vertical
    },

    ---------------------------------------------------------------------------
    -- Signatures
    ---------------------------------------------------------------------------
    RCS = 0.003, -- m2: radar cross section (0.001 to 0.01 in various sources)
    IR_emission_coeff = 0.15, -- IR signature; 1.0 is an Su-27 without afterburner
    IR_emission_coeff_ab = 0, -- IR signature in afterburner; none fitted

    ---------------------------------------------------------------------------
    -- Sensors
    ---------------------------------------------------------------------------
    radar_can_see_ground = false, -- Radar ground detection; no radar
    detection_range_max = 0, -- Search sensor range (AI); no radar. Stock files don't document the unit
    -- Targeting sensors (AI). "IRADS" is the sensor DCS declares for its built-in F-117A.
    Sensors = {
        OPTIC = {"IRADS"},
    },
    laserEquipment = { -- Laser equipment on board
        laserDesignator = true,
        laserRangefinder = true,
    },

    ---------------------------------------------------------------------------
    -- Stores
    ---------------------------------------------------------------------------
    stores_number = 2, -- Total stores stations
    -- pylon(station, type, x, y, z, settings, launchers)
    -- type: stock notes 0 rail and 1 ejector. Stock doesn't document 2; it was noted here as invisible.
    -- x, y, z: unused here, because use_full_connector_position reads the position from the model.
    Pylons = {
        pylon(
            1, -- Station number
            2, -- Pylon type
            0, -- X
            0, -- Y
            0, -- Z
            {
                use_full_connector_position = true, -- Take the position from the model connector
                connector = "Pylon1", -- Model connector name
                DisplayName = "1" -- Station label on the loadout screen
            },
            {
                {CLSID = "<CLEAN>"}, --,attach_point_position = {0.02, 0.00, 0.00}
                -- Laser Paveway III (primary historical)
                {CLSID = "{EF0A9419-01D6-473B-99A3-BEBDB923B14D}"}, --GBU-27
                -- Other LGBs (secondary/hypothetical)
                {CLSID = "{51F9AAE5-964F-4D21-83FB-502E3BFE5F8A}"}, --GBU-10
                {CLSID = "{DB769D48-67D7-42ED-A2BE-108D566C8B1E}"}, --GBU-12
                -- JDAMs (late-career / plausible)
                {CLSID = "{GBU-31}"},                               --GBU-31(V)1/B
                {CLSID = "{GBU-31V3B}"},                            --GBU-31(V)3/B
                {CLSID = "{GBU_32_V_2B}"},                          --GBU-32(V)2/B
                -- Maverick (hypothetical)
                {CLSID = "{444BA8AE-82A7-4345-842E-76154EFCCA47}"}, --AGM-65D Maverick (IIR)
                {CLSID = "{F16A4DE0-116C-4A71-97F0-2CF85B0313EF}"}, --AGM-65E Maverick (laser)
                -- JSOW (hypothetical)
                {CLSID = "{AGM-154A}"},                             --JSOW AGM_154_A
                {CLSID = "{AGM-154B}"},                             --JSOW AGM_154_B
                {CLSID = "{9BCC2A2B-5708-4860-B1F1-053A18442067}"}, --JSOW AGM_154_C_JSOW
                -- CBU (hypothetical)
                {CLSID = "{CBU_105}" },                             --CBU-105
                -- Dumb bombs
                {CLSID = "{BCE4E030-38E9-423E-98ED-24BE3DA87C32}"}, --Mk 82
                {CLSID = "{AB8B8299-F1CC-4359-89B5-2172E0CF4A5A}"}, --Mk 84
            }
        ),
        pylon(
            2, -- Station number
            2, -- Pylon type
            0, -- X
            0, -- Y
            0, -- Z
            {
                use_full_connector_position = true, -- Take the position from the model connector
                connector = "Pylon2", -- Model connector name
                DisplayName = "2" -- Station label on the loadout screen
            },
            {
                {CLSID = "<CLEAN>"}, --,attach_point_position = {0.02, 0.00, 0.00}
                -- Laser Paveway III (primary historical)
                {CLSID = "{EF0A9419-01D6-473B-99A3-BEBDB923B14D}"}, --GBU-27
                -- Other LGBs (secondary/hypothetical)
                {CLSID = "{51F9AAE5-964F-4D21-83FB-502E3BFE5F8A}"}, --GBU-10
                {CLSID = "{DB769D48-67D7-42ED-A2BE-108D566C8B1E}"}, --GBU-12
                -- JDAMs (late-career / plausible)
                {CLSID = "{GBU-31}"},                               --GBU-31(V)1/B
                {CLSID = "{GBU-31V3B}"},                            --GBU-31(V)3/B
                {CLSID = "{GBU_32_V_2B}"},                          --GBU-32(V)2/B
                -- Maverick (hypothetical)
                {CLSID = "{444BA8AE-82A7-4345-842E-76154EFCCA47}"}, --AGM-65D Maverick (IIR)
                {CLSID = "{F16A4DE0-116C-4A71-97F0-2CF85B0313EF}"}, --AGM-65E Maverick (laser)
                -- JSOW (hypothetical)
                {CLSID = "{AGM-154A}"},                             --JSOW AGM_154_A
                {CLSID = "{AGM-154B}"},                             --JSOW AGM_154_B
                {CLSID = "{9BCC2A2B-5708-4860-B1F1-053A18442067}"}, --JSOW AGM_154_C_JSOW
                -- CBU (hypothetical)
                {CLSID = "{CBU_105}" },                             --CBU-105
                -- Dumb bombs
                {CLSID = "{BCE4E030-38E9-423E-98ED-24BE3DA87C32}"}, --Mk 82
                {CLSID = "{AB8B8299-F1CC-4359-89B5-2172E0CF4A5A}"}, --Mk 84
            }
        ),
    },

    ---------------------------------------------------------------------------
    -- Simple Flight Model (AI)
    --   Max climb about 2800 fpm (14.3 m/s) at typical combat weight (44000 to 48000 lb)
    --   Service ceiling about 45000 ft (13.7 km), where climb rate falls to 0 to 300 fpm
    --   Max level speed Mach 0.90 to 0.92 clean at altitude
    --   Subsonic only with no afterburner, and a notable transonic drag rise near Mach 0.9
    ---------------------------------------------------------------------------
    SFM_Data = {
        aerodynamics =
        {
            Cy0       = 0.0,     -- Lift coefficient at zero AoA
            Czbe      = -0.012,  -- Side force per degree of sideslip; affects yaw
            Mzalfa    = 6.6,     -- Pitch agility coefficient
            Mzalfadt  = 1.0,     -- Pitch agility coefficient; higher means more inertia and slower recovery
            cx_gear   = 0.006,   -- Landing gear drag coefficient
            kjx       = 2.85,    -- Roll inertia parameter; smaller means more inertia
            kjz       = 0.00125, -- Pitch inertia parameter
            -- table_data columns:
            -- Mach   = Mach number this row applies at
            -- Cx0    = Zero-lift drag coefficient
            -- Cya    = Normal force coefficient per degree of AoA. Available G falls as this rises
            -- B2     = Polar 2nd power coefficient (induced drag, Cy^2 term)
            -- B4     = Polar 4th power coefficient (high-AoA drag, Cy^4 term)
            -- Omxmax = Roll rate, rad/s
            -- Aldop  = Maximum AoA at this Mach before departure, degrees
            -- Cymax  = Maximum lift coefficient
            --{Mach, Cx0,    Cya,   B2,    B4,     Omxmax, Aldop, Cymax }
            table_data =
            {
              {0.00, 0.0090, 0.065, 0.230, 0.0001, 0.55,   30.0,  1.20},
              {0.20, 0.0090, 0.065, 0.230, 0.0001, 1.50,   30.0,  1.20},
              {0.40, 0.0090, 0.067, 0.230, 0.0001, 2.50,   30.0,  1.20},
              {0.60, 0.0090, 0.070, 0.230, 0.0001, 3.30,   29.0,  1.18},
              {0.70, 0.0090, 0.073, 0.230, 0.0001, 3.30,   28.0,  1.16},
              {0.80, 0.0110, 0.077, 0.240, 0.0001, 3.30,   27.0,  1.14},
              {0.85, 0.0120, 0.079, 0.250, 0.0001, 3.20,   26.0,  1.12},
              {0.90, 0.0135, 0.081, 0.255, 0.0001, 3.00,   25.0,  1.10},
              {0.92, 0.0154, 0.082, 0.260, 0.0001, 3.00,   24.0,  1.09},
            },
        },

        engine =
        {
            type    = "TurboFan", -- Engine type
            --typeng  = 4, -- Older numeric engine type field
            MinRUD  = 0, -- Throttle position: minimum
            MaxRUD  = 1, -- Throttle position: maximum
            MaksRUD = 1, -- Throttle position: military power
            ForsRUD = 1, -- Throttle position: afterburner
            Nmg     = 62.0, -- Idle RPM, percent
            Nominal_RPM = 14000.0, -- Nominal RPM, the same as stock F-15E
            Nominal_Fan_RPM = 10000.0, -- Fan RPM, the same as stock F-15E
            Startup_Prework = 10.0, -- Startup delay before spool-up, the same as stock F-15E; seconds by its name
            Startup_Duration = 40.0, -- Startup time, the same as stock F-15E; seconds by its name
            Shutdown_Duration = 35.0, -- Shutdown time, the same as stock F-15E; seconds by its name
            dcx_eng = 0.0085, -- Engine drag coefficient; affects drag when shut down
            hMaxEng = 19.5, -- km: maximum altitude for safe engine operation
            cemax   = 1.24, -- Fuel use at military power; only for AI flight time checks, not fuel burn
            cefor   = 1.24, -- Fuel use in afterburner; only for AI flight time checks, not fuel burn
            -- Thrust loss per 1000 m, kept as a fallback for altitudes outside the extended table
            dpdh_m  = 8000, -- Military thrust
            dpdh_f  = 8000, -- Afterburner thrust

            extended =
            {
                thrust_max =
                {
                  -- Altitude breakpoints in metres: SL, 15kft, 20kft, 30kft, 32kft, 40kft, 46kft
                  H = { 0, 4572, 6096, 9144, 9754, 12192, 14000 },
                  -- Mach breakpoints, matching table_data below
                  M = { 0.00, 0.20, 0.40, 0.60, 0.70, 0.80, 0.85, 0.90, 0.92 },
                  -- thrust[altitude index] = { Newtons at each Mach }
                  -- Lapse factors (P/P0)^0.82: 1.000, 0.625, 0.535, 0.370, 0.343, 0.251, 0.199
                  thrust =
                    {
                        -- H=0 (SL), the same values as table_data below
                        { 80415, 76404, 75268, 77007, 78995, 81621, 83224, 84806, 85006 },
                        -- H=4572m (15kft)
                        { 50259, 47753, 47043, 48129, 49372, 51013, 52015, 53004, 53129 },
                        -- H=6096m (20kft)
                        { 43022, 40876, 40268, 41219, 42262, 43667, 44525, 45371, 45478 },
                        -- H=9144m (30kft)
                        { 29753, 28269, 27849, 28493, 29228, 30200, 30793, 31378, 31452 },
                        -- H=9754m (32kft) *** CALIBRATION POINT: tune [9] (M0.92) vs EFM ***
                        { 27582, 26207, 25817, 26413, 27095, 27976, 28546, 29088, 29157 },
                        -- H=12192m (40kft)
                        { 20184, 19178, 18892, 19340, 19828, 20487, 20889, 21286, 21337 },
                        -- H=14000m (~46kft)
                        { 16003, 15204, 14978, 15324, 15720, 16242, 16562, 16876, 16926 },
                    }
                }
            },
            -- {Mach, sea level thrust in Newtons}. Two columns, as there is no afterburner.
            -- extended replaces this for altitude scaling, but the engine still needs it.
            table_data =
            {
                { 0.00, 80415 },
                { 0.20, 76404 },
                { 0.40, 75268 },
                { 0.60, 77007 },
                { 0.70, 78995 },
                { 0.80, 81621 },
                { 0.85, 83224 },
                { 0.90, 84806 },
                { 0.92, 85006 },
            },
        },
    },

    ---------------------------------------------------------------------------
    -- Damage
    -- Cell numbers are listed in Scripts\Aircrafts\_Common\Damage.lua.
    -- args = main .edm draw arguments that show damaged parts.
    ---------------------------------------------------------------------------
    Damage = verbose_to_dmg_properties(
        {
            -- Every key must have a same-named ShellNode or SegmentsNode in the EDM, and every
            -- EDM collision name a key here, or DCS logs "Corrupt damage model".
            -- IDs follow DCS Damage.lua. Critical damage values are starting values, not calibrated.
            -- DCS alone owns these visibility arguments; the EFM consumes integrity callbacks.
            ["NOSE_CENTER"] = {critical_damage = 5, droppable = false}, -- 0
            ["COCKPIT"] = {critical_damage = 5, droppable = false}, -- 3: canopy and cockpit station
            ["FUSELAGE_LEFT_SIDE"] = {critical_damage = 10, droppable = false},  -- 9
            ["FUSELAGE_RIGHT_SIDE"] = {critical_damage = 10, droppable = false}, -- 10: same cell as MAIN
            ["FUSELAGE_BOTTOM"] = {critical_damage = 4, droppable = false}, -- 82: weapon bay doors
            ["ENGINE_L"] = {critical_damage = 8, droppable = false}, -- 11
            ["ENGINE_R"] = {critical_damage = 8, droppable = false}, -- 12
            ["TAIL_LEFT_SIDE"] = {critical_damage = 6, droppable = false, deps_cells = {"RUDDER_L"}},  -- 56
            ["TAIL_RIGHT_SIDE"] = {critical_damage = 6, droppable = false, deps_cells = {"RUDDER_R"}}, -- 57

            -- Fixed wing panels. Destroying a panel also destroys the surfaces it carries.
            ["WING_L_IN"] = {critical_damage = 8, droppable = false, deps_cells = {"WING_L_OUT", "FLAP_L"}}, -- 35
            ["WING_R_IN"] = {critical_damage = 8, droppable = false, deps_cells = {"WING_R_OUT", "FLAP_R"}}, -- 36
            ["WING_L_OUT"] = {critical_damage = 5, droppable = false, deps_cells = {"AILERON_L"}}, -- 23
            ["WING_R_OUT"] = {critical_damage = 5, droppable = false, deps_cells = {"AILERON_R"}}, -- 24

            -- Gear doors use the gear bay cells; wheels match damage_element in FM/config.lua.
            ["GEAR_F"] = {critical_damage = 3, droppable = false}, -- 8
            ["GEAR_L"] = {critical_damage = 4, droppable = false}, -- 15
            ["GEAR_R"] = {critical_damage = 4, droppable = false}, -- 16
            ["WHEEL_F"] = {critical_damage = 3, droppable = false}, -- 83
            ["WHEEL_L"] = {critical_damage = 3, droppable = false}, -- 84
            ["WHEEL_R"] = {critical_damage = 3, droppable = false}, -- 85

            -- Left_Wing / Right_Wing are outer elevons, not entire wing structures.
            ["AILERON_L"] = {critical_damage = 3, args = {1010}, droppable = false}, -- 25
            ["AILERON_R"] = {critical_damage = 3, args = {1015}, droppable = false}, -- 26
            ["FLAP_L"] = {critical_damage = 3, args = {1011}, droppable = false},    -- 37
            ["FLAP_R"] = {critical_damage = 3, args = {1014}, droppable = false},    -- 38
            ["RUDDER_L"] = {critical_damage = 4, args = {247}, droppable = false},  -- 53
            ["RUDDER_R"] = {critical_damage = 4, args = {248}, droppable = false},  -- 54
        }
    ),

    ---------------------------------------------------------------------------
    -- Extra aircraft options on the ME payload screen
    ---------------------------------------------------------------------------
    AddPropAircraft = {
        {
            id = "HelmetMountedDevice", -- Option key saved in the mission
            control = "comboList", -- Widget type
            label = _("Helmet Mounted Device"), -- Option label
            values = {
                {id = 0, dispName = _("Not installed"), value = 0.5}, -- value is applied to arg in the ME preview
                {id = 1, dispName = _("NVG"), value = 1.0},
            },
            defValue = 1, -- Default option id
            wCtrl = 150, -- Widget width
            playerOnly = true, -- Hidden for AI aircraft
            arg         = 509, -- Model draw argument for the ME preview
        },
    }
}

add_aircraft(F_117_NightHawk)