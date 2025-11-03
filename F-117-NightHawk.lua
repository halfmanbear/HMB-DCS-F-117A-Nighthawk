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
            file = "f-117-nighthawk", --mods shape file
            life = 20,
            vis = 3,
            desrt = "f-117-nighthawk-oblomok", -- using Mods destruction file
            fire = {300, 2}, -- Fire on the ground after destoyed: 300sec 2m
            username = "F-117-NightHawk", -- Must be same as Name
            index = F_117_NightHawk;
            classname   = "lLandPlane";
            positioning = "BYNORMAL";
        },
        {
        classname = "lLandPlane",
        name  = "f-117-nighthawk-oblomok";
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
                    {_('Specter'),          'Specter'},
                    {_('Goblin'),           'Goblin'},
                    {_('Diamond'),          'Diamond'},
        }
    },
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    -- add model draw args for network transmitting to this draw_args table (32 limit)
    net_animation = {
        22, -- Refuel Bay
        26, -- Bomb bay
        35, -- Drag Chute
        36, -- Drag Chute Wind
        38, -- Canopy
        190, -- Taxi Light
        191, -- Wing lights
        192, -- Landing Lights
        193, -- Beacon Light
        224, -- left wing Damage
        247, -- Left rudder damage 
        248, -- Right rudder damage
        1000, -- Meme Light
        1001, -- Beacon Rotate
        1010, -- left elevon damage (outer)
        1011, -- left elevon damage (inner)
        1014, -- right elevon damage (inner)
        1015, -- right elevon damage (outer)
    },
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    M_empty = 13380, --KG
    M_nominal = 18000, --KG, calculated as half fuel and combat load of 2x 2000lb bombs.
    M_max = 23810, --KG
    M_fuel_max = 8255, --KG
    H_max = 13700, --Meters
    average_fuel_consumption = 0.184,
    bigParkingRamp = false,
    CAS_min = 64,
    V_opt = 230,
    V_take_off = 85,    
    V_land = 77,
    has_afteburner = false,
    has_speedbrake = false,
    main_gear_pos = {-0.292856, -2.055, 2.095716}, -- -0.942, -1.98, 2.449,
    radar_can_see_ground = false,
    nose_gear_pos = {5.0765, -2.020, 0}, -- 4.913, -1.99, 0 ---2.050
    AOA_take_off = 0.14,
    AmmoWeight = 0,
    stores_number = 3, --2
    bank_angle_max = 60,
    Ny_min = -2,
    Ny_max = 6,
    tand_gear_max = math.rad(45), --0.785
    V_max_sea_level = 292,
    V_max_h = 289, 
    tanker_type = 1, --boom
    wing_area = 72, -- From P19-21283_F117 Fast Facts_FINAL_1 - One research paper states 105.9
    wing_span = 13.2,
    _MAC_compatible = true,
    _file = current_mod_path .. "/F-117NightHawk.lua",
    _file_flyable = current_mod_path .. "/entry.lua",
    swapped_names = true,
    WorldID =  WSTYPE_PLACEHOLDER,
    thrust_sum_max = 9800,
    thrust_sum_ab = 9800,
    Vy_max = 30,
    length = 20.08,
    height = 3.78,
    flaps_maneuver = 0,
    wing_type = 0,
    Mach_max = 0.92,
    Rate = "70",
    WingSpan = 13.2,
    EmptyWeight = 13380,
    MaxFuelWeight = 8255,
    MaxHeight = 13700,
    MaxSpeed = 1000,
    MaxTakeOffWeight = 23810,
    country_of_origin = "USA",
    range = 2000,
    RCS = 0.003,
    Ny_max_e = 5.5,
    detection_range_max = 0,
    IR_emission_coeff = 0.15,
    IR_emission_coeff_ab = 0,
    wing_tip_pos = {-6.627, -0.265, 6.6}, --For Visual Effects
    nose_gear_wheel_diameter = 0.5588, -- 22inch = 0.5588m --0.754
    main_gear_wheel_diameter = 0.8128, -- 32inch = 0.8128m --0.972
    brakeshute_name = 3,
    air_refuel_receptacle_pos = {2.356, 1.119, 0.0},
    engines_count = 2,
    engines_nozzles = { 
        [1] = {
            pos = {-4.604, 0.039, -1.427},
            elevation = 0,
            diameter = 0.40,
            exhaust_length_ab = 0,
            exhaust_length_ab_K = 0.76,
            smokiness_level = 0.02
        },
        [2] = {
            pos = {-4.604, 0.039, 1.427},
            elevation = 0,
            diameter = 0.40,
            exhaust_length_ab = 0,
            exhaust_length_ab_K = 0.76,
            smokiness_level = 0.02
        },
    },
    crew_size = 1, --exp
    crew_members = {
        [1] = {
            ejection_seat_name = 17,
            drop_canopy_name = "f-117-nighthawk_canopy",
            pos = {5.213, 0.744, 0},
            canopy_pos = {4.5, 1, 0},
            g_suit =  2.0,
            can_be_playable = true,
            canopy_arg = 38,
            --ejection_order = 1,
            --role = "pilot",
            --role_display_name = "Pilot",
            --ejection_added_speed = {-5, 15, 0},
        },
        [2] = { --required to prevent player ejection crash (although causes ai to eject two pilots)
            can_be_playable = false,
            ejection_seat_name = 17,
        }
    },
    fires_pos = { { -0.865, 1.01, 1 }, { -0.37, -0.23, 3.01 }, { -0.37, -0.23, -3.01 }, { -0.82, 0.265, 2.774 }, { -0.82, 0.265, -2.774 }, { -0.82, 0.255, 4.274 }, { -0.82, 0.255, -4.274 }, { -4.45, 0.08, 1.7 }, { -4.45, 0.08, -1.7 }, { 2, -0.56, -1 }, { -4.08, 0.22, 0 } },
    effects_presets = {
        {effect = "OVERWING_VAPOR", file = current_mod_path.."/Effects/f-117-nighthawk_overwingVapor.lua"},
    },
    CanopyGeometry = {
        azimuth = {-160.0, 160.0}, -- pilot view horizontal (AI)
        elevation = {-50.0, 90.0} -- pilot view vertical (AI)
    },
    Sensors = {
        OPTIC = {"IRADS"}, --"IRADS","Shkval", "Merkury LLTV", "LANTIRN AAQ-14 FLIR" --exp
        --RWR = "Abstract RWR",
    },
    laserEquipment = {
        laserDesignator = true,
        laserRangefinder = true,
    },
    Pylons = {
        pylon(
            1,
            2,
            0,
            0,
            0,
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
            2,
            2,
            0,
            0,
            0,
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
            3,
            2, --exp was 0
            0,
            0,
            0,
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
    SFM_Data = {
      aerodynamics = {
        Cy0       = 0.0,
        Czbe      = -0.012,  
        Mzalfa    = 6.6,    
        Mzalfadt  = 1.0,
        cx_brk    = 0.025,   
        --cx_flap   = 0.035,  
        cx_gear   = 0.006,  
        --cy_flap   = 0.28,     
        kjx       = 2.85,    
        kjz       = 0.00125,  
        --  { Mach,  Cx0,   Cya,   B,     B4,    Omx,  Aldop,  Cymax }
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
        ForsRUD = 0, MaksRUD = 1, MaxRUD = 1, MinRUD = 0,
        Nmg     = 60.00001,      
        type    = "TurboFan",
        dcx_eng = 0.0085,    
        dpdh_m  = 4200,       
        dpdh_f  = 4200,      
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

    Damage = verbose_to_dmg_properties(
        {
          ["WHEEL_F"]        = {critical_damage = 3},
          ["WHEEL_L"]        = {critical_damage = 3},
          ["WHEEL_R"]        = {critical_damage = 3},

          -- Elevons (break-off)
          ["FLAP_L_OUT"]     = {critical_damage = 3, args = {1010}}, -- L outer elevon off
          ["FLAP_L_ CENTER"] = {critical_damage = 3, args = {1011}}, -- L inner elevon off
          ["FLAP_R_ CENTER"] = {critical_damage = 3, args = {1014}}, -- R inner elevon off
          ["FLAP_R_OUT"]     = {critical_damage = 3, args = {1015}}, -- R outer elevon off

          -- Rudders (break-off)
          ["RUDDER_L"]       = {critical_damage = 3, args = {247}},  -- L rudder off
          ["RUDDER_R"]       = {critical_damage = 3, args = {248}},  -- R rudder off

          -- existing fuselage cells
          ["FUSELAGE_BOTTOM"]= {critical_damage = 3},
          ["FUSELAGE_TOP"]   = {critical_damage = 3},
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