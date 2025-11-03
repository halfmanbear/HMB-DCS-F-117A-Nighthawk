dofile(LockOn_Options.script_path .. "devices.lua")

attributes = {
    "support_for_cws", --Disabling breaks HUD / instruments, Enabling breaks NVG implementation
}

MainPanel = {"ccMainPanel", LockOn_Options.script_path .. "mainpanel_init.lua"}

creators = {}
creators[devices.HELMET_DEVICE]          = {"avNightVisionGogglesV2"}
creators[devices.LIGHTS]                 = {"avLuaDevice", LockOn_Options.script_path .. "Systems/lights_system.lua"}
creators[devices.MiscFunc]               = {"avLuaDevice", LockOn_Options.script_path .. "Systems/MiscFunc.lua"}
creators[devices.BOMB_BAY]               = {"avLuaDevice", LockOn_Options.script_path .. "Systems/bomb_bay.lua"}

indicators = {}