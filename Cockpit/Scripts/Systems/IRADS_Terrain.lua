-- Intersect a snapshot of the rendered IRADS ray with DCS terrain.
-- Result is committed by the EFM only for the matching pending request.
local function finite(v)
    return type(v) == "number" and v == v and math.abs(v) < math.huge
end
local function trace(terrain, ray)
    for i=1,6 do if not finite(ray[i]) then return nil, "invalid ray" end end
    local norm=math.sqrt(ray[4]^2+ray[5]^2+ray[6]^2)
    if norm < 0.5 or not finite(norm) then return nil, "invalid direction" end
    local dx,dy,dz=ray[4]/norm,ray[5]/norm,ray[6]/norm
    local function sample(t)
        local x,y,z=ray[1]+dx*t,ray[2]+dy*t,ray[3]+dz*t
        local height=terrain.GetHeight(x,z)
        if not finite(height) then error("invalid terrain height") end
        return y-height
    end
    if sample(0) <= 0 then return nil, "eye below terrain" end
    local previous=0
    -- Terrain only: a 25 m march brackets the first sampled surface crossing.
    for distance=25,79975,25 do
        if sample(distance) <= 0 then
            local low,high=previous,distance
            for _=1,16 do
                local middle=(low+high)*0.5
                if sample(middle)>0 then low=middle else high=middle end
            end
            local t=(low+high)*0.5
            if t < 1 or math.abs(sample(t)) > 0.1 then return nil, "unresolved surface crossing" end
            return {ray[1]+dx*t,ray[2]+dy*t,ray[3]+dz*t}, "terrain hit"
        end
        previous=distance
    end
    return nil, "no terrain hit within 80 km"
end
local function handle(name) return get_param_handle("F117_TERRAIN_"..name) end
local request=handle("REQUEST")
local input={handle("OX"),handle("OY"),handle("OZ"),handle("DX"),handle("DY"),handle("DZ")}
local output={handle("X"),handle("Y"),handle("Z")}
local hit,ack=handle("HIT"),handle("ACK")
local terrain,attempted,last,count=nil,false,0,0
local function update()
    local id=request:get()
    if not finite(id) or id<=0 or id~=math.floor(id) or id==last then return end
    last=id
    if not attempted then
        attempted=true
        local ok,result=pcall(require,"terrain")
        if ok and type(result)=="table" and type(result.GetHeight)=="function" then terrain=result end
    end
    local point,reason=nil,"terrain API unavailable"
    if terrain then
        local ray={}
        for i=1,6 do ray[i]=input[i]:get() end
        local ok,result,detail=pcall(trace,terrain,ray)
        if ok then point,reason=result,detail else reason="terrain query failed" end
    end
    if point then for i=1,3 do output[i]:set(point[i]) end end
    hit:set(point and 1 or 0)
    ack:set(id) -- commit marker after all result fields
    if log and log.write and count<24 then
        count=count+1
        log.write("F117_IRADS_TERRAIN",log.INFO,string.format("request=%d %s%s",id,reason,
            point and string.format(" world=(%.3f,%.3f,%.3f)",point[1],point[2],point[3]) or ""))
    end
end
return {trace=trace,update=update}
