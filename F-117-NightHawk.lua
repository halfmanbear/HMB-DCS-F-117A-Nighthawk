F_117_NightHawk = {
    Name = "F-117-NightHawk",
    DisplayName = _("F-117A Nighthawk"),
    HumanCockpit = true,
    HumanCockpitPath = current_mod_path .. "/Cockpit/Scripts",
    HumanCommPanelPath = current_mod_path .. "/comm.lua", --exp
    Picture = "F-117A.png",
    Shape = "f-117-nighthawk", --mods shape file
    shape_table_data = {
        {
            file = "f-117-nighthawk", -- mods main .edm shape file
            life = 12,
            vis = 3, -- visibility gain.
            desrt = "f-117-nighthawk-oblomok", -- Name of destroyed object .edm file
            fire = {300, 2}, -- Fire on the ground after destoyed: 300sec 2m
            username = "F-117-NightHawk", -- Must be same as Name
            index = F_117_NightHawk;
            classname   = "lLandPlane";
            positioning = "BYNORMAL";
        },
        {
            classname = "lLandPlane",
            name  = "f-117-nighthawk-oblomok"; --edm name
            file  = "f-117-nighthawk-oblomok"; --using Mods destruction file
            fire  = { 0, 1};
            positioning = "BYNORMAL";
        },
    },
    DamageParts = { --exp
        [1] = "f-117-nighthawk-oblomok-wing-r", --using Mods destruction file
        [2] = "f-117-nighthawk-oblomok-wing-l", --using Mods destruction file
    },
    Countries = {"USA"},
    mapclasskey = "P0091000027", --from DCS F-117A
    attribute = {wsType_Air, wsType_Airplane, wsType_Fighter, WSTYPE_PLACEHOLDER, "Bombers", "Refuelable", "All", "NonAndLightArmoredUnits", "NonArmoredUnits", "Air", "Planes", "Battle airplanes"}, --from DCS F-117A required for Ai Bombing
    Categories = {},
    InheriteCommonCallnames = false,
    SpecificCallnames = {
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
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    -- add model draw args for network transmitting to this draw_args table (32 limit) - Note: 8 animations too many
    net_animation = {
        0,  -- nose gear
        1,  -- nose gear strut
        2,  -- nose wheel steering
        3,  -- right gear 
        4,  -- right gear strut
        5,  -- left gear
        6,  -- left gear strut
        9,  -- (coupled) right rudder & elevon
        10, -- (coupled) left rudder & elevon
        11, -- right elevon
        12, -- left elevon
        15, -- right elevon (mixed)
        16, -- left elevon (mixed)
        18, -- rudder
        22, -- Refuel Bay
        --25, -- Hook -- note main .edm doesnt have this integrated yet
        26, -- Bomb bay
        35, -- Drag Chute
        36, -- Drag Chute Wind
        38, -- Canopy
        39, -- Pilot Head Move
        --50, -- Pilot remove
        101,-- Nose wheel rotate
        102,-- Left wheel rotate
        103,-- Right wheel rotate
        --114,-- Remove entire cockpit
        190,-- Taxi Light
        191,-- Wing lights
        192,-- Landing Lights
        193,-- Beacon Light
        --224,-- left wing Damage
        --247,-- Left rudder damage 
        --248,-- Right rudder damage
        --903,-- IRADS rotate
        --1000,-- Meme Light
        1001,-- Beacon Rotate
        --1010,-- left elevon damage (outer)
        --1011,-- left elevon damage (inner)
        --1014,-- right elevon damage (inner)
        --1015,-- right elevon damage (outer)
    },
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
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
    -- SOURCES - Research / white papers:
    -- Development of the F-117 Flight Control System by Robert Loschke (AIAA 2003-5762)
    -- SOURCES - Books:
    --
    -- Skunk Works: A Personal Memoir of My Years at Lockheed (by Ben R. Rich, Leo Janos)
    -- F-117 Nighthawk Stealth Fighter: An Illustrated Developmental History (by Yancy D. Mailes, Tony R. Landis)
    --
    --Max payload = 2268, --kg : 5000lb
    --Typical combat payload = 1814, --kg : 4000 lb
    M_empty = 13381, --kg : 29500 lb
    M_nominal = 19278, --kg : =(M_empty + ((M_fuel_max/2) + typical_combat_payload)
    M_max = 23814, --kg : 52500 lb
    M_fuel_max = 8255, --kg : M_max - M_empty - M_payload  NOTE: public info suggests 18200 lb / 8255 kg
    H_max = 13716, --m : 45000ft 
    average_fuel_consumption = 0.59, --0.184
    bigParkingRamp = false,
    CAS_min = 64, -- Min speed that is shwon in hud in m/s
    V_opt = 230, -- cruise speed in m/s
    V_take_off = 84.9,--m/s : Take-off speed (165 knots) 
    V_land = 77.2,--m/s : Landing Speed (150 knots)
    has_afteburner = false,
    has_speedbrake = false,
    main_gear_pos = {-0.292856, -2.055, 2.095716}, --(+forward/-back,+up/-down,+right/-left)
    radar_can_see_ground = false,
    nose_gear_pos = {5.0765, -2.020, 0}, --(+forward/-back,+up/-down,+right/-left)
    AOA_take_off = 0.14, -- AoA for take-off
    AmmoWeight = 0, -- no gun
    stores_number = 2, --number of pylons (for Ai)
    bank_angle_max = 60,
    Ny_min = -3, -- Min G
    Ny_max = 6, -- Max G
    tand_gear_max = math.rad(45), --0.785
    V_max_sea_level = 292, --m/s : Max speed at sea level
    V_max_h = 273, --m/s : Max speed at max altitude (45000ft)
    Waypoint_Custom_Panel = true,
    tanker_type = 1, --Boom type
    wing_area = 84.8, --m2 : 912.7 sq ft (84.8 m2), Lockheed state 780 sq ft (72 m2) - Research paper suggests 105.9 m2
    wing_span = 13.21, --m : 43ft4in (13.21 m)
    _MAC_compatible = true,
    _file = current_mod_path .. "/F-117NightHawk.lua",
    _file_flyable = current_mod_path .. "/entry.lua",
    swapped_names = true,
    WorldID =  WSTYPE_PLACEHOLDER,
    thrust_sum_max = 8200, -- thrust in kgf N = 9.80665 * 8200 = 80415N
    thrust_sum_ab = 8200, --thrust in kgf (with afterburner)
    Vy_max = 14.3, --m/s : Max climb speed
    length = 20.09, --m : 65ft11in (20.09 m)
    height = 3.78, --m : 12ft5in (3.78 m)
    flaps_maneuver = 0,
    wing_type = 0, -- FIXED_WING = 0 / VARIABLE_GEOMETRY = 1 / FOLDED_WING = 2 / VARIABLE_GEOMETRY_FOLDED = 3
    Mach_max = 0.92, --Mach : 684 mph (1,100 km/h; Mach 0.92 at 35000 ft (10668 meters))
    Rate = "70", --RewardPoint in Multiplayer
    WingSpan = 13.21, --m : 43ft4in (13.21 m)
    EmptyWeight = 13381, --kg : 29500 lb
    MaxFuelWeight = 8255, --kg : M_max - M_empty - M_payload  NOTE: public info suggests 18200 lb / 8255 kg
    MaxHeight = 13716, --m : 45000ft
    MaxSpeed = 1100, --km/h : 684 mph (1,100 km/h; Mach 0.92 at 35000 ft (10668 meters))
    MaxTakeOffWeight = 23814, --kg : 52500 lb
    country_of_origin = "USA",
    range = 1720, --km : ~930 nmi (1,720 km; 1,070 mi) combat radius
    RCS = 0.003, --m^2 : Radar Cross Section
    Ny_max_e = 5.5, --Max G (for AI)
    detection_range_max = 0, --nmi : Maximum distance in meters at which (AI) sensors can detect target
    IR_emission_coeff = 0.15, --IR_emission_coeff = 1 for reference aircraft Su-27
    IR_emission_coeff_ab = 0, --IR emmision coefficient when afterburner active
    wing_tip_pos = {-6.627, -0.265, 6.6}, --For Visual Effects (+forward/-back,height,+right/-left)
    nose_gear_wheel_diameter = 0.5588, --m : 22in = 0.5588m 
    main_gear_wheel_diameter = 0.8128, --m : 32in = 0.8128m 
    brakeshute_name = 3, --type of drag chute
    air_refuel_receptacle_pos = {2.356, 1.119, 0.0}, --(+forward/-back,+up/-down,+right/-left)
    engines_count = 2,
    engines_nozzles = { 
        [1] = { --Left exhaust nozzle
            pos = {-4.604, 0.039, -1.427}, --For Visual Effects (+forward/-back,height,+right/-left)
            elevation = 5, --vertical rotation in degrees
            azimuth= 15, -- horizontal rotation in degrees
            diameter = 0.585,
            exhaust_length_ab = 0.76,
            exhaust_length_ab_K = 0.76,
            smokiness_level = 0.02
        },
        [2] = { --Right exhaust nozzle
            pos = {-4.604, 0.039, 1.427}, --For Visual Effects (+forward/-back,height,+right/-left)
            elevation = 5, --vertical rotation in degree
            azimuth= -15, -- horizontal rotation in degrees
            diameter = 0.585,
            exhaust_length_ab = 0.76,
            exhaust_length_ab_K = 0.76,
            smokiness_level = 0.02
        },
    },
    crew_size = 1, --exp
    crew_members = {
        [1] = {
            ejection_seat_name = 17, --ejection seat model 
            drop_canopy_name = "f-117-nighthawk_canopy", --name of .edm file for canopy jettison
            pos = {5.213, 0.744, 0}, --(+forward/-back,+up/-down,+right/-left)
            canopy_pos = {4.5, 1, 0}, --(+forward/-back,+up/-down,+right/-left)
            g_suit =  5.0, --pilot g-suit type was 2.0
            --can_be_playable = true,
            --canopy_arg = 38, --Animation argument for canopy jettison arg=50 is pilot and seat arg=114 is dash
            --ejection_order = 1,
            --role = "pilot",
            --role_display_name = "Pilot",
            --ejection_added_speed = {-5, 15, 0},
        },
        [2] = { --required to prevent player ejection crash (although causes ai to eject two pilots)
            can_be_playable = false,
            ejection_seat_name = 17, --ejection seat model 
        },
    },
    fires_pos = { 
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
    effects_presets = {
        {effect = "OVERWING_VAPOR", file = current_mod_path.."/Effects/f-117-nighthawk_overwingVapor.lua"},
    },
    CanopyGeometry = {
        azimuth = {-160.0, 160.0}, -- pilot view horizontal (AI)
        elevation = {-50.0, 90.0} -- pilot view vertical (AI)
    },
    Sensors = {
        OPTIC = {"IRADS"}, --Targeting sensors (used by AI) was set to "Shkval"
    },
    laserEquipment = {
        laserDesignator = true,
        laserRangefinder = true,
    },
    Pylons = {
        pylon(
            1, --Pylon Order
            2, --Types: 0=direct,1=delayed, 2=invisible
            0, --X
            0, --Y
            0, --Z
            {
                use_full_connector_position = true,
                connector = "Pylon1",
                DisplayName = "1"
            },
            {
                {CLSID = "<CLEAN>"}, --,attach_point_position = {0.02, 0.00, 0.00}
                -- Laser Paveway III (primary historical)
                {CLSID = "{EF0A9419-01D6-473B-99A3-BEBDB923B14D}"}, --GBU-27
                -- Other LGBs (secondary/hypothetical)
                {CLSID = "{51F9AAE5-964F-4D21-83FB-502E3BFE5F8A}"}, --GBU-10
                {CLSID = "{DB769D48-67D7-42ED-A2BE-108D566C8B1E}"}, --GBU-12
                -- JDAMs (late-career / plausible)
                {CLSID = "GBU31_JDAM"},                             --GBU-31
                {CLSID = "GBU31_V3B_JDAM"},                         --GBU-31(V)3/B
                {CLSID = "GBU32_JDAM"},                             --GBU-32
                -- Maverick (hypothetical)
                {CLSID = "AGM_65_D"},                               --Maverick D 
                {CLSID = "AGM_65_L"},                               --Maverick E/L2
                -- JSOW (hypothetical) Ai Only
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
            2, --Pylon Order
            2, --Types: 0=direct,1=delayed, 2=invisible
            0, --X
            0, --Y
            0, --Z
            {
                use_full_connector_position = true,
                connector = "Pylon2",
                DisplayName = "2"
            },
            {
                {CLSID = "<CLEAN>"}, --,attach_point_position = {0.02, 0.00, 0.00}
                -- Laser Paveway III (primary historical)
                {CLSID = "{EF0A9419-01D6-473B-99A3-BEBDB923B14D}"}, --GBU-27
                -- Other LGBs (secondary/hypothetical)
                {CLSID = "{51F9AAE5-964F-4D21-83FB-502E3BFE5F8A}"}, --GBU-10
                {CLSID = "{DB769D48-67D7-42ED-A2BE-108D566C8B1E}"}, --GBU-12
                -- JDAMs (late-career / plausible)
                {CLSID = "GBU31_JDAM"},                             --GBU-31
                {CLSID = "GBU31_V3B_JDAM"},                         --GBU-31(V)3/B
                {CLSID = "GBU32_JDAM"},                             --GBU-32
                -- Maverick (hypothetical)
                {CLSID = "AGM_65_D"},                               --Maverick D 
                {CLSID = "AGM_65_L"},                               --Maverick E/L2
                -- JSOW (hypothetical) Ai Only
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
            3, --Pylon Order
            2, --Types: 0=direct,1=delayed, 2=invisible
            0, --X
            0, --Y
            0, --Z
            {},
            {
              --{CLSID = "{0519A264-0AB6-11d6-9193-00A0249B6F00}"}, --L-081 Fantasmagoria ELINT pod (unrealistic in this aircraft)
                {CLSID = "{B1EF6B0E-3D91-4047-A7A5-A99E7D8B4A8B}"}, --Mercury LLTV Pod (only required for IR / Night TGP view)
            }
        )
    },
    Tasks = {
        aircraft_task(GroundAttack),
        aircraft_task(PinpointStrike),
        aircraft_task(RunwayAttack),
    },
    DefaultTask = aircraft_task(PinpointStrike),
    -- F-117A Nighthawk — Simple Flight Model (SFM)
    --  • Max climb ≈ 2,800 fpm (~14.3 m/s) at typical combat weight (~44–48k lb)
    --  • Service ceiling ≈ 45,000 ft (~13.7 km) as climb rate → ~0–300 fpm
    --  • Max level speed ≈ M0.90–0.92 clean at altitude
    --  • Subsonic only (no AB), notable transonic drag rise near M~0.9
    --
    -- M   - Mach number
    -- Cx0 - Coefficient, drag, profile, of the airplane
    -- Cya - Normal force coefficient of the wing and body of the aircraft in the normal direction to that of flight. Inversely proportional to the available G-loading at any Mach value. (lower the Cya value, higher G available) per 1 degree AOA
    -- B2 - Polar 2nd power coeff
    -- B4 - Polar 4th power coeff
    -- Omxmax - roll rate, rad/s
    -- Aldop - Alfadop Max AOA at current M - departure threshold
    -- Cymax - Coefficient, lift, maximum possible (ignores other calculations if current Cy > Cymax)
    SFM_Data = {
      aerodynamics = {
        Cy0       = 0.0,
        Czbe      = -0.012,  
        Mzalfa    = 6.6,    
        Mzalfadt  = 1.0,
        --cx_brk    = 0.025, -- No speed brake 
        cx_gear   = 0.006, -- Landing gear drag  
        kjx       = 2.85,    
        kjz       = 0.00125,  
        --  { Mach,  Cx0,   Cya,   B2,     B4,    Omxmax,  Aldop,  Cymax }
        table_data = {
          {0.00, 0.0240, 0.065, 0.075, 0.120, 0.55, 30.0, 1.20},
          {0.20, 0.0240, 0.065, 0.075, 0.120, 1.50, 30.0, 1.20},
          {0.40, 0.0240, 0.067, 0.075, 0.120, 2.50, 30.0, 1.20},
          {0.60, 0.0245, 0.070, 0.075, 0.120, 3.30, 29.0, 1.18},
          {0.70, 0.0255, 0.073, 0.075, 0.120, 3.30, 28.0, 1.16},
          {0.80, 0.0275, 0.077, 0.075, 0.120, 3.30, 27.0, 1.14},
          {0.85, 0.0300, 0.079, 0.090, 0.125, 3.20, 26.0, 1.12},
          {0.90, 0.0335, 0.082, 0.120, 0.135, 3.00, 25.0, 1.10},
          {0.92, 0.0370, 0.083, 0.145, 0.140, 2.90, 24.5, 1.08},
          {0.95, 0.0415, 0.083, 0.170, 0.150, 2.70, 24.0, 1.06},
          {1.00, 0.0480, 0.085, 0.200, 0.160, 2.50, 23.5, 1.04},
        },
      },

      engine = {
        ForsRUD = 1, MaksRUD = 1, MaxRUD = 1, MinRUD = 0, --ForsRUD = 0
        Nmg     = 60.00001,      
        type    = "TurboFan",
        dcx_eng = 0.0085,    
        dpdh_m  = 4200, --8000     
        dpdh_f  = 4200, --8000      
        hMaxEng = 19.5,         
        cemax   = 1.24,
        cefor   = 2.56,
        table_data = {
          {0.00, 94200, 94200}, 
          {0.20, 92000, 92000},
          {0.40, 90000, 90000},
          {0.60, 87000, 87000},
          {0.70, 85000, 85000},
          {0.80, 82000, 82000},
          {0.85, 80500, 80500},
          {0.90, 79000, 79000},
          {0.92, 77500, 77500},
          {0.95, 75000, 75000},
          {1.00, 70500, 70500},
        },
      },
    },

    --damage_cells , index meaning see in  Scripts\Aircrafts\_Common\Damage.lua
    -- args {} = main EDM Animation args that show damaged parts
    Damage = verbose_to_dmg_properties(
        {
          ["COCKPIT"]  = {critical_damage = 3}, --["COCKPIT"] [3]
          ["ENGINE"] = {critical_damage = 10}, --["ENGINE"] [10]
          ["MAIN"] = {critical_damage = 3}, --["MAIN"] [11]
        }
    ),

    AddPropAircraft = {
        {
            id = "HelmetMountedDevice",
            control = "comboList",
            label = _("Helmet Mounted Device"),
            values = {
                {id = 0, dispName = _("Not installed"), value = 0.5},
                {id = 1, dispName = _("NVG"), value = 1.0},
            },
            defValue = 1,
            wCtrl = 150,
            playerOnly = true,
            arg         = 509,
        },
    }
}

add_aircraft(F_117_NightHawk)