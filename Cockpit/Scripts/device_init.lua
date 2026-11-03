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
creators[devices.ELECTRICAL]             = {"avLuaDevice", LockOn_Options.script_path.."Systems/Electrical.lua"}

indicators = {}

local display_config=dofile(LockOn_Options.script_path.."MFD/Indicator/render_config.lua")
-- A bake fills its texture from the source indicator's extents, and the holder
-- shows that texture on its own quad. Match the two or a circle draws as an oval.
local function source_mount(kind,sx_l,sy_l)
    local output=display_config[kind]
    return {sx_l=sx_l,sy_l=sy_l,sz_l=0,
        sh=output.half_height-output.connector_half_height,
        sw=output.half_width-output.connector_half_width,
        rz_l=0,rx_l=0,ry_l=0}
end

-- Centre green IRADS camera; target 0 also supplies the left grayscale repeater.
-- Must be listed BEFORE the overlay so it renders underneath.
indicators[#indicators + 1] = {"ccIndicator", LockOn_Options.script_path.."MFD/Indicator/DLIR_Camera_init.lua",
 devices.DISPLAYS,
    {
        {"SD-CENTER", "SD-DOWN", "SD-RIGHT"},
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
        {"SD-CENTER", "SD-DOWN", "SD-RIGHT"},
        source_mount("centre",0,0)
    }
}

indicators[#indicators + 1] = {"ccIndicator", LockOn_Options.script_path.."HUD/Indicator/HUD_init.lua", --init script
 nil,
    {
        {"HUD-CENTER", "HUD-DOWN", "HUD-RIGHT"},  -- initial geometry anchor , triple of connector names.
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

-- Side connector planes cross the measured screen meshes by fractions of a
-- millimetre. Move the artwork ~1.1 mm toward the pilot (1 mm aft, 0.5 mm up),
-- retaining depth testing so cockpit objects can still obscure the displays.
-- Left colour VSD, using the calibrated left screen connector frame.
indicators[#indicators + 1] = {
    "ccIndicator", LockOn_Options.script_path.."MFD/Indicator/Left/Left_init.lua",
    devices.DISPLAYS,
    {
        {"CMDI-L-CENTER", "CMDI-L-DOWN", "CMDI-L-RIGHT"},
        source_mount("left",-0.001,0.0005)
    }
}

-- Right colour CMDI, default MAP, on the calibrated connector frame.
indicators[#indicators + 1] = {
    "ccIndicator", LockOn_Options.script_path.."MFD/Indicator/Right/Right_init.lua",
    devices.DISPLAYS,
    {
        {"CMDI-R-CENTER", "CMDI-R-DOWN", "CMDI-R-RIGHT"},
        source_mount("right",-0.001,0.0005)
    }
}

-- Holders stay invisible until the native compositor commits all three bakes.
-- Source indicators retain GENERAL drawing if the module cannot initialize.
if display_config.enabled or display_config.holder_test or display_config.bake_test then
    local function holder(kind,connectors,mount)
        indicators[#indicators+1]={"ccIndicator",
            LockOn_Options.script_path.."MFD/Indicator/LCD/"..kind.."_init.lua",
            devices.DISPLAYS,{connectors,mount}}
    end
    holder("centre",{"SD-CENTER","SD-DOWN","SD-RIGHT"},
        {sx_l=0,sy_l=0,sz_l=0,sh=0,sw=0,rz_l=0,rx_l=0,ry_l=0})
    if display_config.enabled then
        -- Same clearance as the side source pages, or the screen mesh cuts through the image.
        holder("left",{"CMDI-L-CENTER","CMDI-L-DOWN","CMDI-L-RIGHT"},
            {sx_l=-0.001,sy_l=0.0005,sz_l=0,sh=0,sw=0,rz_l=0,rx_l=0,ry_l=0})
        holder("right",{"CMDI-R-CENTER","CMDI-R-DOWN","CMDI-R-RIGHT"},
            {sx_l=-0.001,sy_l=0.0005,sz_l=0,sh=0,sw=0,rz_l=0,rx_l=0,ry_l=0})
    end
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
    add_calibration("centre", {"SD-CENTER","SD-DOWN","SD-RIGHT"}, devices.DISPLAYS)
    add_calibration("left", {"CMDI-L-CENTER","CMDI-L-DOWN","CMDI-L-RIGHT"}, devices.DISPLAYS)
    add_calibration("right", {"CMDI-R-CENTER","CMDI-R-DOWN","CMDI-R-RIGHT"}, devices.DISPLAYS)
    add_calibration("hud", {"HUD-CENTER","HUD-DOWN","HUD-RIGHT"}, nil, calibration.hud.mount)
end


-- Data entry panel, drawn directly. The same 1.1 mm clearance toward the pilot
-- as the side displays keeps the artwork in front of the DEP glass.
indicators[#indicators+1]={"ccIndicator",LockOn_Options.script_path.."DEP/Indicator/DEP_init.lua",
    devices.DISPLAYS,{{"DEP-CENTER","DEP-DOWN","DEP-RIGHT"},
    {sx_l=-0.001,sy_l=0.0005,sz_l=0,sh=0,sw=0,rz_l=0,rx_l=0,ry_l=0}}}

-- Independent generic DCS chart source. Keep the first five indicators stable.
-- The third indicator parameter is one-based: DCS stores it minus one as the target.
local charts=dofile(LockOn_Options.script_path.."MFD/Indicator/Map/Charts/config.lua")
if charts.enabled then
    creators[devices.MAP_CHARTS]={"avKneeboard",LockOn_Options.script_path.."MFD/Indicator/Map/Charts/device.lua"}
    indicators[#indicators+1]={"ccKneeboard",LockOn_Options.script_path.."MFD/Indicator/Map/Charts/init.lua",
        devices.MAP_CHARTS,{{},{sx_l=0,sy_l=0,sz_l=0,sw=-.039,sh=-.051},charts.render_target+1}}
end
