-- Native generic chart producer; never depends on F18 or F15E classes.
local M={}
local logger=log
if not logger then
    local ok,value=pcall(require,"log")
    if ok then logger=value end
end
function M.new(source_config)
    local config=dofile(LockOn_Options.script_path.."MFD/Indicator/Map/Charts/config.lua")
    local owns_source=not source_config or (source_config.enabled and source_config.material=="mfd"..tostring(config.render_target))
    local levels=dofile(LockOn_Options.script_path.."Systems/ChartLevels.lua")
    local native,attempted,last_message,waiting_updates
    local handles={}
    local function h(n)
        if not handles[n] then handles[n]=get_param_handle("F117_MAP_"..n) end
        return handles[n]
    end
    local function report(message)
        if message~=last_message then
            last_message=message
            if logger and logger.write then logger.write("F117_CHARTS",logger.INFO,tostring(message)) end
        end
    end
    local function initialize()
        h("SOURCE_READY"):set(0);h("CHART_CAMERA_READY"):set(0)
        h("CHART_EXPERIMENTAL"):set(config.enabled and owns_source and 1 or 0)
        native=nil;attempted=false;last_message=nil;waiting_updates=0
    end
    local function update()
        if not config.enabled or not owns_source then return end
        h("SOURCE_READY"):set(0)
        if not attempted then
            attempted=true
            local loader=package and package.loadlib and package.loadlib(
                LockOn_Options.script_path.."../../bin/F117Displays.dll","luaopen_f117_charts")
            if loader then local ok,value=pcall(loader);if ok and type(value)=="table" then native=value end end
            if not native or type(native.update)~="function" then
                native=nil;report("native chart adapter unavailable; map fallback retained")
            end
        end
        if not native then return end
        if h("VIEW_VALID"):get()<.5 or get_param_handle("mainpower"):get()<.5 then
            h("CHART_CAMERA_READY"):set(0);return
        end
        -- Common terrain charts provide a PMAP-like background. Do not present
        -- it as a verified digital elevation-shaded Harris DMAP implementation.
        local theatre=get_terrain_related_data and get_terrain_related_data("name") or ""
        local level=levels.level(theatre,h("RANGE"):get())
        local ok,ready,message=pcall(native.update,h("VIEW_CENTER_X"):get(),h("VIEW_CENTER_Z"):get(),
            h("VIEW_UP_RAD"):get(),h("VIEW_WIDTH_M"):get(),h("VIEW_HEIGHT_M"):get(),level)
        if not ok then report(ready);h("CHART_CAMERA_READY"):set(0);return end
        h("CHART_LEVEL"):set(level);h("CHART_CAMERA_READY"):set(ready and 1 or 0)
        -- A matching native camera is necessary, but is not pixel verification.
        -- Keep an experimental label on the live display for the first DCS check.
        h("SOURCE_READY"):set(ready and 1 or 0)
        report(message)
        waiting_updates=ready and 0 or waiting_updates+1
        if waiting_updates>0 and waiting_updates%200==0 and type(native.status)=="function" then
            local good,_,details=pcall(native.status)
            if good and logger and logger.write then logger.write("F117_CHARTS",logger.INFO,tostring(details)) end
        end
    end
    return {initialize=initialize,update=update}
end
return M
