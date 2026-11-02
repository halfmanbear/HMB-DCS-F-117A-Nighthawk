-- Register the actual material names, including Layout Studio color overrides.
-- No native object addresses are passed through Lua.
return function(marker)
    if F117_CMDI_BUILDING then return function()end end
    local original_add=Add
    local materials,seen={},{}
    Add=function(element)
        local material=element.material
        if type(material)=="string" and material~="" and not seen[material] then
            seen[material]=true;materials[#materials+1]=material
        end
        original_add(element)
    end
    return function()
        Add=original_add
        if not package or not package.loadlib then return end
        local loader=package.loadlib(LockOn_Options.script_path.."../../bin/F117Displays.dll","luaopen_f117_brightness")
        if not loader then return end
        local ok,native=pcall(loader)
        if not ok or type(native)~="table" or type(native.register)~="function" then return end
        -- The module keeps the names; DCS closes this Lua state after the page loads.
        pcall(native.register,marker,materials)
    end
end
