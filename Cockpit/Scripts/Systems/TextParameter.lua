-- Text parameters that always stay text. Lua handle:set() stores any string that
-- reads as a number as a number, and a "%s" element then crashes DCS. The native
-- setter has no such conversion. Without it, numeric-looking text gains a letter.
local M={}
local logger=log
if not logger then
    local ok,value=pcall(require,"log")
    if ok then logger=value end
end
local function report(message)
    if logger and logger.write then logger.write("F117_TEXT",logger.INFO,message) end
end
local function load_native()
    local loader=package and package.loadlib and package.loadlib(
        LockOn_Options.script_path.."../../bin/F117Displays.dll","luaopen_f117_params")
    if loader then
        local ok,value=pcall(loader)
        if ok and type(value)=="table" and type(value.set_string)=="function" then return value end
    end
end
function M.new()
    local native,attempted
    local written={}
    local function set(name,text)
        if written[name]==text then return end
        written[name]=text
        if not attempted then
            attempted=true
            native=load_native()
            report(native and "native text parameters active"
                or "native text parameters unavailable; numeric-looking text gets a W prefix")
        end
        if native then
            if native.set_string(name,text) then return end
            native=nil
            report("native text parameter write failed; numeric-looking text gets a W prefix")
        end
        get_param_handle(name):set(tonumber(text) and "W"..text or text)
    end
    return {set=set}
end
return M
