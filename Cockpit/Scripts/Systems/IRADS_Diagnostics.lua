-- Read-only ground-point validation. Does not change designation or camera state.
local valid = get_param_handle("F117_IRADS_LOCK_VALID")
local px = get_param_handle("F117_IRADS_LOCK_X")
local py = get_param_handle("F117_IRADS_LOCK_Y")
local pz = get_param_handle("F117_IRADS_LOCK_Z")
local terrain, attempted, previous, count = nil, false, nil, 0
local function finite(v)
    return type(v) == "number" and v == v and math.abs(v) < math.huge
end
local function report(message)
    if log and log.write then log.write("F117_IRADS_TERRAIN", log.INFO, message) end
end
return function()
    if valid:get() < 0.5 then previous = nil; return end
    if count >= 24 then return end
    local x,y,z = px:get(),py:get(),pz:get()
    if not finite(x) or not finite(y) or not finite(z) then return end
    if previous and x == previous[1] and y == previous[2] and z == previous[3] then return end
    previous = {x,y,z}
    if not attempted then
        attempted = true
        local ok, result = pcall(require, "terrain")
        if ok and type(result) == "table" and type(result.GetHeight) == "function" then
            terrain = result
        else
            report("Terrain.GetHeight unavailable in cockpit Lua; ground accuracy unverified")
        end
    end
    if not terrain then return end
    count = count + 1
    local ok, height = pcall(terrain.GetHeight, x, z)
    if ok and finite(height) then
        report(string.format("lock=(%.3f,%.3f,%.3f) terrainY=%.3f deltaY=%.3f",x,y,z,height,y-height))
    else
        report("Terrain.GetHeight failed; ground accuracy unverified")
    end
end
