dofile(LockOn_Options.script_path .. "devices.lua")
dofile(LockOn_Options.script_path.."materials.lua")

attributes = {
    "avNightVisionGogglesV2",
}

MainPanel = {"ccMainPanel", LockOn_Options.script_path .. "mainpanel_init.lua"}

creators = {}
creators[devices.NVG]                    = {"avNightVisionGogglesV2", LockOn_Options.script_path.. "HELMET/NVG.lua"}
creators[devices.LIGHTS]                 = {"avLuaDevice", LockOn_Options.script_path.. "Systems/lights_system.lua"}
creators[devices.MISCFUNC]               = {"avLuaDevice", LockOn_Options.script_path.. "Systems/MiscFunc.lua"}
creators[devices.BOMB_BAY]               = {"avLuaDevice", LockOn_Options.script_path.. "Systems/bomb_bay.lua"}
creators[devices.TAILHOOK]               = {"avLuaDevice", LockOn_Options.script_path.. "Systems/tailhook.lua"}
creators[devices.HUD]                    = {"avLuaDevice", LockOn_Options.script_path.."HUD/Device/HUD_Device.lua"}
creators[devices.DISPLAYS]               = {"avLuaDevice", LockOn_Options.script_path.."Systems/Displays.lua"}
creators[devices.FC3]                    = {"avLuaDevice", LockOn_Options.script_path.."Systems/FC3.lua"}
creators[devices.GAUGES]                 = {"avLuaDevice", LockOn_Options.script_path.."Systems/Gauges.lua"}
creators[devices.WEAPONS]                = {"avSimpleWeaponSystem", LockOn_Options.script_path.."Systems/Weapons.lua"}

indicators = {}

-- Center MFD DLIR camera background (COMMON type renders 3D camera feed)
-- Must be listed BEFORE the overlay so it renders underneath.
indicators[#indicators + 1] = {"ccIndicator", LockOn_Options.script_path.."MFD/Indicator/DLIR_Camera_init.lua",
 devices.DISPLAYS,
    {
        {"MFD-PLASHKA-CENTER", "MFD-PLASHKA-DOWN", "MFD-PLASHKA-RIGHT"},
        {sx_l =  0,
         sy_l =  0,
         sz_l =  0,
         sh   =  0,
         sw   =  0,
         rz_l =  0,
         rx_l =  0,
         ry_l =  0}
    }
}

indicators[#indicators + 1] = {"ccIndicator", LockOn_Options.script_path.."MFD/Indicator/MFD_indication_init.lua",
 devices.DISPLAYS,
    {
        {"MFD-PLASHKA-CENTER", "MFD-PLASHKA-DOWN", "MFD-PLASHKA-RIGHT"},
        {sx_l =  0,
         sy_l =  0,
         sz_l =  0,
         sh   =  0,
         sw   =  0,
         rz_l =  0,
         rx_l =  0,
         ry_l =  0}
    }
}

indicators[#indicators + 1] = {"ccIndicator", LockOn_Options.script_path.."HUD/Indicator/HUD_init.lua", --init script
 nil,
    {
        -- Using ILS-PLASHKA connectors as a stand-in until dedicated HUD connectors are added to the EDM.
        -- Fine-tune position with the sx_l/sy_l/sz_l offsets below once the HUD is visible.
        {"ILS-PLASHKA-CENTER", "ILS-PLASHKA-DOWN", "ILS-PLASHKA-RIGHT"},  -- initial geometry anchor , triple of connector names.
        {sx_l =  0,  -- center position correction in meters (+forward , -backward)
         sy_l =  0.03,  -- was 0.05 center position correction in meters (+up , -down)
         sz_l =  0,  -- center position correction in meters (-left , +right)
         sh   =  0,  -- half height correction 
         sw   =  0,  -- half width correction 
         rz_l =  0,  -- rotation corrections  
         rx_l =  0,
         ry_l =  0}
    }   
}

-- Left colour VSD, using the calibrated left screen connector frame.
indicators[#indicators + 1] = {
    "ccIndicator", LockOn_Options.script_path.."MFD/Indicator/Left/Left_init.lua",
    devices.DISPLAYS,
    {
        {"MFD-PLASHKA-CENTER1", "MFD-PLASHKA-DOWN1", "MFD-PLASHKA-RIGHT1"},
        {sx_l=0,sy_l=0,sz_l=0,sh=0,sw=0,rz_l=0,rx_l=0,ry_l=0}
    }
}

-- Right basic HSD on the calibrated right screen connector frame.
indicators[#indicators + 1] = {
    "ccIndicator", LockOn_Options.script_path.."MFD/Indicator/Right/Right_init.lua",
    devices.DISPLAYS,
    {
        {"RADAR-PLASHKA-CENTER", "RADAR-PLASHKA-DOWN", "RADAR-PLASHKA-RIGHT"},
        {sx_l=0,sy_l=0,sz_l=0,sh=0,sw=0,rz_l=0,rx_l=0,ry_l=0}
    }
}

-- Holders stay invisible until the native compositor commits all three bakes.
-- Source indicators retain GENERAL drawing if the module cannot initialize.
local display_config=dofile(LockOn_Options.script_path.."MFD/Indicator/render_config.lua")
if display_config.enabled then
    local function holder(kind,connectors)
        indicators[#indicators+1]={"ccIndicator",
            LockOn_Options.script_path.."MFD/Indicator/LCD/"..kind.."_init.lua",
            devices.DISPLAYS,{connectors,{sx_l=0,sy_l=0,sz_l=0,sh=0,sw=0,rz_l=0,rx_l=0,ry_l=0}}}
    end
    holder("centre",{"MFD-PLASHKA-CENTER","MFD-PLASHKA-DOWN","MFD-PLASHKA-RIGHT"})
    holder("left",{"MFD-PLASHKA-CENTER1","MFD-PLASHKA-DOWN1","MFD-PLASHKA-RIGHT1"})
    holder("right",{"RADAR-PLASHKA-CENTER","RADAR-PLASHKA-DOWN","RADAR-PLASHKA-RIGHT"})
end

-- Temporary independent calibration pages, drawn after the normal displays.
-- Side calibration is disabled by default now that VSD/HSD are registered.
local calibration = dofile(LockOn_Options.script_path.."Calibration/config.lua")
if calibration.enabled then
    local function add_calibration(kind, connectors, device, mount)
        if not calibration[kind].enabled then return end
        indicators[#indicators+1] = {
            "ccIndicator", LockOn_Options.script_path.."Calibration/"..kind.."_init.lua",
            device, {connectors, mount or {sx_l=0,sy_l=0,sz_l=0,sh=0,sw=0,rz_l=0,rx_l=0,ry_l=0}}
        }
    end
    add_calibration("centre", {"MFD-PLASHKA-CENTER","MFD-PLASHKA-DOWN","MFD-PLASHKA-RIGHT"}, devices.DISPLAYS)
    add_calibration("left", {"MFD-PLASHKA-CENTER1","MFD-PLASHKA-DOWN1","MFD-PLASHKA-RIGHT1"}, devices.DISPLAYS)
    add_calibration("right", {"RADAR-PLASHKA-CENTER","RADAR-PLASHKA-DOWN","RADAR-PLASHKA-RIGHT"}, devices.DISPLAYS)
    add_calibration("hud", {"ILS-PLASHKA-CENTER","ILS-PLASHKA-DOWN","ILS-PLASHKA-RIGHT"}, nil, calibration.hud.mount)
end
