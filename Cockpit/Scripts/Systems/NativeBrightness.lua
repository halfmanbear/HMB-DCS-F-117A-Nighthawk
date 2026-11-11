-- Native renderer brightness, independent of the optional MFD compositor.
local M={}
function M.new()
    local native,last_message
    local active=get_param_handle("F117_NATIVE_BRIGHTNESS_ACTIVE")
    local hud=get_param_handle("HUDBrightness")
    local left=get_param_handle("LDBrightness")
    local right=get_param_handle("RDBrightness")
    local irads=get_param_handle("F117_IRADS_BRIGHTNESS")
    local centre=get_param_handle("CDBrightness")
    local eo=get_param_handle("F117_LEFT_EO")
    local eo_dim=get_param_handle("F117_LEFT_EO_DIM_OPACITY")
    local map_dim=get_param_handle("F117_MAP_DIM_OPACITY")
    local hud_draw=get_param_handle("F117_HUD_DRAW_BRIGHTNESS")
    -- The DEP follows the HUD brightness control (manual 4-4), scaled by its
    -- time-of-day default so it is not full bright at night.
    local dep=get_param_handle("F117_DEP_BRIGHTNESS")
    local dep_draw=get_param_handle("F117_DEP_DRAW_BRIGHTNESS")
    local irads_draw=get_param_handle("F117_IRADS_DRAW_BRIGHTNESS")
    local left_dim=get_param_handle("F117_LEFT_DIM_OPACITY")
    local right_dim=get_param_handle("F117_RIGHT_DIM_OPACITY")
    local video_dim=get_param_handle("F117_IRADS_DIM_OPACITY")
    -- Power-up fades from Systems/Electrical.lua scale every channel.
    local fade={}
    for _,name in ipairs({"HUD","CMDI_L","CMDI_R","SD","DEP"}) do fade[name]=get_param_handle("F117_FADE_"..name) end
    local function f(name) local v=fade[name]:get();return v<0 and 0 or v>1 and 1 or v end
    local function report(message)
        if message==last_message then return end
        last_message=message
        if log then log.write("F117_BRIGHTNESS",log.INFO,message) end
    end
    local function update()
        local enabled=false
        local fl,fr,fs=f("CMDI_L"),f("CMDI_R"),f("SD")
        local hud_gain,dep_gain=hud:get()*f("HUD"),hud:get()*dep:get()*f("DEP")
        local left_gain=1-left:get()
        if eo:get()==1 then left_gain=math.min(left_gain,irads:get()) end
        left_gain=left_gain*fl
        local right_gain=(1-right:get())*fr
        local irads_gain=irads:get()*fs
        if native then
            -- Channel order: HUD, CMDI-L, CMDI-R, SD symbology, SD video, DEP.
            local ok,ready,message=pcall(native.update,hud_gain,left_gain,right_gain,irads_gain,irads_gain,dep_gain)
            enabled=ok and ready==true
            report(ok and tostring(message) or "native brightness error: "..tostring(ready))
        end
        active:set(enabled and 1 or 0)
        hud_draw:set(enabled and 1 or hud_gain)
        dep_draw:set(enabled and 1 or dep_gain)
        irads_draw:set(enabled and 1 or irads_gain)
        left_dim:set(enabled and 0 or 1-(1-left:get())*fl)
        right_dim:set(enabled and 0 or 1-right_gain)
        video_dim:set(enabled and 0 or 1-irads_gain)
        eo_dim:set(enabled and 0 or 1-left_gain)
        map_dim:set(enabled and 0 or 1-right_gain)
    end
    local function initialize()
        active:set(0)
        if package and package.loadlib then
            local loader=package.loadlib(LockOn_Options.script_path.."../../bin/F117Displays.dll","luaopen_f117_brightness")
            if loader then
                local ok,module=pcall(loader)
                if ok and type(module)=="table" and type(module.update)=="function" then native=module end
            end
        end
        if not native then report("native brightness module unavailable; existing dimming retained") end
        update()
    end
    return {initialize=initialize,update=update}
end
return M
