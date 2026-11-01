-- Called from the display device's cockpit lifecycle, never the EFM simulation.
local M={}
function M.new()
    local ready=get_param_handle("F117_LCD_READY")
    local native,attempts,last_message=nil,0,nil
    local config=dofile(LockOn_Options.script_path.."MFD/Indicator/render_config.lua")
    local function report(message)
        if message==last_message then return end
        last_message=message
        if log then log.write("F117_DISPLAYS",log.INFO,message) end
    end
    local function update()
        if not native or attempts>=200 then return end
        attempts=attempts+1
        local options=LockOn_Options.cockpit or {}
        local resolution=config.resolution or options.render_target_resolution or 1024
        local called,active,message
        if config.bake_test and not config.enabled then
            called,active,message=pcall(native.start,resolution,1)
        else
            called,active,message=pcall(native.start,resolution)
        end
        if not called then
            report("native compositor error: "..tostring(active).."; direct drawing retained")
            native=nil
            return
        end
        report(tostring(message))
        if active then attempts=200 end
        if attempts==200 and not active then report("initialisation timed out; direct drawing retained") end
    end
    local function initialize()
        ready:set(0)
        local test_ready=get_param_handle("F117_LCD_TEST_READY")
        test_ready:set(0)
        if config.holder_test and not config.enabled and not config.bake_test then
            test_ready:set(1)
            report("centre holder static-texture test active; native compositor disabled; direct sources retained")
            return
        end
        if not config.enabled and not config.bake_test then report("native compositor disabled; direct drawing retained");return end
        if config.bake_test and not config.enabled then
            if config.bake_test_direct then
                report("centre diagnostic source="..tostring(config.bake_test_source).." direct comparison active; native bake not started")
                return
            end
            report("centre native bake test requested; ordinary three-screen compositor disabled")
            local source=config.bake_test_source
            report("centre native bake test source="..((source=="map" or source=="text") and source or "pattern"))
            if source=="map" or source=="text" then
                report("centre "..source.." bake stroke specular pass="..tostring(config.bake_test_specular~=false))
                report("centre "..source.." bake text class=ceStringSLine; indicator stroke scaling enabled")
            end
        end
        if not package or not package.loadlib then report("package.loadlib unavailable; direct drawing retained");return end
        local loader,reason=package.loadlib(LockOn_Options.script_path.."../../bin/F117Displays.dll","luaopen_f117_displays")
        if not loader then report("module unavailable: "..tostring(reason).."; direct drawing retained");return end
        local ok,module=pcall(loader)
        if not ok or type(module)~="table" or type(module.start)~="function" then
            report("module initialization failed; direct drawing retained");return
        end
        native=module -- closures retain native userdata until this device's Lua state closes
        update()
    end
    return {initialize=initialize,update=update}
end
return M
