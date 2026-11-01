-- Presentation-only IRADS readouts; never changes camera, designation or delivery.
local function handle(name) return get_param_handle(name) end
local function finite(v) return type(v)=="number" and v==v and math.abs(v)<math.huge end
local altitude=handle("F117_IRADS_ALT_TEXT")
local range=handle("F117_IRADS_RANGE_TEXT")
local time=handle("F117_IRADS_TIME_TEXT")
local coords=handle("F117_IRADS_COORD_TEXT")
local mag=handle("F117_IRADS_MAG_TEXT")
local valid=handle("F117_IRADS_LOCK_VALID")
local distance=handle("F117_IRADS_LOCK_RANGE")
local flight=handle("F117_STORE_FLIGHT_TIME")
local zoom=handle("IRADS_ZOOM")
local x,z=handle("F117_IRADS_LOCK_X"),handle("F117_IRADS_LOCK_Z")
local sensor=get_base_data()
local terrain,attempted=nil,false
local lastX,lastZ,lastCoords=nil,nil,nil
local function ddm(v,positive,negative,width)
    local total=math.floor(math.abs(v)*6000+.5)
    local degrees=math.floor(total/6000)
    local minutes=(total-degrees*6000)/100
    return string.format("%s %0"..width.."d'%05.2f",v<0 and negative or positive,degrees,minutes)
end
local function update()
    local alt=sensor.getBarometricAltitude()
    altitude:set(finite(alt) and string.format("ALT %05.0f",alt*3.2808399) or "ALT -----")
    local locked=valid:get()>.5
    local r=distance:get()
    range:set(locked and finite(r) and r>0 and string.format("LR %05.0f",r*3.2808399) or "LR -----")
    local t=flight:get()
    if finite(t) and t>0 and t<6000 then
        local seconds=math.floor(t+.5)
        time:set(string.format("TTI %02d:%02d",math.floor(seconds/60),seconds%60))
    else time:set("TTI --:--") end
    local magnification={[1]="1.4X",[2]="10X",[3]="80X"}
    mag:set(magnification[zoom:get()] or "")
    if not locked then
        coords:set("");lastX,lastZ,lastCoords=nil,nil,nil
        return
    end
    if not attempted then
        attempted=true
        local ok,result=pcall(require,"terrain")
        if ok and type(result)=="table" and type(result.convertMetersToLatLon)=="function" then terrain=result end
    end
    local px,pz=x:get(),z:get()
    if not finite(px) or not finite(pz) then coords:set("");return end
    if px==lastX and pz==lastZ and lastCoords then coords:set(lastCoords);return end
    local label="GPS COORD UNAVAILABLE"
    if terrain then
        local ok,lat,lon=pcall(terrain.convertMetersToLatLon,px,pz)
        if ok and finite(lat) and finite(lon) and math.abs(lat)<=90 and math.abs(lon)<=180 then
            label=ddm(lat,"N LAT","S LAT",2).."  "..ddm(lon,"E LNG","W LNG",3)
        end
    end
    lastX,lastZ,lastCoords=px,pz,label
    coords:set(label)
end
return {update=update}
